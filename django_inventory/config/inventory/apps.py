from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'

    # No signals to register — ledger entries are created explicitly in services.
    # See inventory/signals.py for explanation.
