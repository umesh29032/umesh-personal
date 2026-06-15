# UI Components — Kapil Enterprises Inventory

Component vocabulary for templates. All CSS lives in `config/accounts/templates/accounts/base.html` (single source of truth). Page-specific overrides go in each page's `{% block extra_head %}` scoped under a page-specific class.

**Rule:** Before writing CSS on a page, search this file. If component exists → use it. If 80% match → extend with a modifier. If novel → add to base.html, then add it here.

---

## Layout

| Class | Purpose | Notes |
|---|---|---|
| `.shell` | App root — sidebar + main content flex container | Set on `<body>` direct child |
| `.sidebar` | Left nav rail | Auto-collapses to overlay on ≤768px |
| `.content` | Main scrollable content area | `overflow-y: auto`, padding scales by breakpoint |
| `.topbar` | Top header strip | Hamburger button on mobile |

## Page-level chrome

| Class | Purpose |
|---|---|
| `.page-header` | Title + actions row at top of page |
| `.page-header-text h1` | Page title (26px serif) |
| `.page-header-text p` | Page subtitle (smoke color) |

## Production template patterns (merged from docs/archive/production/UI_PATTERNS.md, 2026-06-12)

| Pattern | How |
|---|---|
| Time-log accordion | `{% include 'inventory/_time_log_styles.html' %}` in extra_head + `_roll_events_accordion.html` / `_adda_events_accordion.html` with `roll_events`/`adda_events` context (select_related, latest 30). Native `<details>/<summary>`, no JS |
| QR print sheet | `barcode_print_sheet.html` — standalone (no base), A4 grid, ECC-Q; `?size=` small 54/A4 · medium 35 · large modes |
| Worker roster chips | `_workers_widget.html` via `_WorkerCheckboxes`; chip CSS canonical in base.html (S1-4) |
| Hinglish comments | templates may use Hinglish in comments; `{# #}` is SINGLE-line only — multi-line MUST use `{% comment %}` (regression history) |
| Shared partials | `production/_form_styles.html` (form-shell) · `_autosave.html` · `_stage_panel_collapse.html` · `inventory/_time_log_styles.html` |
| Empty states | every list/table renders an explicit `.empty` row — never a blank card |

## Template checklist (new pages + updating old pages) — owner rule 2026-06-12

**NEW page:** extends base · page-class wrapper · page CSS only in extra_head
under that class · COMPOSE FROM CANONICALS first (`hero-strip copper` for
money screens — never swap a page's hero variant, that's a re-theme · `.panel`
· `.stat-grid/.stat-card` · `.sticky-bar` · bare `.btn-copper/-ghost/-danger`,
never mixed with `.btn`) · page keeps only TRUE extras as modifiers · tables =
`.table-responsive` + `td[data-label]` (no min-width on stacking tables — F1)
· DataTables → `shared/_datatables_vendor_*` partials, filters OUTSIDE the
responsive wrapper · rule-11 verify 360/768/1280 (cache-busted) before "done"
· `inputmode` on numbers, `aria-label` on icon buttons, `.empty` states ·
no logic in templates (context flags gate forms; display always renders) ·
`confirm()` on money/destructive (completion = P2 pending-workers list) ·
`{# #}` single-line only, multi-line = `{% comment %}`.

**UPDATING old pages:** migrate its duplicated CSS to canonicals while you're
there (one page = one commit) · unexpected drift → revert, never redesign ·
re-verify 3 viewports after ANY edit · docs-sync (CLAUDE rule 12): pattern or
page-list changed ⇒ update this file + the app GUIDE same session.

## Money-family vocabulary (A-scope 2026-06-12) — REFERENCE for G4 / MissingPiece / Alter UIs

The settlement/payroll screens are the reference implementations. Every future
money or list+detail UI composes THESE classes from base.html — do not redefine.

| Class | Purpose | Notes |
|---|---|---|
| `.hero-strip.copper` | Money-screen page hero (copper gradient, h1 20px) | Plain `.hero-strip` = the navy default. Page may add a flex modifier for hero actions/totals |
| `.panel` | Content card: card-bg, radius 14, shadow, padding 16, mb 18 | Page modifiers only for real needs (e.g. `padding:16px 0 4px` table-bleed) |
| `.stat-grid` / `.stat-card` | KPI cards (label uppercase 11px / value 22px; `.payable` → copper value) | auto-fit minmax(140px); 2-col on ≤560px |
| `.sticky-bar` | Frosted bottom action bar (sticky, blur, right-aligned) | Dark-theme variant included |
| `.btn-copper` / `.btn-ghost` / `.btn-danger` (standalone, WITHOUT `.btn`) | Money-screen buttons: radius 10, font 13/700, 40px min-height | `:not(.btn)` shapes — combining with `.btn` keeps the classic 6px-radius system instead |
| stacked table (`.table-responsive` + `td[data-label]`) | THE responsive-table standard for all future lists | thead hidden ≤ breakpoint; label:value rows; F1 fix guarantees width |

