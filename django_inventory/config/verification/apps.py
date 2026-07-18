"""verification — the permanent deployment-verification instrument (Campaign
Phase 13, owner designation 2026-07-12).

READ-ONLY BY ARCHITECTURE (VER-D1): no models, no migrations, no URLs, no
templates — management commands + a cited check registry + report writer only.
Registered in BASE settings (production-present); its read-only nature is what
makes that safe. The engine never seeds, never fixes, never writes: its exit
code is its whole authority.
"""

from django.apps import AppConfig


class VerificationConfig(AppConfig):
    name = "verification"
    verbose_name = "Verification Engine (read-only, Phase 13)"
