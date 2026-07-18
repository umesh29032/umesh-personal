"""Phase 7 — SINGLE WRITER for ApprovedLayout (the manufacturing library).

Owner persistence rules: approval = an explicit HUMAN act (rule 8);
rows freeze at approval (rule 1/4 — the model enforces it); history =
append-only supersede chains (rule 5); staleness is DERIVED, never
stored (rule 6); future Adda consumes ONLY this library (rule 9).
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from accounts.services import MANAGEMENT_ROLES, user_has_role
from patterns_ai.models import ApprovedLayout


def _gate(user):
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied('management role required')


@transaction.atomic
def approve_table_layout(*, user, product, candidate, name='',
                         supersedes=None, notes=''):
    """Freeze a saved table draft into a MANUFACTURING ASSET.

    Gates: verified candidate · same product · saved FROM the Cutting
    Table (the ★ generate-tool designation keeps its own frozen flow) ·
    supersede target must be an ACTIVE layout of the same product.
    Never re-verifies geometry, never copies placements — points at the
    immutable candidate (rule 1)."""
    _gate(user)
    if candidate.pk is None:
        raise ValidationError('save the layout first, then approve.')
    if candidate.run.product_id != product.pk:
        raise ValidationError('that layout belongs to a different product.')
    if not (candidate.verification or {}).get('ok'):
        raise ValidationError('unverified layouts can never be approved.')
    params = candidate.run.params or {}
    if not params.get('table'):
        raise ValidationError(
            'only Cutting-Table saves enter the library — the generator '
            'flow keeps its own ★ designation.')
    if ApprovedLayout.objects.filter(candidate=candidate).exists():
        raise ValidationError('this saved draft is already approved — '
                              'approvals are once-only; duplicate the '
                              'layout to change it.')
    if supersedes is not None:
        supersedes = (ApprovedLayout.objects.select_for_update()
                      .get(pk=supersedes.pk))
        if supersedes.product_id != product.pk:
            raise ValidationError('supersede target belongs to a '
                                  'different product.')
        if supersedes.status != ApprovedLayout.Status.ACTIVE:
            raise ValidationError('only ACTIVE layouts can be superseded.')
    seq = (ApprovedLayout.objects.filter(product=product)
           .aggregate(Max('version_no'))['version_no__max'] or 0) + 1
    layout = ApprovedLayout(
        product=product, candidate=candidate,
        layout_uid=f'LAY-{product.code}-{seq:06d}',
        name=(name or '').strip()[:80] or f'{product.code} layout V{seq}',
        version_no=seq,
        fabric_group=params.get('fabric_group', ''),
        supersedes=supersedes,
        status=ApprovedLayout.Status.ACTIVE,
        approved_by=user, approved_at=timezone.now(),
        notes=notes)
    layout.save()
    if supersedes is not None:
        supersedes.status = ApprovedLayout.Status.SUPERSEDED
        supersedes._status_transition = True
        supersedes.save(update_fields=['status', 'updated_at'])
    return layout


@transaction.atomic
def archive_layout(*, user, layout):
    """ACTIVE → ARCHIVED (rule 4's only other verb). Nothing else moves."""
    _gate(user)
    layout = ApprovedLayout.objects.select_for_update().get(pk=layout.pk)
    if layout.status == ApprovedLayout.Status.ARCHIVED:
        return layout                      # idempotent no-op
    layout.status = ApprovedLayout.Status.ARCHIVED
    layout._status_transition = True
    layout.save(update_fields=['status', 'updated_at'])
    return layout


def layout_is_stale(layout):
    """Rule 6 + platform LAW 11: DERIVED, never stored. A layout is
    STALE when any geometry version it froze is no longer the confirmed
    truth (a newer version confirmed since approval)."""
    from patterns_ai.models.pieces import PatternPieceVersion
    version_ids = [p['version_id']
                   for p in (layout.candidate.run.params or {})
                   .get('pieces', []) if p.get('version_id')]
    if not version_ids:
        return False
    return (PatternPieceVersion.objects
            .filter(pk__in=version_ids)
            .exclude(status=PatternPieceVersion.Status.CONFIRMED)
            .exists())