## Cards & panels

| Class | Purpose | When |
|---|---|---|
| `.card` | Standard data card — border + soft shadow | Most container needs |
| `.card.card-clip` | Card with `overflow: hidden` | Wrap tables to clip border-radius |
| `.card-header` | Card header strip | Inside `.card` |
| `.card-title` | Header title text (uppercase tracked) | Inside `.card-header` |
| `.card-body` | Card padding (24px) | Inside `.card` |
| `.kpi` | KPI/stat card — accent strip + label + value | Used in grids of 3-4 |
| `.kpi-accent` | Color bar at top of KPI | Style with `background:` inline |
| `.kpi-label` | Tiny uppercase label | Above value |
| `.kpi-value` | Big number | The stat |
| `.kpi-sub` | Helper text below | Optional |
| `.kpis` | Grid wrapper for KPI cards | Responsive 1/2/3/4-col |

## Tables

| Class | Purpose |
|---|---|
| `.table-responsive` | Wrap any `<table>` — adds horizontal scroll on overflow |
| `.tbl` | Base table styles (alternate to inline-styled tables) |
| `.tbl-wrap` | Wrapper with rounded corners + horizontal scroll |
| `td[data-label="X"]` | Required on EVERY `<td>` — turns into stacked card row at ≤600px |
| `.td-actions` | Add to actions `<td>` — full-width button row on mobile |

**⚠ Never ship a bare `<table>` (PA-14-1).** Page content sits inside `main.content { overflow-x: hidden }`, so a table wider than the viewport is **clipped with no scroll** — the rightmost columns (often money: "Final payable ₹", "Recovered ₹") become invisible and unreachable on a phone. Wrap EVERY `<table>` in `.table-responsive` AND put `data-label` on every `<td>`. The wrapper gives desktop horizontal-scroll and, at ≤600px, switches to stacked label:value cards. This includes detail/snapshot tables (e.g. settlement detail), not just DataTables lists.

## DataTables — list pages

Use the helper, NOT manual init. CSS overrides are global.

```html
<!-- HEAD -->
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css">

<!-- CARD -->
<div class="card card-clip">
  {% if has_filter %}
  <div id="dt-xxx-filter" class="dt-filter-row" style="display:none;">
    <form method="get" style="display:contents;">...</form>
  </div>
  {% endif %}
  <div class="table-responsive"><table id="xxx-dt">...</table></div>
</div>

<!-- SCRIPTS -->
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
<script>
$(document).ready(function () {
  if (!$('#xxx-dt').length) { $('#dt-xxx-filter').show(); return; }
  initFancyDataTable('#xxx-dt', {
    pageLength: 15,
    itemName: 'things',
    searchPlaceholder: 'Type to filter things…',
    filterRowId: 'dt-xxx-filter',           // omit if no filter
    columnDefs: [{ orderable: false, targets: [0, 4] }]
  });
});
</script>
```

| Class / Helper | Purpose |
|---|---|
| `initFancyDataTable(sel, opts)` | DataTable init + DOM detach fix in one call (defined in base.html) |
| `.dt-search-row` | Generated by DT — styled globally |
| `.dt-bottom` | Pagination row — styled globally |
| `.dt-filter-row` | Add to your filter div — single-row horizontal scroll, surface-2 bg |

## Filter chips

| Class | Purpose |
|---|---|
| `.skill-filter-chip` | Pill-shaped toggle chip — copper when `.active` |
| `.filter-select` | Native-style select with custom arrow (legacy, fancy-select replaces these globally) |
| `.ke-toolbar` | Standalone filter strip ABOVE card (avoid — prefer `.dt-filter-row` INSIDE card) |

### `.filter-card` — horizontal filter bar (MUST stack on mobile, PA-14-2)

The page-scoped `.filter-card` pattern (`display:flex; flex-wrap:nowrap; overflow-x:auto` with `min-width` fields) lays filters out in a horizontal row on desktop. On a phone that row **scrolls sideways** — fields get cut mid-field and later filters are hidden with no scroll affordance. **Every `.filter-card` MUST add a `@media (max-width: 600px)` rule that stacks it vertically:**

```css
@media (max-width: 600px) {
    .<page-scope> .filter-card { flex-direction: column; align-items: stretch; overflow-x: visible; }
    .<page-scope> .filter-card .field { width: 100%; }
    .<page-scope> .filter-card input,
    .<page-scope> .filter-card select { width: 100%; min-width: 0; }
}
```

