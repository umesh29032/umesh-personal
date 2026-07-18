---
id: docs-bod-build-log
type: receipt
status: active
owner: append-only
scope: campaign
anchors: —
verified: 2026-07-18
---

# BOD BUILD LOG — Campaign Phase 15 (append-only evidence)

> Contract: [campaign_contracts/PHASE_15_BUSINESS_OPERATING_DASHBOARD.md](campaign_contracts/PHASE_15_BUSINESS_OPERATING_DASHBOARD.md)
> (frozen; Design Record = its Appendix A). **The first NEW PRODUCT FEATURE since the
> Manufacturing V1 freeze** — the heaviest truth-locks bind: PDD v1.0 FROZEN (the charter
> enters via its amendment register, never around it) · MANUFACTURING_V1_FREEZE · U8/
> Money-Write STOP · U9 Frozen-Foundation rules · ADR-0009 · ADR-0011.
> **THE BOD IS A WINDOW, NEVER AN ENGINE:** zero business logic · zero writes · zero
> duplicated calculations · every metric has ONE authoritative owner · links DOWN into the
> certified surfaces · the existing service layer stays the only writer.

## BOD-0 — Product charter + gate + ratification — ⏸ CHARTER + DECISION PACK PENDING OWNER (opened 2026-07-17)

### 1. Gate — ✅ PASS (re-verified live this session)

