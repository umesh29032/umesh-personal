"""
AppConfig for the accounts app.

`default_auto_field` is set to BigAutoField (64-bit int PKs) — consistent with
the project-wide setting in base.py and safe for tables that could grow large.
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
