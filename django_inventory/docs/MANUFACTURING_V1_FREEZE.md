---
id: docs-manufacturing-v1-freeze
type: truth-lock
status: active
owner: frozen
scope: project
anchors: —
verified: 2026-07-18
---

# MANUFACTURING V1 — FREEZE PACKAGE (2026-07-06)

> **Status: 🔒 MANUFACTURING V1 FROZEN (owner-declared 2026-07-06).**
> From this document forward the manufacturing engine changes ONLY through an
> owner-approved ADR or explicit owner decision. Configuration (products, flows,
> stages, rates, sizes, patterns, machines, skills, users) remains freely
> editable — that is the design, not an exception.
> Change control: new ADR in [docs/adr/](adr/) or an owner ruling recorded in
> [FACTORY_OPERATIONS_MASTER.md](FACTORY_OPERATIONS_MASTER.md) §5/§7.
> Certification + verification annex: §11 of this document.

---

## 1. Final architecture summary

One production engine, four independent money-safe concerns, config-first:

```
CONFIG (freely editable)          ENGINE (frozen)                    MONEY (frozen, settlement-only)
Product · ProductSize             Adda (batch) → AddaStageRecord     AddaSettlement (draft→finalized,
Stage library (+hinglish hints)     per WorkflowStage, append-only     reopen/void armored)
WorkflowStage (order · rate ·     WorkerStageTask → WorkerStage-     StageWorkAssignment = the earning
  cost_method · billed_at ·         Contribution (good/alter/          line, written AT FINALIZE on
  credits_workers · grain)          missing/damaged; immutable         settlement_quantity
StageCategory · MachineType ·       observations; machine_code       WorkerLedgerEntry (append-only,
  Machine · Skills                  stamp; first_report_at)            ONE writer: ledger_service)
SidebarItemRule (menu+URL gate)   Pool: StagePoolSnapshot +          Advances = separate loan pool,
AddaStageRoleRate (rate frozen      WorkerStageAllocation              owner-controlled recovery
  per stage-record at start)        (dimension-scoped, no money)     FactoryExpense (ADR-0011: monthly
                                  Verification: confirms/REDUCES,      salary NEVER per-Adda allocated)
                                    never increases; void+resubmit
                                    = the only upward path
```

- **Four concerns, orthogonal by construction:** allocation (production capacity)
  ⊥ cost_method (standard costing) ⊥ earning (worker pay) ⊥ settlement (the only
  money boundary). Proven by the S4/OP-1 test walls and three settled journeys.
- **Truth flow:** APSCPB (colour×size cut actuals) = the piece truth born at
  Cutting → pools materialize per stage as Σ verified-else-good (J-1) →
  Packing's honest count → settlement pays verified-else-good per contribution.
- **Costing duality (ADR-0009):** standard cost (frozen per-stage
  processing_cost) and actual settled labor are two views of the same work —
  displayed side by side, never added; honest-NULL everywhere (unknown ≠ ₹0).
- **RBAC:** three-concept model — Role (super_admin/manager/worker/
  listing_team/accountant) for pages, SKILL for stage access
  (`access_service.user_can_access_stage`), manager ASSIGNMENT as the only
  roster source (PDD amendment 4); ONE live visibility predicate
  (access ∩ assignment). Sidebar + URL gated together by `SidebarItemRule`.
- **Single-writer services** own every multi-row write; views parse→gate→delegate.
- **Registry-driven stages:** bespoke handlers (layering, cutting_pattern,
  cutting, barcode_generation) + ONE generic handler for every operation stage;
  a new operation is a Stage row + flow row + rate — **config, not code**.

## 2. Major modules

| Module | Home | Role |
|---|---|---|
| Production engine | `config/production/` | Adda lifecycle, stages, flows, pools, allocations, worker tasks/contributions, rates, costing, A360 |
| Expense / money | `config/expense/` | Adda settlement (the ONLY money boundary), payroll, ledger, advances, FnF, factory expenses |
| Machines | `config/machines/` | machine registry + assignment windows (R10; FKs INTO production) |
| Raw materials | `config/raw_materials/` | cloth types/colors/rolls (width, weight, honest-NULL cost), storage |
| Tracking | `config/tracking/` | barcodes/bundles, Adda/roll history (append-only audit) |
| Accounts | `config/accounts/` | auth (Argon2, rate-limited), Role/Skill RBAC, permission_service |
| Inventory | `config/inventory/` | dashboards, sidebar access control, middleware URL gate |
| Core | `config/core/` | shared abstract models (TimeStampedModel, ActiveManager) — no tables |
| Storefront | `config/storefront/` | listing/commerce surface (out of manufacturing scope) |

