# V2-1d Execution Review — WorkerTask Truth Cutover

**Date:** 2026-06-11 · **Status: REVIEW ONLY — no code. Verdict in Part 6 (one
formal gate needs an explicit owner decision before execution).**
Inputs: live grep audit (this doc), V2_1_REVIEW §3.1/§6/§10, ADR 0005,
SOAK_TRACKER (parity history), R0 C2 locked preconditions.

---

## Part 1 — Current State

**Dual-write architecture.** `worker_task_service` is the single chokepoint for
every `AddaStageRecord.workers` write (enforced by check.sh gate [4/5] grep).
`set_stage_workers` writes the M2M **first** (`.set()`, line 59 — still labelled
authoritative) then reconciles WorkerStageTask rows (create-missing /
cancel-removed, `select_for_update`, partial-unique backstop) **gated by
`WORKER_TASK_DUAL_WRITE`** (base.py:177, default True, env kill-switch).
`add_stage_worker` is the additive variant. Since F3/F8,
`resolve_stage_tasks_on_complete` also routes through the chokepoint at every
stage completion.

**M2M responsibilities TODAY (after V2-1b/1c):** it is a **pure shadow**:
1. written by the chokepoint (both fns), 2. read by `check_worker_task_parity`
(by design), 3. read by **one missed template** —
`_stage_panel_cutting_pattern.html:55` `{{ stage_record.workers.count }}` (a
V2-1b escapee found by this review's grep), 4. mentioned in ~6 docstrings/
comments. The reverse accessor `stage_assignments` has zero usages. Nothing
else in runtime code touches it.

**WorkerStageTask responsibilities:** assignment + lifecycle truth (5 statuses,
cancelled terminal, F3/F8 auto-resolution at stage completion), object-level
isolation source (`is_worker_assigned`, dashboard scoping, report-view gate),
readiness input, badge source, audit anchor (cancel notes).

**WorkerStageContribution responsibilities:** dimensional production truth
(grain I3 lines: color/size/qty), draft-vs-completed semantics, frozen
`expected_rate`/`expected_earning` at complete (visibility, no ledger — ADR 0005).

**Still dependent on the M2M:** chokepoint writes · parity command · the one
template count · check.sh gates [4/5] (grep for `.workers.set/.add`) and [5/5]
(parity vs dev DB) · 6 test files asserting M2M↔task parity / roster sync ·
docstrings (incl. adda.py:89-92 = A8). **Nothing functional reads it for
behavior except that one template.**

## Part 2 — Cutover Analysis

| Class | Sites | Disposition at cutover |
|---|---|---|
| Runtime READERS | `_stage_panel_cutting_pattern.html:55` (count) — **the only one** | repoint to `stage_record.active_workers|length` (V2-1b helper) BEFORE the drop |
| Runtime WRITERS | chokepoint lines 59 (`set`) + 117 (`add`) | deleted with the field |
| Tooling | parity command; gates [4/5], [5/5] | final parity run, then retire both; **replacement gate**: grep asserting `worker_task_service` is the sole `WorkerStageTask` writer (the discipline survives the M2M) |
| Flag | `WORKER_TASK_DUAL_WRITE` | retired — its OFF semantics ("M2M-only, tasks stale") become meaningless once tasks are the only store |
| Reporting/UI deps | none — dashboards, panels (except the one above), report UI, badges, isolation all read tasks since V2-1b/P2 | no action |
| Tests | 6 files assert M2M state (dual-write parity, roster sync incl. `test_task_lifecycle`) | rewrite assertions to task-set terms; dual-write-specific tests retire with the mechanism they characterize |
| Docs/comments | adda.py:89-92 (A8), worker_task.py:14 (A8), base.py:173-177, three stage-service side-effect docstrings, barcode.py:24, CLAUDE.md/SYSTEM_DESIGN status lines | all updated in the drop PR |
| Hidden coupling checked | reverse accessor `stage_assignments` (0 uses) · form fields named `workers` (POST params feeding `set_stage_workers` — name coincidence, unaffected) · admin (no reference) · historical migrations 0032/0034 (frozen `apps` models — unaffected by RemoveField) | clear |
| Migration risks | join-table drop; concurrent writes during migrate (single-operator dev DB — none); the ONE template reader if dropped first (500s) — hence reader-first ordering | sequenced below |

## Part 3 — Point Of No Return Review

**Design change that SOFTENS the original plan:** the drop migration gets a
**data-aware reverse**: backward = recreate the M2M field (auto) **+ RunPython
that repopulates membership from non-cancelled WorkerStageTask sets** — which,
by the parity invariant (held through 5 validation runs + gate [5/5] on every
check), equals the dropped data exactly. So:

- **Truly irreversible:** only per-row M2M metadata Django auto-created
  (join-table ids) — carries zero business meaning; and the dual-write
  *mechanism* itself (kill-switch, parity tooling) once deleted — recoverable
  via git, pointless to recover.
- **Reversible:** the membership DATA — reverse migration rebuilds it from task
  truth. "Point of no return" becomes "point of strongly-discouraged return."
- **Rollback strategy (layered):** (1) pre-execution `pg_dump` of dev DB;
  (2) `migrate production 0034` runs the data-aware reverse (M2M rebuilt from
  tasks) + `git revert` the code PR; (3) the dump as last resort.
- **Kill-switch behavior:** ceases to exist at cutover — documented in the PR.
  Pre-cutover it retains its locked semantics (OFF ⇒ tasks stale ⇒ re-backfill
  before re-enable).
- **Clone rehearsal plan (P0.5):** clone dev DB → snapshot
  (per-stage-record M2M sets + task sets + counts) → `migrate` up → verify table
  gone, suite green against clone → `migrate` down → **verify rebuilt M2M sets
  == snapshot exactly** → up again. Rehearsal passes only on exact set equality.
- **Parity validation plan:** gate [5/5] green on every check until execution
  day; one FINAL `check_worker_task_parity` immediately before applying 0035;
  abort on any divergence.

## Part 4 — Migration Plan (no code yet)

**Step 0 — prep PR (reversible, suite-green):**
a. Repoint `_stage_panel_cutting_pattern.html:55` to `active_workers|length`.
b. Make task writes UNCONDITIONAL in the chokepoint (drop the flag *gating*;
   M2M writes stay for now) — tasks formally become the written-always store.
c. Full suite + parity green.

**Step 1 — rehearsal (no repo change):** pre-dump dev DB → clone → run the
Part 3 up/down/up drill with the (locally built) 0035 → exact-set verification.

**Step 2 — drop PR (the cutover):**
a. Migration 0035: RunPython(noop forward / rebuild-from-tasks backward) +
   `RemoveField(AddaStageRecord, workers)`.
b. Chokepoint: delete M2M writes; retire `WORKER_TASK_DUAL_WRITE` from settings.
c. Retire parity command + gates [4/5]/[5/5]; add replacement gate:
   `worker_task_service` = sole WorkerStageTask writer (grep, same pattern).
d. Tests rewritten to task-truth assertions; dual-write characterization tests
   retired with honors.
e. A8 docstrings (adda.py, worker_task.py) + F4 reopen-semantics doc note +
   doc status lines (CLAUDE.md, base.py comment, stage-service docstrings).

**Step 3 — verification sequence:** `makemigrations --check` clean → full suite
green → `grep -rn "\.workers\b" config --include=*.py --include=*.html` returns
ONLY historical migrations → apply to dev DB → browser smoke: assign workers,
worker report draft/submit, stage complete (F3 auto-cancel), badges.

**Deployment sequence:** N/A by owner instruction (deployment parked). When the
VPS eventually deploys, it replays 0031→0035 in order on a fresh or restored DB —
no special cutover choreography needed there.

## Part 5 — Post-Cutover Architecture

```
ASSIGNMENT/LIFECYCLE TRUTH            DIMENSIONAL TRUTH            (unchanged)
WorkerStageTask  ──── task ────▶ WorkerStageContribution      expense.SWA + ledger
 5 statuses, cancel-terminal,      color/size/qty lines,       allocation-era money,
 F3 auto-resolve at complete       draft→completed, frozen     ADR-0007 cutover at V2-2
        ▲                          expected_* (no ledger)
        │ sole writer
 worker_task_service (chokepoint — discipline survives via new grep gate)
        ▲                    ▲                      ▲
 stage start/assign     worker report UI      resolve_on_complete
 (4 stage services)     (draft/submit)        (advance funnel)

READERS: dashboards · panels · isolation gates · badges · readiness — all task-based.
AddaStageRecord: adda/workflow_stage/timestamps/cost snapshots/drafts — NO worker M2M.
```
Ownership: production owns assignment+contribution truth end-to-end; the M2M,
its flag, its parity tooling, and gate [4/5]'s reason to exist are all gone.
One writer, one read path, no shadow copies.

## Part 6 — Readiness Verdict

**Technically: READY.** Evidence, not optimism: exactly one runtime reader
remains (a template count — trivially repointed); writers are two lines in one
service; parity held through every validation scenario INCLUDING the F3/F8
lifecycle change and a data migration; the reverse-rebuild design makes even
the drop recoverable while parity holds; rehearsal and rollback are concrete.

**Formally: ONE BLOCKER — and it is the owner's own rule.** R0 C2 locked the
V2-1d preconditions, including *"soak = pt.2b worker UI exercised on REAL data
through ≥1 full Adda cycle"*, and the soak tracker gates P3 on a signed
TRUE-soak review (real workers, post-deployment). Deployment is now parked, so
that precondition **cannot be satisfied before V2-1d** as written. I will not
quietly pretend it's met. The honest options:

- **(A) Owner amends C2** to accept the developer-validation evidence in lieu:
  full Adda cycle executed, multi-worker reporting, manager correction, parity
  OK ×5, lifecycle change absorbed without divergence — PLUS the new
  reverse-rebuild design, which removes most of what the soak was protecting
  against (an irreversible drop on unproven machinery). Defensible: the thing
  C2 guarded (task data correctness under use) has strong evidence; what's
  missing is only *real-human* usage variety.
- **(B) Hold V2-1d** until deployment + true soak, per the original wording.

Residual risk under (A), stated plainly: real workers may use the report flow
in ways dev validation didn't (the silent-failure pattern suggests UX surprises
are likely) — but post-cutover, any such issue lands on the TASK model, which
will then be the only model; there is no M2M to fall back to. The
reverse-rebuild migration mitigates schema-level regret; it cannot manufacture
usage evidence.

**Recommendation:** (A) — amend C2 explicitly, execute V2-1d per Part 4. The
parity evidence is the strongest signal the soak could have produced, and the
softened reversibility changes the risk calculus the original C2 was written
under. But this is precisely the class of decision the owner reserved: say
"C2 amended, execute" or "hold for true soak."
