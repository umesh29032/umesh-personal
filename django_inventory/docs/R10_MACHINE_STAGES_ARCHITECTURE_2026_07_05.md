---
id: r10-machine-stages-architecture-2026-07-05
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# R10 REDESIGN — Machines as the foundation of machine-based production stages

> **OP-1 ✅ IMPLEMENTED 2026-07-05 (gate PASS 864, browser-proven on 3-PATTI-011):**
> multi-worker dimension-scoped operations — flow-editor "Work split" (grain UI over
> `set_stage_grain`), pool materialize wired at the advance funnel, manager "Split the
> work" panel (available-per-dim from cutting's APSCPB → `WorkerStageAllocation`,
> void returns qty), BLIND worker reporting (schema options = own allocated dims,
> labels only — worker is never shown cut/allocated quantities), manager board
> (Allocated/Good/Alter/Missing/Verified/Expected ₹ per worker), worker panel lens =
> own slice only. Leak fixes: generic panel board + Adda overview totals now
> management-only. NO new models/migrations/money paths — S4 foundation consumed
> as designed. Receipt: [OP1_EXECUTION_PLAN](OP1_EXECUTION_PLAN.md).

> **STATUS: 🔒 APPROVED + FROZEN (owner, 2026-07-05) — THE permanent
> production architecture.** Registered as PDD amendment 5. Changes to this
> foundation require an explicit owner-approved architecture amendment
> BEFORE implementation. Owner's frozen rules 1-12 are §RULES below.
> (v3 = operations model + Stage Categories; v2 added Work Type.)
> **R10-A ✅ + R10-B ✅ IMPLEMENTED 2026-07-05** — gate 848, golden OK; the
> config-only proof ran LIVE: Overlock created purely via UI (Stage row +
> Stitching category + Overlock Machine type + master skill + Flow-Editor
> ₹5/pc) → generic panel (prev-snapshot + skill picker + Machine OL-001
> holder) → phone report 40 good/2 alter/1 missing → frozen ₹200 (good-only
> pays). Category rollup + worker current-op focus live. R10-C = every next
> operation is configuration.
> Owner redefined the business model 2026-07-05: machines are not an asset
> register; after Cutting, almost every future stage (Overlock → Stitching →
> Embroidery → Button → Checking → Packing) RUNS ON a machine. This document
> replaces the thinking in [R10_EXECUTION_PLAN.md](R10_EXECUTION_PLAN.md) v2
> (which stays valid as the asset-layer subset). Supersedes-note: approving
> this = a PDD §25 amendment (machine-stage integration supersets the frozen
> "minimal" scope) — will be registered in the PDD amendments on approval.

## RULES (owner-frozen, 2026-07-05)

1. Every **business operation** is a Stage. 2. Business **processes**
(Stitching, Finishing…) are **StageCategories**, never Stages. 3. Every Stage
defines: category · work type · machine type (Machine only) · access rules ·
workflow position · rate · reporting · verification · snapshot. 4. **Work
Type is the canonical business rule** (Manual ⇒ no MachineType; Machine ⇒
MachineType mandatory; the DB constraint is the single enforcement point).
5. MachineTypes are reusable across operations. 6. Physical Machines are
assets only — runtime resources via MachineAssignment; they never own
workflow, costing, reporting, verification, settlement. 7. WorkerStageTask =
single owner of work lifecycle. 8. MachineAssignment = single owner of
machine possession history. 9. WorkerStageContribution = single owner of
production quantities. 10. Settlement = the only place money moves.
11. Every future operation must be configurable through the existing engine —
no new stage-specific architecture when the generic engine suffices.
12. Foundation-affecting changes require an explicit owner-approved
architecture amendment before implementation.

Implementation rules (R10): do NOT redesign the production engine, settlement,
payroll, WorkerStageTask, snapshots, or A360 — extend only through the
approved extension points; anything that genuinely cannot fit ⇒ STOP,
document, wait for approval.

## 0-A) The operations model (v3) — a Stage is a business OPERATION, never a process

**Owner realization (adopted): "Stitching" is not a stage — it is the
collection of stitching operations.** The workflow runs operation by
operation, each a full first-class Stage:

