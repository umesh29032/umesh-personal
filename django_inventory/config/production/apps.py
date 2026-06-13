from django.apps import AppConfig


class ProductionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'production'
    verbose_name = 'Production'

    def ready(self):
        # Import every stages/<stage>/handler.py so StageHandlers self-register
        # (M2 stage engine). Cheap + import-safe: handlers only do module-level
        # imports of constants + the base contract; services are imported lazily.
        from production.stages.base import autodiscover
        autodiscover()
