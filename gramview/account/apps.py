from django.apps import AppConfig
import logging
import sys

logger = logging.getLogger(__name__)


class AccountConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "account"

    def ready(self):
        # Выполняем только при запуске runserver или celery
        if 'runserver' in sys.argv or 'celery' in sys.argv:
            self.create_periodic_task()

    def create_periodic_task(self):
        from django_celery_beat.models import PeriodicTask, IntervalSchedule

        try:
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=14,
                period=IntervalSchedule.DAYS
            )

            PeriodicTask.objects.update_or_create(
                name='Update subscriber growth',
                defaults={
                    'interval': schedule,
                    'task': 'account.tasks.update_subscriber_growth',
                }
            )
            logger.info("Periodic task created or updated.")
        except Exception as e:
            logger.error(f"Error creating periodic task: {e}")
