from django.shortcuts import render,redirect,reverse
from django.views import View
from django.http import *
import re
from .models import User,Address
from django.db import DatabaseError
import logging
from django.contrib.auth import login,authenticate,logout
from django.contrib.auth.mixins import LoginRequiredMixin
from meiduo_mall.utils.response_code import RETCODE
from django_redis import get_redis_connection
import json
from .utils import generate_verify_email_url,check_token_to_user
from celery_tasks.email.tasks import send_verify_email

# Create your views here.
logger = logging.getLogger('django')


class RegisterView(View):
    """用户注册"""
    def get(self,request):
        # 提供注册界面
        return render(request,'register.html')

    def post(self,request):
        """用户注册功能"""
        # 接收前端传入的表单数据: username, password, password2, mobile, sms_code, allow
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        sms_code = request.POST.get('sms_code')
        allow = request.POST.get('allow')

        #  all None, False, ''
        # 校验前端传入的参数是否齐全
        if all([username,password,password2,mobile,sms_code,allow]) is False:
            return HttpResponseForbidden("缺少必传参数")

        #请输入5-20个字符的用户名
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',username):
            return HttpResponseForbidden('请输入5-20个字符的用户名')
        #请输入8-20位的密码
        if not re.match(r'^[a-zA-Z0-9]{8,20}$',password):
            return HttpResponseForbidden('#请输入8-20位的密码')
        #输入的密码两次不一致
        if password != password2:
            return HttpResponseForbidden('输入的密码两次不一致')
        #您输入的手机号格式不正确
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return HttpResponseForbidden('您输入的手机号格式不正确')

        # 短信验证码校验后期再补充
        redis_conn = get_redis_connection('verify_code')
        sms_code_sever = redis_conn.get('sms_%s'%mobile)
        if sms_code_sever is None or sms_code != sms_code_sever.decode():
            return HttpResponse('短信验证码有误')

        # 创建一个user
        try:
            user = User.objects.create_user(
            username = username,
            password = password,
            mobile = mobile
        )
        except DatabaseError as e:
            # 将e存入error级别日志中
            logger.error(e)
            return render(request,'register.html',context={'register_errmsg':'用户注册失败'})

        # 登入用户，实现状态保持
        login(request,user)
        # 创建好响应对象
        response = redirect('/')
        response.set_cookie('username',user.username,max_age=3600*24*15)
        # return HttpResponse('注册成功，重定向到首页')
        return  response


class UsernameCountView(View):
    """判断用户名是否已注册"""
    def get(self,request,username):
        count = User.objects.filter(username=username).count()
        return JsonResponse({'count':count,'code':RETCODE.OK, 'errmsg':'OK'})


class MobileCountView(View):
    """判断shoujihao是否已注册"""
    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'count': count, 'code': RETCODE.OK, 'errmsg': 'OK'})

class LoginView(View):
    """用户账号登录"""
    def get(self,request):
        """提供登录界面"""
        return render(request,'login.html')
    def post(self,request):
        """账户密码登录实现逻辑"""
        # 接收用户名，密码
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        if all([username,password]) is False:
            return HttpResponseForbidden('缺少必传参数')
        # 登录认证
        user = authenticate(username=username,password=password)
        if user is None:
            return render(request,'login.html',{'account_errmsg':'用户名或密码错误'})
        # 实现状态保持
        login(request,user)
        if remembered != 'on':
            # 没有记住用户：浏览器会话结束就过期, 默认是两周
            request.session.set_expiry(0)

        # 创建好响应对象
        response=redirect(request.GET.get('next','/'))
        response.set_cookie('username',user.username,max_age=3600 * 24 * 15)
        # 响应结果重定向到首页
        return response

class LogoutView(View):
    """退出登录"""
    def get(self,request):
        # 清除session中的状态保持数据
        logout(request)
        # 清除cookie中的username
        response = redirect(reverse('users:login'))
        response.delete_cookie('username')
        # 重定向到login界面
        return response


# class UserInfoView(View):
#     """用户个人信息"""
#     def get(self,request):
#         """提供用户中心界面"""
#         # 判断当前用户是否登录,如果登录返回用户中心界面
#         # 如果用户没有登录,就重定义到登录
#         user = request.user
#         if user.is_authenticated:
#             return render(request,'user_center_info.html')
#         else:
#             return redirect('/login/?next=/info/')
class UserInfoView(LoginRequiredMixin,View):
    def get(self,request):
        return render(request,'user_center_info.html')
# class UserInfoView(View):
#     def get(self,request):
#         return render(request,'user_center_info.html')

class EmailView(LoginRequiredMixin,View):
    """添加用户邮箱"""
    def put(self,request):
        # 接收请求体emai数据
        json_dict=json.loads(request.body.decode())
        email = json_dict.get('email')
        # 校验
        if all([email]) is None:
            return HttpResponseForbidden('缺少邮箱数据')

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return HttpResponseForbidden('邮箱格式有误')
        # 获取到user
        user=request.user
        # 设置user, emai字段
        user.email=email
        # 调用save保存
        user.save()
        #发送一个邮件到email
        verify_url=generate_verify_email_url(user)
        send_verify_email.delay(email,verify_url)

        return JsonResponse({'code':RETCODE.OK,'errmsg':'OK'})
class EmailVerifyView(View):
    """激活邮箱"""
    def get(self,request):
        """实现激活邮箱逻辑"""
        # 获取token
        token=request.GET.get('token')
        # 解密并获取到user
        user=check_token_to_user(token)
        # 修改当前user.email_active=True
        if user is None:
            return HttpResponseForbidden('token无效')
        user.email_active=True
        user.save()
        # 响应
        return redirect('/info/')

