from django.apps import AppConfig
import json

class DistrictsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'districts'

    def ready(self):
        from districts.tasks import update_best_districts_cache
        update_best_districts_cache.delay()
        from django_celery_beat.models import PeriodicTask, IntervalSchedule

        # Only run this once to avoid duplicate entries
        if not PeriodicTask.objects.filter(name="Update Best Districts Cache").exists():
            schedule, _ = IntervalSchedule.objects.get_or_create(every=15, period=IntervalSchedule.MINUTES)
            PeriodicTask.objects.create(
                interval=schedule,
                name="Update Best Districts Cache",
                task="districts.tasks.update_best_districts_cache",
                kwargs=json.dumps({}),
            )
