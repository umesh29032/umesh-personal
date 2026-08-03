---
id: docs-ui-components-catalog
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# UI COMPONENTS CATALOG

> **Status:** Component reference — **DESIGN ONLY, NO CODE.** The "where does it live + how
> do I use it" map for any future frontend developer — usable without reading the whole project.
> Companion to [SPEC](DESIGN_SYSTEM_SPEC.md) (rules) · [ARCHITECTURE](FRONTEND_DESIGN_SYSTEM_ARCHITECTURE.md) (map)
> · [ROADMAP](DESIGN_SYSTEM_IMPLEMENTATION_ROADMAP.md) (build plan) · [UI_COMPONENTS.md](../UI_COMPONENTS.md) (locked canon).
> **Owner:** Umesh · **Created:** 2026-06-16. Counts measured 2026-06-16 (`config/**/*.html`).
>
> **Status legend:** 🟢 BUILT (exists today) · 🟡 PARTIAL (exists, needs consolidation) ·
> 🔵 PLANNED (foundation not built yet — consumer count = current / target).
> **Screenshot refs** name the live page + viewport to capture into `docs/screenshots/`
> (not yet captured — capture during each foundation's browser-verify).

| # | Component | Status | Owner file | Consumers |
|---|---|---|---|---|
| 1 | Buttons | 🟡 | base.html `.btn` | 86 |
| 2 | Forms (chrome) | 🟡 | `_form_styles.html` | 23 |
| 3 | Inputs | 🟡 | base.html + `_form_styles` | `.field` 28 / `.sf-input` 7 |
| 4 | Selects | 🟢 | base.html `fancify()` | `<select>` in 16 |
| 5 | Date inputs | 🟢 | base.html `fancifyDate()` | `data-fancy-date` 2 / native 5 |
| 6 | Tables | 🟢 | base.html `initFancyDataTable` + vendor | TC-1 8 · `.table-responsive` 19 |
| 7 | Cards | 🟡 | base.html `.card` | 59 |
| 8 | KPI cards | 🟢 | base.html `.kpi` | 9 |
| 9 | Summary cards | 🟢 | base.html `.stat-card` | 3 |
| 10 | Status pills | 🟡 | base.html `.badge` + `--status-*` | 17 |
| 11 | Money cells | 🔵 | `shared/financial/` (planned) | 0 / ~10 |
| 12 | Auth shell | 🔵 | `shared/_auth_shell.html` (planned) | 0 / 7 |
| 13 | Export buttons | 🔵 | `shared/_export_buttons.html` (planned) | 0 / 2–4 |
| 14 | Empty states | 🟢 | base.html `.empty-state` | 12 |
| 15 | Badges | 🟢 | base.html `.badge` | 17 |

---

## 1. Buttons 🟡
- **Purpose:** all clickable actions (primary/secondary/destructive/filter).
- **Owner file:** `accounts/base.html` `.btn` + modifiers.
- **Consumers:** 86 templates.
- **Allowed variants:** `.btn` (base, required) + `.btn-primary` · `.btn-copper` ·
  `.btn-ghost` · `.btn-danger` · `.btn-filter` · `.btn-clear` · `.btn-sm` (size, planned F2).
- **Responsive:** full-width stack ≤sm in page-header/form-actions; `.btn-sm` for dense table rows.
- **Accessibility:** real `<button>`/`<a>`; focus-visible; icon-only ⇒ `aria-label`; ≥44px (`--touch-min`).
- **Token deps:** `--copper`/`--copper-d`, `--status-danger-*`, `--radius-md`, `--space-*`, `--fs-*`, `--touch-min`.
- **Screenshot ref:** `buttons.png` — product_list row actions @1280 + @375.
- **Correct:** `<a class="btn btn-ghost btn-sm">Edit</a>` · `<button class="btn btn-primary">Save</button>`
- **Forbidden:** `<a class="btn-ghost" style="padding:4px 10px;font-size:12px">` · variant without `.btn` base · `<div class="button">`.

## 2. Forms (chrome) 🟡
- **Purpose:** form layout/spacing/panels for create/edit/filter pages.
- **Owner file:** `shared/_form_styles.html` (today `production/_form_styles.html` → relocate F3).
- **Consumers:** 23 includes.
- **Allowed variants:** form-shell `.sf-*` (hero + numbered panels + sticky CTA) for create/edit; `.field` light system for admin/inline. Kept separate (not merged).
- **Responsive:** `.form-grid` → single column ≤sm; sticky CTA full-width; partial owns its own responsive CSS.
- **Accessibility:** labeled fields; per-field error association; focus order.
- **Token deps:** `--space-*`, `--surface-input`, `--text-secondary`, `--danger`, `--control-h`.
- **Screenshot ref:** `forms.png` — a create page (form-shell) @1280 + @375.
- **Correct:** `{% include 'shared/_form_styles.html' %}` then `.sf-*` markup.
- **Forbidden:** inline form CSS · merging `.field`+`.sf-*` · swallowing field errors.

## 3. Inputs 🟡
- **Purpose:** text/number/textarea/select fields.
- **Owner file:** base.html (`.sf-input` look) + `_form_styles.html` (`.field`).
- **Consumers:** `.field` 28 · `.sf-input` 7.
- **Allowed variants:** `.sf-input` (cream, fancify-ready, 39px) · `.field` control · `--bare` fallback (auto, unclassed selects).
- **Responsive:** full-width ≤sm; ≥44px touch; cream bg + inset shadow (readability rule).
- **Accessibility:** `<label>` or `aria-label`; visible focus; error tied to field.
- **Token deps:** `--surface-input`, `--surface-input-focus`, `--control-h`, `--radius`, `--fs-base`.
- **Screenshot ref:** `inputs.png` — user_form @375 (cream inputs).
- **Correct:** `<input class="sf-input">` · `<label>` present.
- **Forbidden:** `style="background:#fff"` (white-on-white) · inline font-size · label-less input.

## 4. Selects 🟢
- **Purpose:** single/filter dropdowns.
- **Owner file:** base.html `fancify()` (JS) + `.sf-input` trigger look.
- **Consumers:** `<select>` across 16 templates.
- **Allowed variants:** fancified `.sf-input` select (default) · `data-no-fancy` (filter-select / cloned dynamic rows — documented reasons) · `--bare` fallback (unclassed).
- **Responsive:** trigger 39px (classed) / 44px (`--bare`); dropdown panel mobile-safe.
- **Accessibility:** keyboard open/navigate; focus trap in panel; native fallback labeled.
- **Token deps:** `--surface-input`, `--control-h`, `--radius`, `--border-card`.
- **Screenshot ref:** `selects.png` — a form select open @375.
- **Correct:** `<select class="sf-input">…` (auto-fancified) · `data-no-fancy` on filter selects.
- **Forbidden:** hand-built dropdown divs · re-implementing fancify per page.

## 5. Date inputs 🟢
- **Purpose:** date entry with opt-in calendar.
- **Owner file:** base.html `fancifyDate()` + `.fancy-date-*` CSS.
- **Consumers:** `data-fancy-date` 2 · native `type=date` 5.
- **Allowed variants:** opt-in fancy-date (`data-fancy-date`) · native `<input type=date>` (default).
- **Responsive:** calendar panel mobile-positioned; native picker on mobile OK; ≥44px.
- **Accessibility:** keyboard date nav; labeled; year navigation reachable.
- **Token deps:** `--surface-input`, `--copper` (selected), `--radius`, `--control-h`.
- **Screenshot ref:** `dates.png` — user_form birth_date calendar @375.
- **Correct:** `<input type="date" data-fancy-date>` (opt-in) or plain `type=date`.
- **Forbidden:** custom date widget per page · forcing fancy-date where native is fine.

## 6. Tables 🟢
- **Purpose:** list/CRUD tables with search/sort/paginate + mobile stack.
- **Owner file:** base.html `initFancyDataTable` + `shared/_datatables_vendor_css/js.html` + `.table-responsive`/`data-label` contract.
- **Consumers:** TC-1 engine 8 pages · `.table-responsive` 19.
- **Allowed variants:** A1 (DataTable CRUD) · A2 (plain shared-primitive, migrating to A1) · TC-2 exceptions (workflow/inline/matrix/dashboard/ledger — NOT forced onto engine).
- **Responsive:** mandatory `.table-responsive` + `data-label` card-stack (or scroll/summary). data-label INERT without wrapper.
- **Accessibility:** `<thead>`; `.action-link` real `<a>` (≥44px = debt); labeled search.
- **Token deps:** table chrome + `--status-*` (status cells) + `--border-card`.
- **Screenshot ref:** `tables.png` — product_list @1280 (engine) + @320 (stack).
- **Correct:** `.table-responsive > table#x-dt.tbl` + `initFancyDataTable('#x-dt',{itemName:'…'})` + `data-label` cells.
- **Forbidden:** `.DataTable()` outside helper · table without `.table-responsive` · missing `data-label`.

## 7. Cards 🟡
- **Purpose:** content container (panels, sections, list items).
- **Owner file:** base.html `.card`/`.card-header`/`.card-title`/`.card-clip`.
- **Consumers:** 59 templates.
- **Allowed variants:** `.card` (+`-header`/`-title`/`-clip`); page card SYSTEMS add LAYOUT under a page class, never chrome.
- **Responsive:** stack single-column ≤sm; padding via tokens; no overflow.
- **Accessibility:** card title = heading where it's a section; interactive cards keyboard-reachable.
- **Token deps:** `--border-card`, `--shadow-card`/`-hover`, `--radius-lg`, `--space-*`, `--surface`.
- **Screenshot ref:** `cards.png` — adda_detail @1280 + @375.
- **Correct:** `<div class="card"><div class="card-header"><div class="card-title">…`
- **Forbidden:** inline card chrome · re-defining `.card` in page CSS · `<div>` styled as card.

## 8. KPI cards 🟢
- **Purpose:** dashboard headline metric tiles (hover-lift).
- **Owner file:** base.html `.kpi`.
- **Consumers:** 9 templates.
- **Allowed variants:** `.kpi` (+ value/label children).
- **Responsive:** grid reflow to fewer columns ≤sm; padding shrinks (`@media .kpi`).
- **Accessibility:** metric label readable; sufficient contrast.
- **Token deps:** `--surface`, `--shadow-card`, `--radius-lg`, `--space-*`, type tokens.
- **Screenshot ref:** `kpi.png` — main dashboard @1280 + @375.
- **Correct:** `<div class="kpi">…</div>` in a dashboard grid.
- **Forbidden:** copying `.kpi` look into page CSS · inline tile chrome.

## 9. Summary cards 🟢
- **Purpose:** compact stat strip (label + value), incl. financial totals (= TC-3 SummaryCards).
- **Owner file:** base.html `.stat-card`.
- **Consumers:** 3 templates (low — financial foundation will expand usage).
- **Allowed variants:** `.stat-card` + value modifier (`.payable` etc.).
- **Responsive:** wrap/stack ≤sm; value stays legible.
- **Accessibility:** label + value contrast; value not color-only meaning.
- **Token deps:** `--copper` (payable), `--stone` (label), type tokens, `--radius`.
- **Screenshot ref:** `summary_cards.png` — payroll_overview @1280 + @375.
- **Correct:** `<div class="stat-card payable"><div class="label">Payable</div><div class="value">₹360</div></div>`
- **Forbidden:** hand-built stat tiles in financial pages (use `.stat-card`).

## 10. Status pills 🟡
- **Purpose:** state labels (active/archived, settlement/payment status).
- **Owner file:** base.html `.badge` + `--status-*` (dedicated `.pill` arrives with Financial F6).
- **Consumers:** 17 templates.
- **Allowed variants:** `.badge` `.badge-active` `.badge-inactive`; financial → `.pill pill--<status>` (planned, from `--status-*`).
- **Responsive:** inline, wraps with content; no overflow.
- **Accessibility:** TEXT not color-only; contrast via status pairs.
- **Token deps:** `--status-{success,warning,danger,info,neutral}-{bg,text}`.
- **Screenshot ref:** `status_pills.png` — adda_settlement_list @1280.
- **Correct:** `<span class="badge badge-active">● Active</span>` · `<span class="pill pill--success">Settled</span>`
- **Forbidden:** raw-color pills · color-only status (no text).

## 11. Money cells 🔵 (PLANNED — Foundation 6)
- **Purpose:** consistent ₹ formatting/alignment/sign across all money surfaces.
- **Owner file:** `shared/financial/money_cell.html` (planned).
- **Consumers:** 0 / ~10 financial templates.
- **Allowed variants:** `.money` · `.money--neg` (planned).
- **Responsive:** right-aligned desktop; mobile stack/summary (never raw clip); totals visible.
- **Accessibility:** screen-reader-sane amount; not color-only sign.
- **Token deps:** type tokens, `--danger` (negative), `--text-primary`.
- **Screenshot ref:** `money_cell.png` — costing @1280 (capture at build).
- **Correct:** `{% include 'shared/financial/money_cell.html' with amount=line.total %}`
- **Forbidden:** `<td style="text-align:right">₹{{ a }}</td>` repeated per template · template-side money math.

## 12. Auth shell 🔵 (PLANNED — Foundation 5)
- **Purpose:** one chrome for all 7 auth pages.
- **Owner file:** `shared/_auth_shell.html` (planned).
- **Consumers:** 0 / 7 (login, login_password, signup, signup_otp, otp, reset_otp, forgot_password).
- **Allowed variants:** one shell + per-page form slot.
- **Responsive:** centered card, full-width ≤sm, ≥44px, 320→1280 no overflow.
- **Accessibility:** labeled inputs, focus order, error announce, `autocomplete` preserved.
- **Token deps:** `--surface`, `--page-bg`, brand colors, `--radius-lg`, `--space-*`.
- **Screenshot ref:** `auth_shell.png` — login @375 (capture at build).
- **Correct:** `{% extends 'shared/_auth_shell.html' %}{% block auth_form %}…{% endblock %}`
- **Forbidden:** per-page auth layout copy · changing POST field/CSRF/rate-limit while restyling.

## 13. Export buttons 🔵 (PLANNED — Foundation 7)
- **Purpose:** one CSV/XLSX/PDF export group.
- **Owner file:** `shared/_export_buttons.html` (planned).
- **Consumers:** 0 / 2–4 (barcode_list, _stage_panel_barcode_gen, export pages).
- **Allowed variants:** include with csv/xlsx/pdf urls (+ optional quick-CSV).
- **Responsive:** group wraps on mobile; stays in card-header/page-level, OUTSIDE table; ≥44px.
- **Accessibility:** labeled `<button>` in real `<form>`; keyboard reachable.
- **Token deps:** Button tokens (via `.btn .btn-ghost`).
- **Screenshot ref:** `export_buttons.png` — barcode_list card-header @375.
- **Correct:** `{% include 'shared/_export_buttons.html' with csv_url=… xlsx_url=… pdf_url=… %}`
- **Forbidden:** inline 3-form duplication · forms inside `.dataTables_wrapper` · dropped CSRF/escaping.

## 14. Empty states 🟢
- **Purpose:** zero-data message + CTA.
- **Owner file:** base.html `.empty-state`.
- **Consumers:** 12 templates.
- **Allowed variants:** `.empty-state` (+ `h3`/`p`/CTA button).
- **Responsive:** centered, padding via tokens, full-width ≤sm.
- **Accessibility:** heading + descriptive text; CTA = real button.
- **Token deps:** `--ink`, `--stone`, `--space-*`, type tokens.
- **Screenshot ref:** `empty_state.png` — an empty list @375.
- **Correct:** `<div class="empty-state"><h3>No rows</h3><p>…</p><a class="btn btn-primary">+ Add</a></div>`
- **Forbidden:** ad-hoc "no data" markup per page · table `{% empty %}` without the responsive contract.

## 15. Badges 🟢
- **Purpose:** small inline labels/counts (shares owner with Status pills).
- **Owner file:** base.html `.badge`.
- **Consumers:** 17 templates.
- **Allowed variants:** `.badge` `.badge-active` `.badge-inactive` (status variants).
- **Responsive:** inline, wraps; no overflow.
- **Accessibility:** text content (not icon/color-only); contrast.
- **Token deps:** `--status-*` pairs, `--radius-pill`, `--fs-xs`.
- **Screenshot ref:** `badges.png` — product_list status column @1280.
- **Correct:** `<span class="badge badge-active">● Active</span>`
- **Forbidden:** custom inline label chrome · color-only meaning.

---

## Quick-start for a new frontend dev
1. **Need a control?** Find it above → use its owner + allowed variants. Don't re-implement.
2. **Need a value (color/space/radius/font)?** Use a token (`var(--…)`), never a literal.
3. **New table?** `.table-responsive` + `initFancyDataTable`. **New form?** include `_form_styles`.
   **New button?** `.btn` + modifier. **Money?** the financial partials (F6+).
4. **Pattern in 3+ templates** (financial: 2+) → promote to a shared owner + update
   [UI_COMPONENTS.md](../UI_COMPONENTS.md). Otherwise page-scoped under a page class.
5. **Rules** = [SPEC](DESIGN_SYSTEM_SPEC.md). **Why/where** = [ARCHITECTURE](FRONTEND_DESIGN_SYSTEM_ARCHITECTURE.md). **Build order** = [ROADMAP](DESIGN_SYSTEM_IMPLEMENTATION_ROADMAP.md).

---

**No code authorized. No tokens created.** Catalog complete. Foundation 1 (Design Tokens)
implementation may begin on explicit owner approval, per the ROADMAP, one foundation at a time.
