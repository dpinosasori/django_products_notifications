import os
from celery import Celery

# Establece el módulo Django por defecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Configuración desde settings.py (namespace='CELERY')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Busca tareas en todas las apps de Django
app.autodiscover_tasks()