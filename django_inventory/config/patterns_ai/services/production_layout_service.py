"""production_layout_service — SINGLE WRITER for ProductionLayout
(🔒 Phase-6 M3 frozen API; INTEGRATION_DESIGN §3g/§3h/§3i).

Approve = the explicit, audited, separate act. It validates ELIGIBILITY
and moves the pointer — nothing else. Rule A (owner-locked) eligibility:
belongs to the supplied product · immutable saved layout · already
verified (verification.ok) · exportable (has pieces). Approval NEVER
performs verification itself and never touches any layout row; history =
the immutable saved layouts + this row's audit fields.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.services import MANAGEMENT_ROLES, user_has_role

from patterns_ai.models import ProductionLayout


def _gate(user):
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied('management role required')


@transaction.atomic
def approve_production_layout(*, user, product, layout):
    """Designate ONE saved layout as what production cuts from.

    Same-layout re-approve = strict no-op (F-3): the first-approval
    audit fact is preserved, nothing restamps. A different layout moves
    the pointer with a fresh approved_by/approved_at. Atomic; the
    OneToOne unique constraint is the DB backstop against races.
    """
    _gate(user)
    # Rule A — eligibility only (approval never re-verifies):
    if layout is None or layout.pk is None:
        raise ValidationError('only a saved layout can be approved.')
    if layout.run.product_id != product.pk:
        raise ValidationError('that layout belongs to a different product.')
    if not (layout.verification or {}).get('ok'):
        raise ValidationError('that layout is not verified — only '
                              'verified saved layouts can go to production.')
    if not ((layout.placements or {}).get('placements') or []):
        raise ValidationError('that layout has no pieces to cut — '
                              'nothing to export.')

    # select_for_update: the designation row is the only lock needed;
    # layouts themselves are immutable so nothing else can race.
    designation, created = (
        ProductionLayout.objects.select_for_update().get_or_create(
            product=product,
            defaults={'approved_layout': layout, 'approved_by': user,
                      'approved_at': timezone.now()}))
    if created or designation.approved_layout_id == layout.pk:
        return designation
    designation.approved_layout = layout
    designation.approved_by = user
    designation.approved_at = timezone.now()
    designation.save(update_fields=['approved_layout', 'approved_by',
                                    'approved_at', 'updated_at'])
    return designation