## 3. Implemented capabilities (proven end-to-end)

- **Three real product flows, cut→settled with exact money identities:**
  T-SHIRT 16 ops (₹801.00, 2col×2size, verified 18→17 flowed to pool AND pay) ·
  LOWER 13 ops (₹344.25, 8 workers) · 3-PATTI 12 ops (₹633.00 = A360 expected =
  draft = Σ21 SWA = Σ21 ledger = Σ items = hand-calc).
- **OP-1 multi-worker dimension-scoped operations:** manager Split-the-work
  (pair-select cut lots), pool draw-down with always-on over-allocation refusal,
  blind worker reporting (no quantities visible, choice-membership enforced
  server-side), per-dim prefilled report rows, 4-way G/A/M/D observations.
- **Verification & correction discipline:** manager verify confirms or REDUCES
  (H-1 ceilings), never increases; audited `void_submitted_report` + fresh task
  = the only upward path; report review page + audit events.
- **Machines:** types/registry/assignment windows; `machine_code` stamped on
  contributions; ⚙ chip on worker phones; machines move between Addas.
- **Settlement money armor:** draft gate (all payable stages complete),
  finalize writes SWA + ledger atomically under advisory locks, frozen
  per-worker items, reopen/void guards, reconciliation evidence (S1.1/S5),
  advances recovery, FnF; golden ₹225 byte-identical test wall.
- **Worker experience @390:** 3-tap find-work→report loop, hinglish stage hints
  (`Stage.description` rendered on report hero), My Earnings
  Expected→Earned→Paid ladder, sidebar locked to Main.
- **Management experience:** operations digest (stalled/pending/payable KPIs),
  zero-noise stage chips, A360 per-Adda hub (100% chips, expected vs settled),
  costing page (duality + honest-NULL banners), settlements queue
  (ready vs blocked-by), pending-reports oldest-first, stalled drill-downs.
- **Foundation levers (built, default OFF):** `ENFORCE_ALLOCATION_BOUND`,
  `ENFORCE_SETTLEMENT_RECONCILIATION` (+ tolerance, super-admin audited
  override), `LEDGER_CREDIT_AT_ALLOCATION` era rollback lever.
- **Quality gates:** 885-test suite (money identities, hostile-review walls,
  RBAC leaks, OP-1 hardening, pre-phase-3 A-D, perf pins), import-linter
  contract 1, FoundationPurityTests, conscious query-count pins.

## 4. Owner decisions (binding register)

- **PDD v1.0 FROZEN** (2026-07-04) + amendments register at its top; operational
  foundation frozen 2026-07-05 (gate 827).
- **FACTORY_OPERATIONS_MASTER §5 — sixteen Phase-2 rulings** (checker pay
  monthly-recommended & Good=inspected FORBIDDEN · per-dozen ÷12 · dispatch =
  a stage · alter informal until R11 (R11 = HARD prerequisite of the permanent
  enforcement flip) · printing only-when-real · helpers never rate-split ·
  final-check placement · leg binding = Flatlock self-fabric patti ·
  Overlock→Panel Join rename · packing blank-row honest count · payment cadence
  levers · rate governance · floor-language labels …).
- **Pre-Phase-3 rulings (A–D built):** damaged 4th observation · machine_code
  stamp · first_report_at · audited void-submitted-report. LOCKED business
  rule: **verification confirms/reduces, NEVER increases.**
- **§7 future register rulings:** wash-regrade, print-design split, job-work
  cost/custody, TM-2 bundles, attendance/min-wage, seconds — documented, NOT
  built; **one Adda = one product = one design** standing rule.
- **Freeze conditions (owner-confirmed):** one rate per op per style · no new
  checklist ops · one machine type per op.
- **3-Patti: NO Iron stage** — Checking→Packing→Dispatch is the production
  flow; future ironing = optional configured op, never engine change.
- **J-1 pool truth** = Σ verified-else-good; flags stay OFF until production
  hardening (rollout policy); NO commit until owner checkpoint (this freeze).
