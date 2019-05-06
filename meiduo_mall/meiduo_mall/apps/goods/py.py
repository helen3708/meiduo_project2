from django.shortcuts import render
from django.http import HttpResponseForbidden,JsonResponse
from django.views import View
from django.core.paginator import Paginator

from .models import GoodsCategory,SKU
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
        print(hot_skus)
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': hot_skus})

class DtailView(View):
    """商品详情界面"""
    def get(self,request,sku_id):

        # 获取当前sku的信息
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request,'404.html')

        # sku所属的三级类别
        category=sku.category
        # 查询当前sku所对应的spu
        spu=sku.spu
        """1.准备当前商品的规格选项列表 [8, 11]"""
        # 获取当前正显示的sku商品的所有具体规格
        current_sku_spec_qs=sku.specs.order_by('spec_id')
        # 获取出当前正显示的sku商品的规格选项id列表
        current_sku_option_ids=[]
        for current_sku_spec in current_sku_spec_qs:
            current_sku_option_ids.append(current_sku_spec.option_id)
        """2.构造规格选择仓库
                {(8, 11): 3, (8, 12): 4, (9, 11): 5, (9, 12): 6, (10, 11): 7, (10, 12): 8}
        """
        # 构造规格选择仓库
        # 获取当前spu下的所有sku
        temp_sku_qs=spu.sku_set.all()
        # 选项仓库大字典
        spec_sku_map={}
        for temp_sku in temp_sku_qs:
            # 查询每一个sku的规格数据
            temp_spec_qs=temp_sku.specs.order_by('spec_id')
            # 用来包装每个sku的选项值
            temp_sku_option_ids=[]
            for temp_spec in temp_spec_qs:
                temp_sku_option_ids.append(temp_spec.option_id)
            spec_sku_map[tuple(temp_sku_option_ids)]=temp_sku.id
        """3.组合 并找到sku_id 绑定"""
        # 获取当前spu中的所有规格
        spu_spec_qs=spu.specs.order_by('id')
        # 遍历当前所有的规格
        for index,spec in enumerate(spu_spec_qs):
            # 获取当前规格中的所有选项
            spec_option_qs=spec.options.all()
            # 复制一个新的当前显示商品的规格选项列表
            temp_option_ids=current_sku_option_ids[:]
            # 遍历当前规格下的所有选项
            for option in spec_option_qs:
                temp_option_ids[index]=option.id
                option.sku_id=spec_sku_map.get(tuple(temp_option_ids))
            # 把规格下的所有选项绑定到规格对象的spec_options属性上
            spec.spec_options=spec_option_qs


        # 渲染页面
        context = {
            'categories': get_categories(),
            'breadcrumb': get_breadcrumb(category),
            'category':category,# 当前的显示sku所属的三级类别
            'sku': sku,# 当前要显示的sku模型对象
            'spu':spu,
            'specs':spu_spec_qs# 当前商品的所有规格数据
        }
        return render(request,'detail.html',context)