# PRODUCT DESIGN DOCUMENT — Kapil Enterprises Manufacturing ERP

> **STATUS: 🔒 PDD v1.0 (FROZEN) — approved by owner 2026-07-04.**
> This is the product-truth reference for all future development. From this
> point, no architectural change happens except through a new ADR or an
> approved PDD revision. The goal is execution, not redesign.
> Written 2026-07-04 after a full requirements-vs-code cross-check; hostile
> architecture validation §31 passed same day; owner decisions §27 resolved
> same day. Implementation roadmap derived from this document:
> [IMPLEMENTATION_ROADMAP_PDD_V1.md](IMPLEMENTATION_ROADMAP_PDD_V1.md).
>
> **Layering of truth (who wins on conflict):**
> - **Business intent** → THIS document wins.
> - **Mechanism / technical design** → the ADRs ([docs/adr/](adr/)) and
>   [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md) win; this document references and
>   never restates them in full (one-canonical-per-topic, anti-drift).
> - Technical overview for developers stays [PROJECT_KNOWLEDGE_MAP.md](PROJECT_KNOWLEDGE_MAP.md).
>
> Every ✅ below was verified against code on 2026-07-04 (branch `new_flask_app`).
> Every 🆕 is approved-scope-to-build. All decision points are RESOLVED by the
> owner (2026-07-04), recorded in §27, and binding.
> Build items are labelled by ROADMAP phase (R1–R11 of
> [IMPLEMENTATION_ROADMAP_PDD_V1.md](IMPLEMENTATION_ROADMAP_PDD_V1.md)); these
> are unrelated to the historical "R1" stage-domain-review or foundation "F1–F4"
> labels used elsewhere in the repo.

---

## 1) Product philosophy

One sentence: **a trust machine for a garment factory** — every piece of work,
every rupee, every metre of cloth is traceable forever, and "what a worker did"
can never be silently confused with "what a worker is paid".

Principles (all already load-bearing in code):

| # | Principle | Consequence |
|---|---|---|
| P1 | **Two truths, one gate.** Production truth (work) and financial truth (money) are separate record systems that meet only at settlement. | Money can never leak backward into production numbers. (ADR-0005) |
| P2 | **Append-only money & history.** Mistakes are reversed, never edited or deleted. | Every balance is explainable forever. (ADR-0002/0004) |
| P3 | **Snapshot, never live-read.** Prices/rates/roles are frozen at defined moments; later edits affect only future work. | Old Addas are immune to config changes. (ADR-0009) |
| P4 | **Single writer per truth table.** One service owns each ledger/truth table; CI enforces. | No second door, no unauditable rows. |
| P5 | **Data-driven configuration.** Stages, skills, rates, payability are rows, not code. | New products/stages/skills = data entry, not programming. |
| P6 | **Derived, never stored.** Balances/totals are live SUMs. | No stored total can ever drift from its rows. |
| P7 | **Honest-NULL.** Unknown ≠ zero; backfill only known facts. | Analytics never lie about the past. |
| P8 | **Worker phone-first; admin desktop-rich; never merged.** | Two UIs, one truth. |
| P9 | **YAGNI with reserved seams.** Build the minimum; leave named extension points (G1–G7 roadmap). | Scale designs exist on paper before code. (ADR-0006) |
| P10 | **Business correctness beats implementation convenience.** On any conflict, auditability, financial correctness, production traceability and historical accuracy WIN; code can be optimized later. | Owner lock 2026-07-04. The tie-breaker rule for every future design debate. |

## 2) Domain model & relationships

```
ClothRoll ──(adda FK)──▶ ADDA ◀──(product FK)── Product ◀── ProductSize / ProductPattern
    │ leftovers                │ stage_records                    │ workflow (per product)
    ▼                          ▼                                  ▼
RemainingClothOfClothRoll   AddaStageRecord ◀──(workflow_stage)── WorkflowStage ──▶ Stage (library)
                               │ typed record (LayeringRecord…)      order · cost_method · cost_rate ·
                               │ worker_tasks                        cost_billed_at · credits_workers ·
                               ▼                                     allocation_dimensions
                        WorkerStageTask ──▶ User (accounts)          + WorkflowStageRoleRate (per-role)
                               │ contributions                       + Stage.access_by_skill/role
                               ▼
                  WorkerStageContribution ──settlement_line──▶ StageWorkAssignment (earning line)
                    color · size · good/alter/missing ·                    │ adda_settlement
                    verified · expected_rate/earning ·                     ▼
                    role_snapshot                                   AddaSettlement ──▶ AddaSettlementItem (frozen)
                                                                           │ recovery_lines
WorkerLedgerEntry ◀──(assignment FK)── StageWorkAssignment                 ▼
    ▲ sole writer: ledger_service                              PayrollSettlementItem ──▶ WorkerAdvance
    └── PayrollSettlement (cash-only event)
AddaStageRoleRate = frozen pay-rate per (stage_record, role)   RateCorrectionAudit
StagePoolSnapshot / WorkerStageAllocation = piece-pool (S4, inert until stitching)
AddaHistory / ClothRollHistory / ProductHistory = append-only timelines
BarcodeBatch = piece identity (adda, seq) — payloads permanent (ADR-0010)
```

