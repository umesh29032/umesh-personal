"""Adda service — batch banane + stage advance karne ka logic.

YEH FILE KYU HAI?
─────────────────
Adda creation aur stage transition yahan se hote hain.
Critical: Per-product counter atomically badhna chahiye — warna 2 threads collide kar sakti hain.

Race-safe kaise?
────────────────
`SELECT … FOR UPDATE` Postgres ka row-level lock. Jab tak ye transaction commit nahi hoti,
doosri transaction usi Product row pe wait karti hai. Counter increment kabhi double-count nahi.

Phase 4 (2026-05-20):
────────────────────
`create_adda` ab Layering stage_record bhi auto-create karta hai aur workers M2M
ko `cutting_master` + `cutting_master_helper` skill wale saare users se populate
karta hai. Agar koi skilled user system mein nahi to creation reject.
Reason: helpers ko Adda ban-te hi visible hona chahiye + system stuck-Addas se
bachna chahiye (spec D1 + D5 + D6).
"""
from __future__ import annotations

import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.skills import SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER
from accounts.services import PRODUCTION_ROLES, user_has_role
from production.constants import STAGE_LAYERING
from production.models import Adda, AddaStageRecord, Product

logger = logging.getLogger(__name__)


def _ensure_can_manage(user):
    """Production roles ka gate — service-side authorization check."""
    if not user_has_role(user, PRODUCTION_ROLES):
        raise PermissionDenied("requires production role")


def _skilled_user_pks() -> list[int]:
    """All active users with cutting_master or cutting_master_helper skill.

    Returns plain pk list to keep the SELECT FOR UPDATE transaction small —
    full User rows fetched later only by the M2M setter.
    """
    from accounts.models import User
    return list(
        User.objects.filter(
            is_active=True,
            skills__name__in=[SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER],
        ).distinct().values_list('pk', flat=True)
    )


# ── Streams redesign 2026-07-11 (ADR-H registry #5, same species as
# ARCHIVE_VALIDATORS / LAYOUT_PROVIDER): patterns_ai registers a callable
# product -> [{'fabric_group': str, 'blocking': bool}] in its apps.ready().
# Production never imports patterns_ai; a missing/failing provider
# fail-closes to ONE default lane (single-stream = today's behavior).
FABRIC_GROUPS_PROVIDER = None
DEFAULT_FABRIC_GROUP = 'body'


PRE_PRODUCTION_STAGE_CODES = ('layering', 'cutting_pattern', 'cutting')


def preproduction_joined(adda) -> bool:
    """THE join predicate as a derive-at-read (GAP-5): every live BLOCKING
    lane's CUTTING record is complete (frozen final review §3 — cutting only,
    earlier trio stages are procedure). True when the flow has no cutting
    stage or the Adda has no blocking lanes (nothing gates). Same rule
    `advance_lane` moves the pointer on — one predicate, two readers."""
    from production.models import CuttingStream
    cutting_ws_ids = list(
        adda.product.workflow_stages
        .filter(stage__code='cutting').values_list('pk', flat=True))
    if not cutting_ws_ids:
        return True
    blocking = list(CuttingStream.objects.filter(
        adda=adda, cancelled_at__isnull=True, is_blocking=True)
        .values_list('pk', flat=True))
    if not blocking:
        return True
    done_srs = list(
        AddaStageRecord.objects
        .filter(adda=adda, workflow_stage_id__in=cutting_ws_ids,
                completed_at__isnull=False)
        .values_list('stream_id', flat=True))
    done_lane_ids = {s for s in done_srs if s is not None}
    # legacy NULL-stream completed cutting (pre-adoption fixtures) counts for
    # a single-lane Adda — same tolerance lane_stage_record's Q|NULL gives
    if None in done_srs and len(blocking) == 1:
        return True
    return all(lane_id in done_lane_ids for lane_id in blocking)


