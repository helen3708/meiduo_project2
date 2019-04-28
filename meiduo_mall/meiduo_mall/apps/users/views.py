from django.shortcuts import render,redirect,reverse
from django.views import View
from django.http import *
import re
from .models import User
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