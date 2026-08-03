"""Phase 8A — SINGLE WRITER for ApprovedLayoutUsage.

Owner freezes: F1 history forever (void, never delete/reassign) ·
F2 pointer-only (derivation helpers here compute FROM the layout at
read; nothing is copied or stored) · F3 the recorded layout = the
manufacturing CONTRACT for that (adda, fabric group).
Rule 9 becomes code-law here: the writer accepts ONLY the library —
ACTIVE, non-stale, same-product approved layouts.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.services import MANAGEMENT_ROLES, user_has_role
from patterns_ai.models import ApprovedLayout, ApprovedLayoutUsage

from .layout_library_service import layout_is_stale


def _gate(user):
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied('management role required')


@transaction.atomic
def record_usage(*, user, adda, layout):
    """Link an Adda to its manufacturing contract for one fabric group.

    Refuses: non-ACTIVE layouts · STALE layouts (LAW 11's enforcement
    point — frozen geometry no longer the confirmed truth) · layouts of
    another product · a second active contract for the same
    (adda, fabric group). Wrong pick later = void_usage + record again
    (refinement 1 — never reassign)."""
    _gate(user)
    layout = (ApprovedLayout.objects.select_for_update()
              .select_related('candidate__run')
              .get(pk=layout.pk))
    if layout.status != ApprovedLayout.Status.ACTIVE:
        raise ValidationError(
            f'{layout.layout_uid} is {layout.get_status_display()} — only '
            'ACTIVE layouts can be manufactured.')
    if layout_is_stale(layout):
        raise ValidationError(
            f'{layout.layout_uid} is STALE (LAW 11): a frozen geometry '
            'version is no longer the confirmed truth. Supersede it with '
            'a fresh approved layout before manufacturing.')
    if layout.product_id != adda.product_id:
        raise ValidationError(
            f'{layout.layout_uid} belongs to a different product.')
    clash = (ApprovedLayoutUsage.objects
             .filter(adda=adda, fabric_group=layout.fabric_group,
                     voided_at__isnull=True)
             .select_related('layout').first())
    if clash is not None:
        raise ValidationError(
            f'this Adda already manufactures {layout.fabric_group.upper()} '
            f'from {clash.layout.layout_uid} — void that usage first '
            '(history is kept), then record the new one.')
    return ApprovedLayoutUsage.objects.create(
        layout=layout, adda=adda,
        fabric_group=layout.fabric_group,   # F2's one sanctioned denorm
        recorded_by=user)


@transaction.atomic
def void_usage(*, user, usage, reason):
    """Stop using a layout — the record STAYS (F1). Reason mandatory."""
    _gate(user)
    reason = (reason or '').strip()
    if not reason:
        raise ValidationError('a void reason is required — manufacturing '
                              'history explains itself.')
    usage = (ApprovedLayoutUsage.objects.select_for_update()
             .get(pk=usage.pk))
    if usage.voided_at is not None:
        return usage                        # idempotent no-op
    usage.voided_at = timezone.now()
    usage.void_reason = reason[:200]
    usage._service_transition = True
    usage.save(update_fields=['voided_at', 'void_reason', 'updated_at'])
    return usage


@transaction.atomic
def stamp_stage_record(*, usage, stage_record):
    """8D audit join: pin the usage to the exact pattern-stage record.
    Stamps once; a different SR on a stamped usage is refused (the
    history never rewrites)."""
    usage = (ApprovedLayoutUsage.objects.select_for_update()
             .get(pk=usage.pk))
    if usage.stage_record_id == stage_record.pk:
        return usage                        # idempotent
    if usage.stage_record_id is not None:
        raise ValidationError('this usage is already stamped to a stage '
                              'record — history never rewrites.')
    usage.stage_record = stage_record
    usage._service_transition = True
    usage.save(update_fields=['stage_record', 'updated_at'])
    return usage


# ── derive-at-read helpers (F2/F3 + owner refinement 3: expected pieces
#    are NEVER stored — always computed from the frozen layout) ─────────

def layer_multiplier(layout):
    """M4 G3: plies each laid layer of this marker yields (1 = single,
    2 = double/tubular). A frozen LAYOUT fact from the saved Marker
    Plan; pre-M4 layouts have no key → 1 (byte-identical behavior)."""
    try:
        return max(1, int((layout.candidate.run.params or {})
                          .get('layer_multiplier', 1)))
    except (TypeError, ValueError):
        return 1


def marker_content(layout):
    """Per-size piece counts of the approved marker PER LAID LAYER:
    stored placements counted (design_key = 'piece:size') × the
    layout's layer multiplier (G3 — a double lay cuts 2 per placement).
    M4.5 fold: a placement flagged on_fold OPENS across the crease —
    it yields multiplier÷2 pieces (1 on a double lay; integer by
    construction, fold placements exist only where multiplier is 2).
    Legacy placements carry no flag ⇒ exact M4 math."""
    mult = layer_multiplier(layout)
    counts = {}
    for p in (layout.candidate.placements or {}).get('placements', []):
        try:
            size_id = int(str(p['key']).split(':')[1])
        except (KeyError, IndexError, ValueError):
            continue
        ppp = mult // 2 if p.get('on_fold') else mult
        counts[size_id] = counts.get(size_id, 0) + max(1, ppp)
    return counts


def expected_pieces(usage, lay_count):
    """The manufacturing contract's numbers: marker content × plies.
    lay_count = LayeringRecord.lay_count (the ONE plies truth,
    readiness R-2). Computed, never persisted (refinement 3)."""
    lay = max(0, int(lay_count or 0))
    return {size_id: n * lay
            for size_id, n in marker_content(usage.layout).items()}


def stamp_adda_usages(adda, stage_record):
    """M6 cutting-completion listener body: pin every ACTIVE un-stamped
    usage of this Adda to the completed cutting stage record (once-only
    traceability — which cut used which asset). Called via production's
    CUTTING_COMPLETE_LISTENERS registry; the caller isolates failures."""
    for usage in (ApprovedLayoutUsage.objects
                  .filter(adda=adda, voided_at__isnull=True,
                          stage_record__isnull=True)):
        stamp_stage_record(usage=usage, stage_record=stage_record)
