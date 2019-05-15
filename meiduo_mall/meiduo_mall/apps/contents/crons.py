from django.shortcuts import render
from django.conf import settings
import os,time

from .models import ContentCategory
from .utils import get_categories

def generate_static_index_html():
    """商品分类及广告数据展示"""
    # 用来装所有广告数据的字典
    contents = {}
    print('%s: generate_static_index_html' % time.ctime())
    # 获取所有广告类别数据
    contentCategory_qs = ContentCategory.objects.all()
    # 遍历广告类别数据查询集
    for category in contentCategory_qs:
        # 将广告数据添加到字典
        contents[category.key] = category.content_set.filter(status=True).order_by('sequence')
    # 渲染模板的上下文
    context = {
        'categories': get_categories(),
        'contents': contents

    }

    # return render(request, 'index.html', context)
    response=render(None, 'index.html', context)
    html_text=response.content.decode()  # 获取响应体数据
    # 将首页html字符串写入到指定目录，命名'index.html'
    file_path=os.path.join(settings.STATICFILES_DIRS[0],'index.html')
    with open(file_path,'w',encoding='utf-8') as f:
        f.write(html_text)