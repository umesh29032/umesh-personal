---
id: engineering-excellence-sweep-2026-07-06
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Engineering Excellence Sweep + Engineering Readiness Report (2026-07-06)

> Owner-ordered pre-freeze sweep: engineering quality ONLY (no business logic,
> no workflows, no UI, no AI). Lens: the senior engineer maintaining this
> codebase in five years. Method: mechanical census (import-linter, pyflakes,
> vulture, makemigrations --check) + three parallel read-only deep-dive audits
> (duplication/dead-code · ORM queries/indexes · template repetition/doc drift),
> every finding verified against code before action. Bar for implementing:
> provably behavior-neutral; everything architecture-touching is documented
> instead. Gate after all changes: full suite green (885) + import contracts
> unchanged.

## 1. Census result (the platform is already unusually clean)

- **1** TODO in the entire non-test codebase (a benign hinglish docstring note).
- **0** stray `print()` in app code; **0** vulture dead-code hits at ≥90%
  confidence (all 6 candidates were Django framework-signature params).
- Migrations exactly in sync (`makemigrations --check` clean).
- Largest service = 706 lines (`permission_service`) — the known, registered
  RBAC god-file (arch-remediation backlog), untouched by design.
- Import contracts: contract 1 (core+accounts purity) **KEPT**; contract 2
  (acyclic layering) **BROKEN as documented** — the long-registered
  production→expense reads (a360/costing/credit) + test-only leaks; report-only
  by design, registered debt, NOT a pre-freeze fix.

## 2. Implemented (all behavior-neutral, verified)

**Hygiene (pyflakes now ZERO across all 9 apps):** unused imports removed in 15
files (autoflake, `__init__` re-exports protected); `production.views.__all__`
completed with the 6 routed master views; two dead private `_build_*` re-export
aliases dropped; dead `FinancialRoleMixin` deleted (grep-verified unreferenced).

**Duplication → single homes:**
- `expense/services/_shared.py` now owns **`q_paisa()`** (THE paisa rounding
  rule — was copy-pasted in `settlement_service`, `adda_settlement_service`,
  inline in `ledger_service`) and **`next_reference(model, prefix)`** (was two
  near-identical SETL-/ADST- generators). Call sites delegate; money output
  byte-identical, suite-verified.
- `production/views/mixins.get_adda()` replaces 3 identical `_get_adda` copies.
- `expense.views._WorkerFromPk` mixin replaces 3 identical `_worker()` methods.
- `inventory/views/mixins.ProductionRoleMixin` replaces 4 identical private
  copies in the tracking view modules.
- 2 magic `'layering'` literals → `STAGE_LAYERING` constant.

**ORM (agent-audited hot paths, 6 fixes):** `current_stage__stage` added to the
dashboard Recent-Addas and Adda-list querysets (was ≤50 extra queries/page via
`get_stage_type_display`); AddaDetailView now fetches its Adda with
`select_related` and **reuses** the registry snapshot map instead of computing
layering/pattern snapshots twice per render; Report-Review and settlement-lines
querysets now `select_related('settlement_line__adda_settlement')` (was 1 query
per settled row).

**Indexes (3, additive; migrations production 0049 + tracking 0016 applied):**
`AddaHistory(-created_at)` (global recent-events feed on the management landing
page), `WorkerStageTask(status, created_at)` (pending-reports digest/list),
`AddaStageRecord(completed_at, started_at)` (stalled-stages digest/list/A360).
All three back queries that run on every management dashboard load, on tables
that only grow.

**Documentation drift (4 real contradictions fixed):** RBAC.md pointed helpers
at a non-existent `inventory.services.permission_service` (→ `accounts.…`) and
still labelled the role `karigar`; `stage_earnings_flow.md` listed enum value
`fixed` (actual: `fixed_cost`); GLOSSARY's **Allocation** row still described
era-A allocation-time earning freeze (now: settlement-finalize on
verified-else-good, era-B default) and omitted `WorkerStageAllocation` — both
corrected; `worker_task_service.md` bound formula missing `+damaged`.

