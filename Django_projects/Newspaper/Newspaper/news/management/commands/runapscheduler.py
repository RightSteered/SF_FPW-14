import logging

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from news.models import Post
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
import datetime

logger = logging.getLogger(__name__)


# наша задача по выводу текста на экран
def my_job():
    date = datetime.date.today() - datetime.timedelta(days=7)
    wposts = Post.objects.filter(created__gte=date)
    for post in wposts.objects.all():
        for cat in post.postCategory.all():
            for user in cat.cat_sub.all():
                print (user)
                html_content = render_to_string('Msgweekly.html', {'wposts': wposts, 'user': user})
                e_mail = user.email
                msg = EmailMultiAlternatives(
                    subject=Post.title,
                    body=Post.text,
                    to=[e_mail]
                )
                msg.attach_alternative(html_content, 'text/html')
                msg.send()
                print('Messages sent')


# функция, которая будет удалять неактуальные задачи
def delete_old_job_executions(max_age=604_800):
    """This job deletes all apscheduler job executions older than `max_age` from the database."""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs apscheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # добавляем работу нашему задачнику
        scheduler.add_job(
            my_job,
            trigger=CronTrigger(day_of_week='thu', hour='20', minute='15'),
            # То же, что и интервал, но задача тригера таким образом более понятна django
            id="my_job",  # уникальный айди
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'my_job'.")

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),
            # Каждую неделю будут удаляться старые задачи, которые либо не удалось выполнить, либо уже выполнять не надо.
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info(
            "Added weekly job: 'delete_old_job_executions'."
        )

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")