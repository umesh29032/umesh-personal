"""Activity timeline service — "who did what on which Adda".

YEH FILE KYU HAI?
─────────────────
Spec D10 + D11: per-user, per-Adda activity tracking. Implementation = B1 —
derive timeline from existing FK columns (no new event table).

Sources (UNION):
  • tracking.AddaHistory    — created / stage_advanced / roll_assigned / completed
  • tracking.ClothRollHistory — roll status changes (filtered to rolls touching the Adda)
  • production.LayeringRollEntry — per-roll attach + verify
  • production.AddaStageRecord — completed_by signal

Each source contributes uniform `ActivityEvent` namedtuples sorted by `at` DESC.

Why uniform tuple? Templates don't need to know event source — just render
`when · who · verb · target`.
"""
from __future__ import annotations

from collections import namedtuple
from typing import Iterable



ActivityEvent = namedtuple(
    'ActivityEvent',
    ['at', 'actor', 'verb', 'adda_code', 'target', 'note'],
)


def _adda_history_events(adda_filter: dict, user=None) -> Iterable[ActivityEvent]:
    """AddaHistory rows → ActivityEvent stream.

    `adda_filter` jaisa hai waisa lagta hai (e.g. {'adda': adda_obj} ya {'adda__in': adda_qs}).
    """
    from tracking.models import AddaHistory
    qs = AddaHistory.objects.filter(**adda_filter).select_related(
        'actor', 'adda', 'roll', 'stage_from', 'stage_to',
    )
    if user is not None:
        qs = qs.filter(actor=user)
    verb_map = {
        AddaHistory.ChangeType.CREATED: 'created Adda',
        AddaHistory.ChangeType.STAGE_ADVANCED: 'advanced stage',
        AddaHistory.ChangeType.STAGE_REOPENED: 'reopened stage',
        AddaHistory.ChangeType.STATUS_CHANGED: 'changed status',
        AddaHistory.ChangeType.ROLL_ASSIGNED: 'assigned roll',
        AddaHistory.ChangeType.COMPLETED: 'completed Adda',
        AddaHistory.ChangeType.COST_FROZEN: 'froze stage cost',
        AddaHistory.ChangeType.WORKERS_ASSIGNED: 'assigned workers',
        AddaHistory.ChangeType.BUNDLE_CREATED: 'created bundle',
        AddaHistory.ChangeType.BARCODES_GENERATED: 'generated barcodes',
        AddaHistory.ChangeType.EXPORTED: 'exported barcodes',
        AddaHistory.ChangeType.COMPLETION_OVERRIDE: 'overrode stage completion',
        AddaHistory.ChangeType.VERIFIED_QTY_CORRECTED: 'corrected verified qty',
    }
    for h in qs:
        verb = verb_map.get(h.change_type, h.change_type)
        # Target = stage transition arrow OR roll summary OR adda code
        if h.stage_from and h.stage_to:
            target = f"{h.stage_from.get_stage_type_display()} → {h.stage_to.get_stage_type_display()}"
        elif h.stage_to:
            target = h.stage_to.get_stage_type_display()
        elif h.roll:
            target = h.roll.display_summary
        else:
            target = h.adda.code
        yield ActivityEvent(
            at=h.created_at, actor=h.actor, verb=verb,
            adda_code=h.adda.code, target=target, note=h.note,
        )


def _roll_history_events(adda_filter_qs, user=None) -> Iterable[ActivityEvent]:
    """ClothRollHistory rows for rolls that have ever touched the Adda(s).

    Adda FK direct nahi hai ClothRollHistory pe — roll.adda ke through filter.
    """
    from tracking.models import ClothRollHistory
    qs = ClothRollHistory.objects.filter(
        roll__adda__in=adda_filter_qs,
    ).select_related('roll', 'roll__adda', 'actor')
    if user is not None:
        qs = qs.filter(actor=user)
    for h in qs:
        if h.roll.adda is None:
            continue   # roll detached recently — skip
        yield ActivityEvent(
            at=h.created_at, actor=h.actor, verb=f"roll {h.get_change_type_display().lower()}",
            adda_code=h.roll.adda.code, target=h.roll.display_summary, note=h.note,
        )


