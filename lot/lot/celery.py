import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lot.settings')

app1 = Celery('lot')
app1.config_from_object('django.conf:settings', namespace='CELERY')
app1.autodiscover_tasks()

app2 = Celery('trees')
app2.config_from_object('django.conf:settings', namespace='CELERY')
app2.autodiscover_tasks()