- **ADR locks:** 0007 allocation-era cutover · 0009 cost truth · 0010
  growth/identity · 0011 monthly salary = factory-level, never per-Adda.
- **Standing rules:** mobile-first functional requirement · docs-sync same
  session · money-write STOP rule · manager-assignment-only rosters ·
  settlement-only money · append-only work-history · design system frozen ·
  FancySelect-only selects · one-question pages · compose-from-canon.

## 5. Deferred capabilities (registered, NOT built)

| Item | Register |
|---|---|
| R11 rework loop + `recovered_alter` top-up (prerequisite of enforcement-flag flip) | roadmap / §5.7 |
| Washing + post-wash re-grade (ADR-0010-D4 case pattern) | ops-master §7.1 |
| Print-design lot split (one-Adda-per-design dodge stands) | §7 |
| Job-work: vendor invoice cost truth (JobWorkInvoice + ADR-0009 term-5) + custody/challan (GST ITC-04) | §7 |
| TM-2 barcode/bundle scan-driven reporting (C-TM chokepoint contract) | §7 / §11 |
| Attendance + statutory min-wage top-up layer | §7.5 |
| Seconds/B-grade classification | §7.6 |
| S6 `reported_quantity` retirement (irreversible, post-soak) | master plan V2 |
| M-3 machine-linkage stamp on WST + worker timestamps beyond first_report_at | owner-deferred |
| Rate matrix (op × product, read-only) · §5.2 bulk-split UI · skill-aware machine picker | §5.15 / §5.2 / audits |
| Engineering sweep D-1..D-11 (acyclicity, cross-app mixin family, settlement-queue batching, handler snapshot precompute, hero/panel CSS extraction, …) | ENGINEERING_EXCELLENCE_SWEEP §3 |
| C-4 strict-C3 visibility | owner manual testing |

## 6. Future extension points (bolt-on seams, no redesign needed)

- **Generic stage handler + registry fallback** → any new operation = config.
- **`recovered_alter` pool accessor** (stubbed, formula-stable) → R11/washing.
- **BarcodeBatch (adda, seq) ranges** → future piece identity (ADR-0010 D3).
- **`report_contributions` chokepoint (C-TM)** → scan-driven capture converges here.
- **Quality/ops analytics**: G/A/M/D × dim × op × worker × machine_code +
  first_report_at/completed_at windows + MachineAssignment — already captured,
  read-only surfaces can be built any time.
- **ADR-0010 identity locks** → multi-factory becomes a filter, not a migration.
- **Pattern Design stage seams** → AI Pattern Intelligence (see §9 and
  [AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md](AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md);
  enterprise-era KICKOFF archived, superseded by Vision V2 2026-07-07).

## 7. Frozen contracts (violation = STOP + owner escalation)

1. **Money exists only at settlement.** No new money-write path outside the
   approved single-writer services (`ledger_service` for WorkerLedgerEntry;
   settlement services for SWA/items; census = R5 hostile review Part 2).
2. **Append-only work-that-happened:** contributions, ledger, history tables,
   settlement items — corrections via reversal/void/supersede, never edit.
3. **Verification confirms or reduces — never increases.** Upward = audited
   void + resubmit only.
4. **Frozen snapshots:** `AddaStageRoleRate` at stage start; `expected_rate`/
   `earning_amount_snapshot` on earning lines; processing_cost at stage
   complete; rate corrections only via audited `rerate_stage_role` until
   settlement, settled = locked.
5. **Manager assignment = the only roster source; visibility = access ∩
   assignment** (one predicate, everywhere).
6. **FK direction:** satellite apps (machines, future patterns_ai) point INTO
   production; production never imports them.
7. **Sidebar + URL gated together** (SidebarItemRule + middleware).
8. **Grain monotonicity** (pools never re-fine downstream) + write-once pool
   window (verify-before-advance).
9. **Enforcement flags default OFF** until R11 + owner flip (runbook).
10. **Design system frozen**: tokens/owners only; `{# #}` single-line only;
    mobile-first @390 is functional, not polish.

## 8. Configuration-only guarantees (the 100-product verdict)