def _layering_attach_events(adda_filter_qs, user=None) -> Iterable[ActivityEvent]:
    """LayeringRollEntry rows → per-roll attach events.

    Already partially covered by AddaHistory.ROLL_ASSIGNED but this gives the
    verified width/weight context that AddaHistory doesn't capture.
    """
    from production.models import LayeringRollEntry
    qs = LayeringRollEntry.objects.filter(
        stage_record__adda__in=adda_filter_qs,
    ).select_related('stage_record__adda', 'roll', 'attached_by')
    if user is not None:
        qs = qs.filter(attached_by=user)
    for e in qs:
        note_bits = []
        if e.width_verified_inch:
            note_bits.append(f"{e.width_verified_inch}\"")
        if e.weight_verified_kg:
            note_bits.append(f"{e.weight_verified_kg} KG")
        if e.notes:
            note_bits.append(e.notes)
        yield ActivityEvent(
            at=e.attached_at, actor=e.attached_by,
            verb='attached roll (verified)',
            adda_code=e.stage_record.adda.code,
            target=e.roll.display_summary,
            note=' · '.join(note_bits),
        )


def _stage_completion_events(adda_filter_qs, user=None) -> Iterable[ActivityEvent]:
    """AddaStageRecord rows where completed_by is set → stage-done events.

    AddaHistory STAGE_ADVANCED partially overlaps but doesn't carry "completed by who"
    cleanly (advance triggers come from service, actor may differ from completed_by).
    """
    from production.models import AddaStageRecord
    qs = AddaStageRecord.objects.filter(
        adda__in=adda_filter_qs,
        completed_at__isnull=False,
    ).select_related('adda', 'workflow_stage', 'completed_by')
    if user is not None:
        qs = qs.filter(completed_by=user)
    for sr in qs:
        yield ActivityEvent(
            at=sr.completed_at, actor=sr.completed_by,
            verb='marked stage complete',
            adda_code=sr.adda.code,
            target=sr.workflow_stage.get_stage_type_display(),
            note='',
        )


def adda_activity(adda, user=None, limit: int = 100) -> list[ActivityEvent]:
    """Per-Adda activity timeline. Newest first.

    `user=None` → activity by all users on this Adda.
    `user=<obj>` → filter to this user only (used by user dashboard).
    """
    from production.models import Adda
    # Wrap adda in a "queryset of one" for uniform filtering downstream.
    adda_qs = Adda.objects.filter(pk=adda.pk)
    events = []
    events.extend(_adda_history_events({'adda': adda}, user=user))
    events.extend(_roll_history_events(adda_qs, user=user))
    events.extend(_layering_attach_events(adda_qs, user=user))
    events.extend(_stage_completion_events(adda_qs, user=user))
    # Sort by timestamp DESC; if tied, fall back to actor email for stable order
    events.sort(key=lambda e: (e.at, getattr(e.actor, 'email', '') or ''), reverse=True)
    return events[:limit]


def user_activity_across_addas(user, limit: int = 30) -> list[ActivityEvent]:
    """User dashboard ke liye — yeh user ne kahin bhi kya kya kiya.

    Saare in-progress + recently completed Addas mein iss user ke events.
    Limit applied AFTER sort so cross-source ordering remains deterministic.
    """
    from production.models import Adda
    # Filter Addas to those where user has ANY signal (workers M2M membership)
    # broadens the search safely. We rely on per-source `user=...` filter to narrow.
    adda_qs = Adda.objects.all()
    events = []
    events.extend(_adda_history_events({'adda__in': adda_qs}, user=user))
    events.extend(_roll_history_events(adda_qs, user=user))
    events.extend(_layering_attach_events(adda_qs, user=user))
    events.extend(_stage_completion_events(adda_qs, user=user))
    events.sort(key=lambda e: e.at, reverse=True)
    return events[:limit]