```
Cutting → Overlock → Flatlock → Sleeve Join → Collar Attach → Side Stitch
        → Button Attach → Button Hole → Bartack → Checking → Packing
```

Review verdict — **cleaner, and it dissolves the hardest future problem.**
A composite "Stitching" stage would eventually have demanded sub-stages:
multiple machine types inside one stage (breaks the single
`Stage.machine_type` link), multiple rates inside one stage (breaks the
single `WorkflowStage.cost_rate`), mixed contribution kinds — i.e. a
REDESIGN of the engine's one-stage-one-everything grain. Operation-as-stage
means every operation natively gets what the engine already guarantees:
**one rate · one roster · one report · one verification · one snapshot · one
settlement calculation** — nothing special for stitching, nothing special
for machines. This is also why the L3 config-only archetype matters: eight
stitching operations are only viable because each new operation is
CONFIGURATION, not code.

Two business rules locked with it:
- **Stage names = business operations, never machine numbers.** "Overlock",
  not "OL-001". Machine Type says HOW; physical machines (OL-001…OL-010) are
  register entries bound at runtime — buying ten more Overlocks changes
  NOTHING in any workflow.
- **Per-product flows stay per-product** (WorkflowStage order — a T-shirt's
  operation list differs from a Nikkar's; already supported).

## 0-B2) DATA-DRIVEN MASTERS (owner rule, 2026-07-05 — audited + completed same day)

**"The business owns the data, not the code."** Audit outcome: StageCategory
(the owner's "Stage Type" concept — same thing, one name) was ALREADY a
database master (rows + FK, zero Python choices; names appear only in the
seed migration). What was missing was the OWNERSHIP layer, now shipped:
`is_active` on StageCategory (migration 0047) + full CRUD pages for
**Stage Categories** and **Machine Types** (Stage-library header → Categories /
Machine Types; perm-gated like Stage CRUD: `production.*_stagecategory` /
`*_machinetype`). Create/rename/reorder/deactivate = pure data; pickers read
ACTIVE rows only; deactivation never touches existing stages (PROTECT FK —
history keeps its label). Pinned by test: no static category options may ever
exist in code. **The ONE deliberate exception:** `Stage.work_type`
(Manual|Machine) stays a code-level enum — it is an ENGINE EXECUTION RULE
(the pair-constraint + machine semantics implement its meaning), not a
business classification; a future value (e.g. subcontracted) requires engine
behavior, hence code, per the frozen v2 verdict.

## 0-B) Stage Categories — first-class METADATA, never workflow

Owner wants grouping for dashboards/reporting/filters: *Pre Production*
(Layering, Pattern Design, Cutting) · *Stitching* (Overlock … Bartack) ·
*Finishing* (Thread Cutting, Checking, Iron, Packing) · *Dispatch*.

**Decision: first-class metadata — a `StageCategory` master
(code, name, display_order) + nullable `Stage.category` FK — with a HARD
rule: the workflow engine, money paths, and access control NEVER read it.**
Why first-class rather than UI-side constants: the owner curates categories
himself (like the Stage library), every surface (dashboards, A360, reports,
filters) reads ONE source instead of drifting template lists, and long
pipelines can roll up honestly ("Stitching 3/8 ✓") on mobile. Why
metadata-only: a category that gained lifecycle or money semantics would be
a second workflow — forbidden by the same one-door principle as everything
else. Guard: documented here + a source-inspection-style test (no
`category` reads in services/money paths).

Default mapping for existing stages (data migration): Layering / Pattern
Design / Cutting / Barcode Generation → **Pre Production** (owner may re-file
Barcode Generation later, e.g. under Dispatch).

## 0-C) Work Type — the owner's refinement (v2 of this document, same day)

**Every stage explicitly declares HOW its work is performed:**

```
Stage.work_type ∈ { MANUAL, MACHINE }        (required, explicit — never NULL)
Stage.machine_type → MachineType             (MANDATORY iff work_type=MACHINE,
                                              FORBIDDEN iff MANUAL — DB CheckConstraint)
```

Review verdict — **cleaner than machine_type alone, adopted**:
- Yes, `work_type` is technically derivable from `machine_type IS NULL` — but
  NULL is silent: it can't distinguish *"manual by business intent"* from
  *"machine stage someone forgot to configure"*. The explicit enum + the
  CheckConstraint make misconfiguration impossible and intent readable.
- It is EXTENSIBLE where NULL-semantics are not: a future third work type
  (e.g. `subcontracted`, PDD §31.1-F7) is an enum value, not a redesign.
- **One canonical predicate, no duplicate logic:** code asks `work_type`;
  `machine_type` is only the link to WHICH machine kind. The constraint keeps
  them consistent forever, so no branch can disagree.
- It widens the archetype: the generic handler serves **manual** config-only
  stages too (Checking, Packing…), not just machine ones — every future stage,
  manual or machine, follows ONE pattern.

**The permanent production model (all present + future stages):**

```
StageCategory (metadata: Pre Production | Stitching | Finishing | Dispatch …)
   ▲ display/reporting only — engine never reads it
Stage (= ONE business OPERATION: Overlock, Collar Attach, Checking …)
      ──▶ Work Type (Manual | Machine)
              │ (Machine only)
              ▼
          Machine Type ──▶ Physical Machine ──▶ Assigned Worker (operator window)
                                                     │
Product flow (WorkflowStage: order · rate · payability)   ← money lives HERE, always
                                                     ▼
     manager assigns → worker reports good/alter/missing → verify → snapshot
                                        → expected → settlement (one funnel)
```

**Defaults for existing stages (data migration, owner-specified):**
| Stage | work_type | machine_type |
|---|---|---|
| Layering | MANUAL | — |
| Pattern Design | MANUAL | — |
| Cutting | **MACHINE** | **Cutting Machine** (seeded MachineType) |
| Barcode Generation | MANUAL (proposed default — owner may flip in the hub) | — |

Note: existing bespoke handlers (layering/pattern/cutting/barcode) keep their
handlers — `work_type` is metadata on them, zero behavior change. The
archetype fallback applies only to stages WITHOUT a bespoke package.

**Factory questions this answers at any moment (Stage library reads, no new
logic):** which stages are manual · which require machines · which machine
type performs each stage · which physical machines are in use (assignment
windows) · who operates them.

**What Work Type improves — without duplicate business logic:**
| Surface | Improvement | Mechanism |
|---|---|---|
| Snapshots / A360 | stage cards show "Manual" or "Machine · Sewing · SW-001 (utest)" | ONE archetype renderer reading work_type |
| Operations dashboard | by-stage board can badge machine stages; machine tile unchanged | display read |
| Stage library / Flow Editor | work-type column + machine-type picker (shown only when MACHINE) | config UI, validation by the constraint |
| Reporting | "manual vs machine output" splits = a filter on Stage.work_type | queryset filter |
| Future costing | machine-cost allocation population = `work_type=MACHINE` stages; manual = labor-only (ADR-0011/0009 untouched today) | future SELECT, no logic now |
| Earnings / settlement / visibility | **NO CHANGE** — money never reads work_type; access predicate untouched | by design |

## 1) What changes in the architecture — three layers, one new idea

The deep insight: **your existing stage engine already IS the machine-stage
engine.** R8 proved the recipe — "a new earning stage adds ZERO earning code:
configuration + optionally a schema override" (stage_earnings_flow.md). What
machine stages need is (a) the machine asset layer underneath, (b) one
metadata link answering *"which machine performs this stage?"*, and (c) ONE
generic handler so unlimited future stages need **no code at all**.

```
L1  MACHINE ASSET LAYER (new `machines` app — R10 v2 content; NOTE as-shipped:
    MachineType lives in PRODUCTION (stage-domain metadata, keeps layering
    acyclic) and machines FKs down to it)
    MachineType(code, name)                    ← Overlock / Flatlock / Sewing / …
    Machine(code, name, type→MachineType,      ← the physical instances, status,
            status, notes)                        who exists / active / inactive
    MachineAssignment(machine, worker,         ← who operates it (windows,
            adda?, start_at, end_at)              one open holder per machine)

L2  THE CLASSIFICATION + LINK (three columns on the existing Stage library)
    Stage.work_type ∈ {MANUAL, MACHINE}  — HOW the work is performed (explicit)
    Stage.machine_type → MachineType     — WHICH machine kind (mandatory iff
    MACHINE, forbidden iff MANUAL; DB CheckConstraint)
    Stage.category → StageCategory       — WHERE it groups (metadata ONLY —
    §0-B; engine/money/access never read it). Rates/earnings stay on
    WorkflowStage (ADR-0009 untouched): the STAGE owns money, never the machine.

L3  GENERIC STAGE ARCHETYPE (one handler package, forever — §0 widened it)
    production/stages/generic_stage/ — ONE StageHandler subclass serving
    EVERY stage (MANUAL or MACHINE) that has no bespoke package:
      contribution_schema → good / alter / missing per line (schema-driven
        phone form, existing template machinery)
      snapshot + admin_snapshot → work type badge; for MACHINE stages also
        machine type + instances on this Adda; per-worker good/alter/missing
        totals (the shared partial renders it)
      start/complete/reopen → the _shared skeleton (PAY-2, C3 guard,
        settled-block, downstream-consumer guard all apply automatically)
    Registry fallback: `registry.get(code)` returns the archetype for any
    stage without a bespoke package (work_type-aware rendering).
    ⇒ **future stages become CONFIGURATION, not code** — manual (Checking,
    Packing) AND machine (Overlock, Stitching…): owner creates the Stage row
    (code, access skills in the Access hub), sets Work Type (+ MachineType if
    MACHINE), adds it to a product flow with a rate in the Flow Editor —
    report form, panels, snapshots, A360, pickers, settlement all just work.
    Zero deploy.
```

Product → WorkflowStage → (Stage.machine_type) → workers assigned →
worker reports good/alter/missing → verified → expected → settlement —
**identical to today's lifecycle**, because it IS today's lifecycle.

## 2) What is reused (verified against code, 2026-07-05)

| Existing mechanism | Role for machine stages | Change needed |
|---|---|---|
| `WorkerStageTask` + `set_stage_workers` | assignment, ≤1 active, manager-only roster | NONE |
| `WorkerStageContribution` (S3 good/alter/missing columns EXIST) | worker's own report | NONE (columns already there) |
| `report_contributions` chokepoint (C-TM one door) | line writes | **additive**: accept optional `alter/missing` per line (today the phone form sends good only); same single writer |
| `contribution_schema` seam (handler.py:143 — "adding a stage needs NO worker-UI edit") | good/alter/missing phone form | one schema dict in the archetype |
| Expected freeze (`good_quantity × frozen rate`, worker_task_service:308) | earnings | NONE — alter/missing never pay (owner D2) |
| Settlement funnel / ledger / payroll / F&F | money | NONE — stage-owned, machine-blind |
| `stage_rate_service` (per (SR,role) freeze, rerate) | rates | NONE — Flow Editor config per stage |
| Stage snapshots (`admin_snapshot` + shared partial + prev-stage injection) | admin story per stage | archetype implements once |
| A360 (source-inspection-pinned: NO stage-name literals) | per-Adda board/timeline/money | NONE — new stages appear automatically |
| Access control (Stage.access_by_skill + the ONE live predicate + `eligible_stage_workers` pickers) | who sees/works each stage | NONE — owner wires skills per new stage in the hub (rule 2 holds) |
| Worker isolation (own task, own report, no ₹ leak) | worker screens | NONE |
| Mobile report UI (schema-driven), form-shell, FancySelect | UX | NONE |
| Reopen guards, C3 guard, verified-qty audit, history events | lifecycle | NONE |
| R10 v2 asset design (windows, partial-unique holder, service writer, ops tile) | L1 | carried over + `MachineType` |

The two genuine foundation-seam extensions (both additive, both need this
approval): **registry fallback** (a few lines in `registry.get`) and
**alter/missing line capture** (schema keys + parser + service param through
the SAME chokepoint). Plus **two columns** on `Stage` (`work_type` enum + nullable `machine_type` FK, consistency CheckConstraint) and the §0 data migration for the four existing stages.

## 3) Stage → Machine, MachineType → Stage, or something else?

**Answer: `Stage.machine_type` (stage TYPE → machine TYPE), with physical
instances bound at runtime via MachineAssignment.** Reasoning:

- `WorkflowStage → Machine` (instance) is WRONG: a product's flow must not
  pin a physical machine — instances differ per Adda, per day, per breakdown.
- `MachineType → Stage` (machine owns stages) is backwards: the stage is the
  production concept that owns order/rate/report; the machine is HOW it runs.
- `Stage.machine_type` reads exactly like the business sentence: *"Stitching
  runs on a Sewing machine."* It is metadata — never in money math.
- WHICH physical instance did the work is already captured by
  `MachineAssignment(machine→type, worker, adda, window)` — the admin's
  "which machine" view = open assignments on this Adda whose machine type
  matches the stage's type. If per-stage-record instance binding is ever
  wanted, `MachineAssignment.stage_record` is ONE additive nullable FK —
  documented, not built (YAGNI).

This supports unlimited future stages with zero redesign: every new stage =
one Stage row pointing at a MachineType.

## 4) How future machine stages work (Overlock, Stitching, Embroidery, …)

Owner's flow, end to end — after R10-B ships, each NEW stage is minutes of
configuration:

1. **Once per machine kind:** create MachineType (e.g. Sewing) + its physical
   Machines (SW-001…) in the register; assign operators (windows).
2. **Once per stage:** Stages library → new row `stitching` ("Stitching"),
   pick MachineType=Sewing, wire access skills in the Access hub (e.g. a new
   `stitching_operator` skill). No deploy.
3. **Per product:** Flow Editor → add Stitching after Overlock, set
   per_piece rate ₹X, ✓ Pays workers. (Grouping/non-payable levers work too.)
4. **Per Adda (daily life):** manager assigns workers on the stage panel
   (picker = live access rows); workers see ONLY their task on their phone;
   report **Good / Alter / Missing**; manager reviews (verified-qty path),
   completes; snapshot becomes the next stage's reference; A360/Operations
   update; settlement pays `verified ?? good × frozen rate` through the one
   funnel. Identical story to Layering/Pattern/Cutting today — because it is
   the same machinery.

## 5) Admin and Worker screens

**Admin (all existing surfaces, fed automatically):** stage panel = roster +
per-worker report status + verified quantities + complete; stage
`admin_snapshot` = machine type · instances on this Adda · Σ good/alter/
missing per worker · total vs remaining (vs prev-stage good, the S4 pool
foundation when enabled); A360 = progress/health/worker board/money strip;
Operations = pending reports/stalled; Machines register = who holds what now.
**Worker (phone, unchanged lens):** own task card → own report form
(good/alter/missing) → own submitted state → own Expected on My Earnings
(monthly workers: badge, never ₹) — plus, future map, a "my machine" chip.
Never other workers' production (existing isolation, unchanged).

## 6) Is this better than R10 v2? — YES, and v2 survives inside it

v2 built an asset register beside production; your business model makes
machines part of production. The redesign keeps v2's ENTIRE asset layer as
R10-A and adds the production integration as R10-B — nothing thrown away,
and the "isolated module" risk you flagged is designed out: machine stages
reuse WST, contributions, settlement, snapshots, A360, dashboards,
assignment flow and the mobile UI **by construction**, because they run on
the same engine. The alternative (keeping v2 and bolting machine stages on
later) would have forced exactly the parallel-flow duplication rule 6 forbids.

## Delivery phases (each owner-gated, each with gate + browser E2E)

| Phase | Content | Est |
|---|---|---|
| **R10-A** Machine foundation | v2 plan + `MachineType` (seed incl. Cutting Machine) + `StageCategory` master (seed 4 categories) + `Stage.work_type`+`machine_type`+`category` columns (+CheckConstraint + §0 defaults data migration) + Stage-library/Flow-Editor config UI (work-type + category pickers) + register/assignments/ops tile | ~7.5h |
| **R10-B** Generic-stage archetype | `generic_stage` handler (manual+machine) + registry fallback + alter/missing line capture (schema+parser+service, one door) + FIRST real stage (Overlock) configured on the 3-PATTI flow + full E2E: assign → phone report good/alter/missing → verify → complete → snapshot → A360 → settle | ~8h |
| **R10-C…** every next stage | CONFIGURATION ONLY (Stage row + work type [+ machine type] + skills + flow rate) — minutes, no code, manual or machine | ~0 |

Risks beyond v2's: registry-fallback correctness (pinned by an
open-closed test: unregistered machine-typed stage renders+round-trips),
alter/missing parser (schema-driven, golden untouched — good stays the only
payable), Stage column touching a frozen app (additive nullable, zero
behavior). Acceptance = R10-B E2E proves the owner's §"HOW STAGES SHOULD
WORK" section verbatim on 3-PATTI.

## FINAL PRE-IMPLEMENTATION VERIFICATION (owner's 10-point review, 2026-07-05)

**§2 — one owner per responsibility (verified, no duplicates):**

| Layer | Owns EXACTLY | Never owns |
|---|---|---|
| StageCategory | grouping/rollup for display+reporting | workflow, money, access |
| Stage (operation) | identity, work_type, machine_type link, access skills | order, rates |
| WorkflowStage | per-product order · rate · payability · grouping | execution state |
| Work Type | HOW performed (canonical predicate) | which machine kind |
| MachineType | machine KIND; reusable across ANY number of stages (plain FK, many-stages→one-type — §4 verified: no uniqueness anywhere) | stage identity, money |
| Machine | physical instance + status | operations, workers' pay |
| MachineAssignment | operator↔instance possession windows (+adda) | work quantities, stage state |
| WorkerStageTask | work assignment lifecycle | possession, money |
| WorkerStageContribution | reported good/alter/missing (immutable) | rates |
| Verification | management correction (verified_quantity) | reported truth |
| Snapshot | read-only reference render | stored copies (beyond designed freezes) |
| Settlement funnel | THE money boundary | production truth |

**§3 — constraint sufficiency:** the pair-constraint
(`MANUAL ⇒ machine_type IS NULL` ∧ `MACHINE ⇒ machine_type NOT NULL`) makes
every invalid row IMPOSSIBLE at the DB. Two operational edges covered beyond
it: `machine_type` FK is PROTECT (a MachineType in use cannot vanish) and
Flow-Editor/library validation surfaces friendly errors before the DB does.

**§5 — machine switching mid-stage (verified, the decoupling is the point):**
OL-001 breaks → release its window (+status=maintenance) → open OL-004
window. `MachineAssignment` has NO FK into WST/WSC — so WorkerStageTask,
contributions, verification, snapshots, settlement, payroll are structurally
UNTOUCHED; the worker submits ONE report as always; the stage snapshot's
"instances used" honestly shows both windows. Zero architectural change
needed — this scenario is why possession-windows and work-lifecycle are
separate models (§0.1 of the exec plan).

**§6 — config-only checklist (verified against live surfaces):** Stage CRUD
pages EXIST (`/production/stages/` list/add/edit) → add category/work-type/
machine-type pickers (R10-A); rate+placement = Flow Editor (exists); access =
hub (exists); handler = registry fallback (R10-B). **One honest gap found by
this review:** today only the 4 bespoke stages have start/complete
endpoints — R10-B therefore includes ONE generic parameterized action pair
(`…/stage/<stage_type>/start|complete`, exactly the existing `stage-panel`
URL pattern) that the archetype panel posts to. One set, forever; after
R10-B the checklist above is complete and NOTHING else is ever needed per
stage.

**§7 — 3-5 year scale (100+ machines · 50+ stages · hundreds of workers/
Addas):** DB shapes are indexed FKs + partial uniques (fine at 10⁵ rows);
funnel/ledger scale linearly per line (already the design); dashboards are
bounded per-stage — the category rollup + conscious perf re-pins absorb
longer flows. **One concept intentionally absent: "production line"** — if
the factory later runs parallel lines, a line is ONE additive metadata
dimension (on Adda), not a redesign; noted so it's a decision, never a
surprise.

**§10 — engineering verdict (adversarial):** production-grade YES. What I
would still watch (not redesign): the sequential-per-Adda engine (limit #1
below) is the only ceiling with business consequences — its future is
bundle-level progression on the S4 pool, already foundationed; the category
fence needs its guard test from day one; `MachineAssignment.adda` is the
loosest link (per-SR binding = one documented additive FK if reporting ever
demands operation-level machine attribution). Simpler alternatives were
examined and rejected for cause: machine-number-as-stage (owner rule, breaks
workflow stability), composite process stages (breaks one-stage-one-rate),
machine_type-only without work_type (silent-NULL ambiguity), UI-constant
categories (drift). No hidden debt found beyond the documented limits below.

## UI PHILOSOPHY (owner-final, 2026-07-05 — presentation only, engine untouched)

**StageCategory = the SINGLE source of truth for presentation grouping.** No
page hardcodes "Stitching"/"Finishing"/"Pre Production" — every grouping
derives from `Stage.category` rows through ONE shared helper + partial, so a
new operation (Pocket Attach, Label Stitch, Elastic Insert…) files itself
automatically. The engine keeps iterating `WorkflowStage.order` exactly as
today; categories change NOTHING below the template layer (fence-tested).

| Surface | Presentation |
|---|---|
| Adda detail (stages overview) · A360 board · Operations by-stage | **category-grouped, summary-first, collapsible** — "STITCHING · 4/7 complete", expand for operations. Single-category flows render as today (no header noise) |
| Worker Adda card / phone | **current-operation focus**: current op (+machine when machine-stage), own completed qty, submit report; optionally prev ✔ / next. Never the full pipeline. (Assigned/Remaining qty = the allocation lever's phase — S4 flags; no invented numbers until then) |
| Admin category summary | operations x/y complete first; tap to expand |
| A360 category row (future data as it becomes honest) | ops x/y · workers · machines active · pcs progress |
| FLAT forever (workflow/money surfaces, not presentation) | stage panels (one stage each) · Flow Editor (order IS the content) · settlement/costing lines · review-reports · history timeline |

One truth per concern (re-affirmed): workflow = `WorkflowStage.order` ·
money = the settlement funnel · access = `access_service` · presentation
grouping = `Stage.category`.

## Honest scalability notes (v3 — the limits the owner should know)

1. **The engine is SEQUENTIAL per Adda** (one `current_stage`). Operation
   decomposition makes flows longer (11-15 stages) but keeps them strictly
   one-after-another. If the factory ever runs operations in PARALLEL (bundle
   A at Collar Attach while bundle B is still at Overlock), that is
   bundle-level progression — the future barcode/bundle direction (TM-2) with
   the S4 piece-pool as its foundation. The operations model does NOT block
   it (stages stay the unit; only progression granularity changes), but it is
   a separate future phase, not free.
2. **Long pipelines need density work**: 11+ chips per Adda card overflows
   phones. The mitigation is exactly Stage Categories — pipeline rolls up to
   category chips ("Stitching 3/8 ✓") with expand. Ship the rollup when the
   first long flow arrives (display-only change).
3. **Configuration burden grows**: 8-12 rates per product in the Flow Editor.
   Acceptable at current scale; a "copy flow from product" convenience is a
   backlog nicety, not architecture.
4. **Per-stage query pins**: the Adda page pin (61 queries at 4 stages) grows
   with stage count — bounded per-stage, but the perf baselines will be
   re-pinned consciously as flows lengthen.
5. **More reopen/peel steps** on long chains (reverse-first discipline) —
   works unchanged, just more clicks in rare corrections.

None of these are redesign risks; 1-2 are documented future phases, 3-5 are
operating costs of the finer grain the business wants.

### Verification sources (this review, main-thread)
handler.py:26-180 (contract + schema seam + checklist hook) ·
registry.py:17-43 (dict + get/has) · worker_task_service.py:159-193/308
(lines shape, S3 dual-write, good-only freeze) · stage_earnings_flow.md
recipe · A360 genericness pin (test_a360_overview) · access/picker single
predicate (freeze closeout) · R10 v2 plan §0.