Adding a product line requires ZERO engine code — proven three times, the last
(LOWER) from nothing to settled in one day and 3-PATTI on the REAL flow:
1. Product + sizes (UI) · 2. patterns + assignments (UI) · 3. flow rows from
the stage library, ordered, with grain/rates/payability (flow editor) ·
4. skills/machines if a genuinely new operation type appears (masters UI) ·
5. rate cells. Stages rename/reorder-safe (code immutable, name free, FK-based),
categories = presentation, machines reusable, historical money frozen against
all of it (independence audit 8/9 PASS, M-3 deferred).

## 9. Known future projects (priority order)

1. **AI Pattern Intelligence** — THE next project, largest in the ERP.
   Owner ruling 2026-07-06: the next session is a KICKOFF REVIEW ONLY
   (fresh-eyes, first-principles re-challenge of the blueprint — §17 of the
   kickoff contract); implementation begins only after that review, starting P0.
   Contract + design of record (enterprise-era, archived; live successor):
   [AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md](AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md).
2. R11 rework loop (unlocks enforcement flags).
3. Real rate card entry + re-validation (owner data; precedes production use).
4. Deploy/soak runbook execution (staging → flags ON per runbook).
5. §7 register modules as business arrives (washing, printing, job-work,
   bundles/TM-2, attendance).

## 10. Completion checklist — Manufacturing V1 is complete

- [x] Three real flows configured from the shared stage library (16/13/12 ops)
- [x] Three end-to-end business journeys cut→…→dispatch→settled
- [x] Money identity exact on all three (A360 = draft = SWA = ledger = items = hand-calc)
- [x] Golden ₹225 byte-identical; 885-test suite green (exclusive serial run)
- [x] 4-role audits (owner/manager/checker/low-literacy worker) every phase; mobile @390 first-class
- [x] Manufacturing Excellence Audit — 8 UX fixes shipped, verdict READY
- [x] Engineering Excellence Sweep — hygiene floor (pyflakes 0), single-home
      consolidations, 6 ORM fixes, 3 hot-path indexes, verdict READY
- [x] Independence audit (rename/reorder/rate/activate safety) 8/9 PASS, 1 owner-deferred
- [x] Operation Independence + Architecture Destruction audits survived (core clean; product-scoped gaps registered §7)
- [x] All owner decisions recorded (§4); all deferrals registered (§5)
- [x] Docs synchronized + indexed; drift fixes applied (RBAC paths, GLOSSARY era-B, enum values, bound formula)
- [x] Enforcement flags OFF per rollout policy; levers documented in runbook
- [ ] Real production rate card — **POSTPONED by owner ruling 2026-07-06 to pre-production-rollout** (DEV rates acceptable for local development/testing; enter + re-validate the three journeys before rollout)
- [ ] Checkpoint commit (owner declares with/after this freeze)

## 11. Certification & verification annex

A 5-lens read-only verification (ops-master vs live config+DB · ADR/R10/OP1 vs
code · index/navigation · AI-PI blueprint cross-refs · frozen-contract census)
ran against this package on 2026-07-06 (5/5 lenses returned; ~200 tool reads).

**Code verdict — the certification core:**
- **All frozen contracts HOLD in code**: money single-writers verified by grep
  census (WorkerLedgerEntry created only in ledger_service; SWA only in the
  settlement/allocation services); enforcement flags default OFF;
  `LEDGER_CREDIT_AT_ALLOCATION=False`; verify-reduce guards in place; sidebar
  menu+URL co-gating live; FK directions correct.
- **All three settled money identities reproduced from the DATABASE**:
  ADST-0004 ₹344.25 = Σ16 SWA = Σ16 ledger; ADST-0005 ₹801.00 = Σ44 = Σ44;
  ADST-0006 ₹633.00 = Σ21 = Σ21 (8 items). Flow maps match DB rows exactly
  (16/13/12 ops, Panel Join rename, sleeve_join in T-SHIRT only, no Iron in
  3-Patti). Every OP-1 hardening and pre-Phase-3 claim verified at its cited
  file:line.
- **Zero genuine architecture contradictions found in code.** One nuance
  codified rather than discovered-broken: production holds exactly three
  sanctioned FUNCTION-LEVEL reads of machines (machine_code stamp + ⚙ chip);
  docs that said "production never imports machines" were corrected to the real
  invariant (no model/module-level imports) and the three reads are now
  codified as `ignore_imports` in `config/.importlinter`, with `machines` added
  to root_packages + the top layer (closing R10's claimed-but-unshipped lint
  entry).

