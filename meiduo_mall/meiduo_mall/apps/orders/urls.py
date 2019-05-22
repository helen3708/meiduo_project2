from django.conf.urls import url, include
from django.contrib import admin

from . import views

urlpatterns = [
    # 去结算
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view()),
    # 提交订单
    url(r'^orders/commit/$', views.OrderCommitView.as_view()),
    # 订单成功界面
    url(r'^orders/success/$', views.OrderSuccessView.as_view()),
    # 订单评价
    url(r'^orders/comment/$', views.OrderCommentView.as_view()),
    # 商品详情界面展示评价
    url(r'^comments/(?P<sku_id>\d+)/$', views.GoodsCommentView.as_view()),
    # 取消订单
    url(r'^deleted_order/(?P<order_id>\d+)/$', views.DeletedOrderView.as_view()),
]