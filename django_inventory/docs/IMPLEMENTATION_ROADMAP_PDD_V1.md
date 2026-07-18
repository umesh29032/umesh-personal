---
id: implementation-roadmap-pdd-v1
type: topic-canonical
status: frozen
owner: frozen
scope: PDD-derived execution roadmap R1–R11 (historical register)
anchors: docs/PRODUCT_DESIGN_DOCUMENT.md
verified: 2026-07-13
---

# IMPLEMENTATION ROADMAP — derived from 🔒 PDD v1.0

> **📍 CURRENT STATE lives elsewhere (pointer added 2026-07-13, Phase-7 Q-A2):** this
> roadmap is the frozen R1–R11 execution register; R10 + OP-1 + Phase-3 config are DONE and
> the engine is frozen — **for "what is true now" read
> [MANUFACTURING_V1_FREEZE.md](MANUFACTURING_V1_FREEZE.md)** (owner-declared 2026-07-06) and
> the campaign state in [DEPLOYMENT_CAMPAIGN_STATUS.md](DEPLOYMENT_CAMPAIGN_STATUS.md).
> (Source: DOCUMENTATION_INDEX row for this file; discovery finding F-A-09/D-03.)

> **Source of truth:** [PRODUCT_DESIGN_DOCUMENT.md](PRODUCT_DESIGN_DOCUMENT.md)
> (frozen 2026-07-04). Every task below cites its PDD section (or, for pre-PDD
> locked-stream items in the gated backlog, its locked source doc). Scope
> changes go through a PDD revision or ADR first — never through this file.
> Execution model: **one phase at a time**, owner-gated between phases.
> Naming: R1–R11 here are ROADMAP phases — unrelated to the 2026-06
> stage-domain-review "R1" or the foundation "F1–F4"/"F3 auto-cancel" labels.
>
> **Universal exit gate (every phase):** `bash scripts/check.sh` green
> (811 tests as of A360, run from `config/`) · golden ₹225 byte-identical on
> any money-touching phase · docs updated same session (CLAUDE rule 12) ·
> UI phases browser-verified at 360/768/1280 (rule 11) · PDD stays
> authoritative · testing on the REAL 3-PATTI workflow only (owner rule
> 2026-07-05, no synthetic products) · money-write STOP rule active.

## State after the foundation freeze (owner, 2026-07-05)

```
✅ DONE + ACCEPTED (uncommitted — checkpoint policy):
R1 → R2 → R3 → R4 → R5 → R6 → R7 → R8 (+R9 inside R8) → A360
+ hostile-review fixes (H-1/M-2/M-3/M-4/L-3) + WP-A/B/C
+ ADR-0011 + one-rule non-payable freeze + mobile-density lock
+ E2E business audit (READY) + pre-R10 polish F-1..F-4 (gate 821):
  single My-Dashboard · explicit assignment at Adda start ·
  post-complete bounce (no worker 403) · shared active∩skill pickers
+ 🔒 FREEZE CLOSEOUT C-1..C-3 (gate 827, 2026-07-05): retro-tag REMOVED
  (manager assignment = ONLY roster source — PDD amendment 4; accounts→
  production edge gone, purity contract stricter) · every worker-facing
  listing uses the ONE live predicate (access ∩ assignment; dashboard =
  Adda-page behavior) · report view requires assignment AND live access ·
  V-1 visibility-vs-action split documented (RBAC.md)
═══ OPERATIONAL FOUNDATION FROZEN (owner, 2026-07-05) ═══
─── NEXT SCHEDULABLE ───
R10 (machines)                          independent, anytime
R11 (MissingPiece)                      after R9 (defect flows richest)
─── soak/roadmap-gated (not schedulable now) ───
G1 materials · TM-1 tracking-mode · TM-2 barcode-tracking · S6 reported
retirement · ADR-0007 deletion (also resolves hostile-review H-1 root) ·
F5 ledger close · subcontracting seam · explicit-assignment migration
(→ strict C3) · G6→G5→G2→P&L · future cost-allocation phase (ADR-0011)
```

