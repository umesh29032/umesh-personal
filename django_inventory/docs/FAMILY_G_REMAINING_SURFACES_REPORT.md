---
id: docs-family-g-remaining-surfaces-report
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# Family G — Remaining Surfaces Consolidation Report (Phase G)

> **Evidence-based synthesis of the HTML-by-HTML audit, Phase G (remaining surfaces: cards/dashboards/details/timelines/standalone + partials/infra).**
> Source: [HTML_AUDIT_LEDGER.md](HTML_AUDIT_LEDGER.md) (HTML-061…071G + §"FAMILY G DISCOVERY" + §"PARTIALS/INFRA CENSUS + COMPLETENESS SCAN") + [HTML_CANONICAL_CANDIDATES.md](HTML_CANONICAL_CANDIDATES.md) (Card/Layout family ledger).
>
> **STRICTLY INVENTORY + EVIDENCE.** NO canonical ownership · NO promotions · NO migrations · NO architecture decisions · NO Card/Dashboard/Detail/Timeline/Standalone Foundation · NO TC-Card. **Popularity ≠ architecture. Consumer count ≠ architecture. Shared primitive ≠ architecture.**
> Date 2026-06-16 · Branch `new_flask_app`. Architecture remains OPEN (whole-system review only after ALL families done).

---

## 1. Systems inventory

| Surface system | Units | Render style |
|---|---|---|
| **Card-LIST** (CRUD list as cards) | pattern_list(061) · stage_list(070G) · stage_rate_list(070G) · role_list(070G) | mostly page-scoped; role_list base `.card` |
| **Dashboard** | user_dashboard(063) · adda_dashboard(064) · cloth_dashboard(071G) · pending_reports(069) · stalled_addas(069) · raw_material_dashboard(069) | base-primitive OR page-scoped (multiple) |
| **Detail** | adda_detail(065, A) · roll_detail(066, B) · scan_detail(067, B/unrouted) | 2 systems (A page-scoped+timeline; B base-card+dl) |
| **Timeline** | `_activity_feed`(adda_detail) · adda_history+roll_history(068) | 2 systems |
| **Financial-summary cards** | my_earnings(071G) · worker_detail(054) | base `.stat-card` (= TC-3 SummaryCards) |
| **Standalone** | public_home(071G) · 403/404/500(071G) · auth(CC-22) | no base.html, self-contained |
| **Config** | sidebar_access_list(071G) | form/list |
| **Dead/unrouted** | accounts/home(062) · scan_detail(067) | excluded from live counts |

Plus **~22 partials/infra** (census §8).

---

## 2. Ownership map

- **`base.html` = MASTER SHELL** — owns layout (sidebar/topbar/`.overlay`), global JS (`fancify`/`fancifyDate`/`initFancyDataTable`/`toggleSidebar`), and shared CSS primitives (`.card`/`.kpi`/`.stat-card`/`.form-control`/`.table-responsive`/`.empty-state`/`.btn`).
- **Shared-partial owners:** `_form_styles` · `_user_form_styles` · `_datatables_vendor_css/js` · `_time_log_styles` · `_activity_feed` · `_stage_panel_collapse` · `_autosave` · etc.
- **Page-scoped owners:** `.pattern-list` · `.stage-card` · `.adda-detail` · `.roll-detail` · `.scan-detail` · `.history-page` · `.pending-card` · `.stalled-card` · `.rm-cloth-card`.
- **Standalone owners:** each standalone page owns its own inline CSS (public_home, errors, auth).

---

## 3. Consumer counts (shared primitives)

- **`base.html`** (extends): **78 templates.**
- **base `.card`:** 7 — user_dashboard(063) · adda_dashboard(064) · roll_detail(066) · adda_history(068) · roll_history(068) · role_list(070G) · cloth_dashboard(071G).
- **base `.kpi`:** 2 — adda_dashboard(064) · cloth_dashboard(071G).
- **base `.stat-card` (= TC-3 SummaryCards):** 2 — my_earnings(071G) · worker_detail(054).
- **`_form_styles`:** 19 · **`_datatables_vendor`:** 5 (= TC-1) · **`_time_log_styles`:** 5 · **`_user_form_styles`:** 4 · **`_activity_feed`:** 2.

