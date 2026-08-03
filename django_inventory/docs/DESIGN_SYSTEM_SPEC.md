---
id: docs-design-system-spec
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# DESIGN SYSTEM SPECIFICATION

> **Status:** Permanent frontend contract — **DESIGN ONLY. NO CODE. NO TOKEN CREATION YET.**
> The enforceable rulebook for every foundation. Code examples below are **illustrative**
> (how to consume the system), not edits to the app.
> Companion: [ARCHITECTURE](FRONTEND_DESIGN_SYSTEM_ARCHITECTURE.md) (map) ·
> [ROADMAP](DESIGN_SYSTEM_IMPLEMENTATION_ROADMAP.md) (build plan) · this = the *contract*.
> **Owner:** Umesh · **Created:** 2026-06-16 · **Branch:** `new_flask_app`.

**Goal:** enterprise design system — one change affects whole project · styles centrally
owned · templates mostly intact · backend untouched · React/Tailwind-portable later.

---

## 0. GLOBAL CONTRACT (applies to all foundations)

### 0.1 Naming convention (BEM-lite, already the house style)
- **Block:** `.card`, `.btn`, `.stat-card`, `.field`. **Element:** `.card-header`,
  `.card-title`. **Modifier:** `.btn-primary`, `.btn-sm`, `.badge-active`.
- Page-scope wrapper = a page class on the root (`.product-list`, `.user-create`);
  page-specific CSS lives under it (`.product-list .foo`) so it can't leak.
- **Tokens:** `--<family>-<step>` → `--space-3`, `--radius-md`, `--fs-sm`,
  `--touch-min`, `--status-success-bg`. Colors keep existing names (`--copper`, `--ink`,
  `--stone`, `--cream`, `--surface`, `--text-primary`, `--border-card`, `--shadow-card`).

### 0.2 Token usage rules (the "change-once" guarantee)
- **Forbidden in templates:** raw hex, raw px radius, inline `font-size`, inline
  card/button chrome (border/shadow/padding that a primitive owns).
- **Required:** `var(--token)` for color/space/radius/typography/touch.
- **CSS can't `var()` inside `@media`** → breakpoints are documented constants
  (`xs 414 · sm 600 · md 768 · lg 1024`), enforced by review, not a live var.
- Adding a token = base.html `:root` only. A literal that has a token = review-blocker.

### 0.3 Ownership rule
One concern → one owner file. base.html owns tokens + primitives (`.btn`/`.card`/
`.badge`/`.stat-card`/`.empty-state`) + behaviors (`fancify`/`fancifyDate`/
`initFancyDataTable`). Shared partials own composed surfaces (`_form_styles`, vendor,
`_auth_shell`, `financial/*`, `_export_buttons`).

### 0.4 Responsive + a11y baseline (every foundation inherits)
- Mobile-first FUNCTIONAL. Verify 320/375/390/414/1280. `scrollWidth===innerWidth`.
- Touch targets ≥ `--touch-min` (44px) for interactive controls.
- Focus-visible ring on all interactive controls. Labels/aria on inputs + icon-only buttons.
- Dark theme must work automatically (tokens-driven).

### 0.5 Promotion rule (page-scoped → shared) — global default
A pattern appears in **3+ templates** → promote to a base/shared owner. <3 → stays
page-scoped under its page class. Promotion updates UI_COMPONENTS.md (locked canon) same
session (docs-sync). Each foundation may tighten this; never loosen it.

### 0.6 Backend boundary
Spec governs **presentation only**. No view/service/context/URL/form-field-name change.
Money/auth/export logic stays server-side. Foundations are template+CSS+JS-asset only.

---

## FOUNDATION 1 — TOKENS

- **Purpose:** single source for color, surface, status, spacing, radius, typography,
  touch target, breakpoints. Everything else consumes these.
- **Shared owner:** `base.html` `:root` (+ `[data-theme="dark"]`).
- **Allowed classes:** none — tokens are CSS variables, not classes. Consume via
  `var(--token)` in owned CSS.
- **Forbidden patterns:** raw hex / raw px radius / inline `font-size` / magic spacing
  numbers in templates or component CSS; defining tokens anywhere but base.html `:root`;
  per-component color constants.
