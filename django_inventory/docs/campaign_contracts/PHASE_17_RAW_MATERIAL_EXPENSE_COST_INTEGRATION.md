---
id: docs-campaign-contracts-phase-17-raw-material-expense-cost-integration
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 17 Execution Contract — Raw Material → Expense Cost Integration

> Authored 2026-07-12 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md) and the full new-feature lock-set of
> [PHASE_15_BUSINESS_OPERATING_DASHBOARD.md](PHASE_15_BUSINESS_OPERATING_DASHBOARD.md) +
> [PHASE_16_MONTHLY_EXPENSE_ENGINE.md](PHASE_16_MONTHLY_EXPENSE_ENGINE.md): frozen PDD
> (charter via change-control) · MANUFACTURING_V1_FREEZE · U8/Money-Write STOP (census
> addendum mechanism = MEE-D3 precedent) · U14 migration gate (MEE-A precedent) · Phase-10 UI
> canon · P11/P12 dataset mechanics · P13/P14 instruments · the Phase-4 protocol for any
> confirmed defect. Deltas only.
> **The governing truth-lock is ADR-0009 (cost truth), read in full and load-bearing:**
> Decision 1 — processing_cost and settled labor are NEVER additive · Decision 2 — **the
> full-Adda-cost formula is ALREADY FIXED on record**: material cost (G1, cloth-only) +
> ACTUAL settled labor (Σ non-voided SWA snapshots, both eras) + processing_cost of
> NON-payable priced stages only + overhead (FUTURE, era-stamped) — "the first
> full-cost/profitability implementation (Costing-2) has its formula fixed before any report
> exists" · Decision 3 — the labor-source rule (never WSC.expected_*, never Σ AddaSettlement
> totals; reference = costing_views earn_map) · Decision 5 — material-price semantics:
> `cost_per_kg` = PURCHASE price, **honest-NULL (unknown is never silently zero; any material
> figure with unpriced consumed rolls must state "material costing incomplete")**, leftovers
> valued at SOURCE roll price, leftover consumption written only by
> `roll_service.consume_leftover`.
> **Dual-lock note:** ADR-0009 reserves future overhead in full cost (era-stamped) while
> ADR-0011 forbids the factory-expense/salary class from per-Adda allocation — Phase 17
> touches NEITHER reserved future: no overhead component, no factory-expense allocation.
> **The integration MODEL is not on record** (master-index line: "connect roll cost truth to
> expense reporting") — the owner charters it at RMX-0; nothing is invented.
> Evidence doc (created at RMX-0): `docs/RM_EXPENSE_INTEGRATION_LOG.md`.

## 1. Phase objective

Connect the roll cost truth (ClothRoll.cost_per_kg + its append-only history + leftover
valuation) to expense/cost reporting under the owner's chartered integration model — so
material money becomes VISIBLE where the owner wants it (expense reporting, full-Adda-cost
per the fixed ADR-0009 formula, or both) — while every rupee stays recorded exactly once
(roll truth remains THE material-cost record; no second source, no double count), the
honest-NULL discipline is preserved end-to-end, the FINANCIAL_ROLES wall is honored or
consciously re-ruled by the owner, and the ledger/settlement/costing engines remain
byte-identical.

## 2. Scope

### 2.1 Facts of record (authoring-time, ADR-0009 verified in full; RMX-A censuses the rest)

| Fact | Evidence |
|---|---|
| Material-cost truth today | `ClothRoll.cost_per_kg` (PURCHASE price; honest-NULL; corrections history-audited) + `supplier` — both behind the certified 4-layer FINANCIAL_ROLES wall (form-pop · service PermissionDenied · template · history-strip; MGT-D/E runtime-proven); leftovers valued at source price, consumed only via `roll_service.consume_leftover` (append-only) |
| The full-cost formula | ADR-0009 Decision 2 — FIXED before any report exists; material component = "G1, cloth-only until stated otherwise"; the implementation slot is named "Costing-2" |
| Labor source rule | Decision 3: Σ non-voided SWA earning snapshots (both eras); reference implementation = costing_views earn_map — any full-cost build REUSES that source, never re-derives |
| Never-additive rule | Decision 1: processing_cost + settled labor never summed; standard-vs-actual = a future VARIANCE report, never a cost component |
| Honest-NULL discipline | Decision 5: NULL ≠ ₹0 anywhere; consumed-but-unpriced rolls surfaced prominently; "material costing incomplete" statement is MANDATORY on any material-touching costing report |
| Expense-side reality | FactoryExpense = factory-level cost record, sole writer expense_service, append-only (R5/ADR-0011/P16); Phase-16 adds recurrence — Phase 17 was named at MEE-D2 so the P16 schema cannot corner this phase |
| Reserved futures NOT touched | overhead-in-full-cost (ADR-0009, era-stamp required, owner/ADR) · factory-expense per-Adda allocation (ADR-0011 wall) · non-cloth material classes ("cloth-only until stated otherwise") |
| Permission collision (real, unresolved) | roll financials = FINANCIAL_ROLES (SA + accountant; manager PROVEN blocked); costing/expense surfaces = management — whether an AGGREGATED material figure may be shown to managers is a policy question the record does not answer → RMX-D2, owner |
| Wall-hole note | the accountant cannot reach any page today (PHASE_03 §2.2 contradiction, D1 pending) — Phase-17 surfaces must not silently widen or depend on that unresolved verdict |
| Battery | raw_materials + expense + production are all existing battery members — suite grows naturally, NO framework amendment |

### 2.2 In / out

**In:** the owner-chartered integration model (RMX-D1) · a current-state census (what costing/
expense surfaces already show about material money — evidence, not assumption) · read-path
design + implementation per the chartered model (aggregation functions in OWNING apps —
Phase-15 ladder discipline; full-cost assembly per the fixed formula if chartered) · any
owner-gated schema (U14, MEE-A procedure) or write-path (census addendum, MEE-D3 procedure)
the chartered model requires · surfaces per certified patterns + the RMX-D2 permission ruling
· the no-double-count and honest-NULL proof sets · docs/dataset/BOD/P13 handoffs.
**Out:** overhead allocation (both reserved futures, header) · re-pricing anything (purchase
price is a fact; leftovers keep source price) · a second material-cost record (copying roll
costs into FactoryExpense or any new table AS TRUTH — a materialization model, if chartered,
stores REFERENCES/provenance, never authoritative amounts — RMX-D6) · variance reporting
(Decision 2 names it future) · non-cloth materials · touching settlement/ledger/pay paths ·
blocking roll intake on price (Decision 5 owner amendment stands) · editing the
FINANCIAL_ROLES wall mechanics (a policy change routes through RMX-D2 as an owner ruling
implemented via the certified gate patterns, never a wall demolition).

## 3. Success criteria

Phase 17 is DONE when ALL hold:
1. The owner's integration charter is recorded via PDD change-control (RMX-D1: which
   integration(s) — expense-report aggregation, Costing-2 full-cost per the fixed formula,
   or both; period basis per RMX-D9) — BEFORE design.
