---
id: docs-campaign-contracts-phase-15-business-operating-dashboard
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 15 Execution Contract — Business Operating Dashboard (BOD)

> Authored 2026-07-12 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md). **This is the first NEW PRODUCT FEATURE since the Manufacturing V1
> freeze** — therefore the heaviest truth-locks bind from the first line: **PDD v1.0 FROZEN**
> (product truth; changes only via ADR/approved revision — the BOD's product charter enters
> through that change-control at BOD-0, never around it) · **MANUFACTURING_V1_FREEZE** (engine
> changes only via ADR/owner ruling — the BOD is ADDITIVE and READ-ONLY over every frozen
> module) · **U8/Money-Write STOP** (the BOD writes no money — proven, not promised) ·
> **U9 Frozen-Foundation rules** (settlement-only money · read-only snapshots · **mobile
> summary-first for management surfaces** · access-control-only visibility ·
> fit-existing-architecture) · **ADR-0009** (cost truth: never sum processing_cost + settled
> labor) · **ADR-0011** (monthly salary = factory-level, never per-Adda).
> Also inherits: **PHASE_10** (compose-from-canon, certified owners, tokens-only, frozen
> design families) · **PHASE_05 family** (Standard-compliant docs, graph/generation/sync
> integration) · **PHASE_11/12** (dataset scenario mechanics) · **PHASE_13/14** (verification
> + drift instruments). Deltas only.
> **The deepest honesty constraint: WHAT the BOD displays is not in the repository.** The
> master-index charter is one line ("owner-facing operating dashboard"). This contract
> therefore defines the ARCHITECTURE and the LAWS any KPI must obey; the KPI catalog,
> audiences, and product intent are OWNER-SUPPLIED at BOD-0 (Design Record BOD-D1) — nothing
> product-shaped is invented here.
> Evidence doc (created at BOD-0): `docs/BOD_BUILD_LOG.md`.

## 1. Phase objective

Build the owner's operating overview: one place that answers "how is the factory doing right
now?" by AGGREGATING what the certified system already knows — production state, money state,
material state, machine state — through the existing service layer, read-only, mobile-first,
without becoming a second source of truth for anything. The BOD is a WINDOW, never an engine:
it owns zero business logic, writes zero rows, duplicates zero calculations, and links DOWN
into the certified operational surfaces (Operations, Payroll, Costing, dashboards) rather
than replacing any of them.

## 2. Scope

### 2.1 Facts of record (authoring-time; BOD-0 re-verifies)

| Fact | Evidence |
|---|---|
| Charter | master index: "Owner-facing operating dashboard (feature build — first NEW feature since freeze; PDD/ADR rules bind)" — the ONLY product statement on record |
| Existing dashboard landscape | My Dashboard (`inventory:my_dashboard`, exempt landing, every role) · production Operations dashboard (production role) · Manufacturing Costing (management) · raw_materials dashboards ×2 (production role) · tracking Barcode Dashboard (production role) · Payroll overview (management) — all certified surfaces the BOD must LINK TO, never duplicate |
| Metric-truth owners | money: settlement/ledger services + ADR-0009 cost surfaces (Manufacturing Costing = the per-Adda cost page of record) · production truth: WST/WSC via worker_task_service, pools via pool_service · materials: roll_service + financial fields (FINANCIAL_ROLES) · machines: machine_service (zero-₹ app, grep-pinned) · patterns_ai: its services (PI-vs-ERP boundary, PLATFORM_STATUS §3) · storefront: read-only public content (ADR-0008 commerce boundary: no Order→Adda FK, no price on production models) |
| Money-KPI laws | ADR-0009: processing_cost and settled labor are DISTINCT truths, never summed; ADR-0011: FactoryExpense (incl. monthly salaries) is factory-level, NEVER allocated per-Adda; settlement is the only money boundary (U9); worker money vocabulary = Expected→Earned→Paid ladder (certified visibility ladder) |
| Visibility law | ONE live predicate (access ∩ assignment; RBAC.md "Visibility vs Action"); sidebar + URL gated together (SidebarItemRule + middleware double-gate); financial fields = FINANCIAL_ROLES |
| UI law | Phase-10 certified library (dashboard tiles/cards/KPI families exist in the §6.2 taxonomy); frozen design system; tokens-only; mobile-first rule 11 (360/768/1280); money-family UI canon in UI_COMPONENTS.md |
| Infra reality | no cache layer, websockets, or task queue is configured **in the application** (Redis exists in the production compose stack, `deploy/`, but nothing in the app consumes it as a cache) — liveness strategies requiring such infrastructure are out (BOD-D5) |
| App-layout precedent | new cross-domain apps sit at a NEW topmost import-linter layer (P12/P13 pattern); BOD is a PRODUCTION feature ⇒ BASE-settings registration (unlike devseed) |