def resolve_stream(adda, stream=None):
    """THE lane resolver every trio call site funnels through.

    stream may be a CuttingStream, a pk, or None. None = the single-lane
    convenience: when the Adda has exactly ONE live lane (every product
    today), return it — existing call sites stay byte-identical. With
    multiple lanes, None is refused: the caller must say which lane.
    """
    from production.models import CuttingStream
    if stream is not None:
        if isinstance(stream, CuttingStream):
            if stream.adda_id != adda.pk:
                raise ValidationError('lane belongs to a different Adda.')
            return stream
        return CuttingStream.objects.get(pk=int(stream), adda=adda)
    live = list(CuttingStream.objects.filter(
        adda=adda, cancelled_at__isnull=True).order_by(
        'fabric_group', 'sequence')[:2])
    if not live:
        # pre-redesign rows / raw fixtures: provision the default lane
        # (identical to what the backfill migration gave existing addas)
        return CuttingStream.objects.create(
            adda=adda, fabric_group=DEFAULT_FABRIC_GROUP, sequence=1,
            is_blocking=True)
    if len(live) > 1:
        raise ValidationError(
            f'{adda.code} has multiple cutting lanes — specify which lane.')
    return live[0]


def lane_stage_record(adda, workflow_stage, lane, *, create=False,
                      for_update=False, defaults=None):
    """THE trio SR lookup: lane-scoped, with legacy NULL-stream ADOPTION
    (fixtures / pre-redesign rows join the lane on first touch). Returns
    the SR or None; create=True inserts with the lane stamped."""
    from django.db.models import Q
    qs = AddaStageRecord.objects.filter(
        adda=adda, workflow_stage=workflow_stage).filter(
        Q(stream=lane) | Q(stream__isnull=True))
    if for_update:
        qs = qs.select_for_update()
    sr = qs.order_by('stream_id').first()       # lane row wins over NULL (column, no join)
    if sr is not None and sr.stream_id is None:
        sr.stream = lane
        sr.save(update_fields=['stream', 'updated_at'])
    if sr is None and create:
        sr = AddaStageRecord.objects.create(
            adda=adda, workflow_stage=workflow_stage, stream=lane,
            **(defaults or {}))
        sr._lane_created = True
    return sr


def _derive_fabric_groups(product) -> list[dict]:
    """Blueprint-derived lane specs via the wrapped provider (never raises)."""
    provider = FABRIC_GROUPS_PROVIDER
    if provider is None:
        return [{'fabric_group': DEFAULT_FABRIC_GROUP, 'blocking': True}]
    try:
        groups = provider(product) or []
    except Exception:                       # provider failure = single lane
        logger.exception('fabric-groups provider failed for %s', product.code)
        groups = []
    if not groups:
        return [{'fabric_group': DEFAULT_FABRIC_GROUP, 'blocking': True}]
    return groups