2. The current-state census (RMX-A) is complete: every existing surface touching material
   money mapped (what it shows, from which source, behind which gate) — the integration
   builds on evidence, not memory.
3. **One-rupee-once proven (the signature proof):** for every new aggregate/figure, a seeded-
   world reconciliation shows each roll's cost counted exactly once across ALL surfaces that
   display it (roll truth ⇄ new aggregate ⇄ any FactoryExpense-side view) — plus a structural
   proof that no new table stores an authoritative copy of a roll amount (RMX-D6 provenance
   rules honored).
4. **ADR-0009 compliance proven per surface:** Decision-1 no-forbidden-sums check on every
   figure's query · Decision-2 formula fidelity if full-cost is chartered (component-by-
   component evidence, labor from the Decision-3 source — the earn_map reference — reused not
   re-derived) · Decision-5 honest-NULL end-to-end (an unpriced-roll seeded world shows the
   "material costing incomplete" statement on every material figure; NULL never renders as
   ₹0) · no overhead component anywhere.
5. **ADR-0011 untouched:** factory expenses appear in no per-Adda figure; the P16 engine's
   rows and the material figures never merge into an unlabelled total (any chartered combined
   factory-spend view labels its components and sums only what its charter permits).
6. **Permission ruling implemented + certified:** the RMX-D2 matrix proven all-identity
   (shell + browser, double-gate, negative controls); the existing 4-layer roll wall
   re-proven INTACT for per-roll data regardless of the aggregate ruling; no accidental
   widening of the PHASE_03 accountant question.
