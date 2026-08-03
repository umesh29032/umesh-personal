"""bod — the Business Operating Dashboard (Campaign Phase 15; PDD amendment
register entry 6 = the owner-approved product charter).

WINDOW, NEVER ENGINE (owner law): the BOD reads certified truths through the
existing service layer and presents the owner's business overview — it owns
ZERO business logic, ZERO models, ZERO migrations, ZERO write paths, and every
card drills DOWN into the module that owns its truth. Specialized module
dashboards continue to exist; the BOD only summarizes.
"""

from django.apps import AppConfig


class BodConfig(AppConfig):
    name = "bod"
    verbose_name = "Business Operating Dashboard (owner command center)"
