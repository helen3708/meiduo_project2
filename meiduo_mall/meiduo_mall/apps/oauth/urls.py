from django.conf.urls import url,include
from django.contrib import admin
from .views import *


urlpatterns = [
    # 获取QQ登录界面url
    url(r'^qq/authorization/$',OAuthURLView.as_view()),
    url(r'^oauth_callback/$',OAuthUserView.as_view()),
]