7. Read-only purity where the charter is read-only (zero writes, BOD-style proofs); any
   chartered write path carries its owner-approved census addendum + U14 gates and preserves
   single-writer + append-only disciplines.
8. Money do-no-harm: ledger count/Σ, golden journeys, existing per-Adda costing pages (for
   non-chartered components), and settlement lifecycle all byte-identical around every wave.
9. Battery green at the new baseline (existing suites grow; arithmetic per wave);
   knowledge_sync diff-mode clean at close; U6 docs (raw_materials + expense + production
   owning docs as touched); `seed_feature rm-expense` P11 amendment (incl. an unpriced-roll
   world — the honest-NULL fixture); BOD handoff via the PHASE_15 ladder; status + memory
   synced every sub-phase.

## 4. Rules of engagement (deltas beyond U1–U14 + inherited locks)

- **Charter fidelity:** the integration model, period basis, and permission policy are the
  owner's; the agent proposes nothing onto a money report uninvited.
- **Roll truth stays THE truth:** every material figure derives at read time from roll data
  (or from chartered provenance references back to it); an aggregate that cannot be
  reconciled row-by-row to rolls does not ship.
- **Formula fidelity:** if Costing-2 is chartered, the Decision-2 formula is implemented
  EXACTLY (components, sources, era discipline) — a desired deviation = ADR-0009 revision
  territory (owner process), never an implementation choice.
- **Honest-NULL is a rendering law:** every new figure carries the incomplete-material
  statement machinery from its first render; a figure without it does not merge.
- **Ladder discipline (P15 §6.3 reused):** aggregation functions are born in their OWNING
  apps (roll aggregates in raw_materials' service family; full-cost assembly beside the
  existing costing code in production; expense-report views in expense) — each addition
  individually owner-gated (frozen modules), INERT to existing callers, tested.
- **Write humility:** the default posture is READ-ONLY integration; any chartered write path
  (materialization/provenance rows) triggers the full MEE-B-class treatment: U14 gates,
  census addendum, hostile review, main-thread.
- One wave at a time; money-adjacent waves main-thread (owner standing rule).

## 5. Evidence standard

Per wave: the census tables (RMX-A) with file:line/gate citations · per-figure derivation
notes (source query → components → ADR-0009 checks) · the one-rupee-once reconciliation
tables on seeded worlds (incl. leftover-bearing and unpriced-roll worlds) · honest-NULL
renders screenshotted/quoted · permission matrices all-identity + wall-intact re-proof ·
ledger/golden/costing byte-checks · battery arithmetic · browser 3-width evidence after
restart. Any gate (U14/census-addendum/RMX-D2 ruling) quoted verbatim with owner approval.
Sub-agent sweeps supplemental (U7); charter recording, formula assembly, money proofs,
permission verdicts, certification = main-thread.

## 6. Methodology

### 6.1 The three candidate integration models (charter picks; each with its gate stack)

- **Model A — read-only expense-report aggregation:** expense/BOD-side reporting reads
  material spend from roll truth via owning-app read functions; zero new tables, zero writes
  (BOD-window pattern; purity-proven). Gates: ladder gates only.
