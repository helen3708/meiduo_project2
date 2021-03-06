from django.conf.urls import url, include
from django.contrib import admin

from . import views

urlpatterns = [
    # 发起支付 (获取支付宝登录链接)
    url(r'^payment/(?P<order_id>\d+)/$', views.PaymentView.as_view()),
    # 保存支付结果
    url(r'^payment/status/$', views.PaymentStatusView.as_view()),
]
