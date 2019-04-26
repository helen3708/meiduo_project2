from django.conf.urls import url,include
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from .views import *


urlpatterns = [
    url(r'^register/$',RegisterView.as_view(),name='register'),
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$',UsernameCountView.as_view()),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$',MobileCountView.as_view()),
    url(r'^login/$',LoginView.as_view(),name='login'),
    url(r'^logout/$',LogoutView.as_view(),name='logout'),
    url(r'^info/$',UserInfoView.as_view(),name='info'),
    # url(r'^info/$',login_required(UserInfoView.as_view()),name='info'),
    ]