### 2.2 In / out

**In:** the BOD app (BOD-D2 home) · the owner-chartered KPI catalog resolved through the
metric ladder (§6.3) · widget architecture + read-service wiring · permissions matrix
implementation + certification-grade proofs · mobile-first UI per Phase-10 canon · docs +
dataset scenario + handoffs.
**Out:** ANY write path (the BOD has no POST surface in v1 by default — BOD-D4; interactive
components beyond navigation/filtering are Design-Record territory) · any new business
calculation (a metric needing one = BOD-D3 ladder step 3 → owner/ADR) · any change to frozen
modules beyond individually owner-gated ADDITIVE read-only aggregation functions (§6.3) ·
models/migrations (zero-model default; wanting one = owner + U14) · caching/queue/websocket
infrastructure · replacing/redesigning ANY existing dashboard · storefront/commerce features
(ADR-0008/0010 walls) · PDD text edits (the charter enters via the PDD amendment register per
its own change-control; Phase 18 syncs the docs).

## 3. Success criteria

Phase 15 is DONE when ALL hold:
1. The owner's product charter is recorded (BOD-D1: KPI catalog, audiences, navigation
   placement) THROUGH PDD change-control (amendment-register entry/ADR reference quoted) —
   before any widget was built.
2. Every chartered KPI is resolved through the §6.3 ladder with its **single authoritative
   owner** named (service/function + the certified page that already shows the same truth,
   where one exists) — the no-duplicated-calculations proof is a per-KPI table, and any
   additive owning-service function carries its individual owner gate.
3. **Read-only proven:** the purity test (zero ORM writes from the BOD app) + zero POST
   routes (route census) + runtime row-count-identity proof around a full dashboard render.
4. **Money-KPI compliance proven per money widget:** ADR-0009 (no processing_cost+labor
   summing — checked against the widget's query), ADR-0011 (factory expenses never shown
   per-Adda), settlement-only sourcing, FINANCIAL_ROLES gating where financial fields
   surface; ledger-integrity recount around the money-widget wave (MGT-C discipline).
5. **Permissions matrix proven** (certification-grade): per-identity status matrices (owner /
   manager / worker / accountant / listing) shell + browser, middleware double-gate live
   (SidebarItemRule row + AJAX fork), negative controls, no false SA blocks — the BOD-D4
   matrix holds exactly.
6. **Mobile-first proven:** summary-first layout on phone widths; per-widget responsive
   strategy stated (rule-11 format); 360/768/1280 browser evidence after dev-server restart;
   every component composed from Phase-10 certified owners (compose-from-canon citations per
   widget; zero new shared components without the UI-D3-equivalent gate).
7. **Performance budget met** (BOD-D6): per-page query count measured (django test-client +
   assertNumQueries-class evidence), aggregate-only SQL for list-of-many metrics, no N+1
   (request-cached-principal precedent honored).
8. Battery green at the new baseline (entry + BOD suite; framework amendment per BOD-D7);
   knowledge_sync diff-mode clean (or findings owner-accepted) at close — the P14 discipline's
   first live use.
9. U6 docs complete (app README/GUIDE, feature doc + graph/cards routing noted for Phase 18);
   `seed_feature bod` scenario recorded as a dated P11 spec amendment (BOD-D8); deployment
   handoff written; status + memory synced every sub-phase.

## 4. Rules of engagement (deltas beyond U1–U14 + inherited locks)

- **Window, not engine (normative):** the BOD consumes existing services; it owns no business
  logic; it never becomes a second source of truth; it aggregates only; every metric has one
  authoritative owner; no duplicated calculations; the existing service layer remains the
  only writer. A widget that cannot satisfy all six clauses does not ship — it becomes a
  Design Record item.
- **Metric ladder discipline (§6.3):** no widget is wired before its KPI's ladder row is
  closed (owner named, gate granted if step 2). Step-2 additive functions are INERT to
  existing callers (no signature/behavior changes to anything existing — the 14b819b2 INERT
  standard applied to services) and live in the OWNING app with their own tests.
