from django.conf.urls import url,include
from django.contrib import admin
from .views import *


urlpatterns = [
    url(r'^image_codes/(?P<uuid>[\w-]+)/$',ImageCodeView.as_view(),name='image_codes'),
    url(r'^sms_codes/(?P<mobile>1[3-9]\w{9})/$',SMSCodeView.as_view(),name='sms_codes'),
    url(r'^sms_codes/$',SMSCodeTokenView.as_view()),
]