- **Model B — Costing-2 (full-Adda-cost per the fixed formula):** the Decision-2 formula
  implemented on the costing surface: G1 material (roll consumption valued per Decision 5,
  leftovers at source price) + Decision-3 labor (earn_map source) + non-payable
  processing_cost; honest-NULL banners; NO overhead. Gates: ladder gates + formula-fidelity
  evidence; still read-only (all components exist as data).
- **Model C — materialized linkage:** if the owner wants material spend REPRESENTED in the
  expense domain (e.g. period material-spend records beside FactoryExpense), the rows store
  PROVENANCE (roll references + period + derived-at), never authoritative amounts — display
  re-derives or clearly labels snapshot-with-provenance; requires U14 schema gates + a
  Money-Write census addendum + the no-double-count structural proof. This model is the most
  dangerous and defaults OFF unless the charter demands it.
Combinations permitted per charter; each activated model brings its whole gate stack.

### 6.2 Current-state census (RMX-A — before any design)

Evidence-map: the Manufacturing Costing page's exact current components (processing_cost
presentation, APSCPB pieces, any material mention) · the costing-dashboard unpriced-roll
banner state (Decision 5 says it exists — verify) · roll list/detail financial displays +
history · leftover/remnant flows (V1.1 re-issue) + damage states and how each affects cost
derivation · expense-side report surfaces · every gate on each. Divergence between ADR-0009's
described state and observed state = a finding (conflict rule), reported before design.

### 6.3 Derivation semantics (frame; policy = RMX-D9)

"Material spend" needs a period basis the record does not fix: purchases-in-period (intake
events at purchase price) vs consumption-in-period (rolls/leftovers consumed into Addas) vs
holdings (stock valuation) — different accounting questions with different honest answers.
The charter picks (possibly several, labelled); damaged rolls, remnant re-issues, and
NULL-priced items get their chartered treatment stated per figure. The contract fixes only
the invariants: valuation always per Decision 5; NULL always honest; every figure labels its
basis on-screen (a number without its basis is a lie waiting to happen).

### 6.4 Surfaces + permissions (RMX-D2 frame)

New/extended surfaces follow the certified patterns (dispatch mixin + rule row via Access
Control UI + AJAX fork; Phase-10 canon; mobile summary-first; money-family components). The
wall question is decided ONCE at RMX-D2: default = aggregated material figures inherit the
FINANCIAL_ROLES wall (SA + accountant-when-reachable; managers excluded — consistent with
the certified per-roll wall); the owner may rule that AGGREGATES are management-visible
(a conscious policy change, implemented as gates on the new surfaces — the per-roll 4-layer
wall stays intact regardless, re-proven).

### 6.5 Integration hooks

**BOD (P15):** material-spend / full-cost widgets enter ONLY via the ladder + registry
(this phase's owning read-functions become ladder step-1 answers). **Dataset (P11/P12):**
`seed_feature rm-expense` — priced + unpriced + leftover + damaged roll worlds (the proof
fixtures). **Verification (P13):** candidate checks (one-rupee-once reconciliation predicate;
honest-NULL rendering predicate) = handoff notes per P13's registry law. **Knowledge (P14):**
diff-mode per wave. **P16 coordination:** any chartered combined factory-spend view labels
recurring-expense vs material components and never blends them into an unlabelled total.
**Deployment (P19–21):** nothing deploy-specific expected beyond migrations IF Model C is
chartered (then the MEE deploy-ordering note extends).

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); evidence into the log; **battery at every
code-wave close**.