- **Charter fidelity:** the KPI catalog is the owner's; the executing agent proposes nothing
  onto the dashboard uninvited (a "useful metric" idea = a note in the log for the owner,
  never a widget).
- **Read-only + purity-first:** the purity test lands at BOD-A before any widget (P13
  pattern); no POST routes in v1 (BOD-D4 default); GETs must be side-effect-free beyond
  framework session mechanics.
- **Freeze humility:** frozen-module files are touched ONLY for individually-gated step-2
  additive functions; everything else about them is read-only imports.
- One widget-wave at a time (serial discipline); money widgets in their own U8-hostile wave.
- Certification-grade evidence for permissions (this phase creates a new privileged surface —
  it gets the same treatment the campaign gave every existing one).

## 5. Evidence standard

Per KPI: the ladder row (KPI · owner service/function · certified-page cross-reference ·
ladder step · gate ref if step 2) + the widget's value cross-checked against its
authoritative page on a seeded world (same world, same number — the no-second-truth proof).
Per wave: purity/battery/query-count evidence; browser 360/768/1280 after restart; per-widget
responsive strategy. Money wave additionally: ADR-0009/0011 compliance notes per widget +
ledger recount. Permissions: per-identity URL/render matrices + middleware fork proofs +
exact refusal quotes. Sub-agent scaffolding sweeps supplemental (U7); ladder resolutions,
money widgets, permission verdicts, certification = main-thread.

## 6. Methodology

### 6.1 Information hierarchy + home-screen philosophy (frame; content = BOD-D1)

The BOD is the owner's FIRST screen for "state of the business": a summary-first home
(mobile = the primary design target, U9) of few high-level KPI tiles, each drilling DOWN via
links into the certified operational surface that owns its truth (Operations, Costing,
Payroll, Settlements queue, raw-material dashboards, machine register). Depth lives in the
existing pages — the BOD adds altitude, not duplication. Widget count, grouping, and ordering
= owner charter (BOD-D1); the frame guarantees only: summary-first, drill-down links on every
tile, zero dead-ends, and the existing "My Dashboard" personal landing untouched (the BOD is
a DESTINATION for privileged roles, not the universal landing — changing landing behavior =
owner decision recorded in D9).

### 6.2 Widget architecture

A widget = (KPI id · owning read-call · presentation component from the Phase-10 certified
library · gate predicate · responsive strategy · drill-down target). Widgets are declared in
a registry (code, not DB — zero-model default) so the sidebar/permissions/docs/graph can
enumerate them; each renders independently (one widget's failure degrades to an error tile,
never a 500 page — fail-soft rendering, evidence-tested). Read-only vs interactive: v1 =
read-only + navigation (+ simple GET filters where the owning service already parameterizes);
anything stateful (saved layouts, preferences, alerts) = future Design-Record territory.

### 6.3 The metric resolution ladder (BOD-D3 — the no-second-truth mechanism)

Per chartered KPI, in order:
1. **An existing service/manager function or certified page computation exists** → the BOD
   calls IT (import + call; zero new logic).
2. **The truth exists but only inline in a certified view/template** → EXTRACT it into the
   owning app's service as an additive read-only function (individually owner-gated because
   the owning module may be frozen; INERT to existing callers; the extracted view now calls
   the same function — one calculation, two consumers), then the BOD calls it.
