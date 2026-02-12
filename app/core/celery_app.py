import os
from celery import Celery

# Configuración de URLs para Redis (Broker y Backend)
# Por defecto usa localhost, pero permite sobreescribir con variables de entorno (útil para Docker)
broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "factus_worker",
    broker=broker_url,
    backend=result_backend,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