@transaction.atomic
def create_adda(user, *, product: Product) -> Adda:
    """Naye Adda ka code allocate kar ke row create karta hai + Layering kick off.

    Per-product counter atomic kaise hai?
        Product row pe `select_for_update()` lagaate hain — doosri concurrent
        create_adda(SAME_PRODUCT) call lock release hone tak ruk jaati hai.
        Counter increment + Adda insert dono ek hi transaction mein → no collision.

    Assignment model (F-2 polish 2026-07-05 — supersedes the Phase-4 auto-
    populate): creation NEVER assigns workers. The Layering AddaStageRecord is
    auto-created (started_at=now, rate snapshot frozen) with an EMPTY roster;
    the manager assigns explicitly via the panel form — identical to how
    Pattern/Cutting/Barcode stages already start. Spec-D6 guard retained:
    zero skilled users in the system → refuse creation (dead-end factory).

    Resulting code: {Product.code}-{counter:03d}  e.g. 'T-SHIRT-001'.

    Side effects:
        • UPDATE Product.adda_counter (locked row, atomic increment).
        • INSERT Adda (new batch row).
        • INSERT AddaStageRecord (no worker tasks) — only when first stage is Layering.
        • tracking.services.log_adda → INSERT AddaHistory (CREATED).
    """
    _ensure_can_manage(user)
    if not product.is_active:
        raise ValidationError(f"Product '{product.code}' is archived")

    skilled_pks = _skilled_user_pks()
    if not skilled_pks:
        # Spec D6 — block creation; helpers wouldn't have anyone to execute it.
        raise ValidationError(
            "No cutting_master or cutting_master_helper users exist. "
            "Add at least one user with that skill before creating an Adda."
        )

    # Yahi line race-safety deti hai — Product row lock ho jaati hai
    prod = Product.objects.select_for_update().get(pk=product.pk)
    prod.adda_counter += 1
    prod.save(update_fields=['adda_counter'])   # sirf counter column UPDATE

    # First stage pick — Product ka workflow_stages reverse FK queryset (order ASC)
    first_stage = prod.workflow_stages.order_by('order').first()
    if first_stage is None:
        # Defensive — seed migration ye guarantee karti hai
        raise ValidationError(f"Product '{prod.code}' has no workflow stages defined")

    adda = Adda.objects.create(
        code=f"{prod.code}-{prod.adda_counter:03d}",   # 3-digit zero padded
        product=prod,
        current_stage=first_stage,
        created_by=user,
    )

    # Streams redesign: derive the pre-production lanes from the Blueprint
    # (one row per fabric group, sequence 1). Single-group products derive
    # exactly one lane = today's behavior byte-identical.
    from production.models import CuttingStream
    streams = [
        CuttingStream.objects.create(
            adda=adda, fabric_group=spec['fabric_group'], sequence=1,
            is_blocking=bool(spec.get('blocking', True)), created_by=user)
        for spec in _derive_fabric_groups(prod)
    ]

    # Auto-create stage_record if first_stage is Layering — but NO worker
    # auto-assignment (F-2 polish 2026-07-05, PDD explicit-assignment direction):
    # the manager picks the roster via the panel's Start/Update-workers form
    # (set_stage_workers stays the single WorkerStageTask writer). Rate snapshot
    # is per (stage_record, role) — worker-independent — so it still freezes here.
    # Streams: one layering SR PER LANE (each lane = its own lay).
    if first_stage.stage_type == STAGE_LAYERING:
        from production.services.stage_rate_service import ensure_stage_role_rates
        for stream in streams:
            sr = AddaStageRecord.objects.create(
                adda=adda, workflow_stage=first_stage, stream=stream,
                started_at=timezone.now(),
            )
            # S2: freeze the payable-rate snapshot at stage-start (M-5/D-α).
            ensure_stage_role_rates(sr)

    # tracking app ka lazy import — production pe ulta depend karta hai
    from tracking.services import log_adda
    from tracking.models import AddaHistory
    log_adda(adda, AddaHistory.ChangeType.CREATED, user)
    logger.info(
        "adda.create code=%s adda_id=%s product=%s first_stage=%s",
        adda.code, adda.pk, prod.code, first_stage.stage_type,
    )
    return adda