FK policy: **PROTECT** on every money/history anchor; CASCADE only where a child
is meaningless without its parent; SET_NULL for optional refs.

## 3) Adda lifecycle (creation → settlement)

```
START  (admin picks product → code auto: 3-PATTI-003)
  ├─ one AddaStageRecord per WorkflowStage of the product's flow
  ├─ pay-rate snapshots created (AddaStageRoleRate, per stage×role)   [S2 ✅]
  └─ visible to ALL workers as "new Adda started" (🆕 broadcast row);
     openable ONLY by assigned+skilled workers
STAGES run in configured order (§5); per stage:
  assign → report → complete → (verify) → auto-duration stamped
COMPLETE  (last stage completes → Adda.status=COMPLETED, completed_at set)
SETTLE    (AddaSettlement draft → finalize; §18)                       [✅]
PAY       (PayrollSettlement cash event; §18)                          [✅]
REOPEN    allowed until money exists: settlement-credited stage REFUSES
          reopen (armor ✅); downstream-consumer guard blocks unsafe reopen ✅
```

Adda statuses: `IN_PROGRESS` → `COMPLETED` (verified in `production/models/adda.py`).

## 4) Generic workflow engine ✅

- `WorkflowStage` = ordered per-product pipeline row (product FK, `order`,
  unique (product, order)).
- `Adda.current_stage` tracks position; `flow_service` owns advancement;
  stage N cannot start before N−1 completes; reopen is guarded (§3).
- Different products freely have 3/5/8 stages — data, not code. ✅

## 5) Generic stage engine ✅ (stage-domain review lock of 2026-06, historically labelled "R1" — not roadmap phase R1)

- Each stage type = a **handler package** (open-closed): typed record model
  (e.g. `LayeringRecord`), views, service hooks, `pool_grain`.
- Adding a future stage (stitching, packaging) = new handler package + Stage
  library row + flow-editor row. **No if/else on stage names anywhere.**
- Capture convergence **C-TM (locked)**: every reporting path (manual today,
  barcode later) writes `WorkerStageContribution` ONLY via
  `worker_task_service`. One door, forever.

## 6) Product stage configuration (flow editor) ✅

Per `WorkflowStage` the owner configures:

| Knob | Meaning | Exists |
|---|---|---|
| `order` | pipeline position | ✅ |
| `cost_method` | `per_piece · per_bundle · per_layer · fixed_cost` | ✅ (monthly pay = worker-level, NOT a stage method — §27-D4 resolved) |
| `cost_rate` | standard rate (double duty: manufacturing cost + default pay rate, ADR-0009) | ✅ |
| `WorkflowStageRoleRate` | per-role pay override (Cutting Master ≠ Helper) | ✅ |
| `cost_billed_at` | grouped billing → member stages structurally pay ₹0 (C-1 guard) | ✅ KEEP (§27-C2) |
| `credits_workers` | does completing this stage pay workers? | ✅ |
| `allocation_dimensions` | piece-pool grain (NONE / QUANTITY / COLOR_SIZE) — pool starts at cutting | ✅ |
| Allowed skills/roles | on the Stage **library** row (`access_by_skill`, `access_by_role`) | ✅ |
| Tracking mode (Manual/Barcode/Both/None) | TM-1/TM-2 — locked requirement, not yet built | 🔜 roadmap |

## 7) Worker lifecycle

```
CREATE user (admin) → assign user_type/role + SKILLS
→ appears in stage-assignment pickers only where skill matches
→ ASSIGNED to a stage (WorkerStageTask)
→ sees Adda/task on phone dashboard → works → DRAFTS → REPORTS quantities
→ COMPLETES task → expected earning frozen (visibility)
→ (management may VERIFY / correct via verified_quantity)
→ SETTLED (Adda settlement books real money) → PAID (cash event)
→ EXIT: Full & Final settlement (🆕 §20) → deactivate; history stays forever
```

