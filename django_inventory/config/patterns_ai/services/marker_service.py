"""marker_service — THE single writer for Marker rows (ADR-D, I-1).

Why this service exists: markers are append-only knowledge assets with a
status machine, lineage, and globally-unique references. Every creation and
transition — from UI, import, or backfill tooling — enters HERE so the
invariants hold for a decade. Raw ORM writes outside this module are a
review-reject and are guard-tested (tests/test_purity.py).

INVARIANTS (enforced here, mirrored by DB constraints where expressible):
  * reference = unique 'MRK-000001' assigned under advisory lock 5376.
  * usable_width_band = floor(mm/10), stamped at creation, never recomputed.
  * adda is set IFF origin == adda_temporary (D11).
  * lineage (supersedes / benchmarked_against) stays WITHIN one product and
    never points at a rejected marker.
  * status machine (ADR-D):
        candidate  → validated | rejected(r) | retired(r)
        candidate[adda_temporary] → promoted            (D11)
        promoted   → validated | superseded | retired(r)
        validated  → superseded | retired(r)
        rejected / retired / superseded = TERMINAL
    negative transitions REQUIRE a reason (F2; DB CHECK backs it).
  * markers are never edited after creation — supersession creates a NEW row
    and flips the old one to superseded.
"""
import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction

from accounts.services import MANAGEMENT_ROLES, user_has_role

from patterns_ai.models import CaptureAsset, Marker, MarkerTransitionEvent
from .units import width_band

logger = logging.getLogger(__name__)

# Version of the transition rule-set below — stamped on every event so a
# future rule change never makes historical events ambiguous (F3 discipline).
TRANSITIONS_VERSION = 1

# Advisory-lock key for MRK reference allocation — its own domain, disjoint
# from settlement (5374) and pool (5375) locks.
_MRK_REF_LOCK = 5376

_ALLOWED = {
    Marker.Status.CANDIDATE: {Marker.Status.VALIDATED, Marker.Status.REJECTED,
                              Marker.Status.RETIRED, Marker.Status.PROMOTED},
    Marker.Status.PROMOTED: {Marker.Status.VALIDATED, Marker.Status.SUPERSEDED,
                             Marker.Status.RETIRED},
    Marker.Status.VALIDATED: {Marker.Status.SUPERSEDED, Marker.Status.RETIRED},
    Marker.Status.REJECTED: set(),
    Marker.Status.RETIRED: set(),
    Marker.Status.SUPERSEDED: set(),
}
_NEGATIVE = {Marker.Status.REJECTED, Marker.Status.RETIRED}


def _ensure_management(user):
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied('Only management may write marker knowledge.')


def _emit(marker, from_status, to_status, actor, reason='', **meta):
    """Append the immutable transition event (Block 2C). One event per
    status change, creation included — the marker biography's spine."""
    MarkerTransitionEvent.objects.create(
        marker=marker, from_status=from_status, to_status=to_status,
        actor=actor, reason=reason,
        transition_version=TRANSITIONS_VERSION,
        metadata={'schema_version': 1, **meta})


def _next_reference() -> str:
    """MRK-0000001 … gap-tolerant, serialized by the advisory lock."""
    last = (Marker.objects.order_by('-id')
            .values_list('reference', flat=True).first())
    n = 0
    if last and last.startswith('MRK-'):
        try:
            n = int(last.split('-', 1)[1])
        except (ValueError, IndexError):
            n = Marker.objects.count()
    return f'MRK-{n + 1:06d}'


def _check_lineage(product, other, field):
    if other is None:
        return
    other.refresh_from_db(fields=['product', 'status'])   # callers may hold stale rows
    if other.product_id != product.pk:
        raise ValidationError(
            f'{field} must reference a marker of the SAME product '
            f'(got product {other.product_id}).')
    if other.status == Marker.Status.REJECTED:
        raise ValidationError(f'{field} may not point at a rejected marker.')