Applied to roll-list, adda-list, adda-dashboard, cloth-dashboard, barcode/tracking-dashboard. Mirror it on any new filter bar.

## Forms

Two parallel form styles. Pick one per page. Don't mix.

### Style A: `.field` (used by user, skill, batch, cloth, etc.)
Include `{% include 'accounts/_user_form_styles.html' %}` at end of `{% block extra_head %}` to pull in these styles.

| Class | Purpose |
|---|---|
| `.field` | Form field wrapper (label + input vertically stacked) |
| `.field label` | Field label (12px uppercase) |
| `.field input/select/textarea` | Auto-styled — cream bg, inset shadow, copper focus |
| `.field-grid-2` | 2-col grid inside a panel |
| `.field-error` | Red error text under field |
| `.panel` | Numbered section card — `<header class="panel-head"><span class="panel-num">01</span>...` |
| `.panel-body` | Padded content area inside `.panel` |
| `.chip-pick` | Single-select chip (replaces native `<select>` visually) |
| `.switch-row` | Toggle row with label + switch |
| `.sticky-actions` | Fixed action bar at bottom of form |

### Style B: `.sf-*` (storefront forms — rounder corners, softer look)

| Class | Purpose |
|---|---|
| `.sf-field` | Field wrapper |
| `.sf-label` | Label |
| `.sf-input` | Input/select/textarea — auto-applies select arrow if `<select>` |
| `.sf-hint` | Helper text below input |
| `.sf-error` | Error text |
| `.sf-footer` | Sticky form footer with action buttons |

## Form widget classes (Django)

| Class | Purpose |
|---|---|
| `.form-control` | Generic form input (alternate to `.field`-style) |
| `.form-label` | Generic form label |
| `.form-group` | Vertical field stack |
| `.form-hint` | Helper text |
| `.form-error` | Error text |
| `.form-actions` | Sticky action bar (generic — see also `.sticky-actions`, `.sf-footer`) |

## Multi-box input groups (OTP `.otp-row` / `.otp-digit`) — mobile rule

Proven by the Phase-02 audit fix (PA-02-4). When a row holds many fixed-size
boxes (the 6-digit OTP inputs: `.otp-row` of `.otp-digit`, optionally split by a
decorative `.otp-sep`), the boxes must stay touch-usable on the smallest phones:

- `.otp-digit` uses `flex: 1 1 0` so the boxes share the row width evenly.
- At `@media (max-width: 480px)` shrink height/font (`height: 52px; font-size: 24px;`) — **keep this consistent across all OTP pages** (login `otp.html`, signup, reset). reset_otp.html was missing it; that was the bug.
- At `@media (max-width: 360px)` **drop the decorative separator** (`.otp-sep { display: none; }`), tighten the gap (`.otp-row { gap: 4px; }`) and reduce card padding so each box reaches ~39–46px wide instead of ~30px. Decorative dividers are the first thing to sacrifice for touch width on narrow screens.
- Target ≥44px touch width where the box count allows; document the residual if the count makes 44px impossible at 320px (6 boxes cannot, ~39px is the achievable floor — acceptable for single-char numeric input).

## Selects — fancy-select (automatic)

Just write `<select>`. base.html JS auto-upgrades to custom dropdown that escapes iframe/transform/overflow clipping bugs.