## 3. Deferred (documented — architecture-touching or wrong moment)

| # | Item | Why deferred / where it lives |
|---|---|---|
| D-1 | production→expense acyclicity (contract 2) | registered arch-remediation debt; report-only contract by design |
| D-2 | ONE management/super-admin/production mixin family across apps (3 naming variants remain: `ManagementRoleMixin`/`ManagerOrAdminMixin`/`_ManagementOnly`) | cross-app RBAC relocation = the same registered backlog item; within-app dedup done |
| D-3 | `settlement_queue()` per-Adda query batching + PayrollOverview pagination + costing full-table aggregate watch | money-service refactor; behavior-preserving but non-trivial — post-freeze with its own tests |
| D-4 | Generic stage-handler `snapshot()` re-queries stage records/aggregates per stage on Adda detail | touches the handler contract; grows only with flow length (~2 queries × generic stages) |
| D-5 | Hero-gradient CSS copied in 13+ templates + panel-vocab CSS re-scoped per panel (`_form_styles.html` owner exists) | needs a screenshot-diff visual-regression pass; design system is FROZEN — post-freeze FE batch |
| D-6 | `workflow_stage(adda, code)` helper unification across stage services (+ the `_pattern_workflow_stage` naming split) | chokepoint-service churn; fold into next production-service touch |
| D-7 | `_ensure_management` local copy in adda_settlement_service (distinct error text) | message is possibly asserted; consolidate with a message param post-freeze |
| D-8 | `explain_visibility()` exported but never wired into the Access hub | wire or delete at next RBAC pass |
| D-9 | `role_forms` rebuilds the permission queryset the service already encapsulates | needs list→queryset adaptation |
| D-10 | SWA model comments still describe era-A framing | comment-only; fix at next expense-model touch |
| D-11 | `ROLE_EDITABLE_MODELS_EXCLUDED` empty-frozenset lever + its consumer loop | intentional designed lever — left wired |

## 4. AI Pattern Intelligence idea (added to blueprint §12)

**I-4:** `q_paisa` lesson — money survived 3 rounding-rule copies only because
they happened to stay identical. Geometry math must never take that risk:
blueprint §3's mm-canonical rule gets ONE quantization/precision helper in
`patterns_ai` from the first line of code (piece area, utilization %, placement
coordinates all round through it).

## 5. ENGINEERING READINESS REPORT

**Verdict: ENGINEERING-READY TO FREEZE.** After this sweep I find nothing
meaningful left that is safe or sensible to change before freeze:

1. **Hygiene floor reached** — zero pyflakes across 9 apps, zero ≥90% dead
   code, zero stray TODOs-of-substance, migrations in sync, one benign note.
2. **Single-home discipline extended to the last stragglers** — the paisa
   rounding rule, settlement reference generation, Adda lookup, worker-from-pk,
   and the production-role gate each now have exactly one definition (within
   their app boundaries).
3. **Hot paths are indexed and N+1-free** at current fleet size; the three new
   indexes cover the only growth-table scans that run on every management load.
4. **Docs tell the truth** — the four contradictions a hostile reader could
   have used against the docs are gone; chokepoint docs verified accurate.
5. **The remaining debt is REGISTERED, bounded, and post-freeze by design**
   (D-1…D-11) — none of it gets more expensive by freezing now; D-1/D-2 were
   already in the arch-remediation backlog before this sweep.

Gate: full 885-test suite green (exclusive serial run) after all changes;
import contracts unchanged (1 kept / 1 known-broken-by-design); golden
settlement math executed inside the suite. Post-sweep the suite briefly showed
3 failures — all three were the tests, not the product: two conscious
query-count pins beaten by this sweep's own optimizations (re-pinned with
documented reasons: A360 68→65, adda-list 11→8) and one order-fragile
substring assertion that false-flagged on a row PK (rewritten structurally;
lesson recorded: never substring-assert over payloads containing PKs).

**Proceed to the owner's freeze sequence:** real rate card → re-validate the
three journeys → MANUFACTURING FREEZE → checkpoint commit → AI Pattern
Intelligence kickoff.
