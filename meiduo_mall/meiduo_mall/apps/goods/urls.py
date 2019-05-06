from django.conf.urls import url, include
from django.contrib import admin

from .views import ListView,HotGoodsView,DtailView

urlpatterns = [
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', ListView.as_view()),
    url(r'^hot/(?P<category_id>\d+)/$',HotGoodsView.as_view()),
    url(r'^detail/(?P<sku_id>\d+)/$',DtailView.as_view()),
]
