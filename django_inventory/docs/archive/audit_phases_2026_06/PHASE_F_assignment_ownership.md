> **ARCHIVED 2026-07-13** — 2026-06 production-readiness audit phase; findings closed, superseded by the current frozen architecture ([../../MANUFACTURING_V1_FREEZE.md](../../MANUFACTURING_V1_FREEZE.md)). Kept for history (Phase-7 DOCCLEAN-D). Its own outbound links reflect the 2026-06 tree.

# Phase F — Assignment & Work Ownership

**Scope:** ownership model, worker task visibility ("My Queue"), manager assignment monitoring, cross-worker coordination, assignment lifecycle, future-domain integration. **Grounded in current code/behavior.**
**Out of scope (locked, not re-litigated):** the allocation model itself (worker × color × size × quantity), allocation-bounded reporting, good/alter/missing — those are the Production-Truth Foundation. This phase covers only the **ownership/visibility/monitoring** gaps that remain *outside* those locked decisions. Where the foundation already addresses a gap, it's noted, not re-argued.

---

## Verdict
The assignment **primitive and lifecycle are solid and complete**; the worker side has a real queue. The gaps are on the **management/monitoring side** — there is no cross-Adda assignment overview, no "who hasn't reported" surfacing, and assignment *intent* is discarded at stage completion. These compound as volume and future teams arrive, and they are **not** covered by the locked foundation.

---

## Findings

### MEDIUM

**F-1 — No cross-Adda / cross-worker assignment-monitoring view.** *visibility / bottleneck* · confidence HIGH
- Current: assignment lives per-stage (`set_stage_workers` in each stage workspace). To see who is assigned to what, a manager opens **each Adda → each stage**. The production dashboard shows **stage counts** ("0 at Cutting, 1 at Layering"), not **per-worker** assignment/status.
- Gap: no single "all workers × what each is assigned to × pending vs done" overview. At 2 Addas it's fine; with many Addas + future teams (stitching/finishing/packing) it's a real bottleneck — a manager can't answer "who is working on what right now?" without clicking through.
- Not in foundation scope (allocation makes ownership explicit but doesn't add a monitoring dashboard). Effort: **M**.

**F-2 — Assignment intent is discarded at stage completion (accountability gap).** *ownership* · confidence HIGH
- `resolve_stage_tasks_on_complete` cancels every still-`assigned`/`in_progress` task when a stage completes, so the completed-stage roster shows **only workers who actually reported** (deliberate "truthful roster > assignment-history" owner decision — [worker_task_service.py:86-105](config/production/services/worker_task_service.py#L86)).
- Consequence: "who was assigned but didn't deliver" survives only as a soft `cancel_note` on a cancelled task — **never surfaced**. A manager cannot later see who dropped work on a stage. Accountability signal is lost.
- Foundation interaction: the locked `WorkerStageAllocation` (persistent allocation rows + history) **would preserve assignment intent** — so the foundation *partially* fixes this. But surfacing "assigned-but-undelivered" is a monitoring/report concern beyond the foundation. Effort: **M**.

**F-3 — No "who hasn't reported yet" surfacing on an in-progress stage.** *visibility* · confidence HIGH
- A manager can only see un-reported assignees by opening the stage workspace and reading the roster. There is no queue/alert "Stage X: 2 of 3 assigned workers haven't reported." Combined with F-2, un-reported workers are then **silently auto-cancelled** at completion with no proactive flag.
- Effort: **M** (a derived "pending reports" view).

### LOW

**F-4 — No workload-balancing visibility.** *future scalability* · confidence MED
- No view of who is overloaded vs idle across Addas. Not needed at current volume; becomes relevant when multiple production teams run in parallel. Effort: **M** (defer).

---

## OK / WORKS-WELL (current strengths)

- **Worker "My Queue" exists and is good:** the dashboard's `my_active_stages` lists each stage the worker has an active task on, with a **report badge** (`needed` / `draft` / `submitted`) so the worker sees exactly what still needs reporting ([dashboard.py:98-131](config/inventory/views/dashboard.py#L98)).
- **Assignment lifecycle is complete and real:** `assigned` → `in_progress` (set on first draft save, [worker_task_service.py:166](config/production/services/worker_task_service.py#L166)) → `completed` (submit) → `verified` (management) / `cancelled`. No dead states.
- **Object-level isolation is strong:** a worker sees only their own tasks and only Addas they're actively assigned to ([dashboard.py:48-55](config/inventory/views/dashboard.py#L48); worker-report resolves own task or 403).
- **No dangling tasks:** `resolve_stage_tasks_on_complete` guarantees a completed stage leaves no unresolved active tasks, and the auto-cancel is audited (cancel note).
- **Per-stage roster** is available in each stage workspace (`active_workers`) — the assignment surface itself works.

## Future-domain integration assessment
- **Structurally extensible:** the open-closed stage-handler registry (verified Phase A) means future stages/teams (stitching, finishing, packing, Missing/Alter as report inputs per the foundation) get the same `WorkerStageTask` assignment + per-stage roster **without view edits**. The assignment *primitive* scales.
- **The monitoring/ownership LAYER does not scale** — F-1/F-3/F-4 are single-Adda-shaped. Before multiple parallel teams exist, the manager needs a cross-team assignment+pending overview that today's per-stage-workspace model doesn't provide.
- **Cross-worker coordination on one stage** (two workers, who does which pieces) is the foundation's allocation job (locked, not re-litigated) — today it's uncoordinated free-report; the foundation's Strict allocation resolves it.

---

## Net Phase F
The assignment engine (primitive + lifecycle + worker queue + isolation) is **sound**. The real gaps are **management visibility**: no cross-Adda assignment overview (F-1), lost assignment-intent/accountability at completion (F-2, partially helped by the foundation's persistent allocation), and no pending-report surfacing (F-3). None block staging at current volume; all become important before multiple production teams arrive. All are monitoring/report additions, **not** changes to the locked foundation.
