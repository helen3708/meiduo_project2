from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from django import http
from decimal import Decimal
from django.utils import timezone
import json

from meiduo_mall.utils.views import LoginRequiredView
from users.models import Address
from goods.models import SKU
from .models import OrderGoods,OrderInfo
from meiduo_mall.utils.response_code import RETCODE

# Create your views here.
class OrderSettlementView(LoginRequiredView):
    """订单结算"""
    def get(self,request):
        """提供订单结算页面"""
        user=request.user
        # 获取地址数据Address，查询集找不到数据不会报错，会返回0个，而get会报错
        addresses=Address.objects.filter(user=user,is_deleted=False)
        # 如果有收获地址什么也不做，没有收货地址把变量设置为None
        addresses=addresses if addresses.exists() else None

        # 创建Redis连接对象
        redis_conn=get_redis_connection('carts')
        # 获取hash所有数据
        redis_cart=redis_conn.hgetall('carts_%s'%user.id)
        # {sku_id：count}
        # 获取set集合数据
        cart_selected=redis_conn.smembers('selected_%s'%user.id)
        # {sku_id}
        # 准备一个字典，用来装勾选的商品id ，count
        cart_dict={}
        # 遍历set集合
        for sku_id_bytes in cart_selected:
            # 将勾选的商品sku_id和count装入字典，并都转换为int类型
            cart_dict[int(sku_id_bytes)]=int(redis_cart[sku_id_bytes])
        # 通过set集合中的sku_id查询到对应的所有sku模型
        sku_qs=SKU.objects.filter(id__in=cart_dict.keys())
        # 定义变量count = 0, amount = Decimal('0.00'），定义金钱的数据使用Decimal
        total_count=0
        total_amount=Decimal('0.00')
        # 遍历sku_qs查询集给每个sku模型多定义count和amount属性
        for sku in sku_qs:
            # 获取当前商品的购买数量
            count=cart_dict[sku.id]
            # 把当前商品购物车数据绑定到sku模型对象上
            sku.count=count
            sku.amount=sku.price*count
            # 累加购买商品总数量
            total_count += count
            # 累加商品总价
            total_amount += sku.amount
        # 运费freight = Decimal('10:00')
        freight=Decimal('10.00')
        context={
            'addresses': addresses,  # 用户收货地址
            'skus': sku_qs,  # 勾选的购物车商品数据
            'total_count': total_count,  # 勾选商品总数量
            'total_amount': total_amount,  # 勾选商品总价
            'freight': freight,  # 运费
            'payment_amount': total_amount + freight  # 实付款
        }

        return render(request,'place_order.html',context)

class OrderCommitView(LoginRequiredView):
    """提交订单"""
    def post(self,request):
        # 接收数据前端传入的收货地址，支付方式
        json_dict=json.loads(request.body.decode())
        address_id=json_dict.get('address_id')
        pay_method=json_dict.get('pay_method')
        # 校验
        if not all([address_id,pay_method]):
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('收货有误')
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM.get('CASH'),OrderInfo.PAY_METHODS_ENUM.get('ALIPAY')]:
                return http.HttpResponseForbidden('支付方式有误')

        # 生成订单编号：时间 + user.id
        user=request.user
        order_id=timezone.localtime().strftime('%Y%m%d%H%M%S')+('%09d'%user.id)
        # 判断订单状态
        status=(OrderInfo.ORDER_STATUS_ENUM.get('UNPAID')) if pay_method == OrderInfo.PAY_METHODS_ENUM.get('ALIPAY') else OrderInfo.ORDER_STATUS_ENUM.get('UNSEND')
        # 创建一个订单基本信息模型并存储
        order=OrderInfo.objects.create(
            order_id=order_id,
            user=user,
            address=address,
            total_count=0,
            total_amount=Decimal('0.00'),
            freight=Decimal('10.00'),
            pay_method=pay_method,
            status=status
        )
        # 创建Redis连接
        redis_conn=get_redis_connection('carts')
        redis_cart=redis_conn.hgetall('carts_%s'%user.id)
        # 获取set集合数据
        cart_selected=redis_conn.smembers('selected_%s'%user.id)
        # 遍历set把要购买的sku_id和count包装到一个新的字典中
        cart_dict={}
        for sku_id_bytes in cart_selected:
            cart_dict[int(sku_id_bytes)]=int(redis_cart[sku_id_bytes])
        # 遍历用来包装所有要购买的商品的字典，用一个取一个
        for sku_id in cart_dict:
            # 通过sku_id获取sku模型
            sku=SKU.objects.get(id=sku_id)
            # 获取当前商品要购买的数量
            buy_count=cart_dict[sku_id]
            # 获取当前商品的库存和数量
            origin_stock=sku.stock
            origin_sales=sku.sales
            # 判断库存
            if buy_count > origin_stock:
                return http.JsonResponse({'code':RETCODE.STOCKERR,'errmsg':'库存不足'})
            # 计算新的库存和销量
            new_stock=origin_stock - buy_count
            new_sales=origin_sales + buy_count
            # 修改sku的库存
            sku.stock=new_stock
            # 修改sku的销量
            sku.sales=new_sales
            # 保存
            sku.save()

            # 修改spu的销量
            sku.spu.sales += buy_count
            sku.spu.save()
            # 存储订单商品记录
            OrderGoods.objects.create(
                order=order,
                sku=sku,
                count=buy_count,
                price=sku.price
            )
            # 累加商品订单总数量
            order.total_count += buy_count
            # 累加商品总价
            order.total_amount += sku.price * buy_count
        # 累加运费
        order.total_amount += order.freight
        # 保存order.save(）
        order.save()
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'提交订单成功','order_id':order_id})