---

## 4. Shared vs page-scoped

| | Shared (base/partial) | Page-scoped |
|---|---|---|
| Cards | base `.card`/`.kpi`/`.stat-card` (dashboards, role_list, details B, history, financial-summary) | `.pattern-list`, `.stage-card`, `.adda-detail`, `.pending-card`, `.stalled-card`, `.rm-cloth-card` |
| Verdict | **MIXED** — shared primitives genuinely reused AND page-scoped variants coexist. Same shared-vs-page-scoped pattern as Forms & Tables. (Evidence only.) | |

---

## 5. Multiple-system evidence (NOT one system each)

- **Dashboards ≠ one system:** System A base-primitive (`.kpi`+`.card`: adda_dashboard, cloth_dashboard; `.card`: user_dashboard) vs ≥3 page-scoped (`.pending-card`, `.stalled-card`, `.rm-cloth-card`).
- **Details ≠ one system:** A (adda_detail, page-scoped `.adda-detail` + display chips + `_activity_feed`) vs B (roll_detail + scan_detail, base `.card` + `<dl>`, no timeline).
- **Timelines ≠ one system:** `_activity_feed.html` (shared partial, adda_detail) vs `.history-page` (adda_history + roll_history, 2 duplicated copies).
- **Card-lists ≠ one system:** base `.card` (role_list) vs page-scoped (pattern_list, stage_list, stage_rate_list — each different).
- **Status pills ≠ one owner:** production stage pills (stage_list, stage_rate_list) vs financial pills (settlement_list/detail).
- **Acceptable** (intentional or accidental — classification deferred to whole-system review).

---

## 6. Dead / unrouted surfaces

- **`accounts/home.html`** (062) — rendered by NOTHING (HomeView unconditionally redirects). Hardcoded `₹2.4L` placeholder. Dead-code candidate.
- **`tracking/scan_detail.html`** (067) — `scan_piece` view NOT in any urls.py (test-only). Unrouted. Dead-or-pending-wiring candidate.
- Both **excluded from live consumer counts.** Owner decides disposition (cleanup vs wire) — NOT now.

---

## 7. Standalone lane (no base.html)

- **public_home** (1311L marketing landing) · **403/404/500** (3 near-identical error pages) · **auth** (7 pages, CC-22).
- All self-contained (own inline CSS, no base.html). Error pages **deliberately standalone** (render when base/DB broken — resilience-justified). A distinct architectural lane (not a defect).

---

## 8. Existing shared owners (real, in code)

- **base.html** (78) · **`_form_styles`** (19) · **`_datatables_vendor`** (5, = TC-1) · **`_time_log_styles`** (5) · **`_user_form_styles`** (4, = CC-26) · **`_activity_feed`** (2, timeline).
- These are code-level shared owners that **already exist** (not proposals).
- `_workers_widget` = widget-rendered (`_WorkerCheckboxes` `template_name`, CC-16) — live, not dead.

---

## 9. Conceptual-only systems (recurring concept, fragmented/no single code owner)

- **TC-3 Financial** (SummaryCards/MoneyCell/StatusPill/LedgerGrid/LedgerEmpty/ResponsiveLedger — ~6 consumers, duplicated impl).
- **TC-5 Export** (button-group + manifest + download — duplicated ×2).
- **Card systems** (mixed: shared base `.card`/`.kpi`/`.stat-card` + page-scoped variants).
- **Dashboard / Detail / Timeline / Card-list systems** (MULTIPLE each, per §5).
- These are **concepts with multiple/duplicated implementations** — whether any becomes a foundation is a **whole-system-review decision, NOT an audit decision.**

---

## Decision asks (none yet — inventory acceptance only)

1. Accept the Family G **systems inventory + ownership map + consumer counts** (§1-§8) as evidence.
2. Accept the **multiple-systems** findings (§5) and **dead/unrouted** list (§6) as evidence.
3. **No architecture decision requested** — foundations/promotions/migrations deferred to the whole-system review.

**Family G evidence FROZEN 2026-06-16. Architecture OPEN.** No promotion / no canonical / no migration. Next: any remaining family work → then whole-system architecture review.
