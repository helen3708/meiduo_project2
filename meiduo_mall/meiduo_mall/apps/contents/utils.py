from goods.models import GoodsChannel

def get_categories():
    # 用来包装所有商品类别数据
    categories = {}
    # 获取所有一级类别分组数据
    goods_channels_sq = GoodsChannel.objects.order_by('group_id', 'sequence')
    # 遍历分组数据的查询集
    for channel in goods_channels_sq:
        # 获取组号
        group_id = channel.group_id
        # 判断当前的组号在字典中是否存在
        if group_id not in categories:
            # 不存在, 包装一个当前组的准备数据
            categories[group_id] = {'channels': [], 'cat_subs': []}
        # 若存在，获取一级类别数据
        cat1 = channel.category
        # 将频道中的url绑定给一级类型对象
        cat1.url = channel.url
        # 添加一级数据到字典中
        categories[group_id]['channels'].append(cat1)
        # 获取当前一组下面的所有二级数据
        cat2_qs = cat1.subs.all()
        # 遍历二级数据查询集
        for cat2 in cat2_qs:
            # 获取当前二级下面的所有三级,得到三级查询集
            cat3_qs = cat2.subs.all()
            # 把二级下面的所有三级绑定给cat2对象的cat_subs属性
            cat2.cat_subs = cat3_qs
            # 添加2级数据到字典中
            categories[group_id]['cat_subs'].append(cat2)
    return categories