---
id: docs-rm-expense-integration-log
type: receipt
status: active
owner: append-only
scope: campaign
anchors: —
verified: 2026-07-18
---

# Raw Material → Expense Cost Integration — Build Log (Campaign Phase 17)

> Evidence doc of record for Phase 17 (created at the owner-ordered RMX-0 Architecture &
> Product Review, 2026-07-18; contract =
> [PHASE_17_RAW_MATERIAL_EXPENSE_COST_INTEGRATION.md](campaign_contracts/PHASE_17_RAW_MATERIAL_EXPENSE_COST_INTEGRATION.md)).
> Contract = procedure; THIS log = what is chartered, censused, gated, built, proven.
> Governing truth-locks: **ADR-0009 (read in full this session; all five Decisions
> load-bearing)** · ADR-0011 · the FINANCIAL_ROLES 4-layer roll wall · roll truth = THE
> material-cost record.

## RMX-0 — Phase 17 Architecture & Product Review — presented 2026-07-18 ⏸ AWAITING OWNER CHARTER (RMX-D1/D2/D9 + ratification). ZERO code/migrations/models/services/tests written.

> **[2026-07-18 FFD-E banner — heading preserved as written]:** the awaited charter WAS
> granted same day ("PHASE 17 CHARTER APPROVAL") — rulings of record in contract
> **Appendix A (RMX-D1..D9)** + PDD register entry 8; phase CLOSED at §RMX-F.

### 1. Executive Summary

- **Business objective:** make material money VISIBLE where the owner manages money —
  what materials cost this period, and what each Adda REALLY cost (cloth + labor) — while
  every rupee stays recorded exactly once on the rolls.
- **Problem statement:** the ERP knows every roll's purchase price, every consumption,
  every leftover — but the owner cannot see "material spend this month" anywhere, and the
  Manufacturing Costing page shows labor duality without the material component, so no
  surface answers "what did production really cost?" factory-wide. (Per-Adda full cost
  EXISTS on A360 — see §2's headline finding.)
- **Success criteria:** the contract's §3 verbatim — charter recorded (PDD entry 8
  expected) · census-based build · **one-rupee-once reconciliation across all displaying
  surfaces** · ADR-0009 compliance per surface (sum-guard, formula fidelity, honest-NULL
  end-to-end) · ADR-0011 untouched · D2 permission ruling implemented + wall re-proven ·
  read-only purity · money byte-identical · battery/sync/docs green.
- **Explicit non-goals:** overhead (reserved, era-stamped, ADR process) · factory-expense
  per-Adda allocation (ADR-0011 wall) · re-pricing anything · variance reporting ·
  non-cloth materials (RM-V2 vision territory — post-P22) · supplier/procurement
  workflows · blocking intake on price · touching settlement/ledger/pay · resolving the
  PHASE_03 accountant-reachability question.

### 2. Existing Architecture Review (evidence, file:line)

**HEADLINE FINDING — Costing-2 per-Adda ALREADY EXISTS (major reuse):**
`production/services/cost_service.py:239 material_cost_for_adda(adda)` (M13,
2026-07-12) is a pure, stored-nowhere derive: Σ consumed roll value (verified kg ×
roll ₹/kg) − remnant value + leftovers-reused-in (valued at SOURCE roll price;
**across-Adda exactly-once BY CONSTRUCTION** — the source Adda's figure is already net
of the remnant it gave away; the V1.1 item-2 locked C-1 rule) with honest-NULL
(`unpriced_rolls` counted, never ₹0). And `production/views/a360.py:240` already
assembles the FIXED Decision-2 formula: `full_cost = material_net + settled_total +
nonpayable_priced` (+ ₹/garment), rendered with the incomplete-material flag
(`_a360.html:60` "N unpriced roll(s) — incomplete").

| Existing asset | Where | Reuse verdict |
|---|---|---|
| Material truth | `ClothRoll.cost_per_kg` (purchase fact, honest-NULL, history-audited) + `supplier`, behind the certified 4-layer FINANCIAL_ROLES wall | THE truth; never copied |
| Per-Adda material derive | `cost_service.material_cost_for_adda` | **REUSE as-is** — the aggregation nucleus |
| Decision-2 assembly | `a360.py:232-268` (inline) | **EXTRACT-and-share candidate** (one assembly, two consumers — see §5) |
| Decision-3 labor source | `costing_views.py:75 earn_map` (Σ non-voided SWA snapshots) + a360's `swa_by_sr` | REUSE; never re-derive |
| Honest-NULL banners | `costing.html:53-57` ("material costing is incomplete…") + per-row unpriced notes + A360 flag | REUSE the exact wording/pattern |
| Costing page today | `ProductionCostingView`: std/payable/non-payable processing + earnings + variance + unpriced maps — **NO material ₹, NO full-cost line** | the Model-B completion gap |
| Leftover law | `roll_service.consume_leftover` (sole writer) + source-price valuation | untouched; already priced into the derive |
| Period reads precedent | `expense_service.monthly_totals` + `_parse_month` (P16) | pattern reuse for period views |
| Stock counts (BOD G-1/G-2) | `roll_service.stock_status_counts/stock_by_location` | pattern precedent (owner-gated INERT additions in the owning app) |
| Expense-side surfaces | factory-expense list + P16 recurring pages | navigation home for a Material-Spend view (window pattern) |
| BOD | ladder + registry (P15) | handoff path for any material widget |

