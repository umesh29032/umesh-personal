---
id: docs-apps-bod-guide
type: app-guide
status: active
owner: handwritten
scope: bod
anchors: config/bod/
verified: 2026-07-18
---

# bod — app guide (owner command center, Campaign Phase 15)

> WINDOW, NEVER ENGINE (owner charter: PDD register entry 6; record =
> [BOD_BUILD_LOG.md](../../BOD_BUILD_LOG.md) §BOD-D1). Read-only · zero models ·
> Owner/SA-only v1 · every card drills down into its owning module · specialized
> dashboards continue. Contract: 🔒
> [PHASE_15_BUSINESS_OPERATING_DASHBOARD.md](../../campaign_contracts/PHASE_15_BUSINESS_OPERATING_DASHBOARD.md).

| File | Role |
|---|---|
| `apps.py` | AppConfig — no models, no migrations (read-only by shape) |
| `mixins.py` | `BODAccessMixin` (BOD-D4): Owner/SA only; anon → login redirect, authenticated non-SA → 403; the view half of the certified double-gate (SidebarItemRule row = the owner's Access Control half) |
| `registry.py` | The in-code widget registry (BOD-D2): `Widget` tuple (kpi_id · section · owning read-call · drill-down · responsive strategy · financial · gate) + the charter-fixed `SECTIONS` order. **BOD-D 2026-07-18: 17 widgets live** — 12 non-money (waves 1-3) + **5 financial (F1/F2/F5/F6/F3-W3, ALL `financial=True`, ALL in the financial section — structural pin)** + `NAV_CARDS` (Section 7 = pure links, ZERO counts — owner taste ruling) |
| `widgets.py` | PRESENTATION adapters: thin mappers owning-service-result → tile shape `{value, sub, note[, kind, money, money_sub]}`; per-request `cache` dict so shared owner calls (`operations_digest` · `settlement_queue` · `register_counts` · `monthly_totals`) run ONCE per page (F5/F6 reuse the digest's own `payroll_totals` numbers — one aggregation/page). Zero business logic, zero ORM, zero ₹ formatting (Decimals pass through to `{% money %}`) — ladder provenance per adapter = BOD_BUILD_LOG §BOD-B.1 census row |
| `views.py` | `BODDashboardView` — GET-only TemplateView (`http_method_names` pinned); context = sections (fail-soft `_render_widget`: one broken owner call → error tile, never 500) + `nav_cards` + the BOD-D5 as-of timestamp |
| `urls.py` | ONE route: `bod:dashboard` (zero POST surfaces, v1) |
| `templates/bod/dashboard.html` | The mobile-first shell (2026-07-17 permanent ruling): 1-col phone / 2-col ≥768 / 3-col ≥1280 · 44px touch refresh · page-scoped CSS, tokens only · "Last Updated" + manual refresh · value-tile + chips variant (P5) + error tile + Section-7 nav cards |
| `tests/test_shell.py` (13) | **Permanent pins:** purity (zero ORM/instance writes; modelless shape; BASE registration) · zero-POST (route census = 1; POST → 405) · the BOD-D4 matrix (SA 200 w/ all sections · manager/worker/accountant/listing 403 · anon → login) · read-only render + **≤30-query budget (BOD-D6)** · registry non-empty + ZERO financial widgets (BOD-D territory) + charter section-order + Widget-shape + SA-only sidebar predicate pins |
| `tests/test_widgets_wave1.py` (5) | The standing no-second-truth proof: every tile == its authoritative source on the same DB · tiles == the rendered production-dashboard digest · no money tokens in any tile · fail-soft · live-widget query budget |
| `tests/test_widgets_wave23.py` (3) | Materials tiles == `roll_service` (G-1/G-2) · wave-3 tiles == G-4 sources + chips kind · Section 7 = pure links, no counts |
| `tests/test_widgets_money.py` (8) | **BOD-D money pins:** every ₹ tile == its owning service AND its source page (REAL seeded money via certified writers) · void-awareness flows through · ₹ via `{% money %}` only · FINANCIAL_ROLES wall (non-financial audience → money tiles vanish, board intact) · read-only regression (render moves zero money rows) · ≤30 budget with all 17 widgets |
| `tests/test_certification.py` (8) | **BOD-E certification pins:** D9 landing matrix (SA → BOD; manager/worker/accountant/listing → their pre-D9 landings; anon → login) · full page permission matrix (anon 302 `next=` · SA 200 all-17 · 4 roles 403) · sidebar rendered-HTML visibility both ways · every drill-down + nav card reverses AND serves the SA a 200 · the 17-row widget→destination map pinned as certified · one render ⇒ ≤1 call per shared owning service (`payroll_totals` exactly once, inside the digest) |

Rules of the app: window-never-engine (six clauses, contract §4) · every KPI through the
Metric Resolution Ladder · money widgets = their own U8-hostile wave · compose-from-canon ·
mobile-first certification (mobile + tablet + desktop) before any wave closes.