@transaction.atomic
def advance_to_next_stage(adda: Adda, user, *, enforce_worker_credit: bool = True,
                          override_pending_reason: str | None = None) -> Adda:
    """Adda ko next WorkflowStage pe move karta hai. Last stage ke baad COMPLETED.

    enforce_worker_credit: PAY-2 (M2.7c). When True (default), a PAYABLE stage being
    left (WorkflowStage.credits_workers + self-paid) must have >=1 non-voided worker
    allocation or completion is blocked. Legacy paths pass False to opt out
    (compatibility-only flow, per the payroll architecture decision).

    override_pending_reason: R3 (PDD §27-C3). Default None = the C3 guard BLOCKS
    completion while assigned workers are still pending (assigned/in_progress) —
    production truth first; applies to EVERY stage incl. legacy paths (owner
    P-1) and re-runs after every reopen (stateless, owner P-3). A non-empty
    reason + super_admin actor = audited override: COMPLETION_OVERRIDE history
    event (adda, stage, pending worker names+count, actor, timestamp, reason)
    then the F3 cancel proceeds with the reason stamped on each task.

    Stage services (complete_layering / complete_cutting, in layering_service /
    cutting_service) iss helper ko call karte hain typed record save hone ke baad.

    Last-stage handling:
        nxt=None    → Adda completed, current_stage=None set, completed_at stamp
        nxt set hai → current_stage update

    Side effects:
        • production.services.cost_service.freeze_stage_cost → writes frozen
          processing_cost + cost_*_snapshot on the leaving AddaStageRecord (MONEY).
        • UPDATE Adda (current_stage; + status/completed_at when last stage).
        • tracking.services.log_adda → INSERT AddaHistory (COST_FROZEN if leaving record,
          STAGE_ADVANCED, + COMPLETED on final stage).
    """
    cur = adda.current_stage
    if cur is None:
        raise ValidationError("Adda has no current stage")

    # Streams redesign: a trio (pre-production) stage on a MULTI-lane Adda
    # must advance through advance_lane with its lane's SR — this legacy
    # funnel resolves the single lane so every existing single-lane caller
    # stays byte-identical.
    if cur.stage.code in PRE_PRODUCTION_STAGE_CODES:
        stream = resolve_stream(adda)          # refuses when >1 lane
        from django.db.models import Q
        lane_sr = (AddaStageRecord.objects
                   .filter(adda=adda, workflow_stage=cur)
                   .filter(Q(stream=stream) | Q(stream__isnull=True))
                   .first())
        # legacy NULL-stream rows (fixtures / pre-redesign) are ADOPTED
        # into the single lane so pointer math reads one truth
        if lane_sr is not None and lane_sr.stream_id is None:
            lane_sr.stream = stream
            lane_sr.save(update_fields=['stream', 'updated_at'])
        # lane_sr None = legacy BLIND advance of a never-opened stage:
        # exactly as before, no guard/freeze runs — the pointer simply
        # treats the stage as passed (assume_done_ws).
        return advance_lane(
            adda, stream=stream, leaving_sr=lane_sr, user=user,
            enforce_worker_credit=enforce_worker_credit,
            override_pending_reason=override_pending_reason,
            assume_done_ws=cur if lane_sr is None else None)

    # FREEZE manufacturing cost of the stage being LEFT, before advancing —
    # the shared finalize helper (extracted for the lane path; ONE source
    # of truth for worker-credit + C3 + freeze + resolve + pool + audit).
    leaving_sr = AddaStageRecord.objects.filter(adda=adda, workflow_stage=cur).first()
    _finalize_stage_record(
        adda, leaving_sr, user,
        enforce_worker_credit=enforce_worker_credit,
        override_pending_reason=override_pending_reason)

    # Next stage = order > current ke saare stages mein se sabse pehla
    nxt = adda.product.workflow_stages.filter(order__gt=cur.order).order_by('order').first()
    if nxt is None:
        # Aakhri stage thi — Adda complete mark
        adda.status = Adda.Status.COMPLETED
        adda.completed_at = timezone.now()
        adda.current_stage = None
        adda.save(update_fields=['status', 'completed_at', 'current_stage'])
    else:
        adda.current_stage = nxt
        adda.save(update_fields=['current_stage'])

    from tracking.services import log_adda
    from tracking.models import AddaHistory
    log_adda(adda, AddaHistory.ChangeType.STAGE_ADVANCED, user, stage_from=cur, stage_to=nxt)
    if nxt is None:
        log_adda(adda, AddaHistory.ChangeType.COMPLETED, user)
    logger.info(
        "adda.advance code=%s adda_id=%s stage_from=%s stage_to=%s frozen_cost=%s status=%s",
        adda.code, adda.pk, cur.stage_type, (nxt.stage_type if nxt is not None else None),
        (str(leaving_sr.processing_cost) if leaving_sr is not None else None),
        adda.status,
    )
    return adda


