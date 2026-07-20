"""THE production-truth chokepoint (V2-1 → V2-3; M2M dropped in 0035).

SOLE writer of WorkerStageTask + WorkerStageContribution (CI gate [4/4]).
WST = participation truth (roster; cancel-not-delete). WSC = production truth:
`reported_quantity` is IMMUTABLE (owner §6); `verified_quantity` is the
management correction (P1) — both preserved forever; `expected_*` freezes at
complete and is VISIBILITY ONLY, never money (ADR-0005 Option B).

C-TM (locked): EVERY capture path — manual report today, barcode scans under
TM-2 tomorrow — must converge through these functions. A second WSC writer =
settlement paying numbers nobody can trust; that is what this gate prevents.

Reconcile rule: add missing workers as an ACTIVE task; CANCEL tasks whose worker
was removed (never delete — production history is immutable, owner rule). New
tasks copy the stage's own timestamps + status (completed if the stage completed,
else assigned) — identical to the 0032 backfill, so dual-write and backfill agree.

Leaf module: imports only settings + models (lazily), NEVER the services facade —
so stage services can import it without a circular import.

CALL CONTRACT: `set_stage_workers` must run inside the caller's @transaction.atomic
(verify EVERY caller — P19A C-1: start_layering silently lost its decorator to an
inserted helper and 500'd every roster update in production testing) so the M2M
write + Task reconcile commit together; it locks
the active tasks with select_for_update (Hinglish: roster full-replace hai —
lock ke bina do managers ki save ek doosre ke cancel/create ko khaa jaati). `add_stage_worker` is additive and
lock-free (the skill-sync retro-tag path is not atomic).
"""
import logging
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def _seed_status(stage_record) -> str:
    # Mirror 0032 backfill: a completed stage's tasks are 'completed', else 'assigned'.
    return 'completed' if stage_record.completed_at is not None else 'assigned'


def _new_task_kwargs(stage_record):
    # Copy the stage's own timestamps (same as backfill — keeps parity exact).
    return {
        'status': _seed_status(stage_record),
        'started_at': stage_record.started_at,
        'completed_at': stage_record.completed_at,
    }


def set_stage_workers(stage_record, worker_ids, *, cancel_note: str = ''):
    """Full-replace the stage's workers (V2-1d: WorkerStageTask is the ONLY store).

    Task reconcile: ensure ONE active task per id in `worker_ids`; CANCEL active
    tasks whose worker is no longer present. Idempotent. `cancel_note` (optional)
    is appended to each task cancelled by THIS call — audit trail for auto-cancels
    (F3/F8 stage-completion lifecycle).
    """
    target = {int(getattr(w, 'pk', w)) for w in (worker_ids or [])}
    from production.models import WorkerStageTask
    # Lock active tasks for this stage_record (caller is atomic). The partial
    # unique (one active per sr+worker) is the final race backstop.
    active = {
        t.worker_id: t
        for t in WorkerStageTask.objects
        .filter(stage_record=stage_record)
        .exclude(status=WorkerStageTask.Status.CANCELLED)
        .select_for_update()
    }
    for wid in target:
        if wid not in active:                        # missing → new active task
            WorkerStageTask.objects.create(
                stage_record=stage_record, worker_id=wid, **_new_task_kwargs(stage_record))
    for wid, task in active.items():
        if wid not in target:                        # removed → cancel (never delete)
            # PA-10-2: NEVER cancel a task that already carries frozen production truth
            # (COMPLETED/VERIFIED). complete_worker_task does NOT stamp
            # stage_record.completed_at, so a COMPLETED task routinely exists on an
            # OPEN stage; a manager roster edit (re-running start_* with a reduced
            # roster) reaches here and would otherwise cancel that task — orphaning its
            # WorkerStageContribution rows from settlement (_settleable_lines filters
            # completed/verified) and the review screen, silently unpaying the worker.
            # resolve_stage_tasks_on_complete already passes completed/verified in
            # `target`, so this guard does not change its behaviour — it only closes
            # the direct-reassign hole.
            if task.status in (WorkerStageTask.Status.COMPLETED,
                               WorkerStageTask.Status.VERIFIED):
                continue
            task.status = WorkerStageTask.Status.CANCELLED
            if cancel_note:
                task.notes = (f"{task.notes} | {cancel_note}" if task.notes else cancel_note)[:200]
            task.save(update_fields=['status', 'notes', 'updated_at'])
    logger.info("worker_task.set sr=%s members=%s", stage_record.pk, sorted(target))


