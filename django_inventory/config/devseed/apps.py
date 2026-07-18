from django.apps import AppConfig


class DevseedConfig(AppConfig):
    # AppConfig: Django's app registry entry — devseed ships NO models, so
    # default_auto_field is irrelevant but harmless to pin.
    default_auto_field = "django.db.models.BigAutoField"
    name = "devseed"
    verbose_name = "Dev Seeder Engine (dev-only — Phase 12)"
