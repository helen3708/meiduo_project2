from django.conf.urls import url, include
from django.contrib import admin

from .views import ListView,HotGoodsView,DetailView,DetailVisitView

urlpatterns = [
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', ListView.as_view()),
    url(r'^hot/(?P<category_id>\d+)/$',HotGoodsView.as_view()),
    url(r'^detail/(?P<sku_id>\d+)/$',DetailView.as_view()),
    url(r'^detail/visit/(?P<category_id>\d+)/$',DetailVisitView.as_view()),
]