| # | Scope · Key proofs · Stop deltas |
|---|---|
| **RMX-0** — Integration charter + gate + ratification | Gate: Phase 16 closed (locked order). **Owner charters the integration** (models A/B/C selection + period basis + permission ruling direction) via PDD change-control; ratifies RMX-D1..RMX-D9. Baselines: battery entry; ledger count/Σ; golden references; costing-page reference captures (byte anchors for §3.8). **Stop:** charter absent/ambiguous; any RMX-D unanswered. |
| **RMX-A** — Current-state census | §6.2 evidence-map, read-only (code + seeded-world renders); ADR-0009-described-vs-observed reconciliation; the wall map; divergences reported. NO design yet. **Stop:** a census finding contradicts ADR-0009 or a certification (conflict rule — owner before design). |
| **RMX-B** — Design + gates | Per-model design against the census: derivation functions (owning apps, ladder gates requested per function) · formula assembly plan (Model B: component sources named, earn_map reuse stated) · schema + write-path plans ONLY if Model C chartered (**U14 stop-for-approval + census-addendum request — the MEE-A/B procedure verbatim**) · the RMX-D2 permission ruling recorded. **Stop:** U14/census approvals absent; a design element implying a second authoritative material record or a forbidden sum. |
| **RMX-C** — Read-path implementation (battery-bearing) | The gated owning-app functions + (Model B) full-cost assembly; per-figure ADR-0009 checks; honest-NULL machinery; one-rupee-once reconciliation v1 on seeded worlds (priced/unpriced/leftover/damaged). Model C rows (if chartered) land here under their approved gates, hostile-reviewed, main-thread. **Stop:** reconciliation failure surviving one re-derivation; any write outside approved gates; NULL rendered as ₹0 anywhere. |
| **RMX-D** — Surfaces (battery-bearing) | Expense-report/costing surfaces per charter + RMX-D2 gating; Phase-10 canon + mobile evidence; incomplete-material statements live; per-roll wall re-proof alongside the new aggregates. **Stop:** wall widening beyond the D2 ruling; gating divergence; an unlabelled combined total. |
| **RMX-E** — Money certification wave | Full proof set: one-rupee-once across ALL displaying surfaces · ADR-0009 per-surface compliance table · ADR-0011 no-per-Adda-factory-expense re-proof · ledger/golden/settlement/costing byte-checks (non-chartered components unchanged) · all-identity permission matrices · honest-NULL world walkthrough. **Stop:** any byte-drift; any double-count; any forbidden sum. |
| **RMX-F** — Certification + handoffs | knowledge_sync dispositioned; U6 docs (raw_materials/expense/production READMEs+GUIDEs as touched); P11 amendment; P13 check candidates; BOD ladder handoff; charter-coverage census (every chartered item built/deferred/declined — counted); deploy note if Model C; PHASE-17 VERDICT. **Stop:** unaccounted chartered item. |

## 8. Deliverables

- The chartered integration, live: owning-app derivation functions (+ Model-B full-cost
  assembly and/or Model-C provenance rows, if chartered, under their gates), certified
  surfaces with honest-NULL machinery and the D2 permission ruling implemented.
- The one-rupee-once + ADR-0009/0011 compliance proof sets; suite growth in the battery.
- `docs/RM_EXPENSE_INTEGRATION_LOG.md`: charter record · census · gates (U14/census-addendum
  as applicable) · per-wave evidence · money proofs · certification + handoffs.
- U6 docs; the PDD amendment entry; the P11 spec amendment; filled Design Record
  (RMX-D1..RMX-D9).

## 9. Files expected to change

**Code (gated as stated):** additive read-functions in `raw_materials`/`production`/`expense`
service families (per-function ladder gates) · surfaces (views/templates/URLs) in the
chartered apps · tests in those apps · Model-C ONLY: new additive tables + U14-approved
migrations + the addended write function inside the expense-service family. **Docs:**
`docs/RM_EXPENSE_INTEGRATION_LOG.md` (new) · owning app READMEs/GUIDEs (U6) · status file ·
DOCUMENTATION_INDEX · PDD amendment register · Money-Write census baseline (dated addendum,
Model C only) · `docs/DEV_DATASET_ARCHITECTURE.md` (dated amendment) · this file (Design
Record + amendments) · memory. **Runtime:** scratch worlds. NO framework-README battery
amendment (all touched apps are existing members).

## 10. Files that must never change (touching one = STOP + report)