Un-assign = task CANCELLED (never deleted). Worker deletion is impossible while
any money row exists (PROTECT).

## 8) Manager / Admin lifecycle

Start Adda → configure/adjust flow rates (until settled, audited) → assign
workers per stage → monitor combined progress (`review-reports`, pending-reports,
stalled) → verify quantities (optional, correction not overwrite) → complete
stages → settle Adda (draft → approve → finalize) → record advances anytime →
pay cash (settlement event) → analytics/costing dashboards.

## 9) Assignment model ✅

`WorkerStageTask` — one row per (stage_record, worker):
- Lifecycle `assigned → in_progress → completed → [verified] | cancelled`.
- DB rule: **≤ 1 ACTIVE task per (stage_record, worker)** (partial unique).
- Cancelled history accumulates (immutable work-that-happened).
- Assignment = the object-level half of access (§10). Roster = participation.

## 10) Permission & access model ✅ (ADR-0003)

Three concepts:
| Concept | Grants | Example |
|---|---|---|
| **user_type** | coarse account kind | staff vs worker |
| **role** | functional permissions (management vs worker vs accountant…) | `super_admin, manager, worker, listing_team, accountant` |
| **skill** | WHICH production stages a user can work | Cutting Master, Cutting Master Helper |

Enforcement layers (all ✅):
1. `SidebarItemRule` + middleware — menu hidden ⇒ URL blocked (one config, both enforced).
2. View gates — `permission_service.user_has_perm / user_has_role`; no raw `is_superuser`.
3. Stage gates — `access_service.user_can_access_stage` = skill ∩ stage's allowed skills.
4. Object gates — worker must also hold an ACTIVE `WorkerStageTask` (assignment).
5. Payroll scope — `can_view_worker`: worker sees only self; management all.

**Business rule (owner, this spec):** stage access = *assigned* AND *skilled*. ✅ built exactly so.

## 11) Skill model ✅

`accounts.Skill` rows; user ↔ skill M2M; stage ↔ allowed-skill M2M on the Stage
library. Adding a skill or granting stage access = data entry. Per-product skill
overrides (WorkflowStage-level) are deliberately NOT built (YAGNI; the library-level
rule has no known counter-example — revisit only with a real case).

## 12) Snapshot strategy & lifecycle ✅ (the freeze map)

| Moment | What freezes | Where | Why |
|---|---|---|---|
| Adda/stage start | pay-rate per (stage_record, role) | `AddaStageRoleRate` | later flow-editor edits never re-price started work |
| task complete | worker's role + `expected_rate` + `expected_earning` | `WorkerStageContribution` | role/rate changes never re-price done work |
| stage complete | `cost_method/rate/quantity_snapshot` + `processing_cost` | `AddaStageRecord` | manufacturing cost = price-at-time (ADR-0009) |
| settlement finalize | qty×rate per line + per-worker approved figures | `StageWorkAssignment` + `AddaSettlementItem` | what the owner approved is immutable evidence |
| until settlement | rates CORRECTABLE via audited super-admin `rerate_stage_role` (+ auto-recalc + `RateCorrectionAudit`) | S1.1 | mistakes fixable while no money booked |

Owner's "snapshot at Adda start" intent is satisfied by rows 1+2; row 3's
completion-freeze is the locked ADR-0009 mechanism and is functionally
equivalent protection (§27-C4 RESOLVED: keep exactly as implemented).

## 13) Inventory flow

```
Roll intake (rolls/bulk-add; supplier, weight, cost/kg) ✅
→ attach to Adda at Layering (filterable; missing roll? create from layering
  screen: quick-create / full-create) ✅
→ per-roll verification: width_verified_inch + weight_verified_kg ✅
→ layers_on_roll per roll (completion breakup table) ✅
→ leftovers MANDATORY at layering complete → RemainingClothOfClothRoll
  (weight + length, record-only today; consumption = deferred flag is_consumed) ✅
→ roll detached before complete → returns to unused pool ✅
Future: leftover consumption + material cost per Adda = G1 (§24).
```

## 14) Layering workflow — complete detail

The owner's 11 steps, mapped:

