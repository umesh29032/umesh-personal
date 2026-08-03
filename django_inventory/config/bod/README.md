---
id: config-bod-readme
type: app-readme
status: active
owner: handwritten
scope: bod
anchors: config/bod/
verified: 2026-07-18
---

# bod — Business Operating Dashboard (Campaign Phase 15)

**What:** the Owner's command center — one screen answering *"How is my business doing
right now?"* (the owner-approved product charter: PDD amendment register **entry 6**;
charter of record [docs/BOD_BUILD_LOG.md](../../docs/BOD_BUILD_LOG.md) §BOD-D1).

**Law — WINDOW, NEVER ENGINE (owner):** the BOD reads certified truths through the existing
service layer and presents the overview. It owns ZERO business logic, ZERO models, ZERO
migrations, ZERO write paths (GET-only; POST → 405 — test-pinned); every metric has ONE
authoritative owner; every card drills DOWN into the module that owns its truth;
**specialized module dashboards continue to exist** — the BOD consumes high-level summaries.

**Access (BOD-D4):** v1 = Owner/Super Admin ONLY (`BODAccessMixin`; anonymous → login,
authenticated non-SA → 403). The sidebar MenuItem is SA-predicate-gated; the owner may
additionally manage it via a SidebarItemRule row through Access Control (the certified
double-gate). Financial widgets will additionally gate on FINANCIAL_ROLES.

**Architecture (BOD-D2/D3):** widget registry IN CODE (`registry.py` — the §6.2 tuple:
kpi_id · section · owning read-call · certified component · gate · responsive strategy ·
drill-down). Every KPI enters ONLY through the Metric Resolution Ladder (step-1 reuse an
existing certified service · step-2 an individually owner-gated INERT additive read-function
in the OWNING app · step-3 = STOP for the owner — the BOD never owns a business
calculation). Sections fixed by charter: Attention → Production → Materials & Warehouses →
Workers → Financial → Machines.

**Refresh (BOD-D5):** as-of page load + manual refresh + the visible "Last Updated"
timestamp. No polling, no websockets, no cache. **Performance (BOD-D6):** ≤30 DB queries
per page, measured (test-pinned); no N+1.

**State (BOD-E CERTIFIED, 2026-07-18 — V1 feature-complete):** D9 landing LIVE (Owner/SA
lands on the BOD after login; every other role unchanged — matrix pinned); full permission +
drill-down + responsive (REAL 360/768/1280 screenshots) + UI-consistency + performance
(page 29 ≤ 30 · queue 6, volume-independent · no duplicate service calls — pinned) +
window-never-engine certifications recorded in BOD_BUILD_LOG §BOD-E. Prior state
(BOD-D): **17 widgets live** — 12 non-money (waves 1-3:
digest/settlement-queue counts · materials via G-1/G-2 `roll_service` · production extras
via G-4 `operations_digest` · workers-active · machine counts-only) + **5 financial
(owner-authorized money wave: F1 month expenses · F2 categories · F5 outstanding payments ·
F6 outstanding advances · F3/W3 expected payouts — all L1, all `financial=True`, all in the
financial section, FINANCIAL_ROLES wall on top of the page gate, ₹ rendered ONLY via the
`{% money %}` tag)** + Section 7 = navigation cards ONLY, zero counts. Adapters in
`widgets.py` (thin tile mappers, per-request cache), fail-soft rendering, no-second-truth
cross-checks (every tile == its owning service AND its source page on the same DB) +
read-only money regression (board render moves zero money rows). **F4 permanent law: nothing
derives from `User.salary`/informational fields. OI-C1 resolved by owner Option B:**
`settlement_queue()` batched in the OWNING expense app (35→6 queries, byte-identical output,
parity-pinned) — full page = **29 ≤ 30 queries at live volume** with all 17 widgets.
Deferred by owner order: revenue/P&L/cash-flow/analytics/forecasts/charts/salary-obligations.

**Tests:** part of the first canonical-battery suite (10-app list) per the BOD-D7 dated
amendment. Evidence: [docs/BOD_BUILD_LOG.md](../../docs/BOD_BUILD_LOG.md).