- **Token usage rules:** every visual value resolves to a token. Spacing on a 4px base
  (`--space-1=4 … --space-6=24`). One radius scale, one type scale, one `--touch-min`.
  Dark mode = override token values, never re-author components.
- **Naming conventions:** `--space-N` (N=step), `--radius-{sm,md,lg,pill}`,
  `--fs-{xs,sm,base,md,lg,xl}`, `--lh-{tight,base}`, `--touch-min`, `--control-h`.
  Colors keep current names.
- **Responsive rules:** breakpoint constants documented (not tokens); `--touch-min`
  applies across viewports.
- **Accessibility rules:** color tokens must meet contrast vs their paired surface
  (text-on-surface, status-text-on-status-bg). Verify in light + dark.
- **Promotion rule:** a literal value used in 3+ places MUST become a token before reuse.
- **Examples:**
  - ✅ `padding: var(--space-3) var(--space-4); border-radius: var(--radius-md);`
  - ❌ `padding: 12px 16px; border-radius: 10px;` (in a template/component)
  - ✅ `color: var(--text-secondary);`  ❌ `color: #7a6a58;`

---

## FOUNDATION 2 — BUTTONS

- **Purpose:** one button system, one geometry, themeable, touch-safe.
- **Shared owner:** `base.html` `.btn` + modifiers.
- **Allowed classes:** `.btn` (base, required) + ONE modifier: `.btn-primary` ·
  `.btn-copper` · `.btn-ghost` · `.btn-danger` · `.btn-filter` · `.btn-clear` ·
  `.btn-sm` (size). Combine base+variant+size: `class="btn btn-ghost btn-sm"`.
- **Forbidden patterns:** inline button chrome (`style="padding:4px 10px;font-size:12px"`)
  · variant WITHOUT `.btn` base (the old `:not(.btn)` divergence — banned after Foundation 2)
  · new ad-hoc button styles in page CSS · `<div>`/`<span>` as a button (use `<button>`/`<a>`).
- **Token usage rules:** geometry from `--radius-md`, `--space-*`, `--fs-*`; min-height
  `--touch-min` (`.btn-sm` may reduce padding but stays comfortably tappable on mobile);
  colors from `--copper`/`--status-*`.
- **Naming conventions:** `.btn-<intent|size>`. Intent: primary/copper/ghost/danger.
  Size: sm. Filter group: filter/clear.
- **Responsive rules:** full-width stack on ≤sm where the layout already does
  (`.page-header > .btn`, `.form-actions .btn`); `.btn-sm` for dense table-row actions.
- **Accessibility rules:** real `<button>`/`<a>`; focus-visible ring; icon-only ⇒
  `aria-label`; hit area ≥44px (sm = documented dense exception, still tappable).
- **Promotion rule:** a new button style in 3+ templates → new `.btn-*` modifier in
  base.html; else not allowed (use existing modifier or `.btn-sm`).
- **Examples:**
  - ✅ `<a href="…" class="btn btn-ghost btn-sm">Edit</a>`
  - ❌ `<a href="…" class="btn-ghost" style="padding:4px 10px;font-size:12px;">Edit</a>`
  - ❌ `<div class="my-button">Save</div>`  ✅ `<button class="btn btn-primary">Save</button>`

---

## FOUNDATION 3 — FORMS

- **Purpose:** one form chrome (layout/spacing/inputs/validation) across all create/edit/
  filter forms.
- **Shared owner:** `shared/_form_styles.html` (CSS) + `fancify`/`fancifyDate` (base.html JS)
  + one validation-error contract.
- **Allowed classes:** form-shell system `.sf-*` (hero + numbered panels + cream inputs +
  chip pickers + sticky bar) for create/edit; `.field` (label+control+error) for
  light/admin/inline forms; `.form-error`/`.field-error` for messages; `.sf-input` for
  fancified inputs/selects; `data-fancy-date` to opt a date input in.
- **Forbidden patterns:** white-on-white inputs (cream bg + inset shadow required) ·
  inline input/label CSS · swallowing field errors (must render per-field, CC-29) ·
  re-implementing select dropdowns (use `fancify`) · bare Django multiselect where a chip
  picker is the pattern (CC-20 retired) · merging `.field` and `.sf-*` into one (kept separate).