| Attr / Class | Purpose |
|---|---|
| `<select data-no-fancy>` | Opt out of upgrade (keeps native dropdown) |
| `.fancy-select` | Wrap div (auto-generated) |
| `.fancy-select-trigger` | Button replacing visual `<select>` (copies the select's **classes**) |
| `.fancy-select-trigger--bare` | Auto-added fallback box when the select had **no class** (cream box + 44px touch target) |
| `.fancy-select-panel` | Dropdown options panel (auto-rendered in `<body>` when open) |
| `.fancy-select-option` | Each option in panel |

CSS that targets the select **by a class** (`select.form-control` / `.sf-input` / `.filter-select`) is applied to `.fancy-select-trigger` because the JS copies the select's `className` onto the trigger.

**⚠ Mobile gotcha (PA-14-3):** the trigger is a `<button>`, NOT a `<select>` — so page CSS that styles selects **by tag name** (`.my-form select { … }`) does NOT reach it. A class-less `<select>` would otherwise render as a bare ~20px UA-styled line (sub-44px touch target, visually inconsistent with sibling inputs). base.html now auto-adds `.fancy-select-trigger--bare` to class-less triggers so they always get a default input box. **Best practice when styling form selects: put a styling class on the `<select>` (`class="sf-input"`), or target `.fancy-select-trigger` alongside `select` in your page CSS — never rely on a tag-only `select{}` rule.**

## Buttons

| Class | Purpose |
|---|---|
| `.btn` | Base button |
| `.btn-primary` | Copper filled CTA |
| `.btn-ghost` | Bordered, transparent |
| `.btn-danger` | Red filled |
| `.btn-copper` | Same as primary (used in form contexts) |
| `.action-icon` | Icon-only action button (32×32) for table rows |
| `.action-icon-danger` | Red hover variant |
| `.action-link` | Text + icon link for table actions |
| `.action-link-danger` | Red hover variant |
| `.hamburger` | Mobile sidebar toggle |

## Badges & status

| Class | Purpose |
|---|---|
| `.badge` | Pill base |
| `.badge-active` / `.badge-inactive` | Status pills |
| `.badge-planned` / `.badge-wip` / `.badge-completed` / `.badge-cancelled` | Batch lifecycle |
| `.badge-available` / `.badge-reserved` / `.badge-exhausted` | Stock states |
| `.badge-dot` | Small dot inside badge |
| `.skill-tag` | Inline skill chip inside table rows (different from `.skill-filter-chip`) |

Use `var(--status-*-bg/text)` tokens for custom badges — they auto-flip in dark mode.

## Empty state

| Class | Purpose |
|---|---|
| `.empty-state` | Centered placeholder when list is empty |
| `.empty-icon` | Icon at top |

## Messages (Django messages framework)

| Class | Purpose |
|---|---|
| `.msg` | Message base (slides down) |
| `.msg-error` / `.msg-success` / `.msg-info` / `.msg-warning` | Variants |
| `.msg-stack` | Container for stacked messages |

## Tabs

| Class | Purpose |
|---|---|
| `.tabs` | Tab nav row |
| `.tab-btn` / `.tab-btn.active` | Individual tab |
| `.tab-panel` / `.tab-panel.active` | Tab content panel |

## Hero strips

Each app has its own hero variant (`.user-hero`, `.product-form-hero`, etc.). These are page-specific. For new hero strips, use inline style with linear-gradient on `#0a1628 → copper` for inventory pages, `#130428 → copper` for accounts/user pages.

---

## Design tokens (CSS vars)

### Colors

| Token | Value | Use |
|---|---|---|
| `--ink` | `#0e0b09` | Primary text |
| `--copper` | `#b87333` | Primary CTA, accents, active states |
| `--copper-l` / `--copper-d` | Hover / pressed | |
| `--cream` | `#f5ede0` | Warm surface |
| `--cream-2` | `#ede3d4` | Secondary surface |
| `--cream-3` | `#e2d5c3` | Subtle borders |
| `--stone` | `#7a6a58` | Secondary text |
| `--page-bg` | `#f7f3ee` | Page background |
| `--border-card` | `#cfc0aa` | **All card/panel borders** |
| `--shadow-card` | `0 2px 12px rgba(14,11,9,0.10)` | Default card shadow |
| `--shadow-card-hover` | Bigger shadow | Hover |

### Status tokens (auto-flip in dark mode)
- `--status-success-bg/text`
- `--status-warning-bg/text`
- `--status-danger-bg/text`
- `--status-info-bg/text`
- `--status-neutral-bg/text`

### Semantic
- `--text-primary` / `--text-secondary` / `--text-tertiary`
- `--surface` / `--surface-2` / `--surface-3` / `--surface-input`
- `--border-default` / `--border-subtle`
- `--card-bg` / `--white`

---

## Page-specific overrides — pattern

```html
{% block extra_head %}
<style>
/* Scope under .my-page so overrides can't leak elsewhere */
.my-page .field-grid-2 { grid-template-columns: 1fr; }
.my-page .card { padding: 12px; }
</style>
{% endblock %}

{% block content %}
<div class="my-page">
  ...
</div>
{% endblock %}
```

---

## Naming convention (BEM-lite)

- `.block` — standalone component (`.card`, `.kpi`, `.btn`)
- `.block-element` — child of block (`.card-header`, `.kpi-label`, `.field-error`)
- `.block--modifier` — variant of block (`.btn-primary`, `.btn-ghost`, `.badge-active`)

Modifiers use single dash for legacy compatibility (`.btn-primary` not `.btn--primary`).

---

## When to add a new component to base.html

Trigger: same CSS pattern appears in **3+ templates**.

Process:
1. Define the class in `base.html` with a comment block explaining purpose
2. Update all template uses
3. Add a row to this file under the right section
4. Mention it in commit message