| Step (owner spec) | Status | Mechanism |
|---|---|---|
| 1. Admin starts Adda | ✅ | `addas/start` |
| 2. Assign workers (skill-gated) | ✅ | set_stage_workers; skills §10 |
| 3. Workers see it on dashboard | ✅ + 🆕 | assigned = actionable task; ALL workers get read-only "new Adda" row (🆕 broadcast, §27-D6) |
| 4. Collect rolls; filter inventory; add missing roll inline | ✅ | attach-roll + quick/full-create-roll |
| 5. Per-roll weight + width (mandatory) | ✅ | LayeringRollEntry verified fields (mandatory-at-complete gate) |
| 6. One layer length per layering | ✅ | LayeringRecord.layer_length_meters |
| 7. Number of layers | ✅ | per-roll `layers_on_roll`; `lay_count` = Σ |
| 8. Unused cloth recorded (no processing) | ✅ | RemainingClothOfClothRoll |
| 9. Table of rolls; edit/remove; removed roll freed | ✅ | entries list + remove routes |
| 10. Draft save anytime | ✅ | entries accumulate + draft fields; duration optional at draft |
| 11. Submit → next stage | ✅ | layering/complete (leftover gate) → pattern |
| **Pay per layer ₹10 (3-patti)** | 🆕 roadmap R2 | `cost_method=per_layer` exists; wire worker layer-earning → WSC via the single door; freeze `expected_earning = layers × rate`; attribution RESOLVED §27-D1: each worker reports ONLY their own layers |

Duration: auto-computed at complete (timestamps), draft may carry manual override
field but completion path stamps auto (`stage_views.py:785,847`). ✅ owner rule.

## 15) Pattern workflow ✅

One assigned worker (usually Cutting Master). Product design (`ProductPattern`)
defines required pieces (front/back/pocket/collar/sleeve/cuff…). Worker verifies
each required pattern (`CuttingPatternVerification`), optional photos
(`pattern/photos/add`), then completes. Duration = pattern.completed −
layering.completed (auto). Reopen guarded like all stages.

## 16) Generic multi-worker stage workflow ✅ (the stitching template)

```
manager assigns N workers → each sees ONLY own task (never others' numbers)
→ each reports independently: good / alter(defective-fixable) / missing
   (workers are NOT shown their allocated target — anti-anchoring ✅ by design;
    allocation lives in the internal S4 pool, ENFORCE flag default OFF)
→ each completes independently → manager sees combined progress + grand totals
   (review-reports: per-worker, expected vs actual vs defect)
→ stage completes when all assigned resolve (RESOLVED §27-C3: BLOCK while
   workers pending; Super-Admin override with mandatory audited reason —
   🆕 roadmap R3; TODAY's code still auto-cancels unreported tasks)
→ next stage auto-eligible; duration auto
```

## 17) Payment engine

| Basis | Status | Mechanism |
|---|---|---|
| per_piece | ✅ | qty = good pieces × rate |
| per_layer | ✅ (method exists; layering wiring = roadmap R2) | qty = layers × rate |
| per_bundle / fixed | ✅ | costing methods on stage |
| per-role rates | ✅ | WorkflowStageRoleRate → AddaStageRoleRate frozen |
| grouped stages | ✅ KEEP | `cost_billed_at`; members pay ₹0 structurally (C-1 guard) |
| **MONTHLY** | 🆕 | RESOLVED §27-D4: monthly = property of the WORKER (`WorkerProfile.pay_basis`), never the stage — a stage can host piece-rate karigar + monthly helper simultaneously. Monthly workers' contributions tracked for analytics, structurally EXCLUDED from settlement lines; salary paid via Expenses (§21). |

Payability is data-driven (`credits_workers`); PAY-2 guard blocks completion of a
paying stage with zero completed contributions (flag-aware, Phase-10 fix). ✅

## 18) Expected earning + settlement engine ✅ (LOCKED V2 §11 — reference only)

**Expected (visibility, never money):** at task complete —
`expected_earning = good_quantity × frozen_rate(role)`; shown immediately to the
worker. **Settlement (money):** draft (scratchpad, no money) → FINALIZE books,
per line, `settlement_quantity = verified ?? good` × `effective_pay_rate`
(grouped→0 wins over stale snapshots) → SWA earning line + ledger CREDIT;
advances recovered per-owner-decision (DEBIT + PSI row); per-worker frozen
`AddaSettlementItem`; reconciliation evidence persisted (M-6; BLOCK gate behind
default-OFF flag). Corrections: REVERSE / REVERSE+SUPERSEDE (compensating rows,
chain kept). Cash = separate `PayrollSettlement` (DEBIT settlement_payment).
Worker's three non-overlapping numbers: **Expected → Earned → Paid** (proven by
tests; golden ₹225 byte-identical).

Settlement timing: RESOLVED §27-C1 — owner settles whenever he decides
(completed payable lines); NO hard-gate on Adda completion.

## 19) Advance recovery ✅

