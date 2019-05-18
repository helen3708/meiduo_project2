from django.conf.urls import url,include
from django.contrib import admin
from . import views


urlpatterns = [
    # 获取QQ登录界面url
    url(r'^qq/authorization/$',views.OAuthURLView.as_view()),
    url(r'^oauth_callback/$',views.OAuthUserView.as_view()),
    url(r'^sina/authorization/$',views.OAuthSinaURLView.as_view()),
    url(r'^sina_callback/$',views.OAuthSinaUserView.as_view()),
]