- ADR-0009 and ADR-0011 (a chartered conflict = their own owner processes) · every truth-lock
  · PDD body · MANUFACTURING_V1_FREEZE · enforcement flags (U10) · settings · `.env`.
- `cost_service` (processing_cost freeze), `ledger_service`, settlement services,
  `payroll_service`, `fnf_service`, `advance_service`, existing `expense_service` and
  `roll_service` FUNCTIONS (additive-only beside them; `consume_leftover` stays the sole
  leftover-consumption writer) — and the earn_map labor source is REUSED, never re-derived
  or modified.
- `ClothRoll` schema + the 4-layer wall mechanics + roll history behavior; existing costing
  pages' non-chartered components (byte-proven); intake flow (never price-blocked).
- Any existing table's schema (Model-C migrations are additive-new-tables only).
- The PRIMARY dev DB (scratch worlds only) · non-DEV data · the 2 stashes · `.git` (U2).

## 11. Documentation update rules

At every sub-phase close, same session: (a) log section appended (closed sections append-only,
corrections dated); (b) status-file Phase-17 row + dashboard (battery per wave) + "Next
action"; (c) **U6 fully applies**: owning-app READMEs/GUIDEs current per wave, CHANGE_IMPACT_
MATRIX per changed file, DOCUMENTATION_INDEX rows; (d) the PDD amendment entry (RMX-0), any
census addendum (RMX-B/C), and the P11 amendment (RMX-F) recorded at their owning documents
per those documents' own rules; (e) knowledge_sync findings dispositioned per wave.

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-17
bullet: wave closed, chartered models, gate states, battery arithmetic, log pointer) +
MEMORY.md index line at each sub-phase close. Agents without memory: skip — the log + status
file + the owning registers (PDD/census/spec) are the complete binding record.

## 13. Battery policy

Sequential fresh-DB canonical (U5), **at every code-wave close (RMX-C, RMX-D, any RMX-E fix
wave; RMX-B too if Model-C migrations land there)**. Arithmetic: entry baseline (status
dashboard at RMX-0) + suite growth in raw_materials/expense/production per wave — **no
framework amendment** (existing members). Model-C migration waves additionally prove clean
migrate-forward on fresh scratch + the documented reverse on a disposable copy (MEE-A
procedure).

## 14. Regression policy

- Full battery green every wave; the certified 4-layer roll wall re-proven whenever any
  material figure ships (MGT-D/E behaviors intact); MGT-C expense behaviors intact.
- Ledger/golden/settlement/costing byte-checks = the money regression instruments, every
  money-adjacent wave.
- The one-rupee-once reconciliation + honest-NULL world walkthrough = this phase's standing
  regression instruments (re-run whole at RMX-E; their predicates offered to P13).
- Prior-fix guard list surfaces touched by new pages (#5 delete-confirm class, MGT-B-1 flash
  class) re-proven in browser waves; PHASE_03's accountant contradiction is NOT resolved
  here (evidence touching it = report, route to the OFF-0/D1 owner decision).
- Incidental defects = observations → U12 (+U8 stop if money); fixes via the Phase-4
  protocol (cross-logged); pins only for fixes (U4) — the phase's own feature tests are
  implementation deliverables.

## 15. Rollback policy

- Read-path waves revert file-scoped (additive functions + their consumers in one diff — the
  P15 no-orphan-extraction rule). Surfaces revert with their gates.
- Model-C migrations follow the MEE semantics: reverse path proven pre-landing; post-landing
  reversal = owner decision (U2 semi-irreversibility).
- Probe worlds disposable; landed disclosed artifacts per U13.
- The log + Design Record append-only (dated amendments).
- Session crash mid-wave: next session re-runs the wave's tests + re-baselines
  ledger/counts + the costing byte-anchors FIRST, reconciles the log, completes or reverts
  before new work.

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. RMX-0 charter absent/ambiguous, or any RMX-D1..D9 unanswered.
3. **ADR-0009:** a chartered or emergent requirement implying a forbidden sum, a formula
   deviation, overhead, re-pricing, or NULL-as-zero — owner/ADR territory.
