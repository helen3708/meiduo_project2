from celery import Celery
import os
# 1. 创建celery实例对象（生产者）
# 2.加载配置， 指定谁来做为经纪人（任务存在哪）
# 3.自动注册执行

# 告诉celery 它里面用的Django配置文件在那里
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

celery_app = Celery('meiduo')
celery_app.config_from_object('celery_tasks.config')
celery_app.autodiscover_tasks(['celery_tasks.sms','celery_task.email'])