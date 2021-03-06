import pickle,base64
from django_redis import get_redis_connection

def merge_cart_cookie_to_redis(request,user,response):
    # 获取cookie购物车数据
    cart_str=request.COOKIES.get('carts')
    # 判断是够有cookie数据，如果没有直接return
    if cart_str is None:
        return
    cart_dict=pickle.loads(base64.b64decode(cart_str.encode()))

    # 创建Redis连接对象，创建管道
    redis_conn=get_redis_connection('carts')
    pl=redis_conn.pipeline()
    # 遍历cookie大字典
    for sku_id,sku_dict in cart_dict.items():
        # 将cookie中的sku_id, count向Redis的hash去存
        pl.hset('carts_%s'%user.id,sku_id,sku_dict['count'])
        # 如果当前cookie中的商品是勾选就把勾选商品的sku_id向set集合添加
        if sku_dict['selected']:
            pl.sadd('selected_%s'%user.id,sku_id)
        # 没有勾选就从Redis中移除
        pl.srem('selected_%s'%user.id,sku_id)
    pl.execute()
    # 清空cookie购物车数据
    response.delete_cookie('carts')
    # return response