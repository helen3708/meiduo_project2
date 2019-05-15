from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from django import http
from decimal import Decimal
from django.utils import timezone
import json
from django.db import transaction

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
        # 手动创建事务
        with transaction.atomic():
            # 创建事务保存点
            save_point=transaction.savepoint()
            try:
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
                    while True:
                        # 通过sku_id获取sku模型
                        sku=SKU.objects.get(id=sku_id)
                        # 获取当前商品要购买的数量
                        buy_count=cart_dict[sku_id]
                        # 获取当前商品的库存和数量
                        origin_stock=sku.stock
                        origin_sales=sku.sales

                        # 测试两个用户同时下单
                        import time
                        time.sleep(10)

                        # 判断库存
                        if buy_count > origin_stock:
                            # 事务回滚
                            transaction.savepoint_rollback(save_point)
                            return http.JsonResponse({'code':RETCODE.STOCKERR,'errmsg':'库存不足'})
                        # 计算新的库存和销量
                        new_stock=origin_stock - buy_count
                        new_sales=origin_sales + buy_count
                        # 修改sku的库存
                        # sku.stock=new_stock
                        # # 修改sku的销量
                        # sku.sales=new_sales
                        # 保存
                        # sku.save()

                        # 使用乐观锁解决抢夺时数据库写入脏数据
                        result=SKU.objects.filter(id=sku_id,stock=origin_stock).update(stock=new_stock,sales=new_sales)
                        # 如果下单失败,给它无限次下单机会,只到成功,或库存不足
                        if result==0:
                            continue

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
                        break # 如果当前这个商品下单成功跳出死循环
                # 累加运费
                order.total_amount += order.freight
                # 保存order.save(）
                order.save()
            except Exception:
                # 中间出现任务异常都回滚事务
                transaction.savepoint_rollback(save_point)
                return http.JsonResponse({'code':RETCODE.DBERR,'errmsg':'下单失败'})
            else:
                # 提交事务
                transaction.savepoint_commit(save_point)

        pl=redis_conn.pipeline()
        # 删除hash中已经购买商品数据{2: 1}
        pl.hdel('carts_%s'%user.id,*cart_selected)
        pl.delete('selected_%s'%user.id)
        pl.execute()

        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'提交订单成功','order_id':order_id})

class OrderSuccessView(LoginRequiredView):
    def get(self,request):
        # 接收查询参数order_id, payment_amount, pay_method
        query_dict=request.GET
        order_id=query_dict.get('order_id')
        payment_amount=query_dict.get('payment_amount')
        pay_method=query_dict.get('pay_method')
        # 校验参数
        try:
            OrderInfo.objects.get(order_id=order_id,total_amount=payment_amount,pay_method=pay_method)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('订单有误')
        # 包装要传给模板的数据
        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }
        return render(request,'order_success.html',context)

class OrderCommentView(LoginRequiredView):
    """订单评价"""
    def get(self,request):
        """展示订单评价界面"""
        # 接收查询参数
        order_id=request.GET.get('order_id')
        # 校验
        try:
            order=OrderInfo.objects.get(order_id=order_id,user=request.user,status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('订单有误')
        # 查询当前订单中所有未评价的订单商品
        order_goods_qs=OrderGoods.objects.filter(order=order,is_commented=False)
        # 构造前端渲染需要的数据，新建一个空列表
        uncomment_goods_list=[]
        # 遍历order_goods_qs，获取sku
        for order_goods in order_goods_qs:
            sku=order_goods.sku
            uncomment_goods_list.append({
                'order_id': order_id,
                'sku_id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': str(sku.price),
                'score': order_goods.score,
                'comment': order_goods.comment,
                'is_anonymous': str(order_goods.is_anonymous),
                'is_comment': str(order_goods.is_commented)
            })
        context={
                'uncomment_goods_list': uncomment_goods_list
            }
        return render(request,'goods_judge.html',context)

    def post(self,request):
        """评价订单商品"""
        # 获取请求体中的数据order_id, sku_id, comment, score, is_anonymous
        json_dict=json.loads(request.body.decode())
        order_id=json_dict.get('order_id')
        sku_id=json_dict.get('sku_id')
        comment=json_dict.get('comment')
        score=json_dict.get('score')
        is_anonymous=json_dict.get('is_anonymous')
        # 校验
        # 参数是否齐全
        if not all([order_id,sku_id,comment,score]):
            return http.HttpResponseForbidden('缺少必传参数')
        # order_id, sku_id是否有效,is_anonymous
        try:
            order=OrderInfo.objects.get(order_id=order_id,user=request.user,status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden("订单信息有误")
        try:
            sku=SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku不存在')
        if isinstance(is_anonymous,bool) is False:
            return http.HttpResponseForbidden('参数类型有误')
        # 修改OrderGoods中的评价信息
        OrderGoods.objects.filter(sku_id=sku_id,order_id=order_id,is_commented=False).update(is_anonymous=is_anonymous,comment=comment,score=score,is_commented=True)
        # 修改sku和spu的评价量
        sku.comments += 1
        sku.save()
        sku.spu.comments += 1
        sku.spu.save()
        # 判断订单中的商品是否全部评价完成
        if OrderGoods.objects.filter(order_id=order_id,is_commented=False).count()==0:
            # 如果都评价则将订单状态修改为已完成
            order.status=OrderInfo.ORDER_STATUS_ENUM['FINISHED']
            order.save()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

class GoodsCommentView(View):
    """获取评价信息"""
    def get(self,request,sku_id):
        # 校验
        try:
            sku=SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku不存在')
        # 获取OrderGood中的当前sku_id的所有OrderGoods
        order_goods_qs=OrderGoods.objects.filter(sku_id=sku_id,is_commented=True).order_by('-create_time')
        # 构造前端需要的数据格式  usernmae, score, comment
        comments=[]
        for order_goods in order_goods_qs:
            # 获取当前订单商品所属用户名
            username=order_goods.order.user.username
            comments.append({
                'username':(username[0]+'***'+username[-1]) if order_goods.is_anonymous else username ,
                'score':order_goods.score,
                'comment':order_goods.comment
            })
        # 响应
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK','comment_list':comments})