**Documentation desyncs found and FIXED in this package (~25):** ops-master
status banner + §3 map (Iron removed; reconfiguration past-tense) + §1
today-values + §8 BLOCKED→RESOLVED + §9 payable-stage count (10, 8 with
piece-rate lines) + §12 leftover iron-confirm; R10 plan status → IMPLEMENTED;
ADR-0005 + its index row → settlement BUILT; R10 architecture L1 diagram note
(MachineType lives in production); ALLOCATION_WORKFLOW_AUDIT M-3 → CLOSED
(WSC.machine_code, prod 0048); OP-1 route-name typo; CLAUDE.md → 8 domain apps
+ freeze pointer; DOCUMENTATION_INDEX → freeze row, kickoff entry point,
ops-master v3 row, 9 app guides, allocation-audit link; START_HERE +
PROJECT_ATLAS roadmap repoints; PROJECT_KNOWLEDGE_MAP phase-history row;
docs/apps/README machines row; blueprint width_inch citation; 01_RESEARCH
"reads/writes" → proposals-only supersession note.

**Remaining known-and-accepted (not desync):** ops-master §11 AI-row wording
awaits owner decision D8 (kickoff agenda); import-linter contract 2 stays
report-only with its registered production→expense worklist (arch-remediation
backlog, D-1).

### CERTIFICATION

Architectural consistency review complete. No genuine architecture
contradiction exists between the frozen contracts and the code. The three
settled journeys' money reproduces from the database to the paisa. Docs,
navigation, and code now tell one story.

**Manufacturing V1 is hereby CERTIFIED FROZEN (2026-07-06).**
Change control from this moment: owner-approved ADR or recorded owner decision
only. Next project: AI Pattern Intelligence
([AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md](AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md);
enterprise-era KICKOFF archived).

---

## ADDENDUM — 2026-07-11: Pre-production architecture challenges, owner-ratified

Three owner-ordered first-principles challenges ran against the frozen
architecture using LIVE simulated factory worlds (NKB-001 multi-cycle Nickar ·
NKS-001 3-fabric shortfall · SHT-001 7-component shared-fabric Shirt) — all
review-only, zero code:

1. **Cutting Cycles** ([challenge](CUTTING_CYCLES_ARCHITECTURE_CHALLENGE.md)) —
   verdict A: `CuttingStream(adda, fabric_group, sequence)` — **sequence IS the
   production cycle**; planned multi-lay = the same declared-lane mechanism,
   reason strings are data.
2. **Bundle Assembly** ([review](BUNDLE_ASSEMBLY_ARCHITECTURE_REVIEW.md)) —
   verdict A: Cutting = the written truth of PIECES; complete garments =
   DERIVED (min over mandatory components per size); Bundle = append-only
   physical staging event, never a second count truth.
3. **Production Component** ([review](PRODUCTION_COMPONENT_ARCHITECTURE_REVIEW.md)) —
   verdict A: the component already exists = **`ProductPattern`**;
   `fabric_group` is its lay-routing attribute (shared-fabric components nest
   in ONE marker — the lay is owned by the fabric on the table). Owner: table
   name stays; docs/glossary/UI labels say *Production Component* (GLOSSARY
   updated).

**Ratified hierarchy (frozen):** Product → ProductPattern (Production
Component) → PatternPiece (+`fabric_group` attribute) → CuttingStream
(group, sequence = cycle) → Layering → Pattern Design → Cutting → JOIN →
Bundle (staging) → Barcode (piece identity) → Operations.

**Implementation-debt ledger from the challenges (owner-acknowledged; fixes
follow the normal FDD order, severity-first):**
GAP 2 — lane-blind color/pattern-record validation blocks cross-fabric
cutting completion · GAP 1 — ops pool ≠ Σ-over-streams, refined to
garment-equivalent min per SIZE for assembly ops · GAP 5 — bundle services
never moved post-join/adda-level (schema already shipped; incl. the
(bundle,pattern,color) item-uniqueness detail + the component readiness/derive
panel) · GAP 3 — bare multi-lane console URL 500 · GAP 4 + UI laws — worker
lane-scoping, greyed cancelled lanes, the §10 Add-lane form.
