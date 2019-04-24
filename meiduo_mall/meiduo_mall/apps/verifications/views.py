from django.shortcuts import render
from django.views import View
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import HttpResponse

# Create your views here.

class ImageCodeView(View):
    """生成图形验证码"""
    def get(self,request,uuid):
        # 利用SDK 生成图形验证码 (唯一标识字符串, 图形验证内容字符串, 二进制图片数据)
        name,text,image = captcha.generate_captcha()
        # 创建redis连接对象
        redis_cnn = get_redis_connection('verify_code')
        # 将图形验证码字符串存入到reids
        redis_cnn.setex('image%s'%uuid,300,text)
        # 把生成好的图片响应给前端
        return HttpResponse(image,content_type='image/jpg')