Advance = separate loan pool (never debits payable at grant). At settlement the
owner chooses per-advance recovery amounts (`recovery ≤ remaining`, DB-checked);
reversal un-recovers (stamped `reversed_at`, excluded from sums). Remaining =
`Σ given − Σ active recoveries` — derived, never stored. Exactly the owner's
₹5000/₹3000/₹1000 example.

## 20) Full & Final settlement 🆕 (design)

Trigger: worker leaves before Addas finish. Service-only flow (no new tables):

1. Resolve open tasks: complete-with-reported or cancel (named, audited).
2. Run a per-worker settlement covering ALL unsettled completed lines across
   Addas (reuses the settlement engine, scope = worker not Adda).
3. Advance clearance: recover from payable; residual advance = explicit
   AUDITED WRITE-OFF entry (RESOLVED §27-D5 — nothing disappears silently).
4. Cash payment event; deactivate user (`is_active=False`).
5. History untouched forever (PROTECT + append-only already guarantee).

## 21) Expense model 🆕 (design — minimal)

`FactoryExpense(category[rent|electricity|salary|other], amount>0, expense_date,
notes, entered_by)` in the expense app; admin CRUD (create/void, no edit —
append-only posture); monthly dashboard sum. Monthly salaries recorded here
(links to §17 MONTHLY decision). NOT a general ledger — YAGNI.

## 22) Manufacturing costing ✅ (ADR-0009 — reference only)

`processing_cost` = frozen standard labor cost per stage (rate × quantity at
completion). Settled labor = actual worker cost. **The two are a duality — NEVER
added together.** Full-cost formula reserved: material (G1) + labor (pick ONE
source) + overhead allocation (§21 expenses / future). Grouped members freeze
0.00 (billed at payer). Per-Adda costing dashboard exists (`costing/`).

## 23) Dashboards ✅ philosophy + 🆕 additions

- **Worker (phone):** my tasks, my Addas, my expected/earned/paid, my advances,
  draft progress. Never sees admin data or other workers' numbers. ✅
  🆕 read-only "new Adda started" row (§27-D6).
- **Admin:** active/stalled Addas, pending reports, stage-wise progress, worker
  assignments, costing, settlement queue, payroll overview, advance exposure. ✅
  🆕 buttons: Adda → Settlement / Stage-Rates (roadmap R1). Machines/expenses/P&L panels
  arrive with their modules (§25/§21/§26).

## 24) Future raw-material costing (G1 — sketch only)

Per-stage required materials (thread, elastic, needle, sticker, label) with
reference cost on WorkflowStage; snapshot into Adda at start; consumption rows
at stage complete; material column of the ADR-0009 full-cost formula. Leftover
consumption (`is_consumed`) joins here. **Design slot reserved; build = G1.**

## 25) Machine management 🆕 (future, minimal)

`Machine(code, name, status[active|inactive|maintenance], notes)` +
`MachineAssignment(machine, worker, adda?, from/to)`; admin dashboard counts.
No maintenance scheduling, no utilization math v1 (YAGNI).

## 26) Revenue / Profit-Loss roadmap (gated)

ADR-0008 (locked): revenue NEVER enters manufacturing models. Path:
G6 SKU → G5 finished-goods stock → G2 orders/revenue → THEN P&L =
revenue − (manufacturing cost + expenses §21). Any earlier "quick P&L" inside
production models is refused by design.

## 27) Owner decisions — RESOLVED 2026-07-04 🔒 (binding)

| ID | Question | **Owner decision (locked)** |
|---|---|---|
| C1 | Settlement timing | **Keep settle-anytime.** Flexible, owner-controlled; settle completed work whenever required — never forced to wait for the whole Adda. |
| C2 | Grouped `cost_billed_at` mechanism | **KEEP.** Stronger protection than manual 0-rates; no refactor. |
| C3 | Stage completion with pending workers | **Block with Super-Admin override.** Default: stage cannot complete while assigned workers are pending. Super-Admin may override with a MANDATORY reason recorded in the audit trail. (Replaces the default auto-cancel behavior — foundation label "F3", distinct from §31.1-F3; build item = roadmap R3.) |
| C4 | Snapshot timing | **Keep exactly as implemented.** No change. |
| D1 | Layering multi-worker attribution | **(a) Each worker reports ONLY their own work.** Every worker owns their contribution; manager sees the combined total. |
| D2 | Alter/missing pay policy | **Confirmed.** Until a dedicated Alter/Missing module: only GOOD quantity is payable; alter/missing remain production analytics. |
| D3 | Rate correction actor | **Confirmed.** Super-Admin only; every correction fully audited. |
| D4 | Monthly pay basis | **Worker-level (`WorkerProfile.pay_basis`), never the stage.** A stage may host monthly + piece-rate workers simultaneously. Monthly workers still submit production entries for analytics; those entries MUST NEVER generate settlement lines. |
| D5 | F&F residual advance | **Explicit audited write-off entry.** Nothing disappears silently; every financial adjustment leaves a permanent audit trail. |
| D6 | Adda-start broadcast | **Dashboard broadcast only.** No push infrastructure. Keep it simple. |
| D7 | Worker's per-Adda view | **Dedicated "My Work" section on the Adda page — the worker's PRIMARY entry point.** |

