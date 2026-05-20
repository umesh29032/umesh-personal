"""
AppConfig for the accounts app.

`default_auto_field` is set to BigAutoField (64-bit int PKs) — consistent with
the project-wide setting in base.py and safe for tables that could grow large.

`ready()` ka kaam = signal handlers wire karna. Yahaan se accounts/signals.py
import hota hai jo `User.skills` M2M changes pe retro-tag logic chalata hai.
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # noqa: import side-effect — handlers registered on import
        from accounts import signals  # pylint: disable=unused-import,import-outside-toplevel