- **Token usage rules:** spacing/rhythm from `--space-*`; input bg `--surface-input`,
  focus `--surface-input-focus`; label `--text-secondary`; error `--danger`; control
  height `--control-h` (39px) for fancified triggers.
- **Naming conventions:** `.sf-*` for form-shell, `.field`/`.field-error` for the light
  system, `.form-*` for shared form bits. Page-specific form CSS under page class only.
- **Responsive rules:** `.form-grid` reflows to single column ≤sm; sticky CTA bar full-
  width on mobile; chip pickers wrap; no horizontal overflow. Shared partial owns its own
  responsive CSS (gotcha: scoping must not assume a `.form-shell` ancestor).
- **Accessibility rules:** every input a `<label>` (or `aria-label`); errors associated
  with field; focus-visible; touch ≥44px on inputs/selects/chips; the `--bare` fallback
  guarantees unclassed selects still get a 44px box.
- **Promotion rule:** a form pattern in 3+ forms → into `_form_styles.html`; one-off layout
  stays page-scoped. New select/date behavior → extend `fancify`/`fancifyDate`, never a new picker.
- **Examples:**
  - ✅ `{% include 'shared/_form_styles.html' %}` then `<input class="sf-input">`
  - ✅ per-field: `{% if form.x.errors %}<div class="field-error">{{ form.x.errors.0 }}</div>{% endif %}`
  - ❌ `<input style="background:#fff;border:1px solid #ccc;font-size:14px;">`
  - ❌ rendering only `{{ form.non_field_errors }}` and dropping field errors

---

## FOUNDATION 4 — TABLES

- **Purpose:** one list-table engine (search/sort/paginate) + one responsive contract.
- **Shared owner:** `initFancyDataTable(selector, opts)` (base.html) + `_datatables_
  vendor_css.html`/`_datatables_vendor_js.html` (per-page include) + `.table-responsive`/
  `data-label` contract.
- **Allowed classes:** `.tbl` (table) inside `.table-responsive`; `td[data-label="…"]`
  on every cell; `.td-actions`/`.action-link` for the action column; `.empty-state` /
  `{% empty %}` row; `.dt-filter-row`/`.skill-filter-chip` for the shared filter row.
  Init via `initFancyDataTable('#id', {pageLength,itemName,searchPlaceholder,columnDefs,filterRowId})`.
- **Forbidden patterns:** calling `.DataTable()` directly (only inside the helper) ·
  a table without `.table-responsive` wrapper (data-label is INERT without it) ·
  missing `data-label` on cells · per-page DataTable CSS/JS forks · forcing TC-2 exceptions
  (workflow queue / inline editor / matrix / dashboard summary) onto DataTable · totals
  INSIDE the engine for convertible ledgers (keep in `<tfoot>`/outside).
- **Token usage rules:** table chrome from tokens; status cells use `--status-*`; money
  cells defer to Financial (§7).
- **Naming conventions:** id `#<thing>-dt`; `itemName` = plural noun; non-sortable cols via
  `data-orderable="false"` th (not hardcoded columnDefs index when columns are dynamic).
- **Responsive rules:** mandatory — `.table-responsive` + `data-label` card-stack
  (`td{display:flex}`+`::before`) OR explicit scroll/summary strategy. Form-input cells
  clip (need cell-edit stacking); text cells wrap. Verify 0 overflow at 320.
- **Accessibility rules:** `<thead>` headers; action links real `<a>`; touch ≥44px
  (current `.action-link` ≈23px = debt to fix); search input labeled.
- **Promotion rule:** any new CRUD/list table → TC-1 (no new table system). A genuinely new
  exception type (beyond the 5) needs evidence before a new foundation.
- **Examples:**
  - ✅ `<div class="table-responsive"><table id="products-dt" class="tbl">…<th data-orderable="false">Actions</th>…<td data-label="Code">…</td></table></div>` + `initFancyDataTable('#products-dt',{itemName:'products'})`
  - ❌ `<table>…</table>` with no `.table-responsive` + `$('#t').DataTable()` inline
  - ❌ data-label cells with no `.table-responsive` ancestor (stack silently dead)