## 28) Assumptions · risks · edge cases

**Assumptions:** single factory, single DB (multi-factory = site dimension later,
ADR-0010); INR only; Hindi/Hinglish labels acceptable; phones = common Android.

**Top risks:**
1. Money regression — mitigation: golden ₹225 byte-test + 700-test suite green per phase (non-negotiable gate).
2. Ripping working guards in the name of simplification (C2) — highest-risk/zero-gain; refused unless owner overrides.
3. Doc drift — mitigation: rule 12 docs-sync; this PDD updated same-session with any scope change.
4. Monthly-worker double-pay (salary + settlement) if D4 lands wrong — design excludes monthly contributions from settlement lines structurally.
5. P&L shortcuts violating ADR-0008 — refused until G5/G2.

**Edge cases already handled in code:** reversed recovery restores advance;
reversal never counts as new earning; grouped stale-rate can't pay; era-A/era-B
double-credit guards; reopen refused after settlement credit; downstream-consumer
reopen guard; verified > reported allowed (correction is management truth);
fully-alter/missing line (good=0) legal; recovery ≤ remaining (DB);
settlement item recovery within outstanding (DB).

**Edge cases to design in their phases:** F&F with un-reported open tasks (§20
step 1); worker deactivated with outstanding advance and zero payable; Adda
reopened after F&F of a participant (blocked by settlement armor — verify in roadmap-R7
tests); leftover consumed across Addas (G1); defect root-cause chain
(MissingPiece).

## 29) Implicit business rules register (was code-only; now explicit)

Ledger & settlement: ledger amounts always positive, direction = entry_type ·
exactly one source FK per non-reversal entry · recovery line has exactly one
parent (XOR, DB) · finalized settlement must carry settled_at (DB) · recovery ≤
outstanding (DB) · a contribution line settles AT MOST once (era guards +
settlement_line provenance) · reversal nets by category of the reversed row ·
settlement item amounts non-negative · advances positive · advance pool separate
from payable (grant never debits) · balances derived only.

Production truth: ≤1 active task per (stage_record, worker) (DB) · reported
(good/alter/missing) each ≥ 0 AND sum > 0 (DB) · reported immutable; corrections
→ verified_quantity only · expected_* frozen once, never re-derived · role frozen
at complete · un-assign = cancel, never delete · drafts excluded from business
truth · unreported tasks auto-cancel at stage complete (foundation "F3" behavior,
distinct from §31.1-F3 — decision §27-C3 RESOLVED to block-with-override;
auto-cancel remains ONLY until roadmap R3 ships) · stage
duration auto from timestamps, never asked.

Config & costing: unique (product, order) and (product, stage) per flow · rates
non-negative everywhere (DB) · grouped member never yields a pay rate (C-1,
structural) · processing_cost frozen once (cost_frozen_at) · rate correction
only until settlement, super-admin, audited · cost duality never additive
(ADR-0009) · pool grain monotonic; pool starts at cutting · allocation bound &
reconciliation BLOCK behind default-OFF flags · barcode payloads permanent ·
piece identity = (adda, seq) · size allocation ≤ 100% (DB) · roll cannot attach
twice to one stage (DB) · leftovers mandatory at layering complete.

Access: menu hidden ⇒ URL blocked (one rule, two enforcements) · stage access =
skill ∩ allowed AND active assignment · worker payroll self-only ·
foundation-purity: core/accounts import no domain app; tracking imports neither
production nor expense; expense never imports production at module level.

## 30) Extensibility strategy (adding a future stage — the recipe)

1. Stage library row (code, name, allowed skills, default cost method/rate).
2. Handler package under production (typed record model if needed, views,
   service hooks, pool_grain) — open-closed, no core edits.
