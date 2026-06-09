# V2-1 Pre-Implementation Review — WorkerStageTask + WorkerStageContribution + workers-M2M migration

> Companion to [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md) (§2 production models, §8 LOCK/BUILD, §11 locked
> settlement). **Status: REVIEW — design only, no code, no migration generated, dev DB untouched.**
> Purpose: surface migration risks, rollback strategy, and dependency impact BEFORE implementation.

## 1. Scope of V2-1 (the production-truth foundation — the BUILD-NOW bucket)
Build the two new production-truth models and migrate the bare `AddaStageRecord.workers` M2M onto them.
**In scope:** `WorkerStageTask` (lifecycle + object-level Assignment), `WorkerStageContribution`
(dimensional quantity + frozen `expected_*` at complete), the M2M→Task data migration, repointing the
18 reader/writer sites, and the assignment-isolation security fix. **Out of scope (later waves):** the
worker self-report UI, settlement, SWA repurpose, missing/alter modules. **No money in V2-1** — Option B
means the only financial effect is freezing `expected_*` (visibility), never a ledger write.

## 2. Target models (exact field specs — to confirm before coding)
**`WorkerStageTask`** (production)
```
stage_record   FK production.AddaStageRecord  PROTECT  related_name='worker_tasks'
worker         FK AUTH_USER_MODEL             PROTECT  related_name='stage_tasks'
status         Char  assigned|in_progress|completed|verified|cancelled   (cancelled = terminal)
started_at / completed_at / verified_at   DateTime null
verified_by    FK AUTH_USER_MODEL  PROTECT null   (verification OPTIONAL, non-blocking)
notes          Char/Text blank
+ TimeStampedModel (created_at/updated_at)
Meta:
  UniqueConstraint(stage_record, worker, condition=~Q(status='cancelled'))   # one ACTIVE task per (sr,worker)
  Index(stage_record) ; Index(worker, status)
```
**`WorkerStageContribution`** (production, ≥1 per task)
```
task              FK WorkerStageTask  PROTECT  related_name='contributions'   (PROTECT: may feed a settlement)
color             FK raw_materials.ClothColor  PROTECT null     # capture day one — un-backfillable
size              FK production.ProductSize    PROTECT null
reported_quantity Decimal(12,2)                                  # worker-entered, LOCKED after submit
verified_quantity Decimal(12,2) null                             # manager/supervisor/super_admin only
expected_rate     Decimal(10,4)                                  # FROZEN at complete (matches earning_rate_snapshot 4dp)
expected_earning  Decimal(12,2)                                  # FROZEN at complete = reported × expected_rate
bundle_item       FK production.CuttingBundleItem  PROTECT null  # optional piece-precision
+ TimeStampedModel
Meta: Index(task)
```
> Decimal widths + PROTECT posture deliberately mirror the existing `StageWorkAssignment` so the future
> settlement-written SWA can copy dimensions 1:1. `expected_*` freeze is BUILD-NOW (§8) but writes **no
> ledger row** (Option B).