class AddressView(LoginRequiredMixin,View):
    """用户收货地址"""
    def get(self,request):
        """提供用户收货地址界面"""
        # 获取当前用户的所有收货地址
        user=request.user
        address_qs=Address.objects.filter(user=user,is_deleted=False)
        address_list=[]
        for address in address_qs:
            address_dict = {
                'id': address.id,
                'title': address.title,
                'receiver': address.receiver,
                'province_id': address.province_id,
                'province': address.province.name,
                'city_id': address.city_id,
                'city': address.city.name,
                'district_id': address.district_id,
                'district': address.district.name,
                'place': address.place,
                'mobile': address.mobile,
                'tel': address.tel,
                'email': address.email
            }
            address_list.append(address_dict)
        context={
                'addresses':address_list,
                'default_address_id':user.default_address.id
            }

        return render(request,'user_center_site.html', context)

class CreateAddressView(LoginRequiredMixin,View):
    """新增收货地址"""
    def post(self,request):
        """新增收货地址逻辑"""
        user=request.user
        # 判断用户的收货地址数据,如果超过20个提前响应
        count=Address.objects.filter(user=user,is_deleted=False).count()
        if count >=20:
            return HttpResponseForbidden('用户收货地址上限')
        # 接收请求数据
        json_dict=json.loads(request.body.decode())
        title=json_dict.get('title')
        receiver=json_dict.get('receiver')
        province_id=json_dict.get('province_id')
        city_id=json_dict.get('city_id')
        district_id=json_dict.get('district_id')
        place=json_dict.get('place')
        mobile=json_dict.get('mobile')
        tel=json_dict.get('tel')
        email=json_dict.get('email')
        # 校验
        if not all([title,receiver,province_id,city_id,district_id,place,mobile]):
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$',tel):
                return HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
                return HttpResponseForbidden('参数email有误')
        # 新增
        try:
            address=Address.objects.create(
                user=user,
                title=title,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
            if user.default_address is None:
                user.default_address = address
                user.save()
        except Exception:
            return HttpResponseForbidden('新增地址出错')
        # 把新增的地址数据响应回去
        address_dict={
            'id':address.id,
            'title':address.title,
            'receiver':address.receiver,
            'province_id':address.province_id,
            'province':address.province.name,
            'city_id':address.city_id,
            'city':address.city.name,
            'district_id':address.district_id,
            'district':address.district.name,
            'place':address.place,
            'mobile':address.mobile,
            'tel':address.tel,
            'email':address.email
        }
        return JsonResponse({'code':RETCODE.OK,'errmsg':'OK','address':address_dict})

class UpdateDestroyAddressView(View):
    """修改和删除"""
    def put(self,request,address_id):
        print("1111")
        """修改地址逻辑"""
        # 查询要修改的地址对象
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return HttpResponseForbidden('要修改的地址不存在')
        # 接收
        json_dict=json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        # print()
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        # 校验
        # if not all([title, receiver, province_id, city_id, district_id, place, mobile]):
        #     return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponseForbidden('参数email有误')
        # 修改
        Address.objects.filter(id=address_id).update(
            title=title,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email
        )
        # 要重新查询一次新数据
        address = Address.objects.get(id=address_id)
        # 把新增的地址数据响应回去
        address_dict={
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province_id': address.province_id,
            'province': address.province.name,
            'city_id': address.city_id,
            'city': address.city.name,
            'district_id': address.district_id,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email
        }
        return JsonResponse({'code':RETCODE.OK,'errmsg':'OK','address':address_dict})

    def delete(self,request,address_id):
        """对收货地址逻辑删除"""
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return HttpResponseForbidden('要修改的地址不存在')
        address.is_deleted=True
        address.save()

        return JsonResponse({'code':RETCODE.OK,'errmsg':'OK'})

class DefaultAddressView(LoginRequiredMixin,View):
    """设置默认地址"""

    def put(self,request,address_id):

        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return HttpResponseForbidden('要修改的地址不存在')
        user=request.user
        user.default_address=address
        user.save()
        return JsonResponse({'code':RETCODE.OK,'errmsg':'OK'})

class UpdataTitleAddressView(LoginRequiredMixin,View):
    """editor title"""
    def put(self,request,address_id):
        print("address_id: ", address_id)
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return HttpResponseForbidden('要修改的地址不存在')
        json_dict=json.loads(request.body.decode())
        title=json_dict.get('title')
        address.title=title
        address.save()
        return JsonResponse({'code':RETCODE.OK,'errmsg':'OK'})
class ChangePasswordView(LoginRequiredMixin,View):
    """changepw"""
    def get(self,request):
        """show page"""
        return render(request,'user_center_pass.html')
    def post(self,request):
        # 接收参数
        old_pwd = request.POST.get('old_pwd')
        new_pwd = request.POST.get('new_pwd')
        new_cpwd = request.POST.get('new_cpwd')
        # 校验
        if not all([old_pwd,new_pwd]):
            return HttpResponseForbidden('缺少必传参数')
        user=request.user
        if user.check_password(old_pwd) is False:
            return render(request,'user_center_pass.html',{'origin_pwd_errmsg':'原始密码错误'})
        if not re.match(r'^[0-9a-zA-Z]{8,20}$',new_pwd):
            return HttpResponseForbidden('密码最少8位，最长20位')
        if new_pwd != new_cpwd:
            return HttpResponseForbidden('两次输入的密码不一致')
        # 修改密码
        user.set_password(new_pwd)
        user.save()
        # 响应重定向到登录界面
        # 退出状态保持
        logout(request)
        response=redirect('/login/')
        # 删除cookie中的username
        response.delete_cookie('username')
        return response
