from celery import Celery
from app.worker.celery_config import CELERY_CONFIG

# 创建Celery实例
celery = Celery("TimeTrace_Backend")

# 加载配置
celery.config_from_object(CELERY_CONFIG)

# 自动发现任务
celery.autodiscover_tasks(["app.worker"], force=True)
