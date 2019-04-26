from django.shortcuts import render,redirect
from django.views import View
from django.http import *
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from meiduo_mall.utils.response_code import RETCODE
import logging
from .models import OAuthQQUser
from django.contrib.auth import login

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
            return render(request,'oauth_callback.html')

        # 如果在OAuthQQUser表中查询到openid,说明是已绑定过美多用户的QQ号,oauth_model.user侯的user是外间
        user=oauth_model.user
        login(request,user)
        # 响应结果
        # 获取界面跳转来源
        response = redirect(state)
        response.set_cookie('username',user.username,max_age=3600*24*15)
        return response