3. **The KPI requires genuinely new business calculation** → STOP for that KPI: Design Record
   row + owner decision (and possibly ADR — e.g. anything touching cost aggregation beyond
   ADR-0009's surfaces). The BOD never hosts the new logic itself; if approved it is born in
   the owning app under the owner's ruling.
Ladder outputs are recorded BEFORE wiring (BOD-B) — the census IS the build plan.

### 6.4 Data strategy: queries, aggregation, refresh, performance

Read path: BOD view → widget registry → owning read-calls → template. Aggregation happens in
the OWNING service (SQL aggregates / existing computed properties) — the BOD never re-derives
in Python what SQL/the owner-function can answer. Query budget per page load = BOD-D6
(measured, not vibes; aggregate queries for many-row metrics; select_related/prefetch
discipline; the request-cached principal pattern for RBAC calls). **Refresh strategy (BOD-D5
default): data is as-of page load + a manual refresh affordance; NO polling, NO websockets,
NO cache layer** (none exists in the repo; introducing one = infrastructure decision far
beyond a dashboard). "Live" means "current at load" — stated on-screen (an as-of timestamp),
so the dashboard never lies about freshness.

### 6.5 Permissions (BOD-D4 default matrix)

v1 default: the BOD is OWNER/SA-facing (the charter says owner-facing) — SA full; manager =
owner-decided subset (default: none in v1, revisit with the Office-role integration);
worker/listing/accountant: no access (their surfaces are unchanged; accountant's future
financial-window questions belong to the Phase-3 D1 outcome, not here). Enforcement = the
certified pattern: dispatch mixin + SidebarItemRule row (menu hidden ⇒ URL blocked) + the
middleware AJAX fork; financial-bearing widgets additionally gate on FINANCIAL_ROLES ∩ the
page gate. Future Office-role integration + any manager tier = dated D4 amendments after
Phase-3's verdicts land.

### 6.6 Integration hooks (future phases)

**Dataset (P11/P12):** `seed_feature bod` scenario (dated spec amendment) gives demo +
acceptance worlds; owner acceptance happens on seeded scratch worlds. **Verification (P13):**
the BOD adds no state ⇒ no new invariants; the route census grows (recorded); any BOD-visible
golden value (e.g. a settled-journey total on a seeded world) may join verify goldens by
owner choice. **Knowledge (P05/P08/P09/P14):** feature doc + URL cards enter via the graph/
generation pipeline (source update → rebuild → regenerate — the P09 workflow); knowledge_sync
diff-mode after every wave = the U6 instrument (P14 handoff, first live use). **Deployment
(P19–21):** BOD ships as part of the deployed system; the runbook's route/smoke expectations
grow; no BOD-specific deploy steps by default.

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); evidence into the build log; **battery at
every code-wave close**.