## Phases

### R1 — Navigation, visibility & the F1 guard  *(UI-heavy, no money logic)*
**STATUS: ✅ COMPLETED — accepted by owner 2026-07-04, commit c957fa84.
Plan: [R1_EXECUTION_PLAN.md](R1_EXECUTION_PLAN.md); gate PASS 714 tests;
golden OK; browser-verified 360/768/1280 both roles.**
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
**STATUS: ✅ ACCEPTED by owner 2026-07-04 (uncommitted — checkpoint policy).
Plan: [R2_EXECUTION_PLAN.md](R2_EXECUTION_PLAN.md); gate PASS 726; live phone
E2E: 45 layers → ₹450 expected.**
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
**STATUS: ✅ ACCEPTED by owner 2026-07-04 (uncommitted — checkpoint policy).
Plan: [R3_EXECUTION_PLAN.md](R3_EXECUTION_PLAN.md); gate PASS 734; live
browser block+override E2E. TRANSITIONAL: guard blocks IN_PROGRESS only
(owner "B now + A later") until the explicit-assignment migration (gated
backlog) removes legacy auto-assign — then fully strict.**
PDD: §16, §27-C3.
1. Default: stage complete REFUSES while assigned workers pending (replaces
   the default auto-cancel path — foundation label "F3", NOT PDD §31.1-F3).
2. Super-Admin override: mandatory reason → recorded via `history_service`
   (audit trail); overridden tasks then auto-cancel as today (cancelled, named).
3. Keep explicit un-assign/cancel flows untouched (manager can still cancel a
   worker deliberately BEFORE completing).
Exit: tests for block, override+reason persisted, named-worker error message.

### R4 — MONTHLY pay basis (D4)
**STATUS: ✅ ACCEPTED by owner 2026-07-05 (uncommitted — checkpoint policy).
Plan: [R4_EXECUTION_PLAN.md](R4_EXECUTION_PLAN.md); gate PASS 750; golden OK;
live browser E2E (block/confirm/audit/exclusion/finalize/roles). P-1..P-4 +
warn-and-confirm addendum implemented; expense migration 0012. DEV test data
retained through R5-R7 (owner instruction).**
PDD: §17, §27-D4, §21-link.
1. `WorkerProfile.pay_basis` (piece_rate default | monthly) — migration.
2. Structural guard at the settlement chokepoint: monthly workers' contributions
   NEVER become settlement lines (test: monthly worker settles to zero lines,
   piece-rate colleague on the SAME stage settles normally).
3. Expected-earning display for monthly workers: analytics-only presentation
   (no ₹ expectation shown).
Exit: golden untouched; double-pay impossibility test.

### R5 — FactoryExpense module
**STATUS: ✅ ACCEPTED by owner 2026-07-05 (uncommitted — checkpoint policy).
Plan: [R5_EXECUTION_PLAN.md](R5_EXECUTION_PLAN.md); gate PASS 767; golden OK;
live browser E2E. P-1/P-2 + owner business rule locked as
[ADR-0011](adr/0011-monthly-salary-factory-level.md) (monthly salary =
factory-level, NEVER per-Adda-allocated); expense migration 0013.**
PDD: §21.
1. `FactoryExpense` model (category, amount>0 CHECK, expense_date, entered_by;
   append-only posture: create/void, no edit).
2. Admin CRUD UI + monthly totals on admin dashboard.
Exit: constraint tests; mobile-usable entry form.
**Post-R5 hostile review + fixes DONE 2026-07-05
([R5_HOSTILE_REVIEW](R5_HOSTILE_REVIEW_2026_07_05.md), gate PASS 775):**
H-1 era-A monthly guard (flag-independent) · M-2 ⚠ TEMPORARY no-advances-for-
monthly rule · M-3 duplicate-salary warn-and-confirm · M-4 payroll-overview
monthly visibility + badge · L-3 User.salary → salary prefill · full
payment-path census CLEAN (era-A was the only hole).