4. **ADR-0011:** anything pulling factory expenses per-Adda or blending unlabelled totals.
5. **Double-count/second-truth:** a design or reconciliation showing a rupee counted twice
   or stored authoritatively twice — surviving one re-derivation attempt.
6. **U14 / census addendum:** Model-C needs without their recorded approvals; any write path
   outside approved gates (U8).
7. Wall breach: per-roll financial data reaching a non-FINANCIAL_ROLES identity, or aggregate
   exposure beyond the D2 ruling; any dependency on the unresolved accountant verdict.
8. Money byte-drift (ledger/golden/settlement/non-chartered costing) at any wave.
9. Battery red beyond the wave's own new tests' target behavior; knowledge_sync BLOCKER at a
   wave close.
10. Census-vs-record contradiction at RMX-A (conflict rule — report before design).

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-17 row: which RMX-* is next; battery
   arithmetic; money baselines.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + env) → **ADR-0009 IN FULL + ADR-0011**
   (the governing locks) → `docs/adr/0008` margin addendum if profitability surfaces are
   chartered → this contract FULLY (charter + census + gate states in the Design Record/log)
   → `docs/RM_EXPENSE_INTEGRATION_LOG.md` if it exists (absent ⇒ next = RMX-0).
3. Verify read-only: costing-page byte-anchors vs RMX-0 captures; ledger/golden baselines;
   purity/wall tests green in THIS tree; scratch-world availability (incl. the unpriced-roll
   world once the scenario exists).
4. Money waves = main-thread, hostile-review mindset (owner standing rule); the earn_map
   labor source is reused, never re-derived.
5. Battery environment per framework env facts; browser on :8003 with restart after template
   edits; scratch worlds only.
