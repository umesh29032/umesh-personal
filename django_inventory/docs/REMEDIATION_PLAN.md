# Architecture Remediation Plan — Kapil Enterprises ERP

> Companion to [TARGET_ARCHITECTURE.md](TARGET_ARCHITECTURE.md).
> Status: APPROVED 2026-06-09, **Rev 2 (pre-mortem fixes applied)**. Baseline: **305 tests green**
> (~103s, settings=config.settings.local). Branch: new_flask_app.
> Rev 2 fixes: R1 production↔expense earnings seam, R2 model-discovery mechanism, C2 factory
> seam = chokepoint-only (no columns), + migration-safety + perf-baseline + strangler-cutover phases.

## Governing principle
> **Architect for multi-factory / async / scale. Do NOT implement them.** Seams, not features.
> Target = **8.5–9/10 at low complexity**, NOT a forced 10/10.

## Revised dimension targets

| Dimension | Now | Target | Main driver |
|---|---|---|---|
| Architecture | 7.5 | **9** | cycles broken, facades, engine/logic/data separated |
| Extensibility | 5.5 | **9.5** | stage registry — new stage = 1 folder + 0 edits |
| Tech Debt | 6.5 | **9** | god-files split, copy-paste lifecycle removed |
| Maintainability | 6.5 | **9** | CI gates, one source-of-truth doc, observability |
| Scalability | 6.5 | **~8.5** | in-process wins + async-ready seams (no Redis/Celery yet) |
| RBAC | 7 | **~9** | unified skill-gating + factory seam (no multi-factory UX) |
| Payroll (corr.) | 8 | **10** | allocation↔completion contract, reopen voids credits |
| Workflow | 7 | **9.5** | completion locking + registry |
| Coupling | 7 | **9.5** | cycles forbidden by contract |
| Data Model | 8 | **9.5** | clean polymorphic root, reconciliation checks |