**Census finding for the owner (contract §16.10 class, surfaced BEFORE design):** the
contract's RMX-D2 DEFAULT assumes aggregated material figures inherit the
FINANCIAL_ROLES wall (managers excluded). **Observed reality: A360 already shows
`material ₹net` + full cost to MANAGEMENT** (`adda_views.py:282 if is_management` —
workers leak-tested to zero bytes), shipped and certified at M13. The precedent
"aggregates are management-visible; per-roll price/supplier stays FINANCIAL_ROLES-only"
is LIVE. RMX-D2 must be ruled with this fact on the table (either bless the precedent
as the policy, or rule stricter and A360's cost card becomes a conscious re-gate).

### 3. Product Design (workflow · actors · permissions · lifecycle)

- **Workflow (read-only):** intake records price (unchanged) → production consumes
  rolls/leftovers (unchanged) → **NEW WINDOWS:** (i) Manufacturing Costing page gains the
  material + full-cost columns (Model B completion); (ii) an expense-side **Material
  Spend** view answers period questions (basis-labelled; RMX-D9); (iii) optional BOD
  tiles later via the ladder.
- **Actors:** owner/SA (everything) · management (costing + the aggregate views per the
  D2 ruling) · accountant (unresolved reachability — NOT depended on) · workers (nothing;
  leak-tested).
- **Ownership:** raw_materials owns material aggregation reads · production owns
  full-cost assembly (beside the existing costing code) · expense owns the report VIEW
  (window over the owning services — the BOD discipline).
- **Lifecycle/state:** none — no new stateful objects in the recommended models (A+B are
  stateless reads; figures derive at request time, as-of-now, like every costing surface).

### 4. Data Model Review

- Can existing models hold it? **YES — entirely.** Every input exists: rolls (price,
  weights, purchased_date), LayeringRollEntry (consumption + verified kg),
  RemainingClothOfClothRoll (remnants/leftovers + consumed_in_adda), SWA snapshots
  (labor), AddaStageRecord.processing_cost (non-payable component).
- Can the feature be additive without tables? **YES** for Models A+B: pure read
  functions. **RECOMMENDATION: ZERO new models, ZERO migrations** (first campaign phase
  with none since P11).
- Model C (materialized period rows) — **recommend AGAINST for this phase:** its only
  yields are query speed (volumes don't demand it) and point-in-time snapshots (no
  chartered need); its costs are U14 gates + a census addendum + the standing
  double-count risk the contract calls "most dangerous", and it would harden cloth-shaped
  rows RIGHT where the RM-V2 vision wants generality (the recorded RMX compat
  observation: **prefer read-path over materialization**). If the owner wants monthly
  archival later, Model C can be chartered as its own dated amendment with the full
  MEE-B treatment.

### 5. Service Architecture (reuse-first; every addition ladder-gated in its OWNING app)

| Proposed addition | App/home | Kind |
|---|---|---|
| `material_purchases_in_period(year, month)` — Σ(weight × ₹/kg) over rolls by intake date + unpriced-roll count (honest-NULL) | raw_materials `roll_service` (beside G-1/G-2) | NEW read (gated) |
| `material_consumption_in_period(year, month)` — Σ consumption events valued per Decision-5 (layering entries + leftover consumptions in period) + unpriced count | raw_materials `roll_service` | NEW read (gated) |
| `full_cost_for_adda(adda)` — the Decision-2 assembly EXTRACTED from a360.py:232-268: material (via `material_cost_for_adda`) + Decision-3 SWA labor + non-payable priced processing; returns components + flags | production `cost_service` (beside `material_cost_for_adda`) | **G-4-style INERT extraction** — one assembly, consumers: A360 (switched, byte-behavior identical) + the costing page (new column) |
| Material-Spend view | expense `views.py` (or raw_materials — RMX-B decides with the owner charter; recommendation: expense-side navigation, reading the raw_materials functions — the window pattern) | thin view |
- **Write paths: NONE.** Transaction boundaries: N/A (reads). Rollback: N/A. Idempotency:
  N/A (derives). **Audit:** nothing new to audit — no state changes; the figures are
  reconstructable by any auditor from raw tables (the material derive's own docstring
  discipline).
- Duplicate-logic kill-list: no second material valuation (everything routes through
  `material_cost_for_adda` / the same Decision-5 expressions) · no second labor source
  (earn_map/SWA sums reused) · no second month parser (`_parse_month`) · no second
  honest-NULL wording (reuse costing.html's certified sentence).

### 6. Money Architecture Review — READ-ONLY, PROVEN WHY

Phase 17 (Models A+B) **writes no money and creates no writer**: every function above is
a SELECT-derive; no FactoryExpense/ledger/settlement/SWA/roll row is created, updated, or
deleted; the Money-Write census needs **no addendum** (to be re-proven by BOD-style
purity pins + grep at RMX-C). ADR impact: ADR-0009 is IMPLEMENTED (Decisions 1/2/3/5
each get per-surface evidence), not amended; ADR-0011 untouched (material figures and
FactoryExpense totals never blend — any side-by-side view labels components; the P16
engine's rows stay factory-level). Ledger impact: zero (byte-checks at every wave).
Historical integrity: nothing stored ⇒ nothing to corrupt; append-only guarantees
untouched. Reporting impact: purely additive windows. **If the owner charters Model C,
this section is void and RMX-B re-presents with the full MEE-B gate stack (U14 + census
addendum + hostile review) — the review recommends not doing so.**

### 7. UI Architecture

- **Screens:** (i) Manufacturing Costing page — +Material and +Full-cost columns +
  grand-total line + the existing incomplete-material banner logic extended (compose, no
  redesign); (ii) **Material Spend** page — month-nav (the P16 canon: hero strip ·
  month-nav · totals tiles · data-label table), sections per chartered basis
  ("Purchases in {month}" / "Consumption in {month}" — each labelled with its basis
  sentence, per the contract's "a number without its basis is a lie" rule), unpriced
  banner always present when applicable; (iii) A360 — unchanged visually (switches to the
  extracted assembly).
- **Navigation:** links from the expense pages + Payroll/Raw-Materials sidebar
  (one MenuItem at most — the a360 pin cost is known: +2 for a management-visible item).
- **Responsive:** the certified 3-width discipline (mobile data-label stacks; screenshots
  per the MEE-C headless method). **No parallel UI systems; tokens only.**

### 8. Integration Review

- **Upstream:** raw_materials (rolls/leftovers/prices) · production (consumption events,
  SWA snapshots, processing_cost) — both read-only.
- **Downstream:** expense surfaces (the new window) · BOD (ladder handoff only) ·
  P13 (check candidates: one-rupee-once predicate · honest-NULL rendering predicate) ·
  P11 dataset (`seed_feature rm-expense`: priced/unpriced/leftover/damaged worlds = the
  proof fixtures) · P18A RCP (RC-9 financial certification consumes these surfaces).
- **Cross-app data flow:** rolls → (raw_materials reads) → period aggregates → expense
  window; rolls+SWA+ASR → (production assembly) → costing page/A360. No new FKs, no new
  imports upward, no state crossing apps.
- **P16 coordination:** Material Spend and FactoryExpense/recurring totals may appear on
  one screen ONLY as labelled siblings, never summed (ADR-0011 + contract §6.5).

### 9. Risks

| # | Risk | Mitigation |
|---|---|---|
| R-1 | Double-count via the leftover chain (source-Adda vs consuming-Adda) in PERIOD aggregation — the per-Adda derive solves it per-Adda; period consumption must apply the same net-of-remnant/leftover-at-source rules or rupees count twice | RMX-B design proves period semantics against the same C-1 rule; the one-rupee-once reconciliation (priced+leftover world) is the standing gate |
| R-2 | Purchases-vs-consumption confusion (different honest numbers) | RMX-D9 charter + on-screen basis labels (contract law) |
| R-3 | Honest-NULL regression (a NULL rendered ₹0 in a new aggregate) | reuse the certified banner machinery; unpriced-roll world walkthrough at RMX-E; P13 candidate predicate |
| R-4 | D2 permission drift (aggregate exposure beyond the ruling; or silently blessing the A360 precedent) | the §2 census finding forces an explicit owner ruling; per-roll wall re-proof regardless |
| R-5 | A360 extraction regression (byte-visible change to a certified page) | G-4-procedure: INERT extraction, parity tests, A360 render byte-anchor at RMX-0 baselines |
| R-6 | Decision-1 violation sneaking into a "total cost" column (processing_cost + settled labor summed) | per-figure derivation notes + sum-guard evidence per surface (contract §3.4) |
| R-7 | RM-V2 corner-painting (cloth-shaped period tables) | zero new tables (Models A+B); reads behind service seams — the recorded compat observations honored |
| R-8 | 18A/deployment compatibility | read-only + no migrations ⇒ nothing deploy-specific; RCP consumes the surfaces as-built; no flags |
| Business | a manager seeing factory-wide material spend (if D2 opens aggregates) learns supplier-level economics indirectly | aggregates only; per-roll price/supplier stays walled (4-layer re-proof); owner rules D2 consciously |

### 10. Implementation Strategy (waves = the contract's RMX ladder; each battery-bearing where code lands)

| Wave | Objective · scope | Evidence · acceptance | Stop gate |
|---|---|---|---|
| **RMX-A** | Current-state census COMPLETE (this review = the architecture core; A adds seeded-world RENDERS of every material-touching surface + the wall map + ADR-described-vs-observed reconciliation table) | census tables w/ file:line + gate citations; renders; divergences (incl. §2's D2 finding) dispositioned by owner | census contradiction ⇒ owner before design |
| **RMX-B** | Design + gates: the 3 service functions + extraction specs (exact signatures, queries, period semantics per the D9 charter) presented; ladder gates requested per function; D2 ruling recorded | owner approves each addition; NO U14/census-addendum needed (read-only) | any element implying a second truth/forbidden sum |
| **RMX-C** | Read-path implementation: the gated functions + the A360 INERT switch; per-figure ADR checks; one-rupee-once reconciliation v1 on the 4 proof worlds | parity tests (A360 byte-behavior); reconciliation tables; purity pins; battery | reconciliation failure; NULL-as-₹0; any write |
| **RMX-D** | Surfaces: costing-page columns + the Material Spend page per D2 gating; mobile 3-width evidence; banners live | identity matrices; wall re-proof; canon compliance; battery | wall widening; unlabelled combined total |
| **RMX-E** | Money certification: one-rupee-once across ALL surfaces · per-surface ADR-0009 table · ADR-0011 re-proof · ledger/golden/settlement/costing byte-checks · honest-NULL walkthrough · **MEE-D-style regression section: replay every RMX scenario before the certificate** | the full proof set; battery | any drift/double-count/forbidden sum |
| **RMX-F** | Closure: sync disposition · U6 docs · `seed_feature rm-expense` (spec amendment A4) · P13 candidates · BOD handoff · charter census · the P16-style closure package (exec summary · deferred register · extension points · reuse report · **completion certificate**) · VERDICT | the package | unaccounted chartered item |

### 11. Testing Strategy

- **Unit (owning apps):** period functions (priced/unpriced/leftover/damaged fixtures;
  month boundaries; Decision-5 valuation cases) · `full_cost_for_adda` component tests
  (formula fidelity; earn_map-source equality; grouped/non-payable handling) · A360
  parity (INERT proof).
- **Integration:** one-rupee-once reconciliation tests (a world where a roll feeds two
  Addas via leftover — the R-1 case) · costing page + Material Spend page context
  cross-checks vs the owning services (the no-second-truth instrument) · honest-NULL
  render tests (banner text present; no ₹0 for NULL) · full identity matrices + negative
  controls · purity pins (zero ORM writes from the new views; no new writers anywhere).
- **Browser:** 3-width screenshots of both surfaces on seeded worlds (incl. the unpriced
  world's banner) — the MEE-C headless method.
- **Battery:** entry baseline **1842/1842**; growth in raw_materials/production/expense
  suites per wave; sequential fresh-DB; goldens inside. **RCP coverage:** these surfaces
  + their reconciliation predicates join RC-9 (financial) and RC-3/4/6 (app sweeps).

### 12. Documentation Plan

Per wave (U6, same session): this log · status file + battery dashboard ·
`config/raw_materials/README.md` + `docs/apps/raw_materials/GUIDE.md` (new reads) ·
`config/production/README.md` + GUIDE (cost_service additions; docs/production/OVERVIEW
if the costing page changes) · `config/expense/README.md` + GUIDE (the window view) ·
DOCUMENTATION_INDEX (this log's row) · **PDD amendment register (entry 8 = the RMX-D1
charter)** · `docs/DEV_DATASET_ARCHITECTURE.md` §12 (amendment A4, `rm-expense` worlds)
· PHASE_17 Appendix A (Design Record fills + dated amendments) · campaign memory ·
CHANGE_IMPACT_MATRIX rows for touched files. No PDD-body/ADR edits anywhere.

### RMX-0 Decision Pack — recommendations for the owner (defaults per contract Appendix A)

| # | Recommendation |
|---|---|
| RMX-D1 | **Charter Models A + B-completion (read-only), NO Model C.** Concretely: (a) period material aggregation → the expense-side Material Spend window; (b) full-cost completion on the Manufacturing Costing page via the shared extracted assembly (A360 switched INERT) |
| RMX-D2 | **Rule the live precedent explicitly:** recommendation = aggregates management-visible (consistent with A360's certified M13 card + the costing page audience); per-roll price/supplier stays FINANCIAL_ROLES-walled (4-layer re-proof in-phase). The stricter alternative (FINANCIAL_ROLES-only aggregates) requires consciously re-gating A360's existing cost card |
| RMX-D3/D4 | Read-only posture confirmed; **no schema, no U14, no census addendum** (Model C declined) |
| RMX-D5/D6/D7 | Accept as written (compliance map · no-double-count discipline · suite growth) |
| RMX-D8 | `seed_feature rm-expense` at RMX-F (amendment A4; the 4 proof worlds); BOD widgets = handoff via the ladder (not built in-phase) |
| RMX-D9 | **Charter BOTH bases, labelled:** consumption-in-period (primary — "what production used", the same Decision-5/C-1 rules as the per-Adda derive) + purchases-in-period (procurement view — intake events at purchase price); **holdings/stock-valuation DEFERRED** (a third basis; cheap later via the same seam). Damaged rolls: excluded from consumption (never consumed), visible in purchases (they were bought — honest); remnant re-issues per the C-1 exactly-once rule; NULL-priced: counted + bannered, never ₹0 |

_⏸ STOPPED per the owner stop condition: review complete; no implementation, no code, no
contract edits (Appendix A fills happen at the owner's charter approval). Awaiting the
owner's RMX-D1/D2/D9 charter + D3–D8 ratification → then RMX-A (census renders) under
the PDD change-control entry._

## RMX-A — Current-state census — ✅ COMPLETE 2026-07-18 (owner-authorized; read-only — ZERO code/design)

**Charter recorded first (this session):** PDD amendment register **ENTRY 8** + PHASE_17
Appendix A RMX-D1..D9 filled + dated (owner rulings verbatim: A+B read-only · Model C
refused · D2 = the PERMANENT aggregate/per-roll rule · D9 = consumption-primary +
purchases-secondary, holdings/inventory/stock valuation NOT built).

### A.1 Surface census (every material-money-touching surface; code + gate citations)

| Surface | Shows | Source | Gate | Material money? |
|---|---|---|---|---|
| Roll list/detail (`raw_materials/roll_views`) | per-roll price/supplier (SA/financial only), weights, status | ClothRoll | ProductionRole page + **the 4-layer wall** (A.2) | per-roll — WALLED |
| Cloth/RM dashboards | counts + history accordion | rolls/history | ProductionRole; **PA-13-3 history-strip** (cost/supplier change values excluded for non-financial) | no ₹ shown |
| **Manufacturing Costing** (`costing_views.py:26`, `_ManagementOnly`) | per-Adda STANDARD labor (payable) · non-payable priced · ACTUAL settled labor (earn_map :75) · variance · **unpriced-stage + unpriced-roll flags + the Decision-5 banner** | ASR.processing_cost · SWA snapshots · unpriced maps (:60-74) | management | **NO material ₹, NO full-cost line — the Model-B gap** |
| **A360 card** (adda detail; `adda_views.py:282 if is_management`; `a360.py:232-268`) | material net (net of remnant) · unpriced-roll flag · settled · non-payable · **full cost (Decision-2) + ₹/garment** | `material_cost_for_adda` + SWA + ASR | management-only ctx (workers leak-tested) | **YES — the live Costing-2 implementation** |
| Expense surfaces (factory-expense list · P16 recurring · payroll overview) | FactoryExpense/ledger money only | expense services | management (+SA levers) | **no material anywhere — the Model-A gap** |
| BOD financial section | P15 tiles (expenses/payroll/settlement) | certified services | SA page + FINANCIAL_ROLES | no material (future ladder item) |
| Worker surfaces (my_earnings etc.) | own money only | payroll reads | worker | none (leak-tested at P15/V1.1) |

### A.2 The 4-layer FINANCIAL_ROLES wall map (re-cited; re-proof due at RMX-D)

1. **Form-pop:** `raw_materials/forms/roll_forms.py:51-63` — supplier/cost_per_kg fields
   popped in `__init__` for non-financial users (`user_can_edit_financials`).
2. **Service gate:** `roll_service.py:126-127` — submitted financial values from a
   non-financial user ⇒ reject (first gate comment verbatim).
3. **Template/view strip:** `roll_detail.html` / `roll_list.html` /
   `roll_views.py`/`dashboard.py` via `user_can_view_financials`.
4. **History-strip:** `dashboard.py` PA-13-3 — `field_name__in=('supplier','cost_per_kg')`
   change-values excluded from time-logs for non-financial viewers.

### A.3 ADR-0009-described vs OBSERVED reconciliation

| ADR statement | Observed | Verdict |
|---|---|---|
| D5: costing-dashboard banner exists | **LIVE render captured (scratch_2, SA):** "⚠ 13 consumed rolls without a purchase price — material costing is incomplete… (unknown is never counted as ₹0)" + per-row unpriced notes | ✅ matches |
| D5: leftovers at source price; `consume_leftover` sole writer | derive lines `cost_service.py:265-277` (leftover_in at source ₹/kg; C-1 exactly-once) + R5-census writer map | ✅ matches |
| D5: intake never price-blocked | intake form: financial fields optional + popped; 15/15 dev rolls live with NULL price | ✅ matches |
| D2: formula fixed "before any report exists" | **SUPERSEDED BY REALITY: the report exists** — A360 implements the formula (M13) | ✅ implemented (no divergence; the ADR's future arrived) |
| D3: earn_map = the labor reference | `costing_views.py:75` + a360's SWA sums | ✅ matches |
| D1: duality never summed | costing page shows std vs actual side-by-side + variance; no sum anywhere | ✅ matches |
| Contract D2 DEFAULT (aggregates walled) vs observed A360 | management sees material ₹ on A360 | **RESOLVED by the owner's D2 ruling this session (the precedent is now the permanent rule)** |

### A.4 Live-world evidence (scratch_2; server :8004 temp, stopped after; probe rollback-clean)

- **Wall, both identities (HTTP):** roll detail as SA → financial field labels present;
  as MANAGER → **zero financial tokens** (grep 1 vs 0) — layers live.
- **Honest-NULL world (today's real dev state):** ALL 15 rolls unpriced ⇒ every surface
  exercises the NULL path; costing render (screenshot archived `rmx_costing_sa.png`)
  shows the banner + 13 affected rows + goldens' settled labor (₹801/₹344.25/₹633 visible).
- **Derive, both paths (rollback-wrapped):** `material_cost_for_adda(DEV-SUP-TEE-001)`
  unpriced → `net 0.00 · unpriced_rolls 1 · has_material True` (honest-NULL, never ₹0);
  inside an atomic probe with the roll priced ₹100/kg → `consumed 2500.00 · remnant
  250.00 · net 2250.00 · unpriced 0`; **rollback verified (0 priced rolls after)**.
- **Gap confirmations:** costing page has NO material/full-cost column (screenshot);
  expense side has NO material view; **no priced-roll fixture exists on any dev world**
  → the RMX-F `rm-expense` worlds (priced/unpriced/leftover/damaged) are REQUIRED for
  the one-rupee-once proofs (finding feeds RMX-B test planning).

### A.5 Findings register (all dispositioned)

| # | Finding | Disposition |
|---|---|---|
| A-F1 | D2 default-vs-precedent divergence | RESOLVED — owner ruling (permanent rule) recorded at Appendix A/PDD entry 8 |
| A-F2 | Dev worlds carry zero priced rolls | → RMX-B: the A3-style `rm-expense` worlds become the proof fixtures (already chartered at D8/RMX-F); interim tests build their own priced fixtures |
| A-F3 | A360 assembly is inline (view-local) | → RMX-B design: the chartered INERT extraction (`full_cost_for_adda`) — no action at A |
| A-F4 | No divergence between ADR-0009 and observed behavior | census closes clean — no §16.10 stop |

**Battery: no code this wave — the 1842/1842 terminal-P16 baseline STANDS (BOD-B/RMX-review
precedent: research/census waves don't run the battery).** Primary untouched (read-only
census; probes on scratch_2 only, rollback-proven). Git 49404001 · 2 stashes.

_RMX-A closed. Next: **RMX-B** (design + per-function ladder gates: the 2 raw_materials
period reads · the `full_cost_for_adda` INERT extraction · the Material Spend window
spec · exact period semantics per the D9 charter) — owner-gated._

## RMX-B — Design + implementation gates — ✅ SPEC COMPLETE 2026-07-18 ⏸ awaiting RMX-C authorization. ZERO production code written.

> **[2026-07-18 FFD-E banner — heading preserved as written]:** RMX-C WAS authorized and
> executed same day (§RMX-C below); phase CLOSED at §RMX-F.

**Ownership correction vs the RMX-0 sketch (recorded):** consumption EVENTS
(`LayeringRollEntry` · `RemainingClothOfClothRoll`) are production-domain models — the
consumption read therefore lives in **production `cost_service`** (beside
`material_cost_for_adda`, its semantic sibling), NOT in `roll_service`. Purchases read
(pure rolls) stays in **raw_materials `roll_service`**. Import direction preserved
(production already imports raw_materials; never the reverse).

### B.1 Spec — `roll_service.material_purchases_in_period(year, month)` (raw_materials)

- **Signature:** `material_purchases_in_period(year, month) -> dict` (ints; validated
  1–12 / 2000–2100 like `_month_bounds`).
- **Returns:** `{'period_key': 'YYYY-MM', 'total': Decimal, 'priced_rolls': int,
  'unpriced_rolls': int, 'total_weight_kg': Decimal, 'damaged_rolls': int}`.
- **Query plan (ONE aggregate):** `ClothRoll.objects.filter(purchased_date__year=year,
  purchased_date__month=month).aggregate(total=Sum(F('weight_kg') * F('cost_per_kg'),
  filter=Q(cost_per_kg__isnull=False), output_field=DecimalField()), priced=Count('id',
  filter=Q(cost_per_kg__isnull=False)), unpriced=Count('id',
  filter=Q(cost_per_kg__isnull=True)), weight=Sum('weight_kg'), damaged=Count('id',
  filter=Q(status=Status.DAMAGED)))` — constant query count, index on status exists;
  `purchased_date` is a DateField (NO timezone semantics — month boundaries exact by
  construction).
- **Aggregation rule:** intake value = `weight_kg × cost_per_kg` (both purchase FACTS;
  Decision-5 — never re-priced).
- **NULL prices:** excluded from `total`, counted in `unpriced_rolls` → the caller's
  banner. Never ₹0.
- **Damaged rolls:** INCLUDED in the total (owner ruling: honest in purchases — they
  were bought) and separately counted for transparency.
- **Cancelled records:** none exist for rolls (intake rows are kept or deleted whole;
  no soft-cancel state) — nothing to filter.
- **Callers:** the Material Spend view; future BOD ladder answers; reconciliation tests.

### B.2 Spec — `cost_service.material_consumption_in_period(year, month)` (production)

- **Signature:** `material_consumption_in_period(year, month) -> dict`.
- **Returns:** `{'period_key', 'consumed': Decimal, 'remnant_returned': Decimal,
  'leftover_in': Decimal, 'total': Decimal (= consumed − remnant_returned; leftover_in
  is already inside consumed — SAME shape as the per-Adda derive), 'unpriced_events':
  int}`.
- **Valuation rules (the per-Adda derive's rules, time-sliced — one law, two windows):**
  - **+ layering entries** with `attached_at` in the period:
    `Coalesce(weight_verified_kg, roll.weight_kg) × roll.cost_per_kg` (price NULL ⇒
    unpriced_events += 1, not valued).
  - **− remnants** with `created_at` in the period, valued at the SOURCE roll's ₹/kg
    (cloth returned to stock leaves the period's consumption).
  - **+ leftover consumptions** with `consumed_at` in the period (`is_consumed=True`),
    valued at the SOURCE roll's ₹/kg (never re-priced; price NULL ⇒ unpriced_events).
- **Query plan:** THREE constant aggregates (entries · remnants · leftover-ins), each a
  grouped Sum with the same Coalesce/×-price expressions; no per-row Python loops.
- **C-1 exactly-once proof (the law across time):** each rupee of intake value appears
  as +entry once, −remnant at most once (when weighed back), +leftover_in at most once
  (when re-consumed) — the SAME three event classes the certified per-Adda derive nets,
  so **Σ over all periods ≡ Σ over all Addas of `material_cost_for_adda(...)['net']`**
  (the standing reconciliation identity; a test walks a two-Adda leftover chain and
  proves both sums equal the intake value counted once).
- **Month boundaries:** event timestamps are tz-aware datetimes → sliced with
  `[period-start-local, next-period-start-local)` (Asia/Kolkata local dates — the P15
  lesson, documented on-screen basis sentence). A July entry whose remnant is weighed in
  August legitimately shows July + / August − (physical reality; the cross-period
  reconciliation identity above keeps the total honest).
- **Damaged rolls:** no special casing needed — consumption counts EVENTS; a
  never-consumed damaged roll has no events (owner rule satisfied structurally); a roll
  damaged AFTER real consumption keeps its true events (honest).
- **Cancelled records:** a pre-completion detached `LayeringRollEntry` is DELETED (model
  law) — gone means never happened; post-completion entries are frozen. No cancel flags
  to filter.
- **Callers:** Material Spend view; reconciliation tests; future BOD ladder.

### B.3 Spec — the Decision-2 assembly extraction (production `cost_service`)

- **Shape:** `full_costs_for_addas(addas) -> {adda_id: {'material': <the 6-key derive
  dict>, 'settled_total': Decimal, 'nonpayable_priced': Decimal, 'full_cost': Decimal}}`
  (BULK — grouped queries, constant count) **+ `full_cost_for_adda(adda)` = the
  single-Adda convenience delegating to the bulk** — ONE implementation, two call
  shapes. `material_cost_for_adda` (certified M13) **delegates to the bulk's material
  arm the same way** (INERT: parity-pinned; the original loop algorithm lives on inside
  the parity TEST as the independent reference — the queue-batching precedent).
- **Calculation order + component ownership (byte-equal to a360.py:181-240):**
  1. settled_total = Σ non-voided `SWA.earning_amount_snapshot` grouped by adda
     (a360:181-188's exact filter, grouped).
  2. nonpayable_priced = Σ `ASR.processing_cost` where cost IS NOT NULL and
     `workflow_stage.credits_workers=False`, grouped by adda — **equivalence note
     (documented proof obligation for the parity test):** a360's per-stage loop sums
     per-ws priced lane records then adds ws-level sums for non-payable stages; the flat
     per-SR sum is the same row set (per-ws grouping is associative over the same
     non-null rows).
  3. material = the bulk material arm (entries + remnants + leftover-ins grouped by the
     relevant adda keys: `stage_record__adda` / `layering_entry__stage_record__adda` /
     `consumed_in_adda` — the derive's exact three relations).
  4. full_cost = material.net + settled_total + nonpayable_priced (a360:240 verbatim).
- **Honest-NULL propagation:** material.unpriced_rolls and has_material flow through
  unchanged; full_cost remains a Decimal sum of KNOWN components (the a360 semantic —
  unpriced material is flagged beside the figure, exactly as today; NO behavioral
  change).
- **Parity verification strategy:** (a) unit parity — bulk material vs the in-test
  reference loop on priced/unpriced/leftover/remnant fixtures; (b) A360 context parity —
  render before/after switch on the same world: `material_net/settled_total/
  nonpayable_priced/full_cost/cost_per_garment` byte-equal (plus the scratch_2 live
  render anchor from RMX-A); (c) `material_cost_for_adda` delegation parity — old-loop
  reference vs delegated result, all fixture worlds.
- **Migration path from A360 (INERT):** a360 keeps its per-SR `swa_by_sr` map (row
  display needs it) and REPLACES its three panel totals + material block with ONE
  `full_costs_for_addas([adda])[adda.pk]` call (net query delta ≈ +1 SWA aggregate —
  recorded, display bytes identical). The costing page (RMX-D) consumes the SAME bulk
  for its new columns — one assembly, two consumers, zero duplicated math.

### B.4 Spec — the Material Spend view (expense app)

- **URL:** `/expense/material-spend/` · name `expense:material-spend` · link from the
  Factory Expenses header (sibling nav) + optional sidebar MenuItem (management
  predicate; the known a360 pin cost +2 if added — decision recorded at RMX-D close).
- **Permissions:** `LoginRequiredMixin + _ManagementOnly` (the D2 PERMANENT rule:
  aggregates management-visible). Anon → login; worker/accountant/listing → blocked;
  identity matrix + negative controls at RMX-D. Zero per-roll data on the page (wall
  untouched by construction).
- **View shape (THIN):** `_parse_month(request)` → TWO service calls
  (`material_consumption_in_period` · `material_purchases_in_period`) → context. No
  math, no ORM, no writes.
- **Layout (factory-expense canon: hero copper · month-nav prev/label/next · totals
  tiles · sections):**
  - **Section 1 — Consumption during {month} (PRIMARY):** basis sentence ("Cloth value
    used by production this month: rolls laid, minus leftovers returned to stock, plus
    stored leftovers reused — valued at purchase price."), tiles (net total · consumed ·
    remnant returned · leftover reused), unpriced-events banner when > 0 (the certified
    wording: "…material costing is incomplete… unknown is never counted as ₹0").
  - **Section 2 — Purchases during {month} (secondary):** basis sentence ("Cloth bought
    this month at purchase price — includes rolls later damaged; unpriced rolls are
    counted, never valued at ₹0."), tiles (total · rolls priced/unpriced · weight ·
    damaged count), unpriced banner.
  - **No FactoryExpense numbers anywhere on the page** (ADR-0011: sibling link "Factory
    expenses →" only; never a blended total).
  - Empty states per section ("No purchases recorded for {month}.").
- **Responsive:** tiles wrap → stack at 360; any table = data-label stack; month-nav
  buttons ≥40px; 3-width screenshots at RMX-D (headless method).

### B.5 Architectural review (per function)

| | purchases_in_period | consumption_in_period | full_costs_for_addas |
|---|---|---|---|
| Owner app | raw_materials | production | production |
| Owns | period intake valuation | period consumption valuation (event law) | the Decision-2 assembly |
| Reads | ClothRoll only | LRE · RCOCR · ClothRoll price | SWA · ASR · the material arm |
| Never touches | production/expense/ledger state; any write | expense/ledger/settlement; any write | expense/ledger; any write; WSC.expected_* (Decision-3) |
| Upstream deps | none | raw_materials models (existing direction) | existing costing sources |
| Downstream | Material Spend · BOD ladder · tests | same | A360 (switched) · costing page · tests |
| Duplicate logic eliminated | n/a (first of kind) | REUSES the derive's valuation law (one law, two windows) | KILLS the inline a360 assembly (one assembly, two consumers); delegation kills the loop/bulk dual for material |

### B.6 Read-only certification (re-proven at design level)

All three functions + the view: SELECT aggregates only — **no writes · no model
mutations · no migrations · no transaction requirements** (multi-query derives are
as-of-request, the standing costing-surface semantic; no atomicity needed because
nothing is written) · **Money-Write census UNCHANGED** (zero new writers; the purity
pins extend to the new view) · **ADR-0009 preserved** (Decision-1: no figure sums
processing_cost with settled labor — full_cost adds NON-payable processing only, the
fixed formula; Decision-3: labor = SWA snapshots only; Decision-5: valuation +
honest-NULL everywhere) · **ADR-0011 preserved** (no factory-expense value enters any
per-Adda or material figure; the Material Spend page carries no FactoryExpense number).

### B.7 One-rupee-once scenario review (expected behavior, pre-implementation)

| Scenario | Expected |
|---|---|
| Normal consumption | roll's value appears once: +entry in its month; in the Adda's net once |
| Leftover created | source month/Adda: −remnant at source price; the rupee "returns to stock" |
| Leftover reused | consuming month/Adda: +leftover_in at SOURCE price; intake value net across both Addas/months = counted once (C-1) |
| Remnant never reused | stays subtracted — consumption total honestly excludes cloth not used |
| Damaged, never consumed | purchases: counted (+ damaged count); consumption: absent (no events) |
| Damaged after partial use | its real events stand (honest); purchases counted once |
| Unpriced roll | purchases: unpriced count; consumption: unpriced_events; NEVER ₹0; banners on every surface |
| Month boundary (entry Jul, remnant Aug) | Jul +full, Aug −remnant — physical truth; Σ months ≡ Σ Addas ≡ intake-once (the reconciliation identity, test-pinned) |
| Two Addas, one source roll (via leftover) | Adda-1 net + Adda-2 net = roll value counted once (the derive's C-1 rule; bulk parity keeps it) |
| Purchases vs consumption | DIFFERENT questions, separately labelled; never summed with each other or with FactoryExpense |

### B.8 RMX-C test plan (complete)

- **Unit — purchases:** priced+unpriced+damaged mixed month · month-boundary rolls ·
  empty month · weight/total math.
- **Unit — consumption:** entry valuation (verified-weight fallback) · remnant
  subtraction · leftover-in at source price · unpriced_events · month slicing (tz-local)
  · empty month.
- **Parity:** bulk-material vs in-test reference loop (4 fixture worlds) ·
  `material_cost_for_adda` delegation parity · **A360 context parity before/after switch
  (byte-equal panel values)** · nonpayable per-ws-vs-per-SR equivalence.
- **Reconciliation (the signature):** two-Adda leftover chain: Σ periods ≡ Σ Addas ≡
  intake-once; plus the straddle-month case.
- **Honest-NULL:** unpriced world renders — banner text present on BOTH sections + the
  costing page; no ₹0 anywhere for NULL.
- **Identity:** Material Spend full matrix (anon/worker/accountant/listing/manager/SA) +
  POST-less page (zero POST routes) + **the 4-layer roll wall re-proof suite re-run**
  (D2 order).
- **Purity:** static pin extended (no ORM writes in the new view/templates; no new
  writers anywhere) + read-only render proof (model-counts identical around renders).
- **Browser evidence (RMX-D):** 3-width screenshots of Material Spend (both sections +
  banners) and the costing page with its new columns; SA vs manager identical aggregates
  (D2); worker blocked.

### B.9 Implementation readiness checklist

✅ every function fully specified (signatures · returns · exact filters/expressions) ·
✅ every query known (1 + 3 + 3-grouped aggregates; constant counts; indexes present) ·
✅ every responsibility defined (B.5 ownership table; consumption-read home CORRECTED to
production) · ✅ every dependency identified (import directions verified) · ✅ every ADR
requirement mapped (B.6 + per-figure checks in the test plan) · ✅ every duplicate
calculation eliminated (one valuation law · one assembly · one month parser · certified
banner wording reused) · ✅ **RMX-C can proceed with ZERO remaining architectural
decisions** (the only open cosmetic choice — sidebar MenuItem for Material Spend — is a
RMX-D presentation call with a known cost, not an architecture decision).

_⏸ STOPPED. RMX-B complete; no production code. Awaiting owner authorization for RMX-C
(read-path implementation per §B.1–B.3 + the B.8 tests)._

## RMX-C — Read-path implementation — ✅ COMPLETE 2026-07-18 (owner-authorized "implement exactly what was approved"; RMX-B frozen and honored)

### C.1 Implementation (exactly the frozen §B specs)

- `raw_materials/services/roll_service.py` **+`material_purchases_in_period`** — ONE
  aggregate (value = weight×price filtered priced · priced/unpriced/damaged counts ·
  weight), spec-verbatim.
- `production/services/cost_service.py` **+the engine section:** `_material_value_expr`
  (THE Decision-5 SQL expression, 4dp parity scale) · `material_costs_for_addas` (bulk
  arm: 3 grouped aggregates; **NullIf(verified_weight, 0) replicates the original
  Python `or` fallback exactly** — the one parity subtlety found and closed) ·
  `material_cost_for_adda` → **DELEGATES** (docstring updated, signature/shape
  unchanged) · `full_costs_for_addas` + `full_cost_for_adda` (THE Decision-2 assembly:
  material.net + Σ non-voided SWA snapshots + non-payable priced processing) ·
  `material_consumption_in_period` (the derive law time-sliced; local-month event
  windows).
- `production/views/a360.py` — the INERT switch: panel values (material · settled ·
  nonpayable · full_cost) now read from the ONE assembly; per-SR display maps stay
  view-local. **a360 query pin 78→80, conscious + spec-recorded** (§B.3 predicted the
  delta: the assembly's own SWA + ASR aggregates; material 3-for-3 neutral).

### C.2 Mandatory verification (owner's four)

1. **A360 parity:** test `test_a360_context_parity` (build_a360 context ==
   assembly outputs, key-by-key) + **live scratch_2 anchor reproduction**: the
   delegated derive returns EXACTLY the RMX-A pre-switch numbers (DEV-SUP-TEE-001:
   net 0.00 · unpriced 1 · has_material True) and the assembly reports the world's
   known settled journey (settled ₹150.00 → full ₹150.00).
2. **One-rupee-once (the §B.7 scenarios, executed):** the two-Adda leftover-chain world:
   A1 = 24kg×₹100 − ₹250 remnant = **₹2150**; A2 = leftover-in **₹250** at SOURCE price
   + unpriced roll counted ⇒ Σ Addas = **₹2400 = the 24kg consumed of R1, once**.
   Straddle month: July +2400, August (−250 remnant +250 leftover-in) = 0 ⇒
   **Σ periods ≡ Σ Addas ≡ intake-consumed-once (test-pinned)**. Purchases ≠
   consumption (2500 vs 2400 — different honest questions; never blended). Damaged
   August roll: IN purchases (+ counted), absent from consumption.
3. **Read-only purity:** `test_derives_write_nothing` (all-model row counts
   byte-identical around every new function) + the static no-write-token pin over the
   engine section + **zero Money-Write census impact** (no writer exists; census
   untouched).
4. **ADR verification:** ADR-0009 — Decision 1 pinned (`full_cost` ≠ any sum including
   the payable standard; explicit test), Decision 2 component fidelity (per-component
   asserts incl. the voided-SWA exclusion), Decision 3 (SWA snapshots only), Decision 5
   (source-price valuation + honest-NULL: unpriced counted never ₹0, live 13-event
   evidence on scratch_2); ADR-0011 — untouched (no FactoryExpense value anywhere in
   any new figure; grep + zero imports).

### C.3 Tests (+11, `production/tests/test_rmx_read_paths.py`)

Bulk-vs-**original-reference-loop** parity (the M13 algorithm lives in the test as the
independent reference — the queue-batching precedent) · delegation parity · the
verified-weight-0 quirk parity (NullIf) · assembly components + Decision-1 pin ·
per-ws≡per-SR nonpayable equivalence (the §B.3 proof obligation, discharged) · a360
context parity · purchases (incl. damaged-included) · consumption straddle-month ·
the one-rupee-once identity · purity ×2.

### C.4 Battery + sync + primary

**1853/1853 — NEW BASELINE** (10-app S1 = 1108 [chain 1097 + 11] · patterns_ai 528 ·
devseed 139 · verification 78). In-wave dispositions: the a360 pin 78→**80** (conscious,
dated, spec-referenced) · P14 guard's 5th live catch (doc floor — this log) → routine
graph rebuild (validator ALL PASS; `aa0e2eb8835e`) → sync **BLOCKER=0 / WARN=369**
(367 + this log's standing residue rows). S2/S4 ran green in-close before the pin/graph
fixes (S1/S3-domain-only fixes; both re-run green — disclosed, the MEE-C pattern).
**PRIMARY EXACT: ledger 170/Σ₹10,880.25 · FactoryExpense 4.**

_RMX-C closed. Next: **RMX-D** (surfaces: costing-page material/full-cost columns + the
Material Spend page + identity matrices + the D2-ordered 4-layer wall re-proof + 3-width
evidence) — owner-gated._

## RMX-D — Surfaces — ✅ COMPLETE 2026-07-18 (owner-authorized; presentation strictly — zero new business logic/calculations/valuation rules)

### D.1 Implementation

- **Manufacturing Costing completion (Model B):** `ProductionCostingView` merges
  `full_costs_for_addas([...])` per row (pass-through values; the grand full-cost line =
  a presentation-sum of the certified per-Adda figures, documented in-code);
  `costing.html` + two columns (Material (net) w/ per-row incomplete flags · **Full Cost
  (ADR-0009)**) + the second hero tile ("Full cost (ADR-0009, shown Addas)") — clearly
  SEPARATE from the standard-labor total (Decision-1 duality visually preserved).
  Costing perf pin **11→16, conscious + dated** (+5 = exactly the assembly's constant
  query set: material 3 + SWA 1 + ASR 1 — volume-independent).
- **Material Spend page:** `expense.MaterialSpendView` (`/expense/material-spend/`,
  `_ManagementOnly` per the D2 permanent rule, **GET-only by shape** —
  http_method_names, POST→405 pinned) — THIN: `_parse_month` → the two certified RMX-C
  reads → context; `material_spend.html` per the B.4 spec (canon layout; consumption
  PRIMARY + purchases secondary, both basis-labelled; certified banner wording; empty
  states; **zero FactoryExpense numbers on-page** — sibling links only).
- **Navigation (the approved entry):** the Factory-Expenses header link
  "Material spend →" (+ links back to factory expenses and the costing page from the
  new page's month-nav). **Sidebar MenuItem deliberately NOT added** (recorded decision:
  each management-visible MenuItem costs +2 on the a360 pin; the money pages
  cross-link — owner may order a MenuItem + Access-Control row later at RMX-F/BOD-ladder
  time).

### D.2 Security (the owner-ordered proofs)

- **Identity matrices, both pages** (`test_material_spend.py`, 11 tests): anon 302 ·
  worker/accountant/listing blocked · manager + SA 200 (the D2 permanent rule live on
  BOTH surfaces); Material Spend POST → 405.
- **4-layer wall re-proof:** manager sees the ₹1000 AGGREGATE on Material Spend while
  the SAME roll's detail page hides ₹100/kg and the supplier (template layer); SA sees
  both (financial layer); the SERVICE gate refuses a manager submitting financials
  (`update_roll_details` → PermissionDenied — layer 2 re-fired); the form-pop + history
  strip layers re-ran green inside the suites (roll-form + PA-13-3 pins).
- Aggregate exposure exactly per D2: nothing beyond period totals/counts on the new
  page; no per-roll rows anywhere.

### D.3 Browser evidence (scratch_2 via temp :8004, stopped; SA session)

9 headless-chrome captures (3 pages × 360/768/1280) in the session scratchpad
(`rmxd_{spend_jul,spend_empty,costing_new}_{m,t,d}.png`), visually verified:
- **Material Spend 2026-07 (the honest-NULL world):** live banner "⚠ 13 consumption
  events without a purchase price — material costing is incomplete…"; ₹0.00 tiles with
  the unpriced context; purchases empty state; month-nav + sibling links; mobile stacks
  clean, no overflow.
- **Material Spend 2026-01:** BOTH empty states render.
- **Costing page:** both new columns + the ADR-0009 grand tile (₹9,598.25 full vs
  ₹9,899.75 standard — visibly separate figures); the Decision-5 banner intact;
  per-row "1 unpriced roll — incomplete" flags live.

### D.4 Regression

A360 unchanged (parity pins + suites green — the assembly serves both consumers) ·
existing costing components byte-untouched (columns appended; all prior pins green) ·
no workflow regressed (full battery). In-wave disposition: costing perf pin 11→16
(above) · P14 guard's 6th live catch (URL floor — the new route) → routine graph
rebuild (validator ALL PASS; `e31c756a4a73`) → sync **BLOCKER=0 / WARN=369, body_hash
identical to the RMX-C baseline**.

### D.5 Battery + primary

**1864/1864 — NEW BASELINE** (10-app S1 = 1119 [chain 1108 + 11 surface tests] ·
patterns_ai 528 · devseed 139 · verification 78). **PRIMARY EXACT: ledger
170/Σ₹10,880.25 · FactoryExpense 4.**

_RMX-D closed. Next: **RMX-E** (money certification wave: one-rupee-once across ALL
displaying surfaces · per-surface ADR tables · byte-checks · honest-NULL walkthrough ·
the full scenario replay) — owner-gated._

## RMX-E — Money certification wave — ✅ CERTIFIED 2026-07-18 (certification only; zero features/calculations/architecture changes)

### E.1 ONE-RUPEE-ONCE CERTIFICATION (all user-visible surfaces)

**The certification world** (`test_rmx_certification.py`, the §B.7 scenario table as ONE
world: priced R1 · unpriced R2 · damaged R3 · leftover chain A1→A2 · shared source roll
· straddle months) — **every surface shows THE same rupees:**

| Surface | Figure | == the one source |
|---|---|---|
| Manufacturing Costing rows | material_net · full_cost per Adda | ✅ == `full_costs_for_addas` |
| A360 (adda-detail ctx, management) | material_net · full_cost | ✅ == the same assembly |
| Material Spend | consumption · purchases contexts | ✅ == the period services |
| Costing grand line | Σ row full_cost | ✅ presentation-sum of certified rows |

**Identities (test-pinned + LIVE):** Σ periods ≡ Σ Addas ≡ intake-consumed-once
(₹2,400 = 24kg of R1, exactly once, across the A1→A2 leftover chain and the July/August
straddle: July +2,400 · August −250 remnant +250 reuse = 0) · purchases ≠ consumption
(₹2,500 vs ₹2,400 — separate labelled questions) · damaged R3: in purchases (+counted),
absent from consumption everywhere · empty month = zeros, nothing invented ·
**LIVE priced-world walkthrough (scratch_2, rollback-wrapped):** all 15 rolls priced
₹100/kg inside an atomic → **Σ costing-row material (₹29,250.0000) ≡ period-consumption
net (₹29,250.0000)** — the cross-surface identity holding on real rendered pages;
Material Spend ctx == service; the honest-NULL banner correctly DISAPPEARS in the priced
world and returns after rollback (0 priced rolls after; ledger 90/₹3,128.25 frozen
throughout). **No unexplained differences anywhere.**

### E.2 ADR-0009 CERTIFICATION (Decision-by-Decision)

| Decision | Requirement | Proof |
|---|---|---|
| **1** — duality never summed | no figure adds processing_cost to settled labor | assembly adds NON-payable priced only (explicit `assertNotEqual` incl. the payable standard); costing page keeps std/actual/variance as separate labelled columns; full-cost tile visually separate from the standard total (₹9,598.25 vs ₹9,899.75 on the live render) |
| **2** — the fixed formula | material + Σ non-voided SWA + non-payable priced; no overhead | component-by-component pins (`test_full_cost_components_decision_2`; voided SWA excluded); ONE assembly serves every surface; zero overhead anywhere (grep + tests) |
| **3** — labor source | Σ non-voided SWA snapshots; never WSC.expected_*, never Σ ADST totals | the assembly's settled arm = exactly that filter; earn_map untouched on the costing page; no WSC.expected_* read in any new code (grep) |
| **4** — grouped never pay twice | member stages yield no rate | UNTOUCHED by this phase — the existing C-1 pins (`test_c1_hardening`) ran green in every battery; the assembly reads SWA outcomes, never rates |
| **5** — material semantics | purchase price · honest-NULL · leftovers at source price · `consume_leftover` sole writer · intake unblocked | the ONE `_material_value_expr`; NULL counted-never-valued on every surface (banners live-rendered both states); leftover valued at source (chain test ₹250); no writer touched; intake flow untouched |

### E.3 ADR-0011 CERTIFICATION (separation, both directions)

Financial-surface inventory: Manufacturing Costing · A360 · Material Spend (material
money) — Factory Expenses · Recurring Expenses · Payroll/Settlements · BOD financial
tiles (factory/worker money). **Proven both directions on the certification world:** a
₹8,888.88 FactoryExpense appears on NO material surface; the material figures
(₹2,400/₹2,150) appear on NO factory-expense surface; the only crossings are sibling
LINKS. Separation is structural: zero FactoryExpense reads in any Phase-17 code path
(grep) + the both-direction rendering pins.

### E.4 READ-ONLY CERTIFICATION

Zero writes (all-model row counts byte-identical around every surface render AND every
service call — pinned) · zero mutations · zero migrations (expense migrations still end
at 0015; raw_materials/production migration dirs unchanged this phase) · **zero
Money-Write census changes** (the census addendum count for Phase 17 = 0; no writer
exists) · no hidden side effects (Material Spend is GET-only by shape, POST→405; the
live probes left ledger + roll rows byte-identical).

### E.5 HISTORICAL INTEGRITY

Nothing stored ⇒ nothing to corrupt: every figure derives at request time from the raw
tables (rolls · layering entries · remnant rows · SWA · ASR) — reconstructable by any
auditor (the reference-loop lives in the test suite as the independent recomputation);
no duplicated valuation (ONE expression, ONE assembly, delegation); no hidden state
(no caching, no materialization — Model C refused by charter and absent by grep).

### E.6 FULL SCENARIO REPLAY (the owner's list)

priced world ✅ (live rollback walkthrough) · unpriced world ✅ (scratch_2's real state:
13-event banner live) · leftover chain ✅ (₹2,150+₹250) · remnant ✅ (−₹250 at source
price) · damaged roll ✅ (purchases-only) · shared source roll ✅ (the chain, once) ·
month boundary ✅ (July/August) · empty month ✅ (2026-01 zeros + empty states) ·
honest-NULL ✅ (banners both pages + costing flags, live-rendered both states) ·
management permissions ✅ (mgr sees aggregates — D2) · worker permissions ✅ (blocked
from both pages; the adda-detail render carries ZERO a360 bytes — leak law re-pinned).

### E.7 REGRESSION CERTIFICATION

A360 parity ✅ (pins + the assembly-equality context test) · Manufacturing Costing ✅
(all prior columns byte-untouched; pins green) · Material Spend ✅ (11 RMX-D pins) ·
permission wall ✅ (4-layer re-proof suite green) · browser ✅ (the RMX-D 9 captures +
this wave's live renders) · **battery 1870/1870 — NEW BASELINE** (10-app S1 = 1125
[chain 1119 + 6 certification] · patterns_ai 528 · devseed 139 · verification 78; zero
failures, zero guard catches — no new docs/urls this wave) · **golden values ✅:
`verify_factory` 19/19 with body_hash `121c2ed5a3e56644…` — IDENTICAL to the MEE-D run
(cross-phase determinism with all Phase-17 code present)** · **ledger integrity ✅:
PRIMARY 170/Σ₹10,880.25 EXACT · FE 4 · users 48; scratch ledger frozen through every
probe.** Sync: BLOCKER=0 / WARN=369, body_hash = the standing baseline.

**RMX-E VERDICT: PHASE 17 MATERIAL-MONEY SURFACES ARE FINANCIALLY CERTIFIED.**

_RMX-E closed. Next: **RMX-F** (certification + handoffs: `seed_feature rm-expense`
spec amendment A4 · P13 candidates · BOD ladder handoff · charter-coverage census ·
the closure package + PHASE-17 VERDICT) — owner-gated._

## RMX-F — Certification + handoffs — ✅ COMPLETE 2026-07-18 → 🏁 PHASE 17 CLOSED

### F.1 Dataset (A4 — the chartered closure deliverable)

**`seed_feature feature-rm-expense`** (dataset-spec **dated amendment A4**; registry⇄
CONTENT⇄spec agreement): a DEV-RME settled journey whose consumed roll stays UNPRICED
(the live honest-NULL banner world) · a PRICED-but-unconsumed roll (purchases fixture,
via `update_roll_details`) · a DAMAGED roll (purchases-only fixture, via
`mark_roll_damaged`) · **the journey's REAL 2.5kg leftover `consume_leftover`'d into a
second adda — the one-rupee-once reuse chain, every step a certified writer**;
state-probed convergence (fixtures selected by STATE, not index — the one build defect
found and fixed in-wave). The exact-value straddle-month reconciliation fixtures live in
the battery suites (documented split). **LIVE scratch_2: created=16 PASS → second run
created=0 (pure convergence) → `verify_feature` 8/8 PASS.** +1 registry test.

### F.2 Executive Summary (owner deliverable 1)

Phase 17 connected the roll cost truth to the money surfaces — as a completion, not a
rebuild. The owner can now see: **what production really cost per Adda** (the
Manufacturing Costing page's new Material and Full-Cost columns — the ADR-0009 formula
that previously lived only on A360), and **what cloth cost this month** (the Material
Spend page: consumption and purchases, separately labelled, honest about unknowns).
Architecturally: ZERO new tables, ZERO writers, ZERO migrations — four read functions
in their owning apps, one INERT extraction that made A360's assembly THE shared
implementation, and two thin windows. Financially: every rupee provably counted once
(across Addas, across months, across surfaces — including the live ₹29,250 ≡ ₹29,250
rendered-page identity), honest-NULL end-to-end, the FINANCIAL_ROLES wall re-proven,
and the goldens byte-stable through the whole phase.

### F.3 PHASE 17 COMPLETION CERTIFICATE (owner deliverable 2)

| Dimension | Status |
|---|---|
| **Architecture** | CERTIFIED — read-path only; owning-app ladder honored (purchases→raw_materials · consumption/assembly→production · window→expense); ONE valuation expression, ONE assembly, delegation; Model C refused and absent |
| **Implementation** | COMPLETE — every chartered item live (F.7 census: 11 implemented · 4 deferred · 2 N/A · 0 unaccounted) |
| **Security & permissions** | CERTIFIED — D2 permanent rule live on both surfaces (full identity matrices); the 4-layer per-roll wall re-proven at all four layers; worker leak-law re-pinned (zero A360 bytes) |
| **Financial correctness** | CERTIFIED (RMX-E §E.1–E.7) — one-rupee-once across all surfaces + live; identities pinned; ledger/goldens byte-stable (verify_factory body_hash identical across MEE-D→RMX-E) |
| **ADR compliance** | CERTIFIED — ADR-0009 all five Decisions (per-Decision table §E.2); ADR-0011 both directions (§E.3); zero census impact |
| **Testing** | 28 new pins across 3 suites (11 read-path + 11 surfaces + 6 certification) + 1 dataset test; the original M13 loop preserved as the independent auditor reference |
| **Documentation** | COMPLETE — log (charter→census→spec→waves→certification→closure) · PDD entry 8 · spec amendment A4 · Appendix A filled · GUIDEs/READMEs · index |
| **Battery** | **1871/1871 — TERMINAL PHASE-17 BASELINE** (10-app 1125 [chain 1097 entry +11 C +11 D +6 E] · patterns_ai 528 · devseed 140 [+1 A4] · verification 78) |

### F.4 Architecture Reuse Report (owner deliverable 3)

REUSED: `material_cost_for_adda` (became the delegated face of the bulk arm) · the A360
assembly (extracted, now serves 3 consumers) · earn_map/SWA source (Decision 3, never
re-derived) · `_parse_month` · the certified banner wording · the factory-expense page
canon (hero/month-nav/tiles) · `_ManagementOnly` · the 4-layer wall (untouched,
re-proven) · `consume_leftover`/`update_roll_details`/`mark_roll_damaged` (dataset
world) · the queue-batching parity-test pattern. DUPLICATES ELIMINATED: the inline A360
assembly (now shared) · the would-be second valuation implementation (delegation) · a
second month parser · a second banner wording. IMPROVEMENTS: one assembly for every
full-cost consumer; the costing page finally shows the fixed formula; period material
questions answerable without touching per-roll data.

### F.5 Deferred Features Register (owner deliverable 4)

Holdings/inventory/stock valuation (owner D9: future work) · Model-C materialization
(refused) · overhead component (ADR-0009 reserved, era-stamped, ADR process) ·
factory-expense allocation (ADR-0011 wall) · variance reporting (Decision 2 names it
future) · non-cloth materials (RM-V2 vision, post-P22) · supplier/procurement workflows ·
a Material-Spend sidebar MenuItem (recorded RMX-D decision; owner may order later) —
**all confirmed OUTSIDE Phase 17; none blocking.**

### F.6 Future Extension Points (owner deliverable 5) + P13 + BOD handoffs (deliverables 7–8)

- **Extension points:** holdings valuation = a third basis behind the same service seam ·
  new materials (RM-V2) = new truth tables feeding the SAME window/assembly patterns ·
  supplier analytics = reads over the walled fields (FINANCIAL_ROLES surfaces) ·
  effective full-cost reporting per product/period = loops over `full_costs_for_addas`.
- **P13 verification candidates (recorded per P13's registry law):** (a) the
  one-rupee-once predicate (Σ periods ≡ Σ Addas over any window); (b) the honest-NULL
  rendering predicate (unpriced>0 ⇒ the incomplete statement present, no ₹0
  substitution); (c) assembly-consistency predicate (costing rows ≡
  `full_costs_for_addas`).
- **BOD handoff (nothing implemented):** candidate ladder answers now exist as L1 —
  month material-spend (consumption net / purchases total) · unpriced-roll count (the
  data-quality tile) · factory full-cost roll-up. Each enters ONLY via the PHASE_15
  Metric Resolution Ladder + Widget Registry in a later owner-gated session; financial
  tiles inherit the FINANCIAL_ROLES wall per the BOD charter (D2's aggregate rule noted
  for that session's decision pack).

### F.7 Charter Coverage Census (owner deliverable 9 — every RMX charter item)

| Chartered item | Status |
|---|---|
| Model A — period material aggregation → expense-side window | ✅ Implemented |
| Model B — full-cost completion on the costing surface | ✅ Implemented |
| Model C — materialization | N/A (owner-refused) |
| Consumption-in-period (PRIMARY, labelled) | ✅ Implemented |
| Purchases-in-period (secondary, labelled) | ✅ Implemented |
| Holdings/inventory/stock valuation | ⏸ Deferred (owner) |
| D2 permanent permission rule (aggregates mgmt-visible) | ✅ Implemented + certified |
| Per-roll 4-layer wall re-proof | ✅ Implemented (all four layers re-fired) |
| Damaged-roll rules (excluded-from-consumption / honest-in-purchases) | ✅ Implemented |
| NULL always honest (banners everywhere) | ✅ Implemented + live-proven both states |
| One-rupee-once standing proof | ✅ Implemented (tests + live identity) |
| A360 byte-parity through the extraction | ✅ Implemented |
| `seed_feature rm-expense` (A4) | ✅ Implemented (live 8/8) |
| BOD widgets | ⏸ Deferred (owner boundary; ladder handoff) |
| Overhead / allocation / variance / non-cloth | N/A / ⏸ per their own locks (F.5) |

**0 unaccounted.**

### F.8 Final verification + VERDICT (owner deliverables 10 + final)

No unfinished implementation (census above) · no undocumented changes (U6 synced every
wave; sync BLOCKER=0 at close, body_hash at baseline) · no unresolved architectural
issues (readiness checklist closed at B.9; no open questions) · no unresolved financial
issues (RMX-E certificate) · no open ADR questions (compliance tables; zero revisions
needed) · no Phase-17 blockers. **PRIMARY EXACT at close: ledger 170/Σ₹10,880.25 ·
FactoryExpense 4 · users 48.** Git 49404001 · 2 stashes · NO commits (U2).

**VERDICT: PHASE 17 — RAW MATERIAL → EXPENSE COST INTEGRATION — COMPLETE · CERTIFIED ·
READY FOR PHASE 18.**

_🏁 Phase 17 CLOSED 2026-07-18. Next: Phase 18 (FFD-0) — owner-gated; then 18A (RCP) →
19–22 per the frozen roadmap._

---

## Post-closure dated corrections — 2026-07-18 (Phase-18 FFD-E finding disposition; append-only — nothing above rewritten)

FFD-D (the protocol acceptance demonstration, run ON this phase) audited this log
against the tree; its confirmed findings are dispositioned here (register:
FEATURE_DOC_SYNC_LOG §FFD-E).

1. **§F.3 "Documentation COMPLETE — … GUIDEs/READMEs" was an OVERCLAIM at close
   (FFD-D M-1/M-4):** the three GUIDEs, PDD entry 8, A4, Appendix A and index were
   complete, but the three app READMEs (raw_materials/production/expense) and the
   CHANGE_IMPACT_MATRIX venues (CHOKEPOINTS/cost_service · DATA_FLOWS/material_flow ·
   REQUEST_JOURNEYS/costing_flow) carried NO Phase-17 content. **Repaired at FFD-E
   2026-07-18** (all six venues now current — grep evidence in FEATURE_DOC_SYNC_LOG
   §FFD-E); the §F.3 documentation row is TRUE as of this correction, not as of the
   original closure date.
2. **§F.7 census arithmetic restated at item grain (FFD-D m-2):** the "11 implemented ·
   4 deferred · 2 N/A" line was a bundling slip (the 4-item bundled row carried no
   per-item statuses). Item-grain census, each status from its own recorded lock:
   **11 implemented · 5 deferred** (holdings [D9] · BOD widgets [D8 ladder] · overhead
   [ADR-0009 reserved-future] · variance [ADR-0009 future report] · non-cloth materials
   [RM-V2, post-P22]) · **2 N/A** (Model C [owner-refused D1] · factory-expense
   allocation [ADR-0011 FORBIDDEN — never-build]) · **0 unaccounted** (18 items total).
3. **RMX-0 baselines were recorded one wave late (FFD-D m-8):** the contract's RMX-0
   row chartered battery/ledger/golden/render baselines at RMX-0; in practice the
   battery baseline (1842) was cited at RMX-0 but the ledger Σ (170/₹10,880.25) first
   appears at RMX-C and the pre-switch A360 anchor actually used at C.2 was RMX-A's
   DEV-SUP-TEE-001 capture. Discipline was materially honored; the substitution is now
   stated.
4. Two closed-wave headings (§RMX-0, §RMX-B) still read "⏸ AWAITING" — clarifying
   banners inserted UNDER them (FFD-D m-3); original heading text preserved.