AUTO_CANCEL_NOTE = "auto-cancelled: stage completed without submitted report"


def resolve_stage_tasks_on_complete(stage_record, *, cancel_note: str = ''):
    """F3/F8 (owner-locked 2026-06-11): a completed stage leaves NO unresolved
    active tasks. assigned / in_progress (with or without draft lines) → CANCELLED;
    completed / verified → untouched (immutable work). Draft contribution lines on
    cancelled tasks are RETAINED (evidence of partial work; invisible to business
    reads, which only consume completed tasks).

    R3 (PDD §27-C3): this now runs only when nothing is pending OR behind the
    super-admin override — advance_to_next_stage BLOCKS first. `cancel_note`
    lets the override stamp its reason on each cancelled task (defaults to the
    legacy auto-cancel note).

    Routed through set_stage_workers — the completed-stage roster (active tasks)
    then shows only workers who actually reported (owner decision: truthful
    roster > assignment-history display).
    """
    from production.models import WorkerStageTask
    keep = list(
        WorkerStageTask.objects
        .filter(stage_record=stage_record,
                status__in=(WorkerStageTask.Status.COMPLETED,
                            WorkerStageTask.Status.VERIFIED))
        .values_list('worker_id', flat=True)
    )
    set_stage_workers(stage_record, keep,
                      cancel_note=cancel_note or AUTO_CANCEL_NOTE)
    logger.info("worker_task.resolve_on_complete sr=%s kept=%s",
                stage_record.pk, sorted(keep))


def add_stage_worker(stage_record, worker):
    """Additive: ensure ONE active task for this worker. Does NOT
    cancel others. Used by the layering skill-sync retro-tag (non-atomic)."""
    wid = int(getattr(worker, 'pk', worker))
    from production.models import WorkerStageTask
    # Re-activate by creating a fresh active task if none exists (a prior cancelled
    # task does not block — partial unique excludes cancelled).
    has_active = (
        WorkerStageTask.objects
        .filter(stage_record=stage_record, worker_id=wid)
        .exclude(status=WorkerStageTask.Status.CANCELLED)
        .exists()
    )
    if not has_active:
        WorkerStageTask.objects.create(
            stage_record=stage_record, worker_id=wid, **_new_task_kwargs(stage_record))


# ── V2-1c: worker self-report + complete-freeze (Option B: NO ledger here) ──────

def _ensure_task_actor(task, user):
    """The task's own worker (reports/completes own work) OR management."""
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    if user_has_role(user, MANAGEMENT_ROLES):
        return
    if task.worker_id != getattr(user, 'pk', None):
        raise PermissionDenied("not your task")


def _resolve_machine_code(task) -> str:
    """Pre-Phase-3 B: which physical machine is this worker on RIGHT NOW?
    Only meaningful on machine stages; resolution = the worker's OPEN
    MachineAssignment of the stage's machine type (adda-matched window wins over
    a global one). Returns '' when unresolvable — passive metadata, never an
    error. Lazy machines import (function-level, same as generic_stage handler —
    model-level FKs stay machines→production only)."""
    stage = task.stage_record.workflow_stage.stage
    if stage.work_type != stage.WorkType.MACHINE or not stage.machine_type_id:
        return ''
    from machines.models import MachineAssignment
    open_assignments = (
        MachineAssignment.objects
        .filter(worker_id=task.worker_id, end_at__isnull=True,
                machine__machine_type_id=stage.machine_type_id)
        .select_related('machine')
        .order_by('-start_at'))
    adda_match = next((a for a in open_assignments
                       if a.adda_id == task.stage_record.adda_id), None)
    chosen = adda_match or next(iter(open_assignments), None)
    return chosen.machine.code if chosen else ''


