from django.apps import AppConfig


class CoreConfig(AppConfig):
    # BigAutoField = default PK type. core has only ABSTRACT models (no tables),
    # so this never actually creates a PK — it's here for convention/parity.
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core (shared base models)'
