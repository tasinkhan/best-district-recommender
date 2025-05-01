from django.apps import AppConfig


class DistrictsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'districts'

    def ready(self):
        from districts.tasks import update_best_districts_cache
        update_best_districts_cache.delay()