@transaction.atomic
def void_submitted_report(task, *, actor, reason: str):
    """Pre-Phase-3 D (owner-approved 2026-07-06): audited, MANAGER-ONLY recovery
    for a wrongly-submitted report (fat-finger). Workers never edit after
    submit; verification never increases — this is THE explicit path when the
    true number is HIGHER than submitted.

    Mechanics (append-only, first-pass truth never edited — ADR-0010 D4):
      • the COMPLETED task is set to CANCELLED (its contributions stay attached
        as inert history: settlement funnel + pool materialize + board totals
        all read completed/verified tasks only, so the voided lines drop out of
        every truth surface without a row edit);
      • a FRESH active task is created for the same worker (existing
        add_stage_worker primitive) — they re-report through the normal path;
      • the void is a DB-resident AddaHistory event (REPORT_VOIDED) with the
        voided lines snapshot + mandatory reason.

    Guards: management only · mandatory reason · task must be COMPLETED/VERIFIED
    · REFUSED once the stage has completed (the downstream pool froze at
    advance — reopen the stage first) · REFUSED if any line is settlement-
    credited (reverse the settlement first — money armor).
    """
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    from production.models import WorkerStageTask

    if not user_has_role(actor, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can void a submitted report.")
    if not (reason or '').strip():
        raise ValidationError("A reason is required to void a submitted report.")
    t = (WorkerStageTask.objects.select_for_update()
         .select_related('stage_record__workflow_stage__stage', 'worker')
         .get(pk=task.pk))
    if t.status not in (WorkerStageTask.Status.COMPLETED,
                        WorkerStageTask.Status.VERIFIED):
        raise ValidationError("Only a submitted (completed) report can be voided.")
    sr = t.stage_record
    if sr.completed_at is not None:
        raise ValidationError(
            "This stage has already been completed — its output pool is frozen. "
            "Reopen the stage first, then void the report.")
    lines = list(t.contributions.select_related('settlement_line').all())
    for c in lines:
        if c.settlement_line_id and c.settlement_line.voided_at is None:
            raise ValidationError(
                "This report was already settled "
                f"({c.settlement_line.adda_settlement.reference}) — reverse that "
                "settlement first.")
    t.status = WorkerStageTask.Status.CANCELLED
    note = f"[report voided: {reason.strip()}]"
    t.notes = (f"{t.notes} | {note}" if t.notes else note)[:200]
    t.save(update_fields=['status', 'notes', 'updated_at'])
    # Fresh active task — same primitive manager rostering uses (additive;
    # partial-unique one-active-per(sr,worker) permits it past the cancelled row).
    add_stage_worker(sr, t.worker)
    new_task = (WorkerStageTask.objects
                .filter(stage_record=sr, worker=t.worker)
                .exclude(status=WorkerStageTask.Status.CANCELLED)
                .latest('pk'))
    from tracking.models import AddaHistory
    from tracking.services import log_adda
    log_adda(
        sr.adda, AddaHistory.ChangeType.REPORT_VOIDED, actor,
        stage_record=sr,
        note=(f"{t.worker.get_full_name() or t.worker.email}: submitted report "
              f"voided — {reason.strip()[:80]}"),
        metadata={
            'task': t.pk, 'new_task': new_task.pk,
            'worker': t.worker.get_full_name() or t.worker.email,
            'worker_id': t.worker_id,
            'stage': sr.workflow_stage.stage.name,
            'reason': reason.strip()[:200],
            'lines': [{'color': c.color_id, 'size': c.size_id,
                       'good': str(c.good_quantity), 'alter': str(c.alter_quantity),
                       'missing': str(c.missing_quantity),
                       'damaged': str(c.damaged_quantity)} for c in lines],
        })
    logger.info("worker_task.void_report task=%s new_task=%s by=%s",
                t.pk, new_task.pk, actor.pk)
    return new_task


@transaction.atomic
def report_contributions(task, lines, *, actor):
    """Worker submits reported production lines (append-only) for their task.

    Each line = {reported_quantity, color_id?, size_id?, bundle_item_id?}. Creates
    WorkerStageContribution rows; `expected_*` stay NULL (frozen later at complete —
    Option B, no money here). Moves an `assigned` task to `in_progress`. Rejected
    once the task is completed/verified/cancelled (locked after submit).
    """
    from production.models import WorkerStageContribution, WorkerStageTask
    _ensure_task_actor(task, actor)
    locked = (WorkerStageTask.Status.COMPLETED, WorkerStageTask.Status.VERIFIED,
              WorkerStageTask.Status.CANCELLED)
    if task.status in locked:
        raise ValidationError("Cannot report on a completed or cancelled task.")
    # Pre-Phase-3 B: machine identity snapshot, resolved ONCE per report call.
    machine_code = _resolve_machine_code(task)
    created = []
    for line in lines:
        # PA-07-1: the worker view passes reported_quantity as a RAW string. A
        # non-numeric value (tampered POST, or a locale comma like "1,5" on mobile)
        # makes Decimal() raise decimal.InvalidOperation — NOT a ValidationError — so
        # the view's `except ValidationError` misses it and the request 500s. Convert
        # it to a graceful ValidationError (the view then shows a message).
        try:
            qty = Decimal(str(line['reported_quantity']))
        except InvalidOperation:
            raise ValidationError("Quantity must be a number.")
        if qty < 0:
            raise ValidationError("reported_quantity cannot be negative.")
        # Foundation S3 (RC-3 dual-write): the worker UI submits the payable
        # GOOD quantity; reported_quantity is dual-written equal (legacy column,
        # renamed-not-dropped at S6). R10-B: generic machine/manual stages also
        # capture ALTER + MISSING observations per line (S3 columns; immutable
        # analytics — D2: only good is EVER payable; the freeze reads good only).
        # Pre-Phase-3 A: DAMAGED (scrap) is the 4th observation.
        def _obs(key):
            raw = line.get(key)
            if raw in (None, ''):
                return Decimal('0')
            try:
                val = Decimal(str(raw))
            except InvalidOperation:
                raise ValidationError(f"{key} must be a number.")
            if val < 0:
                raise ValidationError(f"{key} cannot be negative.")
            return val

        alter = _obs('alter_quantity')
        missing = _obs('missing_quantity')
        damaged = _obs('damaged_quantity')
        # A line must observe SOMETHING (mirrors wsc_gamd constraint): good may be
        # 0 only when an alter/missing/damaged observation is positive.
        if qty == 0 and alter == 0 and missing == 0 and damaged == 0:
            raise ValidationError("reported_quantity must be greater than 0.")

        created.append(WorkerStageContribution.objects.create(
            task=task,
            reported_quantity=qty,
            good_quantity=qty,
            alter_quantity=alter,
            missing_quantity=missing,
            damaged_quantity=damaged,
            machine_code=machine_code,
            color_id=line.get('color_id'),
            size_id=line.get('size_id'),
            bundle_item_id=line.get('bundle_item_id'),
        ))
    now = timezone.now()
    update = ['updated_at']
    # Pre-Phase-3 C: first WORKER report timestamp (passive — nothing reads it).
    if created and task.first_report_at is None:
        task.first_report_at = now
        update.append('first_report_at')
    if task.status == WorkerStageTask.Status.ASSIGNED:
        task.status = WorkerStageTask.Status.IN_PROGRESS
        update.append('status')
        if task.started_at is None:
            task.started_at = now
            update.append('started_at')
    if len(update) > 1:
        task.save(update_fields=update)
    logger.info("worker_task.report task=%s lines=%s machine=%s",
                task.pk, len(created), machine_code or '-')
    return created


@transaction.atomic
def report_bundle(task, line, *, actor):
    """AE-3 per-bundle submit — the "My Assigned Work" card flow.

    A worker may hold several bundles on ONE stage task; reporting one must NOT lock the
    others. So this UPSERTS a single bundle's contribution (replaces only that (colour,size)
    line, leaves the rest untouched), enforces the allocation bound for THAT bundle
    immediately, and completes the task ONLY when every active-allocated bundle now has a
    report. Returns {'completed': bool, 'remaining_bundles': int}.

    (The full multi-line form's save_draft + complete path is unchanged; this is the
    focused single-bundle path.)

    R1 (2026-07-20 engineering review): the over-report rule is NOT re-derived here — it is the
    single canonical `pool_service.check_allocation_bound`. We upsert the line first, then call
    that one validator; on refusal the enclosing @transaction.atomic rolls the upsert back, so
    the worker's prior state is preserved. No duplicated business rule; reads persisted `good`
    (never the S6-retired `reported_quantity` form key)."""
    from production.models import (
        WorkerStageAllocation, WorkerStageContribution, WorkerStageTask,
    )
    from production.services import pool_service
    _ensure_task_actor(task, actor)
    locked = (WorkerStageTask.Status.COMPLETED, WorkerStageTask.Status.VERIFIED,
              WorkerStageTask.Status.CANCELLED)
    if task.status in locked:
        raise ValidationError("Cannot edit a completed or cancelled submission.")

    color_id = line.get('color_id')
    size_id = line.get('size_id')
    sr = task.stage_record

    # Upsert: drop only THIS bundle's existing line(s), keep the other bundles' lines.
    task.contributions.filter(color_id=color_id, size_id=size_id).delete()
    report_contributions(task, [line], actor=actor)

    # CANONICAL over-report bound (single source) — raises if this (or any reported) dim
    # exceeds its allocation; the atomic rollback then undoes the upsert above.
    pool_service.check_allocation_bound(task)

    # All allocated bundles reported? (every active (colour,size) has a contribution)
    alloc_pairs = set(
        WorkerStageAllocation.objects
        .filter(stage_record=sr, worker=task.worker, voided_at__isnull=True)
        .values_list('color_id', 'size_id'))
    reported_pairs = set(
        WorkerStageContribution.objects
        .filter(task=task).values_list('color_id', 'size_id'))
    remaining = alloc_pairs - reported_pairs
    if not remaining:
        complete_worker_task(task, actor=actor)
        return {'completed': True, 'remaining_bundles': 0}
    return {'completed': False, 'remaining_bundles': len(remaining)}


@transaction.atomic
def save_draft_contributions(task, lines, *, actor):
    """Save the worker's DRAFT contribution lines — operational convenience, NOT
    business truth. REPLACES the task's current draft lines (so a worker can keep
    editing); allowed only while the task is not completed/cancelled. Drafts are
    excluded from costing/settlement/earnings/readiness (those read only COMPLETED
    tasks via `task.is_draft`). Business truth begins at complete_worker_task().

    Drafts are not history → clearing + rewriting them is safe (unlike completed
    work, which is immutable).
    """
    from production.models import WorkerStageTask
    _ensure_task_actor(task, actor)
    if task.status in (WorkerStageTask.Status.COMPLETED, WorkerStageTask.Status.VERIFIED,
                       WorkerStageTask.Status.CANCELLED):
        raise ValidationError("Cannot edit a completed or cancelled submission.")
    task.contributions.all().delete()           # draft ≠ history → safe to replace
    return report_contributions(task, lines, actor=actor)


@transaction.atomic
def complete_worker_task(task, *, actor):
    """Worker marks their task complete → FREEZE `expected_*` on each contribution
    (`reported_quantity × the stage rate snapshot for this worker`). NO ledger entry
    (Option B — payable is decided at Adda settlement). Immutable: a later rate edit
    never rewrites these. Verification is OPTIONAL and does NOT gate this.
    """
    from production.models import WorkerStageTask
    from production.services import cost_service
    # LOCK the task row + re-check its AUTHORITATIVE DB status (P0-5). The caller
    # passes a `task` read earlier (in the view), so its in-memory status can be
    # STALE vs a concurrent manager stage-complete — resolve_stage_tasks_on_complete
    # cancels open tasks under its own select_for_update. Locking the row and reading
    # the status from the DB (not the stale instance) serializes the two:
    #   • manager's cancel committed first → status=CANCELLED → refuse (never
    #     resurrect the task to COMPLETED);
    #   • we acquire the lock first → set_stage_workers blocks, then keeps us
    #     COMPLETED (completed/verified are never cancelled) → no stranded frozen
    #     contributions.
    # We keep operating on the caller's `task` object so its in-place mutation to
    # COMPLETED (relied on by callers) is preserved. Also the prerequisite lock
    # pattern for the future allocation draw-down race (S5).
    locked_status = (WorkerStageTask.objects.select_for_update()
                     .values_list('status', flat=True).get(pk=task.pk))
    _ensure_task_actor(task, actor)
    if locked_status in (WorkerStageTask.Status.COMPLETED, WorkerStageTask.Status.VERIFIED):
        raise ValidationError("Task already completed.")
    if locked_status == WorkerStageTask.Status.CANCELLED:
        raise ValidationError("Cannot complete a cancelled task.")
    # Foundation S4/Phase 4: Strict allocation bound BEFORE any freeze (a refused complete
    # freezes nothing). Always enforced; a no-op only on non-pool / pool-producer stages.
    # Production-CAPACITY only (good+alter+missing ≤ Σ active allocated) — reads no money.
    from production.services import pool_service
    pool_service.check_allocation_bound(task)
    ws = task.stage_record.workflow_stage
    # R8 WP-4: a FIXED-pay stage pays rate × 1 exactly ONCE per stage record —
    # a second completed report would double the fixed amount (two assigned
    # workers each reporting "done"). Refuse with the responsible name.
    # Reverse/re-settle is unaffected (this reads task status, never money).
    from production.models import CostMethod as _CM
    if ws.cost_method == _CM.FIXED:
        other = (WorkerStageTask.objects
                 .filter(stage_record=task.stage_record,
                         status__in=(WorkerStageTask.Status.COMPLETED,
                                     WorkerStageTask.Status.VERIFIED))
                 .exclude(pk=task.pk).select_related('worker').first())
        if other is not None:
            raise ValidationError(
                "This fixed-pay stage was already reported complete by "
                f"{other.worker.get_full_name() or other.worker.email} — a "
                "fixed amount pays once. Ask a manager if this is wrong.")
    from production.services import stage_rate_service
    # Foundation S2 (addendum M-5): freeze the worker's ROLE now, and pay the rate
    # FROZEN on the Adda (AddaStageRoleRate), not the live workflow — so a later
    # workflow-rate edit or a worker role change never re-prices this work.
    role = task.worker.role
    # Contract 2: snapshots are created at stage-start; this is the safety net —
    # if it has to create them here, a creation site was missed (surface it).
    if stage_rate_service.ensure_stage_role_rates(task.stage_record):
        logger.warning(
            "stage_rate.snapshot_missing_at_complete sr=%s task=%s — created late; "
            "a stage-record creation site is not calling ensure_stage_role_rates "
            "(contract 2; expected only for pre-S2 records)",
            task.stage_record_id, task.pk)
    # Lock the rate row (contract 1: lock order task → AddaStageRoleRate) and read
    # the frozen rate. Fallback to the live resolution ONLY when no snapshot exists
    # (pre-S2 records) — and warn, never silently fall back forever (contract 2).
    rate, rate_row = stage_rate_service.frozen_rate_for(task.stage_record, role, lock=True)
    if rate is None:
        rate = cost_service.resolved_payable_rate(ws, role)
        logger.warning(
            "stage_rate.live_fallback sr=%s role=%s task=%s — no frozen rate; using "
            "live resolution (legit only for pre-S2 / off-roster role)",
            task.stage_record_id, getattr(role, 'pk', None), task.pk)
    # F2: grouped→0 STRUCTURAL guard — a grouped member never pays, even if the frozen
    # snapshot is a stale non-zero (set before the stage was grouped). Grouped wins.
    rate = cost_service.effective_pay_rate(ws, rate)
    for c in task.contributions.all():
        c.expected_rate = rate
        # S3: visibility earning is on the PAYABLE good (good == reported in the thin
        # slice; diverges once Missing/Alter ship). Settlement pays good via the resolver.
        c.expected_earning = (c.good_quantity * rate).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP)
        c.role_snapshot = role
        c.save(update_fields=['expected_rate', 'expected_earning',
                              'role_snapshot', 'updated_at'])
    stage_rate_service.mark_locked(rate_row)   # first completion → rate immutable
    task.status = WorkerStageTask.Status.COMPLETED
    task.completed_at = timezone.now()
    task.save(update_fields=['status', 'completed_at', 'updated_at'])
    logger.info("worker_task.complete task=%s contributions=%s rate=%s role=%s",
                task.pk, task.contributions.count(), rate, getattr(role, 'pk', None))
    return task