@transaction.atomic
def create_marker(*, user, product, origin, usable_width_mm,
                  construction=Marker.Construction.UNKNOWN,
                  fabric_group=None, ratio_counts=None, label='', adda=None,
                  supersedes=None, benchmarked_against=None, strategy='',
                  notes='', photo=None, candidate=None,
                  benchmark_evidence=None):
    """Create an immutable marker row (any origin).

    Purpose: the ONLY way a marker is born — UI, import, backfill included.
    Invariants: see module docstring. Creating with `supersedes=` flips the
    old marker to SUPERSEDED in the same transaction (append-only change).
    """
    _ensure_management(user)

    origin = Marker.Origin(origin)
    if (adda is not None) != (origin == Marker.Origin.ADDA_TEMPORARY):
        raise ValidationError(
            'adda must be provided for adda_temporary markers and ONLY for them (D11).')
    if strategy and origin != Marker.Origin.GENERATED:
        raise ValidationError('strategy applies to generated markers only.')
    # P3: promotion linkage — a generated marker carries its immutable
    # candidate; every other origin must not (evidence stays honest).
    if (candidate is not None) != (origin == Marker.Origin.GENERATED):
        raise ValidationError(
            'candidate must be provided for generated markers and ONLY '
            'for them (D11 promotion).')
    if candidate is not None and candidate.run.product_id != product.pk:
        raise ValidationError('candidate belongs to a different product.')
    usable_width_mm = int(usable_width_mm)
    if usable_width_mm <= 0:
        raise ValidationError('usable_width_mm must be positive.')
    _check_lineage(product, supersedes, 'supersedes')
    _check_lineage(product, benchmarked_against, 'benchmarked_against')

    # photo linkage (Block 3B): manual markers ARE their chalk-layout photo.
    if origin == Marker.Origin.MANUAL_PHOTO and photo is None:
        raise ValidationError('A manual marker requires its chalk-layout photo.')
    if photo is not None:
        photo.refresh_from_db(fields=['product', 'kind', 'status'])
        if photo.product_id != product.pk:
            raise ValidationError('Photo belongs to a different product.')
        if photo.kind != CaptureAsset.Kind.MARKER_PHOTO:
            raise ValidationError('Asset is not a marker photo.')
        if photo.status != CaptureAsset.Status.STORED:
            raise ValidationError(
                f'Photo is {photo.get_status_display()} — only stored assets '
                'can back a marker.')
        clash = Marker.objects.filter(photo=photo).first()
        if clash is not None:
            raise ValidationError(
                f'This photo already backs marker {clash.reference} — '
                'one photo, one marker.')

    ratio = {'schema_version': 1,
             'counts': {str(k): int(v) for k, v in (ratio_counts or {}).items()}}

    # serialize reference allocation (transaction-scoped advisory lock)
    with connection.cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(%s)', [_MRK_REF_LOCK])

    marker = Marker.objects.create(
        reference=_next_reference(), product=product, origin=origin, photo=photo,
        fabric_group=fabric_group or Marker._meta.get_field('fabric_group').default,
        usable_width_mm=usable_width_mm,
        usable_width_band=width_band(usable_width_mm),
        construction=construction, ratio=ratio, label=label, adda=adda,
        supersedes=supersedes, benchmarked_against=benchmarked_against,
        strategy=strategy, notes=notes, created_by=user,
        candidate=candidate)

    _emit(marker, '', Marker.Status.CANDIDATE, user,
          origin=str(origin), usable_width_mm=usable_width_mm,
          photo_asset=photo.pk if photo else None,
          candidate=candidate.pk if candidate else None,
          benchmark_evidence=benchmark_evidence)

    if supersedes is not None and supersedes.status not in (
            Marker.Status.SUPERSEDED, Marker.Status.REJECTED, Marker.Status.RETIRED):
        old_status = supersedes.status
        supersedes.status = Marker.Status.SUPERSEDED
        supersedes.status_reason = f'superseded by {marker.reference}'
        supersedes.save(update_fields=['status', 'status_reason', 'updated_at'])
        _emit(supersedes, old_status, Marker.Status.SUPERSEDED, user,
              reason=supersedes.status_reason, superseded_by=marker.reference)

    logger.info('marker.create %s origin=%s product=%s by=%s',
                marker.reference, origin, product.pk, user.pk)
    return marker


@transaction.atomic
def transition_marker(*, user, marker, to_status, reason=''):
    """Move a marker through the append-only status machine.

    Purpose: every status change (validate, promote, retire, reject,
    supersede) is a governed, logged decision — never a field edit.
    Allowed transitions: module docstring table. Negative targets require a
    reason (F2). PROMOTED is reachable only by adda_temporary candidates
    (D11); placement-pin confirmation joins this gate when placements land
    (documented limitation, Block 2B report).
    """
    _ensure_management(user)
    to_status = Marker.Status(to_status)
    marker = Marker.objects.select_for_update().get(pk=marker.pk)

    allowed = _ALLOWED[Marker.Status(marker.status)]
    if to_status not in allowed:
        raise ValidationError(
            f'Illegal transition {marker.status} → {to_status} '
            f'(allowed: {sorted(s.value for s in allowed) or "none — terminal"}).')
    if to_status == Marker.Status.PROMOTED and marker.origin != Marker.Origin.ADDA_TEMPORARY:
        raise ValidationError('Only adda_temporary markers can be PROMOTED (D11).')
    if to_status in _NEGATIVE and not reason.strip():
        raise ValidationError(f'{to_status} requires a reason (decisions are knowledge, F2).')

    from_status = marker.status
    marker.status = to_status
    if reason:
        marker.status_reason = reason.strip()
    marker.save(update_fields=['status', 'status_reason', 'updated_at'])
    _emit(marker, from_status, to_status, user, reason=(reason or '').strip())
    logger.info('marker.transition %s → %s by=%s reason=%r',
                marker.reference, to_status, user.pk, reason)
    return marker
