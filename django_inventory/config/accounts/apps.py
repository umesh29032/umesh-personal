"""
AppConfig for the accounts app.

`default_auto_field` is set to BigAutoField (64-bit int PKs) — consistent with
the project-wide setting in base.py and safe for tables that could grow large.

No signals (CLAUDE.md rule #4). The skill→layering retro-tag that used to live
in a `ready()`-wired m2m_changed signal is now an explicit call:
`accounts.services.user_service.sync_user_skills(user)`, invoked from the user-
management views + the Django admin's `save_related`.
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