| # | Scope · Key proofs · Stop deltas |
|---|---|
| **BOD-0** — Product charter + gate + ratification | Gate: Phase 14 closed (locked order; the knowledge instruments exist for this build). **Owner supplies the product charter:** KPI catalog, audiences, navigation placement — recorded via PDD change-control (amendment register/ADR ref). Owner ratifies BOD-D1..BOD-D9. Baselines: battery entry, route-census count. **Stop:** charter absent/ambiguous (nothing to build that isn't invention); any BOD-D unanswered. |
| **BOD-A** — App skeleton + gates + purity (battery-bearing) | The BOD app (BOD-D2): base-settings registration, topmost import-linter layer, dispatch mixin, SidebarItemRule row, empty summary-shell page; **purity test + zero-POST route proof land first**; browser: shell renders for SA, refused for every other identity (matrix v0). **Stop:** any write path; sidebar/middleware wiring diverges from the certified double-gate pattern. |
| **BOD-B** — Metric resolution census | The ladder run for EVERY chartered KPI (§6.3): owner-service mapping, certified-page cross-reference, step classification; step-2 extraction list with per-item owner gates requested; step-3 items → Design Record + owner. NO wiring yet. **Stop:** a KPI resolves to nothing on record and the owner is absent (never invented). |
| **BOD-C** — Non-money widget waves (battery-bearing; repeatable) | Wire step-1/gated-step-2 non-money KPIs: production state, materials, machines, patterns counts, storefront content state; per-widget: cross-check vs authoritative page on a seeded world, fail-soft proof, responsive strategy + 3-width browser evidence, query budget measurement. **Stop:** cross-check mismatch (= duplicated/diverged calculation — back to the ladder); budget blown without an owner-accepted note. |
| **BOD-D** — Money widget wave (battery-bearing; U8-hostile) | Financial KPIs: settlement/ledger/costing/factory-expense reads; per-widget ADR-0009 + ADR-0011 compliance notes; FINANCIAL_ROLES ∩ page-gate proofs; ledger recount around the wave; Expected→Earned→Paid vocabulary + money-family UI canon compliance. **Stop:** U8 anomaly (ANY write, even "denormalizing a total"); an ADR-0009/0011 conflict in a chartered KPI (→ owner: the KPI changes, the ADR does not). |
| **BOD-E** — Permissions + UI certification | Full per-identity matrices (shell + browser, all five roles + anon), middleware forks, negative controls, no-false-SA-block check; full mobile-first pass (summary-first proven on phone width; every widget's strategy verified); Phase-10 canon compliance census (per-widget compose-from-canon citations); accessibility per the UI-D5-ratified baseline. **Stop:** any 200-leak / false block; a widget needing a new shared component without its gate. |
| **BOD-F** — Certification + handoffs | knowledge_sync diff-mode run (findings = the docs work list, closed or owner-accepted); U6 docs complete; `seed_feature bod` spec amendment recorded; route-census delta recorded; deployment + Phase-16/17/18 handoff notes (the BOD is the natural DISPLAY surface for Phase-16 expense automation and Phase-17 cost integration — their contracts add widgets via this contract's ladder + registry, never ad hoc); PHASE-15 VERDICT. **Stop:** unaccounted chartered KPI (built/deferred/declined — counted). |

## 8. Deliverables

- The BOD app: registry-declared widgets over owning read-calls, certified-pattern gating,
  fail-soft rendering, mobile summary-first UI from Phase-10 canon — read-only proven.
- The KPI ladder census (the per-metric single-owner record) + any owner-gated additive
  read-functions in their owning apps (with tests).
- Its test suite in the battery (+ framework amendment); permissions certification evidence.
- `docs/BOD_BUILD_LOG.md`: charter record · ladder census · per-wave evidence · money
  compliance notes · matrices · certification + handoffs.
- U6 docs (app README/GUIDE, index rows, feature-doc routing note); the P11 spec amendment;
  filled Design Record (BOD-D1..BOD-D9).

## 9. Files expected to change

**New (code):** the BOD app tree (views/templates/registry/mixin/tests — NO models) · its app
README + GUIDE. **Updated (code, individually gated):** owning apps' service files ONLY for
approved step-2 additive read-functions (+ their tests) — each with its gate reference ·
`config/config/settings/base.py` (the one registration line) · `config/.importlinter` (layer
row) · the SidebarItemRule seed... **NO** — sidebar rules are DB rows managed via the owner's
Access Control page (runtime), not new migrations: the BOD's rule row is created through the
certified admin UI at execution and recorded in evidence (U14 stays untriggered; a
seed-migration desire = owner + U14). **Docs:** `docs/BOD_BUILD_LOG.md` (new) · status file ·
DOCUMENTATION_INDEX · framework README (battery amendment) · `docs/DEV_DATASET_ARCHITECTURE.md`
(dated `seed_feature bod` amendment per its rules) · PDD amendment register entry (per PDD
change-control, quoted) · this file (Design Record + amendments) · memory. **Runtime:**
scratch worlds for cross-checks/acceptance.

## 10. Files that must never change (touching one = STOP + report)

- Frozen-module code beyond the individually-gated additive read-functions; ALL existing
  views/templates/URLs of certified surfaces (the BOD links to them, never edits them).
- Money single-writer services beyond gated read-function additions — and NEVER their write
  paths (U8); enforcement flags (U10); migrations (none — U14); `production.py`/`.env`.
- PDD BODY TEXT (the amendment register is the entry point, per its own change-control) ·
  ADRs · MANUFACTURING_V1_FREEZE · ARCHITECTURE_V2 · `docs/DOC_STANDARDS.md` ·
  `canonical_manifest.json` · graph/generated artifacts (Phase-9/14 own their lifecycle).
- Existing dashboards' behavior (incl. My Dashboard landing) absent a D9 owner ruling.
- The PRIMARY dev DB (scratch worlds only) · non-DEV data · the 2 stashes · `.git` (U2).

## 11. Documentation update rules

At every sub-phase close, same session: (a) build-log section appended (closed sections
append-only, corrections dated); (b) status-file Phase-15 row + dashboard (battery per wave)
+ "Next action"; (c) **U6 fully applies** (new code): app README + GUIDE at BOD-A, current
per wave; CHANGE_IMPACT_MATRIX per changed file (incl. owning-app docs for step-2 functions);
DOCUMENTATION_INDEX rows; (d) knowledge_sync diff-mode findings dispositioned at every wave
close (the P14 discipline); (e) the PDD amendment-register entry + P11 spec amendment
recorded at their owning documents per their own rules.

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-15
bullet: wave closed, KPI ladder counts, battery arithmetic, log pointer) + MEMORY.md index
line at each sub-phase close. Agents without memory: skip — the build log + status file +
the PDD amendment register are the complete binding record.

## 13. Battery policy

Sequential fresh-DB canonical (U5), **at every code-wave close (BOD-A, BOD-C waves, BOD-D,
and any BOD-E fix wave)**. Arithmetic: entry baseline (status dashboard at BOD-0) + the BOD
suite + step-2 functions' tests in their owning apps, per wave. Suite membership = the BOD-D7
framework amendment (SEED-D4 mechanism). Dev-server restart before browser evidence after
template edits (the standing lesson).

## 14. Regression policy

- Full existing battery green every wave = the frozen-engine do-no-harm proof; step-2
  extractions additionally re-run the OWNING app's suite attention-first (the extracted view
  must behave byte-identically — INERT standard).
- The purity + zero-POST tests permanently pin the read-only property; the permissions
  matrices are certification-grade and their pins join the app's test module.
- Cross-check-vs-authoritative-page is the standing no-second-truth regression instrument
  (re-run at BOD-F over every widget).
- Prior-fix guard list: surfaces the BOD links to are NOT re-certified, but any BOD-E
  evidence contradicting a closed certification = report (never reopen unilaterally).
- Incidental defects = observations → U12 backlog (+U8 stop if money); fixes only via the
  Phase-4 protocol (cross-logged).

## 15. Rollback policy

- The BOD app is additive: a bad wave reverts file-scoped; battery to green; report.
- Step-2 additive functions revert with their BOD consumers in the same diff (never leave an
  orphan extraction half-adopted — the owning view either uses it or the extraction reverts).
- The sidebar rule row is removed via the same admin UI that created it (recorded).
- Scratch worlds disposable; the log + Design Record append-only (dated amendments).
- Session crash mid-wave: next session re-runs the wave's tests + a shell render FIRST,
  reconciles the log, completes or reverts the half-done widget before new work.

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. BOD-0 charter absent/ambiguous, or any BOD-D1..D9 unanswered — building without a
   chartered KPI catalog = invention.
3. U8 anomaly: ANY write path in the BOD or its wave (money or otherwise — the app is
   read-only, period).
4. A KPI demands new business logic (ladder step 3) mid-wave, or an ADR-0009/0011 conflict
   surfaces — owner territory, never improvised.
5. A frozen-module change beyond an individually-gated step-2 addition; a migration or
   base-settings change beyond the registration line; a new shared UI component without its
   gate.
6. Cross-check mismatch that survives one ladder re-resolution (the dashboard would show a
   second truth).
7. Permissions evidence shows a leak or false block on any identity; or the BOD's gating
   pattern diverges from the certified double-gate.
8. Battery red beyond the wave's own new tests' target behavior; knowledge_sync BLOCKER at a
   wave close.
9. Scope creep toward interactivity/state (saved layouts, alerts, polling, caching) —
   Design-Record territory, not wave work.

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-15 row: which BOD-* is next; battery
   arithmetic.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + env + battery amendments) → this
   contract FULLY (esp. the ladder §6.3 + the charter record in the Design Record/log) →
   the PDD amendment-register entry (the product truth for this feature) →
   [PHASE_10_UI_COMPONENT_LIBRARY.md](PHASE_10_UI_COMPONENT_LIBRARY.md) canon +
   `UI_COMPONENTS.md` → `docs/BOD_BUILD_LOG.md` if it exists (absent ⇒ next = BOD-0).
