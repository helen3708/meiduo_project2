from django.conf.urls import url,include
from django.contrib import admin
from .views import *


urlpatterns = [
    url(r'^image_codes/(?P<uuid>[\w-]+)/',ImageCodeView.as_view(),name='image_codes'),

]