---

## FOUNDATION 5 — CARDS

- **Purpose:** one set of card primitives; page card SYSTEMS consume them, never re-author chrome.
- **Shared owner:** `base.html` `.card`/`.card-header`/`.card-title`/`.card-clip` ·
  `.stat-card` · `.kpi` · `.badge` · `.empty-state`.
- **Allowed classes:** the primitives above; `.stat-card` (+ `.payable` etc. value
  modifiers) = the SummaryCards primitive shared with Financial; page card systems add
  LAYOUT under a page class (`.dashboard .grid`), not chrome.
- **Forbidden patterns:** inline card chrome (border/radius/shadow/header) · re-defining
  `.card` look in page CSS · a new card style copied across pages without promotion ·
  using a `<div>` styled as a card instead of `.card`.
- **Token usage rules:** chrome from `--border-card`, `--shadow-card`/`--shadow-card-hover`,
  `--radius-lg`, `--space-*`, `--surface`. Already mostly tokenized — finish it.
- **Naming conventions:** `.card`/`.card-*` for the primitive; page systems = `.<page> .<thing>-card`.
- **Responsive rules:** cards stack to single column ≤sm; padding shrinks via tokens; no overflow.
- **Accessibility rules:** card title = real heading where it's a section; interactive cards
  keyboard-reachable; sufficient contrast on `.badge`/`.stat-card` values.
- **Promotion rule:** card variant in 3+ templates → base modifier; else page-scoped.
  Dashboard/detail/timeline systems stay page-scoped CONSUMERS (documented, not foundations).
- **Examples:**
  - ✅ `<div class="card"><div class="card-header"><div class="card-title">Batches</div></div>…</div>`
  - ✅ `<div class="stat-card payable"><div class="label">Payable</div><div class="value">₹360</div></div>`
  - ❌ `<div style="background:#fff;border:1px solid #cfc0aa;border-radius:12px;box-shadow:…">`

---

## FOUNDATION 6 — AUTH

- **Purpose:** one auth shell for all 7 auth pages; zero chrome duplication; backend/security intact.
- **Shared owner:** `shared/_auth_shell.html` (chrome) + Form (§3) inputs + Button (§2).
- **Allowed classes:** the auth-shell classes (brand + centered/split card + slot);
  inputs via `.sf-*`/`.field`; submit via `.btn .btn-primary`.
- **Forbidden patterns:** copy-pasting the auth layout into each page (the 7-copy debt
  being removed) · per-page auth CSS forks · **changing any POST field name, CSRF, redirect,
  or rate-limit behavior** (security — template-only) · inventing auth-only inputs/buttons.
- **Token usage rules:** all chrome via tokens; same `--surface`/`--page-bg`/brand colors;
  no auth-specific hardcoded values.
- **Naming conventions:** `_auth_shell.html` + a single `.auth-*` namespace; each page
  supplies only its form block + copy.
- **Responsive rules:** centered card, full-width ≤sm, no overflow, inputs/buttons ≥44px;
  works 320→1280.
- **Accessibility rules:** labeled inputs, focus order, error announcement, `autocomplete`
  hints preserved; OTP inputs labeled.
- **Promotion rule:** auth is a closed set (7) → one shell owns all; new auth page extends
  the shell, never forks.
- **Examples:**
  - ✅ `{% extends 'shared/_auth_shell.html' %}{% block auth_form %}…login form…{% endblock %}`
  - ❌ each of login/signup/otp re-declaring the same brand + card + background markup
  - ❌ renaming `password`/`email`/`otp` POST fields while restyling (breaks backend/rate-limit)

---

## FOUNDATION 7 — FINANCIAL (TC-3)

- **Purpose:** one financial component set so every money surface looks/behaves identically;
  presentation only, money logic stays server-side.
- **Shared owner:** `shared/financial/*` partials + scoped CSS (built on tokens + `.stat-card`
  + `--status-*` + `initFancyDataTable` where convertible).
- **Allowed classes / primitives:** SummaryCards (`.stat-card`) · MoneyCell · StatusPill ·
  LedgerGrid · TotalsBar · LedgerEmpty · ResponsiveLedger.