## 3. Current state — the `workers` M2M and its 18 touch-points
`AddaStageRecord.workers = ManyToManyField(User, related_name='stage_assignments', blank=True)`
→ Django join table **`production_addastagerecord_workers`** (bare: only `addastagerecord_id`,
`user_id` — NO per-worker status/timestamps). Defined [adda.py:101](../config/production/models/adda.py#L101);
its docstring still claims a future `StageWorkAssignment through=` conversion — **stale** (V2 supersedes
that with a separate `WorkerStageTask`; fix the comment during V2-1).

**Writers (set/add — full-replace semantics):**
| Site | Call | Note |
|---|---|---|
| `adda_service.py:119` | `sr.workers.set(skilled_pks)` | layering first-stage pool snapshot (Hardcode #1) |
| `layering/service.py:234` | `sr.workers.set(worker_ids)` | layering assign |
| `layering/service.py:261` | `sr.workers.add(user)` | via `sync_layering_workers_for_skill` |
| `cutting/service.py:421` | `sr.workers.set(worker_id_list)` | cutting assign |
| `cutting/service.py:983` | `sr.workers.set(worker_ids or [])` | cutting reassign |
| `cutting_pattern/service.py:216` | `sr.workers.set(...)` | pattern assign |
| `barcode_generation/service.py:212` | `sr.workers.set(...)` | barcode assign |

**Readers (membership / list):**
| Site | Call | Purpose |
|---|---|---|
| `_shared.py:43` | `sr.workers.filter(pk=user.pk).exists()` | `_ensure_assigned_worker` — **the isolation guard** |
| `layering/service.py:132` | `sr.workers.all()` | snapshot panel |
| `stage_views.py:145,213,926,941,1003` | filter/exists, values_list, `.all()` | panel gate + allocation workers |
| `pattern_stage_views.py:160,208` | filter/exists, values_list | panel gate + form |
| `barcode_gen_views.py:110,147` | filter/exists, values_list | panel gate + form |

**Cross-app + side effects:** `accounts/services/user_service.py:104-105` calls
`sync_layering_workers_for_skill` (the **accounts→production back-edge**, also targeted by remediation
M4.1). Every assign logs `AddaHistory.WORKERS_ASSIGNED` (tracking) at 5 sites.

## 3.1 FINAL grep-level dependency audit (2026-06-09) — COMPLETE inventory
> The §3 "18 touch-points" count was **INCOMPLETE**. A multi-vector sweep (attribute access · reverse
> accessor · field-name lookups · string refs · `.through` · raw join-table SQL · templates) found the
> **hidden readers below**. This §3.1 is the authoritative map; §3 above is the first-pass that it corrects.

**Vectors swept (exhaustive for a Django M2M):** `.workers` attr (variable-agnostic) · reverse
`stage_assignments` · `workers=` / `workers__` lookups · `'workers'` string (prefetch/values/forms) ·
`.workers.through` · raw `production_addastagerecord_workers` · all `.html`.

**WRITERS — 7 call sites (M2M mutation):** `adda_service:119`, `layering:234`, `layering:261` (via
`sync_layering_workers_for_skill`), `cutting:421`, `cutting:983`, `cutting_pattern:216`, `barcode_generation:212`.
*(No `form.save()` writer — the assign forms are plain `forms.Form`, not ModelForm; see FORMS below.)*

**READERS — Python (15 sites):**
- *production (already in §3, 11):* `_shared.py:43` (isolation guard) · `layering/service.py:132` (snapshot) ·
  `stage_views.py:145,213,926,941,1003` · `pattern_stage_views.py:160,208` · `barcode_gen_views.py:110,147`.
- **⚠ MISSED in §3 — `inventory/views/dashboard.py` (3):** `:85` `.filter(workers=request.user, …)` (worker's
  "my active stages" — **an isolation surface**), `:103` `.prefetch_related('workers')`, `:110`
  `active_layering.filter(workers=request.user)` (helper layering). **`inventory` is therefore a reader app.**
- **⚠ MISSED in §3 — `adda_views.py:131`** `.prefetch_related('workers')` (Adda detail, feeds stage-panel display).

**READERS — templates (4 direct `X.workers.all` + indirect):**
- direct: `_stage_panel_barcode_gen.html:103`, `_stage_panel_cutting_pattern.html:243`,
  `_stage_panel_cutting.html:176`, `templates/inventory/user_dashboard.html:302`.
- indirect (via context vars, already counted at their view/service): `allocation_workers`
  (`_stage_panel_cutting.html:692` ← `stage_views.py:941`); the layering snapshot `'workers'` key
  (`_layering_summary.html` / `_stage_panel_layering.html` ← `layering/service.py:132`); the Adda-detail
  prefetched `workers` (← `adda_views.py:131`).
- `{{ *_form.workers }}` widgets (barcode/pattern/cutting/layering panels) render the FORM field, not a
  record's M2M — handled under FORMS.

**FORMS (assignment input — feed the chokepoint, NOT direct M2M writers):** `workers =
ModelMultipleChoiceField` on plain `forms.Form` classes — `BarcodeGenStartForm` (`barcode_gen_views.py:70`,
queryset `:79`), `PatternStartForm` (`pattern_stage_views.py:83`, queryset `:97`), `CuttingForm` (workers
field). The view reads `cleaned_data['workers']` → passes `worker_ids=[…]` to the service
(`stage_views.py:368,868,1047`; `pattern:270`; `barcode:195`), which does `sr.workers.set()`. So forms are
upstream of the writers — relevant to V2-1b/c UI, not a hidden write path.

**Confirmed CLEAN / not-a-dependency:**
- **Reverse accessor `user.stage_assignments`** — defined (`adda.py:102`) but **ZERO readers** in code or
  templates → drops harmlessly with the M2M in V2-1d.
- **`.workers.through`** — none. **Raw SQL on `production_addastagerecord_workers`** — none (only a comment).
- **False positives** (different `workers`): `expense/views.py:153` (`ctx['workers']` = payroll list) +
  `expense/.../payroll_overview.html:66`.

**TESTS exercising the M2M (characterization scope — 8 files, 15 refs):** `test_layering_workflow`,
`test_cutting_workflow`, `test_cutting_breakdown_materialization`, `test_barcode_generation_workflow`,
`test_stage_credit`, `test_open_closed_proof`, `test_phase4` (production); `test_barcode_export` (tracking).

**CONCLUSION — confidence statement:** every route to `AddaStageRecord.workers` falls into one of the
swept vectors; all are now enumerated. **No hidden writers** (the only mutations are the 7 `.set()/.add()`
sites; forms aren't ModelForm-bound). The hidden *readers* were the 3 `inventory` dashboard sites + the
1 Adda-detail prefetch + 4 direct template reads — now captured. The map is **complete**; V2-1b reader-repoint
scope must include `inventory/views/dashboard.py` and the 4 templates, not just production services/views.

**~6 templates** render the worker list (`_workers_widget.html`, the stage panels, `user_dashboard.html`).

## 4. The migration (strangler — never drop-recreate)
**4a. Forward data migration (reversible `RunPython`, rehearsed on a DB clone per P0.5):**
For each `(addastagerecord_id, user_id)` row in `production_addastagerecord_workers`, create a
`WorkerStageTask`:
- `status`: stage `completed_at` not null → **`completed`**; else → **`assigned`** (conservative — we do
  NOT know an active-stage roster member actually started; don't fabricate `in_progress`). ← owner Q1.
- `started_at` = `sr.started_at`; `completed_at` = `sr.completed_at` (stage-level — see Risk R1).
- `verified_*` = null (no historical verification concept).
- **No `WorkerStageContribution` rows are backfilled** — the M2M holds no quantity/color/size, so
  per-worker production history is **unreconstructable**. Existing Addas get tasks, zero contributions;
  contributions (and `expected_*`) exist only for work completed *after* V2-1. This is acceptable (pre-V2
  there were no expected snapshots) but must be stated, not silent. ← Risk R2.

**4b. Coexistence window (strangler):** keep the `workers` M2M column **live** while both the M2M and
`WorkerStageTask` are written (dual-write) and readers are repointed one at a time behind parity tests.
Drop the M2M only in a final follow-up PR after every reader uses `WorkerStageTask`. **No big-bang swap.**

## 5. Migration RISKS (enumerated)
- **R1 — per-worker timeline loss (low, accepted).** The M2M has no per-worker timestamps; backfilled
  tasks inherit the *stage-level* `started_at`/`completed_at`. Historical per-worker timing can't be
  reconstructed. Accept; new tasks capture real per-worker times.
- **R2 — no contribution backfill (medium, document).** Historical expected earnings/quantities don't
  exist on the M2M → can't be created. Reports over old Addas show tasks but no contribution lines.
  Mitigation: scope contribution-dependent UI to post-V2 Addas; label clearly.
- **R3 — `.set()` full-replace semantics change (HIGH — the sharpest one).** M2M `.set()` *removes*
  absent members outright. So the set-equivalent becomes a **reconcile service**: add missing as
  `assigned`; for removed members → **always `cancel` (terminal), NEVER delete** (owner Q2 — uniform
  immutable history, whether or not contributions exist). Behavior change: un-assigning a worker who
  already reported work *cancels* their task and retains their contributions. Every `.set()` writer
  (6 sites) must route through this reconcile, never a raw delete.
- **R4 — unique-constraint vs re-assign (medium).** M2M is naturally unique per `(sr,user)`. The partial
  `UniqueConstraint(stage_record, worker, condition=~Q(status='cancelled'))` allows re-assigning a
  previously-cancelled worker (a new active task) without colliding. Without the partial condition,
  re-assign would `IntegrityError`. Django 5.0.1: use `condition=` on `UniqueConstraint` (NOT `check=`).
- **R5 — assignment guard timing (security, HIGH).** `_ensure_assigned_worker` is the isolation guard.
  During coexistence it must check `WorkerStageTask` (active, non-cancelled), not the M2M, the moment
  Task becomes the writer — else a cancelled worker keeps access. Repoint the guard FIRST among readers.
- **R6 — cross-app edge (`sync_layering_workers_for_skill`).** It writes the M2M from an accounts
  service. Under V2-1 it must write `WorkerStageTask`. Good moment to also execute remediation **M4.1**
  (relocate the orchestration out of accounts) — but keep the two changes in *separate* PRs to bound risk.
- **R7 — `model_label`/autodiscovery (low).** New models live under conventional `production/models/`
  (NOT a `stages/<stage>/` folder), so the M2.1 import-time model autodiscovery does NOT apply here —
  no `app_label` gymnastics. Standard app models. (If later moved into a stage folder, that's a separate
  concern.)

## 6. Rollback strategy
- **Reverse `RunPython`** repopulates the M2M from `WorkerStageTask` (active tasks → `workers.add`) and
  the schema migration drops the two new tables. Because the M2M is **kept** through the coexistence
  window, a rollback during that window is a pure table-drop — the M2M never stopped being authoritative
  until the final drop PR.
- **Rehearse up+down on a clone of the dev DB** before applying (P0.5). The forward backfill + reverse
  must round-trip with zero row loss on the clone.
- **Feature-flag the reader cutover** (or do it reader-by-reader behind parity tests) so the Task path
  can be reverted to the M2M path without a migration.
- **Point of no return** = the final "drop M2M column" PR. Everything before it is reversible.

## 7. Dependency impact (revised per the §3.1 audit)
- **production** — 2 new models, ~16 internal sites repointed (7 writers via the chokepoint + 11 reader
  sites), 1 stale docstring fixed. Import-linter: **no new edges** (Task/Contribution are production-internal).
- **inventory** — ⚠ **NEW (was missing): 3 reader sites in `views/dashboard.py`** (`:85`/`:110`
  `filter(workers=user)` — the worker's own-stages isolation query — + `:103` prefetch). The
  `inventory → production` edge **already exists**, so reading `WorkerStageTask` adds **no new edge**; but
  inventory IS in the V2-1b repoint scope, and `:85`/`:110` are **security-sensitive** (own-stage visibility).
- **accounts** — `sync_layering_workers_for_skill` call becomes a Task writer (still the existing edge;
  M4.1 relocation is a *separate* PR).
- **tracking** — `WORKERS_ASSIGNED` history is unchanged (still logged at assign time).
- **expense** — **none in V2-1.** Contributions feed settlement *later*; SWA untouched; ledger untouched.
  (`expense/views.py:153` `ctx['workers']` is a false-positive, unrelated to the M2M.)
- **templates** — repoint the **4 direct `X.workers.all` reads** (`_stage_panel_barcode_gen`,
  `_stage_panel_cutting_pattern`, `_stage_panel_cutting`, `user_dashboard.html`) + the indirect consumers
  (`allocation_workers`, layering-snapshot `workers` key, Adda-detail prefetch) to the Task-derived view-model.
- **tests** — characterization on the 8 M2M test files BEFORE refactor (write against the service facade,
  not module paths — they move in M2); an M2M↔Task parity test during coexistence; up/down migration test
  on a clone.

## 8. Recommended sub-PR sequence (each green before the next)
1. **V2-1a** — add `WorkerStageTask` + `WorkerStageContribution` models + the reversible backfill
   migration, **behind dual-write** (writers update BOTH M2M and Task). M2M stays authoritative. Parity test.
2. **V2-1b** — repoint readers to `WorkerStageTask`, **guard (`_ensure_assigned_worker`) FIRST** (R5),
   then the **`inventory` dashboard isolation queries** (`dashboard.py:85,110` — security-sensitive) +
   `:103` prefetch, the `adda_views.py:131` prefetch, and the **4 direct-read templates** (§3.1).
   `.set()` writers route through the reconcile service (R3). Flip authority to Task.
3. **V2-1c** — worker self-report contributions + freeze `expected_*` at task-complete (no ledger).
   Assignment-isolation fix (the HIGH leak: dashboards/panels gate by Task membership, not skill alone).
4. **V2-1d** — drop the `workers` M2M column (point of no return) + fix the stale docstring.

## 9. Owner decisions — RESOLVED (2026-06-09)
- **Q1 → `assigned`** for active-stage roster members; **`completed`** for completed stages. Backfill
  only facts known from historical data; never infer/invent workflow states that were never recorded.
- **Q2 → cancel task, keep contributions.** Un-assign = task → terminal `cancelled`; reported
  contributions + audit + (future) settlement/defect traceability are retained. Assignment can change;
  production history cannot.
- **Q3 → ACCEPTED** the partial `UniqueConstraint(stage_record, worker, condition=~Q(status='cancelled'))`
  — one active task per (sr, worker); cancelled workers re-assignable.
- **Q4 → separate later PR.** V2-1b makes the sync a Task writer at behavior-parity only; the
  accounts→production edge relocation (remediation **M4.1**) is its own PR *after* the WorkerStageTask
  foundation is stable. Do not mix migration risk with coupling-remediation risk.

### Two governing principles (owner, 2026-06-09) — apply throughout V2-1
1. **Backfill only known facts.** A data migration must not fabricate states the source never recorded.
   (Drives Q1: roster ≠ "started work".)
2. **Work that happened is immutable history.** Assignment is mutable; production history (contributions,
   audit, settlement, defect traceability) is append-only and never erased by a roster change.
   (Drives Q2 + R3: un-assign cancels, never deletes.)

---

# §10 — V2-1a implementation review (deep dive)

> **Status: ✅ BUILT 2026-06-09 (uncommitted; migrations applied to dev DB).** Delivered:
> `WorkerStageTask` model + migrations `0031`/`0032` (rehearsed on a clone, round-trip verified,
> APPLIED to dev — 0 backfilled, dev empty), the dual-write chokepoint
> `production/services/worker_task_service.py` (`set_stage_workers`/`add_stage_worker`) behind
> `WORKER_TASK_DUAL_WRITE` (base.py), all 7 writer sites routed through it, 15 tests
> (`production/tests/test_worker_task.py` — model constraints, backfill logic, dual-write parity/reconcile,
> flag-off), the anti-drift gate in `scripts/check.sh` [4/4]. Full suite **366 OK**. M2M still
> authoritative; readers unchanged → no user-visible change. **NOT committed** (owner approval pending).
> V2-1a = the FIRST sub-PR: introduce the model, backfill from the M2M, and **dual-write** while the
> M2M stays authoritative and all readers keep reading the M2M.

### 10.0 Scope refinement (recommendation — confirm)
- **V2-1a = `WorkerStageTask` ONLY.** Defer `WorkerStageContribution` to **V2-1c**, where its writer (the
  self-report UI + `expected_*` freeze) actually lands. Rationale: Contribution has no rows and no reader
  until V2-1c; adding it now would freeze its nullability (`expected_*` is null-until-complete) before the
  code that defines that behavior exists. Smaller V2-1a = smaller blast radius. *(Supersedes the §8
  sketch that put both models in V2-1a.)* ← decision D-A1.
- **V2-1a precondition:** migrations `0029_workflowstage_credits_workers` + `0030_seed_cutting_credits_workers`
  are **on-disk but UNAPPLIED** on the dev DB. V2-1a's migrations stack as `0031`/`0032` on `0030`, so
  `0029/0030` MUST be applied (and rehearsed) first. The app 500s on the `credits_workers` column until
  `0029` is applied — apply the pending pair before V2-1a work begins. ← decision D-A2.

### 10.1 Exact model definition (V2-1a)
```
class WorkerStageTask(TimeStampedModel):          # core.TimeStampedModel → created_at/updated_at
    class Status(models.TextChoices):
        ASSIGNED    = 'assigned', 'Assigned'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED   = 'completed', 'Completed'
        VERIFIED    = 'verified', 'Verified'
        CANCELLED   = 'cancelled', 'Cancelled'    # terminal
    stage_record = FK('production.AddaStageRecord', PROTECT, related_name='worker_tasks')
    worker       = FK(AUTH_USER_MODEL, PROTECT, related_name='stage_tasks')
    status       = Char(max_length=12, choices=Status.choices, default=Status.ASSIGNED)
    started_at   = DateTime(null=True, blank=True)
    completed_at = DateTime(null=True, blank=True)
    verified_at  = DateTime(null=True, blank=True)
    verified_by  = FK(AUTH_USER_MODEL, PROTECT, null=True, blank=False, related_name='+')
    notes        = Char(max_length=200, blank=True)
    class Meta:
        constraints = [
            UniqueConstraint(fields=['stage_record','worker'],
                             condition=~Q(status='cancelled'),
                             name='uniq_active_worker_task_per_stage'),   # ≤1 active task per (sr,worker)
            CheckConstraint(check=models.Q(status__in=[*Status.values]), name='workerstagetask_status_valid'),
        ]
        indexes = [Index(fields=['stage_record']), Index(fields=['worker','status'])]
        ordering = ['stage_record','worker']
```
Notes: `max_length=12` fits `in_progress`. `verified_by` mirrors the codebase posture `null=True` **without**
`blank=True` (DB-nullable, form-required — matches `created_by`/`entered_by` everywhere). `condition=` (NOT
`check=`) on the partial `UniqueConstraint` per Django 5.0.1 (the existing `uniq_one_reversal_per_entry`
uses the same idiom); `check=` on the `CheckConstraint`. PROTECT on both FKs — never orphan a task that may
later carry contributions/settlement.

### 10.2 Migration sequence (V2-1a — two migrations, schema then data)
1. **`0031_workerstagetask.py`** — `CreateModel(WorkerStageTask)` + constraints + indexes. Pure schema,
   additive, trivially reversible (drops the table). Depends on `0030`.
2. **`0032_backfill_worker_tasks.py`** — `RunPython(forward, reverse)`, depends on `0031`. Uses the
   **historical** model via `apps.get_model('production','AddaStageRecord')` and `WorkerStageTask`.
   - **forward:** for each `AddaStageRecord` with M2M members, for each `(sr, worker)`:
     `get_or_create` a task (idempotent) with `status = 'completed' if sr.completed_at else 'assigned'`,
     `started_at = sr.started_at`, `completed_at = sr.completed_at` (stage-level — R1), `verified_* = null`.
     Wrap the whole loop in `transaction.atomic` (all-or-nothing). Batch with `bulk_create(ignore_conflicts=True)`
     guarded by the partial unique for large sets (low volume here → simple loop is fine).
   - **reverse:** `WorkerStageTask.objects.all().delete()` — explicit + clean (the M2M is still authoritative,
     so deleting shadow tasks loses nothing; makes a down→up cycle idempotent).
   - **historical-model caveat:** M2M access in a data migration goes through the historical relation —
     read membership via `sr.workers.all()` on the historical `AddaStageRecord`; do NOT import the live model.
3. **No `WorkerStageContribution` migration in V2-1a** (per D-A1).

### 10.3 Dual-write implementation strategy
- **One chokepoint function** (e.g. `production.services.assign_stage_workers(stage_record, worker_ids, *, user)`)
  replaces all 6 raw `sr.workers.set(...)/.add(...)` calls. It does, **inside the caller's `@transaction.atomic`**:
  (a) `sr.workers.set(worker_ids)` — M2M stays authoritative; (b) **reconcile** `WorkerStageTask`:
  create-or-reactivate an active task for each id in the set; for ids no longer present, **`cancel`** the
  active task (never delete — R3); leave already-active tasks untouched (idempotent).
- **Atomicity:** M2M write and Task reconcile share ONE transaction → they can never diverge on commit.
  If the Task side raises, the M2M write rolls back too (manager sees an error, nothing half-written).
- **Feature flag `WORKER_TASK_DUAL_WRITE` (recommend).** Gate the Task reconcile so it can be disabled
  instantly (no redeploy) if it ever causes an assign to fail. Flag ON in V2-1a after parity is verified;
  it becomes unconditional in V2-1b. ← decision D-A3.
- **Anti-drift gate:** forbid raw `.workers.set(`/`.workers.add(` outside the chokepoint (grep check in
  `scripts/check.sh`), so no writer silently bypasses the dual-write.
- **Readers unchanged in V2-1a** — still `sr.workers...`. Task is write-only/shadow until V2-1b.

### 10.4 Rollback walkthrough (V2-1a is fully reversible — M2M never stops being truth)
1. **Code rollback:** flip `WORKER_TASK_DUAL_WRITE` off → instantly back to M2M-only writes, no redeploy,
   no migration. Tasks freeze but are harmless (unread).
2. **Migration rollback:** `migrate production 0030` → runs `0032` reverse (delete all tasks) then `0031`
   reverse (drop table). M2M is intact and authoritative throughout; zero data loss.
3. **Full revert:** revert the chokepoint code (writers return to plain `.set()`), drop the two migrations.
4. **Point of no return: NONE in V2-1a.** (That arrives only at V2-1d's M2M drop.)
5. **Rehearse up→down→up on a clone** (P0.5) before touching the dev DB: assert row-count parity and a
   clean round-trip.

### 10.5 Concurrency risks
- **C1 — backfill vs live assigns.** If `0032` runs while a manager assigns, a row could be created twice.
  Mitigation: `get_or_create` + the partial unique constraint (DB backstop) make backfill idempotent; on a
  1-factory low-traffic app, run the migration during the deploy window. No online-migration tooling needed.
- **C2 — concurrent reconciles on one `stage_record`.** Two managers reassign the same stage at once →
  could race to create a second active task. The partial unique is the DB backstop (one tx wins,
  `IntegrityError` on the other). Recommend the chokepoint take `select_for_update()` on existing
  `worker_tasks` for that `stage_record` (or on the Adda, matching the advance lock) to serialize cleanly.
  (Today's raw `.set()` is unlocked too — so this is *no worse*, and the constraint makes it *safer*.)
- **C3 — dual-write partial visibility.** None — single transaction; readers see M2M only in V2-1a.

### 10.6 Data-integrity risks
- **D1 — idempotency / duplicates** → `get_or_create` on `(stage_record, worker)` among non-cancelled +
  partial unique. Backfill creates only `assigned`/`completed` (never `cancelled`), so no constraint clash.
- **D2 — legacy NULL `started_at` on completed stages.** Pre-layering-workspace rows: `completed_at` set,
  `started_at` null → task = `completed` with `started_at=null`. Known-legacy shape; do not synthesize a
  start time (principle #1). Document.
- **D3 — empty rosters.** `workers` is `blank=True`; some stage_records have zero members → zero tasks.
  Correct, not an error.
- **D4 — user-deletion posture change.** M2M auto-cleans if a user is deleted; Task FK is PROTECT → a user
  with tasks can't be hard-deleted. Going forward this is the *desired* stricter posture (workers aren't
  deleted under live work); backfill only references existing users so no failure.
- **D5 — parity definition.** Invariant for V2-1a: `set(sr.workers.all()) == {t.worker for t in
  sr.worker_tasks if t.status != 'cancelled'}` for every stage_record. A management command asserts this
  fleet-wide post-deploy.

### 10.7 Test plan (V2-1a)
- **Characterization (before any change):** snapshot current M2M behavior at all 6 writer + reader sites,
  written against the **service facade** (not module paths — they move in M2). Lock the 305-test baseline.
- **Model tests:** partial unique (2 active tasks for one (sr,worker) → `IntegrityError`; 1 active + N
  cancelled → OK; re-assign after cancel → OK); status choices; PROTECT on worker/stage_record.
- **Migration tests:** seed a fixture DB covering {active stage w/ roster, completed stage w/ roster, empty
  roster, completed stage w/ null started_at}; run `0032` forward → assert status mapping + timestamps;
  run reverse → assert table empties cleanly; **round-trip up→down→up** with zero drift.
- **Idempotency:** run backfill twice → no duplicate tasks.
- **Dual-write parity:** after each of the 6 writer paths, assert the D5 invariant. Include an un-assign
  case → asserts the dropped worker's task is `cancelled` (not deleted) and any contributions (none yet in
  V2-1a) would be retained.
- **Concurrency (optional):** two reconciles on one stage_record → exactly one active task survives.
- **Flag test:** `WORKER_TASK_DUAL_WRITE=off` → only M2M written, no tasks; `on` → both.
- **Gate:** full suite green + import-linter (no new edges) + the anti-drift grep check.

### 10.8 Deployment sequence (V2-1a)
1. **Pre:** apply + rehearse pending `0029/0030` on a clone, then the dev DB (clears the `credits_workers`
   500). Confirm 305 green.
2. **Rehearse V2-1a on a clone:** `0031`+`0032` up, parity command, down, up again.
3. **Deploy** code (model + chokepoint dual-write + flag default ON) + run `0031`,`0032`.
4. **Post-deploy:** run the parity command fleet-wide → expect zero drift. App behavior unchanged (readers
   still on M2M). Low-traffic / 1-factory → a short window for the backfill is trivial; no online tooling.

### 10.9 Cutover strategy (V2-1a = shadow, NOT the real cutover)
- The real read-cutover is **V2-1b**. V2-1a only turns on dual-write behind the flag.
- Sequence: backfill establishes Task == M2M → dual-write keeps them in lockstep → parity command proves
  zero drift over a soak period → **only then** proceed to V2-1b (flip readers).
- Users see nothing change in V2-1a. Zero-risk, reversible, observable (parity command is the gate to V2-1b).

### 10.10 Failure scenarios + responses
| # | Failure | Blast radius | Response |
|---|---|---|---|
| F1 | Backfill `0032` errors mid-run | none (atomic → rolls back; migration stays unapplied) | fix data assumption, re-run; M2M untouched |
| F2 | Dual-write Task reconcile throws in prod (latent dup/constraint) | an assign action 500s (M2M also rolls back — no half-write) | flip `WORKER_TASK_DUAL_WRITE` off instantly → M2M-only; fix; re-enable |
| F3 | Parity drift detected by the command | reporting only (readers still on M2M) | find the writer bypassing the chokepoint (anti-drift grep should've caught it); reconcile + add the missing call |
| F4 | A writer path was missed entirely | that path's tasks stale | parity command flags it; route it through the chokepoint |
| F5 | Need to roll back after backfill + live assigns | none | reverse `0032` (delete tasks) + `0031` (drop table); M2M authoritative throughout |
| F6 | V2-1a deployed without applying `0029/0030` | migration dependency error at deploy | precondition check (D-A2) blocks deploy until pending pair applied |
| F7 | Concurrent reconciles double-create | one tx errors | partial unique backstops; `select_for_update` (C2) serializes; retry |

### 10.11 V2-1a decisions — RESOLVED (2026-06-09)
- **D-A1 → CONFIRMED:** V2-1a = `WorkerStageTask` only; `WorkerStageContribution` deferred to V2-1c.
- **D-A2 → REQUIRED:** apply pending `0029/0030` (rehearsed on a clone) before V2-1a begins.
- **D-A3 → CONFIRMED:** dual-write ships behind a `WORKER_TASK_DUAL_WRITE` flag (ON after parity verified;
  unconditional in V2-1b).
- **D-A4 → ACCEPTED:** chokepoint takes `select_for_update` on the stage_record's tasks (or the Adda) to
  serialize concurrent reconciles.

### 10.12 Clarifications locked before implementation (owner, 2026-06-09)
1. **`verified` is OPTIONAL and is NOT a workflow blocker.** The `WorkerStageTask` status set includes
   `verified`/`verified_at`/`verified_by`, but the **business gate is unchanged**: a stage advances only
   when **all assigned workers' tasks are `completed`** — verification is **never required** to advance and
   may be skipped entirely. Verification is a **future enhancement** (a manager review step that may later
   set `verified` / correct `verified_quantity`); making it a gate is a **policy change with no schema
   change** (the fields already exist). V2-1a/V2-1b advance logic must read `completed`, not `verified`.
   *(Consistent with ARCHITECTURE_V2 §3 `ready_for_advance` and §4.)*
2. **`WorkerStageTask` is the future traceability anchor for `MissingPieceCase` + `AlterCase`** — but **no
   such models are introduced in V2-1a.** When those modules are built (own future PRs, §11.11), a missing
   or alter/rework investigation will reference the relevant `WorkerStageTask` (who was assigned, when they
   completed, their contributions) to trace *where/when/by-whom* a defect or shortfall originated. V2-1a
   only needs to ensure `WorkerStageTask` carries the stable `(stage_record, worker)` identity + lifecycle
   timestamps those future cases will point at — which it already does. **No new model, FK, or field in
   V2-1a for this; it is an architectural intent note only.**
