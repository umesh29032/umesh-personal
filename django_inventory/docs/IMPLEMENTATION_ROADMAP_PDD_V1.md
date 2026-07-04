# IMPLEMENTATION ROADMAP — derived from 🔒 PDD v1.0

> **Source of truth:** [PRODUCT_DESIGN_DOCUMENT.md](PRODUCT_DESIGN_DOCUMENT.md)
> (frozen 2026-07-04). Every task below cites its PDD section (or, for pre-PDD
> locked-stream items in the gated backlog, its locked source doc). Scope
> changes go through a PDD revision or ADR first — never through this file.
> Execution model: **one phase at a time**, owner-gated between phases.
> Naming: R1–R11 here are ROADMAP phases — unrelated to the 2026-06
> stage-domain-review "R1" or the foundation "F1–F4"/"F3 auto-cancel" labels.
>
> **Universal exit gate (every phase):** `bash scripts/check.sh` green
> (700+ tests, run from `config/`) · golden ₹225 byte-identical on any
> money-touching phase · docs updated same session (CLAUDE rule 12) ·
> UI phases browser-verified at 360/768/1280 (rule 11) · PDD stays authoritative.

## Dependency graph

```
R1 (nav/visibility + F1 guard)          independent ──┐
R2 (layering earnings)                  independent ──┤
R3 (completion guard C3)                after R2* ────┤   * soft: same code path,
R4 (MONTHLY pay basis D4)               independent ──┼──   avoid merge friction
R5 (FactoryExpense)                     independent ──┤
R6 (verified-qty audit F6)              independent ──┤
R7 (Full & Final, D5)                   after R4* ────┤   * monthly workers' F&F
R8 (cutting-pattern earnings)           after R2 + owner spec
R9 (cutting earnings)                   after R8 + owner spec
R10 (machines)                          independent, anytime
R11 (MissingPiece)                      after R9 (defect flows richest)
─── soak/roadmap-gated (not schedulable now) ───
G1 materials · TM-1 tracking-mode · TM-2 barcode-tracking · S6 reported
retirement · ADR-0007 deletion · F5 ledger close · subcontracting seam ·
G6→G5→G2→P&L
```
**Parallel-safe if ever needed:** R1 ∥ R2 ∥ R4 ∥ R5 ∥ R10 (disjoint files).
R6 shares `worker_task_service.py` with R2's write path — keep those two serial.
Recommended serial order (solo dev, merge sanity): R1 → R2 → R3 → R4 → R5 →
R6 → R7 → R8 → R9 → R10 → R11.

## Phases

### R1 — Navigation, visibility & the F1 guard  *(UI-heavy, no money logic)*
**STATUS: IMPLEMENTED 2026-07-04 (awaiting owner acceptance) — plan:
[R1_EXECUTION_PLAN.md](R1_EXECUTION_PLAN.md); gate PASS 714 tests; browser-verified.**
PDD: §3, §23, §27-D6, §27-D7, §31.1-F1.
1. Adda detail: **Settlement** button (management-gated → settlement start/detail)
   + **Stage Rates** button (existing page; correction stays super-admin, §27-D3).
2. Adda detail: worker **"My Work" section** — self-scoped tasks, quantities,
   expected earning; becomes the worker's PRIMARY entry point (D7).
3. Worker dashboard: read-only **"new Adda started"** broadcast row (D6 — no push).
4. **F1 guard:** `Product.code` immutable once the product has any Adda
   (form + service validation; protects Adda-code uniqueness + barcode prefixes).
Exit: browser-verified 3 viewports; access checks (worker never sees mgmt buttons).

### R2 — Layering earnings  *(first per-stage money wiring)*
PDD: §14, §17, §18, §27-D1, §27-D2.
1. Config (data): 3-patti layering `cost_method=per_layer`, rate ₹10,
   `credits_workers=True`, ungrouped.
2. Worker layer-report: each assigned worker reports ONLY own layers (D1) via
   `worker_task_service` (C-TM single door) → WSC `good_quantity=layers`
   (dimensionless grain — color/size null).
3. Verify freeze fires: `expected_earning = layers × frozen AddaStageRoleRate`.
4. Reconciliation WARN: Σ worker-reported layers vs `lay_count` breakup mismatch
   (warn, never block — mirrors M-6 philosophy).
5. Settlement E2E test: layering line pays via existing engine; good-only (D2).
Exit: golden ₹225 byte-identical + new layering golden; mobile report flow verified.

### R3 — Stage-completion guard (C3)
PDD: §16, §27-C3.
1. Default: stage complete REFUSES while assigned workers pending (replaces
   the default auto-cancel path — foundation label "F3", NOT PDD §31.1-F3).
