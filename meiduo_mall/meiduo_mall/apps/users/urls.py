from django.conf.urls import url,include
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from .views import *


urlpatterns = [
    # 注册
    url(r'^register/$',RegisterView.as_view(),name='register'),
    # 判断用户名是否已注册
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$',UsernameCountView.as_view()),
    # 判断手机号是否已注册
    # 用户登录
    url(r'^login/$',LoginView.as_view(),name='login'),
    # 退出登录
    url(r'^logout/$',LogoutView.as_view(),name='logout'),
    # 用户中心
    url(r'^info/$',UserInfoView.as_view(),name='info'),
    # url(r'^info/$',login_required(UserInfoView.as_view()),name='info'),
    # 设置用户邮箱
    url(r'^emails/$',EmailView.as_view(),name='emails'),
    # 激活邮箱
    url(r'^emails/verification/$',EmailVerifyView.as_view()),
    # 用户收货地址
    url(r'^addresses/$',AddressView.as_view(),name='address'),
    # 用户新增收货地址
    url(r'^addresses/create/$',CreateAddressView.as_view()),
    #用户收货地址修改和删除
    url(r'^addresses/(?P<address_id>\d+)/$',UpdateDestroyAddressView.as_view()),
    #设置默认地址
    url(r'^addresses/(?P<address_id>\d+)/default/$',DefaultAddressView.as_view()),
    # 修改用户地址标题
    url(r'^addresses/(?P<address_id>\d+)/title/$',UpdataTitleAddressView.as_view()),
    #changpwd
    url(r'^password/$',ChangePasswordView.as_view()),
    url(r'^browse_histories/$',UserBrowseHistory.as_view()),
    url(r'^orders/info/(?P<page_num>\d+)/$',UserOrderInfoView.as_view()),
]

