# ERP_MASTER_CONTEXT Review — Run State (2026-06-10)

**Status: ✅ COMPLETE 2026-06-10.** Final deliverable: `docs/ERP_MASTER_CONTEXT_REVIEW.md` (12 sections, first phase = R0 doc-truth reconciliation + ADR 0007 cutover lock, awaiting owner approval). RBAC-isolation area finished inline (object-level assignment gate confirmed built: mixins.py:35-45, dashboard worker_tasks scoping, can_view_worker). Run-3 verifiers confirmed all production (5/5) + financial (2/2) conflicts. Deployment/missing-alter verifier passes skipped (readers' file:line cites stand).
Historical run log below.
**Old status: RUN 3 IN FLIGHT.** Run 1 completed `v2-docs` (verified). Run 2 completed 5 more area maps: `production`, `financial`, `deployment`, `perf-tests`, `missing-alter` (findings in §7 below). Run 3 re-runs only: `rbac-isolation` map, 12 pending verifiers, critic. Resume = `Workflow({scriptPath: <script in §2>, resumeFromRunId: "wf_4d2a63ed-094"})` — all completed agents cached.
This file checkpoints the architecture review of `ERP_MASTER_CONTEXT.md` so it can resume without redoing finished work. Run-2 raw output: `/tmp/claude-1000/-home-tech-umesh-personal-django-inventory/55253ea4-3c31-4c8e-8b37-6225d9c74030/tasks/wdtbib3c0.output`.

---

## 1) Goal

Review-first architecture audit of the user-supplied `ERP_MASTER_CONTEXT.md` against the actual repo + locked docs. **No code.** Final deliverable = 12 sections:

1. Architecture Verdict · 2. Risk Matrix · 3. Decision Matrix (KEEP/MODIFY/DEFER/REJECT per master-context decision) · 4. Foundation Gaps · 5. Deployment Readiness Review · 6. Phased Roadmap · 7. Recommended First Phase (then STOP) · 8. Risks To Avoid · 9. Decisions to Lock Before Coding · 10. Decisions to Keep Deferred · 11. Long-Term Rewrite Risks · 12. Microservice Extraction Readiness.

Per the user's Phase Execution Policy: after the roadmap, recommend first phase, explain why/risks/dependencies/success criteria, **STOP — implementation only after explicit approval**.

## 2) Method + run identity

Multi-agent workflow (ultracode): 7 parallel readers → adversarial verifiers per flagged conflict → completeness critic.

- Workflow run ID: `wf_4d2a63ed-094` (task `w32ty9qz0`)
- Script file: `/home/tech/.claude/projects/-home-tech-umesh-personal-django-inventory/55253ea4-3c31-4c8e-8b37-6225d9c74030/workflows/scripts/erp-master-context-review-wf_4d2a63ed-094.js`
- Full raw output: `/home/tech/.claude/projects/-home-tech-umesh-personal-django-inventory/55253ea4-3c31-4c8e-8b37-6225d9c74030/tool-results/bib0hvmiq.txt`
- **Resume command (after limit reset):** `Workflow({scriptPath: "<script file above>", resumeFromRunId: "wf_4d2a63ed-094"})` — the completed `v2-docs` reader + its 4 verifiers return cached; only the 6 failed readers re-run.

## 3) What completed: `v2-docs` area (reader + 4 adversarial verifications, all confirmed)

### 3.1 Master-context claims that MATCH the locked repo docs
- **Option B locked**: no ledger until settlement; `expected_*` frozen = visibility only (ARCHITECTURE_V2 §5, §2; ADR 0005).
- **Model A locked**: AddaSettlement = Adda-centric earning+recovery event; PayrollSettlement narrowed to cash-only payment; recovery at settlement, payment never re-runs recovery (§11.0, §11.2).
- **Migration discipline**: backfill known-facts-only, unassign=cancel-never-delete, `WORKER_TASK_DUAL_WRITE` flag (built, `config/config/settings/base.py:177`), reversible until V2-1d M2M drop, clone rehearsal done (V2_1_REVIEW Q1/Q2/D-A3/§6/§10).
- **Missing/Alter**: future first-class domains (MissingPieceCase/AlterCase), settlement consumes summaries, never owns workflow (§11.0 d5, §11.11). Not in code (grep confirmed).
- **Stage taxonomy**: explicitly provisional; Cutting = reference implementation; STAGE_DOMAIN_REVIEW_AGENDA is the pending review; 2026-06-10 owner decision: proceed against current flow with inline `FUTURE-STAGE-REDESIGN` markers.
- **`StageHandler.contribution_schema()`**: locked direction AND already built (`config/production/stages/base/handler.py:106`); attributes-JSONB column deferred until a non-cutting stage needs it.

### 3.2 Master-context claims needing CORRECTION (adversarially verified)
1. **Implementation status is STALE (biggest finding).** Master-context says "V2-1a in progress". Reality: V2-1a, V2-1b, V2-1c-i/ii/iii-pt.2a/iv are **BUILT and COMMITTED** on `new_flask_app` (commits e4953ef9, adddec97, bf9bfff3, 77d5d773, 5e4b4516, 2580a7d6, cfdb2d26; migrations 0031/0032/0033 applied to dev DB; 389→417 tests green; clean tree). Still design-only: V2-2 AddaSettlement build, V2-3 SWA repurpose, V2-1d M2M drop, worker-report UI pt.2b/2c, Missing/Alter modules. Also stale: ARCHITECTURE_V2.md line 3 header ("design only"), V2_1_REVIEW §10 "NOT committed", CLAUDE.md "In progress (V2-1a)".
2. **Task lifecycle has FIVE statuses**, not four: assigned/in_progress/completed/**verified**/cancelled — `verified` optional, never a stage-advance gate (`config/production/models/worker_task.py:32-38`).
3. **StageWorkAssignment is NOT "replaced/absorbed".** Locked §11.4 **RETAINS** SWA, repurposed as the settlement-written earning line: at finalize, one SWA row per settled worker-stage line backs each `WorkerLedgerEntry.assignment` (PROTECT) credit — zero ledger schema change. No removal migration planned (`config/expense/models.py:35,153-156`).
4. **WorkerStageContribution is no longer deferred** — built (migration 0033). The M2M read path is flipped to WorkerStageTask (V2-1b) but `AddaStageRecord.workers` still exists and is dual-written; drop = V2-1d (point of no return), not done (`config/production/models/adda.py:101-103`).
5. **Internal doc contradiction found**: ARCHITECTURE_V2 §2 (line ~84) and §10 summary (line 222) say "add WorkerAdvance.adda FK"; locked §11.3 (lines 324-326) explicitly REJECTS it ("Do not add it"). §11 wins; §2/§10 never reconciled.
6. **ADR 0005 documents the live-runtime gap**: today's money path still credits earnings at allocation (pre-§11 build). "No ledger until settlement" is locked design, NOT current runtime behavior.

### 3.3 Locked decisions the master-context OMITS (~15, all doc-verified)
factory_absorbs launch variance policy (tracked, never auto-deducts); frozen append-only AddaSettlementItem (never recomputed post-finalize); manual source-agnostic variance entry at finalize (future modules feed same seam); WorkerAdvance.adda REJECTED; NO per-Adda paid/unpaid flag ("money is fungible at worker level"); §11.9 invariants (double-credit guard: contribution → ≤1 non-voided settlement SWA line; quantity-freeze at finalize; per-worker variance grain; write-once audit snapshots); settlement lifecycle draft→finalized→reversed/superseded (corrections never edit); finalize lock order (advisory lock 5374 → settlement → stage records → WorkerProfile → WorkerAdvance); advance gate = all active tasks completed (verification never gates); derived-never-stored progress/balances; LOCK-NOW fields (color/size on contribution lines day one; reported_quantity vs verified_quantity; cancelled terminal); partial UniqueConstraint = one ACTIVE task per (stage_record, worker); chokepoint uses select_for_update; earning computation swappable per stage (F2); Stage.code immutable identity vs Stage.name display; WorkflowStage flat list (sub-stages via additive parent FK later); ADR 0006 architect-for-scale-do-NOT-implement (target 8.5-9/10); factory seam = `current_factory()` chokepoint, NO factory columns now; credits_workers permanently on WorkflowStage; production→expense one-way facade in one file (stages/base); ADRs 0001-0004; P4.2 barcode cycle-break PARKED (likely code relocation, not data migration; barcode models stay in tracking).

## 4) What FAILED (session limit) — 6 readers to re-run

| Area | What it was checking |
|---|---|
| `production` | WorkerStageTask/Contribution code state; hardcoded stage-name dispatch inventory; readiness/advance derivation; draft/submit; AddaStageRecord fields |
| `financial` | WHEN WorkerLedgerEntry written today (allocation vs settlement) file:line; single-writer; advances pool; PayrollSettlement = settle+pay conflation; reverse_settlement gap |
| `rbac-isolation` | Object-level vs skill-level worker access (querysets); StageViewAccessMixin; cross-worker data leaks; financial info on worker screens |
| `deployment` | env config, cache backend (locmem vs redis — rate-limit/principal-cache multi-process correctness), storage/local-fs coupling, sync long jobs, logging, session backend |
| `perf-tests` | run test suite; assertNumQueries coverage; N+1 in dashboards/lists at 100k-Adda scale; mypy island |
| `missing-alter` | where missing/alter counters live today; whether settlement math reads them; backfill seams for future MissingPieceCase |

## 5) Critic's gap list (what's still needed for the 12 sections)
- KEEP/MODIFY/DEFER/REJECT verdicts for master-context decisions outside worker-tracking/settlement (RBAC model, service-layer/no-signals, stage registry, costing freeze, DRF/Redis phasing).
- Independent re-verification of scorecard metrics (417 tests, import-linter, ~68% coverage, mypy 211-island) — currently self-reported docs.
- **Whether any LIVE production deployment exists** (swings dual-write-window severity, V2-1d point-of-no-return, all of Section 5).
- production.py settings contents, requirements pinning/WSGI server, Dockerfile/CI absence (gap vs seam), backup/restore, secret provisioning.
- **Cutover plan for allocation-era WorkerLedgerEntry rows when V2-2 lands** (backfill/void/coexist; does §11.9 double-credit invariant cover historical rows?).
- Dual-write reconciliation check (M2M vs tasks divergence test; kill-switch mid-flight semantics).
- Enumeration of OPEN/unlocked questions (V2-2 schema specifics, machine sub-stages, Missing/Alter field design) for Sections 9-10.
- Roadmap dependency graph: V2-1d vs V2-2 ordering; where parked Phase 7 (cycle break) + Phase 8 (stage_views split) slot vs stage-domain review.
- Cross-app coupling map for Section 12.

## 6) Resume procedure

1. After 1:10am IST (limit reset), in this repo say: **"resume the ERP master-context review per docs/ERP_MASTER_CONTEXT_REVIEW_STATE.md"**.
2. Agent resumes workflow with `resumeFromRunId: wf_4d2a63ed-094` (v2-docs cached, 6 readers re-run) — or re-runs the 6 failed areas directly.
3. Then synthesize the 12-section deliverable, recommend first phase, STOP (no implementation without approval).

**Known sequencing anchor** (from agenda, for the roadmap): pt.2b worker-report UI → pt.2c dashboard badges → V2-1d M2M drop → V2-2 AddaSettlement → V2-3 SWA repurpose → Missing/Alter modules.

---

## 7) Run-2 findings (5 areas mapped — pre-verification, but readers cite file:line)

### 7.1 `production` — stage engine further along than master-context assumes
- **WorkerStageTask AND WorkerStageContribution both built+migrated** (0031/0032/0033), dual-write chokepoint behind `WORKER_TASK_DUAL_WRITE`, reversible backfill, V2-1b reads repointed. Report/draft/complete-freeze services exist but have **no view/UI caller yet** (pt.2b pending).
- **Full stage engine exists ("M2")**: `StageHandler` ABC + `contribution_schema()` hook, self-registering registry + `autodiscover()` in `production.apps.ready()`, per-stage packages under `config/production/stages/` (layering, cutting_pattern, cutting, barcode_generation), data-driven `WorkflowStage.credits_workers`, executable open-closed proof test.
- **BUT open-closed is partial in practice**: ~25-30 hardcoded stage-code sites across views/services/cross-app callers + 4 template if/elif include chains; each stage has bespoke view module + workspace URL; `adda_service` has layering-only auto-start.
- **Correction to master-context §4.3**: `CuttingPatternVerification` IS a hard gate for completing the cutting_pattern stage (`complete_pattern_stage` requires all pattern assignments verified). Only the per-worker task `verified` status is optional. "Stage advance should not depend on verification today" conflicts with shipped behavior.
- Stage advance lives in `adda_service.advance_to_next_stage` (flow_service.py = product-flow CRUD only). AddaStageRecord lifecycle is **timestamp-derived, no status field**; `cost_billed_at` lives on WorkflowStage (not the stage record); frozen `processing_cost` + cost snapshots on the record; PROTECT on adda.
- StageWorkAssignment = live allocation-driven payroll input, written solely by `expense/services/allocation_service`.

### 7.2 `financial` — live money path is PRE-V2 (acknowledged transitional)
- **Ledger credits written at allocation time today** (`allocation_service.py:110`, cutting workspace) — opposite of locked Option B; PAYROLL_ARCHITECTURE.md line 5 banner openly acknowledges V2 moves money-write to settlement.
- `ledger_service` verifiably the **sole writer** (single `objects.create` at ledger_service.py:36; admin read-only).
- **PayrollSettlement conflates settle+pay+recovery** in one atomic event (`amount_paid` on header) — V2 WRAP/Model A split not built; **AddaSettlement absent from code**.
- Advances: strictly separate loan pool (no ledger debit on issue; owner-controlled partial recovery at settlement). Matches master-context §3.6.
- **Two parallel earning surfaces now coexist**: SWA ledger credits = live money; WSC `expected_*` (frozen by `complete_worker_task`, books NO ledger) = visibility. Cutover/coexistence plan for allocation-era ledger rows when V2-2 lands = OPEN QUESTION (must lock before V2-2).
- No variance/deduction engine ('deduction' ledger category has zero writers; factory_absorbs is design-only). **reverse_settlement still unbuilt**: `reverse_entry` exists but PayrollSettlementItem recovery rows cannot be compensated — advance outstanding stays reduced (known deferred gap, now load-bearing).

### 7.3 `deployment` — seams decent, concrete blockers found
- Settings split base/local/production + python-decouple; SECRET_KEY/DB/ALLOWED_HOSTS/email/OAuth from .env; no hardcoded secrets. Sessions DB-backed. RBAC principal/perm caches are request-scoped on user object = deployment-safe. No sqlite.
- **🔴 NO `CACHES` setting → LocMemCache → auth rate limiter (`accounts/throttle.py`) broken under multi-worker** (per-process counters; its own docstring admits Redis needed; Redis neither configured nor in requirements).
- **🔴 argon2-cffi missing from requirements.txt** (only ad-hoc in venv) — clean deploy cannot hash/verify passwords (Argon2 first in PASSWORD_HASHERS).
- **🔴 SECURE_SSL_REDIRECT=True without SECURE_PROXY_SSL_HEADER** → redirect loop behind any proxy/PaaS.
- **🔴 Production media unsolved**: /media/ served only when DEBUG=True; whitenoise = static only → uploaded images (pattern photos, storefront, advance attachments) 404 in prod.
- Job-queue candidates (sync in request cycle today): barcode print-sheet renders one QR PNG per piece in a loop; CSV/XLSX/PDF exports expand every piece per request.
- Logging plain-text, request-id-correlated, rotating local files + security.log (RotatingFileHandler = multi-process unsafe; logs/ created at import time). Advance issuance has no log line. No gunicorn in requirements.

### 7.4 `perf-tests` — safety net real
- **417 tests green in ~134s.** ⚠️ Footgun: discovery only works from `config/` — running `config/manage.py test` from repo root silently finds 0 tests and exits OK (check.sh does it correctly).
- Perf baselines locked (`config/production/tests/test_perf_baseline.py`): dashboard ctx worker=14 / mgmt=20 queries, adda-list render=11, costing=9, `attach_layering_snapshots` flat at 5 regardless of Adda count; permission_service cached=1.
- V2-1 heavily characterized (dual-write chokepoint, 0032 backfill, contribution freeze, isolation) + check.sh grep gate = sole-M2M-writer. Settlement math pinned in expense/tests.
- Scale risks: unified dashboard lists ALL in-progress Addas unpaginated (mgmt); costing view builds three full-table per-Adda aggregate dicts in memory (display capped 200, memory not) — degrade at 100k Addas though query counts stay flat.
- mypy: strict island over `*.services.*`/`*.stages.*` but **report-only with ~242 violations**; only accounts user_service clean. "Typed island" overstates.

### 7.5 `missing-alter` — thinner than "counters"
- Missing pieces = ONLY `BatchBarcode.Status.MISSING` enum + on-the-fly dashboard aggregates. No missing field on any cutting/stage/expense/settlement model. Alter/rework = zero code.
- Nothing in costing or settlement consumes missing/alter numbers → future MissingPieceCase/AlterCase design is unconstrained by current code (good).
- **🔴 Dead flow**: `mark_status` writer has NO view/URL caller — missing status cannot be set from the UI at all; SYSTEM_DESIGN.md:260 scan-flow diagram (scan → mark_status) is wrong; UI_PATTERNS.md "reprint flow" can't be exercised.
- Backfill seams: dimensions good (adda/color/size/pattern/qty on CuttingPieceBreakup, frozen breakdown, BatchBarcode FKs, WSC lines); lifecycle facts weak (no detection-stage, no missing-date, no per-status-change audit).

## 8) Still pending (run 3)
- `rbac-isolation` map (object-level vs skill-level worker access — last unverified security claim).
- 12 adversarial verifiers across production/financial/deployment/perf/missing-alter conflicts.
- Critic pass → then synthesize 12-section deliverable → recommend first phase → STOP for owner approval (no code).