| Gate item | Proof |
|---|---|
| Phase 14 closed · Knowledge Sync certified | KNOWLEDGE_SYNC_LOG §KS-E: "PHASE 14 COMPLETE — KNOWLEDGE SYNC CERTIFIED" + the PHASE_05-family closure — owner-accepted; the locked order's whole 5→14 chain precedes |
| Deployment status advanced | DEPLOYMENT_CAMPAIGN_STATUS Last-updated = the Phase-14 close; "Next: Phase 15 (BOD, BOD-0)" |
| Phase-14 handoffs present | KNOWLEDGE_SYNC_LOG §KS-E.4 — the P15-relevant instrument: `knowledge_sync --diff` after every wave (contract §11(d), the U6 discipline's first live use) |
| PDD + change-control live | `docs/PRODUCT_DESIGN_DOCUMENT.md` FROZEN v1.0 with the amendment register at its top (existing entries: Pattern-Design rename · ADR-0011 · stage-trio · C3-transitional) — the BOD charter's entry point |
| Freeze + money locks live | MANUFACTURING_V1_FREEZE.md · ADR-0009 (cost truth) · ADR-0011 (factory-level salary) · U9 rules · `FINANCIAL_ROLES` in `permission_service` |
| Phase-10 UI canon live | UI_COMPONENTS.md = the certified library (19-family canon, 127-token registry, frozen families) — the compose-from-canon source |
| Certified dashboard landscape | My Dashboard (`inventory:my_dashboard`, exempt landing) · Operations · Manufacturing Costing · raw_materials ×2 · Barcode Dashboard · Payroll overview — the link-down targets, all certified |
| Dataset/verify/sync instruments | P12 seeder (`seed_factory`/scratch worlds; the D8 `seed_feature bod` amendment path = DEV_DATASET_ARCHITECTURE §12) · P13 verify (route census grows, recorded) · P14 sync (23 detectors live) |
| Gating pattern live | SidebarItemRule (21 rows — the anchor) + `SidebarAccessMiddleware` double-gate + AJAX fork + dispatch-mixin precedent |
| Baselines | Battery entry **1745/1745** (the terminal P14 baseline, this session) · route census: graph 528 url nodes (482 named) · git `49404001` · 2 stashes · primary sentinels ledger 170/Σ₹10,880.25 · users 48 · SidebarItemRule 21 · dev.min 0 |

### 2. Reconciliation (inherited contracts → what Phase 15 actually consumes)

| Inherited | Guarantee consumed | Interface/artifact | Out of scope here |
|---|---|---|---|
| PDD v1.0 FROZEN | product truth + its change-control | the amendment register = the D1 charter's entry point (entry quoted on ratification) | PDD body edits (never) |
| MANUFACTURING_V1_FREEZE + U9 | frozen engine stays untouched; settlement-only money; read-only snapshots; mobile summary-first | read-only imports of frozen services; step-2 additive functions ONLY with individual owner gates | any engine/behavior change |
| U8 Money-Write STOP | the BOD writes no money — proven per money widget | ledger recount discipline at BOD-D; purity + zero-POST pins from BOD-A | any write path, period |
| ADR-0009 / ADR-0011 | cost-truth laws every money KPI must obey | per-widget compliance notes (no processing_cost+labor sums; factory expense never per-Adda) | new cost aggregation (ladder step 3 → owner/ADR) |
| Phase 10 | certified component canon + tokens + frozen families | compose-from-canon citations per widget; dashboard-tile families from the §6.2 taxonomy | new shared components without the gate |
| Phase 3 / RBAC | ONE visibility predicate; double-gate pattern; FINANCIAL_ROLES | dispatch mixin + SidebarItemRule row + middleware fork; per-identity matrices (certification-grade) | office-role tiers (dated D4 amendments post-Phase-3-verdicts) |
| P11/P12 | deterministic worlds for cross-checks + acceptance | `seed_factory` today; `seed_feature bod` via the dated spec amendment (D8) | seeding mechanics changes |
| P13 | verification instrument | route-census delta recorded; optional BOD-visible goldens = owner choice | new invariants |
| P14 | drift instrument | `knowledge_sync --diff` at every wave close; findings dispositioned | regeneration (the stale residue stays owner-ruled) |
| P16/P17 (forward) | their contracts ADD widgets via THIS ladder + registry | the registry + ladder become their display interface | building their widgets now |

**Ambiguities RECORDED (not resolved — §16 discipline):**
- **A-1 · The product charter does not exist in the repository** (by design): the master
  index's one line is the only product statement. BOD-D1 is the owner's to supply — the
  phase is BLOCKED on it (nothing is invented). This is the D1 gate, listed here for
  completeness.
- **A-2 · SidebarItemRule row vs the frozen census anchors:** the contract creates the BOD's
  sidebar rule via the certified Access Control UI at execution (no migration) — on the
  PRIMARY dev DB, moving the SidebarItemRule anchor 21→22 and the campaign's 34-anchor
  census. Needs a disclosed anchor-update protocol at BOD-A (owner-visible, evidence-logged)
  — recorded, not decided.
- **A-3 · Browser-evidence dependencies:** SA browser flows need the owner-run dev server
  (:8003) + the owner-supplied password (never in repo docs) — an execution dependency for
  BOD-A/E sessions, recorded.
- **A-4 · PDD register entry format:** the charter entry follows the register's existing
  entry style (dated, owner-attributed, quoted verbatim); the executing agent records it ON
  the D1 ruling — mechanics noted, content strictly owner's.

### 3. Charter (the authoritative execution frame — from the frozen contract, condensed)

- **Objective:** the owner's operating overview — "how is the factory doing right now?" —
  aggregating what the certified system already knows (production · money · materials ·
  machines) through existing services, read-only, mobile-first, never a second truth.
- **Terminology:** *widget* = (KPI id · owning read-call · certified component · gate
  predicate · responsive strategy · drill-down target); *ladder* = the §6.3 metric
  resolution (1 call-existing → 2 gated-extraction → 3 STOP/owner); *registry* = the
  in-code widget declaration (zero models).
- **Architecture:** new `bod` app (BASE settings, topmost linter layer, NO models/
  migrations); registry-declared widgets; fail-soft rendering (error tile, never a 500);
  aggregation in the OWNING service; refresh = as-of load + manual refresh + visible
  timestamp (no polling/websockets/cache).
- **Boundaries/invariants:** the six window-clauses (normative §4) · purity + zero-POST
  from BOD-A · charter fidelity (nothing proposed onto the dashboard uninvited) · frozen
  modules = read-only imports + individually-gated additive functions only · money widgets
  = their own U8-hostile wave · certification-grade permissions.
- **Inputs:** the D1 charter (owner) · certified services/pages (metric truth) · Phase-10
  canon · seeded scratch worlds · the gating pattern. **Outputs:** the BOD app + KPI ladder
  census + permissions certification + this log + U6 docs + the P11 spec amendment + the
  PDD register entry.
- **Implementation waves:** BOD-A skeleton/gates/purity-first → BOD-B the ladder census
  (NO wiring) → BOD-C non-money widget waves (serial) → BOD-D the money wave (U8-hostile,
  ledger recount) → BOD-E permissions + UI certification (matrices · 360/768/1280 ·
  canon census) → BOD-F certification + handoffs (16/17/18/19) + VERDICT.
- **Battery strategy:** entry **1745/1745**; BOD suite joins via the BOD-D7 dated framework
  amendment; battery at every code-wave close; owning-app suites attention-first on step-2
  extractions; `knowledge_sync --diff` dispositioned at every wave close.
- **Documentation touchpoints:** this log · app README/GUIDE (BOD-A) · CHANGE_IMPACT_MATRIX
  · DOCUMENTATION_INDEX · framework README (D7) · DEV_DATASET_ARCHITECTURE dated amendment
  (D8) · PDD amendment register (D1) · status + memory per wave.
- **Phase/deployment interfaces:** P16/P17 add their widgets via this ladder + registry
  (never ad hoc) · P18 syncs the feature docs (graph → cards) · P19–21: the BOD ships with
  the system; route/smoke expectations grow; no BOD-specific deploy steps by default.

### 4. ⏸ Decision pack — BOD-D1..BOD-D9 (defaults binding unless overridden; → contract Appendix A)

| # | Decision | Default in one line | Notes |
|---|---|---|---|
| **BOD-D1** | **Product charter** | **NO DEFAULT — OWNER-SUPPLIED.** Required before anything is built: **(a)** the KPI catalog — the list of things the dashboard shows, in your words (e.g. "today's production count", "unsettled addas", "worker dues", "roll stock") · **(b)** audiences (owner-only? manager?) · **(c)** grouping/ordering of tiles · **(d)** navigation placement + sidebar label · recorded through the PDD amendment register | an unanswered D1 BLOCKS the phase — nothing is invented; each KPI then runs the §6.3 ladder |
| BOD-D2 | App home | new app `bod`: BASE settings, topmost import-linter layer, ZERO models/migrations, widget registry in code | the P12/P13 layout precedent |
| BOD-D3 | Metric ladder + step-2 gates | §6.3 as written; every step-2 additive read-function individually owner-gated, INERT to existing callers, born in the owning app with tests | the no-second-truth mechanism |
| BOD-D4 | Permissions | v1 = SA/owner ONLY; all other roles refused; financial widgets additionally FINANCIAL_ROLES-gated; ZERO POST routes | office/manager tiers = dated amendments later |
| BOD-D5 | Refresh/liveness | as-of page load + manual refresh + visible as-of timestamp; NO polling/websockets/cache | no cache infra exists in the app |
| BOD-D6 | Performance budget | per-page query ceiling ratified here (proposal: ≤ 30 queries for the full dashboard, measured assertNumQueries-style; aggregate-SQL-only for many-row metrics); breaches need an owner-accepted note | measured, not vibes |
| BOD-D7 | Battery membership | BOD suite joins the canonical battery (dated framework-README amendment, SEED-D4 mechanism) | |
| BOD-D8 | Dataset scenario | `seed_feature bod` via a dated DEV_DATASET_ARCHITECTURE §12 amendment; owner acceptance on seeded scratch worlds | |
| BOD-D9 | Navigation + landing | sidebar placement per D1; **My-Dashboard landing UNCHANGED** (BOD = destination, not landing); link-down-never-duplicate to every existing dashboard | changing landing = an explicit ruling here |

**Rulings requested — D1 is the phase gate.** On ratification: the PDD register entry is
recorded (quoting your charter verbatim), answers land in the contract's Appendix A (dated),
the BOD-D7 battery amendment is recorded, and BOD-A (skeleton + gates + purity-first) is
authorized — owner-gated.

### 5. BOD-0 accounting

- **Git:** HEAD `49404001` · 0 staged · 2 stashes — reads only.
- **Battery:** **1745/1745** entry baseline (the terminal Phase-14 run, this same session);
  NOT re-run at BOD-0 (zero code — charter only).
- **Repository:** working tree = the standing uncommitted campaign state; knowledge
  artifacts at the KS-C-I1-amended baseline (graph `203547859d65…`; 558 stale outputs = the
  owner-ruled expected state).
- **Primary DB anchors:** ledger 170/Σ₹10,880.25 · users 48 · SidebarItemRule 21 (the
  A-2-relevant anchor) · dev.min 0 — read-only census only.
- **Implementation status: NOTHING implemented** — no app, no views, no registry, no tests.
  BOD-A is gated on the owner's D1 charter + D2..D9 rulings.

### 6. Dated note — owner engineering ruling received 2026-07-17 (mid-BOD-0, binding on this phase's implementation)

**MOBILE-FIRST UI STANDARD (permanent):** every new UI in Phase 15 and every later phase =
mobile-first + desktop-friendly + tablet-friendly + responsive on all breakpoints; certified-
library reuse only; no horizontal scrolling; touch-friendly; accessible; **certification
minimum = mobile + tablet + desktop layout verification, else NOT production-ready.**
Engineering rule only — no product-charter/business-logic change; the BOD-D1 interview
remains pending. Recorded: CLAUDE.md rule 11 (strengthened) · UI_COMPONENTS.md (dated
ruling block) · memory. ⚠ The ruling's "existing Zeta Rule" reference has NO on-record
definition anywhere in the repo — flagged for owner clarification, never guessed.

## BOD-D1 — THE OWNER PRODUCT CHARTER — ✅ "BOD-D1 APPROVED" 2026-07-17 (recorded verbatim-faithful; PDD amendment-register entry 6)

Captured across the owner's vision narration + the 16-question interview + the final
clarification, and approved with the exact phrase **"BOD-D1 APPROVED"**. The owner's intent
below is BINDING product truth (PDD register entry 6 points here as the charter of record).

### D1.1 Identity & objective (owner's words)
The **Owner's Business Operating Dashboard** — NOT another operational/production/inventory/
financial page. *"Whenever I log into my ERP, I should understand the health of my complete
business within a few seconds"* — one question: **"How is my business doing right now?"** An
**Owner Decision Dashboard**, the ERP's **command center**, used every day, telling the owner
*"where my attention is required."* Desktop + mobile equally (the 2026-07-17 permanent
mobile-first engineering ruling applies).

### D1.2 Window, never engine (owner's law, verbatim intent)
Never a working screen · never duplicates business logic · never a calculation engine ·
never another reporting system · every module keeps owning its logic and workflows · the BOD
reads truth and presents the overview · **one source of truth per KPI** · no different
numbers in different places · NO editing from the dashboard (adding an expense happens in
the Expense module; the dashboard reflects it because the module owns the data).
**Owner clarification (2026-07-17, post-approval, recorded same day): the BOD never replaces
SPECIALIZED dashboards — every major module continues owning its own detailed dashboard and
workflows (Production/Expense/Inventory/Warehouse/Payroll/Machine dashboards); the BOD
consumes only HIGH-LEVEL SUMMARIES and provides drill-down navigation into them.**

### D1.3 Access
V1 = **Owner / Super Admin ONLY** ("the highest-level business dashboard; workers should
never access it"). Manager access = future versions. Manager + accountant dashboards =
planned-but-intentionally-deferred; perfect the Owner Dashboard first.

### D1.4 V1 KPI catalogue + the owner's definitional rulings
| # | Section | V1 content | Owner ruling |
|---|---|---|---|
| 1 | **Business Attention / Critical Alerts** | items ALREADY tracked by the ERP needing the owner (pending settlements; genuinely-blocked/ERP-tracked states) | "I do not want artificial business rules invented during Version 1" |
| 2 | **Production** | active Addas · blocked-if-ERP-tracked · today's production | "Delayed" (stuck-N-days class) = DEFERRED (new rule) |
| 3 | **Raw Materials & Warehouses** | current stock; owner identifies shortages manually in v1 | configurable per-material minimum stock levels = FUTURE; when configured, the dashboard uses them; nothing hardcoded |
| 4 | **Workers** | who is currently working (EXISTING assignments only) · completed work · expected payment · pending settlements | no new attendance/productivity rules |
| 5 | **Financial Overview** | current month's expenses · factory expenses · **upcoming commitments: expected worker payouts (month) · monthly salary obligations · outstanding worker payments · outstanding advances** (+ any other certified obligations the ERP already owns) | **Revenue / complete P&L = DEFERRED** — "if the ERP does not yet own revenue information, the dashboard should not invent it"; full P&L when the ERP officially owns those entities |
| 6 | **Machines** | simple visibility only, if already available | advanced machine analytics deferred |
| 7 | **Other Business Modules** | content = a deferred owner micro-decision (surface at the BOD-B ladder census: summaries vs links vs drop) | the long-term philosophy: every major module is EVALUATED for BOD inclusion as the ERP grows |

### D1.5 Organization & navigation
Section order: **Attention/Alerts → Production → Materials & Warehouses → Workers →
Financial → Machines → Other.** Nothing collapsed by default; the most important information
always immediately visible. Sidebar label: **"Business Operating Dashboard"**; a PRIMARY
navigation item. **Landing (explicit owner override of the contract default → BOD-D9): for
Owner/SA the BOD becomes the DEFAULT LANDING PAGE after login; all other roles' landings
unchanged.**

### D1.6 Financial visibility
Money widgets = financially-authorized users only (v1 effectively Owner/SA). Nothing hidden
from the Owner — the complete business picture, always.

### D1.7 V1 boundary + roadmap
V1 priority: Alerts → Production → Inventory/Warehouses → Workers → Financial Summary →
Machines. **Deferred by ruling:** anything requiring new business logic, AI, forecasting,
analytics, trends, predictions, or new business entities. **Expense-module roadmap
(future, NOT BOD-A work):** a dedicated Expense Financial Dashboard (analyze/trends/compare/
categories/manage) evolves independently; the BOD later consumes its summaries. **Long-term:
the BOD continuously evolves into the single Owner Command Center while modules keep their
logic, workflows, calculations, and detailed dashboards.**

### D1.8 Decision-pack state after this recording
- **BOD-D1 ✅ recorded** (this section; PDD register entry 6; Appendix A).
- **Charter-derived answers recorded:** BOD-D4 (Owner/SA-only + financial gating — D1.3/D1.6)
  · BOD-D9 (label/position/landing OVERRIDE — D1.5) · BOD-D5's product face (numbers current
  at load, refreshed on return — consistent with the as-of-load default).
- **Still awaiting formal ratification at BOD-A authorization:** BOD-D2 (app home) · BOD-D3
  (ladder mechanics) · BOD-D6 (query ceiling — the ≤30 proposal) · BOD-D7 (battery
  amendment) · BOD-D8 (dataset scenario) — engineering defaults presented at BOD-0, not yet
  owner-answered.

## BOD-A — Skeleton + gates + purity — ✅ DONE 2026-07-18 · BATTERY 1758/1758

**Owner authorization 2026-07-18 + full ratification: D2 · D3 · D5 · D6 (≤30 queries) ·
D7 · D8 — recorded in Appendix A; the BOD-D7 battery amendment recorded (framework README:
`bod` joins the FIRST suite → the 10-app list).** Zero KPIs, zero widgets, zero business
data — exactly the ordered scope.

### 1. What landed

| Piece | Content |
|---|---|
| `config/bod/` (NEW app; ZERO models/migrations/forms) | `apps.py` · `mixins.py` (`BODAccessMixin`: Owner/SA only; anon → login redirect, authenticated non-SA → 403) · `registry.py` (the §6.2 Widget tuple + the charter-fixed SECTIONS order; **REGISTRY EMPTY by owner order**) · `views.py` (GET-only TemplateView, `http_method_names` pinned; BOD-D5 as-of timestamp) · `urls.py` (ONE route `bod:dashboard`) · `templates/bod/dashboard.html` (mobile-first shell per the 2026-07-17 permanent ruling: 1-col phone → 2-col ≥768 → 3-col ≥1280 · 44px touch refresh · tokens-only page-scoped CSS · "Last Updated" + manual Refresh · honest per-section empty states) |
| Licensed wiring | `base.py` +1 registration line · root `config/urls.py` +1 mount (`/bod/`) · `.importlinter` (+root pkg; layer `verification : bod` below devseed) · **sidebar = a CODE MenuItem in the SIDEBAR registry** ('Business Operating Dashboard', SA-only predicate, top of Main — the documented new-feature path; string url_name, no import, layering clean) |
| Tests (13 — the bod suite) | purity (zero ORM/instance writes · modelless shape · BASE registration) · **zero-POST** (route census = 1 · `POST → 405`) · the BOD-D4 matrix (SA 200 with all six sections · manager/worker/accountant/listing **403** · anon → login w/ `next=/bod/`) · **read-only render + the ≤30-query BOD-D6 pin** (runtime row-count identity around a GET) · empty-registry pin · charter section-order pin · Widget-shape pin · SA-only sidebar-predicate pin |

**A-2 RESOLVED WITHOUT TOUCHING THE ANCHOR:** the sidebar item is CODE-predicate-gated
(SA-only visibility); no SidebarItemRule row was created — that row remains the OWNER's
Access Control action (the certified pattern's optional panel-gate; unmanaged URLs fall to
the view mixin, per the middleware's own pass-through contract). **SidebarItemRule = 21,
unchanged.**

### 2. Live browser-class evidence (the owner's RUNNING dev server :8003, real login flow)

- **Anonymous:** `GET /bod/` → **302 → /app/?next=/bod/** ✓
- **Super Admin (real password login):** `GET /bod/` → **200** — all six charter sections
  rendered · "Last Updated: 18 Jul 2026, 00:31" visible · 6 honest "No widgets yet" empty
  states · the sidebar shows "Business Operating Dashboard" ✓
- **Non-SA (cutting master, real login):** `GET /bod/` → **403**; their My Dashboard 200;
  their sidebar contains ZERO "Business Operating Dashboard" ✓
- Disclosures: my first login attempt used the wrong form field (`email` vs `username`) —
  one failed attempt logged by the security throttle, then success; live probes wrote
  normal session rows on the owner's running server (read-only GETs otherwise).
  Full 360/768/1280 screenshot pass = BOD-E per contract (the shell's responsive CSS is
  code-pinned mobile-first meanwhile).

### 3. The Phase-14 discipline's first live catch (dispositioned in-wave)

The SYNC-D4 build-red guard FIRED during the battery — exactly as designed: **(a)** the
knowledge graph was stale vs the new `bod` app (INV-8 floors) → the routed venue remedy =
the routine Phase-8 rebuild (`203547859d65…` → intermediate `e36c119b…`); **(b)** the
rebuilt graph then flagged **`app:bod` as a doc island (INV-7)** — the system ENFORCING U6
— fixed by writing the owed `config/bod/README.md` (+ GUIDE) and rebuilding once more →
**final graph hash `bb3c2d7149f5…`** (13 apps · 529 urls · 926 docs · 230 views). Guards
green. The 558 generated outputs remain owner-accepted-stale (the KS-C-I1 option-(a)
ruling; regeneration stays deferred). One conscious test-pin bump recorded:
`test_a360_overview` 75 → 76 queries (+1 SidebarItemRule managed-check per render — the
inherent cost of ANY sidebar registry addition; dated comment in the pin, the 74→75
precedent's exact pattern).

### 4. Certification

- **Battery — NEW BASELINE 1758/1758** (BOD-D7 shape: **10-app 1015** (190.7s, incl. bod 13)
  + patterns_ai 528 (159.0s) + devseed 137 (45.5s, knowledge guards green post-rebuild) +
  verification 78 (19.8s)). Arithmetic: 1745 + 13 ✓.
- **Primary EXACT:** ledger 170/Σ₹10,880.25 · users 48 · **SidebarItemRule 21** · dev.min 0.
  Git `49404001` · 2 stashes · zero migrations · zero POST surfaces · zero KPIs wired.

**Next: BOD-B — the Metric Resolution Ladder census for EVERY chartered KPI (NO wiring) —
owner-gated. Carried: the section-7 "Other Business Modules" micro-decision surfaces there.**

_BOD-A closed 2026-07-18._

### Dated owner addendum — 2026-07-18 (received at BOD-B authorization; roadmap, recorded verbatim-faithful)

**THE BOD AS THE ERP'S SEMANTIC LAYER (long-term):** every KPI carries a PERMANENT
definition — `KPI · Owner Module · Source Service · Business Rule · Drill-down` — the
owner's own example format. Effect on this phase: the BOD-B census below IS that semantic
layer's first edition (a permanent artifact, not a one-time build plan), and the in-code
widget registry remains its machine-readable home. No v1 scope change.

## BOD-B — THE BUSINESS INTELLIGENCE MAP (metric resolution census) — ✅ COMPLETE 2026-07-18 · ⏸ AWAITING OWNER APPROVAL

**Method:** three parallel module readers (production · materials/machines · dashboards/
patterns/storefront) + the ENTIRE money domain verified MAIN-THREAD (function bodies read:
`payroll_totals` · `settlement_queue` · `monthly_totals` · `worker_balance` · advance pool
— per the Money-Write/audit-honesty rules); every load-bearing row re-verified by direct
reads. ZERO code written. This census = the semantic layer's FIRST EDITION (the owner's
2026-07-18 addendum) — a permanent artifact.

### 1. KPI census + Metric Resolution Ladder (the semantic layer, v1 rows)

Legend: L1 = reuse existing certified service/function · L2 = owner-gated INERT additive
extraction into the OWNING app (truth today lives inline in a certified view) · L3 = owner
decision (no certified truth exists). Frozen? = touches a frozen-era module (all L2 rows do
— each needs its individual gate; all are INERT extractions: the view calls the same new
function). Every drill-down = an existing certified page.

| # | KPI | Business meaning | Owner module | Source (verified file:line) | Certified screen | Ladder | Frozen/INERT | Drill-down | Ambiguity |
|---|---|---|---|---|---|---|---|---|---|
| A1 | Settlements ready | addas fully payable-complete, money waiting to be settled | Expense | `adda_settlement_service.settlement_queue()['ready']` (:178 — per-adda expected ₹, workers, lines) | settlements queue page | **L1** | no/— | `expense:adda-settlement-list` | Σ-of-ready = presentation-sum of owner rows (see R-2) |
| A2 | Settlements blocked | addas whose settlement waits on named open payable stages | Expense | same, `['waiting']` (incomplete stage names included) | same | **L1** | no/— | same | — |
| A3 | Stalled addas | open stage unmoved > STALLED_ADDA_DAYS (setting, default 3 — an EXISTING configurable rule, base.py:220) | Production | `operations_digest.stalled_stage_records()` (:17 — THE single stalled path) | `production:dashboard` digest + `production:stalled-addas` | **L1** | no/— | `production:stalled-addas` | none — the charter's "no new delay rule" is satisfied: the rule already exists |
| A4 | Pending worker reports | workers on the hook (assigned/in-progress on open stages) | Production | `operations_digest.pending_report_tasks()` (:35) | digest + `production:pending-reports` | **L1** | no/— | `production:pending-reports` | — |
| P1 | Active addas | in-progress adda count | Production | `operations_digest()` `active_addas` (:73) | `production:dashboard` | **L1** | no/— | `production:dashboard` | — |
| P2 | On-hold addas | the ERP-tracked "blocked" status (admin/manual; no service writes it) | Production | inline `AddaDashboardView` (:50) — status=ON_HOLD count | `production:dashboard` KPI | **L2** (tiny) | production/INERT | `production:dashboard` | — |
| P3 | Completed today (addas) | addas finished today | Production | `operations_digest()` `completed_today` (:74-77) | digest | **L1** | no/— | `production:dashboard` | — |
| P4 | Today's production PIECES | Σ good pieces completed today | Production | **NO certified truth exists** (all good_quantity aggregates are per-worker-all-time or per-adda; none date-scoped) | — | **L3 OWNER** | — | — | define: pieces-today = new derivation; v1 alternative = P3 |
| P5 | In-progress per stage | where the factory's addas sit right now | Production | inline `AddaDashboardView` stage_breakdown (:60-74) | `production:dashboard` chips | **L2** (optional) | production/INERT | `production:dashboard` | owner: wanted on BOD v1? |
| M1 | Roll stock counts | total / available / damaged / used rolls | Raw Materials | inline `ClothDashboardView` (:110-114) | `raw_materials:cloth-dashboard` | **L2** | raw_materials/INERT | `raw_materials:cloth-dashboard` | counts only (no kg anywhere — R-4) |
| M2 | Stock by type×color | the buying-decision pivot | Raw Materials | inline pivot (:120-148) | same | **L2** (or drill-only v1) | raw_materials/INERT | same | owner: summary tile + drill, or full pivot on BOD? |
| M3 | Stock by warehouse | per-StorageLocation counts ("which warehouse needs attention") | Raw Materials | inline by-location (:151-167) | same | **L2** | raw_materials/INERT | same | — |
| M4 | Low stock / needs purchase | — | — | **threshold concept confirmed ABSENT everywhere** | — | ruled FUTURE by charter | — | — | none — v1 = M1-M3 + owner judgment (as ruled) |
| W1 | Who is working now | workers currently on open work + machine holders | Production + Machines | `pending_report_tasks()` distinct workers (L1) + `machine_service.register_counts()['assigned_now']` (:42-50) | pending-reports page + `machines:list` | **L1** | no/— | `production:pending-reports` / `machines:list` | "distinct workers" = presentation-distinct of owner rows |
| W2 | Completed work | what work finished (owner's words — grain undefined) | Production | per-worker all-time exists (`payroll_service.worker_production_stats` :292); NO global "completed work today/recent" aggregate | worker pages | **L3 OWNER** (meaning) | — | — | choose: (a) reuse P3 adda-count, (b) recent-completions list = new derivation |
| W3 | Expected payment | money workers will receive when ready settlements settle | Expense | `settlement_queue()['ready']` per-adda `expected` (guard-correct, PA-11-2) | queue page | **L1** | no/— | `expense:adda-settlement-list` | Σ = presentation-sum (R-2) |
| W4 | Pending settlements | = A1 | Expense | = A1 | = A1 | **L1** | — | = A1 | dedupe with A1 on the board |
| F1 | Month factory expenses (total) | current month's FactoryExpense | Expense | `expense_service.monthly_totals(y,m)` (:107 — total/count/by_category, void-aware) | my_dashboard mgmt expense digest + expense pages | **L1** | no/— | expense module | "current month's expenses" resolved to the CERTIFIED truth (FactoryExpense); anything broader = R-5 |
| F2 | Month expenses by category | rent/electricity/salary/other split (PDD §21-locked set) | Expense | same, `by_category` | same | **L1** | no/— | expense module | — |
| F3 | Expected worker payouts | = W3 total | Expense | = W3 | = W3 | **L1** | — | = W3 | — |
| F4 | Monthly salary obligations (upcoming) | what monthly-basis workers will cost this month | — | **NO certified owner**: `User.salary` = informational prefill ONLY (L-3 ruling, expense/views.py:478); ADR-0011 salary = FactoryExpense WHEN RECORDED | — | **L3 OWNER** | — | — | v1 certified alternative = F2's salary category (salary PAID this month) |
| F5 | Outstanding worker payments | Σ credits − Σ debits, factory-wide (Earned-not-yet-paid) | Expense | `payroll_service.payroll_totals()['pending_payable']` (:32 — built FOR the digest) | `expense:payroll-overview` + digest | **L1** | no/— | `expense:payroll-overview` | — |
| F6 | Outstanding advances | Σ given − Σ recovered (reversal-aware, PA-12-A) | Expense | `payroll_totals()['advance_exposure']` | same | **L1** | no/— | `expense:payroll-overview` | — |
| MC1 | Machine register counts | total / active / maintenance / assigned-now | Machines | `machine_service.register_counts()` (:42-52 — PDD §25 "admin dashboard counts") | `machines:list` | **L1** | no/— | `machines:list` | — |
| MC2 | Machine holders | who holds which machine (open windows) | Machines | `machines_with_holder()` (:21) + `open_assignment_for` (:33) | `machines:list` | **L1** | no/— | `machines:list` | v1 = counts only vs holder list — owner taste at BOD-C |
| O1-O3 | Section 7: Other modules | lightweight summaries/nav cards (owner ruling 2026-07-18: KEEP; grows with the ERP) | patterns_ai · storefront · tracking | nav cards = zero data; optional trivial counts (e.g. `intelligence_service.factory_kpis` markers_total :121; storefront model counts; tracking `tracking:dashboard` totals) | their own pages | **L1/none** | no/— | `patterns_ai:home` · `storefront:product_list` · `tracking:dashboard` | counts vs pure nav = owner taste at BOD-C |

**Ladder totals: 17 × L1 · 4 × L2 (P2 · P5 · M1+M3 · M2) · 3 × L3 owner decisions (P4 ·
W2 · F4).** Deferred-by-charter confirmed intact: revenue/P&L (no revenue entity — verified
none) · low-stock thresholds (verified absent) · analytics/AI.

### 2. Business Truth Ownership Map (the BOD owns NONE)

| Module | Owns (the truths above + their writers) |
|---|---|
| **Production** | adda lifecycle/status/stages · stalled + pending-report predicates (`operations_digest`) · WST/WSC production truth · A360 per-adda board · frozen per-stage processing cost (`cost_service`, ADR-0009 surface = `production:costing`) |
| **Expense/Payroll** | THE money boundary: ledger (credits/debits/balances) · settlement lifecycle + queue + expected ₹ · advances pool · FactoryExpense (incl. salary category, ADR-0011) · payroll totals |
| **Raw Materials** | roll stock/status/consumption · type/color/storage masters · roll history |
| **Machines** | register + possession windows (zero-₹ app) |
| **Pattern Intelligence** | pattern definitions/markers/yield (PI-vs-ERP boundary) |
| **Storefront** | public content (ADR-0008 commerce wall stands: NO revenue/orders anywhere) |
| **Tracking** | barcode batches/statuses/exports |
| **BOD** | **NOTHING** — registry + presentation + gates only |

### 3. Specialized-dashboard review (consume summaries · link down · never duplicate)

| Dashboard | Owns/displays | BOD consumes | NEVER duplicated on BOD |
|---|---|---|---|
| `production:dashboard` (Operations, mgmt landing) | KPIs + stage chips + recent addas + history + the 6-tile digest | the digest numbers (A3/A4/P1/P3/F5/F6 — one call) | the recent-addas table, history log, date filters |
| `inventory:my_dashboard` | personal work board (+ mgmt month-expense digest) | nothing (stays the personal landing) | worker-scoped boards |
| `production:costing` | per-adda frozen cost + variance (ADR-0009 page of record) | link only in v1 (cost aggregates = ADR-0009 territory) | any cost math |
| `expense:payroll-overview` | per-worker money board + totals | payroll_totals numbers | the per-worker table |
| `expense:adda-settlement-list` | the queue (ready/waiting) + settlement history | queue counts + expected ₹ | per-settlement lifecycle UI |
| `raw_materials:dashboard` + `cloth-dashboard` | stock counts · pivot · by-location · history | the (L2-extracted) summary counts | the pivot detail + history feed |
| `machines:list` | register + holders + assign panel | `register_counts()` | the assign workflow |
| `tracking:dashboard` | barcode totals/status per adda | optional O3 count/nav | per-adda barcode drill |
| patterns_ai pages | 5-station rail, markers, yield | optional O1 count/nav | any PI analytics |

### 4. Drill-down map — every v1 tile lands on a certified page (column 9 above; zero dead-ends)

### 5. Step-2 extraction list (each = ONE owner gate; INERT: the certified view switches to the same new function — one calculation, two consumers)

| Gate | New additive read-function (in the OWNING app) | Extracted from | Consumers after |
|---|---|---|---|
| G-1 | `raw_materials`: stock summary counts (total/available/damaged/used) | `ClothDashboardView` :110-114 | cloth-dashboard view + BOD (M1) |
| G-2 | `raw_materials`: by-location stock counts | same view :151-167 | same + BOD (M3) |
| G-3 | `raw_materials`: type×color pivot (only if the owner wants M2 ON the BOD; else drill-only, no gate) | same view :120-148 | same + BOD (M2) |
| G-4 | `production`: on-hold count (+ stage-breakdown if P5 chartered) | `AddaDashboardView` :49-74 | operations dashboard view + BOD (P2/P5) |

### 6. Step-3 OWNER DECISIONS (nothing built until ruled)

1. **P4 today's-production-pieces:** no certified truth. Options: (a) v1 uses P3
   (completed-addas-today, certified) and pieces-today is DEFERRED; (b) approve a new
   date-scoped Σ(good_quantity) derivation born in production (a NEW business aggregate).
2. **W2 "completed work" meaning:** (a) fold into P3; (b) approve a "recent completions"
   list (new derivation); (c) defer.
3. **F4 monthly-salary-obligations (upcoming):** no certified owner (`User.salary` is
   informational-only by the L-3 ruling). Options: (a) v1 shows F2's salary-paid-this-month
   (certified) and upcoming-obligations is DEFERRED; (b) promote `User.salary` (or a new
   config) to a certified obligation source — an ADR-class decision.

### 7. Risks discovered

- **R-1 Query budget vs `settlement_queue()`:** it loops payable stage-records per adda
  (correctness-first design) — on a large queue this could strain the ≤30-query page
  ceiling. Mitigation path if measurement shows it: an owner-gated L2 totals-aggregate in
  expense; NOT assumed now — BOD-C measures first (D6 law: measured, not vibes).
- **R-2 Presentation-sum boundary:** Σ over `settlement_queue()['ready']` expected values =
  arithmetic over owner-service rows (no rule invented). Recorded as the ladder's
  presentation-sum convention; the alternative (a totals key inside expense) = an optional
  gate if the owner prefers service-side totals.
- **R-3 `completed_today` timezone note:** digest uses `completed_at__date` vs now-date —
  the certified page's own semantics; BOD shows the SAME number by construction (single
  source, so no divergence is possible).
- **R-4 No kg/weight stock truth:** both RM dashboards count ROLLS only; weight aggregates
  exist nowhere. If the owner ever wants kg-stock, that's a new derivation (L3 then).
- **R-5 "Current month's expenses" breadth:** resolved to the certified FactoryExpense
  truth (F1). A broader "total money out this month" (settlement payments + expenses)
  would need a month-scoped ledger aggregate that no service owns today → would be L2/L3.

### 8. Recommended BOD-C implementation order (serial waves)

1. **C-wave-1 (pure L1, digest-backed):** A3 · A4 · P1 · P3 (one `operations_digest()`
   call = four tiles) + A1/A2 counts + MC1 — the cheapest, highest-value board.
2. **C-wave-2 (materials, after gates G-1/G-2):** M1 · M3 (+ M2 per owner taste).
3. **C-wave-3 (production extras + section 7):** P2 (after G-4) · W1 · O1-O3 cards.
4. **BOD-D (money wave, U8-hostile, own wave):** F1 · F2 · F5 · F6 · W3/F3 (+ any ruled
   step-3 outcomes) — ledger recount discipline, FINANCIAL_ROLES gating, ADR-0009/0011
   notes per widget.

**⏸ STOPPED — awaiting the owner's BOD-B review: the 3 step-3 rulings (§6), the 4 step-2
gates (§5), and the taste calls flagged in-table (M2 depth · MC2 list-vs-counts · O-counts
vs pure nav · P5). BOD-C starts only on explicit approval.**

_BOD-B census composed 2026-07-18._

### 9. Owner disposition — BOD-B APPROVED 2026-07-18 (verbatim rulings)

- **Step-3:** P4 → **Option A** (v1 = Completed Addas Today; pieces-today DEFERRED until a
  certified production aggregate exists) · W2 → **Option C** (Completed Work DEFERRED —
  concept not yet sufficiently defined) · **F4 → DEFERRED with a permanent law:** the
  dashboard must NEVER derive obligations from `User.salary` or any informational field;
  the BOD consumes a certified Payroll-Obligation entity/financial source of truth WHEN the
  ERP officially owns one; no financial calculations invented.
- **Step-2 gates:** G-1 ✅ stock summary counts · G-2 ✅ warehouse summary counts ·
  **G-3 ❌ REJECTED for v1** (type×color pivot stays inside the Raw Materials dashboard;
  the BOD needs high-level summaries only) · G-4 ✅ on-hold count **+ stage chips approved**.
- **Taste:** Machines = **counts only, no holder lists** (widget clicks into the machine
  register) · **Section 7 = navigation cards ONLY, no counts** (future modules may expose
  summaries later).
- **BOD-C authorized** in the exact recommended order (waves 1→2→3); **the Money Wave/BOD-D
  NOT authorized.**

## BOD-C — Non-money widget waves — ✅ COMPLETE 2026-07-18

**Owner order executed exactly:** Wave 1 (digest-backed L1) → Wave 2 (materials after G-1/G-2)
→ Wave 3 (production extras G-4 + Section 7 nav cards). Money Wave NOT touched (BOD-D).
Implementation laws honored: window-never-engine · one source of truth · zero duplicate
calculations · zero business logic in BOD · certified services only · every widget drills
into its owning module.

### 1. Widgets shipped — 12 tiles + 3 nav cards

| Wave | kpi_id | Section | Source (owning service) | Drill-down |
|---|---|---|---|---|
| 1 | stalled-addas | attention | `operations_digest()` (shared per-request cache) | `production:stalled-addas` |
| 1 | pending-reports | attention | `operations_digest()` | `production:pending-reports` |
| 1 | settlements-ready | attention | `adda_settlement_service.settlement_queue()` (len ready) | `expense:adda-settlement-list` |
| 1 | settlements-blocked | attention | `settlement_queue()` (len waiting + top blocking stages) | `expense:adda-settlement-list` |
| 1 | active-addas | production | `operations_digest()` | `production:dashboard` |
| 1 | completed-today | production | `operations_digest()` (owner P4 Option A: Addas, not pieces) | `production:dashboard` |
| 1 | machine-counts | machines | `machine_service.register_counts()` — counts ONLY (owner taste) | `machines:list` |
| 2 | roll-stock | materials | `roll_service.stock_status_counts()` **(G-1 extraction)** | `raw_materials:cloth-dashboard` |
| 2 | stock-by-warehouse | materials | `roll_service.stock_by_location()` **(G-2 extraction)** | `raw_materials:cloth-dashboard` |
| 3 | on-hold-addas | production | `operations_digest.adda_status_counts()` **(G-4 extraction)** | `production:dashboard` |
| 3 | stage-chips | production | `operations_digest.stage_breakdown()` **(G-4; chips tile variant)** | `production:dashboard` |
| 3 | workers-active | workers | presentation-DISTINCT over `pending_report_tasks()` rows + machines assigned_now | `production:pending-reports` |
| 3 | Section 7 | other | **NAV_CARDS — pure links, ZERO counts (owner ruling):** Pattern Intelligence (`patterns_ai:home`) · Storefront (`storefront:product_list`) · Tracking (`tracking:dashboard`) | their own pages |

Registry: `config/bod/registry.py` (12 `Widget` rows + `NAV_CARDS`); adapters:
`config/bod/widgets.py` (thin tile-shape mappers, per-request cache so shared owner calls
run ONCE); renderer: `BODDashboardView._render_widget` fail-soft (one broken owner call →
error tile, never a 500); template: value-tile + chips variant + nav cards, mobile-first
grid (1-col → 2-col ≥768 → 3-col ≥1280; 44px touch refresh; chips wrap on phone).

### 2. Owner-gated extractions (all INERT — pages byte-behavior identical, proven by tests)

- **G-1** `raw_materials/services/roll_service.stock_status_counts(from_dt,to_dt,color_id)` —
  verbatim from `ClothDashboardView`; view switched to consume it.
- **G-2** `roll_service.stock_by_location(...)` — verbatim (Count+Q filter annotations); view switched.
- **G-4** `production/services/operations_digest.adda_status_counts(from_dt,to_dt)` +
  `stage_breakdown(from_dt,to_dt)` — verbatim from `AddaDashboardView` (incl. the
  pre-existing completed_today local-vs-UTC date semantics, preserved untouched); view switched.
- G-3 NOT built (owner rejected for v1 — pivot stays in the RM dashboard).

### 3. Tests (new this sub-phase)

- `bod/tests/test_widgets_wave1.py` (5): tiles == authoritative sources on same DB ·
  tiles == the rendered production-dashboard digest · no money tokens in ANY tile
  (pending_payable/advance_exposure/₹/payable) · fail-soft (patched owning service →
  200 + error tile + live siblings) · query budget ≤30 (test DB).
- `bod/tests/test_widgets_wave23.py` (3): materials tiles == roll_service · wave-3 tiles ==
  G-4/pending-distinct sources (+ chips kind) · Section 7 = pure links, no counts.
- `raw_materials/tests/test_stock_reads.py` (4): G-1/G-2 functions + ClothDashboard INERT
  parity + filter semantics.
- `production/tests/test_g4_status_reads.py` (4): G-4 functions + AddaDashboard INERT parity +
  date-filter semantics (completed_today deliberately global, as always).
- `bod/tests/test_shell.py`: empty-registry pin replaced by non-empty + **zero financial
  widgets** pin (money = BOD-D territory).

### 4. Battery + knowledge sync (per wave close — U5 sequential fresh-DB)

| Close | S1 (10 apps) | patterns_ai | devseed | verification | Total | Sync diff |
|---|---|---|---|---|---|---|
| Wave 1 | 1020/0F | 528/0F | 137/0F | 78/0F | 1763 | BLOCKER=0 WARN=361 (baseline residue) |
| Wave 2 | 1024/0F | 528/0F | 137/0F | 78/0F | 1767 | identical — 0 new findings |
| Wave 3 | 1031/0F | 528/0F | 137/0F | 78/0F | **1774** | identical — 0 new findings (body_hash ed2e87a45686ceb1…) |

**New battery baseline: 1774/1774** (S1 now = 10-app list incl. bod, per the BOD-D7 dated amendment).

### 5. Query measurement (BOD-D6: measured, not vibes — PRIMARY DB, read-only shell)

- Per-widget (shared cache): digest 8 · **settlement_queue 35** · machines 2 · roll-stock 4 ·
  stock-by-warehouse 1 · on-hold 4 · stage-chips 2 · workers-active 1 · rest 0 (cache hits).
- Full page (RequestFactory, view+template, no session write): **59 queries** at live data volume.
- **Budget verdict: without the settlement tiles' owning call the page = 24 ≤ 30 ✅; the single
  exception = `adda_settlement_service.settlement_queue()` (per-adda loop in the OWNING expense
  service, ~7 addas in queue today).** Window-never-engine forbids BOD from rewriting it; a fix
  is an owning-app read-path optimization (money-adjacent → owner-gated). → **Owner review item
  OI-C1** (options: accept exception for v1 · authorize expense read-path prefetch at BOD-D ·
  degrade the two settlement tiles). Test-DB budget test stays as the ≤30 regression tripwire.

### 6. Live evidence (owner dev server :8003, SA login, 2026-07-18 02:01 IST)

- `GET /bod/` → 200; ALL 12 tiles + 5 live stage chips (Elastic Attach 1 · Layering 3 ·
  Panel Join 1 · Pattern Design 1 · Side Seam Close 3) + 3 nav cards + "Last Updated" stamp.
- Live values cross-checked against the owning services in the same shell (stalled 7 ·
  pending 5 · ready 2 · blocked 5 "waiting on Panel Join" · active 9 · machines 4/2-out ·
  rolls 32 total/2 avail-DEV-rack · workers-active 5). Zero money figures on the board.
- Primary DB re-certified after all work: ledger 170 rows / Σ ₹10,880.25 · users 48 ·
  dev.min 0 · HEAD 49404001 · 2 stashes · no commits.

### 7. Responsive verification

CSS proven in template + tests: mobile-first 1-col grid → 2-col ≥768px → 3-col ≥1280px;
44px touch refresh target; chips + sub-lines wrap on phone; nav cards stack. **Real
3-width screenshots not capturable in this sandbox (no browser) — disclosed; visual
3-layout certification lands in the BOD-E certification pass on the owner's machine.**

### 8. Residuals / carried

- **OI-C1** settlement_queue query exception (above) — owner decision.
- D9 landing-override wiring (BOD = Owner/SA landing) — NOT wired yet; proposed for BOD-E.
- D8 `seed_feature bod` scenario — BOD-F.
- W2 (Completed Work) · F4 (salary obligations — permanent never-derive law) · G-3 pivot ·
  MC2 holder lists · pieces-today — all DEFERRED per owner rulings, unchanged.

_BOD-C closed 2026-07-18. Next: BOD-D (money wave) — owner authorization required._

## BOD-D — Money widget wave — ✅ COMPLETE 2026-07-18 (owner-authorized; U8-hostile, money verified MAIN-THREAD)

**Owner rulings executed:** OI-C1 → **Option B** (owning-app read-path optimization, identical
behavior — proven, below) · financial widgets = the approved V1 set ONLY · forbidden list
honored (NO revenue/P&L/cash-flow/analytics/forecasts/charts/salary-obligations/tiers/
derived metrics — none built). Financial correctness > performance throughout.

### 1. OI-C1 Option B — settlement_queue() batched read-path (expense app)

- **What:** the per-Adda `_payable_stage_records` + `_settleable_lines` calls inside
  `settlement_queue()` were an N+1. Now: ONE bulk stage-record query (Meta ordering
  `['adda','workflow_stage__order']` preserves each Adda's list order → waiting
  `incomplete` names unchanged) + ONE `_settleable_lines` pass over the union,
  partitioned by adda. **The shared funnel helpers are UNTOUCHED** — preview/finalize
  paths byte-identical; the queue calls the same functions, once instead of N times.
- **Identity proof (three independent instruments):**
  1. **Primary DB before/after JSON snapshot byte-identical** (md5
     `16120ae04547345cc1152a13d1514f78` both sides; full ready/waiting content incl.
     per-Adda expected ₹136.50/₹10.50, skips, drafts, incomplete names).
  2. **Parity pin** `expense/tests/test_queue_batching.py`: batched output == an
     independent per-Adda recomputation through the untouched helpers (the exact
     pre-optimization algorithm) on a mixed world (multi-worker ready · waiting ·
     monthly-skip · fully-credited dropout).
  3. Full expense suite green unchanged (178 before-edit re-run + suite after).
- **Partition-equivalence argument (recorded):** every per-line verdict depends only on
  per-line/global facts — settlement_line state · exact (worker_id, stage_record_id)
  era-A pair membership · the worker's global pay basis — so a union-then-partition is
  provably identical to per-Adda calls; ready-entry consumers are order-insensitive
  (len / sets / exact-Decimal sums). PA-11-2 grouped→0 guard untouched, applied per line
  as before.
- **Measured:** **35 → 6 queries** (volume-INDEPENDENT — `assertNumQueries(6)` pinned at
  two different Adda volumes). No API change, no signature change, no business-rule change.

### 2. Financial widgets shipped — 5 tiles (census F1/F2/F5/F6/F3-W3, all L1)

| kpi_id | Census | Source call | Drill-down |
|---|---|---|---|
| month-expenses | F1 | `expense_service.monthly_totals(y,m)['total']` (+count, month label) | `expense:factory-expense-list` |
| expense-categories | F2 | same call, `by_category` (PDD §21 locked set; largest-first = presentation order) | `expense:factory-expense-list` |
| outstanding-payments | F5 | `payroll_totals()['pending_payable']` (via the digest's SAME call — one aggregation/page) | `expense:payroll-overview` |
| outstanding-advances | F6 | `payroll_totals()['advance_exposure']` (PA-12-A reversal-aware) | `expense:payroll-overview` |
| expected-payouts | F3/W3 | Σ over `settlement_queue()['ready']` per-Adda `expected` (census-R-2 sanctioned presentation-sum of owner rows; each row = the owning funnel incl. PA-11-2) | `expense:adda-settlement-list` |

W4 "Pending Settlements" = A1 by census → **deduped** (count on the wave-1
settlements-ready attention tile; ₹ dimension on expected-payouts — no duplicate tile).
All 5 = `financial=True`, ALL in the charter financial section (structural pin), rendered
ONLY through the `{% money %}` tag (`core.templatetags.finance` — the single owner of
currency display; no BOD-side formatting). **FINANCIAL_ROLES wall** (charter D1.6) sits ON
TOP of the SA-only page gate in the view — money tiles vanish for any future non-financial
page audience (test-pinned via mocked `user_can_view_financials`).

### 3. Financial traceability report (owner mandate: widget → service → entity → rule → drill-down)

| Widget | Source service | Financial entity | Business rule | Drill-down |
|---|---|---|---|---|
| This Month's Expenses | `expense_service.monthly_totals` | `FactoryExpense` | non-voided rows of the current calendar month; factory-level ONLY (ADR-0011) | Factory-expense list |
| Expenses by Category | `expense_service.monthly_totals` (same call) | `FactoryExpense.Category` (§21 locked: rent/electricity/salary/other) | same void-aware month scope, grouped by category | Factory-expense list |
| Outstanding Worker Payments | `payroll_service.payroll_totals` | `WorkerLedgerEntry` | Σ credits − Σ debits (Earned-not-yet-paid; the payroll-overview definition) | Payroll overview |
| Outstanding Advances | `payroll_service.payroll_totals` | `WorkerAdvance` + `PayrollSettlementItem` | Σ given − Σ non-reversed recoveries (PA-12-A) | Payroll overview |
| Expected Worker Payouts | `adda_settlement_service.settlement_queue` | `WorkerStageContribution` → the settlement funnel | per-Adda expected = Σ settlement_quantity × effective_pay_rate (grouped→0 PA-11-2) over uncredited lines; Σ-of-ready = R-2 presentation-sum | Settlement queue |

### 4. ADR compliance report

- **ADR-0009 (cost-truth):** ✅ no widget reads `processing_cost`; no tile combines
  processing cost with labor; no sum crosses the two. Expected-payouts uses the settlement
  funnel's own per-line rate (the F2 chokepoint applies).
- **ADR-0011 (monthly salary / factory expenses):** ✅ F1/F2 read `FactoryExpense` only,
  factory-level totals, NEVER allocated per-Adda; the salary category shows salary PAID
  as recorded — no obligation derivation. **F4 permanent law honored: nothing reads
  `User.salary` or any informational field** (no such code path exists in bod/).
- **Settlement-only money flow:** ✅ zero new write paths anywhere in the wave — the
  R5 Money-Write census needs NO addendum (grep-verified: bod/ contains no ORM writes;
  the expense edit is a read-path batch inside an existing read-only function).
- **Expected → Earned → Paid separation:** ✅ Expected (queue funnel) and Earned-not-paid
  (ledger balance) are separate tiles from separate certified sources, never combined,
  never netted.
- **Advances:** ✅ sourced from the certified advance system (`payroll_totals`,
  reversal-aware) — no BOD re-derivation.

### 5. Performance report (BOD-D6 — measured, primary data volume)

| Measurement | Before | After |
|---|---|---|
| `settlement_queue()` alone | **35 queries** (N+1: 1+3 per Adda) | **6 queries** (volume-independent) |
| BOD page, 12 widgets (BOD-C close) | 59 | — |
| BOD page, **17 widgets** (all money live) | would be ~62 | **29 ≤ 30 ✅** |
| read_calls only (17 widgets, shared cache) | — | 26 |

Additional in-scope trims (both one-truth-preserving): F5/F6 reuse the digest's OWN
`payroll_totals` call (the census notes it was "built FOR the digest") instead of running
the identical aggregation twice per page; `adda_status_counts` gained a `fields=` subset
(same expressions, ONE calculation site — the on-hold tile runs 1 count instead of 4;
dashboard call unchanged, parity test-pinned). Known shared-shell residue (NOT BOD's):
the accounts permission layer runs ~5 role/extra-roles lookups per request on EVERY page —
out of BOD-D scope, noted for the owner.

### 6. Financial regression results (owner list, all ✅)

- Ledger totals unchanged: primary re-cert **170 rows / Σ ₹10,880.25 EXACT** after all work.
- Settlement totals unchanged: expense suite 178→180 green (incl. golden fixtures);
  queue before/after byte-identical; finalize/preview funnels untouched.
- Advance totals unchanged: `advance_exposure` live == service == page (₹0.00 today).
- Expense totals unchanged: `monthly_totals` untouched; live ₹10,500.00 == service == list page.
- Worker balances unchanged: `MoneyReadOnlyRegressionTests` — double board render moves
  ZERO money rows (ledger/advances/expenses/settlements count+Σ byte-identical around renders).
- Money widgets == source pages: test-pinned (payroll overview `total_payable`/
  `total_advance_out`; factory-expense list `totals` — same certified call) + live
  cross-check below. Void-awareness flows through (voided expense leaves the tile — pinned).
- Battery green across the accounting system (below).

### 7. Live evidence (owner :8003, SA, 2026-07-18)

- `GET /bod/` → 200: all 17 tiles + 3 nav cards; financial section renders
  ₹10,500.00 (month) · Salary ₹9,000.00 + Electricity ₹1,500.00 (categories) ·
  ₹5,812.25 (outstanding payments) · ₹0.00 (advances) · ₹147.00 (expected payouts).
- **Main-thread cross-verification on the same primary:** every live ₹ == its owning
  service exactly (`payroll_totals` 5812.25/0.00 · `monthly_totals` 10500.00
  {Salary 9000, Electricity 1500} · Σ queue ready expected 147.00 = the OI-C1 snapshot's
  136.50 + 10.50). Zero derived numbers.

### 8. Battery + sync (wave close)

**1785/1785 — NEW BASELINE** (10-app S1 = 1042 [chain 1031 + 2 queue-batching + 1 G-4
fields + 8 bod money] · patterns_ai 528 · devseed 137 · verification 78; sequential
fresh-DB). `knowledge_sync --diff`: BLOCKER=0, WARN=361 residue identical to baseline —
0 new findings. Primary EXACT (ledger 170/Σ₹10,880.25 · users 48 · dev.min 0) ·
git HEAD 49404001 · 2 stashes · no commits.

### 9. Test pins added this wave

- `expense/tests/test_queue_batching.py` (2): parity vs the untouched per-Adda funnel ·
  `assertNumQueries(6)` at two volumes.
- `bod/tests/test_widgets_money.py` (8): tiles == owning services (with REAL seeded money
  through certified writers) · tiles == source pages · void-awareness · ₹ via {% money %} ·
  FINANCIAL_ROLES wall (mocked non-financial audience → money tiles vanish, board intact) ·
  SA sees all 5 · read-only money regression · ≤30 budget with 17 widgets.
- `production/tests/test_g4_status_reads.py` +1: `fields=` subset == the full call.
- Evolved pins: shell registry pin → "5 money widgets, ALL financial=True, ALL in the
  financial section, and ONLY those there"; wave-1 no-money pin → scoped to non-financial
  tiles (the BOD-C law, kept for every non-money tile forever).

### 10. Residuals / carried

- Shared permission-layer ~5 role lookups/request (every ERP page) — owner may authorize
  an accounts-app request-cache separately; NOT touched in this wave.
- D9 landing override → BOD-E proposal · D8 `seed_feature bod` → BOD-F ·
  3-width screenshots → BOD-E (sandbox has no browser) — all carried unchanged.

_BOD-D closed 2026-07-18. Next: BOD-E (permissions + UI certification) — owner authorization required._

## BOD-E — Permissions + UI certification — ✅ COMPLETE 2026-07-18

**Owner scope honored:** certification + final polish ONLY — zero new widgets/KPIs/services/
business logic; the one behavior change = the owner-ordered D9 landing override.

### 1. D9 landing override — LIVE

`accounts.views.HomeView`: **super_admin → `bod:dashboard`** (D9); manager → Operations
dashboard (P1-1, byte-unchanged); worker/accountant/listing → My Dashboard (unchanged);
anonymous → login (unchanged). `LOGIN_REDIRECT_URL`/auth flow untouched — the override is
one branch inside the existing role-based landing. Pins: `bod/tests/test_certification.py`
(full landing matrix, every role) + `test_p1_1_operations_landing.py` (+SA case; manager/
worker cases pass UNCHANGED = the no-regression proof).

### 2. Permission certification report (matrix, all test-pinned + live)

| Audience | /app/home/ landing | GET /bod/ | Sidebar item | Widgets | Financial tiles |
|---|---|---|---|---|---|
| Anonymous | → login | 302 → login (`next=/bod/`) | — | — | — |
| Owner / Super Admin | **→ BOD (D9)** | 200 | ✅ visible (Main) | all 17 | all 5 |
| Manager | → Operations (unchanged) | 403 | hidden | — | — |
| Worker | → My Dashboard (unchanged) | 403 | hidden | — | — |
| Accountant | → My Dashboard (unchanged) | 403 | hidden | — | — |
| Listing team | → My Dashboard (unchanged) | 403 | hidden | — | — |

Financial wall additionally proven independent of the page gate (mocked non-financial
audience → money tiles vanish, board intact — BOD-D pin re-run green). Sidebar visibility
asserted on RENDERED HTML both ways (SA link present · manager link absent).

### 3. Drill-down certification

Every widget's `drill_down` + every Section-7 nav card: URL name reverses (dead link ⇒
test failure) AND serves the SA a 200 (follow=True). The full widget→destination map is
PINNED as the certified mapping (17 rows — `test_destination_map_is_the_certified_mapping`).
Shared destinations are the CORRECT owning module (settlements-ready/blocked + expected
payouts → the settlement queue; F1/F2 → factory-expense list; F5/F6 → payroll overview;
production tiles → the Operations dashboard) — no wrong-module links, no dead ends.

### 4. Responsive certification — REAL browser screenshots (first in-sandbox)

Method: authenticated live page from the owner's :8003 (session-cookie fetch), CSS fully
inline (single-CSS-source base.html) → headless google-chrome captures at three widths.
Artifacts: scratchpad `bod_mobile.png` (360×3200) · `bod_tablet.png` (768×2200) ·
`bod_desktop.png` (1280×1600) — VISUALLY VERIFIED:

- **360px:** single-column; every tile full-width; chips wrap to 3 lines; nav cards stack;
  44px refresh; NO horizontal overflow/scroll; ₹ values fit unclipped.
- **768px:** 2-column grid; cards aligned; sub-lines readable; chips card spans naturally.
- **1280px:** 3-column grid; sidebar shows "Business Operating Dashboard" ACTIVE under
  Main; section rhythm consistent; financial row renders ₹10,500.00 / categories /
  ₹5,812.25 / ₹0.00 / ₹147.00 exactly as the services report.
- Typography/spacing/cards identical to the certified system (Inter, cream cards,
  --border-card/--shadow-card tokens) at all three widths.

### 5. UI consistency report

- Tokens only: `.bod-tile` uses `--border-card`/`--shadow-card`/`--text-muted`/
  `--surface-muted`; zero hex values outside token fallbacks; page-scoped CSS under
  `.bod-dashboard` (CLAUDE rule 10) — nothing leaks.
- Component reuse: app shell + sidebar + `{% money %}` (single currency owner) — no
  duplicated pattern, no new shared component (rule-of-3 not triggered; tile/chips/nav-card
  live page-scoped). No icons/buttons beyond the shell's own.
- No design-system violations found (screenshots + template review).

### 6. Performance certification (re-measured on PRIMARY at close)

- Page with all 17 widgets: **29 queries ≤ 30** ✅ (BOD-D6).
- `settlement_queue()`: **6 queries**, volume-independent ✅ (OI-C1 Option B holding).
- No N+1: every multi-row read is a single aggregate/bulk query (audited per widget).
- No duplicate service calls: `NoDuplicateServiceCallTests` — one render ⇒ ≤1 call per
  shared owning service; `payroll_totals` exactly once (inside the digest; F5/F6 reuse it).

### 7. Window-never-engine audit (final)

Grep-audited + test-pinned: **0** ORM statements in bod non-test modules (services only) ·
**0** ORM writes anywhere in bod/ · **0** POST surfaces/forms/csrf (1 GET route; POST→405
pinned) · **0** models/migrations · exactly ONE arithmetic site (the census-R-2 sanctioned
Σ of ready `expected`) · no financial calculation, no duplicated calculation/workflow/truth ·
no duplicate dashboards (all 9 specialized dashboards remain the drill-down targets).

### 8. Battery + sync + docs

**1794/1794 — NEW BASELINE** (10-app S1 = 1051 [chain 1042 + 8 certification + 1 P1-1 D9
pin] · patterns_ai 528 · devseed 137 · verification 78). `knowledge_sync --diff`: BLOCKER=0,
residue identical (0 new findings). Docs cross-referenced this close: PDD register entry 6
(charter — consistent, no edit needed; completion lives here) · this log · bod README +
GUIDE (BOD-E state) · accounts GUIDE (HomeView D9 row) · DOCUMENTATION_INDEX (bod row
updated) · DEPLOYMENT_CAMPAIGN_STATUS · campaign memory. Primary EXACT (ledger 170/
Σ₹10,880.25) · git 49404001 · 2 stashes · no commits.

### 9. Remaining for BOD-F

- D8 `seed_feature bod` scenario (dated P11/P12 amendment path).
- Final certification package + handoffs (P16/P17 widgets enter ONLY via the PHASE_15
  ladder + registry; P13 check-candidate review).
- Owner residue decisions carried: accounts permission-layer ≈5 role lookups/request
  (every page, out of BOD scope) · snapshot refresh still due · 558 outputs
  owner-accepted-stale.

_BOD-E closed 2026-07-18. Next: BOD-F (certification + handoffs) — owner authorization required._

## BOD-F — Certification + handoffs — ✅ COMPLETE 2026-07-18 → 🏁 PHASE 15 CLOSED

**Closure phase — zero new widgets/KPIs/service edits/permission edits/UI changes.
Delivered: D8 dataset support + the final certification package + handoffs.**

### 1. D8 — `seed_feature feature-bod` (spec amendment A2)

Per the dataset architecture's OWN §15 interface row ("new scenarios ONLY via dated
amendments here"): **spec §12 amendment A2** (dated, recorded in
[DEV_DATASET_ARCHITECTURE.md](DEV_DATASET_ARCHITECTURE.md)) + §7 feature row updated.
Implementation = NO new architecture: registry entry `feature-bod` (class feature, layers
2,3,4,6,7,8) + a per-tag DEV-BOD clone of the deterministic settled money world + post step
`post_bod_board` — one DEV-noted FactoryExpense via the certified `record_expense` writer,
then the board's OWNING services re-run as the world's evidence (`operations_digest` ·
`monthly_totals`; window-never-engine: the BOD owns nothing, so the world is proven at the
services). Registry⇄CONTENT⇄spec three-surface agreement holds (knowledge_sync d7 clean).
**LIVE on `inventory_seed_scratch_2`:** seed → `created=11 assertions=PASS`
(settlement ADST-0010, ₹150.00 delta-explained) → second run `created=0 skipped=16` (pure
convergence) → **`verify_feature feature-bod` = 8/8 PASS** (body_hash b699d6e70f111888…).
Battery: devseed 137→138 (the new world joins the whole-registry twice-converge loop).

### 2. FINAL CERTIFICATION PACKAGE — Phase 15, all nine

1. **Architecture:** separate BASE-settings `bod` app; ZERO models/migrations; in-code
   registry (17 `Widget` rows + `NAV_CARDS`); thin presentation adapters with per-request
   cache; fail-soft renderer; linter layer `verification : bod`; sidebar = CODE MenuItem
   (SA predicate) + the owner's SidebarItemRule half (anchor 21 unchanged). ✅
2. **Window-never-engine:** 0 ORM statements in bod non-test modules · 0 writes anywhere in
   bod/ · 0 POST surfaces (1 GET route; POST→405 pinned) · 0 business/financial logic ·
   exactly ONE arithmetic site (census-R-2 sanctioned Σ) · no duplicated calculation/
   workflow/truth/dashboard — grep-audited + purity/zero-POST/read-only pins. ✅
3. **Money:** 5 financial widgets, all L1 from certified services; ADR-0009 + ADR-0011 +
   settlement-only + Expected→Earned→Paid separation verified (§BOD-D tables); F4
   never-derive law holds; ₹ only via `{% money %}`; FINANCIAL_ROLES wall; tiles == owning
   services == source pages (pinned + live-verified); render moves ZERO money rows;
   ZERO new write paths (R5 census unamended); ledger 170/Σ₹10,880.25 EXACT throughout. ✅
4. **Permissions:** full matrix pinned + live (anon 302 `next=` · SA 200/17-widgets/
   sidebar-visible · manager/worker/accountant/listing 403/sidebar-hidden); D9 landing
   LIVE (SA → BOD; all other roles byte-unchanged); drill-down access certified. ✅
5. **Performance:** page 29 ≤ 30 queries at live volume (BOD-D6); `settlement_queue()`
   35→6 volume-independent (OI-C1 Option B, byte-identical output); no N+1; ≤1 call per
   shared owning service per render (pinned). ✅
6. **Responsive:** REAL headless-chrome screenshots of the live page at 360/768/1280,
   visually verified — 1-col/2-col/3-col, chips wrap, no horizontal overflow; the
   2026-07-17 mobile-first certification minimum MET with actual 3-width evidence. ✅
7. **Battery:** **TERMINAL PHASE-15 BATTERY 1795/1795** (10-app 1051 · patterns_ai 528 ·
   devseed 138 · verification 78; chain 1745 entry → +13 A → +5/+4/+7 C waves → +11 D →
   +9 E → +1 F = 1795 ✓; every wave closed green, sequential fresh-DB). ✅
8. **Documentation:** BOD_BUILD_LOG (charter D1 → census → waves → certifications) ·
   PDD register entry 6 · bod README + GUIDE · accounts/expense/production/raw_materials
   GUIDEs · DOCUMENTATION_INDEX · DEV_DATASET_ARCHITECTURE A2 · campaign status + memory —
   all cross-referenced, internally consistent; knowledge_sync --diff clean at every close
   (0 new findings; body_hash stable ed2e87a45686ceb1…). ✅
9. **Deployment readiness (Phase-15 slice):** bod ships in BASE settings (production-
   present, read-only by architecture); no migrations to run; no flags; no runbook steps
   beyond normal deploy; `verify_production` untouched (bod adds no prod checks — correct:
   no state of its own); demo/acceptance = `seed_factory` + `seed_feature feature-bod`
   (dev-only, never in deployment paths). ✅

### 3. Handoffs — how future phases integrate with the BOD

**The three permanent laws (owner charter, reconfirmed at closure):**
1. **Every future KPI enters ONLY through the Metric Resolution Ladder** (BOD-B census
   pattern): L1 reuse a certified service · L2 owner-gated INERT additive read-function in
   the OWNING app · L3 = STOP for the owner. No exceptions, no ad-hoc tiles.
2. **Every future widget enters ONLY through the Widget Registry** (`bod/registry.py`
   `Widget` tuple; financial=True ⇒ the FINANCIAL_ROLES wall is automatic; money tiles
   live ONLY in the financial section — structurally pinned).
3. **The BOD never owns business logic** — adapters stay presentation-thin; any number the
   BOD shows must be explainable by its owning module (traceability table = the standing
   register, §BOD-D.3).
- **Phase 16 (Monthly Expense Engine):** its BOD widgets (if any) enter via this ladder +
  registry at MEE-D8 — the F4 salary-obligations slot stays EMPTY until the ERP owns a
  certified Payroll-Obligation entity (permanent owner law).
- **Phase 17 (RM→Expense Cost Integration):** same path; ADR-0009 sum-guard applies to any
  cost tile; honest-NULL renders as a note, never ₹0.
- **Phase 18/19:** BOD docs live at docs/apps/bod/GUIDE.md + this log; deploy = nothing
  special (readiness row above). **P13 candidates:** none added — the BOD holds no state to
  verify; its truth = the owning services already covered.
- **Standing instruments:** cross-check tests (tile == service == page) are the permanent
  no-second-truth tripwire; the ≤30-query pins are the budget tripwire; the destination-map
  pin freezes drill-downs.

### 4. Residue at closure (owner-visible, none blocking)

Accounts permission layer ≈5 role lookups/request on EVERY page (out of Phase-15 scope;
needs its own owner authorization) · snapshot refresh still due (owner) · 558 generated
outputs owner-accepted-stale until the regeneration phase · 3-width screenshots archived in
the session scratchpad (PNG artifacts; re-capturable any time via the §BOD-E method).

_🏁 Phase 15 CLOSED 2026-07-18. Primary EXACT (170/Σ₹10,880.25 · users 48 · dev.min 0) ·
git 49404001 · 2 stashes · NO commits (checkpoint = Phase 22). Next: Phase 16 (Monthly
Expense Engine, MEE-0) — owner-gated._
