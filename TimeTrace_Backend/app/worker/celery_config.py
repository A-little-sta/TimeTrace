from app.core.config import settings

# Celery配置
CELERY_CONFIG = {
    "broker_url": settings.CELERY_BROKER_URL,
    "result_backend": settings.CELERY_RESULT_BACKEND,
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "timezone": "Asia/Shanghai",
    "enable_utc": True,
    "task_routes": {
        "app.worker.tasks.*": "default",
    },
    "task_queues": {
        "default": {
            "binding_key": "default",
        },
        "repair_tasks": {
            "binding_key": "repair_tasks",
        },
    },
}
