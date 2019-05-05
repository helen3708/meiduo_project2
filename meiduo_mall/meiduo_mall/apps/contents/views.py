from django.shortcuts import render

from django.views import View
from goods.models import GoodsChannel
from .utils import get_categories
from .models import ContentCategory


class IndexView(View):
    def get(self,request):
        """商品分类及广告数据展示"""
        # 用来装所有广告数据的字典
        contents={}
        # 获取所有广告类别数据
        contentCategory_qs=ContentCategory.objects.all()
        # 遍历广告类别数据查询集
        for category in contentCategory_qs:
            # 将广告数据添加到字典
            contents[category.key]=category.content_set.filter(status=True).order_by('sequence')
        # 渲染模板的上下文
        context={
            'categories':get_categories(),
            'contents':contents

        }

        return render(request,'index.html',context)