### R6 — verified_quantity audit trail (F6)
**STATUS: ✅ ACCEPTED by owner 2026-07-05 (implicit via R7 go-ahead;
uncommitted — checkpoint policy). Plan:
[R6_EXECUTION_PLAN.md](R6_EXECUTION_PLAN.md); gate PASS 779; no migration;
live browser E2E.**
PDD: §31.1-F6, §29.
`set_verified_quantity` emits history event (who/old/new/when) via
`history_service`. Tiny, independent.

### R7 — Full & Final settlement (D5)
**STATUS: ✅ ACCEPTED by owner 2026-07-05 (uncommitted — checkpoint policy).
Plan: [R7_EXECUTION_PLAN.md](R7_EXECUTION_PLAN.md); pre-implementation
verification CLEAN 4/4 before any code; gate PASS 788; golden OK; live
browser E2E; expense migration 0014. Canonical business flow:
[fnf_business_flow.md](LEARNING_2_0/DATA_FLOWS/fnf_business_flow.md).**
PDD: §20, §27-D5, §31.2 (deactivation never blocks money).
**🔒 ADR-0011 guardrail (hostile review 2026-07-05, M-1):** the per-worker
line-collector MUST reuse the `_settleable_lines` funnel (or its exact
monthly filter) — a fresh collector would silently bypass the R4 exclusion.
Monthly F&F = ZERO earning lines + audited advance WRITE-OFF (the only exit
for a monthly worker's outstanding advance — see review M-2) + deactivate;
pin with a test.
1. Service: resolve open tasks (complete-with-reported or audited cancel) →
   per-WORKER settlement across all unsettled lines (reuses engine, scope=worker)
   → advance clearance with explicit AUDITED WRITE-OFF entry for residual →
   cash payment event → deactivate.
2. Edge tests: zero-payable + outstanding advance; F&F then Adda-reopen attempt
   (settlement armor must refuse); monthly worker F&F (needs R4).
Exit: golden untouched; ledger write-off category audited.

### R8 — Pattern Design redesign + rename + layering reversal  *(owner spec ARRIVED 2026-07-05)*
**STATUS: UNBLOCKED — spec-of-record + impact analysis:
[STAGE_TRIO_SPEC_IMPACT_2026_07_05.md](STAGE_TRIO_SPEC_IMPACT_2026_07_05.md)
(functions as the owner-approved PDD §15/§16 amendment). Scope: "Cutting
Pattern"→"Pattern Design" display rename (identifier frozen) · pattern-master
phone report = verification CHECKLIST of ProductPatternAssignments (+ optional
photos) · FIXED-per-Adda pay (rate per product, fixed double-guard at the
chokepoint) · layering = production-input-only (credits_workers=False after
C-1 delete-and-rebuild) · layering→pattern lead-time analytics · **GENERIC
stage-snapshot architecture** (handler `admin_snapshot` + one shared partial +
auto prev-stage consumption — the standard for Bundling/Sewing/Checking/
Packing and reused by Adda-360).
**STATUS: ✅ ACCEPTED by owner 2026-07-05 (uncommitted — checkpoint policy).
Plan: [R8_EXECUTION_PLAN.md](R8_EXECUTION_PLAN.md); gate PASS 800; golden OK;
migrations prod 0043+0044; full REAL-3-PATTI trio E2E (₹1500 settled);
lead-minutes behavior + future waiting/working split documented
(STAGE_TRIO_SPEC_IMPACT §F).**
PDD: §15 + §17 + §30 recipe.

### R9 — Cutting: snapshot + config + real-workflow E2E  *(owner spec ARRIVED 2026-07-05)*
**STATUS: SUBSTANTIALLY DELIVERED INSIDE R8 (2026-07-05): the generic
snapshot gave cutting its "Pattern Design — reference" panel automatically;
₹100 configured via Flow Editor; bundles reused; the full-trio 3-PATTI E2E
ran through settlement. Remaining R9 scope (if any) = owner call at R8
review.**
PDD: §16 + §17 + §30 recipe.

### A360 — Adda-360 management overview  *(owner-accepted concept 2026-07-05)*
**STATUS: ✅ ACCEPTED by owner 2026-07-05 + follow-ups (one-rule freeze, mobile-density) accepted (uncommitted).
Plan v2: [A360_EXECUTION_PLAN.md](A360_EXECUTION_PLAN.md); gate PASS 808;
golden OK; ZERO migrations/writes; genericness test-pinned (no stage names in
a360.py); live E2E on real 3-PATTI (settled + mid-flight + monthly + leak=0).
Design source: [ADDA_OVERVIEW_AUDIT_2026_07_05.md](ADDA_OVERVIEW_AUDIT_2026_07_05.md)
§4.** Scope: three READ-ONLY management panels on the Adda page (cost panel
w/ ADR-0009 full-cost + variance + recon flags — fixes finding P-COST ·
per-Adda worker board · money summary strip) + costing-page column relabel.
All data behind existing services; no new tables/writes; money-write STOP
rule applies.

### R10 — Machines + the operations production model 🔒
**R10-A ✅ + R10-B ✅ IMPLEMENTED 2026-07-05 (gate PASS 848; golden OK; live
config-only Overlock proof on 3-PATTI incl. phone good/alter/missing → ₹200
freeze; category rollup + worker current-op focus shipped; uncommitted).
Awaiting owner acceptance → R10-C = config-only operations forever.**
PDD: §25 as amended by **PDD amendment 5** — the owner-frozen
[machine-stages architecture](R10_MACHINE_STAGES_ARCHITECTURE_2026_07_05.md)
(operation-as-stage · StageCategory metadata · Work Type canonical ·
MachineType reusable · machines as runtime assets). Phases: **R10-A**
foundation (StageCategory+MachineType+Stage.work_type/machine_type/category in
production; machines app Machine+MachineAssignment; register+assign UI; ops
tile; config pickers) → **R10-B** generic-stage archetype (registry fallback +
generic start/complete endpoints + alter/missing capture + Overlock on
3-PATTI E2E) → **R10-C…** every next operation = configuration only.

### R11 — MissingPiece module
**ADR-0011 guardrail (hostile review 2026-07-05):** any worker-charge /
deduction mechanism must handle MONTHLY workers explicitly — they have no
settlement lines to deduct from.
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
| ADR-0007 era-A deletion | soak | [ADR-0007](adr/0007-allocation-era-ledger-cutover.md) (pre-PDD lock). **Also permanently resolves hostile-review H-1** (lever-ON allocation credits monthly workers — [R5_HOSTILE_REVIEW](R5_HOSTILE_REVIEW_2026_07_05.md)) |
| F5 yearly ledger close | scale trigger (multi-year) | PDD §31.1-F5 |
| G6 SKU → G5 stock → G2 orders → P&L | strict order, ADR-0008. **P&L guardrail (ADR-0011): SUM FactoryExpense at factory level only — never allocate into per-Adda cost; salaries + settled labor are disjoint populations (no double-count by construction)** | PDD §26 |
| Subcontracting (external-User pattern) | business need | PDD §31.1-F7 |
| **Explicit-assignment migration** — ✅ DELIVERED 2026-07-05 (F-2 removed `create_adda` auto-assign; freeze-closeout C-1 removed `sync_layering_workers_for_skill`; manager assignment = the only roster source, PDD amendment 4). **REMAINING PIECE, still gated: the strict-C3 flip** (R3 completion guard drops its transitional IN_PROGRESS-only filter and blocks on ASSIGNED too) — owner deferred pending manual business testing (C-4, 2026-07-05) | owner manual testing → decision | PDD §9/§16 + owner decisions 2026-07-04/05 |

### Verification sources
Derived 2026-07-04 from PDD v1.0 §§3,6,14–18,20–21,23–25,27,29,31 — every phase
cites its sections above. Dependencies hand-traced against the service layout
verified this session. Confidence: High.