def _finalize_stage_record(adda, leaving_sr, user, *,
                           enforce_worker_credit=True,
                           override_pending_reason=None):
    """Everything that must happen to a stage record being LEFT — extracted
    (streams redesign) so the lane path and the legacy linear path share ONE
    truth: PAY-2 worker-credit guard → C3 pending guard/override → cost
    freeze → F3/F8 task resolve → pool materialize → COST_FROZEN audit."""
    if leaving_sr is None:
        return
    from production.services.cost_service import freeze_stage_cost
    stage_ws = leaving_sr.workflow_stage
    # Legacy blind-advance parity: stage services stamp completed_at BEFORE
    # funneling here; raw advance callers historically didn't — stamp it so
    # the lane pointer math (completed_at = the lane truth) stays honest.
    if leaving_sr.completed_at is None:
        leaving_sr.completed_at = timezone.now()
        if leaving_sr.completed_by_id is None and getattr(user, 'pk', None):
            leaving_sr.completed_by = user
        leaving_sr.save(update_fields=['completed_at', 'completed_by',
                                       'updated_at'])
    # PAY-2 (M2.7c): block completing a payable stage with zero worker allocations.
    # Runs BEFORE the freeze so nothing is mutated on rejection. No-op for
    # non-payable stages; legacy callers opt out via enforce_worker_credit=False.
    if enforce_worker_credit:
        from production.stages.base import ensure_worker_credit
        ensure_worker_credit(leaving_sr)

    # ── R3 C3 guard (PDD §27-C3) — runs BEFORE any mutation (freeze/cancel),
    # at the single funnel every stage's complete_* passes through, so every
    # current and future stage inherits it (open-closed). Stateless: a reopen
    # simply re-enters here on the next completion attempt (owner P-3).
    #
    # ⚠ TRANSITIONAL COMPATIBILITY LAYER (owner decision 2026-07-04, "B now +
    # A later") — NOT a permanent business rule. `create_adda` still
    # AUTO-assigns every skilled user to layering (legacy convenience that
    # predates the PDD's explicit manager-assignment model, §9/§16). Blocking
    # on bare ASSIGNED would therefore block every Adda on non-participants.
    # Until the assignment-model migration lands (roadmap gated-backlog item
    # "explicit-assignment migration"), the guard blocks only workers who
    # ENTERED the workflow: any draft or report flips a task to IN_PROGRESS
    # (worker_task_service), so status=IN_PROGRESS ⇔ started-but-unsubmitted.
    # Untouched ASSIGNED tasks keep the legacy F3 auto-cancel. When the
    # migration removes auto-assignment, DELETE the transitional filter and
    # block on (ASSIGNED, IN_PROGRESS) — the PDD-strict rule.
    cancel_note = ''
    if True:
        from production.models import WorkerStageTask
        pending = list(
            WorkerStageTask.objects
            .filter(stage_record=leaving_sr,
                    status=WorkerStageTask.Status.IN_PROGRESS)
            .select_related('worker')
        )
        if pending:
            names = ', '.join(
                (t.worker.get_full_name() or t.worker.email) for t in pending)
            if override_pending_reason is None:
                raise ValidationError(
                    f"Cannot complete {stage_ws.stage.name}: {len(pending)} "
                    f"worker(s) have STARTED work but not submitted: {names}. "
                    "Wait for their reports, have them submit, or (Super Admin) "
                    "override with a reason.")
            # Override path — Super Admin ONLY (owner P-2), reason MANDATORY.
            from accounts.services import ROLE_SUPER_ADMIN, user_has_role
            if not user_has_role(user, {ROLE_SUPER_ADMIN}):
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied(
                    "Only a Super Admin can override pending worker reports.")
            reason = (override_pending_reason or '').strip()
            if not reason:
                raise ValidationError(
                    "An override reason is required — it becomes part of the "
                    "permanent audit trail.")
            # Audit-complete event (owner instruction): adda + stage + pending
            # names + count + actor + timestamp (created_at) + reason, all on
            # the AddaHistory row itself — no dependence on external logs.
            from tracking.models import AddaHistory
            from tracking.services import log_adda
            log_adda(
                adda, AddaHistory.ChangeType.COMPLETION_OVERRIDE, user,
                stage_from=stage_ws, stage_record=leaving_sr,
                note=reason[:200],
                metadata={
                    'stage': stage_ws.stage.name,
                    'pending_workers': [
                        (t.worker.get_full_name() or t.worker.email)
                        for t in pending],
                    'pending_count': len(pending),
                    'reason': reason,
                })
            cancel_note = f"cancelled via super-admin override: {reason}"[:200]
            logger.warning(
                "stage.completion_override adda=%s stage=%s pending=%s by=%s",
                adda.code, stage_ws.stage.name, len(pending), getattr(user, 'pk', None))

    freeze_stage_cost(leaving_sr, user=user)
    # F3/F8 lifecycle (owner-locked 2026-06-11): completed stage leaves no
    # unresolved active tasks — unreported assigned/in_progress → cancelled
    # (+ M2M roster sync via the chokepoint; parity by construction).
    # completed/verified tasks untouched. R3: reaches here only when nothing
    # is pending OR behind the audited override (cancel_note = the reason).
    from production.services.worker_task_service import resolve_stage_tasks_on_complete
    resolve_stage_tasks_on_complete(leaving_sr, cancel_note=cancel_note)
    # OP-1 (S4 consumer wiring): freeze the leaving stage's PIECE POOL at the one
    # funnel every complete_* passes — the next stage allocates from it. AFTER the
    # F3 resolve (pool sums COMPLETED/VERIFIED tasks only, statuses now final).
    # Handler-dispatched: cutting no-op (APSCPB is its pool), NONE-grain → 0 rows,
    # write-once; reopen clears via reopen_stage_record (S4-P5).
    from production.services.pool_service import materialize_stage_pool
    materialize_stage_pool(leaving_sr)

    # Audit the freeze (logged even when cost is NULL — 'unpriced completion').
    from tracking.services import log_adda
    from tracking.models import AddaHistory
    log_adda(
        adda, AddaHistory.ChangeType.COST_FROZEN, user, stage_from=stage_ws,
        stage_record=leaving_sr,
        metadata={
            'method': leaving_sr.cost_method_snapshot or None,
            'rate': str(leaving_sr.cost_rate_snapshot) if leaving_sr.cost_rate_snapshot is not None else None,
            'qty': str(leaving_sr.cost_quantity_snapshot) if leaving_sr.cost_quantity_snapshot is not None else None,
            'cost': str(leaving_sr.processing_cost) if leaving_sr.processing_cost is not None else None,
            'lane': leaving_sr.stream.label if leaving_sr.stream_id else None,
        },
    )


