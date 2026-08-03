"""fabric_profile_service — SINGLE WRITER for ProductFabricProfile
(🔒 Phase-6 M3 frozen API; INTEGRATION_DESIGN §3h/§3i).

Rule B (owner-locked): the profile is DEFAULTS ONLY — prefill values for
NEW work started after the change. Changing it never modifies existing
layouts, approved layouts, generation runs, saved markers or historical
exports (test-asserted byte-identity). Structurally: this module imports
NOTHING layout-side and writes exactly one table.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from accounts.services import MANAGEMENT_ROLES, user_has_role

from patterns_ai.models import ProductFabricProfile
# one truth for fabric bounds — the generation limits (constants only;
# no layout logic crosses this import)
from .marker_generation_service import (MAX_HEIGHT_MM, MAX_WIDTH_MM,
                                        MIN_WIDTH_MM)


def _gate(user):
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied('management role required')


@transaction.atomic
def set_fabric_profile(*, user, product, default_width_mm=None,
                       default_length_mm=None, default_spacing_mm=None,
                       fabric_type='', gsm=None, lay_mode=''):
    """Create-or-replace the product's manufacturing defaults.

    FULL-REPLACE semantics (the Hub form posts every field): omitted/None
    clears a default. Idempotent — same values twice = the same single row
    (OneToOne). Bounds reuse the generation constants so a stored default
    can never be a value generation would refuse.
    """
    _gate(user)
    if default_width_mm is not None:
        default_width_mm = int(default_width_mm)
        if not (MIN_WIDTH_MM <= default_width_mm <= MAX_WIDTH_MM):
            raise ValidationError(
                f'default width {default_width_mm} mm outside '
                f'{MIN_WIDTH_MM}..{MAX_WIDTH_MM}.')
    if default_length_mm is not None:
        default_length_mm = int(default_length_mm)
        if not (0 < default_length_mm <= MAX_HEIGHT_MM):
            raise ValidationError('default length must be a positive '
                                  f'length up to {MAX_HEIGHT_MM} mm.')
    if default_spacing_mm is not None:
        if float(default_spacing_mm) < 0:
            raise ValidationError('default spacing cannot be negative.')

    # get_or_create + assign + full_clean: OneToOne = one row per product;
    # full_clean re-checks field-level rules (lengths, non-negatives).
    profile, _created = ProductFabricProfile.objects.get_or_create(
        product=product, defaults={'created_by': user})
    profile.default_width_mm = default_width_mm
    profile.default_length_mm = default_length_mm
    profile.default_spacing_mm = default_spacing_mm
    profile.fabric_type = (fabric_type or '').strip()
    profile.gsm = int(gsm) if gsm is not None else None
    profile.lay_mode = (lay_mode or '').strip()
    profile.full_clean(exclude=['created_by'])
    profile.save()
    return profile
