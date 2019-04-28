from django.shortcuts import render,redirect
from django.views import View
from django.http import *
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from meiduo_mall.utils.response_code import RETCODE
import logging
import re
from .models import OAuthQQUser
from django.contrib.auth import login
from .utils import *
from django_redis import get_redis_connection
from users.models import User

# Create your views here

logger = logging.getLogger('django')

class OAuthURLView(View):
    """提供QQ登录界面链接"""
    def get(self,request):
        # 提取前端用查询参数传入的next参数:记录用户从哪里去到login界面
        next = request.GET.get('next','/')
        # 获取QQ登录页面网址
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                    client_secret=settings.QQ_CLIENT_SECRET,
                    redirect_uri=settings.QQ_REDIRECT_URI,
                    state=next)
        # 拼接QQ登录连接
        login_url = oauth.get_qq_url()

        return JsonResponse({'login_url':login_url,'code':RETCODE.OK,'errmsg':'OK'})
class OAuthUserView(View):
    """QQ登录后回调处理"""
    def get(self, request):
        code = request.GET.get('code')
        state = request.GET.get('state','/')

        # 创建QQ登录SDK对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        )
        try:
             # 调用SDK中的get_access_token(code) 得到access_token
            access_token = oauth.get_access_token(code)
             # 调用SDK中的get_openid(access_token) 得到openid
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code':RETCODE.SERVERERR,'errmsg':'QQ服务器不可用'})

        # 在OAuthQQUser表中查询openid
        try:
            oauth_model = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果在OAuthQQUser表中没有查询到openid, 没绑定说明第一个QQ登录
            # 先对openid进行加密
            openid=generate_openid_signature(openid)
            return render(request,'oauth_callback.html',{'openid':openid})
        # 如果在OAuthQQUser表中查询到openid,说明是已绑定过美多用户的QQ号,oauth_model.user侯的user是外间
        user=oauth_model.user
        login(request,user)
        # 响应结果
        # 获取界面跳转来源
        response = redirect(state)
        response.set_cookie('username',user.username,max_age=3600*24*15)
        return response

    def post(self,request):
        """实现openid绑定用户逻辑"""
        # 当用户点击绑定界面中的保存时，把表单中的数据及表单中隐藏的openid一并发给后端
        # 接收数据
        mobile=request.POST.get('mobile')
        password=request.POST.get('password')
        sms_code=request.POST.get('sms_code')
        openid=request.POST.get('openid')
        # 校验
        # 手机号、密码、短信认证码校验
        if all([mobile,password,sms_code,openid]) is False:
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('您输入的手机号格式不正确')

        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseForbidden('请输入8-20位的密码')

        # 短信验证码校验
        redis_coon = get_redis_connection('verify_code')
        sms_code_server = redis_coon.get('sms_%s' % mobile)  # 获取redis中的短信验证码

        if sms_code_server is None or sms_code != sms_code_server.decode():
            return HttpResponseForbidden('短信验证码有误')

        # 对openid使用itsdangerous解密及校验
        openid=check_openid_sign(openid)
        if openid is None:
            return HttpResponseForbidden('openid无效')
        # 使用mobile查询User表

        try:
            user=User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 如果没有查到mobile对应的用户user说明是新用户
            # 就创建一个新的user, 手机号也作为username
            user=User.objects.create_user(username=mobile,password=password,mobile=mobile)
        else:
        # 如果查到user说明是已注册的美多用户
        # 再校验输入的密码是否正确
            if user.check_password(password) is False:
                return HttpResponseForbidden('账号或密码错误')
        # 然后无论是新用户还是已存在用户，直接和openid绑定,user和openid绑定
        OAuthQQUser.objects.create(user=user,openid=openid)
        # 做状态保持，保存username和cookie
        # 重定向到参数记录的界面来源或首页
        login(request,user)
        response=redirect(request.GET.get('state'))
        response.set_cookie('username',user.username,max_age=settings.SESSION_COOKIE_AGE)
        return response