@transaction.atomic
def add_stream(adda: Adda, *, fabric_group: str, reason: str, user):
    """GAP-4: THE declared-lane writer (CUTTING_STREAM_LIFECYCLE §1–§9,
    frozen verbatim). A sequence-1 lane is DERIVED; every later lane is a
    DECLARED management act with a mandatory reason — appended, never
    rewriting anything that already happened.

    §1 management-only · §2 any time until the Adda completes (never on a
    completed Adda) · §3 mandatory reason (reasons are DATA) · §5 sequence =
    Max+1 under the Adda row lock (abandoned lanes never collide) · §6 the
    fabric group must already EXIST in the Adda's derived lanes (a new group
    = a Blueprint change → FUTURE Addas) · §9.5 append-only history event.
    Blocking is inherited from the group's existing lanes (mandatory pieces
    are a group fact, not a lane fact)."""
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    from production.models import CuttingStream

    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can add a cutting lane.")
    if not (reason or '').strip():
        raise ValidationError("A reason is required to add a cutting lane.")
    locked = Adda.objects.select_for_update().get(pk=adda.pk)   # §5 lock
    if locked.status == Adda.Status.COMPLETED:
        raise ValidationError(
            "This Adda is completed — more work on it is a NEW Adda, "
            "not a lane (lifecycle §2).")
    group = (fabric_group or '').strip()
    siblings = list(CuttingStream.objects.filter(
        adda=locked, fabric_group=group))
    if not siblings:
        raise ValidationError(
            f"'{group}' is not one of this Adda's fabric groups — a new "
            "group is a Blueprint change and applies to future Addas "
            "(lifecycle §6).")
    next_seq = max(s.sequence for s in siblings) + 1
    lane = CuttingStream.objects.create(
        adda=locked, fabric_group=group, sequence=next_seq,
        is_blocking=any(s.is_blocking for s in siblings),
        reason=reason.strip(), created_by=user)
    from tracking.models import AddaHistory
    from tracking.services import log_adda
    log_adda(locked, AddaHistory.ChangeType.STREAM_ADDED, user,
             metadata={'stream_id': lane.pk, 'fabric_group': group,
                       'sequence': next_seq, 'reason': reason.strip()})
    logger.info("adda.stream_added code=%s lane=%s seq=%s by=%s",
                locked.code, lane.label, next_seq, getattr(user, 'pk', None))
    return lane