## Execution rules (non-negotiable)
1. Service layer owns all multi-row writes; views stay thin (CLAUDE rule #4).
2. **Characterization tests before every refactor** (M0.3) — refactors must be provably behavior-preserving.
3. One concern per PR; `Edit` not `Write`; full suite + import-linter green before merge.
4. No abstraction used <3 times.
5. Re-score at each milestone boundary.

---

## M0 — Safety Net & Baseline  *(zero behavior change)*
- **P0.1 Lock baseline.** ✅ 305 tests green recorded. TODO: commit current dirty tree to a baseline commit + tag `pre-refactor-baseline` (working tree is heavily uncommitted — needs a real rollback point). Add coverage report.
- **P0.2 CI gate.** ruff + mypy(gradual) + pytest + import-linter + coverage floor. Pre-commit hooks.
- **P0.3 Characterization + concurrency harness.** Golden tests for every stage lifecycle (start→complete→reopen), cost-freeze, allocation. Concurrency test helper. NOTE: when M2 moves views/services into `stages/<stage>/`, these tests' imports move with them — write them against the **service facade**, not module paths, to survive the move.
- **P0.4 Observability baseline.** Structured logging + rotation + route service loggers to file + error aggregation (Sentry/GlitchTip) + request-id.
- **P0.5 Migration-safety protocol (NEW).** Written rule, enforced for every schema phase: **NO drop-recreate on data that will ever be real; reversible `RunPython` only; rehearse each migration against a clone of the dev DB before applying.** (Memory shows a past "drop-recreate, data-loss OK because local" habit — banned going forward.) Covers R2 model move, C2 future factory wave, P2.9 draft move, M4.2 barcode relocation.
- **P0.6 Performance baseline (NEW).** Capture per-hot-page **query counts + timings** now (dashboards, costing, adda list, cutting workspace, allocation panel) using `assertNumQueries`/silk. This is the regression oracle M5 needs — "no regression" is unprovable without it.

## M1 — Correctness Hardening  *(surgical, high-trust)*
- **P1.1 Lock stage completion/advance (WF-4).** select_for_update Adda + re-check under lock. Concurrency test.
- **P1.2 Reopen voids worker credits (PAY-3).**
- **P1.3 Allocation↔completion contract pt.1 (PAY-2).** `pays_workers` semantics; block completing a paying stage with no allocations.
- **P1.4 Reconciliation report (PAY-4).** Σ earnings vs processing_cost, per Adda/stage.

## M2 — The Stage Engine  *(KEYSTONE — biggest multi-dimension lift)*
- **P2.1 Define seam (includes the R1 earnings design — do NOT defer to P2.7).** `stages/base/handler.py` (StageHandler ABC + StageService template) + `registry.py` (register/get/import-time **model** autodiscovery, per R2; handlers self-register). Decide the earnings edge HERE: `handler.complete()` returns a `CompletionResult` (worker allocations as primitives); the **base StageService** owns the single `expense` earnings-facade call. Handlers never import expense. Service signatures take `user_id`+primitives (async-ready). No behavior change yet.
- **P2.2–P2.5 Migrate each stage onto the seam** (one PR each, behind golden tests): layering → cutting_pattern → cutting → barcode_generation. Each stage's typed models get `Meta.app_label='production'` + move to `stages/<stage>/models.py` under the import-time autodiscovery (R2). Cutting also splits into bundle/breakup/completion services.
- **P2.6 Replace ALL dispatch sites with registry** (StagePanelView, cost_service._quantity_for, adda_views snapshot, remove adda_service first-stage special-case WF-5, remove complete_cutting sentinel SVC-6). Grep clean: no `stage_type ==`.
- **P2.6b Strangler cutover (NEW).** Do P2.6 behind a `STAGE_REGISTRY_ENABLED` flag: old `if/elif` and the registry **coexist**, run both in tests for parity, flip the flag, verify, THEN delete the old path in a follow-up PR. No big-bang swap of 6 sites in one commit.
- **P2.7 Move the expense call into the base StageService** (completes R1/PAY-2): every paying stage credits workers through the base service's single facade call — relocating the import that lives in `stage_views.py:59-61` today into `stages/base/service.py`. Net module edge: one-way `production → expense`.
- **P2.8 Presentation cleanup.** Dissolve stage_views.py into stages/<stage>/views.py + generic StageView (VF-2/3). Replace parallel-array POST parsing with formsets (VF-4). Fix allocation N+1 (VF-5).
- **P2.9 Clean polymorphic root (DM-6) — DATA MIGRATION, not a line.** Move layering-specific draft_* off AddaStageRecord into per-handler draft storage. Migrate existing in-flight draft rows (reversible RunPython per P0.5).
- **P2.9b Template + test sweep (NEW).** Migrate ~10 stage templates `stage_type → stage.code`; relocate moved view/service imports in tests. ⚠️ watch the recurring `{# #}` multi-line-comment regression — use `{% comment %}` for multi-line.
- **P2.10 Open-closed proof.** Dummy stage in tests proves new stage = **+1 URL line, 0 other edits** (per the corrected claim in TARGET_ARCHITECTURE.md).

## M3 — RBAC
- **P3.1 Unify skill-gating data-driven (RBAC-3/4).** Delete hardcoded SKILL_* constants in services; gate mutations too.
- **P3.2 Split permission_service into package (RBAC-6).** principal / perms / menu / role_editor; cache user_has_perm.
- **P3.3 Factory SEAM ONLY — CHOKEPOINT, NO COLUMNS (Fork A + C2 correction):**
  - P3.3a `current_factory()` helper (returns the single default factory today).
  - P3.3b `TenantScopedManager`/queryset chokepoint that all tenant-data queries route through — a **no-op** while there is one factory.
  - **NO `factory` FK columns added now.** Adding them = *implementing* multi-factory (forbidden by the principle) and half-scoping leaks across sites. When site #2 is funded: ONE migration wave adds the FK to **ALL** tenant-data tables + flips the chokepoint to a real filter.
  - **OUT (deferred until 2nd site funded): the column migration, factory switcher UI, factory admin, factory dashboards, per-factory RBAC UX.**
- **P3.4 Kill SIDEBAR dual-source.** Seed SidebarItemRule from code registry; sync test.

## M4 — Coupling
- **P4.1 Remove accounts→production back-edge (COUP-5) — specify the new home.** Moving `sync_layering_workers_for_skill` "to a view" is NOT enough: the user-edit views live in `accounts/views.py`, so an accounts view calling production keeps the `accounts→production` edge at module level. Relocate the orchestration to an **`inventory` orchestrator** (inventory already depends on production+accounts) OR a `production` service the inventory view calls. accounts (services AND views) must end with zero production imports — verified by import-linter.
- **P4.2 Break production↔tracking cycle (COUP-2) — this is a MIGRATION-BEARING ownership move, not a facade.** A logging facade fixes only `production→tracking`. The `tracking→production` half (barcode gen/export reading production models) requires **relocating barcode-assembly into `production`**, leaving `tracking` a dumb range/scan primitive (cross-app model + data migration, per P0.5). Size it as a real phase.
- **P4.3 Tame production god-app (COUP-4).** Finalize stages/ + cutting/ packages.
- **P4.4 Strict import contract.** Tighten .importlinter: one-way `production→expense` + `production→tracking` allowed; all reverse edges + deep imports forbidden. Removes the current `ignore_imports` TODO for production↔tracking.

## M5 — Scalability  *(cheap in-process wins + async-ready SEAMS only)*
- **P5.1 Kill N+1 + paginate everything.** Query-count tests cap hot pages.
- **P5.2 Ledger closing-balance snapshots (PAY-6 perf).** O(1) balance at any ledger size.
- **P5.3 Denorm reconciliation (DM-4).** Periodic command verifying counters vs source.
- **DEFERRED (seam ready, not built): Celery/Redis async tier, Redis cache.** Behind a flag; switch on at real load.

## M6 — Maintainability & Docs
- **P6.1 One source of truth.** Rewrite SYSTEM_DESIGN.md to reality (7 apps, Django 5.0.1, post-relocation RBAC); collapse the two ARCHITECTURE.md; fix false "raw_materials never imports production" claim; update PAYROLL doc (Settlement not WorkerPayment). Doc-accuracy spot-check test.
- **P6.2 Archive discipline.** Dated audit/handoff docs → docs/archive/; introduce docs/adr/.
- **P6.3 Remove dead weight (now safe).** Legacy fallbacks + back-compat shims (stage_type property) once templates use stage.code. Document inventory migration graveyard (do not delete).
- **P6.4 Coverage + types.** ~90% service coverage; raise mypy strictness.

## M7 — Verify
- **P7.1 Re-run architecture review workflow + load test + CSO security pass.**
- **P7.2 Scorecard sign-off vs targets above.**

---

## Scope focus
The real business problems stay primary: **Adda · Stages · Payroll · Production Flow.**
Critical path: **M0 → M1 → M2.** After M2 the system is already strong (most dimensions
8.5–9.5). M3/M4 can partly parallelize. M5 infra deferred until load demands it.
