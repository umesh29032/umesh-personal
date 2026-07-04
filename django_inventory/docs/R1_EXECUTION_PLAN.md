# R1 EXECUTION PLAN — Navigation, Visibility & F1 Guard

> Phase R1 of [IMPLEMENTATION_ROADMAP_PDD_V1.md](IMPLEMENTATION_ROADMAP_PDD_V1.md),
> derived from 🔒 [PDD v1.0](PRODUCT_DESIGN_DOCUMENT.md).
> STATUS: **IMPLEMENTED 2026-07-04 — awaiting owner acceptance.**
> Approved with 2 owner clarifications (both honored): R1 strictly read-only
> except the F1 guard; My Work presentation-only (no submit/edit surface).
> Results: gate PASS (714 tests, +14 new) · golden ₹225 OK · browser-verified
> 360/768/1280 both roles · docs synced. Deviations + discovered risks: see
> the implementation summary in the session log / roadmap R1 note.
> Anchors below verified against code 2026-07-04.

## 1) Scope (PDD refs)

| # | Item | PDD |
|---|---|---|
| R1.1 | **Settlement** + **Stage-Rates** buttons on Adda detail — management-gated. Settlement button is state-aware: no settlement → start page; draft/finalized exists → its detail page. | §23 |
| R1.2 | **"My Work" section** on Adda detail — self-scoped: the viewing worker's tasks in THIS Adda, quantities, expected earning. Worker's PRIMARY entry point. | §27-D7 |
| R1.3 | **"New Adda started"** broadcast row on the worker dashboard — read-only, all workers see production started; only assigned workers get an actionable link. No push infra. | §27-D6 |
| R1.4 | **F1 guard** — `Product.code` immutable once the product has any Adda. VERIFIED: `ProductForm` already disables `code` on every edit (stricter, acceptable — stricter satisfies the rule). Remaining: model-level `clean()` + service-path guard = defense-in-depth (P10). | §31.1-F1 |

Explicitly OUT of scope: any money logic, any new URL/route (→ §30-8 rule N/A),
any R2+ work.

## 2) Files to modify (no new files except tests)

| File | Change |
|---|---|
| `config/production/views/adda_views.py` | `AddaDetailView.get_context_data`: + `is_management`, + settlement-state (existing ADST for this Adda → button target), + `my_tasks` (request.user's WSTs + contributions + expected sum; prefetched) |
| `config/production/templates/production/adda_detail.html` | buttons block (mgmt-only) + My Work section (worker, mobile-first cards) |
| `config/inventory/views/dashboard.py` | `_build_dashboard_context`: recent IN_PROGRESS Addas for non-mgmt view (broadcast list, capped ~5) |
| `config/inventory/templates/inventory/user_dashboard.html` | broadcast row/card |
| `config/production/models/core.py` | `Product.clean()`: refuse `code` change when `adda_counter > 0` / Addas exist |
| `config/production/services/product_service.py` | mirror guard on the service update path (if it bypasses `full_clean`) |
| tests (production + inventory apps) | see §6 |

## 3) Database migrations

**NONE.** All features read existing tables; F1 is validation-only.

## 4) Views / services affected

- `AddaDetailView` — context only (read).
- `user_dashboard` context builder — read.
- `Product.clean` + `product_service` — validation guard.
- **NO chokepoint service touched. NO money write. NO new route.**

## 5) UI pages affected

`adda_detail.html`, `user_dashboard.html`. Rules: reuse existing card/chip/btn
classes (UI_COMPONENTS.md, rule 9); page-scoped CSS only under the page class
(rule 10); My Work = stacked cards on ≤600px, 44px touch targets; verify
360 / 768 / 1280 (rule 11). Broadcast + My Work must NOT leak cost/rate/
financial fields to workers (PA-03-1 precedent).

## 6) Tests to add

1. Buttons: management sees Settlement + Stage-Rates; worker response contains
   NEITHER (assertNotContains).
2. Settlement button state: no ADST → start URL; existing draft → detail URL.
3. My Work scoping: worker A sees own task + expected ₹ only; worker B's
   numbers absent from A's response; A's expected equals `/expense/my/` figure
   (same service source).
4. Broadcast: non-assigned worker sees "new Adda" row WITHOUT task link;
   assigned worker sees actionable link; management dashboard unchanged.
5. F1: product WITH Adda — model `clean()` raises on code change + service path
   refuses; form already locks (regression-pin test).
6. Full suite stays green (700+); golden ₹225 untouched (no money code in R1).

## 7) Documentation updates (rule 12, same session)

- `docs/PAGES/` adda-detail page contract (update or create).
- `docs/apps/production/GUIDE.md` + inventory app GUIDE rows for touched files.
- `UI_COMPONENTS.md` only if a genuinely new pattern emerges (target: none).
- Roadmap R1 status flip on acceptance. PDD unchanged (execution within frozen scope).

## 8) Risks

| Risk | Mitigation |
|---|---|
| N+1 on my_tasks/contributions | prefetch_related on the ctx query |
| Cross-worker data leak in My Work | filter strictly by `request.user`; leak test (§6-3) |
| Broadcast leaking financials | show code/product/status ONLY; leak test |
| F1 clean() breaking existing fixtures that mutate code | run suite; fix fixtures, never weaken the guard (P10) |
| Stale-template verification | restart runserver before every browser check (known gotcha) |

## 9) Rollback strategy

No migration ⇒ `git revert` of the R1 commit(s) restores the previous state
exactly. Zero data risk (read-only features + a validation guard). The F1 guard
can be reverted independently if it ever blocks a legitimate flow — but per
PDD F1 there is none (code with Addas must never change).

## 10) Acceptance criteria

- [ ] Admin on Adda detail: both buttons visible; Settlement routes by state;
      Stage-Rates opens the rate page (super-admin correction intact, §27-D3).
- [ ] Worker on the same page: zero admin buttons; My Work shows own quantities
      + expected ₹ matching My-Earnings; nothing of other workers.
- [ ] Every worker's dashboard shows "New Adda started · <code>" for
      IN_PROGRESS Addas; only assigned workers get a link into it.
- [ ] Product code immutable once Addas exist — UI, model, service paths; clear
      error message.
- [ ] `bash scripts/check.sh` green; browser-verified at 360/768/1280;
      docs updated same session.

## 11) Implementation order (estimated)

1. F1 model + service guard + tests (isolated, smallest) — ~30 min
2. AddaDetailView context + buttons + tests — ~1 h
3. My Work section (ctx + template, mobile-first) + tests — ~1.5 h
4. Dashboard broadcast + tests — ~45 min
5. Browser verification (3 viewports, both roles) + docs sync — ~45 min

Total ≈ half a working day. One commit per numbered step or one squashed R1
commit — owner's preference at ship time.