6. Execute exactly ONE sub-phase per §7. STOP per §16.
7. Anything inconsistent across status file / charter / ADR-0009 / census / log / this
   contract → report before working (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (RMX-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| RMX-D1 | **Integration charter** | OWNER-SUPPLIED via PDD change-control: which model(s) — A (read-only expense-report aggregation) / B (Costing-2 full-cost per the FIXED Decision-2 formula) / C (materialized provenance linkage) — and what the expense-report view(s) actually show. No default; unanswered = phase blocked | **APPROVED 2026-07-18** ("PHASE 17 CHARTER APPROVAL"): **Models A + B-completion; Model C REFUSED (no materialized tables/snapshots/persistence — read-path only)**. A completion-and-integration phase on the existing costing architecture, NOT a rebuild. Charter = PDD register **entry 8**; record RM_EXPENSE_INTEGRATION_LOG §RMX-0 |
| RMX-D2 | Permission ruling | Default: aggregated material figures inherit the FINANCIAL_ROLES wall (managers excluded, consistent with the certified per-roll wall); owner may consciously open AGGREGATES to management — either way the per-roll 4-layer wall stays intact and re-proven; no reliance on the unresolved accountant reachability verdict (PHASE_03 D1) | **RULED 2026-07-18 — the recommended policy is now the PERMANENT project rule:** factory-wide aggregate material values MAY be management-visible; per-roll pricing/supplier/individual roll economics stay behind the certified FINANCIAL_ROLES wall; security model never weakened; **4-layer wall re-proven during implementation** |
| RMX-D3 | Write posture | Default READ-ONLY (Models A/B; purity-proven); Model C only if chartered, with the full MEE-B treatment: U14 gates + dated Money-Write census addendum + hostile review + main-thread | **APPROVED 2026-07-18** — read-only architecture maintained |
| RMX-D4 | Schema + U14 | Model-C only: additive-new-tables (provenance references + period + derived-at; NEVER authoritative amounts), per-migration owner approval BEFORE writing, reverse proven on disposable copy | **APPROVED 2026-07-18** — NO schema changes, NO migrations |
| RMX-D5 | ADR-0009 compliance map | Per-surface checklist implemented as evidence: Decision-1 sum-guard · Decision-2 formula fidelity (Model B) with Decision-3 labor source (earn_map reuse) · Decision-5 honest-NULL + incomplete-material statements · zero overhead | **APPROVED 2026-07-18** — one source of truth; no duplicate calculations |
| RMX-D6 | No-double-count discipline | Roll truth = the sole authoritative material record; aggregates derive at read time or carry provenance-only snapshots (labelled); one-rupee-once reconciliation = a standing proof + P13 check candidate; combined views label components, never blend | **APPROVED 2026-07-18** — ADR compliance mandatory |
| RMX-D7 | Tests + battery | Suite growth in the owning apps (reconciliation predicates, honest-NULL renders, wall + gate pins, formula component tests); NO framework amendment (existing members) | **APPROVED 2026-07-18** — existing testing discipline maintained |
| RMX-D8 | Dataset + BOD | `seed_feature rm-expense` P11 amendment (priced/unpriced/leftover/damaged worlds — the proof fixtures); BOD widgets only via the PHASE_15 ladder + registry (built here as a final owner-gated wave or handed off — owner's call) | **RULED 2026-07-18:** rm-expense dataset at RMX-F; **BOD changes OUTSIDE this phase** — Phase-15 Ladder methodology for any later widget |
| RMX-D9 | Period/valuation semantics | OWNER POLICY: purchases-in-period vs consumption-in-period vs holdings (each a different honest number — possibly several, labelled); treatment of damaged rolls, remnant re-issues, and NULL-priced items per figure; valuation always Decision-5 (purchase price; leftovers at source price; corrections-only) | **APPROVED 2026-07-18 exactly as recommended:** BOTH clearly-labelled views — consumption-in-period (PRIMARY) + purchases-in-period (secondary); **holdings/inventory/stock valuation = future work, NOT built**; damaged rolls excluded-from-consumption/honest-in-purchases; NULL always honest |

Date · answered by: **2026-07-18 · owner ("OWNER AUTHORIZATION — PHASE 17 CHARTER APPROVAL"), recorded same session**

## Dated amendments

**2026-07-18 (FFD-E, Phase-18 finding disposition — owner-authorized close sweep):**
1. **RM-V2 compat observations RECORDED** (repairs FFD-D M-3; promised by
   [RAW_MATERIALS_V2_PRODUCT_VISION.md](../RAW_MATERIALS_V2_PRODUCT_VISION.md) §"Phase 17"
   and honored by the build, but never written here): **(a)** all material-cost reads sit
   behind a SERVICE SEAM (`roll_service.material_purchases_in_period` ·
   `cost_service.material_costs_for_addas`/`full_costs_for_addas`/
   `material_consumption_in_period`) — pages never query material money directly, so
   RM-V2 later widens the seam instead of rewriting pages; **(b)** READ-PATH MODELS
   PREFERRED over materialization (Model C refused per RMX-D1) — no stored aggregates
   exist for RM-V2 to migrate.
2. **Slug correction** (FFD-D m-5): everywhere this contract says `seed_feature
   rm-expense`, the registry slug is **`feature-rm-expense`** (the command errors
   loudly on the short form; log §F.1 used the correct slug).
3. **Quote note** (FFD-D m-4): §"master-index line" is a PARAPHRASE of
   campaign_contracts/README.md row 158 ("Connect roll cost truth to expense/cost
   reporting"), not a verbatim quote.

# Evidence note

All build evidence lives in `docs/RM_EXPENSE_INTEGRATION_LOG.md` (created at RMX-0) —
contract = procedure, log = what was chartered, censused, gated, built, and proven (framework
hierarchy rule). The cost truth stays exactly where ADR-0009 put it: on the rolls, in the SWA
snapshots, in the frozen processing_cost — this phase adds windows and, at most, provenance;
never a second ledger of material money.
