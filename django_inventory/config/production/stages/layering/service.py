"""Layering stage service — Stage 1 lifecycle.

YEH FILE KYU HAI?
─────────────────
Stage 1 (Layering) ka SAARA service logic yahan. Future stages cutting_service.py,
packing_service.py, etc same shape mein. Sirf state transitions + DB writes — no
HTTP, no template, no form parsing.

Public funcs (call order during a typical Adda):
  start_layering(adda, worker_ids, user)
  attach_roll_to_layering(stage_record, roll, width, weight, ..., user)
  update_layering_roll_entry(entry, ..., user)
  detach_roll_from_layering(entry, user)
  save_layering_breakup(entry, layers, leftover_*, user)           # single-entry breakup save
  save_layering_draft(adda, header_*, per_entry_data, user)        # bulk breakup + header draft save
  record_remaining_cloth(entry, weight, length, user)              # extra leftover piece
  remove_remaining_cloth(leftover, user)
  complete_layering(adda, ..., user)
  sync_layering_workers_for_skill(user)                            # signal handler hook

Side effects in save_layering_breakup / save_layering_draft / complete_layering:
  • LayeringRollEntry.layers_on_roll updated
  • RemainingClothOfClothRoll upserted (primary leftover)
  • ClothRoll.remaining_length_meters / remaining_weight_kg denormalized
  • On complete: ClothRoll.layers_on_roll + layer_length_meters copied; LayeringRecord created
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from django.db.models import Count, Sum

from production.constants import STAGE_LAYERING
from production.models import (
    Adda, AddaStageRecord, LayeringRecord, LayeringRollEntry,
    RemainingClothOfClothRoll,
)
from production.services.adda_service import advance_to_next_stage

# Absolute import — _shared stays in production/services/ (shared across stages);
# this module moved into stages/layering/ (M2.8).
from production.services._shared import (
    _ensure_assigned_worker,
    _ensure_can_complete_layering,
    _ensure_can_manage,
    _ensure_layering_skill,
    _ensure_management,
    downstream_started_guard,
    reopen_stage_record,
)

logger = logging.getLogger(__name__)


# ── Public summary helper (used by 3 dashboard surfaces) ────────────────────


def get_layering_snapshot(adda) -> dict:
    """Return a normalized snapshot of Layering stage data for any Adda.

    Used by:
      • Adda dashboard Recent Addas table (compact summary per row)
      • Adda Detail page (full summary card above tabs)
      • User Dashboard Active Addas list (compact summary per Adda card)

    Returns dict with the same shape regardless of stage state — caller branches
    on `state` to render. Lightweight: 2-3 small queries.

    Keys:
      state           'not_started' | 'in_progress' | 'completed' | 'absent'
      stage_record    AddaStageRecord | None
      lay_count       int | None     (sum of per-roll layers, both pre + post complete)
      layer_length    Decimal | None (overall meters)
      duration_min    int | None
      total_colors    int | None
      rolls_count     int            (attached rolls so far)
      leftover_length_sum  Decimal   (across all rolls)
      leftover_weight_sum  Decimal   (across all rolls)
      total_fabric_used    Decimal | None (lay_count × layer_length, set only post-complete)
      started_at      datetime | None
      completed_at    datetime | None
      completed_by    User | None
      workers         queryset       (assigned worker users)
      record          LayeringRecord | None  (only when completed)
    """
    from decimal import Decimal

    snap = {
        'state': 'absent',
        'stage_record': None,
        'lay_count': None,
        'layer_length': None,
        'duration_min': None,
        'total_colors': None,
        'rolls_count': 0,
        'leftover_length_sum': Decimal('0'),
        'leftover_weight_sum': Decimal('0'),
        'total_fabric_used': None,
        'started_at': None,
        'completed_at': None,
        'completed_by': None,
        'workers': AddaStageRecord.objects.none(),
        'record': None,
    }

    # Locate the Layering stage_record (if any). If product has no layering stage,
    # snapshot stays 'absent' — defensive for future workflow variants.
    layering_stage = adda.product.workflow_stages.filter(
        stage__code=STAGE_LAYERING
    ).first()
    if layering_stage is None:
        return snap

    sr = (
        AddaStageRecord.objects
        .filter(adda=adda, workflow_stage=layering_stage)
        .select_related('completed_by')
        .prefetch_related('worker_tasks__worker')   # V2-1b: feeds active_workers (no N+1)
        .first()
    )
    if sr is None:
        snap['state'] = 'not_started'
        return snap

    snap['stage_record'] = sr
    snap['started_at'] = sr.started_at
    snap['workers'] = sr.active_workers   # V2-1b: live (non-cancelled) workers from tasks

    # Aggregates from entries (works pre + post complete)
    entry_agg = sr.layering_roll_entries.aggregate(
        rolls=Count('id'),
        layers=Sum('layers_on_roll'),
    )
    snap['rolls_count'] = entry_agg['rolls'] or 0
    snap['lay_count'] = entry_agg['layers']  # may be None if no row has layers set yet

    # Leftover aggregates across all attached entries' primary remaining_pieces
    leftover_agg = RemainingClothOfClothRoll.objects.filter(
        layering_entry__stage_record=sr,
    ).aggregate(
        len_sum=Sum('remaining_length_meters'),
        wt_sum=Sum('remaining_weight_kg'),
    )
    snap['leftover_length_sum'] = leftover_agg['len_sum'] or Decimal('0')
    snap['leftover_weight_sum'] = leftover_agg['wt_sum'] or Decimal('0')

    if sr.completed_at is None:
        snap['state'] = 'in_progress'
        # Show draft header values while in progress (so dashboards reflect WIP)
        snap['layer_length'] = sr.draft_layer_length_meters
        snap['duration_min'] = sr.draft_duration_minutes
        return snap

    # Completed branch
    snap['state'] = 'completed'
    snap['completed_at'] = sr.completed_at
    snap['completed_by'] = sr.completed_by
    lr = getattr(sr, 'layering', None)
    if lr is not None:
        snap['record'] = lr
        snap['lay_count'] = lr.lay_count
        snap['layer_length'] = lr.layer_length_meters
        snap['duration_min'] = lr.duration_minutes
        snap['total_colors'] = lr.total_colors
        snap['total_fabric_used'] = lr.total_fabric_used_meters
    return snap


# ── Helpers internal to layering ─────────────────────────────────────────────


def _sync_roll_leftover(roll, leftover: RemainingClothOfClothRoll | None) -> None:
    """Denormalize leftover values onto the ClothRoll. Called from breakup save.

    Single source: the primary (most recent non-consumed) leftover row's values
    copy onto roll.remaining_length_meters + roll.remaining_weight_kg. If no
    leftover row exists or it's consumed, NULL out the roll fields.
    """
    if leftover is None or leftover.is_consumed:
        if roll.remaining_length_meters is not None or roll.remaining_weight_kg is not None:
            roll.remaining_length_meters = None
            roll.remaining_weight_kg = None
            roll.save(update_fields=['remaining_length_meters', 'remaining_weight_kg'])
        return
    roll.remaining_length_meters = leftover.remaining_length_meters
    roll.remaining_weight_kg = leftover.remaining_weight_kg
    roll.save(update_fields=['remaining_length_meters', 'remaining_weight_kg'])


# ── Worker assignment + retro-tag ────────────────────────────────────────────


@transaction.atomic
def start_layering(*, adda: Adda, worker_ids: list[int], user) -> AddaStageRecord:
    """Manager refines workers. After Phase 4 semantic = "update workers".

    Adda creation already provisions the stage_record (auto-populated with
    skilled users). This function lets manager override that list.
    """
    _ensure_management(user)
    stage = adda.current_stage
    if stage is None or stage.stage_type != STAGE_LAYERING:
        raise ValidationError("Adda is not at Layering stage")
    if adda.status != Adda.Status.IN_PROGRESS:
        raise ValidationError(f"Adda {adda.code} is not in-progress")
    if not worker_ids:
        raise ValidationError("Assign at least one worker")

    from accounts.models import User
    from accounts.skills import SKILL_CUTTING_MASTER

    has_master = User.objects.filter(
        pk__in=worker_ids, skills__name=SKILL_CUTTING_MASTER,
    ).exists()
    if not has_master:
        raise ValidationError(
            "At least one assigned worker must have the 'cutting_master' skill"
        )

    sr, created = AddaStageRecord.objects.get_or_create(
        adda=adda, workflow_stage=stage,
        defaults={'started_at': timezone.now()},
    )
    if not created and sr.completed_at is not None:
        raise ValidationError("Layering stage already completed for this Adda")
    if not created and sr.started_at is None:
        sr.started_at = timezone.now()
        sr.save(update_fields=['started_at'])
    from production.services.worker_task_service import set_stage_workers
    set_stage_workers(sr, worker_ids)   # dual-write: M2M (authoritative) + WorkerStageTask
    from tracking.services import log_adda
    from tracking.models import AddaHistory
    log_adda(adda, AddaHistory.ChangeType.WORKERS_ASSIGNED, user,
             stage_record=sr, metadata={'worker_ids': list(worker_ids)})
    return sr


def sync_layering_workers_for_skill(user) -> int:
    """Retro-tag: new skilled user → added to workers M2M on every active Layering.

    Side effects:
      • AddaStageRecord.workers (M2M) — adds `user` to every active Layering stage_record
      • Cross-app read: accounts.skills.user_has_skill (gate)
    """
    from accounts.skills import SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER, user_has_skill
    if not user_has_skill(user, [SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER]):
        return 0

    active_srs = AddaStageRecord.objects.filter(
        workflow_stage__stage__code=STAGE_LAYERING,
        started_at__isnull=False,
        completed_at__isnull=True,
        adda__status=Adda.Status.IN_PROGRESS,
    )
    count = 0
    from production.services.worker_task_service import add_stage_worker
    for sr in active_srs:
        add_stage_worker(sr, user)   # additive dual-write (re-tag); not a full replace
        count += 1
    logger.info("layering.workers_retro_tag worker_id=%s tagged_stage_records=%s", user.pk, count)
    return count


# ── Roll attach / edit / detach ─────────────────────────────────────────────


@transaction.atomic
def attach_roll_to_layering(
    *,
    stage_record: AddaStageRecord,
    roll,
    width_verified_inch: int,
    weight_verified_kg: Decimal,
    notes: str = '',
    user,
) -> LayeringRollEntry:
    """Worker attaches cloth roll. ClothRoll.status flips USED via shared service.

    Side effects:
      • LayeringRollEntry — created (one per attached roll)
      • ClothRoll — status→USED, adda/used_at/used_by set (via raw_materials.assign_roll_to_adda)
      • Cross-app service: raw_materials.services.assign_roll_to_adda (also logs ClothRollHistory)
    """
    _ensure_assigned_worker(stage_record, user)
    _ensure_layering_skill(user)

    stage_record.refresh_from_db(fields=['completed_at'])
    if stage_record.completed_at is not None:
        raise ValidationError("Layering stage already completed — cannot attach more rolls")
    if stage_record.workflow_stage.stage_type != STAGE_LAYERING:
        raise ValidationError("Stage record is not a layering stage")
    if width_verified_inch is None or width_verified_inch < 1:
        raise ValidationError("Verified width is required")
    if weight_verified_kg is None or Decimal(weight_verified_kg) <= 0:
        raise ValidationError("Verified weight must be > 0")

    from raw_materials.services import assign_roll_to_adda
    adda_obj = stage_record.adda.__class__.objects.get(pk=stage_record.adda_id)
    assign_roll_to_adda(
        user, roll=roll, adda=adda_obj,
        weight_kg=Decimal(weight_verified_kg),
        width_inch=int(width_verified_inch),
    )
    entry = LayeringRollEntry.objects.create(
        stage_record=stage_record,
        roll=roll,
        width_verified_inch=int(width_verified_inch),
        weight_verified_kg=Decimal(weight_verified_kg),
        notes=notes or '',
        attached_by=user,
    )
    logger.info(
        "layering.roll_attach adda=%s roll=%s entry=%s width_inch=%s weight_kg=%s user_id=%s",
        stage_record.adda.code, roll.roll_id, entry.pk,
        int(width_verified_inch), Decimal(weight_verified_kg), user.pk,
    )
    return entry


@transaction.atomic
def update_layering_roll_entry(
    *,
    entry: LayeringRollEntry,
    width_verified_inch: int | None,
    weight_verified_kg: Decimal | None,
    notes: str | None,
    layers_on_roll: int | None = None,
    user,
) -> LayeringRollEntry:
    """Corrects an existing entry. ClothRoll fields sync where relevant."""
    _ensure_assigned_worker(entry.stage_record, user)
    _ensure_layering_skill(user)
    if entry.stage_record.completed_at is not None:
        raise ValidationError("Cannot edit roll entry after layering completion")

    roll = entry.roll
    roll_dirty: list[str] = []
    if width_verified_inch is not None:
        if width_verified_inch < 1:
            raise ValidationError("Verified width must be >= 1")
        entry.width_verified_inch = int(width_verified_inch)
        roll.width_inch = int(width_verified_inch)
        roll_dirty.append('width_inch')
    if weight_verified_kg is not None:
        weight_dec = Decimal(weight_verified_kg)
        if weight_dec <= 0:
            raise ValidationError("Verified weight must be > 0")
        entry.weight_verified_kg = weight_dec
        roll.weight_kg = weight_dec
        roll_dirty.append('weight_kg')
    if layers_on_roll is not None:
        if int(layers_on_roll) < 1:
            raise ValidationError("layers_on_roll must be >= 1")
        entry.layers_on_roll = int(layers_on_roll)
    if notes is not None:
        entry.notes = notes

    entry.save(update_fields=[
        'width_verified_inch', 'weight_verified_kg', 'layers_on_roll', 'notes', 'updated_at',
    ])
    if roll_dirty:
        roll.save(update_fields=roll_dirty)
    return entry


@transaction.atomic
def detach_roll_from_layering(*, entry: LayeringRollEntry, user) -> None:
    """Deletes entry + flips ClothRoll.status back to NOT_USED.

    Side effects:
      • ClothRoll — status→NOT_USED, adda/used_at/used_by cleared
      • LayeringRollEntry — deleted
      • Cross-app service: tracking.services.log_roll (ClothRollHistory) + log_adda (AddaHistory)
    """
    _ensure_assigned_worker(entry.stage_record, user)
    _ensure_layering_skill(user)
    if entry.stage_record.completed_at is not None:
        raise ValidationError("Cannot detach roll after layering completion")

    roll = entry.roll
    from raw_materials.models import ClothRoll
    roll.status = ClothRoll.Status.NOT_USED
    roll.adda = None
    roll.used_at = None
    roll.used_by = None
    roll.save(update_fields=['status', 'adda', 'used_at', 'used_by'])

    from tracking.services import log_roll, log_adda
    from tracking.models import ClothRollHistory, AddaHistory
    log_roll(
        roll, ClothRollHistory.ChangeType.STATUS_CHANGED, user,
        field_name='status', old_value='used', new_value='not_used',
        note=f"detached from {entry.stage_record.adda.code} layering",
    )
    log_adda(
        entry.stage_record.adda, AddaHistory.ChangeType.ROLL_REMOVED, user,
        roll=roll, note='detached from layering',
    )
    logger.info(
        "layering.roll_detach adda=%s roll=%s entry=%s user_id=%s",
        entry.stage_record.adda.code, roll.roll_id, entry.pk, user.pk,
    )
    entry.delete()


# ── Per-row breakup save (single entry) ─────────────────────────────────────


@transaction.atomic
def save_layering_breakup(
    *,
    entry: LayeringRollEntry,
    layers_on_roll: int,
    leftover_weight_kg: Decimal,
    leftover_length_meters: Decimal | None = None,
    notes: str = '',
    user,
) -> tuple[LayeringRollEntry, RemainingClothOfClothRoll]:
    """Single-shot save for one breakup row: layers + primary leftover.

    Worker screen captures leftover WEIGHT only (owner decision 2026-06-03);
    `leftover_length_meters` is optional and defaults to 0. Denormalizes leftover
    onto ClothRoll so cloth dashboards show it without joining RemainingCloth.
    """
    _ensure_assigned_worker(entry.stage_record, user)
    _ensure_layering_skill(user)

    if entry.stage_record.completed_at is not None:
        raise ValidationError("Layering stage already completed — breakup is locked")
    if layers_on_roll is None or int(layers_on_roll) < 1:
        raise ValidationError("Layers must be >= 1")
    if leftover_weight_kg is None or Decimal(leftover_weight_kg) < 0:
        raise ValidationError("Leftover weight must be >= 0")
    # Length optional now (weight-only capture). Default 0; reject only negatives.
    leftover_length_meters = Decimal(leftover_length_meters) if leftover_length_meters is not None else Decimal('0')
    if leftover_length_meters < 0:
        raise ValidationError("Leftover length must be >= 0")

    entry.layers_on_roll = int(layers_on_roll)
    entry.save(update_fields=['layers_on_roll', 'updated_at'])

    # Upsert primary leftover (most recent non-consumed)
    primary = entry.remaining_pieces.order_by('-created_at').first()
    if primary is None or primary.is_consumed:
        primary = RemainingClothOfClothRoll.objects.create(
            roll=entry.roll,
            source_adda=entry.stage_record.adda,
            layering_entry=entry,
            remaining_weight_kg=Decimal(leftover_weight_kg),
            remaining_length_meters=Decimal(leftover_length_meters),
            notes=notes or '',
            created_by=user,
        )
    else:
        primary.remaining_weight_kg = Decimal(leftover_weight_kg)
        primary.remaining_length_meters = Decimal(leftover_length_meters)
        if notes:
            primary.notes = notes
        primary.save(update_fields=[
            'remaining_weight_kg', 'remaining_length_meters', 'notes', 'updated_at',
        ])

    # Denormalize leftover onto the roll
    _sync_roll_leftover(entry.roll, primary)
    return entry, primary


# ── Bulk draft save (header + all rows in one call) ─────────────────────────


@transaction.atomic
def save_layering_draft(
    *,
    adda: Adda,
    layer_length_meters: Decimal | None,
    duration_minutes: int | None,
    notes: str | None,
    per_entry_data: dict[int, dict],
    user,
) -> AddaStageRecord:
    """Save Section 04 draft state — header fields + per-row breakup in one call.

    `per_entry_data` shape: {entry_pk: {layers, leftover_length, leftover_weight, notes}}.
    Only entries present in the dict get touched. Missing entries left alone
    (user can save partial progress). Lax validation — only reject obviously
    invalid values (negative, < 1 layers when provided).

    Header values (layer_length, duration, notes) saved onto AddaStageRecord
    draft_* fields. Cleared on complete.

    Use complete_layering for the final advance.
    """
    _ensure_can_manage(user)

    stage = adda.current_stage
    if stage is None or stage.stage_type != STAGE_LAYERING:
        raise ValidationError("Adda is not at Layering stage")
    if adda.status != Adda.Status.IN_PROGRESS:
        raise ValidationError(f"Adda {adda.code} is not in-progress")

    try:
        sr = AddaStageRecord.objects.get(adda=adda, workflow_stage=stage)
    except AddaStageRecord.DoesNotExist:
        raise ValidationError("Layering stage hasn't been started yet")
    if sr.completed_at is not None:
        raise ValidationError("Layering stage already completed — draft locked")

    # Save header drafts (any None = skip that field). Lax — partial drafts OK.
    dirty_header: list[str] = []
    if layer_length_meters is not None:
        ll = Decimal(layer_length_meters)
        if ll < 0:
            raise ValidationError("layer_length_meters must be >= 0")
        sr.draft_layer_length_meters = ll
        dirty_header.append('draft_layer_length_meters')
    if duration_minutes is not None:
        dm = int(duration_minutes)
        if dm < 0:
            raise ValidationError("duration_minutes must be >= 0")
        sr.draft_duration_minutes = dm
        dirty_header.append('draft_duration_minutes')
    if notes is not None:
        sr.draft_notes = notes
        dirty_header.append('draft_notes')
    if dirty_header:
        sr.save(update_fields=dirty_header)

    # Save per-row data via save_layering_breakup (which also denormalizes leftover).
    # Skip entries with all-None values; tolerate partial fills as long as we have a layers count.
    entries_by_pk = {
        e.pk: e for e in sr.layering_roll_entries.select_related('roll').all()
    }
    for pk, data in per_entry_data.items():
        if pk not in entries_by_pk:
            continue   # silently skip unknown entry pks
        entry = entries_by_pk[pk]
        layers = data.get('layers')
        leftover_len = data.get('leftover_length')   # optional now (weight-only capture)
        leftover_wt = data.get('leftover_weight')
        # Persist a row once we have layers + leftover weight; length defaults 0.
        if layers is None or leftover_wt is None:
            continue
        try:
            save_layering_breakup(
                entry=entry,
                layers_on_roll=layers,
                leftover_weight_kg=leftover_wt,
                leftover_length_meters=leftover_len,
                notes=data.get('notes', ''),
                user=user,
            )
        except ValidationError:
            # Lax — single bad row doesn't fail the whole draft. Skip it.
            continue
    return sr


# ── Leftover bookkeeping (extra pieces beyond primary) ──────────────────────


@transaction.atomic
def record_remaining_cloth(
    *,
    entry: LayeringRollEntry,
    remaining_weight_kg: Decimal,
    remaining_length_meters: Decimal,
    notes: str = '',
    user,
) -> RemainingClothOfClothRoll:
    """Append an additional leftover piece. Used for multi-piece edge cases.

    Side effects:
      • RemainingClothOfClothRoll — created (extra leftover piece)
      • ClothRoll.remaining_length_meters / remaining_weight_kg — re-denormalized via _sync_roll_leftover
    """
    _ensure_assigned_worker(entry.stage_record, user)
    _ensure_layering_skill(user)

    if remaining_weight_kg is None or Decimal(remaining_weight_kg) < 0:
        raise ValidationError("Remaining weight must be >= 0 (use 0 for 'no leftover')")
    if remaining_length_meters is None or Decimal(remaining_length_meters) < 0:
        raise ValidationError("Remaining length must be >= 0 (use 0 for 'no leftover')")

    lo = RemainingClothOfClothRoll.objects.create(
        roll=entry.roll,
        source_adda=entry.stage_record.adda,
        layering_entry=entry,
        remaining_weight_kg=Decimal(remaining_weight_kg),
        remaining_length_meters=Decimal(remaining_length_meters),
        notes=notes or '',
        created_by=user,
    )
    # Re-denormalize the roll (this row may now be the most recent)
    _sync_roll_leftover(entry.roll, lo)
    logger.info(
        "layering.remaining_cloth_record adda=%s roll=%s entry=%s leftover=%s weight_kg=%s length_m=%s user_id=%s",
        entry.stage_record.adda.code, entry.roll.roll_id, entry.pk, lo.pk,
        Decimal(remaining_weight_kg), Decimal(remaining_length_meters), user.pk,
    )
    return lo


@transaction.atomic
def remove_remaining_cloth(*, leftover: RemainingClothOfClothRoll, user) -> None:
    """Delete leftover entry. Blocked if leftover.is_consumed (historical record)."""
    if leftover.layering_entry is not None:
        _ensure_assigned_worker(leftover.layering_entry.stage_record, user)
    else:
        _ensure_management(user)
    _ensure_layering_skill(user)
    if leftover.is_consumed:
        raise ValidationError("Leftover already consumed in another Adda; cannot delete")
    roll = leftover.roll
    leftover.delete()
    # Refresh denorm from the new primary (if any remains)
    new_primary = roll.remaining_pieces.order_by('-created_at').first()
    _sync_roll_leftover(roll, new_primary)


# ── Completion ───────────────────────────────────────────────────────────────


@transaction.atomic
def complete_layering(
    *,
    adda: Adda,
    duration_minutes: int,
    layer_length_meters: Decimal,
    per_entry_layers: dict[int, int],
    notes: str,
    user,
) -> LayeringRecord:
    """Finalize Layering → advance to Cutting.

    Validates: layers per entry, leftover per entry, layer_length, duration.
    Propagates layer metrics to each used ClothRoll. Clears stage draft_*
    fields. Creates LayeringRecord summary.

    Side effects:
      • LayeringRollEntry.layers_on_roll — set per entry
      • ClothRoll.layers_on_roll / layer_length_meters — copied per used roll
      • AddaStageRecord — completed_at/completed_by set, draft_* cleared
      • LayeringRecord — created (summary) + rolls_used M2M set
      • Cross-app/service: adda_service.advance_to_next_stage (advances Adda → Cutting;
        also triggers stage cost freeze + AddaHistory logging downstream)
    """
    _ensure_can_manage(user)
    _ensure_can_complete_layering(user)

    stage = adda.current_stage
    if stage is None or stage.stage_type != STAGE_LAYERING:
        raise ValidationError("Adda is not at Layering stage")
    if adda.status != Adda.Status.IN_PROGRESS:
        raise ValidationError(f"Adda {adda.code} is not in-progress")
    if duration_minutes is None or int(duration_minutes) < 1:
        raise ValidationError("duration_minutes must be >= 1")
    layer_length_dec = Decimal(layer_length_meters) if layer_length_meters is not None else None
    if layer_length_dec is None or layer_length_dec <= 0:
        raise ValidationError("layer_length_meters must be > 0")

    try:
        # WF-4: lock the stage row so a concurrent completer blocks here and then
        # sees completed_at set below — prevents double-advance / double-freeze.
        sr = AddaStageRecord.objects.select_for_update().get(adda=adda, workflow_stage=stage)
    except AddaStageRecord.DoesNotExist:
        raise ValidationError("Layering stage hasn't been started yet")
    if sr.completed_at is not None:
        raise ValidationError("Layering stage already completed")

    entries = list(
        sr.layering_roll_entries
        .select_related('roll')
        .prefetch_related('remaining_pieces')
        .all()
    )
    if not entries:
        raise ValidationError("Attach at least one cloth roll before completing Layering")

    entry_ids = {e.pk for e in entries}
    missing = entry_ids - set(per_entry_layers.keys())
    if missing:
        raise ValidationError(
            f"Layer count missing for {len(missing)} roll(s). Fill the breakup table for every attached roll."
        )
    for pk, count in per_entry_layers.items():
        if pk not in entry_ids:
            raise ValidationError(f"Unknown entry pk={pk} in breakup")
        if not isinstance(count, int) or count < 1:
            raise ValidationError(f"Layer count for entry {pk} must be a positive integer")

    missing_leftover = [e.roll.roll_id for e in entries if not list(e.remaining_pieces.all())]
    if missing_leftover:
        raise ValidationError(
            "Record leftover cloth for every roll before completing Layering. "
            "Missing: " + ', '.join(missing_leftover)
        )

    lay_count_total = sum(per_entry_layers.values())

    roll_ids = []
    for e in entries:
        e.layers_on_roll = per_entry_layers[e.pk]
        e.save(update_fields=['layers_on_roll', 'updated_at'])
        e.roll.layers_on_roll = per_entry_layers[e.pk]
        e.roll.layer_length_meters = layer_length_dec
        e.roll.save(update_fields=['layers_on_roll', 'layer_length_meters'])
        roll_ids.append(e.roll_id)

    total_colors = (
        sr.layering_roll_entries.values('roll__cloth_color').distinct().count()
    )

    sr.completed_at = timezone.now()
    sr.completed_by = user
    # Clear draft fields — they're no longer needed once complete
    sr.draft_layer_length_meters = None
    sr.draft_duration_minutes = None
    sr.draft_notes = ''
    sr.save(update_fields=[
        'completed_at', 'completed_by',
        'draft_layer_length_meters', 'draft_duration_minutes', 'draft_notes',
    ])

    lr = LayeringRecord.objects.create(
        stage_record=sr,
        lay_count=lay_count_total,
        total_colors=total_colors,
        duration_minutes=int(duration_minutes),
        layer_length_meters=layer_length_dec,
        notes=notes or '',
    )
    lr.rolls_used.set(roll_ids)

    advance_to_next_stage(adda, user)
    logger.info(
        "layering.complete adda=%s record=%s lay_count=%s rolls=%s total_colors=%s "
        "layer_length_m=%s duration_min=%s user_id=%s",
        adda.code, lr.pk, lay_count_total, len(roll_ids), total_colors,
        layer_length_dec, int(duration_minutes), user.pk,
    )
    return lr


@transaction.atomic
def reopen_layering(*, adda: Adda, user) -> AddaStageRecord:
    """Admin-only: completed Layering stage ko correction ke liye unlock.

    YEH KAB ZAROORAT PADTI HAI?
      Manager/Helper ne galti se complete kar diya, ya values galat fill
      ki — admin "Edit / Reopen" button click karke stage wapas in-progress
      kar deta hai. Workers + attached rolls + per-roll layers + leftover
      preserve rehte hain (sirf typed LayeringRecord delete hota hai).

    ROLLBACK KARTA HAI:
      • adda.current_stage  → Layering WorkflowStage pe wapas
      • stage_record.completed_at / completed_by → cleared (sr active again)
      • LayeringRecord summary → deleted (re-create hoga next complete)
      • adda.status → IN_PROGRESS (agar COMPLETED ho gaya tha to)

    REFUSE KARTA HAI:
      Agar koi DOWNSTREAM stage (cutting_pattern, cutting) start ho chuka
      hai — partial rollback dangerous hota hai. Admin pehle un stages ko
      manually clean kare.

    HEADER PRESERVE TRICK (important):
      LayeringRecord delete karne se pehle uske layer_length_meters,
      duration_minutes, notes ko sr.draft_* fields mein wapas copy karte
      hain. Warna re-edit form blank dikhega aur user ko galti lagegi.
      (Yeh bug 2026-05-28 ko mila tha — silent ValidationError pe
      "duration_minutes must be >= 1" aata tha.)

    AUDIT: tracking.AddaHistory mein STAGE_REOPENED entry log hoti hai.

    Side effects:
      • AddaStageRecord — completed_at/completed_by cleared, draft_* restored
      • LayeringRecord — deleted (summary; re-created on next complete)
      • Adda — current_stage→Layering, status→IN_PROGRESS, completed_at cleared
      • Cross-app/service: cost_service.clear_stage_cost (drops frozen processing cost)
        + tracking.services.log_adda (AddaHistory STAGE_REOPENED)
    """
    def _teardown(sr):
        # Preserve header values BEFORE deleting the typed LayeringRecord, else
        # the reopened editor renders blank layer_length/duration/notes and the
        # next Complete fails strict validation ("duration_minutes must be >= 1").
        # Copy them into sr.draft_* so the form pre-fills (bug found 2026-05-28).
        lr = LayeringRecord.objects.filter(stage_record=sr).first()
        if lr is None:
            return []
        sr.draft_layer_length_meters = lr.layer_length_meters
        sr.draft_duration_minutes = lr.duration_minutes
        sr.draft_notes = lr.notes or ''
        lr.delete()
        return ['draft_layer_length_meters', 'draft_duration_minutes', 'draft_notes']

    # Shared skeleton (mgmt gate, lock, already-open check, clear cost, reset
    # Adda, STAGE_REOPENED log). Layering's deltas: downstream guard + draft
    # preserve/teardown above. Workers + rolls + leftovers are kept.
    return reopen_stage_record(
        adda=adda, stage_code=STAGE_LAYERING, stage_label='Layering', user=user,
        guard=downstream_started_guard, teardown=_teardown,
    )