@transaction.atomic
def set_verified_quantity(contribution, quantity, *, actor):
    """P1 (F5-lite, ADR-0009-adjacent): management corrects PRODUCTION truth —
    sets/clears `verified_quantity` on a completed contribution. The worker's
    `reported_quantity` is NEVER touched (both preserved — owner §6/§7).
    Settlement reads verified-else-reported, so this is the lever that fixes a
    typo'd report BEFORE money books.

    Guards:
      • management only;
      • task must be completed/verified (reports in flight are the worker's);
      • a settlement-credited line (active settlement_line) REFUSES — money
        already booked on the old number; reverse the settlement first (same
        philosophy as the V2-3 reopen/void armor).
    quantity=None clears the correction (back to reported).
    """
    from django.core.exceptions import PermissionDenied
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    from production.models import WorkerStageContribution, WorkerStageTask

    if not user_has_role(actor, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can verify quantities.")
    # of=('self',): settlement_line is a nullable FK → LEFT JOIN, and Postgres
    # refuses FOR UPDATE on the nullable side — lock only the WSC row.
    c = (WorkerStageContribution.objects.select_for_update(of=('self',))
         .select_related('task', 'settlement_line')
         .get(pk=contribution.pk))
    if c.task.status not in (WorkerStageTask.Status.COMPLETED,
                             WorkerStageTask.Status.VERIFIED):
        raise ValidationError("Report not submitted yet — nothing to verify.")
    if c.settlement_line_id and c.settlement_line.voided_at is None:
        raise ValidationError(
            "This line was already settled "
            f"({c.settlement_line.adda_settlement.reference}) — reverse that "
            "settlement first, then correct the quantity.")
    if quantity is not None:
        # PA-07-2: same guard as report_contributions — AddaReportReviewView passes the
        # verified value as a raw string; a non-numeric one (tampered/locale comma) would
        # make Decimal() raise InvalidOperation, which the review view's
        # `except (ValidationError, PermissionDenied)` misses → 500.
        try:
            quantity = Decimal(str(quantity))
        except InvalidOperation:
            raise ValidationError("Verified quantity must be a number.")
        if quantity < 0:
            raise ValidationError("Verified quantity cannot be negative.")
        # H-1 (owner-approved 2026-07-06): verification REDUCES or CONFIRMS
        # production — it can never create it. Two ceilings (this is a
        # post-complete money path — settlement pays verified-else-good):
        #   1. never above what the worker reported good;
        if quantity > c.good_quantity:
            raise ValidationError(
                f"Verified quantity ({quantity}) cannot exceed the reported good "
                f"quantity ({c.good_quantity}) — verification reduces or confirms "
                "production, never creates it.")
        #   2. on a piece-pool stage WHERE this worker holds an allocation for
        #      the dimension, never above that allocation (Σ verified-else-good
        #      of the task's OTHER lines on the same dimension counts against
        #      the same ceiling). allocated == 0 → the stage ran un-split —
        #      ceiling 1 alone governs, otherwise verification would be unusable
        #      exactly where corrections are most needed.
        from production.constants import ALLOC_DIM_NONE
        sr_ = c.task.stage_record
        if sr_.workflow_stage.allocation_dimensions != ALLOC_DIM_NONE:
            from production.services import pool_service
            allocated = pool_service.worker_allocated(
                sr_, c.task.worker, c.color_id, c.size_id)
            if allocated > 0:
                siblings = (WorkerStageContribution.objects
                            .filter(task=c.task, color_id=c.color_id,
                                    size_id=c.size_id)
                            .exclude(pk=c.pk))
                others = sum(((s.verified_quantity if s.verified_quantity is not None
                               else s.good_quantity) for s in siblings), Decimal('0'))
                if quantity + others > allocated:
                    raise ValidationError(
                        f"Verified quantity ({quantity}) would take this worker's "
                        f"dimension total to {quantity + others}, above the "
                        f"{allocated} allocated. Allocate more first, or correct "
                        "the allocation.")
    old = c.verified_quantity
    if old == quantity:
        return c        # no-op — no row churn, no timeline noise (R6)
    c.verified_quantity = quantity
    c.save(update_fields=['verified_quantity', 'updated_at'])
    # R6 (PDD §31.1-F6): DB-resident audit on the Adda timeline — who/old/new/
    # when, never dependent on this log line. Same atomic txn as the write
    # (event and correction commit or roll back together). History goes
    # through log_adda — the single AddaHistory writer (rule 5).
    from tracking.services import log_adda
    from tracking.models import AddaHistory
    sr = c.task.stage_record
    worker = c.task.worker
    log_adda(
        sr.adda, AddaHistory.ChangeType.VERIFIED_QTY_CORRECTED, actor,
        stage_record=sr,
        note=(f"{worker.get_full_name() or worker.email}: "
              f"{old if old is not None else 'reported'} → "
              f"{quantity if quantity is not None else 'cleared (reported)'}"),
        metadata={
            'contribution': c.pk,
            'worker': worker.get_full_name() or worker.email,
            'worker_id': worker.pk,
            'stage': sr.workflow_stage.stage.name,
            'reported': str(c.reported_quantity),
            'old': str(old) if old is not None else None,
            'new': str(quantity) if quantity is not None else None,
        })
    logger.info("worker_task.verify_qty wsc=%s task=%s qty=%s by=%s",
                c.pk, c.task_id, quantity, actor.pk)
    return c
