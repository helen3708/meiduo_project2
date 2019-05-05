# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-05-01 12:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoodsVisitCount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('count', models.IntegerField(default=0, verbose_name='访问量')),
                ('date', models.DateField(auto_now_add=True, verbose_name='统计日期')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='goods.GoodsCategory', verbose_name='商品分类')),
            ],
            options={
                'verbose_name': '统计分类商品访问量',
                'verbose_name_plural': '统计分类商品访问量',
                'db_table': 'tb_goods_visit',
            },
        ),
        migrations.CreateModel(
            name='SKU',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('name', models.CharField(max_length=50, verbose_name='名称')),
                ('caption', models.CharField(max_length=100, verbose_name='副标题')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='单价')),
                ('cost_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='进价')),
                ('market_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='市场价')),
                ('stock', models.IntegerField(default=0, verbose_name='库存')),
                ('sales', models.IntegerField(default=0, verbose_name='销量')),
                ('comments', models.IntegerField(default=0, verbose_name='评价数')),
                ('is_launched', models.BooleanField(default=True, verbose_name='是否上架销售')),
                ('default_image', models.ImageField(blank=True, default='', max_length=200, null=True, upload_to='', verbose_name='默认图片')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='goods.GoodsCategory', verbose_name='从属类别')),
            ],
            options={
                'verbose_name': '商品SKU',
                'verbose_name_plural': '商品SKU',
                'db_table': 'tb_sku',
            },
        ),
        migrations.CreateModel(
            name='SKUImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('image', models.ImageField(upload_to='', verbose_name='图片')),
                ('sku', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='goods.SKU', verbose_name='sku')),
            ],
            options={
                'verbose_name': 'SKU图片',
                'verbose_name_plural': 'SKU图片',
                'db_table': 'tb_sku_image',
            },
        ),
        migrations.CreateModel(
            name='SKUSpecification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': 'SKU规格',
                'verbose_name_plural': 'SKU规格',
                'db_table': 'tb_sku_specification',
            },
        ),
        migrations.CreateModel(
            name='SpecificationOption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('value', models.CharField(max_length=20, verbose_name='选项值')),
            ],
            options={
                'verbose_name': '规格选项',
                'verbose_name_plural': '规格选项',
                'db_table': 'tb_specification_option',
            },
        ),
        migrations.CreateModel(
            name='SPU',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('name', models.CharField(max_length=50, verbose_name='名称')),
                ('sales', models.IntegerField(default=0, verbose_name='销量')),
                ('comments', models.IntegerField(default=0, verbose_name='评价数')),
                ('desc_detail', models.TextField(default='', verbose_name='详细介绍')),
                ('desc_pack', models.TextField(default='', verbose_name='包装信息')),
                ('desc_service', models.TextField(default='', verbose_name='售后服务')),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='goods.Brand', verbose_name='品牌')),
                ('category1', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cat1_spu', to='goods.GoodsCategory', verbose_name='一级类别')),
                ('category2', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cat2_spu', to='goods.GoodsCategory', verbose_name='二级类别')),
                ('category3', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cat3_spu', to='goods.GoodsCategory', verbose_name='三级类别')),
            ],
            options={
                'verbose_name': '商品SPU',
                'verbose_name_plural': '商品SPU',
                'db_table': 'tb_spu',
            },
        ),
        migrations.CreateModel(
            name='SPUSpecification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('name', models.CharField(max_length=20, verbose_name='规格名称')),
                ('spu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='specs', to='goods.SPU', verbose_name='商品SPU')),
            ],
            options={
                'verbose_name': '商品SPU规格',
                'verbose_name_plural': '商品SPU规格',
                'db_table': 'tb_spu_specification',
            },
        ),
        migrations.AddField(
            model_name='specificationoption',
            name='spec',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='goods.SPUSpecification', verbose_name='规格'),
        ),
        migrations.AddField(
            model_name='skuspecification',
            name='option',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='goods.SpecificationOption', verbose_name='规格值'),
        ),
        migrations.AddField(
            model_name='skuspecification',
            name='sku',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='specs', to='goods.SKU', verbose_name='sku'),
        ),
        migrations.AddField(
            model_name='skuspecification',
            name='spec',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='goods.SPUSpecification', verbose_name='规格名称'),
        ),
        migrations.AddField(
            model_name='sku',
            name='spu',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='goods.SPU', verbose_name='商品'),
        ),
    ]