3. Flow-editor row per product (order, rate, role-rates, payability, grain).
4. Worker report path via `worker_task_service` ONLY (C-TM).
5. Constraints + tests (incl. golden money test untouched).
6. Docs same session (rule 12).
7. **Stage-specific fields live on the TYPED record, never on `AddaStageRecord`**
   (the existing `draft_layer_length_meters` / `draft_duration_minutes` columns
   are a grandfathered layering-specific wart — do not repeat the pattern).
8. **Every new route ships with a `SidebarItemRule` OR a gated view mixin.**
   The middleware default-allows unmanaged URLs by design (defense-in-depth:
   views are the second gate) — a route with neither is silently open to all
   logged-in users. This is a hard checklist item, verified in review.
Stitching (5-worker example), packaging, ironing all fit this recipe with zero
engine changes. **Proven by:** barcode_generation was added exactly this way.

## 31) Final architecture validation (2026-07-04, pre-freeze hostile pass)

A last adversarial review as manufacturing-ERP product architect — implementation
deliberately ignored, then re-verified against code. Verdict at the end.

### 31.1 New findings (all folded into this document)

| # | Finding | Severity | Disposition |
|---|---|---|---|
| F1 | **Adda-code collision on product-code reuse.** `Adda.code = {product.code}-{counter:03d}` with a per-product counter. Rename product X→Y, later create a NEW product with code X → its counter restarts → `X-001` collides with the old Adda `X-001` → IntegrityError 500. | MED (latent) | New explicit rule: **`Product.code` is immutable once the product has any Adda** (enforce in product edit form/service; roadmap R1 item 4, tiny). Also protects permanent barcode payload prefixes (ADR-0010). |
| F2 | Layering-specific draft columns sit on generic `AddaStageRecord` (OCP wart). | LOW | Grandfathered; recipe rule §30-7 prevents recurrence. No migration churn now (YAGNI). |
| F3 | Middleware default-allows unmanaged URLs; safety currently rests on the audited view gates. A future ungated route = silent hole. | LOW now, compounds | Process rule §30-8 (route checklist). No code change. |
| F4 | Django admin: all expense money tables read-only ✅, WST/WSC not registered ✅ — but `Adda`/`WorkflowStage` are admin-editable, letting a super-admin hand-edit status/current_stage/rates around `flow_service`. | LOW (super-admin-only surface) | Accepted as the deliberate super-admin escape hatch; revisit to read-only if a real incident occurs. Snapshots make rate edits harmless to started work. |
| F5 | **Ledger unbounded growth.** Every balance is a live SUM over an append-only, never-pruned table. Fine for years at this factory's scale (indexed); at multi-year × multi-factory scale dashboards will slow. | Future | Named seam: **yearly ledger close** (opening-balance snapshot row per worker + period filter). Classic accounting close; additive, no schema redesign. Do NOT build now. |
| F6 | `verified_quantity` changes carry no audit trail (who set what, previous value) — known since Phase 10. | LOW | Small add — roadmap R6 (history_service event on set_verified_quantity). Money already safe (frozen items + ledger provenance). |
| F7 | **Subcontracting / job-work** (common in garment industry) is the only surveyed future feature with friction: `WorkerLedgerEntry.worker` is a hard User FK. | Future | Zero-redesign pattern reserved: external party = `User` row flagged external, no login credentials. Earnings/settlement/advances work unchanged. Documented seam, not built. |
| F8 | Tiered/slab piece rates (rate varies with volume) would extend, not break, the payment engine — rate resolution is already centralized (`resolved_payable_rate` → `effective_pay_rate` chokepoint). | Future | Note only; one-service change when needed. |

### 31.2 Explicit-rule additions (were implicit; now part of §29 by reference)

- Multiple settlements per Adda are LEGAL (era guards make double-crediting a
  line impossible); settlement is per completed payable lines, not one-shot.
- Worker deactivation (`is_active=False`) blocks LOGIN, never money flows —
  a deactivated worker can still be settled and paid (F&F depends on this).
- The same worker MAY hold tasks on multiple stages of one Adda (unique
  constraint is per stage_record, by design).
- Draft contributions are operational scratch — excluded from business truth
  and from management money views until task complete.
- `entry_date` is the financial day (owner may backdate deliberately);
  `created_at` is the immutable system timestamp. Reports filter `entry_date`.
- Rate `0` ≠ rate `NULL`: 0 = priced-at-zero (grouped member / unpaid stage);
  NULL = honestly unpriced (legacy) — never coerce one into the other.
- Advances may be granted to any active user (owner discretion), not only
  role=worker.

### 31.3 Validation results (the owner's 14 challenges)