@transaction.atomic
def cancel_stream(adda: Adda, *, stream, reason: str, user):
    """GAP-4: the cancel-if-empty ESCAPE (lifecycle §9.4) — the single
    permitted mutation on a stream row. Management-only · mandatory reason ·
    only while the lane has ZERO stage records · a sequence-1 DERIVED lane is
    never cancellable (the Blueprint put it there). Cancelled lanes leave the
    join predicate and grey out on A360; the row lives forever."""
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    from production.models import CuttingStream

    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can cancel a cutting lane.")
    if not (reason or '').strip():
        raise ValidationError("A reason is required to cancel a lane.")
    lane = CuttingStream.objects.select_for_update().get(
        pk=stream.pk if hasattr(stream, 'pk') else int(stream), adda=adda)
    if lane.cancelled_at is not None:
        raise ValidationError("This lane is already cancelled.")
    if lane.sequence == 1:
        raise ValidationError(
            "A derived lane can never be cancelled — if the Blueprint is "
            "wrong, fix the Blueprint; future Addas derive correctly "
            "(lifecycle §9.4).")
    if AddaStageRecord.objects.filter(stream=lane).exists():
        raise ValidationError(
            "Work has started on this lane — it is history now and lives "
            "forever (lifecycle §9.4). Use reverse/void/reopen for wrong "
            "numbers; a lane is never erased.")
    lane.cancelled_at = timezone.now()
    lane.cancel_reason = reason.strip()
    lane.save(update_fields=['cancelled_at', 'cancel_reason'])
    from tracking.models import AddaHistory
    from tracking.services import log_adda
    log_adda(adda, AddaHistory.ChangeType.STREAM_CANCELLED, user,
             metadata={'stream_id': lane.pk, 'fabric_group': lane.fabric_group,
                       'sequence': lane.sequence, 'reason': reason.strip()})
    logger.info("adda.stream_cancelled code=%s lane=%s by=%s",
                adda.code, lane.label, getattr(user, 'pk', None))
    return lane