2. Super-Admin override: mandatory reason → recorded via `history_service`
   (audit trail); overridden tasks then auto-cancel as today (cancelled, named).
3. Keep explicit un-assign/cancel flows untouched (manager can still cancel a
   worker deliberately BEFORE completing).
Exit: tests for block, override+reason persisted, named-worker error message.

### R4 — MONTHLY pay basis (D4)
PDD: §17, §27-D4, §21-link.
1. `WorkerProfile.pay_basis` (piece_rate default | monthly) — migration.
2. Structural guard at the settlement chokepoint: monthly workers' contributions
   NEVER become settlement lines (test: monthly worker settles to zero lines,
   piece-rate colleague on the SAME stage settles normally).
3. Expected-earning display for monthly workers: analytics-only presentation
   (no ₹ expectation shown).
Exit: golden untouched; double-pay impossibility test.

### R5 — FactoryExpense module
PDD: §21.
1. `FactoryExpense` model (category, amount>0 CHECK, expense_date, entered_by;
   append-only posture: create/void, no edit).
2. Admin CRUD UI + monthly totals on admin dashboard.
Exit: constraint tests; mobile-usable entry form.

### R6 — verified_quantity audit trail (F6)
PDD: §31.1-F6, §29.
`set_verified_quantity` emits history event (who/old/new/when) via
`history_service`. Tiny, independent.

### R7 — Full & Final settlement (D5)
PDD: §20, §27-D5, §31.2 (deactivation never blocks money).
1. Service: resolve open tasks (complete-with-reported or audited cancel) →
   per-WORKER settlement across all unsettled lines (reuses engine, scope=worker)
   → advance clearance with explicit AUDITED WRITE-OFF entry for residual →
   cash payment event → deactivate.
2. Edge tests: zero-payable + outstanding advance; F&F then Adda-reopen attempt
   (settlement armor must refuse); monthly worker F&F (needs R4).
Exit: golden untouched; ledger write-off category audited.

### R8 — Cutting-pattern earnings  *(BLOCKED on owner's per-stage spec)*
PDD: §15 (workflow) + §17 (payment engine) + §30 (stage-earning recipe = the
wiring authority). Same recipe as R2; single-worker stage. Scope arrives as the
owner's per-stage spec — a PDD §15 revision if it changes workflow rules.

### R9 — Cutting earnings  *(BLOCKED on owner's per-stage spec)*
PDD: §16 (workflow) + §17 + §30 recipe. Multi-worker template; good/alter/
missing already native here. Owner spec gates start, as R8.

### R10 — Machines (minimal)
PDD: §25. `Machine` + `MachineAssignment`, admin counts. No maintenance/
utilization v1 (YAGNI).

### R11 — MissingPiece module
PDD: §28 (defect root-cause edge cases) + §31.3. Case-level defect root-cause
(which stage lost pieces, who, why). Detailed design source:
[ROADMAP_REVIEW_POST_C1_2026_06_11.md](ROADMAP_REVIEW_POST_C1_2026_06_11.md)
(pre-PDD locked roadmap). Schedule after R9.

## Gated backlog (not schedulable — gate + source cited per row)
| Item | Gate | Source |
|---|---|---|
| G1 raw-material costing | after R-phases stable | PDD §24 |
| TM-1 tracking mode (Manual/None) | post-deploy (locked TM requirement) | PDD §6 + [REQUIREMENT_REVIEW_STAGE_TRACKING.md](REQUIREMENT_REVIEW_STAGE_TRACKING.md) |
| TM-2 tracking mode (Barcode/Both) | future Barcode/Traceability review | PDD §6/§31.3 + [REQUIREMENT_REVIEW_STAGE_TRACKING.md](REQUIREMENT_REVIEW_STAGE_TRACKING.md) |
| S6 `reported_quantity` retirement | deploy + soak (irreversible) | foundation stream (pre-PDD lock; CLAUDE.md + [PRE_S1_DESIGN_ADDENDUM.md](PRE_S1_DESIGN_ADDENDUM.md)) |
| ADR-0007 era-A deletion | soak | [ADR-0007](adr/0007-allocation-era-ledger-cutover.md) (pre-PDD lock) |
| F5 yearly ledger close | scale trigger (multi-year) | PDD §31.1-F5 |
| G6 SKU → G5 stock → G2 orders → P&L | strict order, ADR-0008 | PDD §26 |
| Subcontracting (external-User pattern) | business need | PDD §31.1-F7 |

### Verification sources
Derived 2026-07-04 from PDD v1.0 §§3,6,14–18,20–21,23–25,27,29,31 — every phase
cites its sections above. Dependencies hand-traced against the service layout
verified this session. Confidence: High.
