from django.shortcuts import render,redirect
from django.views import View
from django.http import *
import re
from .models import User
from django.db import DatabaseError
import logging
from django.contrib.auth import login,authenticate
from meiduo_mall.utils.response_code import RETCODE
from django_redis import get_redis_connection

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

        # return HttpResponse('注册成功，重定向到首页')
        return redirect('/')


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
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        if all([username,password]) is False:
            return HttpResponseForbidden('缺少必传参数')

        user = authenticate(username=username,password=password)
        if user is None:
            return render(request,'login.html',{'account_errmsg':'用户名或密码错误'})

        login(request,user)
        if remembered != 'on':
            request.session.set_expiry(0)
        return redirect('/')