def advance_lane(adda: Adda, *, stream, leaving_sr, user,
                 enforce_worker_credit: bool = True,
                 override_pending_reason: str | None = None,
                 assume_done_ws=None) -> Adda:
    """Streams redesign: a pre-production LANE finished one of its trio
    stages. Finalize THAT lane's stage record (shared helper — all money/
    task/pool laws identical), then move the Adda's coarse pointer:

        pointer = earliest trio stage where ANY live BLOCKING lane is
                  incomplete; none left = the JOIN — advance into the
                  first post-trio stage exactly like the linear path.

    Single-lane products walk pointer stages one-by-one = byte-identical
    to the legacy behavior (MIN over one lane is that lane)."""
    _finalize_stage_record(
        adda, leaving_sr, user,
        enforce_worker_credit=enforce_worker_credit,
        override_pending_reason=override_pending_reason)

    from production.models import CuttingStream
    from tracking.services import log_adda
    from tracking.models import AddaHistory

    trio_stages = list(
        adda.product.workflow_stages
        .filter(stage__code__in=PRE_PRODUCTION_STAGE_CODES)
        .order_by('order'))
    blocking_lanes = list(CuttingStream.objects.filter(
        adda=adda, cancelled_at__isnull=True, is_blocking=True))
    done = {
        (sr.workflow_stage_id, sr.stream_id)
        for sr in AddaStageRecord.objects.filter(
            adda=adda, workflow_stage__in=trio_stages,
            completed_at__isnull=False)}
    if assume_done_ws is not None:
        # legacy blind advance of a never-opened stage (see caller)
        done.add((assume_done_ws.pk, stream.pk if stream else None))

    old = adda.current_stage

    # THE JOIN PREDICATE (frozen §3): every blocking lane's CUTTING record
    # is complete — earlier trio stages are procedure, not the gate.
    cutting_ws = [ws for ws in trio_stages if ws.stage.code == 'cutting']
    joined = bool(blocking_lanes) and all(
        any((ws.pk, lane.pk) in done for ws in cutting_ws)
        for lane in blocking_lanes
    ) if cutting_ws else False
    if not blocking_lanes:
        joined = True                       # nothing gates (edge fixtures)

    if not joined:
        # coarse pointer keeps the LEGACY forward-walk invariant: move to
        # the first incomplete trio stage AHEAD of the old pointer; never
        # regress, never jump past cutting. Per-lane truth is rendered on
        # the A360 lane cards, not on this pointer.
        pointer = next(
            (ws for ws in trio_stages
             if old is not None and ws.order > old.order
             and any((ws.pk, lane.pk) not in done
                     for lane in blocking_lanes)),
            None)
        if pointer is not None:
            adda.current_stage = pointer
            adda.save(update_fields=['current_stage'])
            log_adda(adda, AddaHistory.ChangeType.STAGE_ADVANCED, user,
                     stage_from=old, stage_to=pointer)
        return adda

    # THE JOIN — every blocking lane is cut. Resume the linear line.
    # Frozen late-lane rule: the join gate has NO MEMORY — a lane that
    # completes AFTER the Adda already joined must never regress the
    # pointer (its output appends; the line keeps moving).
    last_trio_order = trio_stages[-1].order if trio_stages else 0
    if old is not None and old.order > last_trio_order:
        return adda                     # already past the join — no move
    nxt = (adda.product.workflow_stages
           .filter(order__gt=last_trio_order).order_by('order').first())
    if nxt is None:
        adda.status = Adda.Status.COMPLETED
        adda.completed_at = timezone.now()
        adda.current_stage = None
        adda.save(update_fields=['status', 'completed_at', 'current_stage'])
    else:
        adda.current_stage = nxt
        adda.save(update_fields=['current_stage'])
    log_adda(adda, AddaHistory.ChangeType.STAGE_ADVANCED, user,
             stage_from=old, stage_to=nxt,
             metadata={'join': True,
                       'lanes': [lane.label for lane in blocking_lanes]})
    if nxt is None:
        log_adda(adda, AddaHistory.ChangeType.COMPLETED, user)
    logger.info(
        "adda.lane_join code=%s adda_id=%s lane=%s stage_to=%s status=%s",
        adda.code, adda.pk, stream.label if stream else None,
        (nxt.stage_type if nxt is not None else None), adda.status,
    )
    return adda
