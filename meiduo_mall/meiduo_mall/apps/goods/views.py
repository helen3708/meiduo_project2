from django.shortcuts import render
from django.http import HttpResponseForbidden,JsonResponse
from django.views import View
from django.core.paginator import Paginator

from .models import GoodsCategory
from contents.utils import get_categories
from .utils import get_breadcrumb
from meiduo_mall.utils.response_code import RETCODE

class ListView(View):
    """商品列表界面"""
    def get(self,request,category_id,page_num):
        """
        :param category_id: 当前选择的三级类别id
        :param page_num: 第几页
        """
        try:
            category=GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return HttpResponseForbidden('商品类别不存在')
        # 获取查询参数中的sort 排序规则
        sort = request.GET.get('sort','default')
        if sort=='price':
            sort_fields='price'
        elif sort=='hot':
            sort_fields='-sales'
        else:
            sort_fields='create_time'
        # 面包屑导航数据
        # 查询当前三级类别下面的所有sku
        # order_by(只能放当前查询集中每个模型中的字段)
        sku_qs=category.sku_set.filter(is_launched=True).order_by(sort_fields)
        # 创建分页对象
        # Paginator(要进行分页的所有数据, 每页显示多少条数据)
        paginator=Paginator(sku_qs,5)
        # 获取指定界面的sku数据
        page_skus=paginator.page(page_num)
        # 获取当前的总页数
        total_page=paginator.num_pages
        context={
            'categories':get_categories(),#频道分类
            'breadcrumb':get_breadcrumb(category),#面包屑导航
            'sort': sort,  # 排序字段
            'category': category,  # 第三级分类
            'page_skus': page_skus,  # 分页后数据
            'total_page': total_page,  # 总页数
            'page_num': page_num,  # 当前页码
        }
        return render(request,'list.html',context)

class HotGoodsView(View):
    """热销排行数据"""
    def get(self,request,category_id):
        try:
            category=GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return HttpResponseForbidden('商品类别不存在')
        # 获取当前三级类别下面销量最高的前两个sku
        skus_qs=category.sku_set.filter(is_launched=True).order_by('-sales')[0:2]
        # 包装两个热销商品字典
        hot_skus=[]
        for sku in skus_qs:
            hot_skus.append({
                'id':sku.id,
                'name':sku.name,
                'price':sku.price,
                'default_image_url':sku.default_image.url
            })
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': hot_skus})