| Challenge | Result |
|---|---|
| Long-term ERP view, assumptions re-challenged | PASS — the two-truths + snapshot + single-writer core is exactly what a piece-rate factory needs; no structural rethink found. |
| 2–3 year scalability | PASS with named seams: F5 ledger close; history tables same pattern (colder). Postgres + current indexes carry this factory for years. |
| Implicit rules → explicit | Done — §31.2 + F1 rule added to the §29 register scope. |
| Over-engineering | S4 pool machinery is ahead of its consumer (stitching) — justified, tested, flags OFF; keep. `inventory` app is a misnomer (hosts dashboards/RBAC, no inventory) — naming debt, accepted, renaming = churn for zero behavior. |
| Under-engineering | MONTHLY basis (D4), F&F (§20), expenses (§21) — already scoped as build items. Nothing else found. |
| YAGNI / DRY / OCP / SoC | PASS — one OCP wart (F2, contained), `cost_rate` double-duty is a documented, locked trade (ADR-0009), app boundaries verified acyclic. |
| Module responsibility | PASS — settlement in expense (money boundary), read/write services split, tracking as string-FK event log all correct. |
| Future stage w/o engine change | PASS — recipe §30, precedent barcode_generation, R1 locked. |
| Future payment method w/o redesign | PASS — enum + handler quantity accessor + centralized rate resolution (F8). MONTHLY lands worker-level (D4), untouched engine. |
| Future material costing w/o Adda redesign | PASS — G1 attaches consumption rows + snapshots to existing stage events; ADR-0009 reserves the material column; `is_consumed` seam waiting. |
| Corruption-impossible via normal flows | PASS — single-writer + CI gates, DB constraints, PROTECT FKs, append-only + reversal, frozen snapshots, era guards, reopen armor, admin read-only on money (F4 caveat = super-admin escape hatch, accepted). |
| Workers never reach manager functions | PASS — 5 gate layers verified; residual risk is FUTURE ungated routes → §30-8 checklist closes it as process. |
| Hidden edge cases | F1 found (adda-code collision). Others re-verified handled: cancelled-task pay orphan (Phase-10 fix), reversed-recovery restore, stale grouped rate, reopen-after-credit. |
| Machines · QC · subcontracting · multi-factory · barcode · procurement · POs | None forces redesign. QC = a stage. Machines/procurement/PO = additive apps. Multi-factory = ADR-0010 site dimension. Subcontracting = F7 pattern. Barcode = TM-2 locked path. |

### 31.4 Document organization verdict

Keep the PDD as ONE file — it is the product front door and cross-section churn
is low. Split only when a section starts changing independently at high
frequency (likely candidates later: Layering/Pattern per-stage specs once every
stage has one — then a `docs/stages/` folder with the PDD holding the index).
Not now.

### 31.5 Recommendation

**The architecture is mature, internally consistent, scalable for this
business's horizon, auditable by construction, and aligned with the owner's
vision. RECOMMEND FREEZE as PDD v1.0** — conditional on exactly two things:
1. Owner answers §27 (C1–C4, D1–D7) — they gate business behavior, not safety.
2. F1 rule (product-code immutability once Addas exist) enters the first
   implementation phase.

---

### Approval

- [x] Final hostile architecture validation (§31, 2026-07-04) — verdict:
      RECOMMEND FREEZE.
- [x] Owner answered §27 (C1–C4, D1–D7) — 2026-07-04, recorded above.
- [x] Owner added principle P10 (business correctness beats convenience).
- [x] Freeze condition 2 of §31.5 satisfied: the F1 product-code-immutability
      rule is scheduled in roadmap R1 (item 4).
- [x] **FROZEN as PDD v1.0 — 2026-07-04.** Change control: new ADR or approved
      PDD revision only. Roadmap: [IMPLEMENTATION_ROADMAP_PDD_V1.md](IMPLEMENTATION_ROADMAP_PDD_V1.md).
      (Post-freeze editorial pass same session: phase labels unified to
      R-numbering, dangling references fixed — no decision or rule changed.)

### Verification sources
Cross-checked against code 2026-07-04: `production/models/{core,adda,layering,worker_task}.py`,
`expense/models.py`, `production/services/{worker_task,stage_rate,cost,access,adda}_service.py`,
`expense/services/{adda_settlement,payroll,settlement_resolver,ledger}_service.py`,
URL maps of all 7 routed apps, constraint sweep (DB rule register §29).
Confidence: High. Conflicts with ADRs/ARCHITECTURE_V2: none — §27 items are the
only deltas, held as decisions, not silent changes.
