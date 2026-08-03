"""
AppConfig for the accounts app.

`default_auto_field` is set to BigAutoField (64-bit int PKs) — consistent with
the project-wide setting in base.py and safe for tables that could grow large.

No signals (CLAUDE.md rule #4), and — since the C-1 freeze closeout
(2026-07-05) — NO cross-app writes at all: the historical skill→layering
retro-tag (signal, later an explicit `sync_user_skills` call) was removed.
Saving a user never touches production rosters; managers assign explicitly
on the stage panels (the ONLY roster source).
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