- **Forbidden patterns:** per-page money-table CSS forks · hand-formatting ₹ inline in
  many templates · status pills built from raw colors instead of `--status-*` · putting
  totals INSIDE the DataTable body · **performing money math in the template** (format only)
  · touching money services/figures while restyling.
- **Token usage rules:** money text via type tokens, right-aligned; pills via `--status-*-bg/text`;
  cards via `--stat-card`/`--copper`.
- **Naming conventions:** `.money` / `.money--neg` / `.pill pill--<status>` / `.ledger-*`
  under a `shared/financial/` namespace.
- **Responsive rules:** money tables get a defined mobile strategy (stack/summary) — never
  raw horizontal clip; totals visible on mobile; verify against real figures at 320.
- **Accessibility rules:** money right-aligned + screen-reader-sane; pills have text not
  color-only; totals row labeled; tables follow §4 a11y.
- **Promotion rule:** any money-presentation pattern in 2+ surfaces → into `financial/*`
  (financial debt threshold tighter than global 3, because trust-sensitive). Structural
  exceptions (grouped settlement workflow) documented, kept.
- **Examples:**
  - ✅ `{% include 'shared/financial/money_cell.html' with amount=line.total %}`
  - ✅ `<span class="pill pill--success">Settled</span>` (from `--status-success-*`)
  - ❌ `<td style="text-align:right">₹{{ a|floatformat:2 }}</td>` repeated across 6 templates
  - ❌ `{{ a }} + {{ b }}` math in template · reopening golden ₹225 chain to test

---

## FOUNDATION 8 — EXPORT (TC-5)

- **Purpose:** one export-button group; no duplicated inline export forms.
- **Shared owner:** `shared/_export_buttons.html` (params: csv/xlsx/pdf urls + optional quick-CSV).
- **Allowed classes:** `.btn .btn-ghost` (tokenized) inside the partial's form group;
  include the partial, pass urls.
- **Forbidden patterns:** copy-pasting the 3-form CSV/XLSX/PDF group inline (the dup being
  removed) · placing export forms INSIDE `.dataTables_wrapper`/the table · dropping CSRF ·
  emitting un-escaped cells (formula-injection — PA-13-6 protection stays) · changing export
  view URLs/method.
- **Token usage rules:** buttons via Button foundation tokens; no export-specific chrome.
- **Naming conventions:** `_export_buttons.html`; `.export-actions` wrapper.
- **Responsive rules:** button group wraps (`flex-wrap`) on mobile; stays in card-header /
  page-level, outside the table; touch ≥44px.
- **Accessibility rules:** each export = a labeled `<button>` in a real `<form>`; group
  reachable by keyboard.
- **Promotion rule:** export-button group is shared the moment it appears in 2+ pages (already does).
- **Examples:**
  - ✅ `{% include 'shared/_export_buttons.html' with csv_url=… xlsx_url=… pdf_url=… %}` in `.card-header`
  - ❌ three `<form>`s with CSV/XLSX/PDF buttons duplicated inline on each export page
  - ❌ export `<form>` nested inside `.table-responsive`/the DataTable wrapper

---

## 9. ENFORCEMENT + PORTABILITY

- **Review gates:** new raw hex / px-radius / inline `font-size` / inline card-or-button
  chrome / `.DataTable()` outside the helper / table without `.table-responsive` /
  duplicated auth-or-export chrome = **review-blockers**.
- **Docs-sync:** any promotion/owner change updates UI_COMPONENTS.md (locked canon) same
  session; this SPEC + ARCHITECTURE + ROADMAP stay aligned.
- **Portability (React/Tailwind later):** tokens → theme config; primitives (`.btn`/`.card`/
  `.stat-card`/MoneyCell/StatusPill) → components; shared partials → composable components;
  strict ownership = one source per concern = clean port. Keeping style in tokens/classes
  (never inline) is what makes the future migration mechanical.
- **Backend:** untouched throughout. Spec is presentation-only.

---

**No code authorized. No tokens created.** This is the contract. Foundation 1 (Tokens)
implementation begins only on explicit owner approval, per the ROADMAP, one foundation at a time.