3. Verify read-only: charter + ladder census state; purity tests green in THIS tree before
   any render probing; scratch-world availability (`seed_feature bod` if the scenario is
   live, else seed_factory); identities per cast lists (owner password owner-supplied).
4. Money widgets (BOD-D) = main-thread, U8-hostile, ledger recount discipline — never
   delegated wholesale.
5. Battery environment per framework env facts; browser on :8003 with dev-server restart
   after template edits.
6. Execute exactly ONE sub-phase per §7 (widget waves strictly serial). STOP per §16.
7. Anything inconsistent across status file / charter / ladder / log / this contract →
   report before working (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (BOD-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| BOD-D1 | **Product charter** | OWNER-SUPPLIED at BOD-0: the KPI catalog (what the dashboard shows), audiences, grouping/ordering, navigation placement — recorded through PDD change-control (amendment register/ADR ref). No default exists: an unanswered D1 blocks the phase (nothing is invented) | **✅ "BOD-D1 APPROVED" 2026-07-17.** Charter of record = [BOD_BUILD_LOG §BOD-D1](../BOD_BUILD_LOG.md); PDD amendment-register **entry 6**. Headlines: Owner command center, window-never-engine + specialized-dashboards-continue clarification; V1 = Owner/SA only; sections Attention→Production→Materials→Workers→Financial→Machines(→Other, content deferred); financial focus = upcoming commitments the ERP already owns; **deferred by ruling:** revenue/P&L, delay/threshold rules, manager/accountant tiers, analytics/AI, the future Expense Financial Dashboard |
| BOD-D2 | App home | New app (default name `bod`), BASE settings, topmost import-linter layer, ZERO models (no migrations); widget registry in code | _(pending)_ |
| BOD-D3 | Metric ladder + step-2 gates | §6.3 as written; each step-2 additive read-function individually owner-gated (frozen-module additive change), INERT to existing callers, born in the owning app with tests | _(pending)_ |
| BOD-D4 | Permissions matrix | v1 = SA/owner only; manager/office tiers = dated amendments after Phase-3 verdicts; financial widgets additionally FINANCIAL_ROLES-gated; zero POST routes in v1 | **✅ ANSWERED VIA THE D1 CHARTER (2026-07-17):** Owner/SA only ("workers should never access it"); manager = future versions; money widgets = financially-authorized only; nothing hidden from the Owner |
| BOD-D5 | Refresh/liveness | As-of page load + manual refresh + visible as-of timestamp; NO polling/websockets/cache infra | _(pending)_ |
| BOD-D6 | Performance budget | Per-page query ceiling set here (measured with assertNumQueries-class evidence); aggregate-SQL-only for many-row metrics; budget breaches need an owner-accepted note | _(pending)_ |
| BOD-D7 | Battery membership | BOD suite joins the canonical battery (dated framework-README amendment, SEED-D4 mechanism) | _(pending)_ |
| BOD-D8 | Dataset scenario | `seed_feature bod` added to the P11 spec via dated amendment; owner acceptance runs on seeded scratch worlds | _(pending)_ |
| BOD-D9 | Navigation + landing | Sidebar placement + label; existing My-Dashboard landing UNCHANGED (BOD = destination, not landing) unless the owner rules otherwise here; relationship to existing dashboards = link-down-never-duplicate | **✅ OWNER OVERRIDE VIA THE D1 CHARTER (2026-07-17):** label "Business Operating Dashboard"; a PRIMARY navigation item; **for Owner/SA the BOD BECOMES the default landing after login** — all other roles' landings unchanged; link-down-never-duplicate + the specialized-dashboards-continue clarification |

Date · answered by: **2026-07-17 · owner — BOD-D1 verbatim-approved ("BOD-D1 APPROVED")
after a full vision narration + 16-question interview + one post-approval clarification
(specialized dashboards continue; Expense Financial Dashboard = future roadmap; recorded
same day). D4 + D9 answered THROUGH the charter (quoted above).
2026-07-18 · owner (BOD-A authorization): D2 · D3 · D5 · D6 · D7 · D8 ALL RATIFIED exactly
as proposed** — D2 separate `bod` app, BASE settings, topmost linter layer, zero models/
migrations, registry in code · D3 the Metric Resolution Ladder verbatim (step-2 additive
INERT functions in the owning app; step-3 = STOP for owner; "the BOD must never become the
owner of business calculations") · D5 as-of load + manual refresh + visible "Last Updated";
no polling/websocket/cache · D6 **≤30 DB queries per page, measured; no N+1; exceptions
need explicit owner approval** · D7 BOD suite joins the canonical battery (dated framework
amendment) · D8 `seed_feature bod` per the existing dataset architecture (spec amendment at
its owning document per contract §7 BOD-F).

## Dated amendments

- **2026-07-13 (Campaign Approval Pass, owner-ordered):** §2.1 infra-reality row corrected —
  "no cache layer in the repo" → "in the application" (Redis exists in the production compose
  stack; the application configures no cache). BOD-D5's default and every conclusion stand
  unchanged.

# Evidence note

All build evidence lives in `docs/BOD_BUILD_LOG.md` (created at BOD-0) — contract =
procedure, log = what was chartered, resolved, built, and proven (framework hierarchy rule).
The product truth lives in the PDD amendment register; the metric truth lives in the owning
services; the BOD's own record proves it never claimed either.
