import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Newspaper.settings')
app = Celery('Newspaper')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send_news_weekly': {
        'task': 'news.tasks.weekly_broadcast',
        'schedule': crontab(hour='22', minute='27', day_of_week='tue')
    },
}
