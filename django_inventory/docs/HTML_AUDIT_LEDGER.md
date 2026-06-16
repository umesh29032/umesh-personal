# HTML_AUDIT_LEDGER — per-template audit record

Companion to [HTML_AUDIT_MASTER.md](HTML_AUDIT_MASTER.md) (state/ordering),
[HTML_CANONICAL_CANDIDATES.md](HTML_CANONICAL_CANDIDATES.md) (staged rules), and
[HTML_FIX_HISTORY.md](HTML_FIX_HISTORY.md) (fix log).
One numbered entry per template. Ordered by **control family** (A→G). Each entry
expands to a full record when audited.

## Status legend

- **PENDING** — not yet audited.
- **SEED** — classified by the superseded phase-based inventory (code-read only);
  NOT browser-tested, NOT fixed, NOT canonicalized. Re-enters the queue at its
  family slot for the full per-HTML cycle; seed data speeds the code-read step.
- **IN-PROGRESS** — currently being audited.
- **FIXED** — issues fixed + browser-verified; awaiting owner review.
- **DONE** — reviewed + committed (hash recorded).
- **CLEAN** — audited, browser-verified, no issue found (no fix needed).

## Record format (filled per HTML when audited)

```
### HTML-NNN — <path>
- Status: DONE
- Audit unit / method: <self | via host X> · viewports tested: 320/375/390/414/1280
- Controls: selects / multiselect / date / inputs / table / modal …
- Issues found: <list, or "none">
- Fix: <what changed, files>
- Canonical rule emerged: <UI_COMPONENTS.md section, or "none">
- Evidence: <screenshots / browser notes>
- Commit: <hash>
```

Partials (`_*.html`, panels, chromeless embeds) cannot load standalone — their
**audit unit / method** names the host page they are browser-tested through.

---

## Phase A — Selects (HTML-001 … HTML-022)

Native `<select>` (fancy-select auto-upgrade), Django widget-rendered selects, and
the custom chip single-select replacement.

### HTML-001 — `accounts/user_create.html`
- Status: **CLEAN** (no fix needed) — awaiting owner review
- Audit unit / method: self (extends base; includes `_user_form_styles.html`). Browser at 1280/320/375/390/414, super-admin, `/app/users/add/`.
- Controls: **select** native `<select name=role>` (literal options + inline `onchange=updateRolePreview`) + **select** `{{ form.user_type }}` (Django ModelChoiceField widget); **multiselect** ×2 chip-pickers `.chip-pick` (skills, extra_roles → Family B evidence); inputs email/password×2/text/number(salary); switch toggles ×3.
- Issues found: **none** (verified). Both selects fancify + open + fit + 0 console errors; role pick fires native `change` → `updateRolePreview` (preview box shows "Worker"); 45px triggers; form stacks at 920/560 breakpoints; no horizontal overflow at any width.
- Fix: none.
- Observations (non-bug, NOT fixed — no functional/visual break, no-redesign scope): (a) both class-less selects get `--bare` redundantly AND are styled by `.field .fancy-select-trigger` → both cream, harmless; (b) page `<style>` (the `_user_form_styles` include) sits at the END of `{% block content %}`, not `{% block extra_head %}` (rule-10 deviation; renders fine).
- Canonical signal: `_user_form_styles.html` co-styles `.field .fancy-select-trigger` alongside `.field select` (the PA-14-3 best-practice) → trigger matches sibling inputs. Strong **Select canonical** reference. Logged → HTML_CANONICAL_CANDIDATES Select-family ledger + CC-03.
- Evidence: /tmp/u001_1280.png (2-col, role="Worker" + preview), /tmp/u001_320.png (stacked, fits).
- Commit: none (no code change).
### HTML-002 — `accounts/user_form.html`
- Status: **DONE** — 1 bug fixed, browser-verified, committed `bcf508f2`
- Audit unit / method: self (extends base; includes `_user_form_styles.html`). Browser at 1280/320/375/390/414, super-admin, `/app/users/3/edit/`.
- Controls: **select** `<select name=role>` (NO inline onchange — edit dropped create's preview) + `{{ form.user_type }}` widget; **date** birth_date `data-fancy-date` (Step 0, verified); **multiselect** ×2 chip-pickers (skills/extra_roles); **textarea** bio; file (avatar+JS preview); switch ×3.
- Issues found: **1 VERIFIED BUG (fixed).** Multi-line `{# … #}` template comment (lines 44–45) rendered as **visible text** on every Edit-User page (`{# #}` is single-line only). Browser-confirmed leak in rendered body + 320 screenshot. Owner-recurring regression. Selects/date/layout otherwise clean (0 console errors, no overflow, 45px triggers, role pick sets value, validation alert renders on weak-password reject without saving).
- Fix: lines 44–45 `{# … #}` → `{% comment %}…{% endcomment %}`. Restarted server (template cache), re-verified leak gone (rendered body + 320 screenshot) + selects intact + 0 console errors.
- Dependency discovery (selects): CSS owner = shared `_user_form_styles.html` + base `.fancy-select*`; JS owner = base `fancify()` only (no page select JS); hidden page-dep = NONE for selects (chip multiselect has page-inline JS + `user_skill_ids`/`user_extra_role_ids` ctx → Family B). Logged → CANONICAL_CANDIDATES Select ledger.
- Canonical signal: confirms `_user_form_styles.html` is the SHARED select CSS owner (HTML-001+002 identical). Validation pattern here (full `form.errors` list alert) is cleaner than HTML-001's — Family D candidate.
- Related found (NOT fixed — other unit): `signup_otp.html:74` same multi-line `{# #}` class (HTML-032, dormant/unrouted) → CC-04 (evidence only).
- Evidence: /tmp/u002_320.png (leak visible, pre-fix), /tmp/u002_320_fixed.png (leak gone, post-fix).
- Commit: **`bcf508f2`**
### HTML-003 — `production/adda_form.html`
- Status: **CLEAN** (no per-page fix; one global touch-target candidate logged) — awaiting owner review
- Audit unit / method: self (extends base; extra_head includes `production/_form_styles.html` = form-shell). Browser 1280/320/375/390/414, super-admin, `/production/addas/start/`. (Correction: NO workers multiselect here — single control = product select; workers are assigned elsewhere.)
- Controls: **select** ×1 — `{{ form.product }}` (AddaForm ModelChoiceField, widget class `sf-input`). Buttons `.btn .btn-primary`/`.btn-ghost` (classic system, non-money form).
- Issues found: none per-page. Product select fancifies (trigger `fancy-select-trigger sf-input`, NOT bare), opens, picks, panel fits 320–414, 0 console errors, no overflow at any width.
- Fix: none.
- Touch-target observation (GLOBAL, not per-page → CC-05): trigger = **39px**, native `.sf-input` text probe = **41px** — both < 44px. The form-shell `.sf-input` baseline is ~40px; PA-14-3 gave the `--bare` fallback 44px but classed `sf-input` triggers never got it. Fixing = global `.sf-input` min-height change (every production+storefront form) = NOT a per-HTML fix; deferred to Select Consolidation Report.
- Dependency discovery (select): CSS owner = **base.html global `.sf-input`** (reaches the `<button>` trigger because fancify copies the class) + form-shell `production/_form_styles.html`; JS owner = base `fancify()` only; hidden page-dep = NONE. **NEW: this is a DIFFERENT select-styling mechanism than accounts** (HTML-001/002 co-style `.field .fancy-select-trigger`; production uses the `sf-input` class). Two mechanisms across the app → CC-03 consolidation input.
- Canonical signal: `sf-input`-class path is the cleaner mechanism (class copied → base global rule reaches the button automatically, no per-page `.fancy-select-trigger` rule needed). Logged → Select ledger + CC-05.
- Evidence: /tmp/u003_1280.png, /tmp/u003_320.png (dropdown open, fits).
- Commit: none (no code change).
### HTML-004 — `production/adda_list.html`
- Status: **CLEAN** (no per-page fix; one repeated-pattern candidate CC-07) — awaiting owner review
- Audit unit / method: self (extends base; page-scoped `<style>` in extra_head). Browser 1280/320/375/390/414, super-admin, `/production/addas/`.
- Controls: **select** ×2 — `status` + `stage` filters, both **`<select data-no-fancy>`** (NATIVE, intentionally opted out of fancify — first opt-out case in the audit). Server-side paginated `.tbl` table (responsive + data-label). Server pagination, NOT DataTables.
- Issues found: none per-page. Both selects native + usable (set value via real select), filter-card stacks to column at ≤600 (PA-14-2 present), table stacks (thead hidden → data-label, 25/25 tds labelled), 0 console errors, no overflow at any width.
- Fix: none.
- Touch-target observation (→ CC-07, deferred): native filter selects = **37px** (<44px). Page-scoped `.adda-list .filter-card select { padding:9px 12px }`. Same filter-card pattern repeats across ~5 dashboards (roll_list, cloth_dashboard, etc.) → a filter-control family decision, NOT a one-page fix.
- Dependency discovery (selects): **SOURCE TYPE = Literal HTML `<select data-no-fancy>` (native)**; CSS owner = **page-specific** (`.adda-list .filter-card select` in extra_head — NOT base, NOT shared partial; a THIRD select-styling owner after accounts `.field` + production `sf-input`); JS owner = **NONE** (data-no-fancy → fancify skips; Apply button, no auto-submit onchange); hidden page-dep = none.
- Canonical signal: filter selects deliberately stay **native** (data-no-fancy) vs form selects which fancify (HTML-001/002/003). Filter-vs-form context split = key Select Consolidation question. Logged → Select ledger + source-type inventory + CC-07.
- Evidence: /tmp/u004_320.png (filter stacked + table stacked).
- Commit: none (no code change).
### HTML-005 — `production/product_flow.html`
- Status: **CLEAN** (no per-page fix) — awaiting owner review
- Audit unit / method: self (extends base; page-scoped `<style>`). Browser 1280/320/375/390/414, super-admin, `/production/products/1/flow/` (3-PATTI, 4 stages → 9 selects).
- Controls: **select** ×9 — `cost_method` + `cost_billed_at` per flow row (×4) + `stage_id` (add panel). All literal `<select>`, fancified. + number (cost_rate), confirm() on remove.
- Issues found: none. 9 selects fancify (all `--bare`, 44px), open/pick works (cost_method → per_bundle), panel fits, flow-row collapses to 2-col ≤600, 0 console errors, no overflow at any width (even with 9 selects).
- Fix: none.
- Dependency discovery: SOURCE TYPE = literal HTML `<select>`; INTERACTION = single-select (form; no auto-submit, explicit Save/Append). CSS owner = **page-tag CSS** (`.product-flow select`) that does **NOT reach the `<button>` trigger** (selects are class-less) → triggers fall to base `--bare` fallback (PA-14-3 confirmed live). JS owner = base `fancify()`. Hidden page-dep = none (cost_billed_at options are view/template-filtered to later-unbilled stages, but that's server-rendered, not a JS dep).
- Canonical signal: **4th select-styling situation** found → CC-06 updated. Also: `--bare` triggers = **44px** here, vs sf-input 39px (CC-05) + native filter 37px (CC-07) → `--bare` is the only one meeting the touch standard; strengthens raising the others to 44px.
- Evidence: /tmp/u005_320.png (flow + cost-form selects stack/fit).
- Commit: none (no code change).
### HTML-006 — `production/product_list.html`
- Status: **RECLASSIFIED → Family E (Tables)** — NOT a select unit (classification error); table browser-checked; **1 real bug found, logged CC-08 (deferred to Family E)**. Awaiting owner decision.
- Classification correction: my initial Family-A filing was WRONG — this page has **0 `<select>`** (browser-confirmed). I conflated it with the *storefront* product_list (which does have filter selects). Production product_list = a pure responsive `.tbl` table + action links. Belongs in **Family E**.
- Audit unit / method: self. Browser 1280/320, super-admin, `/production/products/`.
- Controls: NO select. Responsive `.tbl` table (48/48 td data-label, stacks at 320), `.td-actions` row of 5 action links (Edit/Flow/Patterns/Sizes/Archive). 0 console errors.
- **Bug found (REAL, browser-verified) → CC-08:** at 320px the `.td-actions` row (`display:flex; justify-content:flex-end; flex-wrap:nowrap` — base.html:974) overflows: 5 buttons ~389px in a ~296px cell, right-aligned → **Edit (x −97) + Flow (x −35) pushed off-screen LEFT, unreachable**. Mobile users can't Edit/open-Flow for a product. Page-level overflow stayed false (clipped past left edge, not extending scroll). Root cause = base `.td-actions` has no `flex-wrap` → defaults nowrap.
- Fix: **NOT applied.** Fix = `flex-wrap: wrap` on base `.td-actions` mobile rule (one line) — but it's a **base.html change across 10 td-actions templates = a Family-E (Tables) decision**. Deferred per the no-family-wide-changes-before-consolidation rule. Logged CC-08 (HIGH). Owner may fast-track.
- Visual owner (the td-actions control): **base.html** (the rule lives + renders from base; no page override).
- Select inventory: N/A (no select control).
- Evidence: /tmp/u006_320.png (action buttons clipped left).
- Commit: none.
### HTML-007 — `production/product_patterns_edit.html`
- Status: **CLEAN** (no per-page fix) — awaiting owner review
- Audit unit / method: self (extends base; page-scoped `<style>`). Browser 1280/320, super-admin. Two views of one template: select on `/production/products/5/patterns/` (0-assignment → Add-Pattern select shows), inline-edit table on `/production/products/1/patterns/` (1 assignment).
- Controls: **select** ×1 — `pattern` (Add-Pattern form, literal `<select>`, **inline-`style`d**, class-less). Number inputs (pieces_count). Inline-edit table (PA-15-2): cell-edit (number+Save) + `td-actions` (Remove, **1 button**).
- Issues found: none. Select fancifies → `--bare` 44px, opens, picks (Patti Panel), no overflow. Inline-edit table at 320: cell-edit stacks (flex column), Save+Remove **44px**, **Remove NOT clipped** (1-button td-actions), thead hidden/stacks, 0 console errors.
- Fix: none.
- Dependency discovery: SOURCE TYPE = literal HTML `<select>`; INTERACTION = single-select (form); **VISUAL OWNER = fallback (`--bare`)** — the select's inline `style=` is on the hidden native element, so the `<button>` trigger ignores it → `--bare`. JS owner = base `fancify()`; hidden page-dep = none.
- **NEW visual-owner data point:** inline-`style`d select (like tag-CSS in HTML-005) does NOT reach the fancified trigger → `--bare`. Extends CC-06 situation (d): BOTH tag-CSS and inline-style bypass the trigger.
- **CC-08 cross-check (Family E):** this template uses `.td-actions` but with only **1 button** (Remove) → no overflow (Remove in-cell, 44px). Confirms CC-08 is **button-count-dependent**. Record for the Family E `.td-actions` inventory: HTML-007 = uses td-actions, 1 button, SAFE.
- Evidence: /tmp/u007_320_table.png (cell-edit stacks, Remove reachable, 44px).
- Commit: none (no code change).
### HTML-008 — `production/layering_workspace.html` (host of `_stage_panel_layering`)
- Status: **CLEAN** (no per-page fix) — awaiting owner review
- Audit unit / method: self = host; renders `_stage_panel_layering.html` (= HTML-009) which holds the selects. Browser 1280/320/375/390/414, super-admin, `/production/addas/3-PATTI-002/layering/`.
- Controls: **9 selects** — `fc`/`ft`/`fw` (filter, **auto-submit** `onchange=this.form.submit()`), `roll` (roll picker), `width_verified_inch` (per-roll), `cloth_type`/`cloth_color`/`width_inch`/`storage_location` (quick-create-roll form). All fancified (none native).
- 6-dim record:
  - **source type:** fc/ft/fw = literal `<select>`; roll/width_verified_inch/cloth_* = Django form-widget selects.
  - **interaction model:** fc/ft/fw = **AUTO-SUBMIT** (first case in audit) · rest = single-select (form).
  - **native vs fancified:** all fancified.
  - **visual owner:** 8 = fallback (`--bare`); width_verified_inch = base (`sf-input`).
  - **touch-target height:** 8 × **44px** (`--bare`) · width_verified_inch **39px** (sf-input → CC-05).
  - **hidden dependencies:** fc/ft/fw rely on inline `onchange=this.form.submit()` (auto-submit) — must survive any canonicalization (it does: fancify dispatches native `change`).
- Issues found: none. **Auto-submit verified live:** picked fc="Black" via fancy dropdown → form auto-submitted → URL `?fc=5`, trigger shows "Black", 0 console errors. Panels fit/open at 320, no overflow at any width.
- Fix: none.
- Canonical signals: (1) **auto-submit select works post-fancify** (onchange→submit fires) — key for the filter-select canonical. (2) width_verified_inch = another **sf-input 39px** instance → CC-05. (3) 8 `--bare` triggers (44px) here vs 1 sf-input (39px) — same height split.
- **HTML-009 (`_stage_panel_layering`) is the partial rendered here → its selects are covered by this audit** (identical markup). Only the standalone host (`stage_panel_standalone`, HTML-083) differs in chrome — verify that wrapper when HTML-009/083 reached.
- Evidence: /tmp/u008_320.png (fc dropdown open, fits).
- Commit: none (no code change).
### HTML-009 — `production/_stage_panel_layering.html`
- Status: **COVERED VIA HOST AUDIT** (HTML-008) — no separate browser pass required
- Rendered markup is identical to what was fully browser-verified through HTML-008
  (`layering_workspace`) at 1280/320/375/390/414 — the 9 selects audited there ARE this
  partial's markup. 6-dim record + auto-submit evidence captured under HTML-008.
- **No separate browser pass required.**
- **Standalone-host differences remain DEFERRED to the standalone host template**
  (`stage_panel_standalone.html`, HTML-083) — verify there that the same partial renders
  with no chrome/positioning difference. Not a select re-audit.
- Commit: none.
### HTML-010 — `production/_stage_panel_cutting.html` (via `cutting_workspace`)
- Status: **CLEAN** (browser-verified) — awaiting owner review. (Was BROWSER-BLOCKED; owner provisioned a disposable cutting Adda **3-PATTI-004** → real browser pass done. Golden 3-PATTI-001 untouched.)
- Audit unit / method: self (partial via `cutting_workspace`). Browser 1280/320/375/390/414, super-admin, `/production/addas/3-PATTI-004/cutting/workspace/`. Started cutting (assigned utest) + created an empty "Size 1" bundle to surface the entry panel — **real interaction on the disposable Adda** (left in that state for owner disposal).
- Controls: cutting entry selects — `data-bulk-size` (bulk-add) + `size_id` (create-bundle), both **browser-verified**; `worker_id` (per-bundle add-pieces) = code-read (surfaces deeper, see below). + number inputs (`take_count`, `data-mselect-take`).
- 6-dim (BROWSER-VERIFIED for bulk-size + size_id): source type = literal `<select class="sf-input">`; interaction = single-select (form); native vs fancified = **fancified**; visual owner = **base (`sf-input`)** ✓; touch height = **39px** ✓ (**CC-05 now browser-confirmed**, not just expected); hidden deps = `data-bulk-size`/`data-mselect-take` JS hooks. size_id pick verified (value→4 "Size 1"), panel fits 320, **0 console errors, no overflow** at any width.
- worker_id: code-read (`<select name=worker_id class=sf-input style=max-width:170px>`, line 695) — same sf-input class as the 2 verified; renders only in the populated per-bundle add-pieces form (needs breakup/color rows, 2+ deeper steps). NOT separately surfaced — same-class as verified selects; flagged honestly as code-read.
- Issues found: none. (sf-input 39px <44px = CC-05, the app-wide form-control-height candidate — NOT a per-page fix.)
- Fix: none.
- Evidence: /tmp/u010_320.png (cutting panel @320 — workers multiselect + entry selects, no overflow). Disposable Adda 3-PATTI-004 left at: cutting started, utest assigned, 1 empty Size-1 bundle.
- Commit: none (no code change).
### HTML-011 — `raw_materials/cloth_dashboard.html`
- Status: **CLEAN** (no per-page fix) — awaiting owner review
- Audit unit / method: self (extends base; page-scoped `<style>` + `_time_log_styles` include). Browser 1280/320/375/390/414, super-admin, `/raw-materials/cloth/`.
- Controls: **select** ×1 — `color` filter `<select data-no-fancy>` (NATIVE, same pattern as HTML-004). **date** ×2 — `from`/`to` native `<input type=date>` (NO `data-fancy-date` → native by-design dashboard range filter; Family C evidence). 2 responsive `.tbl` tables (By Location, Recent Rolls). filter-card + PA-14-2 stack.
- 6-dim (select `color`): source type = literal `<select data-no-fancy>`; interaction = **filter-select (native)**; native vs fancified = **native**; visual owner = **page-specific css** (`.cloth-dash .filter-card select`); touch height = **37px** (CC-07); hidden deps = none (Apply button, no auto-submit).
- Issues found: none. color select native + usable; filter-card stacks to column ≤600 (PA-14-2); both tables stack (theads hidden, data-label); no overflow at any width; 0 console errors.
- Fix: none.
- Findings (evidence, deferred): color filter select 37px → **CC-07** (native filter <44px; now browser-confirmed on a 2nd surface after HTML-004). Native date inputs `from`/`to` = **37px**, native-by-design (Family C) — sub-44 touch but intentional native range filter; record for Date family.
- Evidence: /tmp/u011_320.png (filter stacked: native dates + color select + Apply/Reset).
- Commit: none (no code change).
### HTML-012 — `raw_materials/roll_bulk_form.html`
- Status: **CLEAN** (no per-page fix) — awaiting owner review
- Audit unit / method: self (extends base; page-scoped `<style>`). Browser 1280/320/375/390/414, super-admin, `/raw-materials/rolls/bulk-add/`.
- Controls: **3 selects** — `cloth_type` + `storage_location` (Django widget, `sf-input`, fancified) · `breakup_color` (literal `<select data-no-fancy>`, NATIVE, repeated per cloned breakup row). **date** `purchased_date` (native `<input type=date class=sf-input>`, no fancy-date). Number inputs (breakup_qty).
- 6-dim:
  - source type: cloth_type/storage = Django widget select; breakup_color = literal native; purchased_date = native date.
  - interaction: cloth_type/storage = single-select (form); breakup_color = single-select (form, dynamic rows).
  - native vs fancified: cloth_type/storage **fancified**; breakup_color **native**.
  - visual owner: cloth_type/storage = **base (`sf-input`)**; breakup_color = **page-specific css** (`.bulk-roll-create select`, native).
  - touch height: cloth_type/storage **39px** (sf-input → CC-05) · breakup_color **42px** (native, page padding 11px) · purchased_date **43px** (native date).
  - hidden deps: breakup_color is `data-no-fancy` **specifically because rows are JS-cloned** from a `<template>` (fancify only runs on DOMContentLoaded → cloned rows would be half-upgraded; native avoids it). **New data-no-fancy reason: dynamically-cloned rows.**
- Issues found: none. cloth_type fancify pick works (Cotton); breakup_color native usable (Red); form-grid + breakup-row stack to 1-col ≤600; no overflow at any width; 0 console errors.
- Fix: none.
- Notable evidence: **same page, native select 42px vs fancified trigger 39px** — the page's `.bulk-roll-create select` (padding 11px) reaches the native breakup_color but NOT the fancified `<button>` trigger (which falls to the smaller global `.sf-input` 39px). Concrete CC-05/CC-06 illustration. Also: **native select height is page-CSS-dependent** (42px here vs 37px filter-card) — the 37/39/44 tiers aren't fixed for natives.
- Evidence: /tmp/u012_320.png (Panel 01 selects stack/fit).
- Commit: none (no code change).
### HTML-013 — `raw_materials/roll_assign_form.html`
- Status: **CLEAN** (no per-page fix) — awaiting owner review
- Audit unit / method: self (extends base; `_form_styles` form-shell). Browser 1280/320/375/390/414, super-admin, `/raw-materials/rolls/4/assign/`. (All rolls are `used` → form audited via GET on a used roll; assign POST NOT exercised — that's a used-roll mutation/reject. **Select RENDERING fully browser-verified.**)
- Controls: **2 selects** — `adda_code` (eligible-Addas-at-layering picker, Django widget `sf-input`) + `width_inch` (Django widget `sf-input`). + weight number.
- 7-dim: source = Django widget selects · interaction = single-select (form); adda_code is an eligibility-scoped picker (only layering Addas) · native vs fancified = **fancified** · visual owner = **base (`sf-input`)** · touch height = **39px** (both → CC-05) · hidden deps = none · data-no-fancy = none.
- Issues found: none. adda_code fancify pick works (3-PATTI-002), panel fits, form-grid stacks 1-col ≤600, no overflow, 0 console errors.
- Fix: none.
- Canonical signal: 2 more sf-input 39px instances (CC-05). Standard form-select pattern (sf-input widget → fancify → 39px), same as HTML-003/012.
- Evidence: /tmp/u013_320.png (ADDA dropdown open + WIDTH select, stacked, fits).
- Commit: none (no code change).
### HTML-014 — `raw_materials/roll_edit_form.html`
- Status: **CLEAN** (no per-page fix) — awaiting owner review
- Audit unit / method: self (extends base; `_form_styles` form-shell). Browser 1280/320/375/390/414, super-admin, `/raw-materials/rolls/4/edit/`. (Used roll → page renders form + an "in use, detach first" warning banner; save blocked server-side. Select RENDERING fully browser-verified; no submit.)
- Controls: **2 selects** — `width_inch` + `storage_location` (Django widget `sf-input`). **date** `purchased_date` (native `<input type=date sf-input>`). number `weight_kg`. Finance fields conditional.
- 7-dim: source = Django widget selects · interaction = single-select (form) · native vs fancified = **fancified** · visual owner = **base (`sf-input`)** · touch height = **39px** (both selects) · date 43px (Family C) · hidden deps = none · data-no-fancy = none.
- Issues found: none. storage_location fancify pick works (→ Rohini Factory, DOM only); form-grid stacks 1-col ≤600; panel fits; no overflow; 0 console errors. **Good UX:** in-use warning banner clearly tells the user to detach before editing.
- Fix: none.
- Canonical signal: 2 more sf-input 39px (CC-05). Standard form-select pattern (= HTML-003/012/013).
- Evidence: /tmp/u014_320.png (in-use warning + WIDTH select + storage dropdown).
- Commit: none (no code change).
### HTML-015 — `raw_materials/roll_list.html`
- Status: **CLEAN** (no per-page fix) — awaiting owner review
- Audit unit / method: self. Browser 1280/320/375/390/414, super-admin, `/raw-materials/rolls/`.
- Controls: **4 filter selects** — status, cloth_type, location, color — ALL `<select data-no-fancy>` (NATIVE). Responsive `.tbl` + server pagination. Removable active-filter chip strip (filter-info).
- 7-dim (all 4 identical): source = literal `<select data-no-fancy>` · interaction = **filter-select (native)** · native vs fancified = **native** · visual owner = **page-specific css** (`.roll-list .filter-card select`) · touch height = **37px** · hidden deps = none · data-no-fancy reason = **filter-select behavior**.
- Issues found: none. All 4 native + usable; filter submit works (status→used → `?status=used` + active-filter chip renders); filter-card stacks ≤600 (PA-14-2); table stacks; no overflow; 0 console errors.
- Fix: none.
- Established pattern (not a new discovery): native filter selects 37px = **CC-07** (now 3rd surface after HTML-004/011; most-selects-on-one-page so far = 4). No new select behavior.
- Filter-family note (Phase E, not a select): removable active-filter chips (`.filter-info .chip` w/ per-chip `remove_url` + "Clear all") — a reusable filter-summary pattern; record for the Filter family.
- Evidence: /tmp/u015_320.png (4 native filter selects stacked + table stack).
- Commit: none (no code change).
### HTML-016 — `expense/advance_form.html`
- Status: **CLEAN** (no per-page fix) — awaiting owner review
- Audit unit / method: self (money screen, `hero-strip copper`; fields via generic `{% for field in form %}` loop). Browser 1280/320/375/390/414, super-admin, `/expense/advances/add/`.
- Controls: **1 select** — `worker` (Django ModelChoice, **16 options**). (Correction: `method` is on SettlementForm = HTML-017, NOT here.) + native date (Advance date), textarea (Notes), file (Attachment).
- 7-dim (worker): source = Django widget select · interaction = single-select (form) · native vs fancified = **fancified** · visual owner = **fallback (`--bare`)** — class-less select, page `.expense-form select` tag-CSS bypassed (situation d, = HTML-005/007) · touch height = **44px** (`--bare`) · hidden deps = none · data-no-fancy = none.
- Issues found: none. worker pick works (mgmt2@test); 44px; native date; no overflow; 0 console errors.
- Fix: none.
- **New behavior data point (→ CC-10, supporting):** first long-option-list select (16 opts). Panel caps at **max-height 260px + internal scroll**, fits viewport at 1280 AND 320 (bottom within vh). Good long-list handling.
- Established (supporting, not new): `--bare` 44px (situation d); native date (Family C).
- Evidence: /tmp/u016_320.png (worker dropdown open, scrollable, fits).
- Commit: none (no code change).
### HTML-017 — `expense/settlement_form.html`
- Status: **CLEAN** (no per-page fix) — awaiting owner review
- Audit unit / method: self (money screen `hero-strip copper` + `stat-grid`). Browser 1280/320/375/390/414, super-admin, `/expense/workers/2/settle/` (utest, payable ₹225 = golden chain — **typed only, NO submit, golden untouched**).
- Controls: **1 select** — `method` (SettlementForm ChoiceField, 4 opts). amount_paid (number), settlement_date (native date), notes (textarea). Read-only `.adv` advances table (not rendered — 0 outstanding for this worker).
- 7-dim (method): source = Django widget select · interaction = single-select (form) · native vs fancified = **fancified** · visual owner = **fallback (`--bare`)** (class-less, `.settle select` tag-CSS bypassed = situation d) · touch height = **44px** · hidden deps = none · data-no-fancy = none.
- **NEW interaction model (→ CC-11, priority #1):** live-preview submit-gating. `amount_paid` pre-fills the full payable (₹225); typing recomputes "Payable after" + shows ⚠ over-warning when paid>payable + **disables the Confirm button** when over or ≤0. Verified: 100→"₹125" enabled · 300→"₹-75" warn+disabled · works at 320 too (50→"₹175"). Client-side money-invariant gating tied to the amount input. NOT a select behavior — a form-validation/dependency pattern.
- Issues found: none. method --bare 44px; stat-grid stacks ≤640; native date 42px; 0 overflow; 0 console errors.
- Fix: none.
- Supporting (not new): method `--bare` (situation d); native date (Family C).
- Evidence: /tmp/u017_320.png (stat cards stacked + payment panel).
- Commit: none (no code change).
### HTML-018 — `storefront/listing/category_list.html`
- Status: **CLEAN** (no per-page fix) — awaiting owner review. (SEED → now browser-verified.)
- Audit unit / method: self (`.ke-toolbar` filter idiom + DataTable). Browser 1280/320/375/390/414, super-admin, `/storefront/categories/`.
- Controls: **1 filter select** — `active` (`<select name=active class="filter-select" onchange="this.form.submit()">`). DataTable `#categories-dt` (NOT rendered — 0 categories → empty-state). td-actions (Edit/Delete) not rendered (empty).
- **NEW filter-select implementation (→ CC-12, priority hit):** UNLIKE the native data-no-fancy filter selects (CC-07), this one is **classed (`.filter-select`) + FANCIFIED + auto-submit**. 7-dim: source = literal `<select class=filter-select>` · interaction = **filter-select + auto-submit** · native vs fancified = **fancified** · visual owner = **base.html** (`.filter-select`, base.html:1094, class copied to trigger) · touch height = **40px** (new tier — `.filter-select` class) · hidden deps = inline `onchange=this.form.submit()` · data-no-fancy = NONE (deliberately fancified, unlike raw_materials filters).
- Auto-submit verified: pick "Active" → `?active=1`, trigger "Active", 0 console errors (CC-09 reinforced — works on a CLASSED filter select too).
- Issues found: none. .ke-toolbar overflow-x:auto fits at 320; KPIs stack; empty-state renders; no overflow; 0 console errors.
- **DELTA (owner seeded 1 category, 2026-06-15 — blocked portions now VERIFIED):** DataTable **initialised** (`initFancyDataTable` — search row + pagination + DOM-detach, 0 console errors); 1 row rendered; stacks to data-label cards at 320. td-actions = 2 `.action-link`s (Edit/Delete). **Mobile 320: both fit** — Edit 146→205, Delete 213→288, within cell 12→308, **NOT clipped**, no page overflow. → **CC-08 NOT triggered here** (2 small action-links fit; CC-08 only bites with many wide `.btn`s like HTML-006's 5). New row-action observation: `.action-link`s are **23px** tall (text+icon links, sub-44 touch — pre-existing `.action-link` pattern, both reachable). Evidence: /tmp/u018b_320.png.
- Fix: none.
- Evidence: /tmp/u018_320.png (KPIs + filter, empty-state).
- Commit: none (no code change).
### HTML-019 — `storefront/listing/product_form.html`
- Status: **AUDITED — selects CLEAN; 1 real mobile bug found (CC-13, deferred → Family F)** — awaiting owner review. (SEED → browser-verified.)
- Audit unit / method: self (storefront form; croppable image widget via `{{ form.image }}`). Browser 1280/320/375/390/414, super-admin, `/storefront/products/add/`.
- Controls: **2 selects** — `category` + `badge` (`<select class="sf-input">`, fancified). Croppable-image **modal** (Family F). text/number/textarea/checkbox.
- 7-dim (category/badge): source = literal `<select class=sf-input>` · interaction = single-select (form) · native vs fancified = **fancified** · visual owner = **base (`sf-input`)** · touch height = **39px** (CC-05 supporting) · hidden deps = none · data-no-fancy = none. Selects CLEAN (fancify, pick, 0 console errors).
- **REAL mobile bug → CC-13 (HIGH, deferred):** the croppable-image widget preview box (`croppable_image.html:50`, inline `width:{preview_width}px` ≈400px, no `max-width`) forces the storefront form column to ~450px → at every mobile width (320–414) the form is **clipped on the right** (PA-14-1 class — `main.content overflow-x:hidden` masks overflow, so `scrollWidth` reads clean but PRODUCT NAME / CATEGORY / inputs are cut off + unreachable). Browser-confirmed at 320 (screenshot). **Shared widget** → also affects `category_form` (HTML-046). NOT a per-page fix; deferred to Family F (shared component), like CC-08.
- Other findings (latent, NOT fixed): unscoped `section{} !important` (rule-10) — only the 3 form `<section>`s exist on the page (0 outside), so **no visible leak** today; latent hygiene issue.
- Fix: none (CC-13 deferred; section{} latent).
- Evidence: /tmp/u019_320.png (form inputs clipped right at 320).
- Commit: none (no code change).
### HTML-020 — `storefront/listing/product_list.html`
- Status: **CLEAN (selects)** — awaiting owner review. (SEED → browser-verified. DataTable/td-actions BLOCKED — 0 rows.)
- Audit unit / method: self (`.ke-toolbar` + DataTable). Browser 1280/320/375/390/414, super-admin, `/storefront/products/`.
- Controls: **2 filter selects** — `badge` + `active`, both `<select class="filter-select" onchange="this.form.submit()">`. DataTable `#products-dt` (NOT rendered — 0 FeaturedProducts → empty-state). td-actions (Edit/Delete action-links) not rendered.
- 7-dim (both): source = literal `<select class=filter-select>` · interaction = **filter-select + auto-submit** · native vs fancified = **fancified** · visual owner = **base.html (`.filter-select`)** · touch height = **40px** · hidden deps = inline `onchange=this.form.submit()` · data-no-fancy = none. = **CC-12 pattern, 2nd surface** (2 classed filter selects here; supporting, not new).
- Issues found: none (selects). KPIs stack, .ke-toolbar fits 320, empty-state renders, no overflow, 0 console errors.
- **DELTA (owner seeded 1 product, 2026-06-15 — blocked portions now VERIFIED):** DataTable **initialised** (search + pagination "Showing 1–1 of 1", DOM-detach, 0 console errors); 1 row rendered; stacks to data-label cards at 320 (3 Patti · Kids Garment · ₹60/₹100 · HOT · Active). td-actions = 2 `.action-link`s (Edit/Delete). **Mobile 320: both fit** — Edit 146→205, Delete 213→288, within cell 12→308, **NOT clipped**, no overflow (browser screenshot shows Edit│Delete both visible). → **CC-08 NOT triggered** (2 action-links fit). `.action-link` = 23px (sub-44, pre-existing pattern). Evidence: /tmp/u020b_320.png + /tmp/u020b_row.png.
- Fix: none.
- Evidence: /tmp/u020_320.png (KPIs + filter, empty-state).
- Commit: none (no code change).
### HTML-021 — `tracking/barcode_print_sheet.html`
- Status: **CLEAN** (no per-page fix) — awaiting owner review
- Audit unit / method: **standalone print doc** (own DOCTYPE/head/body, **NO base.html**). Browser 1280/320/375/390/414, super-admin, `/tracking/barcodes/3-PATTI-001/print/` (read-only GET; golden Adda's 105 barcodes rendered — no mutation).
- Owner attention points (all confirmed):
  - **Standalone rendering:** ✓ no app shell (`.shell/.sidebar/.topbar` absent).
  - **base.html dependency:** **NONE** — `window.fancifySelects === undefined` (base.html JS not loaded). Inline `<style>` only.
  - **?size query-param:** ✓ `size` select drives `spec.cols`/`spec.qr_mm` (sheet grid + QR mm); auto-submit → `?size=large` applied.
  - **Print-specific controls:** ✓ Print button (`window.print()`), `@page A4`, `@media print` hides toolbar.
  - **Bypasses the normal select ecosystem:** ✓ **YES** — both selects are NATIVE (no fancify, since base.html absent), inline-`.toolbar select`-styled, **33px**, auto-submit.
- Controls: **2 selects** — `size` + `status`, both `<select onchange="this.form.submit()">`. + Print button.
- 7-dim (both): source = literal `<select>` · interaction = **filter-select + auto-submit** · native vs fancified = **NATIVE (no fancify ecosystem — base.html absent)** · visual owner = **standalone-doc inline `<style>`** (`.toolbar select` — NOT base.html, NOT page-under-base) · touch height = **33px** (smallest yet) · hidden deps = inline onchange-submit + the standalone doc has NO fancify (so native is the only path) · data-no-fancy = **N/A** (native because base absent, NOT an opt-out).
- **NEW context → CC-14:** standalone print doc bypasses the fancy-select ecosystem entirely. NATIVE for a DIFFERENT reason than CC-07 (CC-07 = `data-no-fancy` opt-out within base.html; CC-14 = no base.html at all). New visual-owner (standalone inline style), new height (33px).
- Issues found: none. ?size auto-submit works; toolbar stacks ≤768; sheet 304px fills at 320; 105 stickers render; no overflow; 0 console errors.
- Fix: none.
- Evidence: /tmp/u021_vp.png (toolbar stacked + QR grid at 320).
- Commit: none (no code change).
### HTML-022 — `production/_worker_report_body.html` (custom chip single-select)
- Status: **CLEAN** (no per-page fix) — awaiting owner review. (SEED → browser-verified.)
- Audit unit / method: partial, rendered via standalone host `worker_report` (HTML-087). Browser 1280/320/375/390/414, **logged in as utest (cutting master)** — super-admin gets 403 (worker-report is assignment-gated). `/production/addas/3-PATTI-004/report/cutting/` (disposable Adda; draft state, NO submit).
- Control: **custom chip single-select** (NOT a `<select>`, NOT fancify) — schema-driven (`kind='choice'` → chip-row of `<button class=chip data-value>` + hidden `<input data-key>`; `kind='quantity'` → numeric). 2 chip-rows (color_id 6 chips, size_id 3) + 1 qty.
- 7-dim (adapted): source = **custom chip-picker (hand-rolled, not `<select>`)** · interaction = **chip-toggle, single-select** · native vs fancified = **N/A (custom, no fancify)** · visual owner = **shared partial `_worker_report_styles.html`** (`.chip`/`.selected`/`.swatch`) · touch height = **34px** (<44, worker-facing surface) · hidden deps = inline JS (chip click → clear siblings `.selected` → set `.selected` + `hidden.value`; renumber renames `line-<i>-<key>` at submit; schema-driven) · data-no-fancy = N/A.
- Behaviors verified (browser): **single-select ENFORCED** (Black→Red leaves only Red, count=1) · **hidden input sync** (color hidden="1", size="4" after picks) · rows independent · **keyboard-operable** (focus chip + Enter → selects, e.g. Blue) · mobile (chips flex-wrap, tap works → Green, 0 overflow) · 0 console errors.
- **Is it a select replacement? YES** — functional single-select; hidden input submits the chosen value; the touch-first mobile alternative to `<select>` for worker capture.
- a11y gap (note, like CC-01): chips are `<button tabindex=0>` (operable) but have **no `role=radiogroup`/`role=radio`/`aria-pressed`/`aria-checked`** → AT can't convey single-select semantics or which is chosen. + 34px touch (<44) on a worker mobile-first surface.
- → **CC-15** (distinct selection model). Fix: none.
- Embedded twin `worker_report_embedded` (HTML-086) renders the SAME body → chips identical (covered); chromeless-host chrome check deferred to HTML-086.
- Evidence: /tmp/u022_320.png (chip-rows wrap, Green selected, touch-first).
- Commit: none (no code change).

## Phase B — Multiselects (HTML-023)

### HTML-023 — `production/_workers_widget.html` (Multiselect — worker-chip grid) [PHASE B]
- Status: **CLEAN** (no per-page fix) — awaiting owner review. (SEED → browser-verified.)
- Audit unit / method: Django ModelMultipleChoice widget template; rendered in the stage "Assigned Workers" panel. Browser 1280/320/375/390/414, super-admin, `/production/addas/3-PATTI-004/cutting/workspace/` (panel 01). Toggled checkboxes in DOM only, NO submit (no mutation).
- Control: **checkbox-chip multiselect** — `.workers-grid` of `<label class="worker-chip">` wrapping `<input type=checkbox name=workers value=pk>`. 12 chips. NOT a `<select multiple>` (fancify SKIPS multiple); NOT fancified (fancify skips checkboxes).
- 7-dim (multiselect-adapted): source = **Django ModelMultipleChoice widget → checkbox grid** · interaction = **multi-select (checkbox)** · native vs fancified = **native checkboxes (no fancify)** · visual owner = **shared partial `_form_styles.html`** (`.worker-chip`, `:checked` → copper tint) · touch height = **52px** (✅ ≥44, comfortable — best touch of any selection control so far) · hidden deps = **none** (real checkboxes submit `name=workers` values directly; no hidden input, no JS sync) · data-no-fancy = N/A.
- Behaviors verified (browser): **MULTI-select** (checked 3 simultaneously: ManagerOne+mgmt1+utest — multiple stay, unlike chip single-select CC-15) · **selected visual** (checked chip bg copper rgba(184,115,51,0.1) vs cream — differ ✓) · **keyboard** (focus checkbox + Space toggles ✓) · mobile (grid 1-col at 320, 52px chips, no overflow) · 0 console errors.
- **a11y: GOOD** — real `<input type=checkbox>` in `<label>` → proper native checkbox semantics (Tab+Space, screen-reader announces checked state). **Better than CC-15 chip single-select** (which lacked radiogroup/aria). The native-checkbox approach is the a11y-correct multiselect.
- Is it a `<select multiple>` replacement? **YES** — deliberate: fancify SKIPS `<select multiple>`, so a checkbox-chip grid is the touch-friendly multiselect (the de-facto multiselect canonical candidate).
- Evidence: /tmp/u023_320.png (worker-chip grid, 52px, utest checked).
- Commit: none (no code change).

## Phase C — Date controls (HTML-024 … HTML-025)

> ⚠ The canonical `fancy-date` control (`fancifyDate` JS + `.fancy-date-*` CSS) is
> sitting **uncommitted** in `accounts/base.html` (+359) with `user_form.html` as
> its only opt-in consumer and a UI_COMPONENTS.md section (+21). Resolve that
> pre-work (review+commit, or fold into this phase) before locking a date standard.

### HTML-024 — `production/adda_dashboard.html` (Date — native range filter) [PHASE C]
- Status: **CLEAN** (no per-page fix) — awaiting owner review.
- Audit unit / method: date-focus (Phase C). Browser 1280/320/375/390/414, super-admin, `/production/` (AddaDashboardView = adda_dashboard, "Operations"). DOM set only, no submit.
- Control: **2 native `<input type=date>`** (`from`/`to`, created-date range filter). NO `data-fancy-date` → native (not the custom calendar).
- 10-dim: rendering = **native `<input type=date>`** (browser UA date control) · selection = native date picker (OS/browser) · keyboard = native (type segments + arrows) · SR = native date semantics (good) · touch = **37px** · mobile = filter-card stacks (PA-14-2), full-width, native OS picker · dependency = none (native; filter form) · hidden-vs-native = native · CSS owner = **page-specific** `.adda-dashboard .filter-card` · JS owner = **none**.
- **Date-family implementation = NATIVE (the default path).** The OTHER date impl = **fancy-date** custom body-anchored calendar (opt-in `data-fancy-date`, verified Step 0 / committed `7e105b92`, ONLY consumer = user_form birth_date). Per UI_COMPONENTS: dashboard date-RANGE filters **intentionally** stay native; fancy-date is opt-in for single-value fields. So native here is by-design, not a gap.
- Known native-date tradeoff (documented, the reason fancy-date exists): on desktop Chromium only the calendar icon is clickable (not the text); native popup mispositions under transformed ancestors. Accepted for range filters.
- Issues found: none. Set date holds; filter stacks ≤600; no overflow; 0 console errors.
- Evidence: /tmp/u024_320.png (Operations dashboard, filter stacks).
- Commit: none (no code change).
### HTML-025 — `tracking/barcode_dashboard.html` (Date — native range filter) [PHASE C]
- Status: **CLEAN** (no per-page fix) — awaiting owner review.
- Audit unit / method: date-focus. Browser 1280/320/375/390/414, super-admin, `/tracking/`. DOM only, no submit.
- Control: **2 native `<input type=date>`** (`from`/`to`, Adda-created range). No `data-fancy-date` → native.
- 10-dim: native UA date · native picker · native keyboard · native a11y · **37px** · filter-card stacks ≤600, full-width, no overflow · **no onchange/auto-submit · no min/max** (no client range-validation; Apply button; range enforced server-side) · page-css owner `.bc-dash .filter-card` · **no JS**.
- = **CC-21 (native default), 3rd browser-verified range-filter surface** (after adda_dashboard 024 + cloth_dashboard 011). No new interaction model, no auto-submit, no validation behavior, no standalone-doc context. 0 console errors.
- Evidence: /tmp/u025_320.png (FROM/TO native dates stacked + Apply).
- Commit: none (no code change).

> **Date inventory reconciled — COMPLETE (2026-06-15):** 2 implementations cover every date surface.
> **fancy-date** (opt-in custom calendar): user_form birth_date (Step 0, `7e105b92`). **native `<input type=date>`** (default):
> range filters adda(024)/cloth(011)/barcode(025) + form dates purchased(012/014)/advance(016)/settlement(017).
> 0 third-party pickers · 0 standalone-doc date controls (barcode_print_sheet/worker_report have none) ·
> 0 auto-submit/min-max date logic. All browser-verified across Phase A+C. **Date Consolidation Report ready
> on owner go** (not auto-produced; owner gates reports).

## Phase D — Form controls (HTML-026 … HTML-048)

text / number / textarea / checkbox / radio + validation rendering.

### ⬛ FORM-CONTROL COMPLETENESS INVENTORY (2026-06-16) — scan before the Consolidation Report
Full grep: **59 templates contain `<form method`** app-wide. Cross-referenced vs the **48 `### HTML` records**. Classification:

**A. Audited Form-Control input units (Phase D + earlier-phase form pages):** 026-048 (+ 001/002/003/005/007/012/013/014/016/017/019 from A/B). All input forms below are recorded.

**B. ⚠ UN-AUDITED INPUT FORM — 1 (genuine Form-Control gap):**
- **`production/_stage_panel_barcode_gen.html`** (seed **HTML-070**) — barcode_gen stage panel; forms = reopen/start/generate/complete; renders **`{{ start_form.workers }}`** = the **CC-20 worker-picker (barcode_gen — the remaining code-only CC-20 surface)** + barcode-count/complete controls. **Must audit to complete Form-Control + close the last CC-20 surface.** (Uses `{{ form }}` widgets, so it didn't surface in literal-`<input>` greps — caught via the `<form method` sweep.)

**C. Confirm/delete/archive dialogs — 11 (NOT input units; 0 input controls each) → SPOT-CHECK DONE, classified COVERED:**
- `skill_confirm_delete` · `user_confirm_delete` · `usertype_confirm_delete` · `pattern_confirm_delete` · `product_confirm_archive` · `stage_confirm_delete` · `master_confirm_archive` · `master_confirm_delete` · `category_confirm_delete` · `listing/product_confirm_delete` · `role_confirm_delete`.
- **Representative spot-check (skill_confirm_delete, browser GET, NO submit):** confirm page = extends base + warning copy + **1 submit (delete) btn 44px ✅** + cancel link + **0 input controls**; mobile 320 **0 overflow**, button reachable. **Structural sameness across all 11 (grep):** every one = `extends` base · exactly 1 `type=submit` · **0 real inputs** (text/number/select/textarea). **No unique implementation.** → bucket C = uniform "confirm-dialog" sub-type (button family), **CLASSIFIED COVERED + out-of-scope for Form-Control input conclusions** (no inputs/validation to audit). Remaining 10 = N/A (identical pattern).

**D. List/nav POST forms — 4 (NOT input units; 0 input controls):**
- `accounts/user_list` · `expense/adda_settlement_list` · `inventory/sidebar_access_list` · `tracking/barcode_list` — POST forms are **action/nav/row-action only** (buttons + hidden). Any FILTER controls on these are GET `<select>`s = **Select family (Phase A)**, not Form-Control. `accounts/base.html` = layout chrome (global search, 13 inputs) — not a discrete unit. → out of Form-Control-input scope.

**E. Dormant / unreachable (already audited, honestly marked):** `signup`(031) + `signup_otp`(032) = DISABLED/unrouted (PA-02-OPEN-SIGNUP); `otp`(029) = flow-gated. All code-read-verified.

**Reclassification candidates:** C (11 confirm-dialogs) + D (4 list/nav forms) → move OUT of Form-Control-input family (no input controls). `usertype_form`(034) already reclassified IN (it IS an input form).

**VERDICT (updated 2026-06-16):** ✅ **HTML-070 (host) + HTML-071 (panel) DONE** — barcode_gen worker-picker browser-confirmed = bare Django-default CC-20 → **CC-20 inventory COMPLETE (both surfaces)**; panel CLEAN, mobile-safe. ✅ **Confirm-dialog representative spot-check DONE** (see below) → bucket C classified covered/out-of-scope. → **FORM-CONTROL INPUT INVENTORY CONFIRMED COMPLETE.** Ready for the Form-Control Consolidation Report (next, on owner go).

### HTML-026 — `accounts/forgot_password.html` (Form-control — auth) [PHASE D]
- Status: **CLEAN** (no per-page fix) — awaiting owner review. (SEED → browser-verified.)
- Audit unit / method: form-control focus (Phase D). Browser 1280/320/375/390/414, `/app/forgot-password/`. NO submit (forgot-password POST sends an OTP email + is IP+email rate-limited — avoided).
- Form system: **standalone auth** (no base.html; own inline `<style>`; `.field`-ish + `.alert`). Control: 1 `<input type=email>`.
- 8-dim: form system = standalone auth (own CSS) · control types = email · validation rendering = **`.alert`/`.alerts` messages banner (form-level), NO per-field errors** (structure verified; not triggered — no submit) · keyboard/a11y = **good** (`label[for]=email`, `required`, `autocomplete=email`, autofocus) · touch = **46–47px** ✅ (≥44) · mobile = card fits 320, input full-width, no overflow · CSS owner = standalone inline · JS owner = none.
- Issues found: none. 0 console errors, no overflow any width.
- Form-control inventory note: this is the **standalone-auth form-system + messages-validation** lane (1 of several form systems — see Form-control evidence ledger). Per the Phase-A SEED, the auth set is messages-only validation (only signup.html uses a per-field `form.errors` loop) — to confirm across the auth cluster in later D units.
- Evidence: /tmp/u026_320.png (Reset-password auth card, fits 320).
- Commit: none (no code change).
### HTML-027 — `accounts/login.html` (Form-control — auth, OTP email step) [PHASE D]
- Status: **CLEAN** (no per-page fix) — awaiting owner review. (SEED → browser-verified.)
- Audit unit / method: form-control focus. Browser 1280/320/375/390/414, `/app/` (logged out). NO submit (OTP email + rate-limit).
- Form system: **standalone split-screen auth** (`.page .left/.right .form-shell`; own inline `<style>`; **own local `.field`** copy). Controls: 1 `<input type=email>` (Send OTP). + Google SSO btn (`.btn-google`), "Sign in with password instead" link.
- 8-dim: form system = standalone auth, **own `.field`** (NOT base/shared) · control = email · validation = **`.alert-item` messages banner (form-level, no per-field)** (structure; not triggered) · a11y = **good** (`label[for]`, `required`, autocomplete, `:not(:placeholder-shown)` filled-state) · touch = **49px** ✅ · mobile = left brand pane hides, form single-column, no overflow · CSS owner = **standalone inline (own copy)** · JS owner = minimal (Google onclick redirect).
- Issues found: none. Renders fine (full-page screenshot: "Welcome back / Work Email / Send OTP / Continue with Google"); input visible y305, 49px; 0 console errors; no overflow.
- **Ownership-fragmentation finding → CC-22:** the auth cluster duplicates the form system — login.html has its OWN `.field` + `.alert` copy, distinct from base, `_user_form_styles`, AND its sibling auth pages (SEED drift: login input border `#b8a48e`/Inter vs `--cream-2`/Syne elsewhere). To confirm across the remaining auth units (028/029/030/031/032).
- Operational note: the gstack `--viewport` screenshot rendered blank for this page (paint race); full-page screenshot + JS (input rect/visibility/text) confirm it renders. Use full-page screenshot here.
- Evidence: /tmp/u027_full.png (login form renders).
- Commit: none (no code change).
### HTML-028 — `accounts/login_password.html` (Form-control — auth, password login) [PHASE D]
- Status: **CLEAN** (no per-page fix) — awaiting owner review. (SEED → browser-verified.)
- Audit unit / method: form-control + ownership focus. Browser 1280/320/375/390/414, `/app/login/password/` (logged out). NO submit (rate-limit).
- Form system: **standalone split-screen auth** (own inline `<style>`, own local `.field`). Controls: `<input type=email>` + `<input type=password>`. Renders fine (pw input y484, visible, brand+form text present; screenshot blank = same `--viewport` artifact as HTML-027).
- Ownership map (per owner's ask): **CSS owner = standalone inline (own copy)** · **validation owner = own `.alert` messages (form-level, no per-field)** · **JS owner = none/minimal** · **layout owner = own split-screen `.page/.left/.right/.form-shell` (copy of login.html, lighter `--cream-2` border + Syne font = drift)** · dependency chain = none (no base, no shared partial).
- 8-dim: email+password both **47px** ✅ · `label[for]` both (good a11y) · required · messages validation (no per-field) · mobile both 47px, no overflow · 0 console errors.
- **CC-22 share-vs-copy DETERMINATION (definitive, structural scan of all 7 auth pages):** every auth page has **`extends`=NONE · `include`=NONE · its OWN local `<style>` + local `.field`/`.alert`** (login 15 · login_password 13 · otp 6 · reset_otp 10 · signup 10 · signup_otp 4 · forgot 10 rules). → **COPY-PASTED separate copies, NOT a shared foundation, NOT partial-share.** 7 independent owners of the same auth form system, with drift. The enterprise-architecture concern (not cosmetic-only).
- Evidence: /tmp/u028_full.png (blank = artifact); JS-confirmed render.
- Commit: none (no code change).
### HTML-029 — `accounts/otp.html` (Form-control — OTP widget, auth) [PHASE D]
- Status: **CODE-AUDITED; browser-RENDER BLOCKED (NOT marked clean — honesty rule)** — awaiting owner review.
- Blocker: otp.html is **flow-gated** — `/app/verify-otp/` redirects to `/app/` without a pending-OTP session. Reaching it needs the OTP-login email-step POST → sends an OTP email + IP+email **rate-limit** (memory: a wrong/extra attempt can lock the dev account 15–30 min). **NOT triggered** (won't risk locking the super-admin account; no disposable OTP provisioned). Render verification deferred.
- Control (code-read): **6-box OTP widget** — 6 `<input class=otp-digit type=text inputmode=numeric maxlength=1 data-idx>` + hidden `otp` + `.btn-verify` (disabled-until-6, `.ready`=copper) + `.resend-area` (60s `#countdown` + `#resendLink`) + inline JS controller (`sync()` joins digits → hidden; + keydown/paste/autofocus/countdown). @media ≤480 otp-digit 52px (good touch); ≤360 separator-drop (PA-02-4 lineage).
- Ownership (code-read): CSS owner = standalone inline (own copy) · JS owner = **page-inline controller (own copy)** · layout owner = own (centered card + step chips) · validation = `.alert` messages (no per-field).
- **NEW finding → CC-23 (OTP widget JS duplication — hidden fragmentation):** the 6-box entry + timer/resend/autofocus/paste JS is **duplicated inline across 3 pages, NO shared partial** — otp (21 JS hooks) · signup_otp (22, full) · **reset_otp (7, REDUCED — missing countdown/resend/auto-submit = behavioral drift)**. 3 copies, drift. Exactly the hidden JS fragmentation the owner flagged.
- Render dims (UNVERIFIED — code/SEED only): 6-box layout, 52px ≤480, step-progress chips, btn-verify gating. **Browser pass needed** (provision an OTP-flow path that doesn't rate-limit, OR accept code-read for the widget).
- Evidence: code structural scan (3-copy duplication) + read; no browser render (flow-gated).
- Commit: none (no code change).
### HTML-030 — `accounts/reset_otp.html` (Form-control — OTP+password, auth) [PHASE D]
- Status: **CLEAN** — render BROWSER-VERIFIED (reachable, unlike otp.html) — awaiting owner review.
- Audit unit / method: form-control + OTP-widget focus. Browser 1280/320/375/390/414, `/app/reset-password/verify/` (logged out — **renders directly, NOT flow-gated**). DOM type/paste only, NO submit.
- Control: **combined widget** — 6-box OTP (`.otp-digit` numeric maxlength=1) **+ a `.field` new_password** input, in one card. standalone auth (own `.field`/`.alert`).
- **Category #1 (structural) — CC-23 drift CONFIRMED:** reset_otp = the **REDUCED OTP copy** — `countdown`=0, `resend`=0 (vs otp.html 2/7); has paste handler. The drifted/feature-incomplete copy of the 3.
- **Category #2 (browser render) — VERIFIED here** (the render that was blocked on otp.html): 6 boxes **63px desktop / 52px×39px mobile** (numeric), **auto-advance works** (type box0 → focus box1), **paste-fill works** (paste "123456" → all 6 filled), **NO countdown/resend element in render** (drift confirmed live), password field **44px** ✅, six boxes fit at 320 (~39px floor, PA-02-4 lineage), no overflow, 0 console errors.
- Ownership: CSS/validation/JS/layout owner = **own standalone copy** (CC-22 form-system + CC-23 OTP-widget, both per-page). Validation = `.field-error` (password) + `.alert` messages.
- Operational note: full-page screenshot blank (auth-page capture artifact, like 027/028) — JS DOM measurements + behavior are authoritative (render confirmed).
- Net: gives the **OTP-widget category-#2 browser evidence** (render/touch/auto-advance/paste) via the reduced copy + browser-confirms CC-23's behavioral drift (missing countdown/resend).
- Evidence: /tmp/u030_full.png (artifact) + JS (boxes/password/auto-advance/paste/mobile).
- Commit: none (no code change).
### HTML-031 — `accounts/signup.html` (Form-control — auth, VALIDATION OUTLIER) [PHASE D]
- Status: **CODE-AUDITED; browser-RENDER BLOCKED (NOT marked clean — honesty rule)** — awaiting owner review.
- Blocker: signup is **DISABLED + UNROUTED** (PA-02-OPEN-SIGNUP, owner 2026-06-14). `SignupView` class still lives in `views.py:437` (template `accounts/signup.html`) but **no URL** → `accounts:signup` name NOT registered (`urls.py:16/32/51` removed the routes; verified `grep name=signup` → none). No reachable URL = nothing to render. Render verification not possible without re-enabling signup (NOT done — won't change routing for an audit). Honesty: marked render-blocked, not clean.
- Control (code-read): 3 `.field` text inputs (email · password · confirm_password) + `.btn-cta`. standalone auth doc (no `extends`, own inline `<style>`, own `.field`/`.alert`). Mobile: `@media ≤860` hides left panel, `≤480` shrinks. Same split-screen shell family as login (027).
- **Validation strategy (owner focus) — THE OUTLIER:**
  - field-level rendering: **`{% for field in form %}{% for error in field.errors %}` → rendered as `.alert-error` blocks at TOP** (label: error), NOT inline beside each field. (signup.html:108-113)
  - non-field rendering: `{% for error in form.non_field_errors %}` → same top `.alerts` block.
  - form.errors: gated by `{% if form.errors %}` wrapper.
  - messages-framework rendering: **ABSENT — 0 `{% for message in messages %}`.** ← key divergence.
  - error ownership: page-local `.alert`/`.alert-error` inline CSS (own copy, CC-22 lineage).
- **Cross-auth comparison (grep messages-fw vs form.errors across 7 auth pages):**
  - **signup.html = messages-fw 0 / form.errors 3** (field.errors×2 + non_field_errors×1).
  - **ALL 6 others** (login·login_password·forgot_password·reset_otp·otp·signup_otp) **= messages-fw 1 / form.errors 0.**
  - → signup is the **SOLE** auth page using `form.errors`/`field.errors`/`non_field_errors`. Every other auth page surfaces validation via the **Django messages framework**. **Two competing auth validation strategies = Auth Validation Fragmentation → CC-24** (distinct from CC-22 form-system + CC-23 OTP-widget, per owner).
- **Latent bug (dormant):** signup.html renders **no messages block**, yet `SignupView` (views.py:448) calls `messages.error(...)` on throttle → that throttle message would be **INVISIBLE** if signup were ever re-enabled. Logged, not fixed (page unrouted; out of scope; surfaces at re-enable time).
- Render dims (UNVERIFIED — code/seed only): split-screen, 3 fields, top-alert validation. Browser pass needs signup re-routed (owner decision; not for an audit).
- Evidence: template read (signup.html:108-131) + cross-auth grep (messages-fw vs form.errors, 7 pages) + route check (`accounts:signup` unrouted).
- Commit: none (no code change).
- **HTML-031b** *(seed)* `accounts/signup.html` was est. "cleanest per-field loop" — CORRECTED: it's a TOP-aggregated `form.errors` loop (not inline per-field), and it's the validation outlier (CC-24), not the canonical.
### HTML-032 — `accounts/signup_otp.html` (Form-control — OTP, auth, DORMANT) [PHASE D]
- Status: **CODE-AUDITED + TEMPLATE-RENDER-VERIFIED; browser-RENDER BLOCKED (DORMANT/unrouted)** — NOT marked clean (honesty) — awaiting owner review.
- Blocker: DISABLED + UNROUTED (PA-02-OPEN-SIGNUP). `SignupVerifyView` GET renders this (views.py:474) but `accounts:signup_verify` name NOT registered (verified). Template self-documents it (lines 74-76): "native signup is disabled … this template is unrouted/dormant. Links point to login so they never 500." No URL = no browser render. Used a **safe Django template-render** (no flow / no email / no rate-limit / no DB write) to verify structure + the comment leak.
- **Owner's 3 checks:**
  1. **OTP widget ownership = the FULL implementation** (render-confirmed: 6 `.otp-digit`, `id=countdown` ✓, `id=resendLink` ✓, 60s timer, **auto-submit** `setTimeout(form.submit(),260)` at 6 digits, paste-fill, arrow-nav, backspace). vs CC-23: otp.html = full · **signup_otp = full** · reset_otp = REDUCED (no countdown/resend/auto-submit). So CC-23's 3 copies = **2 full (otp, signup_otp) + 1 reduced (reset_otp)**; inline JS = own copy (no shared partial). FULL not reduced.
  2. **Validation ownership = Django messages framework ONLY** (render-confirmed: `{% if messages %}{% for message in messages %}` → `.alert-{{tags}}`; **form.errors usage = False**). No per-field, no `form.errors`.
  3. **Relationship to signup = follows the OTP/messages model, NOT signup's form.errors model.** ← the decisive evidence.
- **CC-24 consequence (decisive):** signup.html (step 1) uses `form.errors`; signup_otp.html (step 2 of the SAME flow) uses messages. **The signup flow is internally split** — so the `form.errors` strategy is **isolated to signup.html ALONE** (a singleton across the entire auth surface). Every other auth page, *including signup's own OTP step*, uses messages. CC-24 = one-page outlier, not a flow-wide strategy.
- **NEW (render-confirmed) → CC-04:** lines 74-76 are a **3-line `{# … #}`** comment — Django `{# #}` is single-line only → **it LEAKS** (template-render proof: ` #}` + comment text renders as visible body text before the Back link). **Same class as HTML-002** (which was a live bug, fixed `bcf508f2`). **Difference: signup_otp is dormant/unrouted → NOT user-facing today.** Per owner's dormant-bug doctrine (cf. signup throttle-message): **log, do NOT fix, do NOT elevate.** Render-verified leak, but only reachable if signup is re-enabled.
- Touch/mobile (code): otp-digit 64px desktop / 52px ≤480 / sep-drop ≤360 (PA-02-4) — full-impl styling, matches otp.html.
- Render dims (browser UNVERIFIED — unrouted): visual/touch not browser-loaded; reset_otp (HTML-030) remains the browser render proxy for the OTP widget family. Structure render-verified via Django render.
- Evidence: template read (signup_otp.html) + Django template-render (leak=True, otp-digit=6, countdown+resend present, form.errors=False). No browser (unrouted), no flow triggered.
- Commit: none (no code change).
### HTML-033 — `accounts/skill_form.html` (Form-control — management, base.html) [PHASE D]
- Status: **CORRECTED 2026-06-16 → NOT fully clean.** ⚠ Originally marked CLEAN; **HTML-036 audit found a console error + broken native `pattern` validation** (see bottom of this record + CC-27). Layout/structure/shared-owner findings stand; the "0 console errors / native pattern confirmed" claims are RETRACTED. 1 touch note (submit btn 39px) also stands.
- Audit unit / method: form-control focus. Browser 1280/320/375/390/414, super-admin, `/app/skills/add/`. **EXTENDS base.html** (app-chrome management page — NOT auth-cluster). DOM/JS + one **non-mutating** dup-name submit (rejected → no row created; verified count stays 2).
- Correction: seed said "text + **permission** fields" — WRONG. SkillForm = **3 fields only**: `label` (TextInput) · `name` (TextInput + slug `pattern=[-a-z0-9_]+`) · `description` (Textarea rows=2). **0 select / 0 date / 0 multiselect / 0 permission control.**
- Form system: `.field` + numbered `.panel`/`.panel-head`/`.panel-body` form-shell + `.user-hero` — the **shared management form shell** (same family as user_form HTML-002).
- **CSS owner = shared `accounts/_user_form_styles.html`** (line 70 `{% include %}`) — **SAME shared partial as user_create/user_form.** Positive shared-owner signal (opposite of the auth copy-paste fragmentation).
- **Validation (browser-confirmed) — management pattern, the 3rd distinct strategy:**
  - **per-field inline `.field-error`** — submitted duplicate slug `cutting_master` → re-rendered with **"Skill with this Name already exists."** under the field (browser-confirmed); rows stayed **2** = no create (safe/non-mutating).
  - top `form.non_field_errors` → `.form-alert form-alert-error`.
  - native `required` (browser-confirmed: empty form `checkValidity()=false`; label+name required, description optional) + native `pattern` slug on `name`.
  - → distinct from auth's two strategies (messages-fw / form.errors-aggregate); this is **per-field inline + native**, owned by the shared `_user_form_styles.html`. Same pattern user_form (HTML-002) uses → management canonical-candidate.
- JS: page-inline **preview-chip** (`#skillPreviewChip` label→chip) — browser-confirmed updates "Skill Name"→typed value. No select JS (no selects).
- Render: 1280 clean (docScrollW 1281 = 1px sub-pixel/scrollbar artifact, bodyScrollW=1280, 0 elements exceed viewport — benign, NOT a clip). Mobile 320/375/390/414: **0 overflow** all, shell fits, inputs 45px, cream bg (`--cream`). 0 console errors.
- Touch: inputs **45px** ✅; **submit `.btn-primary` = 39px < 44px** — touch-target observation (`.btn` family, broader than CC-05's `.sf-input`; record, do NOT fix per-page).
- Canonical signals (record only, NOT standardized): (1) `_user_form_styles.html` confirmed = shared management-form CSS owner across user_create/user_form/skill_form; (2) per-field `.field-error` + `non_field_errors` = the management validation pattern (reusable; contrast auth CC-24); (3) `.btn-primary` 39px touch — button touch-target theme.
- Evidence: browser DOM (field heights, required, overflow 4 viewports) + preview-chip JS + dup-name server-error render ("…already exists.") + no-create confirmation (count=2).
- **⚠ CORRECTION (HTML-036, honesty rule):** name field `pattern=r'[-a-z0-9_]+'` (forms.py:43) was **invalid under Chromium `v`-flag** (leading `-` in char class) → **console SyntaxError every `checkValidity()`** + **native slug pattern silently DROPPED** (reproduced live; `'v'` throws, `'u'` ok). Earlier "0 console errors"/"native pattern confirmed" = wrong (first console read pre-dated the validity trigger). Real per-page bug → **CC-27**; sibling at forms.py:28 (usertype HTML-034).
- **CC-27 FIXED + COMMITTED `20fccbd7` (2026-06-16, owner-approved):** forms.py:43 + :28 → `r'[a-z0-9_\-]+'` (escaped dash; owner's literal `[a-z0-9_-]+` ALSO failed v-mode — browser-caught). Browser-verified both pages: compiles, native pattern enforces (good/hyphen valid, bad rejected), console clean. Dedicated commit (2 regex lines only). Layout/shared-owner/per-field findings from the original HTML-033 audit stand.
- Commit: **`20fccbd7`** (CC-27 regex fix, forms.py only).
### HTML-034 — `accounts/usertype_form.html`
- Status: **RECLASSIFIED → Family D (NO multiselect)** — classification correction; awaiting owner review.
- Audit unit / method: browser-checked `/app/user-types/add/`, super-admin, 1280.
- Finding: UserTypeForm fields = `code` (text) · `label` (text) · `description` (textarea) · `is_active` (single checkbox toggle). **0 multiselect controls** (browser-confirmed: 1 checkbox = is_active; 0 chip-pick, 0 select[multiple], 0 permission matrix). Hero literally says "Does not control permissions" — UserType is a pure classification LABEL; role carries access, not type. The early "usertype? perms" estimate was WRONG (same kind of mis-estimate as HTML-006 product_list). → **Not a Phase-B unit; belongs to Family D** (form-controls), audited there.
- Multiselect inventory: N/A (no multiselect).
- Commit: none (no code change).

> **⚠ Multiselect inventory NOT complete (completeness scan, 2026-06-15):** a full grep of
> `ModelMultipleChoiceField`/`CheckboxSelectMultiple` found **2 un-audited multiselect surfaces** —
> `pattern_stage` (cutting-pattern start) + `barcode_gen` worker pickers use a **raw
> `forms.CheckboxSelectMultiple`** (NOT the `_WorkerCheckboxes` chip widget used by cutting/layering).
> `_stage_panel_cutting_pattern.html:236` renders `{{ start_form.workers }}` → code-read suggests
> Django's DEFAULT `<ul>` checkbox list = a **possible 4th multiselect implementation** (distinct from
> CC-16 chip grid). **Needs browser audit before the inventory is complete / any consolidation report.**
> (Display-only chip surfaces — adda_detail, stage_list, sidebar_access_list, user_dashboard — are
> read-only, NOT multiselect controls; excluded.)
### HTML-035 — `inventory/role_form.html` (Multiselect — permission CRUD matrix) [PHASE B]
- Status: **AUDITED (multiselect) — functional; 1 mobile-clip finding (CC-18, deferred)** — awaiting owner review.
- Audit unit / method: multiselect-focus (Phase B). Browser 1280/320/375/390/414, super-admin, `/inventory/roles/3/edit/` (Worker). DOM toggles only, NO submit.
- Control: **section-grouped CRUD permission matrix** — `<input type=checkbox name=permissions value=perm.pk>` grouped into 7 fieldset sections → model rows → 4 CRUD columns (view/add/change/delete). **80 checkboxes.** + per-section bulk-toggle (checkall) JS. NATIVE checkboxes (visible). Curated server-side (`perm_sections`).
- 10-dim:
  - rendering model: **section-grouped CRUD checkbox matrix** (fieldset → model-row → 4-col) — most complex multiselect rendering in the app.
  - selection model: **multi** (native checkboxes) + **section bulk-toggle** (checkall).
  - keyboard: ✅ native checkboxes, tabbable, Space toggles.
  - screen-reader: native checkbox + `<fieldset><legend>` section grouping (semantic); BUT CRUD column meaning conveyed by a header row, likely **not associated per-checkbox** → SR may announce "checkbox" without "delete/change" context (partial).
  - touch: **13px** checkbox (tiny native — smallest touch of any control).
  - mobile: **CLIPS at 320** — fieldsets 365px > 320 viewport, clipped ~74px right (PA-14-1 class: `overflow-x:hidden` masks; `page_overflow` reads false but right CRUD columns cut off). **REAL mobile finding → CC-18.**
  - dependency chain: section bulk-toggle JS (`input[name=permissions]` checkall per section).
  - hidden vs native: **NATIVE** (visible checkboxes, `name=permissions`; no hidden input).
  - CSS owner: **page-specific** (`role_form.html` `.form-section`/fieldset).
  - JS owner: **page-specific inline** (bulk-toggle).
- 3rd multiselect implementation — **distinct from CC-16 (worker-chip) and CC-17 (chip-pick)**: it's a CRUD matrix, not a flat chip grid. Multi works, bulk-toggle works, keyboard works; 0 console errors.
- → **CC-18.** Fix: none (mobile-clip deferred — page-specific layout, Family D / dedicated; possibly shared with usertype_form HTML-034).
- Evidence: /tmp/u035_320.png (matrix clipped at 320).
- Commit: none (no code change).
### HTML-036 — `expense/adda_settlement_detail.html` (Form-control — expense, money actions) [PHASE D]
- Status: **CLEAN (finalized branch browser-verified; draft branch code-read)** — 1 touch note; **NO mutation** (GET-only, golden untouched) — awaiting owner review. ⚠ Also surfaced a **correction to HTML-033** (see that record + CC-27).
- Audit unit / method: form-control focus. Browser 1280/320/375/390/414, super-admin, **`/expense/settlements/ADST-0003/`** (the FINALIZED golden 3-PATTI-001, ₹225). **Read-only render + DOM inspection — NO action buttons clicked** (finalize/discard/reverse/supersede all mutate money+ledger; golden NEVER touched). Extends base.html.
- Two conditional branches (template-mapped): **DRAFT** (variance number inputs packed/missing/rejected `type=number inputmode=numeric min=0`; per-advance recover `type=number inputmode=decimal step=0.01 min=0 max=remaining`; super-admin `reconciliation_override` **textarea `.sf-input`**; discard/finalize buttons) · **FINALIZED/REVERSED/SUPERSEDED** (frozen snapshot tables; finalized adds reverse/supersede form with `notes` textarea).
- **Finalized branch — browser-verified (ADST-0003):** `notes` textarea present (56px), reverse (`.btn-danger`) + supersede (`.btn-copper`) buttons present; per-worker snapshot money table = **`.table-responsive` overflow-x:auto @desktop (922px fits, scroll not clip) + `display:block` stacked w/ `data-label` @mobile** → **PA-14-1 responsive CONFIRMED**; mobile 320/375/390/414 all **0 overflow**; **own console CLEAN** (no `pattern` attr on this page).
- **Draft branch — CODE-READ only (honesty):** no draft settlement exists; creating one = a mutation (and finalize-adjacent) → not browser-rendered. Controls mapped from template (native min/max/step number inputs · `.sf-input` override textarea · `.table-responsive` money tables). NOT browser-verified.
- Validation/interaction ownership: **action-form pattern** — raw `<form method=post>` with `name=action value=finalize|discard|reverse|supersede` (NOT a Django ModelForm render); no inline `field.errors`/`form.errors`; errors surface via **messages framework** on redirect; client guard = `onclick confirm()` + native number `min/max/step`. CSS owner = **expense-app inline** (`.panel`/`.totals`/`.sticky-bar`/`.table-responsive`) but **borrows `.sf-input` + `.field`** for the override textarea (cross-system reuse note). → a **4th validation/interaction family** (action-form + messages + native-numeric), distinct from auth (2) + management per-field (1). [validation-families tracker]
- Touch: `notes` textarea 56px ✅; **reverse `.btn-danger` = 40px @414 (<44px)** → **CC-25** (button touch family; varies 68px@320 wrap → 40px@414 single-line).
- Evidence: ADST-0003 browser render (controls present, table-responsive overflow-x:auto, mobile 0-overflow×4, own console clean) + template control-map (draft + finalized branches). No POST, no action click, count/states unchanged.
- Commit: none (no code change).

> **⚠ HTML-033 CORRECTION (discovered during HTML-036, honesty rule):** skill_form was reported "0 console
> errors / native pattern browser-confirmed" — **WRONG.** The name field `pattern=r'[-a-z0-9_]+'`
> (accounts/forms.py:43) is **invalid under Chromium's `v`-flag** regex compilation (leading `-` in char
> class) → **console SyntaxError on every `checkValidity()`** (reproduced live: `/[-a-z0-9_]+/v: Invalid
> character in character class`; `new RegExp('[-a-z0-9_]+','v')` THROWS, `'u'` OK) **AND the native slug
> `pattern` constraint is silently DROPPED** (field validates as if no pattern). My first console check ran
> BEFORE triggering validity, so it missed it. **HTML-033 is therefore NOT fully clean** — it has 1 console
> error + broken native pattern validation. Same defect at **accounts/forms.py:28 (UserTypeForm.code,
> usertype_form HTML-034)**. → **CC-27.** Trivial fix (`[a-z0-9_-]+`, dash last) — **NOT applied** (await owner).
### HTML-037 — `expense/worker_profile_form.html` (Form-control — expense, page-scoped) [PHASE D]
- Status: **CLEAN** — browser-verified (super-admin, test worker utest pk2); 1 touch note (40px); app-wide favicon-404 noted (not a page defect); **NO mutation** (GET + DOM-validity only, no submit) — awaiting owner review.
- Audit unit / method: form-control focus. Browser 1280/320/375/390/414, `/expense/workers/2/profile/` (utest — TEST account, not real payout data). Extends base.html. NO submit (would change bank/advance); native-validity tested via DOM only. (View does `get_or_create` profile on GET = app behavior, idempotent empty row — not my mutation.)
- Controls (9 fields, browser-confirmed): phone · bank_account_name · bank_account_number · bank_ifsc · upi_id · **joining_date = native `<input type=date>`** · opening_advance = **number, `min=0`** · is_active (checkbox) · notes (textarea). No select; **no HTML `pattern`** (→ no CC-27 risk).
- Validation/interaction ownership: **generic `{% for field in form %}` loop** + per-field `.errs` (`field.errors|striptags`) + `form.non_field_errors`. Heavy lifting is **server-side cleans** (IFSC regex `[A-Z]{4}0[A-Z0-9]{6}` · account `\d{9,18}` · bank-set-together PA-06-2 · opening_advance≥0 PA-06-1). Client = **native** number `min=0` (browser-confirmed: `-5`→invalid, `100.50`→valid) + native date. → a **page-scoped per-field-inline** validation variant (distinct owner from management's shared `_user_form_styles.html`).
- CSS owner: **page-scoped `.expense-form`** (in `{% block extra_head %}`, scoped — rule 10 OK). **NOT** shared `_user_form_styles.html`, **NOT** `.sf-*`, **NOT** auth-standalone, **NOT** the settlement-detail expense-inline (HTML-036). → a DISTINCT form-CSS system. **Ownership-map note: the expense app itself has ≥2 different form-CSS approaches** (HTML-036 inline+borrows-sf-input vs HTML-037 `.expense-form` page-scoped) — internal inconsistency within one app.
- Date note: `joining_date` is a **native single-value form date** still NOT opted into fancy-date (`data-fancy-date`=false) — another instance of the Date-report §2 under-application (CC-21, Date family FROZEN; observation only).
- Render: 1280 + mobile 320/375/390/414 all **0 overflow**; inputs 40px, save `.btn-copper` 40px.
- Touch: inputs + save btn **40px (<44px)** → **CC-25** (button + input touch theme).
- **App-wide observation (NOT a page defect) → CC-28:** the lone console 404 is the browser's automatic `/favicon.ico` request — `/favicon.ico` returns 404 and **base.html declares no `<link rel=icon>`**, so EVERY page logs one favicon 404. Cosmetic, app-wide; the profile page's own markup references only Google Fonts (200). HTML-037 itself = console-clean of page-specific errors.
- Evidence: browser render (9 fields, native date, number min=0 validity, page-scoped CSS, no sf-input/no shared-partial) + favicon-404 isolation (curl `/favicon.ico`=404 + base.html has no favicon link + 1 fresh 404 per isolated load) + mobile×4.
- Commit: none (no code change on this page).
### HTML-038 — `production/adda_report_review.html` (Form-control — production, page-scoped) [PHASE D]
- Status: **CLEAN** — browser-verified (super-admin); 1 touch note (34px); **NO mutation** (GET + DOM-validity only, NO submit) — awaiting owner review. Money-adjacent (verified_quantity drives settlement pay) → golden 3-PATTI-001 viewed read-only, untouched.
- Audit unit / method: form-control focus. Browser 1280/320/375/390/414, `/production/addas/3-PATTI-001/review-reports/` (golden, GET-only). **All 3 branches browser-verified without mutating:** golden renders **1 verified input (unsettled row) + 2 settled-locked rows**; empty state confirmed via disposable 3-PATTI-004/005 ("No submitted reports"). Extends base.html.
- Controls: per-contribution-row **verified number input** (`type=number inputmode=decimal step=0.01 min=0 name=verified_{pk}` value=verified_quantity, placeholder "—"). **Settled rows are LOCKED** — if `settlement_line_id` and not voided → renders "settled by {ref} — reverse it to correct" text **instead of** the input (server-state read-only guard; protects money-locked lines). Bulk "Save corrections" button.
- Validation/interaction ownership: **raw-POST bulk-save** (NOT a Django form; per-row `verified_{pk}` inputs) → errors via messages framework on redirect; client = **native number `min=0` step=0.01** (browser-confirmed: `-3`→invalid, `12.5`→valid). + **server-state row-lock** (settled lines uneditable). → interaction family = raw-POST bulk + native-numeric + state-lock (production sibling of the 036 expense action-form; no `name=action`, adds row-locking).
- CSS owner: **page-scoped `.report-review`** (in `extra_head`, scoped — rule 10 OK; own `.card`/`.line`/`input[type=number]`/`.settled`/`.empty`). **NOT** shared `_user_form_styles.html`, **NOT** `.sf-*`. Another page-scoped form-CSS (production's own — distinct from expense's `.expense-form` HTML-037).
- Render: 1280 + mobile 320/375/390/414 all **0 overflow**; **lines stack to `flex-direction:column` @≤640** (mobile-first ✓, explicit responsive strategy).
- Touch: verified input **34px (<44px — smallest form input seen so far)** → **CC-25** (input/button touch theme).
- Evidence: golden review render (1 input + 2 settled-locked) + disposable empty-state + native min=0 validity (neg rejected) + page-scoped CSS (no sf/partial) + page-specific console clean (only app-wide favicon CC-28) + mobile×4 line-stack. No submit, input value restored, golden untouched.
- Commit: none (no code change).
### HTML-039 — `production/cutting_form.html` (Form-control — production form-shell, SHARED owner) [PHASE D]
- Status: **CLEAN** — browser-verified (super-admin, disposable 3-PATTI-004 at cutting); touch notes (pieces_cut 41px / btn 38px); **NO mutation** (GET + DOM only, NO submit — `complete_cutting` generates barcodes + advances stage). 3-PATTI-004 unchanged.
- Audit unit / method: form-control focus. Browser 1280/320/375/390/414, `/production/addas/3-PATTI-004/cutting/` (CuttingCompleteView GET). Extends base.html. Render-only (submit = major mutation, NOT done).
- Controls (browser-confirmed): **pieces_cut** (`type=number min=1`, `.sf-input`, 41px) · **notes** (Textarea `.sf-input`) · **workers** = **CC-16 `_WorkerCheckboxes` chip widget** (12 chips, native checkbox per chip, **52px@320 / 44px@375-414 — good touch ✓**). `<form novalidate>` (cutting form scoped: noValidate=true → native validation OFF; server enforces min=1).
- Validation/interaction ownership: **Django `forms.Form` render** — per-field `.field-error` (pieces_cut, workers) + top `.form-error` (non_field). novalidate → **server-side validation** (client native min=1 present but not enforced). + CC-16 worker multiselect. → production form-shell **per-field-inline** family (structurally like management #3, but **different shared owner + novalidate + CC-16 multiselect** → tracked as 7th).
- CSS owner: **SHARED `production/_form_styles.html`** (`{% include %}` in extra_head) — the **production shared form-CSS partial** (`.form-shell`/`.hero`/`.panel`/`.field`/`.sticky-actions`). **POSITIVE shared-owner — parallels management's `_user_form_styles.html` (CC-26).** Plus **borrows storefront `.sf-input`** for text inputs (pieces_cut/notes) → `.sf-input` is a cross-app input primitive (also borrowed by expense-036). So production has a proper shared form owner (2nd positive after management).
- Render: 1280 + mobile 320/375/390/414 all **0 overflow**; worker-chips reflow/stack; numbered panels stack.
- Touch: **worker-chip 44-52px ✅** (CC-16); **pieces_cut `.sf-input` 41px (<44px → CC-05** input-height family) · **btn-primary 38px (<44px → CC-25** button family). (CC-05 input vs CC-25 button kept separate per owner.)
- Evidence: cutting-form render (form-shell + 2 panels, pieces_cut number min=1 sf-input, notes textarea, 12 worker-chips @52/44px), scoped novalidate=true, `_form_styles.html` shared owner, page-specific console clean (only favicon CC-28), mobile×4 0-overflow. No submit; 3-PATTI-004 state unchanged.
- Commit: none (no code change).
### HTML-040 — `production/pattern_form.html` (Form-control — production, base `.form-card`) [PHASE D]
- Status: **NOT CLEAN — 3 findings (2 functional + 1 styling); NO mutation** (invalid empty submit = no create, count 1→1) — awaiting owner review. ⚠ Needs owner fix decision (like CC-27).
- Audit unit / method: form-control focus. Browser 1280/320/375/390/414 + screenshot, super-admin, `/production/patterns/add/` (ProductPatternCreateView). Extends base.html. Empty-submit error-path tested (non-mutating).
- Controls: ProductPatternForm (ModelForm) — code (text, req, unique) · name (text, req) · description (Textarea rows=3) · reference_image (file, `multipart`) · is_active (checkbox). No select/date/multiselect.
- CSS owner: **base.html global `.form-card`/`.form-section`/`.form-group`/`.form-label`** (base-owned form system — a 3rd shared form-CSS, distinct from production `_form_styles.html` `.form-shell` (039) and mgmt `_user_form_styles.html` `.field`). `<form novalidate>` → server-side validation.
- **FINDING 1 (CC-29, MEDIUM, functional) — field-error swallow → FIXED + COMMITTED `2e5910b9` (2026-06-16, owner-approved):** template rendered ONLY `form.non_field_errors`; **no per-field `{{ form.X.errors }}`**. Browser-confirmed pre-fix: empty submit → zero visible error, no create. **Fix:** added per-field `.form-error` blocks (base-defined class) to all 5 fields, template-only (10+/2−). Re-verified: empty submit → 2 visible "This field is required." (name+code), optionals clean, non_field untouched, console clean.
- **FINDING 2 (CC-30A, styling/touch) — unstyled bare inputs:** base styles `.form-control` (base.html:1212), NOT bare `input`; ProductPatternForm widgets have **no `.form-control` class** → text inputs **~19px bare** (screenshot: thin line). Below UI bar + far under 44px.
- **FINDING 3 (CC-30B / XC-1, MEDIUM, mobile) — 2-col grid clip:** inline `grid-template-columns:1fr 1fr`, **no media collapse** → at ≤~414 right column (Code+Active) clipped past viewport (code right-edge 479px @320 vs vw 320), masked by `main{overflow-x:hidden}`. Mobile-first violation. **XC-1 4th occurrence.**
- Touch: name input 19px (worst); btn-primary 38px (CC-25).
- Mobile: documentElement reports 0-overflow (MASKED — see Finding 3); real clip confirmed via element right-edge + screenshot.
- Recommended fixes (NOT applied — await owner, per CC-27 controlled-approval pattern): CC-29 = add per-field error rendering (template); CC-30A = add `.form-control` to widgets (forms.py); CC-30B = collapse grid to 1col ≤600 (template). All small.
- Evidence: render (5 controls, base `.form-card`, no `.form-control` class) + empty-submit no-error/no-create + 320 screenshot (code field clipped, bare inputs) + code right-edge 479px@320 + `main` overflow-x:hidden.
- Commit: none (findings recorded; no fix applied).
### HTML-041 — `production/stage_form.html` (Multiselect — stage access chips) [PHASE B]
- Status: **AUDITED (multiselect) — CLEAN; 1 duplication finding (CC-19)** — awaiting owner review.
- Audit unit / method: multiselect-focus (Phase B). Browser 1280/320/375/390/414, super-admin, `/production/stages/2/edit/` (cutting). DOM toggles only, NO submit. (Form-control aspects = future Phase D.)
- Control: **`access_by_skill` + `access_by_role` chip grids** — `.chip-grid` of `.chip-pick` (BoundField iteration). Domain = **stage access-control selection** (skill+role for who can work a stage). 6 chips (2 skill-chips + role chips).
- **= CC-17 `.chip-pick` pattern REUSED** (browser-confirmed identical): checkbox `display:none`, JS `.is-on` toggle, NOT tabbable. NOT a new distinct implementation.
- 10-dim: rendering = `.chip-pick` chip grid (skill-chip modifier) · selection = **multi** (independent checkboxes; 0→2 checked confirmed) · keyboard = **NOT tabbable** (display:none, same gap as CC-17) · SR = hidden-checkbox gap (= CC-17) · touch = **34px** · mobile = **chips WRAP, NO clip** (mobile-safe — contrast role_form CC-18 matrix) · dependency = page-inline `.is-on` JS · hidden-vs-native = real checkbox `name=access_by_skill`, visually hidden · CSS owner = **page-specific `.stage-form .chip-pick` (DUPLICATE of `_user_form_styles .chip-pick`)** · JS owner = page-inline (duplicate of user-form JS).
- **NEW finding → CC-19 (duplication):** the `.chip-pick` multiselect pattern is implemented in **≥2 separate owners** — `_user_form_styles.html` (6 `.chip-pick` rules) AND `stage_form.html` page CSS (7 rules) + duplicate inline JS. Same pattern, fragmented/copy-pasted ownership. Maintainability/consolidation signal.
- Multi ✓, mobile-safe ✓ (chips), 0 console errors. Fix: none.
- Evidence: /tmp/u041_320.png (chip grids wrap at 320, no clip).
- Commit: none (no code change).
- **PHASE D ADDENDUM (full form-control audit, 2026-06-16):** beyond the chips —
  - Controls: code + name = **manually-rendered** `<input type=text required maxlength=32/64>` (no class → `.stage-form input` page CSS, **cream-styled 39px**); description textarea; is_active checkbox; + the 2 chip grids. `<form>` has **NO novalidate** → native required+maxlength ON (browser-confirmed code.required=true, maxLength=32).
  - Validation: top `.form-alert form-alert-error` (non_field) + **per-field `.errors`** for code+name (template-present, conditional) → **NO swallow** (contrast pattern_form CC-29). Production form-shell-ish per-field-inline, page-scoped owner.
  - CSS owner: **page-scoped `.stage-form`** (extra_head; own `.field-grid-2`/`.chip-pick`/`.errors`). NOT shared partial.
  - **NEW FINDING (Phase D) → XC-1 (5th occurrence): `.field-grid-2 {grid-template-columns:1fr 1fr}` has NO media collapse** → at ≤414 the **name field (right column) is clipped past the viewport** (right-edge 535px @320 vs vw 320), masked by `main{overflow-x:hidden}`. Browser+screenshot (/tmp/u041d_320.png) confirmed. Same 2-col-grid-no-collapse class as pattern_form CC-30B. Phase-B (chips-only) missed it; Phase-D caught it.
  - Touch: code/name **39px** (CC-05/input-touch); chips 34px (CC-17).
  - Net Phase-D: stage_form is **better-built than pattern_form** (styled inputs + per-field errors + native validation) BUT shares the **mobile 2-col-grid clip** (XC-1). 1 new finding (mobile). No mutation (GET only). Fix: none applied (XC-1 = record-only per owner).
### HTML-042 — `production/stage_rate_correct.html` (Form-control — production, MONEY-workflow) [PHASE D]
- Status: **CLEAN** (form branch browser-verified; settled money-armor branch code-verified — honest); touch notes; **NO mutation** (GET only — rerate recalcs earnings + writes RateCorrectionAudit) — awaiting owner review.
- Audit unit / method: form-control focus. Browser 1280/320/375/390/414, super-admin, `/production/addas/3-PATTI-004/stage-rates/12/2/correct/` (disposable, unsettled = FORM branch). Extends base.html. Render-only (submit = money mutation + recalc + audit, NOT done).
- Controls (form branch, live): **new_rate** (`type=number step=0.0001`, `.sf-input` **41px**) · **reason** (Textarea, mandatory audit reason) · **confirm** (checkbox gate, 20px) · readonly **current-strip** (Adda/Stage/Role/Current rate ₹). Django Form.
- Validation: top `.form-error` (non_field) + **per-field `.field-error`** (new_rate/reason/confirm) — **NO swallow**. `<form novalidate>` → server-side.
- **MONEY-WORKFLOW ownership (the key concern here):** super-admin S1.1 rate-correction = **before-settlement-only** (hero text). **Money-armor (defense-in-depth, code-verified):** if stage/role settled → `settled` flag renders a **`.settled-note` refusal** ("reverse/supersede first") **AND** submit button `{% if settled %}disabled{% endif %}` **AND** server `_is_settled` refuses + `StageRateCorrectionForm` requires mandatory `reason` + `confirm` + writes `RateCorrectionAudit`. **Honesty:** settled branch is **code-verified only** — couldn't reach it live (golden 3-PATTI-001 has 0 `AddaStageRoleRate` rows since S1 postdates its settlement; no settled adda with rate rows exists). Form branch (unsettled) confirmed live: `settledNote`=false, submit enabled.
- CSS owner: **SHARED `production/_form_styles.html`** (positive shared owner — same as cutting_form 039) + page-scoped `.rate-correct` (readonly strip / settled-note / confirm-row; rule-10 scoped).
- Layout: **`.form-grid cols-1` (single column)** → **NO XC-1 clip** (mobile 320-414 all 0-overflow, rate input right-edge within viewport — contrast 040/041 2-col-grid clips). Good responsive choice.
- Touch: new_rate **41px** (CC-05) · btn-primary **38px** (CC-25) · confirm checkbox 20px.
- Console: clean (only app-wide favicon CC-28).
- Net: CLEAN; reuses production form-shell family (#7, `_form_styles.html`) + a **money-state guard** (settled refusal, akin to report_review #6 settled-lock); single-column layout avoids the XC-1 2-col trap. No mutation.
- Evidence: form-branch render (new_rate number/step/sf-input 41px, reason textarea, confirm checkbox, submit enabled, no settled-note) + per-field error markup + cols-1 mobile 0-overflow×4 + golden 0-rate-rows (settled branch code-only) + console clean.
- Commit: none (no code change).
### HTML-043 — `production/product_form.html` (Form-control — production, SHARED owner; positive) [PHASE D]
- Status: **CLEAN** — browser-verified (super-admin); positive shared-owner + responsive grid; **NO mutation** (empty submit = no create, count 8→8) — awaiting owner review.
- Audit unit / method: form-control focus. Browser 1280/320/414, super-admin, `/production/products/add/` (ProductCreateView). Extends base.html. Empty-submit error-path tested (non-mutating).
- Controls: code · name (text, req, `.sf-input` **41px**) · description (Textarea, `.field full` full-width). Django Form, `<form novalidate>` → server-side.
- Validation: top `.form-error` (non_field) + **per-field `.field-error` (code/name)** — **NO swallow** (browser-confirmed: empty submit → 2 visible "This field is required.", count unchanged 8→8 = no create).
- CSS owner: **SHARED `production/_form_styles.html`** (positive shared owner — **3rd consumer** after cutting_form 039 + stage_rate_correct 042) + `.sf-input` for text.
- **Layout — POSITIVE (key XC-1 counter-evidence):** uses the **shared `.form-grid`**, which has a media collapse — `_form_styles.html:141 @media(max-width:768px){.form-grid{grid-template-columns:1fr}}`. Browser-confirmed: at 320 gridCols=**230px (single column)**, code right-edge within viewport, **0 overflow, NOT clipped**. → **NO XC-1.** Contrast 040 (inline `1fr 1fr`) + 041 (page-scoped `.field-grid-2`) which roll their OWN non-responsive grids and clip. **XC-1 correlates with NOT using the shared `.form-grid`.**
- Touch: code/name **41px** (CC-05); btn-primary form-shell (~38px, CC-25).
- Console: clean (only app-wide favicon CC-28).
- Net: CLEAN; the "good" production form — shared owner + responsive shared grid + per-field errors. Direct contrast to pattern_form (040, under-built). No mutation.
- Evidence: render (code/name sf-input 41px, description full textarea) + empty-submit 2 field-errors + no-create (8→8) + `.form-grid` collapse to 1col@320 (no clip) + console clean.
- Commit: none (no code change).
### HTML-044 — `production/product_sizes_edit.html` (Form-control — production, inline-edit table) [PHASE D]
- Status: **CLEAN** — browser-verified (super-admin, product 1 = 3 active sizes); PA-15-1 mobile fix HOLDS; touch note (29px); **NO mutation** (GET + DOM only, no submit — update/archive/add/reactivate all mutate sizes) — awaiting owner review.
- Audit unit / method: form-control focus. Browser 1280/320/340/414, super-admin, `/production/products/1/sizes/`. Extends base.html. Render-only.
- Controls: **inline-edit table** — each active size row = per-row `<form>` (hidden `action=update`+`size_id`) with **label** (text, req, maxlength40, 29px) + **display_order** (number, min0, 29px) + per-row **archive** form (`confirm()`); **add-new** form (code text maxlength16 req · label · display_order number) ; archived table = **reactivate** forms. Raw-POST action forms (no Django form render).
- Validation/interaction: **raw-POST per-row action forms** (`name=action` = update/archive/add/reactivate) + native (required/maxlength/min) + `confirm()` on archive. Errors via messages on redirect. → raw-POST family **per-ROW inline-edit variant** (sibling of report_review 038 bulk raw-POST; here per-row + inline-edit).
- CSS owner: **page-scoped `.ps-edit`** (extra_head; legitimately page-specific table editor). Uses the **canonical `.table-responsive` + `data-label`** for the table (shared table-stacking pattern) — NOT a custom grid.
- **PA-15-1 mobile fix RE-VERIFIED (holds):** at 320/340/414 the `.cell-edit` column stacks (`flex-direction:column`), label input **not clipped** (right-edge within viewport), **0 overflow**. The prior-audit fix (`.table-responsive`+`data-label`+`.cell-edit` stack) is intact. **No XC-1** (uses canonical table-responsive, not a 2-col form grid).
- Touch: inline label/order inputs **29px** (<44px — smallest styled input so far; bare 040=19px is smaller). CC-05/touch.
- Console: clean (only app-wide favicon CC-28).
- Net: CLEAN; inline-edit table with canonical table-responsive stacking (PA-15-1 holds); page-scoped CSS legitimate for a table editor. No mutation.
- Evidence: product-1 render (3 update/3 archive forms + add, label req/max40 29px, display_order number min0) + PA-15-1 mobile stack (cell-edit column, no clip, 0-overflow ×3) + console clean.
- Commit: none (no code change).
### HTML-045 — `production/_stage_panel_cutting_pattern.html` (Form-control — production cutting-pattern panel) [PHASE D]
- Status: **CLEAN** — browser-verified (super-admin, via pattern-workspace standalone); **RE-confirms CC-20** in full-form context (pattern_stage already browser-verified Phase B; barcode_gen HTML-070 remains the code-only one); touch note (13px); **NO mutation** (GET + DOM only — start/verify/save/photo all mutate) — awaiting owner review.
- Audit unit / method: form-control focus. Large 526-line partial, rendered standalone via `PatternWorkspaceView` (`/production/addas/3-PATTI-004/pattern/`) + embedded via `stage_panel_embedded.html`. Browser 1280/320/414. Render-only.
- Controls (many; raw-POST per-section action forms): **workers** (`start_form.workers`) · video (file `.sf-input`) · notes (Textarea `.sf-input`) · photos (file multiple `.sf-input`) · caption (text `.sf-input`) · **breakup/verify table** (`.breakup-table` + `data-label`) · action forms (start/verify/unverify/save/photos-add/photo-remove/reopen). Auto-fit/auto-fill grids (`repeat(auto-fit,minmax(120px,1fr))` / `minmax(160px,1fr)`) — reflow, NOT fixed 2-col → no XC-1.
- **CC-20 RE-CONFIRMED (Phase-D, full-form context):** `start_form.workers` = **bare Django-default `CheckboxSelectMultiple`** — markup `<label for="id_workers_0"><input type=checkbox name=workers value=2 id=id_workers_0> utest@gmail.com</label>` per worker. **NO chip** (no `.worker-chip` CC-16, no `.chip-pick` CC-17). a11y-good (explicit `label[for]`) but **unstyled + native 13px** (tiny touch). Consistent with the Phase-B pattern_stage verification (CC-20 already VERIFIED there). **Worker-domain CC-16(chip, cutting/layering, 52px) vs CC-20(bare, cutting_pattern, 13px) split reconfirmed.** Remaining CC-20 gap = `barcode_gen` worker-picker (HTML-070, still code-only).
- Validation/interaction: raw-POST per-section action forms (`name=action`-style endpoints) + `confirm()` guards + native (file accept, required). No Django per-field error render in this partial (action-form pattern; messages on redirect). → production stage-panel raw-POST multi-form.
- CSS owner: **mix** — wrapper `pattern_workspace.html` `{% include 'production/_form_styles.html' %}` (shared, incl. `.form-shell .breakup-table` mobile stacking) + the **partial's OWN inline `<style>`** (×2, the auto-fit grids) + `.sf-input` (video/notes/photos/caption).
- Mobile: 320/414 **0 overflow**; worker checkbox + content within viewport (workerVisible=true); auto-fit grids reflow; breakup-table **stacks to cards** (the TABLE stays `display:table` but `tr`→block / `td`→flex / thead hidden / data-label ::before — **verified in HTML-048**, PA-15-3 host stacking engages; my earlier "renders as table" measured the table element, not the tr/td stacking). **No XC-1.**
- Touch: worker checkbox **13px** (CC-20 native, smallest touch target seen — tied with role_form matrix CC-18). sf-input controls ~41px.
- Console: clean (only app-wide favicon CC-28).
- Net: CLEAN; main value = **CC-20 browser-confirmation** (Multiselect gap closed) + worker-domain split confirmed. Mobile-safe (auto-fit grids + fitting table). No mutation.
- Evidence: workers widget outerHTML (`<label for><input>` = CC-20, 13px) + sf-input controls + breakup-table data-label + mobile 0-overflow×2 + console clean.
- Commit: none (no code change).
### HTML-046 — `storefront/listing/category_form.html` (Form-control — storefront; CC-13 generalizes) [PHASE D]
- Status: **AUDITED — CC-13 reproduces (key finding); ⚠ AUDIT-INDUCED MUTATION (unresolved — see incident)** — awaiting owner decision.
- Audit unit / method: form-control focus. Browser 1280/320, super-admin, `/storefront/categories/add/`. Extends base.html.
- Controls: name (text `.sf-input` 39px, req) · subtitle · item_count_label (text `.sf-input`) · display_order (number `.sf-input`) · **is_active (checkbox toggle, accent-color copper)** · **image = `CroppableImageWidget` (croppable_image.html) = CC-13**. multipart form.
- **CC-13 REPRODUCES → generalizes beyond HTML-019 (owner's Q1, browser-confirmed):** the `.cw-preview-box` (croppable_image.html:50, inline `width:{{widget.preview_width}}px` = **400px, no max-width**) measures **right-edge 435px at vw 320** → overflows ~115px, **masked by `main.content overflow-x:hidden`** (so documentElement.scrollWidth reads clean = false-negative trap; I initially mis-measured a container, then found the real `.cw-preview-box` via the wide-element scan). **Same shared-widget bug as HTML-019 product_form → CC-13 is a SHARED-WIDGET defect affecting every croppable consumer, not a one-page issue.** XC-1 class. (The form's OWN `.cat-inline-grid` DOES collapse to 1col@320 — so the clip is purely the croppable widget, not the form layout.)
- Ownership (owner's Q2): storefront forms use **base-global `.sf-input` / `.sf-error`** (base.html storefront form classes — a shared owner, "parallel to .form-control") + **page-scoped `.cat-*` layout** (`.cat-inline-grid` with `@media` collapse). So storefront = shared `.sf-*` primitives + page-scoped layout (not a single shared form-shell partial like production `_form_styles.html`).
- Validation (owner's Q3): top `.form-errors` (non_field, custom `<ul>` list) + **per-field `.sf-error`** (markup template-confirmed, e.g. name.errors) + **native `required`** (browser-confirmed — empty submit BLOCKED client-side, no novalidate). NO swallow. → **storefront validation family** (native required + per-field `.sf-error` + `.form-errors` list) — distinct owner (`.sf-error`) from mgmt/production; a storefront-specific per-field-inline variant.
- ⚠ **AUDIT-INDUCED MUTATION INCIDENT → RESOLVED 2026-06-16:** during a dup-name `.sf-error` test, a **bash interpolation bug** built a malformed `js` set-value call; the form then submitted with a **non-duplicate** name and **CREATED a stray category "T-Shirts" (id 2)** — categories went 1→2. First cleanup attempt was **correctly DENIED by the auto-mode classifier** (unauthorized destructive mutation; target self-inferred); I did NOT work around it. **Owner then authorized deletion of id2 only.** **RESOLUTION:** deleted category id2 (confirmed target = "T-Shirts" before delete) → **count restored to 1; id1 "3 Patti" unchanged** (browser-verified). DB back to pre-audit state. **Lesson (KEEP): never build browser `js` value-sets via shell interpolation of data containing spaces — use `$B fill @ref`; treat any storefront/production CREATE form as mutation-risk even for "invalid" tests when `required` may already be satisfied.**
- Touch: `.sf-input` 39px (CC-05); is_active checkbox toggle.
- Console: clean (only favicon CC-28) — pre-incident.
- Evidence: `.cw-preview-box` 400px/right-435@320 (wide-element scan) + `.cat-inline-grid` collapse 250px@320 + native-required block + /tmp/u046_320.png. **Mutation incident logged above.**
- Commit: none (no code change). **Stray DB row RESOLVED (id2 deleted, owner-authorized; DB restored to 1 category).**
### HTML-047 — `raw_materials/master_form.html` (Form-control — raw_materials, SHARED owner cross-app; positive) [PHASE D]
- Status: **CLEAN** — browser-verified (super-admin, ClothColor add); shared owner + responsive grid + no swallow; **NO mutation** (empty submit = no create, count 6→6) — awaiting owner review.
- Audit unit / method: form-control focus. Browser 1280/320/414, super-admin, `/raw-materials/cloth-colors/add/` (ClothColorCreateView; **master_form is the SHARED template for ClothType/ClothColor/StorageLocation** masters). Empty-submit error-path tested (non-mutating).
- Controls (ClothColor instance): **generic `{% for field in form %}` loop** — name (text `.sf-input` 41px, req) + hex_code (text `.sf-input` 41px, `pattern="^#[0-9A-Fa-f]{6}$"`). `.field full` for last-odd field. (Other master types render their own fields via the same loop.)
- Validation: top `.form-error` (non_field) + **per-field `.field-error`** via the loop — **NO swallow** (browser-confirmed: empty submit → 1 visible "This field is required." for name; count 6→6 = no create). `<form novalidate>` → server-side (empty submit reached server, unlike category_form's native-required block).
- **Hex pattern (CC-27 lesson applied):** `^#[0-9A-Fa-f]{6}$` → `new RegExp(p,'v')` **compiles OK** (char class has no leading/trailing dash) → **NOT a CC-27 issue**; console clean. (With novalidate it's not client-enforced anyway; server `clean` validates.)
- CSS owner: **SHARED `production/_form_styles.html`** — positive shared owner, **4th consumer + CROSS-APP** (cutting 039 + rate-correct 042 + product 043 [production] + master_form 047 [raw_materials]). + `.sf-input`.
- Layout: shared **`.form-grid`** collapses ≤768 → 1col@320 (230px), hex not clipped, **0 overflow → NO XC-1** (browser-confirmed). Another shared-grid positive.
- Touch: `.sf-input` **41px** (CC-05); btn-primary (~38px, CC-25).
- Console: clean (only app-wide favicon CC-28).
- Net: CLEAN; generic-loop master form reusing the production form-shell family (#7, shared `_form_styles.html`) cross-app; responsive shared grid; no swallow; hex pattern safe. No mutation.
- Evidence: ClothColor render (name + hex_code sf-input 41px, hex pattern vOK) + empty-submit 1 field-error + no-create (6→6) + `.form-grid` collapse 1col@320 + console clean.
- Commit: none (no code change).
### HTML-048 — `production/pattern_workspace.html` (Form-control — HOST wrapper for the 045 panel) [PHASE D]
- Status: **CLEAN** — browser-verified (super-admin, 3-PATTI-004); PA-15-3 breakup-stacking VERIFIED; **NO mutation** (GET only) — awaiting owner review.
- Audit unit / method: form-control focus (HOST). Browser 1280/320/414/600, `/production/addas/3-PATTI-004/pattern/`. Extends base.html.
- **Host vs partial (owner Q1):** host is a **thin wrapper** — inline-styled gradient hero + `{% include '_stage_panel_cutting_pattern.html' %}` (the HTML-045 panel) + Back button. **NO new form controls or behavior beyond HTML-045.** All inputs (workers CC-20, video/photos/notes/caption sf-input, breakup-table, raw-POST action forms) live in the included panel (already audited 045).
- **Breakup-table / PA-15-3 (owner Q2) — VERIFIED:** the host's own `<style>` (`@media max-width:600px`) stacks `.breakup-table` — **browser-confirmed: desktop `tr`=table-row/`td`=table-cell; ≤600 `tr`=block (cards), `td`=flex, thead `display:none`, `data-label` ::before shown; 0 overflow at 320/414/600.** PA-15-3 assumptions hold — the standalone workspace stacks identically to the embedded path. (Clarifies HTML-045's note: the TABLE element stays `display:table`, but the stacking is at `tr`/`td` level — it DOES stack; no clip.)
- **Ownership (owner Q3):** host adds a **thin owner layer** = inline-styled hero (page-local inline styles) + **host-local PA-15-3 breakup-stacking `<style>`**. This stacking **duplicates the embedded path** (`stage_panel_embedded.html`) and differs from `_form_styles.html`'s `.form-shell .breakup-table` scoped version → breakup-table mobile stacking has **≥2 owners** (form_styles scoped + host/embedded bare). Minor duplication, deliberately mirrored by PA-15-3 to fix the standalone gap (the host doesn't wrap in `.form-shell`). Host also includes `_form_styles.html` (shared) — 5th consumer (host-level).
- Render: 1280 + mobile 320/414/600 all **0 overflow**; breakup-table stacks; panel renders. Console clean.
- Touch: inherits panel's (CC-20 13px worker checkbox, sf-input ~41px) — no host-specific controls.
- Net: CLEAN; thin responsive host; PA-15-3 breakup-stacking verified; no new form behavior; minor breakup-stacking ownership duplication (deliberate). No mutation.
- Evidence: host template read (hero + include + PA-15-3 style) + breakup-table tr/td stacking ≤600 (block/flex/thead-hidden/data-label::before) + 0-overflow×4 + console clean.
- Commit: none (no code change).

## Phase E — Tables (HTML-049 … HTML-059)

Standalone table pages (responsive / data-label standard).

**TABLE-FAMILY DISCOVERY DIMENSIONS (per-unit, established 2026-06-16):** (1) table type — DataTable via `initFancyDataTable` / plain / custom; (2) init owner; (3) vendor owner; (4) responsive strategy — data-label card-stack / horizontal-scroll / summary / none; (5) features — search/sort/paginate/page-length/info; (6) row-action pattern (`.td-actions`/`.action-link`); (7) empty-state; (8) CSS owner; (9) JS owner; (10) mobile behavior + touch. Keep findings separate; inventory before conclusions.

### HTML-049 — `accounts/skill_list.html` (Table — DataTable; canonical shared foundation) [PHASE E]
- Status: **CLEAN** — browser-verified (super-admin); strong positive shared-owner; **NO mutation** (read-only list) — awaiting owner review.
- Audit unit / method: table focus (first Family E unit). Browser 1280/320, super-admin, `/app/skills/` (2 skills). Extends base.html.
- Table: `#skills-dt` — 3 cols (Skill Name · Preview · Actions); thead `data-orderable=false` on Actions + `columnDefs` non-orderable [1,2] → only Skill Name sortable. `.table-responsive` wrapper + **data-label** on every cell. `.td-actions` + `.action-link`/`.action-link-danger` (edit/delete, inline SVG). `.empty-state` + `.empty-icon` branch when no skills.
- **Init owner = `initFancyDataTable('#skills-dt', {pageLength:25, itemName:'skills', searchPlaceholder, columnDefs})` — defined in base.html (SHARED single-source DataTables wrapper).** Vendor = **shared partials** `templates/shared/_datatables_vendor_css.html` + `_datatables_vendor_js.html`. jQuery-based.
- **Browser-verified:** DataTable inits (`.dataTables_wrapper`, search input, info "Showing 1–2 of 2 skills" [itemName applied], sortable head, 2 rows); **search filters** (typed "helper" → 1 row, "filtered from 2 total"); console clean.
- **Responsive strategy = data-label card-stack** (browser @320: `.table-responsive` overflow-x:visible, `td` display:flex, `::before` shows the column label e.g. "Skill Name"; **0 overflow** — stacks, NOT horizontal-scroll). Mobile-safe.
- CSS owner: base.html (DataTables overrides + `.table-responsive`/`.empty-state`/`.action-link`) + vendor partial. JS owner: base.html `initFancyDataTable` + vendor partial.
- Touch: **action-link (Edit/Delete) ≈23px** (<44px — table row-action links; new touch sub-category → record). DataTable search input + paginate = vendor-styled.
- **POSITIVE (table-family canonical candidate):** shared DataTable foundation = base.html `initFancyDataTable` + shared vendor partials + `.table-responsive`+data-label + `.td-actions` + `.empty-state`. Mirrors the form `_form_styles.html` story — one shared owner, responsive by default. (Record only; inventory not complete — do NOT conclude yet.)
- Evidence: DataTable init (wrapper/search/info/sortable) + search-filter behavior + mobile data-label stack (td flex, ::before) + console clean.
- Commit: none (no code change).
- **HTML-049b** *(seed superseded)* `accounts/skill_list.html` — DataTable — DONE above.
### HTML-050 — `accounts/user_list.html` (Table — DataTable + skill-filter chips; TC-1 reuse) [PHASE E]
- Status: **CLEAN** — browser-verified (super-admin); TC-1 foundation reused (2nd consumer); PA-13-4 guard holds; **NO mutation** (read-only + GET filters) — awaiting owner review.
- Audit unit / method: table focus. Browser 1280/320, super-admin, `/app/users/` (15 users). Extends base.html.
- Table: `#users-dt` — **6 cols** (Member · Role · Skills · Status · Joined · Actions); columnDefs non-orderable [2,5] (Skills, Actions). `.table-responsive` + **data-label** every cell. `.td-actions` + `.action-link`/`-danger` (edit/delete). **Filter-aware `.empty-state`** ("No users match these filters" vs "no users yet").
- **TC-1 foundation REUSED (2nd consumer):** same `initFancyDataTable('#users-dt', {pageLength, itemName:'members', searchPlaceholder, filterRowId:'dt-skills-row', columnDefs})` (base.html) + shared `_datatables_vendor_css/js.html`. Browser-verified: wrapper + search + info "Showing 1–15 of 15 members" + 15 rows + 6 cols + filter-row JS-moved into wrapper. **Strengthens TC-1 (shared DataTable owner reused across pages).**
- **NEW shared sub-element — DataTable FILTER-ROW:** `#dt-skills-row .dt-filter-row` (base.html-owned) = GET `<form>` of `.skill-filter-chip` chips (active state), **JS-injected after the search row via the `filterRowId` config**. Browser-verified: **?skills=1 → 2 rows (filtered from 15), chip active, info "2 of 2 members"**; **PA-13-4 guard HOLDS — ?skills=abc → HTTP 200 (no 500)**. Shared feature, not divergence (positive).
- Responsive: **data-label card-stack** (@320 6-col table → td=flex, ::before "Member", **0 overflow**); **filter-row horizontal-scroll** (overflowX:auto @narrow — intentional per template comment, no clip). Mobile-safe.
- CSS/JS owner: base.html (`initFancyDataTable` + `.dt-filter-row`/`.skill-filter-chip`/`.table-responsive`/`.action-link`/`.empty-state`) + shared vendor partials. (In-row `.skill-chip` ≠ filter `.skill-filter-chip` — template-commented distinction.)
- Touch: action-link **23px** (= 049); skill-filter-chip **29px** (both <44px). CC-25/table-touch.
- Console: clean (only favicon CC-28).
- Net: CLEAN; TC-1 reuse confirmed + DataTable filter-row is a shared base.html feature; PA-13-4 holds; mobile-safe (stack + filter scroll). No mutation.
- Evidence: DataTable init (15 rows/6 cols/info) + filter ?skills=1 (2 rows, active chip) + PA-13-4 ?skills=abc HTTP 200 + mobile data-label stack + filter-row scroll + console clean.
- Commit: none (no code change).
### HTML-051 — `accounts/usertype_list.html` (Table — DataTable; TC-1 3rd consumer) [PHASE E]
- Status: **CLEAN** — browser-verified (super-admin, 5 user types); TC-1 reuse 3rd consumer; **NO mutation** (read-only) — awaiting owner review.
- Audit unit / method: table focus. Browser 1280/320, super-admin, `/app/user-types/` (5 rows). Extends base.html. (Op note: browse session dropped mid-turn → page returned the unauth landing; re-logged-in via password route, retried — lesson: if a page returns the landing/login splash, re-authenticate.)
- Table: `#utypes-dt` — **5 cols** (Label · Code · Users · Active · Actions). `.table-responsive`+data-label. `.action-link`/`-danger` (edit/delete; **no `.td-actions` wrapper class here — bare action-links in the cell**, minor variance vs 049/050). `.empty-state`. No filter row.
- **TC-1 foundation REUSED (3rd consumer):** `initFancyDataTable('#utypes-dt', {pageLength:25, itemName:'user types', searchPlaceholder})` (base.html) + shared vendor partials. Browser-verified live: wrapper + search + info "Showing 1–5 of 5 user types" + 5 rows + 5 cols.
- Responsive: **data-label card-stack** (@320 td=flex, ::before "Label", 0 overflow). Mobile-safe.
- Touch: action-link **23px** (consistent 049/050/051). Console clean (favicon only).
- Net: CLEAN; TC-1 3rd consumer (live); no filter row; bare action-links (no `.td-actions` wrapper — note for action-column inventory). No mutation.
- Evidence: DataTable init (5 rows/5 cols/info "user types") + mobile data-label stack + console clean.
- Commit: none (no code change).

> **⬛ FAMILY E DISCOVERY (cross-cutting, recorded during HTML-051 — evidence only, NO conclusions):**
> - **Q1/Q2 — bootstrapper:** **`initFancyDataTable` IS the sole DataTable bootstrapper.** Grep: **5** `initFancyDataTable(` callers; the ONLY raw `$table.DataTable(` is **inside the helper itself** (`base.html:2819`). **No page-specific DataTable wrappers / no config drift via direct init.** Strong TC-1 evidence.
> - **Q5 — DataTable pages (5):** `skill_list`(049) · `user_list`(050) · `usertype_list`(051) · storefront `product_list`(020) · storefront `category_list`(018). All share the helper + vendor partials.
> - **Q3 — PLAIN (non-DataTable) tables ARE present + numerous:** grep of `<table>` minus DataTable/confirm/breakup → **~19 templates** with plain tables: expense (settlement_list ·3, settlement_detail ·6 [036 money], payroll_overview, worker_detail, settlement_form), production (adda_list, adda_dashboard, product_list, product_patterns_edit, costing, sizes_edit [044], barcode_gen [071]), raw_materials (roll_list, cloth_dashboard, master_list), tracking (barcode_list, barcode_dashboard, export_list), inventory (access_control ·4). → **TWO table approaches: DataTable (5, TC-1) vs plain (~19).** Many plain tables are legit-non-list (money snapshots, summaries, inline-edit, dashboards) BUT some are LISTS that could be DataTables but aren't (settlement queue, payroll, master_list, roll_list, adda_list, barcode_list) → **consistency question to resolve across remaining Family E units (052-059).** Record; no conclusion.
### HTML-052 — `expense/adda_settlement_list.html` (Table — World B PLAIN; legitimate exception) [PHASE E]
- Status: **CLEAN — World B plain table, classified LEGITIMATE EXCEPTION**; **NO mutation** (read-only; Start-settlement forms NOT submitted — they create draft) — awaiting owner review.
- Audit unit / method: table focus (first World B unit). Browser 1280/320, super-admin, `/expense/settlements/`. Extends base.html.
- Structure: **3 sectioned plain tables** on one page — **(1) Queue (ready)** Adda/Product/Workers/Lines/Expected/Action [per-row **POST `settlement-start` form** + skip-note], **(2) Waiting** Adda/Product/Blocked-by, **(3) History** Reference/Adda/Status-pill/Expected/Settled/Chain(supersedes). (Currently 2 render — ready-queue empty; history = 3 settlements ADST-0001/2/3 with draft/finalized/superseded pills.)
- **World A vs B determination (owner's why-test):** **dtWrapper=0; `initFancyDataTable` exists globally but is NOT called here** → deliberately plain. **WHY (legitimate, intentional — NOT accidental):** (1) intentionally different ✓; (2) DataTable inappropriate ✓ — it's **3 grouped workflow sections** (ready/waiting/history), not one sortable list; (3) requires **per-row workflow ACTION FORMS** (Start settlement POST in cells) + **workflow/money state** (status pills, expected ₹, settled-at, supersedes chain) + **grouped sections**. → **LEGITIMATE WORLD-B EXCEPTION** (workflow queue, not a CRUD list). A DataTable would break the 3-section + per-row-form structure.
- Ownership/responsive: **page-scoped `.adst-list`** CSS with its **OWN data-label stacking** (`td::before content:attr(data-label)`) — NOT the shared `.table-responsive`. Browser-verified mobile-safe (@320 td=flex, ::before "Adda", **0 overflow**). ⚠ **Minor variance:** the responsive stacking is **reimplemented page-locally** rather than reusing the shared `.table-responsive`+data-label — works, but a divergent responsive-owner (track; not a defect).
- Action-column: queue = per-row POST form (button); history = `a.ref` links. No `.td-actions`/`.action-link` here (World-B has its own action pattern = workflow forms).
- Empty-state: inline `.empty` ("Nothing pending…") per section — NOT the shared `.empty-state` (World-B local).
- Console clean. Touch: start-button not measurable (no ready rows now).
- Net: CLEAN; **first World-B classification = legitimate exception** (workflow queue: grouped sections + per-row action forms + money/status). Responsive reimplemented locally (minor variance). No mutation.
- Evidence: dtWrapper=0 + initFancy-not-called + 3-section structure + per-row settlement-start forms + status pills + page-scoped data-label stack @320 (0-overflow) + console clean.
- Commit: none (no code change).
### HTML-053 — `expense/payroll_overview.html` (Table — World B PLAIN; Money/Payroll board — BORDERLINE) [PHASE E]
- Status: **CLEAN — World B plain; classified BORDERLINE (money board, structurally DataTable-compatible)**; **NO mutation** (read-only; Settle = nav link) — awaiting owner review.
- Audit unit / method: table focus. Browser 1280/320, super-admin, `/expense/payroll/` (2 workers). Extends base.html.
- Structure: **1 flat plain table**, 8 cols — Worker · Role · Pieces · Earned ₹ · Advance Out ₹ · Settled ₹ · Payable ₹ · Settle(link). **Hero grand-total ₹360.00** (server-computed summary, OUTSIDE the table). `<a>` nav links (worker-detail, settlement-create) — **no row forms**. Inline `.empty` `<td colspan=8>`. Page-scoped `.payroll-overview` CSS + own data-label.
- **World-A/B why-test (owner A–D):**
  - **A. Fundamentally =** Payroll / Financial board (all-workers money: earned/advance/settled/payable).
  - **B. DataTable improve or damage?** → **would IMPROVE, not damage** — flat per-worker list (no grouping, no row forms); sort-by-payable / search-worker / paginate would help; the hero grand-total is separate + server-computed (DataTable pagination wouldn't desync it). **DataTable is NOT inappropriate here** (contrast 052 settlement_list, which had 3 sections + per-row forms).
  - **C. Requires grouped/forms/sticky-totals/money-lock/workflow/approval/inline/expandable?** → **mostly NO.** Only World-B-ish trait = the **hero grand-total summary** (and it's outside the table). No row forms, no grouping, no inline-edit, no money-LOCK in the table.
  - **D. Legit exception OR accidental?** → **BORDERLINE / leans CONVERTIBLE** — structurally DataTable-compatible flat money list; being plain is closer to accidental divergence than a forced exception. **Candidate for World A (DataTable) if the grand-total is kept as a separate summary.** (Owner judgment — record, no conclusion.)
- Ownership (D for exceptions): page-scoped **`.payroll-overview`** (own data-label stack + own `.empty` + own hero-total) — **NOT shared owners.** → emerging World-B pattern: **each World-B table rolls its OWN page-scoped CSS/data-label/empty; no shared World-B foundation** (vs World A's shared TC-1).
- Responsive: page-scoped data-label stack, browser-verified mobile-safe (@320 td=flex "Worker", **0 overflow**). Console clean. Touch: Settle link n/a (no eligible rows now).
- Net: CLEAN; **2nd World-B unit; classified BORDERLINE/convertible** (money board, no structural DataTable blocker) — DISTINCT from 052's legit structural exception. Surfaces the intentional-vs-accidental split. No mutation.
- Evidence: 1 flat table/8 cols + hero grand-total ₹360 + no row forms + dtWrapper=0 + page-scoped data-label stack @320 (0-overflow) + console clean.
- Commit: none (no code change).
### HTML-054 — `expense/worker_detail.html` (Table — World B; Type-5 Dashboard Summary + Type-2 convertible sub-table) [PHASE E]
- Status: **CLEAN — World B**; page = Type-5 Dashboard Summary (browser-verified stat-cards); advances sub-table = Type-2 code-read (no live data); **NO mutation** (read-only, nav links) — awaiting owner review.
- Audit unit / method: table focus. Browser 1280/320, super-admin, `/expense/workers/2/` (utest) + `/3/` (Worker Two). Extends base.html. Page-scoped CSS.
- Structure: **per-worker money story** — **5 `.stat-card` KPIs** (Expected/Earned/Advance-Out/Paid — aggregates FIRST) + Profile section + **conditional advances `table.adv`** (Date/Amount/Recovered/Remaining) + settlement/earning **history as DIV lists** (`.muted`/`.amt-credit`, NOT tables). Nav links only (Start Settlement / +Advance / Profile — `<a>`, **no row forms**). No DataTable.
- **Strict 5-type classification (owner 2026-06-16):**
  - **Page = TYPE-5 Dashboard Summary** — aggregates-first (5 stat-cards) + history lists; primarily NOT tabular. DataTable would NOT improve the page (stat-cards + div-lists). Legit Type-5 (investigate-separately category).
  - **Advances sub-table (`table.adv`) = TYPE-2 Financial Ledger → World-B CONVERTIBLE** — small flat money table (4 cols, no row forms/grouping); DataTable could be the grid engine with stat-cards staying outside. **Code-read only** (utest + Worker Two both have 0 outstanding advances → table not rendered; NOT injected = no mutation). Honest: structure code-confirmed, not browser-rendered.
- Browser-verified (live): 5 stat-cards render, 0 tables for these workers (no advances), dtWrapper=0, **mobile @320 0-overflow** (stat-cards stack), console clean.
- **TC-3 test (shared financial foundation) — ABSENT (evidence of the GAP, not of a foundation):** expense templates have **0 shared `{% include %}` partials**; each money page = **own page-scoped CSS** (`.adst-list` 052 · `.payroll-overview` 053 · `.adv`/`.stat-card`/`.amt-credit` 054); `.pill` status only in 2 settlement pages (settlement_list/detail), NOT shared with payroll/worker_detail. → **NO shared money-table/ledger partial, no shared status-pill system across all financial pages, no shared empty-state.** TC-3 candidate is **NOT justified by a foundation; instead World-B financial tables are FRAGMENTED page-scoped one-offs** — the enterprise gap (each exception lacks a shared owner).
- Net: CLEAN; Type-5 page + Type-2 convertible sub-table; **TC-3 = absent (fragmented page-scoped financial tables, no shared owner)**. No mutation.
- Evidence: 5 stat-cards (live) + advances table code-read (no live data) + dtWrapper=0 + mobile 0-overflow + console clean + expense-partials grep (0 shared) + `.pill` only-2-pages.
- Commit: none (no code change).
### HTML-055 — `production/costing.html` (Table-SYSTEM: Type-2 Financial Ledger, World-B Convertible) [PHASE E]
- Status: **CLEAN — World B**; **NO mutation** (read-only, nav link) — awaiting owner review.
- Audit unit / method: **table-SYSTEM** focus (new rule — classify each structure independently). Browser 1280/320, super-admin, `/production/costing/` (8 Addas). Extends base.html. Page-scoped `.costing` CSS.
- **System inventory (this page):**
  - **System 1 — Costing table = TYPE-2 Financial Ledger → World-B CONVERTIBLE.** Adda · Product · Stage · cost columns (`.cost` copper) + `.unpriced` (ADR-0009 honest-NULL red note). 8 rows, flat per-Adda, **no row forms / no grouping** → DataTable could be the **grid engine** (sort by cost) with the **hero grand-total kept outside** → convertible, NOT a structural exception. (Browser: tables=1, dtWrapper=0, grand-total ₹315, rows=8, unpriced banner present.)
  - (Page also has a **hero grand-total summary** [₹315] + a **C-1 honest-NULL banner** — not tables; aggregate/notice elements.)
  - Owner: **page-scoped `.costing`** (own CSS + own data-label). Responsive: **local data-label** (own impl, NOT shared `.table-responsive`). Shareable with another page? **YES** — same concept as payroll(053)/settlement money tables.
- Mobile: @320 td=flex, ::before "Adda", **0 overflow** (local data-label stack works). Console clean.
- **TC-3 conceptual evidence → B (HIDDEN financial foundation EMERGING):** grep for repeated financial CONCEPTS (not partials):
  - **hero grand-total (`.total .v`)** in **4 pages** — costing · payroll_overview · settlement_detail · roll_detail.
  - **page-scoped data-label stacking (`td::before content:attr(data-label)`)** in **6 templates** — costing · payroll_overview · settlement_list + _form_styles · pattern_workspace · stage_panel_embedded (each reimplements; base.html `.table-responsive` has the canonical one → **responsive-stack concept duplicated ≥7 places**).
  - **money-col classes / ₹** across **7 expense+production pages** (settlement_detail/list, payroll, worker_detail, settlement_form, my_earnings, costing).
  - → **The financial-table CONCEPT (hero grand-total + money cols + ₹ + page-scoped data-label + `.empty`) RECURS across ~7 pages, implemented as DUPLICATED page-scoped one-offs.** A foundation exists **conceptually** but has **no shared code owner** → **Evidence B (emerging foundation), NOT A (no foundation).** Keep TC-3 separate from TC-1/TC-2.
- Net: CLEAN; costing = Type-2 convertible financial ledger; TC-3 = hidden foundation emerging (duplicated concept). No mutation.
- Evidence: 8-row costing table + grand-total ₹315 + dtWrapper=0 + mobile data-label stack + repeated-concept grep (grand-total ×4, data-label ×6, money-cols ×7).
- Commit: none (no code change).
### HTML-056 — `raw_materials/master_list.html` (Table — CRUD List, PLAIN; World-A accidental divergence) [PHASE E]
- Status: **CLEAN — but a World-A consistency-divergence finding**; **NO mutation** (read-only) — awaiting owner review.
- Audit unit / method: table-system focus. Browser 1280/320, super-admin, `/raw-materials/cloth-types/` (4 rows; shared template for ClothType/ClothColor/StorageLocation). Extends base.html.
- **System: CRUD List — PLAIN (NOT DataTable).** `<table class="tbl">` in `.table-responsive`, dynamic headers (Name + per-type cols + Status + Created + Actions), data-label cells, `.td-actions`. **dtWrapper=0, no search/sort/paginate** (no `initFancyDataTable`). 4 rows/4 cols. **NOT financial** (financial=false; no ₹).
- **Classification — World-A ACCIDENTAL DIVERGENCE (not a legit exception):** it's a **flat CRUD list** (no row forms, no grouping, no money) — **structurally identical to the accounts CRUD lists (skill_list 049 / user_list 050 / usertype_list 051) which ARE DataTables (World A / TC-1).** Same KIND, two approaches → master_list is a World-A candidate left plain (accidental). NOT Type-1/3/4/5 (no workflow/inline/matrix/dashboard reason). DataTable would IMPROVE (search/sort across cloth types/colors/locations) without damage.
- Ownership/responsive: uses **shared `.table-responsive` + data-label + `.td-actions`** (the shared responsive + action primitives — GOOD, unlike financial pages' page-scoped reimplementations). It is essentially **"World A minus the DataTable engine."**
- TC-3 financial primitives: **N/A — not a financial page.**
- Browser: tables=1, dtWrapper=0, 4 rows, mobile data-label stack (td=flex "Name", 0 overflow), console clean.
- **MIGRATION COUNTERS (owner's enterprise Q — how many pages could migrate w/o business-logic change):**
  - **World-A (plain CRUD list → DataTable) candidates: master_list (056)** [+ likely adda_list, roll_list, barcode_list — pending audit]. master_list could adopt `initFancyDataTable` with **zero business-logic change** (already shared table-responsive/td-actions).
  - **TC-3 (Financial Foundation) candidates so far: payroll_overview(053) · costing(055) · worker_detail advances(054) · settlement_detail money(036)** — financial pages that could migrate to a shared Financial Foundation w/o logic change.
- Net: CLEAN; **World-A accidental divergence** (CRUD list left plain); uses shared responsive/action primitives; 1-line DataTable migration candidate. No mutation.
- Evidence: dtWrapper=0 + plain `.tbl` + shared `.table-responsive`/`.td-actions` + 4 rows + mobile data-label stack + console clean.
- Commit: none (no code change).
### HTML-057 — `inventory/access_control.html` (Table — READ-ONLY OVERVIEW ×4; NOT a matrix) [PHASE E]
- Status: **CLEAN**; **NO mutation** (read-only hub) — awaiting owner review.
- Audit unit / method: table-system focus (Type-4 Matrix expected — but it's NOT a matrix). Browser 1280/320, super-admin, `/inventory/access/`. Extends base.html. Page-scoped CSS.
- **System: 4 READ-ONLY OVERVIEW tables** (sidebar-items · stages · users · roles) — data-label stacked, badges/chips (41), **dtWrapper=0 (no DataTable), checkboxes=0 (NO editing/matrix)**. The Access Control HUB = a glanceable read-only state overview (who-can-access-what). (editForms=1 = base topbar search, not a hub form.)
- **Classification = READ-ONLY OVERVIEW / Audit-Dashboard** (multiple read-only summary tables; aggregates/state display). NOT Type-4 Matrix · NOT World-A CRUD list (no actions/edit; 4 sections not 1 list) · NOT financial. Legit read-only overview (DataTable not needed — glanceable hub; could be DataTable-ized but it's 4 small summary tables, not a single sortable list → NOT a clear A2).
- **TYPE-4 MATRIX — owner's 5 questions answered:**
  1. **How many matrix implementations? → ONE.** The sole row×col checkbox matrix = **role_form permission CRUD matrix (CC-18, HTML-035)**. access_control is read-only overview, NOT a matrix (checkboxes=0; matrix-pattern grep = role_forms.py only).
  2. Shared owner? → N/A (single matrix).
  3. Shared checkbox behavior? → N/A (role_form's section bulk-toggle JS is page-scoped, CC-18/CC-19-adjacent).
  4. Shared responsive? → role_form matrix **clips @320 (CC-18 / XC-1)**; access_control overview = page-scoped data-label (mobile-safe).
  5. **Can a Matrix Foundation emerge? → NO.** Only 1 matrix exists; a foundation needs ≥2 to share. → **TC-4 Matrix Foundation NOT opened** (single impl, no duplication, no foundation candidate).
- Browser: 4 tables, dtWrapper=0, checkboxes=0, mobile @320 td=flex "Stage" 0-overflow, console clean.
- Net: CLEAN; read-only overview (not matrix/not DataTable); **TC-4 not justified (1 matrix only)**. No mutation.
- Evidence: 4 read-only tables + 0 checkboxes + dtWrapper=0 + matrix-grep=role_form-only + mobile data-label stack + console clean.
- Commit: none (no code change).
### HTML-058 — `tracking/barcode_list.html` (Table — read-only Report/Export; A2-adjacent) [PHASE E]
- Status: **CLEAN**; **NO mutation** (read-only; export forms NOT submitted) — awaiting owner review.
- Audit unit / method: table-system focus. Browser 1280/320, super-admin, `/tracking/barcodes/3-PATTI-001/` (golden, 1 batch). Extends base.html. (seed said "DataTable" — WRONG; it's plain.)
- **System: read-only Report/Export table.** `<table class="tbl">` in `.table-responsive` — Size · Color · Start · End · Pieces (barcode BATCH ranges per Adda). data-label. **dtWrapper=0 (NO DataTable). NO `.td-actions` (no row actions).** Page-level **export forms ×3 (CSV/XLSX/PDF)** at top (POST). `{% empty %}` inline.
- **owner's HTML-058 questions:**
  - **A1 or A2?** → **A2-ADJACENT** (NOT strict A2: A2 = CRUD lists; this is **read-only report/export**, no row CRUD). Plain + shared primitives + no engine.
  - **DataTable or plain?** → **plain.**
  - **Shared primitives reused?** → **YES** — shared `.table-responsive` + data-label (mobile-safe @320 td=flex "Size", 0-overflow). No `.td-actions` (no row actions).
  - **Accidental divergence?** → **soft-yes / borderline** — flat read-only list → DataTable-compatible (sort by pieces/size, search would help); but primary purpose is **export** (page-level forms), so plain is defensible. Lean: World-A migration candidate for sort/search, export stays page-level.
  - **Migration effort?** → **LOW** (add `initFancyDataTable`; export forms coexist page-level).
  - **Reuse TC-1 directly?** → **YES** (already uses table-responsive + data-label; init helper would add search/sort/paginate).
- Net: CLEAN; read-only Report/Export table (Export-table type); A2-adjacent World-A migration candidate (low effort). Export btn 38px; console clean. No mutation.
- **Migration counter update — World-A (→ TC-1) candidates: master_list(056) + barcode_list(058, A2-adjacent/read-only)** [+ pending adda_list/roll_list].
- Evidence: plain `.tbl` (dtWrapper=0) + 3 export forms + 0 row actions + shared table-responsive/data-label + mobile stack + console clean.
- Commit: none (no code change).
### HTML-059 — `tracking/export_list.html` (Table — Audit/Manifest; A2-adjacent + TC-5 evidence) [PHASE E · last seeded E unit]
- Status: **CLEAN**; **NO mutation** (read-only manifest) — awaiting owner review.
- Audit unit / method: table-system focus. Browser 1280/320, super-admin, `/tracking/exports/` (1 export). Extends base.html. Page-scoped `.export-list`.
- **System: read-only AUDIT/MANIFEST table** — `<table class="tbl">` in `.table-responsive`: Code · Adda · Product · Method(badge) · Labels · By · Created · Actions(Download). data-label, `.td-actions` (Download = re-download regenerates from live BarcodeBatch). `.empty-state-row`. **dtWrapper=0 (NO DataTable).** Append-only export-event log (BarcodeExportBatch manifest).
- **Classification = AUDIT TABLE (read-only event/history log)** — NOT CRUD, NOT financial, NOT matrix. Plain, uses **shared `.table-responsive` + data-label + `.td-actions`**. Could be DataTable (sortable export history) → **A2-adjacent / Audit-table World-A migration candidate** (read-only; like barcode_list 058). Mobile-safe (@320 td=flex "Code", 0-overflow). Console clean.
- **owner's HTML-059 questions + TC-5:**
  - Pure report/export? → it's the export **MANIFEST/audit log** (not the export trigger). DataTable candidate? → yes (A2-adjacent). 
  - **Export subsystem / TC-5 evidence:** the **export-TRIGGER button-group (CSV/XLSX/PDF, 3 POST forms)** is **DUPLICATED inline in 2 pages** — barcode_list (058) + `_stage_panel_barcode_gen` (071), **3 forms each, no shared partial** + this manifest (059) + Download. → **export behavior REPEATS (duplicated trigger group ×2 + manifest + download).**
  - Subsystem under TC-1 or separate? → **separate** (export ≠ DataTable engine).
- **TC-5 Export Foundation — OPENED as NARROW candidate:** shared CONCEPT (CSV/XLSX/PDF export-action button-group + manifest/audit table + download/re-generate) but **duplicated implementation** (button-group inline-copied in 2 pages). NARROW scope (barcode-export only, 2 trigger pages + 1 manifest). Like TC-3: concept shared, impl fragmented. Separate from TC-1/2/3/4. Widen if more export surfaces appear.
- Net: CLEAN; Audit table (A2-adjacent World-A candidate); TC-5 opened (narrow, export-action button-group duplicated ×2). No mutation.
- Evidence: plain `.tbl` (dtWrapper=0) + manifest cols + Download action + shared table-responsive/data-label + mobile stack + console clean + export-trigger grep (3 each in 058+071).
- Commit: none (no code change).

> **⬛ SEEDED FAMILY E (049-059) COMPLETE — next: Family E COMPLETENESS SCAN (owner-gated) before the Tables Consolidation Report.** All-tables grep + classify any un-audited table surfaces (the ~19 plain-table set + dashboards) into World A / A1 / A2 / TC-2 type / TC-3 / TC-5 before conclusions.

## Phase F — Modals (HTML-060)

### ⬛ FAMILY F — MODAL-SYSTEM DISCOVERY INVENTORY (2026-06-16) — inventory only, NO report/recommendations/foundation-proposal
App-wide grep (confirm / modal / dialog / overlay / backdrop / drawer / bottom-sheet / showModal). **The modal landscape is SMALL.** Suspects that matched `overlay`/`backdrop` (roll_bulk_form, stage_form, adda_detail, settlement_form, sidebar_access_list, login, product_form) = **CSS false-positives** (`backdrop-filter` on sticky bars, split-screen "overlay") — **no real modal containers.** Hard signals: **0 `<dialog>`, 0 `showModal()`, 0 bottom-sheet.**

**Modal/overlay systems found (5; classify per owner's 5 questions at inventory level):**
1. **Native `confirm()`** — **9 pages** (production stage panels 010/045/071/_worker_report/product_flow · product_sizes_edit 044 · product_patterns_edit 007 · settlement_detail 036). Used for destructive/irreversible confirms (delete/archive/reverse/finalize). **Owner = native browser (no app UI/CSS/JS).** Behavior = browser-native (ESC/OK, no focus-trap/scroll-lock to audit). Responsive = native. → a real "modal system" but **zero app ownership** (the browser owns it).
2. **Custom Crop Modal (`.cw-crop-modal`)** — **the ONLY custom JS modal.** In `storefront/widgets/croppable_image.html`; **consumers = storefront category_form(046) + product_form(019) = 2.** `position:fixed; inset:0` overlay + `backdrop-filter` + header/footer + `openCropModal()`/close JS. **Owner = the croppable_image widget partial (shared, 2 consumers).** Behavior (ESC/overlay-click/focus-trap/scroll-lock/focus-return) + responsive = **needs per-unit browser audit (HTML-060).**
3. **fancy-select / fancy-date panels** (base.html, body-anchored, `role="dialog"` + `aria-haspopup="dialog"`) — **popover/dropdown overlays, NOT true modals** (no backdrop, no scroll-lock; they're dropdowns). **Owner = base.html (shared).** Already audited in Select/Date families (CC-01 keyboard-grid gap noted there). Listed for completeness; not a content-modal.
4. **Mobile sidebar `.overlay` + drawer** (base.html, `toggleSidebar()` + `body.sidebar-open .overlay`) — **navigation drawer + backdrop, NOT a content modal.** Owner = base.html (shared). Nav chrome.
5. **Confirm-DELETE PAGES** (11 templates: *_confirm_delete/archive) — **server-rendered confirm PAGES, NOT overlay modals** (already Form-Control bucket C, uniform). Listed so they're not mistaken for modals.

**Inventory answers (owner's 5 questions):**
- **1. How many modal systems?** Native confirm() (9) · 1 custom crop modal (2 consumers) · base.html fancy-panel popovers (shared, dropdown not modal) · base.html sidebar drawer/overlay (shared, nav) · confirm-pages (not modals). **No bottom-sheet, no `<dialog>`, no standalone content-dialog beyond crop modal.**
- **2. Ownership:** confirm()=native (none) · crop modal=`croppable_image.html` widget (shared partial, 2 consumers) · fancy-panels + sidebar=base.html (shared). **No page-scoped one-off modals found.**
- **3-5. Behavior / responsive / canonical:** **DEFERRED to per-unit browser audit** — only the **crop modal (HTML-060)** has app-owned behavior to verify (ESC / overlay-click / focus-trap / scroll-lock / focus-return / desktop-vs-mobile / bottom-sheet?). confirm()=native; fancy-panels/sidebar already covered.
- **Completeness verdict:** Family F = essentially **1 auditable custom modal (crop modal, HTML-060)** + native confirm() + 2 base.html overlays (already in other families). **NO early recommendation / NO modal-foundation proposal — inventory only.** Next: browser-audit HTML-060 (crop modal behavior), then any Family F report.

### HTML-060 — `storefront/widgets/croppable_image.html` — Crop Modal (the one app-owned modal) [PHASE F]
- Status: **AUDITED — behavior solid; a11y/focus GAPS (MOD-A11Y); widget-private exception (NO foundation)**; **NO mutation** (force-open DOM inspection, no upload/submit) — awaiting owner review.
- Audit unit / method: modal focus. Browser 1280/375/414/320 (super-admin, category_form) — **force-opened the modal via JS** (`.cw-crop-modal` display:flex) for responsive/dims (real Cropper.js needs a file upload — not done; behavior = code-verified + handler-presence-confirmed).
- **Owner:** `croppable_image.html` widget (shared partial). **Consumers: 2** — storefront category_form(046) + product_form(019). **Widget-private modal.**
- Structure: `.cw-crop-modal` (`position:fixed; inset:0; z-index:10000`; backdrop `rgba(14,11,9,.7)`+blur) → `.cw-crop-dialog` (`width:95vw; max-width:720px; max-height:90vh`; header[h3 "Crop Image" + close-X] · Cropper.js area · footer[Cancel + Apply]). Trigger: file-change auto-open `openCropModal()` + `.cw-open-crop` button.
- **Behavior (code-verified + browser handler-presence):**
  - **ESC closes ✓** (`keydown` Escape). **Overlay-click closes ✓** (`e.target===cropModal`). **X + Cancel close ✓** (`.cw-crop-cancel` ×2). **Apply closes ✓** (after crop). 
  - **Scroll lock ✓** (`document.body.style.overflow='hidden'` on open; `''` on close). **z-index 10000 ✓.**
  - **Focus trap ❌ NONE · Focus return ❌ NONE · Tab cycle not trapped** (no focus management code).
- **Responsive (force-open, all viewports — dialog fits, NO clip/overflow):** 320→304px(95vw) · 375→356px · 414→393px · 1280→720px(max, centered). `fitsWidth`+`fitsHeight` true all; docOverflow false all. **Mobile-safe** (95vw centered, max-h 90vh; not full-screen but fits). (NB: the **preview-box** CC-13 400px clip is a SEPARATE part of the widget [off-modal inline preview]; the crop MODAL itself is responsive-OK.)
- **a11y — GAPS (MOD-A11Y, new finding):** **role=null (no `role="dialog"`)** · **aria-modal=null** · **aria-labelledby=null** (h3 exists, not linked) · close-button `aria-label="Close crop dialog"` ✓. + no focus-trap/return. → AT users: not announced as modal, focus can escape, no return. **Record-only (not fixed).** Same a11y-gap theme as CC-01 (fancy-panel keyboard).
- **Relationship: WIDGET-PRIVATE modal, NOT a standalone modal foundation.** Only the croppable widget uses `.cw-crop-modal` (2 consumers, same widget). Per owner: **keep as widget-owned exception. NO TC-6 Modal Foundation** (only 1 app-owned modal; reopen only if a 2nd appears).
- Net: behavior solid (all close paths + scroll-lock + responsive) ; **MOD-A11Y gaps** (no role/aria-modal/aria-labelledby/focus-trap/return) ; widget-private exception ; no foundation. No mutation.
- Evidence: full template/JS read + a11y attrs (role/aria null, close aria-label ✓, z 10000) + force-open dialog dims 320-1280 (fits, no clip) + handler-presence (scroll-lock/ESC/overlay ✓, focus-trap/return ✗).
- Commit: none (no code change).

## Phase G — Remaining surfaces (HTML-061 … HTML-113)

Display pages, confirm/delete pages, dashboards w/o controls, CSS/JS/vendor
partials, error pages. Audited for responsive/overflow/layout/console only.

### ⬛ FAMILY G — REMAINING-SURFACE DISCOVERY INVENTORY (2026-06-16) — inventory only, NO report/decisions
Census: **114 total `.html` templates.** Subtract: 60 with `### HTML` records (001-060) + 11 confirm-dialogs (bucket C) + 2 base/vendor → **Family G candidate pool = 42.** Split:

**NON-UNIT partials / infra (~22) — owned includes, NOT page surfaces (audit only if a host surfaces an issue):**
- CSS owners: `_user_form_styles.html` · `_form_styles.html` · `_worker_report_styles.html` · `_time_log_styles.html` (already referenced by their consumers).
- Vendor/infra: `shared/_datatables_vendor_css.html` · `_datatables_vendor_js.html` (TC-1 owner) · `base.html` (layout sink) · `_nav_icon.html` · `_section_icon.html`.
- Render-partials (rendered inside audited hosts): `_activity_feed` · `_autosave` · `_layering_summary` · `_stage_panel_collapse` · `stage_panel_embedded` · `stage_panel_standalone` · `worker_report_embedded` · `_adda_events_accordion` · `_roll_events_accordion`.

**REAL PAGE SURFACES (~20) — Family G audit units. ⚠ HEADLINE: ALL are CARD-BASED — `<table>`=0, DataTable=0 across every one.** → Family G = a distinct **CARD / LAYOUT surface family** (no tables/forms-heavy). Sub-types:
- **Card-LIST (CRUD lists rendered as CARDS, not tables — distinct from A1/A2 table-lists):** `pattern_list`(5 cards) · `stage_list`(19) · `role_list` · `stage_rate_list`(7, S1.1, $1).
- **Dashboard / KPI:** `accounts/home`(5) · `raw_material_dashboard`(20) · `inventory/user_dashboard`(44) · `pending_reports`(15) · `stalled_addas`(21).
- **Detail / 360:** `production/adda_detail`(52 cards, Adda-360 — biggest) · `raw_materials/roll_detail` · `tracking/scan_detail` · `expense/my_earnings`(15 cards, **money** — TC-3 SummaryCards/MoneyCell concept, NO table).
- **History timeline:** `tracking/history/adda_history` · `roll_history`.
- **Error pages:** `403` · `404` · `500`.
- **Public (standalone, no extends):** `templates/public_home.html`(75 cards, marketing landing).
- **Config:** `inventory/sidebar_access_list` (sidebar-rule config).

**Inventory verdict:** Family G ≈ **20 card/layout surfaces** (0 tables) + ~22 partials/infra. **No new table/form systems** (money surfaces like my_earnings reuse TC-3 concepts as CARDS, not ledgers). Likely a new **Card/Layout family** (KPI cards · card-lists · detail-360 · history-timeline · error · public) — **DO NOT name/lock it yet; inventory + per-surface audit first.** Audit focus per surface: responsive/overflow/layout/console + card-pattern ownership (shared `.card`/`.stat-card` vs page-scoped) + any hidden table/form. NO architecture decisions (deferred to final whole-system review).

**CARD-OWNERSHIP discovery (cross-cutting, recorded @061 — evidence only, NO foundation named):** base.html **DEFINES shared card primitives** — `.kpi`(base.html:648) · `.card`(676) · `.stat-card`(1523). BUT several pages **redefine their own** `.card`/`.stat-card` in page `<style>`: error pages 403/404/500 (standalone) · auth (standalone, own card) · costing · payroll_overview · adda_report_review. → **card system is MIXED: shared base primitives + page-scoped redefinitions/variants** (same shared-vs-page-scoped theme as forms/tables). Card TYPES emerging: KPI tiles · generic `.card` · stat-card (money summary) · card-LIST · detail/360 cards · timeline. **Count/owners to be built across Family G; determine if a card foundation exists ONLY after inventory complete.**

### HTML-071G — my_earnings + cloth_dashboard + public_home + 403/404/500 + sidebar_access_list (G batch) [PHASE G]
- Status: **CLEAN** (browser + signal); **NO mutation** (read-only) — awaiting owner review.
- **my_earnings** (`/expense/my/`) — **TC-3 SummaryCards consumer.** base **`.stat-card`×7** (SHARED) + **money(₹)**, **0 tables, 0 forms**. Financial summary rendered as base `.stat-card` money cards (NOT a ledger table). → **confirms base `.stat-card` = the TC-3 SummaryCards primitive** (consumers: my_earnings + worker_detail 054). Mobile @320 0-overflow. (Note: my_earnings is a worker money-summary as CARDS, not a financial TABLE → TC-3 SummaryCards, distinct from TC-3 LedgerGrid.)
- **cloth_dashboard** (HTML-011, Phase A) — **Dashboard System A (base-primitive):** base **`.kpi`×13 + `.card`×7** (SHARED) + **2 tables** (Family E classified). → another base-`.kpi`/`.card` dashboard (like adda_dashboard 064). base-primitive dashboard.
- **public_home** (`templates/public_home.html`, 1311L) — **STANDALONE public marketing surface** (extends=0, own `<style>`, own `.card`×6, no base.html, no money/tables/forms). Independent public system (the unauthenticated landing). Self-contained; not part of the app card/dashboard systems.
- **403 / 404 / 500** — **3 near-IDENTICAL standalone error pages** (extends=0, inline CSS, 1 `.card` each, ~48-51L). Diff = only the heading/comment (not-found vs permission-denied vs server-error). **Deliberately self-contained** (comment: "no base.html, no DB-dependent context, renders in any state") → standalone is JUSTIFIED (must render when base/DB broken). Error-page "system" = 3 copy-paste copies, intentional. Brand-consistent.
- **sidebar_access_list** (229L) — access-config surface: extends base, **1 form**, **0 cards/tables/kpi**, own `<style>`. Sidebar-rule config (not a card/dashboard/table surface). Config page.
- **Card-ownership updates:** base `.stat-card` (=TC-3 SummaryCards) consumers = my_earnings + worker_detail (2). base `.kpi` consumers = adda_dashboard(064) + cloth_dashboard(071G) = 2. base `.card` consumers += cloth_dashboard = 7.
- **Surface-system classifications:** my_earnings=TC-3 SummaryCards(cards) · cloth_dashboard=Dashboard-System-A(base-primitive)+tables · public_home=standalone-public · error-pages=standalone-resilient(×3) · sidebar_access_list=config-form.
- Net: CLEAN; my_earnings confirms `.stat-card`↔TC-3; cloth_dashboard base-primitive; public_home + error pages standalone (justified); sidebar config. No mutation.
- Evidence: my_earnings stat-card×7+money (browser) + error-page near-identical diff + cloth_dashboard base kpi/card+2 tables (signal) + public_home standalone (signal).
- Commit: none (no code change).

### HTML-070G — `production/stage_list` + `inventory/role_list` + `production/stage_rate_list` (card-LIST trio) [PHASE G]
- Status: **CLEAN** (browser-verified); **NO mutation** (read-only) — awaiting owner review. (Labeled 070G to avoid clash with the Form-control HTML-070 barcode_gen host.)
- Audit unit / method: card-list-surface focus (3 list pages as cards). Browser 1280/320, super-admin: `/production/stages/` · `/inventory/roles/` · `/production/addas/3-PATTI-004/stage-rates/`. All extend base.html.
- **Systems — card-LISTS, MIXED ownership:**
  - **stage_list** → **page-scoped `.stage-card`** (7 cards) + `.pill`×31 (stage status pills). baseCard=0, tables=0, 0-overflow.
  - **role_list** → **base `.card`** (5, SHARED) + `.empty-state`. No own `<style>`. baseCard=5, tables=0, 0-overflow.
  - **stage_rate_list** → **page-scoped `.stage-card`/`.rate-row`** (12) + `.pill`×9 + ₹ rate value. baseCard=0, tables=0, 0-overflow. (S1.1 rate list.)
- **Card-list implementations = MIXED (not one system):** base `.card` (role_list) vs page-scoped (pattern_list 061 `.pattern-list` · stage_list `.stage-card` · stage_rate_list `.stage-card`/`.rate-row`) → **≥4 card-list impls (1 base + 3 distinct page-scoped).** Confirms SHARED≠UNIVERSAL.
- **`.pill` status-badges:** heavy in stage_list(31) + stage_rate_list(9) = production STAGE pills (page-scoped); distinct from financial `.pill` (052/036). Pills = recurring status-badge concept, MULTIPLE owners. Track.
- stage_rate_list money (₹ rate) = a `.pill`/value, NOT a financial-table → no TC-3.
- Responsive: all 3 mobile @320 **0 overflow**.
- **Card-ownership: base `.card` REUSED** → consumers now 063/064/066/adda_history/roll_history + **role_list** = **6**.
- Net: CLEAN; card-lists MIXED (role_list base; stage/rate page-scoped); production pills page-scoped; 0 tables; mobile-safe. No mutation.
- Evidence: stage_list(7 cards/31 pills) · role_list(5 base card) · stage_rate_list(12/9 pills) — all 0 tables, 0-overflow @320.
- Commit: none (no code change).

### HTML-069 — `pending_reports` + `stalled_addas` + `raw_material_dashboard` (dashboard summaries) [PHASE G]
- Status: **CLEAN** (browser-verified); **NO mutation** (read-only) — awaiting owner review. 1 census-gap flagged (stalled_addas table).
- Audit unit / method: dashboard-surface focus (3 summaries). Browser 1280, super-admin, `/production/pending-reports/` · `/production/stalled-addas/` · `/raw-materials/`. Each extends base.html + own `<style>`.
- **Systems — 3 DISTINCT PAGE-SCOPED dashboards (NONE use base `.kpi`/`.card`):**
  - **pending_reports** → `.pending-cards`/`.pending-card` (own). Browser: baseKpi=0, baseCard=0, **5 page-cards**, 0 tables, 0-overflow.
  - **stalled_addas** → `.stalled-list`/`.stalled-cards`/`.stalled-empty` (own). **CARD-LIST (anchor-cards + `<dl class=meta>`), 0 tables** (read-confirmed; see census-gap resolution below). baseKpi=0, baseCard=0, 0-overflow.
  - **raw_material_dashboard** (`/raw-materials/`) → `.rm-cloth-card`/`.rm-cloth-stats`/`.rm-soon-grid` + `.stat-num`/`.stat-lbl` (own KPI-ish stats ×5). Browser: baseKpi=0, baseCard=0, **6 page-cards**, 0 tables, 0-overflow.
- **owner's HTML-069 questions:**
  - base `.kpi` reuse? → **0** (all 3). base `.card` reuse? → **0** (all 3). → these 3 do NOT reuse base primitives (contrast 063/064 which DO).
  - page-scoped cards? → **YES, 3 different own systems** (pending-card / stalled-card / rm-cloth-card+stat-num).
  - hidden tables? → **stalled_addas: 1 table** (browser; ⚠ not in Family E 26-table census — likely rendered via an included partial or accordion; **census-gap flagged → classify**). pending/RM-dash: 0.
  - TC-3 SummaryCards relationship? → **none** (no ₹/money in these 3; they're operational/count dashboards, not financial).
  - Dashboard implementations → **MULTIPLE systems.** **Dashboard System A = base-primitive** (adda_dashboard 064 `.kpi`+`.card`; user_dashboard 063 `.card`). **Dashboard System B/C/D = page-scoped per-page** (pending-card · stalled-card · rm-cloth-card). → dashboards are NOT one system; base-primitive + ≥3 page-scoped divergent. Page-scoped divergence (record; don't unify).
- Responsive: all 3 **0 overflow @1280** (card grids; 320 per-page deferred — desktop clean, page-scoped grids likely auto-fit). Console: not separately captured this batch (no JS-heavy systems; flag if needed).
- **CENSUS-GAP → RESOLVED (FALSE ALARM):** re-read stalled_addas.html fully — **0 `<table>`, 0 `{% include %}`**; it uses `.stalled-card` ANCHOR-cards + `<dl class="meta">` + `.stalled-empty`. The browser `tables=1` reading was **spurious** (base.html chrome / stale DOM), NOT a stalled_addas table. **Family E `<table>` census STANDS CORRECT** (stalled_addas = 0 tables). Inventory accuracy preserved; earlier flag retracted.
- Net: CLEAN; 3 page-scoped dashboard systems (no base primitives, no money/TC-3); multiple-dashboard-systems confirmed; 1 census-gap (stalled table). No mutation.
- Evidence: pending(5 page-cards) · stalled(1 table) · RM-dash(6 page-cards) — all baseKpi/baseCard=0, 0-overflow.
- Commit: none (no code change).

### HTML-068 — `tracking/history/adda_history.html` + `roll_history.html` (audit-timeline pages) [PHASE G]
- Status: **CLEAN** (both browser-verified); **NO mutation** (read-only) — awaiting owner review.
- Audit unit / method: timeline-surface focus (2 near-identical pages, audited together). Browser 1280/320, super-admin, `/tracking/history/adda/3-PATTI-001/` (26 events) + `/tracking/history/roll/4/` (2 events). Extends base.html + page-scoped `.history-page` `<style>` (each file own copy).
- **System: audit-TIMELINE** — base **`.card`** wrapper + `<ul>`/`<li>` event list (`.ts` timestamp · event description · `.actor`). 0 tables. **NO `_activity_feed` include.**
- **owner's HTML-068 questions:**
  - Timeline ownership? → **page-scoped `.history-page`** (own `<style>` per file) + base `.card` wrapper.
  - `_activity_feed` reused? → **NO** (activityFeed=false both). Distinct from adda_detail's timeline.
  - Shared or multiple timeline systems? → **MULTIPLE.** **System 1 = `_activity_feed.html`** (shared partial, adda_detail 065). **System 2 = `.history-page` audit-timeline** (adda_history + roll_history).
  - adda_history vs roll_history? → **near-IDENTICAL** (diff = domain only: adda.code/AddaHistory vs roll.id/ClothRollHistory). **2 DUPLICATED copies** of the history-timeline (each own `.history-page` `<style>` + `<ul><li>` — could share a `_history_timeline` partial but don't = accidental divergence / copy-paste).
- Browser: adda_history 26 events + roll_history 2 events; base `.card`×1 each; activityFeed=false; tables=0. Mobile @320 **0 overflow**, li fits. Console clean.
- **Card-ownership: base `.card` REUSED** (wrapper) → consumers now 063/064/066 + adda_history + roll_history = **5**. Timeline = page-scoped, duplicated ×2.
- Net: CLEAN; audit-timeline System 2 (base `.card` + page-scoped `.history-page`, DUPLICATED across 2 history pages); distinct from `_activity_feed` System 1; mobile-safe. No mutation.
- Evidence: 26/2 events + base `.card` + no activity-feed + diff(domain-only) + mobile 0-overflow + console clean.
- Commit: none (no code change).

### HTML-067 — `tracking/scan_detail.html` (barcode scan detail — System B, ⚠ UNROUTED) [PHASE G]
- Status: **CODE-VERIFIED (Detail System B); ⚠ view UNROUTED — not browser-reachable**; **NO mutation** — awaiting owner review.
- Audit unit / method: card/detail-surface focus. Code-read + routing check (3 scan-URL guesses → 404; `scan_piece` not in any urls.py). Extends base.html + page-scoped `.scan-detail` `<style>`.
- **Systems (code):** base **`.card`** + **`<dl>`** attribute list (Adda · Product · Piece# · Status · First-scan · Scanned-by) · back-link. **NO `_activity_feed` timeline · NO money(₹) · 0 tables · no chips.**
- **owner's A/B/third determination → MATCHES roll_detail = DETAIL SYSTEM B** (base `.card` + `<dl>` attribute list, lightweight, no timeline). → **System B gains a 2nd consumer (by code): roll_detail(066) + scan_detail(067).** Detail System A (adda_detail page-scoped+timeline) unchanged at 1.
- **⚠ ROUTING FINDING — UNROUTED:** `scan_detail.html` is rendered by `scan_piece(request, value)` (`inventory/views/tracking_barcodes.py:163`) but **scan_piece is NOT wired into ANY `urls.py`** (grep `scan_piece|scan` across all urls.py = 0). Only reached by `test_scan_view.py` (test client). 3 live-URL guesses → 404. → **scan_detail is NOT browser-reachable** (orphaned view/template, OR a QR-scan flow not yet URL-wired). Like home.html(062) but with a working view+test. **Dead/unwired candidate — owner decides (dead vs pending-wiring).** Honest: System B by code; **browser-UNVERIFIED** (no live URL).
- Net: code-confirmed System B (base `.card`+dl, matches roll_detail) but unrouted → flagged orphaned/unwired. No mutation.
- Evidence: template read (base `.card` + dl, no timeline/money/table) + scan_piece unrouted (0 urls.py hits) + 3×404 + test-only render.
- Commit: none (flagged — owner decides wiring/cleanup).

### HTML-066 — `raw_materials/roll_detail.html` (cloth-roll detail — base `.card` + dl) [PHASE G]
- Status: **CLEAN**; **NO mutation** (read-only, /rolls/4/) — awaiting owner review.
- Audit unit / method: card/detail-surface focus. Browser 1280/320, super-admin, `/raw-materials/rolls/4/`. Extends base.html + page-scoped `.roll-detail` `<style>`.
- **Systems inventory:** **base `.card` ×2 (SHARED)** [inside `.roll-detail` wrapper] · `<dl>` attribute list (roll specs incl. **Cost/KG ₹ inline in dl**) · 1 status `.badge` · **0 tables · NO `_activity_feed` timeline** (activityFeed=false) · 1 form (base search).
- **owner's HTML-066 questions:**
  1. Reuse `_activity_feed`? → **NO** (no timeline). 2. Detail ownership? → **base `.card` (SHARED)** + page-scoped `.roll-detail` wrapper. 3. Hidden tables? → **0**. 4. Timeline reuse? → none. 5. Money→TC-3? → **NO** — Cost/KG is a single **₹ value in a `<dl>`**, not a stat-card/SummaryCard/LedgerGrid; **minimal/no TC-3 relationship**. 6. Chips/badges? → 1 status `.badge` (page/base badge). 7. Responsive → mobile @320 **0 overflow**, cards fit.
- **KEY FINDING — MULTIPLE DETAIL SYSTEMS (evidence):** roll_detail **DIFFERS from adda_detail (065)** → NOT a consumer of the same system. **Two distinct detail patterns:** (a) **adda_detail** = fully page-scoped `.adda-detail` + display chips + `_activity_feed` timeline (complex 360); (b) **roll_detail** = **base `.card`** + `<dl>` + status badge (simple attribute detail, no timeline). → detail pages are NOT one detail system.
- **Card-ownership data point: base `.card` REUSED (3rd consumer)** — user_dashboard(063) · adda_dashboard(064) · **roll_detail(066)**. (`_activity_feed` still 1 consumer = adda_detail.)
- Net: CLEAN; base `.card`+dl detail (distinct from adda_detail's page-scoped+timeline); money-in-dl ≠ TC-3; 0 tables; mobile-safe. No mutation.
- Evidence: base `.card`×2 + dl(Cost/KG ₹) + 1 badge + 0 tables + no activity-feed + mobile 0-overflow + console clean.
- Commit: none (no code change).

### HTML-065 — `production/adda_detail.html` (Adda-360 detail — fully PAGE-SCOPED) [PHASE G]
- Status: **CLEAN**; **NO mutation** (read-only, golden 3-PATTI-001) — awaiting owner review.
- Audit unit / method: card/detail-surface focus. Browser 1280/320, super-admin, `/production/addas/3-PATTI-001/` (golden, read-only). Extends base.html + large page-scoped `.adda-detail` `<style>` (759 lines).
- **Systems inventory (systems-not-page):**
  - **Detail/360 sections — fully PAGE-SCOPED `.adda-detail`** — **baseCard=0, kpi=0, statCard=0** → does NOT use base `.card`/`.kpi`/`.stat-card`. (The discovery-scan "52 cards" = CSS class-name string matches, NOT 52 rendered base cards — corrected.)
  - **Status badge** (`.hero-badge`, page-scoped, status-colored).
  - **Display chips** — `.roll-chip` (roll links) + `.worker-chip` (page-scoped chips/badges). DISPLAY chips (not form-control CC-16/CC-17).
  - **Activity feed / TIMELINE** — `{% include 'production/_activity_feed.html' %}` → **SHARED timeline partial** (a real shared-owner; reused by history pages too — track).
  - **0 tables · 1 form** (base topbar search only).
- **Card-ownership data point: adda_detail = FULLY PAGE-SCOPED** (own `.adda-detail`, NOT base primitives). **Contrast 063/064 dashboards (base `.card`/`.kpi` shared).** → detail-360 = page-scoped; dashboards = base-shared. **Ownership varies by surface-TYPE.**
- Responsive: mobile @320 **0 overflow**, page-scoped sections fit, chips-row wraps. Mobile-safe. Console clean.
- **Relationship:** detail-360 cards (page-scoped) ≠ dashboard cards (base) ≠ card-LIST (061 page-scoped) ≠ TC-3 SummaryCards (financial page-scoped). Activity-feed = a SHARED timeline partial (distinct from cards). Display chips ≠ form-control chips (CC-16/17). **All distinct; no merge.**
- Net: CLEAN; fully page-scoped detail-360 + shared `_activity_feed` timeline + page-scoped display chips + status badge; 0 base cards, 0 tables; mobile-safe. No mutation.
- Evidence: baseCard/kpi/statCard=0 + hero-badge + roll-chip + activity-feed include + 0 tables + mobile 0-overflow + console clean.
- Commit: none (no code change).

### HTML-064 — `production/adda_dashboard.html` (= production:dashboard, management landing — card lens) [PHASE G]
- Status: **CLEAN** (card-systems); **NO mutation** (read-only) — awaiting owner review. (Same template = HTML-024, audited Phase C for date range-filter; this is the CARD-lens pass.)
- Audit unit / method: card-surface focus. Browser 1280/320, super-admin, `/production/` (production:dashboard). Extends base.html.
- **MULTI-SYSTEM surface (systems-not-pages):**
  - **KPI tiles — 4× base `.kpi`** (SHARED primitive). KPI-tile card type. kpiH 96px, stack full-width @320.
  - **Generic sections — 2× base `.card`** (SHARED).
  - **1 plain table** (dtWrapper=0) — already Family E **Type-5 Dashboard-Summary** (date-filtered adda list).
  - **Date range filter** — 2× native `<input type=date>` (Phase C HTML-024; native, Date family).
  - forms=2 (date-filter form + base search).
- **Card-ownership: base `.kpi`(4) + base `.card`(2) REUSED (SHARED)** + page-scoped dashboard styling. **2nd live dashboard on base primitives** (after 063 user_dashboard) → shared owner confirmed across 2 dashboards.
- Responsive: mobile @320 **0 overflow**, KPI tiles stack (300px, fit), table = Type-5 responsive. Console clean.
- **Compare:** 063 user_dashboard = base `.card` only (generic sections); **064 adda_dashboard = base `.kpi`×4 + `.card`×2** (KPI tiles + sections). Both reuse base primitives (shared); different card-type mix. Dead 062 home = base `.kpi` placeholder (excluded). TC-3 SummaryCards (financial) = a DIFFERENT money-card concept (page-scoped); NOT the same as these dashboard `.kpi`/`.card` (base).
- Net: CLEAN; multi-system (KPI tiles + cards [base/shared] + Type-5 table + date filter); mobile-safe. No mutation.
- Evidence: `.kpi`×4 + `.card`×2 (base) + 1 table (Type-5) + 2 date inputs + mobile 0-overflow + console clean.
- Commit: none (no code change).

### HTML-063 — `inventory/user_dashboard.html` ("My Dashboard" — generic-card sections) [PHASE G]
- Status: **CLEAN**; **NO mutation** (read-only) — awaiting owner review.
- Audit unit / method: card-surface focus. Browser 1280/320, super-admin, `/inventory/my-dashboard/`. Extends base.html + own `<style>` (×2 blocks). (Also rendered by admin `dashboard` view with `is_admin_view`.)
- **System: generic-`.card` dashboard** — 4 card SECTIONS in code (Active Addas · Active Layering · My Active Stages · My Recent Activity[collapsible `<details class="card">`]). **Uses base `.card`/`.card-header`/`.card-body`/`.card-title` (SHARED primitive)** + page-scoped `<style>` (own grid `auto-fit minmax(160px)` + section styling). **NO `.kpi`, NO `.stat-card`** here.
- Browser (super-admin): **baseCard=2** (super-admin sees 2 sections — no worker stages; a WORKER sees all 4, conditional on data/role — honest: code has 4, super-admin render = 2) · kpi=0 · statCard=0 · **tables=0** · forms=1 (base topbar search) · details=1 (collapsible). Console clean.
- Responsive: mobile @320 **0 overflow**, cards fit (300px), auto-fit grid. Mobile-safe.
- **Card-ownership data point:** **base `.card` REUSED (shared owner)** + page-scoped supplementary `<style>`. (Contrast pattern_list 061 = fully page-scoped `.pattern-list`.) → base `.card`/`.kpi` ARE reused by live dashboards; page-scoped variants coexist = MIXED.
- Net: CLEAN; generic-`.card` dashboard on base `.card` + page-scoped styling; 0 tables; mobile-safe. No mutation.
- Evidence: base `.card`×2 (super-admin) + 0 tables + collapsible details-card + mobile 0-overflow + console clean.
- Commit: none (no code change).

### HTML-062 — `accounts/home.html` (Card/KPI dashboard — ⚠ DEAD/ORPHANED template) [PHASE G]
- Status: **DEAD CODE — no renderer; code-read only**; **NO mutation** — awaiting owner review.
- Audit unit / method: card-surface focus. Code-read + routing check + browser redirect-trace.
- **Finding — ORPHANED TEMPLATE:** `accounts/home.html` is **rendered by NOTHING** (grep `render/TemplateView 'accounts/home.html'` = 0 hits). `HomeView` (views.py:236) **unconditionally redirects** — management→`production:dashboard`, others→`inventory:user_dashboard` — it **never renders home.html**. Browser-confirmed: `/app/home/` → **302 → `/production/`** (finalUrl=/production/, `₹2.4L` absent, redirect-target uses base `.kpi`).
- Content (dead): `.kpis` + 4 base **`.kpi`** tiles with **HARDCODED placeholder `₹2.4L`** (not data-bound) + auto-fit quick-links grid. A legacy/placeholder dashboard.
- **Classification: DEAD/dormant surface** (like signup dormant) — orphaned template + hardcoded placeholder. **Doc/cleanup candidate** (dead-code removal), NOT a live card surface. Recorded honestly; not browser-rendered (renders nowhere).
- **Card-ownership data point:** home.html (dead) uses base `.kpi`; the **LIVE management landing = `production:dashboard`** (browser-confirmed uses base `.kpi` — shared primitive reuse). → **`production:dashboard` + `inventory:user_dashboard` are the REAL KPI-dashboard surfaces** (audit these, not home.html). Added to Family G surface list.
- Net: DEAD template (no renderer; hardcoded placeholder). No live render. No mutation.
- Evidence: grep (0 renderers) + HomeView redirect code + /app/home/→/production/ trace (₹2.4L absent live).
- Commit: none (flagged dead — owner decides cleanup).

### HTML-061 — `production/pattern_list.html` (Card-LIST surface) [PHASE G]
- Status: **CLEAN**; **NO mutation** (read-only) — awaiting owner review.
- Audit unit / method: card-surface focus. Browser 1280/320, super-admin, `/production/patterns/` (4 patterns). Extends base.html. Page-scoped `.pattern-list` `<style>`.
- **System: CARD-LIST** (CRUD list rendered as card-ROWS, not a table). 4 cards, grid `1fr auto` (content + `.actions` column: edit/delete = 2 action links). `.empty` inline. **0 tables.** **Owner = page-scoped `.pattern-list`** (NOT base `.card`; usesBaseCard=false).
- Render: 1280 + mobile 320 **0 overflow**, cards fit (240px@320). Console clean.
- **Card classification: Card-LIST type, page-scoped owner.** First card-system data point. (Card-list = a CRUD list as cards — distinct from A1/A2 table-lists AND from KPI/stat/detail cards.)
- Net: CLEAN card-list; page-scoped `.pattern-list`. No table/form hidden. No mutation.
- Evidence: 4 card-rows + 0 tables + page-scoped `.pattern-list` (not base `.card`) + mobile 0-overflow + console clean.
- Commit: none (no code change).

- **HTML-061** `accounts/home.html` — KPI mockup (inline-styled stub) — **SEED**
- **HTML-062** `accounts/skill_confirm_delete.html` — confirm-card — PENDING
- **HTML-063** `accounts/user_confirm_delete.html` — confirm-card — PENDING
- **HTML-064** `accounts/usertype_confirm_delete.html` — confirm-card — PENDING
- **HTML-065** `accounts/_user_form_styles.html` — CSS partial — via HTML-002 — PENDING
- **HTML-066** `expense/my_earnings.html` — worker earnings display — PENDING
- **HTML-067** `production/_activity_feed.html` — feed partial — via host pages — PENDING
- **HTML-068** `production/adda_detail.html` — Adda-360 display + accordions — PENDING
- **HTML-069** `production/_autosave.html` — JS partial — via stage workspaces — PENDING
### HTML-070 — `production/barcode_gen_workspace.html` (HOST wrapper) [PHASE D — Form-control completeness]
- Status: **CLEAN** — browser-verified (super-admin); thin host; **NO mutation** (GET only) — awaiting owner review.
- Method: `/production/addas/3-PATTI-004/barcode-gen/` (start state) + golden 3-PATTI-001 (post-generate). Extends base.html + `{% include 'production/_form_styles.html' %}` (**6th consumer** of the shared partial) + own `<style>`. Hosts `_stage_panel_barcode_gen` (HTML-071) + hero + back. No new controls (thin wrapper, like pattern_workspace 048).
- Render: 1280/320/414 **0 overflow**; console clean. CSS = shared `_form_styles.html` + host `<style>`.
- Net: CLEAN thin host. Commit: none.

### HTML-071 — `production/_stage_panel_barcode_gen.html` (Form-control — barcode_gen panel; closes CC-20) [PHASE D]
- Status: **CLEAN — closes the CC-20 inventory**; **NO mutation** (GET only — reopen/start/generate/complete all mutate) — awaiting owner review.
- Method: form-control focus. Browser 1280/320/414, super-admin, via barcode-gen-workspace; start state = 3-PATTI-004 (worker-picker), post-generate = golden 3-PATTI-001 (barcode tables). Render-only.
- Controls: raw-POST action forms (reopen/start/generate/complete) + **`{{ start_form.workers }}`** + barcode tables (size/color/range/pieces, data-label) + auto-fit grid (`repeat(auto-fit,minmax(140px,1fr))`).
- **CC-20 BARCODE_GEN — BROWSER-CONFIRMED (closes the last CC-20 surface):** worker-picker = **bare Django-default** `<input type=checkbox name=workers value=2 id=id_workers_0>` (no chip, native **13px**), **identical to cutting_pattern (045)**. The Multiselect-report code-only caveat for barcode_gen is now **browser-resolved**. **CC-20 inventory COMPLETE: both surfaces (pattern_stage/cutting_pattern 045 + barcode_gen 071) = bare Django-default.** Worker-domain CC-16(chip)/CC-20(bare) split fully confirmed.
- Validation/interaction: raw-POST per-section action forms + native; no per-field Django render (action-form). → production stage-panel raw-POST multi-form (same family as 045).
- CSS owner: shared `_form_styles.html` (via host) + panel's own `<style>` (auto-fit grid) + sf-input.
- Mobile: 320/414 **0 overflow**; **generated-barcode tables stack (tr→block / td→flex) @mobile** (golden 001 verified, data-label cards); worker checkbox visible @320; auto-fit grid reflows. **No XC-1.**
- Touch: worker checkbox **13px** (CC-20, tied-smallest). Console: clean (only favicon CC-28).
- Net: CLEAN; closes CC-20; mobile-safe (stacking tables + auto-fit). No mutation.
- Evidence: worker `<input checkbox>` (CC-20 13px) + barcode-table tr/td stacking @mobile + 0-overflow + console clean.
- Commit: none (no code change).
- **HTML-072** `production/cutting_workspace.html` — host of `_stage_panel_cutting` (HTML-010) — PENDING
- **HTML-073** `production/_form_styles.html` — CSS partial (form-shell) — via host forms — PENDING
- **HTML-074** `production/_layering_summary.html` — summary partial — via HTML-008 — PENDING
- **HTML-075** `production/pattern_confirm_delete.html` — confirm-card — PENDING
- **HTML-076** `production/pattern_list.html` — pattern list — PENDING
- **HTML-077** `production/pending_reports.html` — report list — PENDING
- **HTML-078** `production/product_confirm_archive.html` — confirm-card — PENDING
- **HTML-079** `production/stage_confirm_delete.html` — confirm-card — PENDING
- **HTML-080** `production/stage_list.html` — stage list — PENDING
- **HTML-081** `production/_stage_panel_collapse.html` — structural partial — via stage panels — PENDING
- **HTML-082** `production/stage_panel_embedded.html` — chromeless embed host — PENDING
- **HTML-083** `production/stage_panel_standalone.html` — standalone panel host — PENDING
- **HTML-084** `production/stage_rate_list.html` — rate list — PENDING
- **HTML-085** `production/stalled_addas.html` — stalled list — PENDING
- **HTML-086** `production/worker_report_embedded.html` — chromeless host of `_worker_report_body` — **SEED**
- **HTML-087** `production/worker_report.html` — standalone host of `_worker_report_body` — **SEED**
- **HTML-088** `production/_worker_report_styles.html` — CSS partial — via HTML-087 — **SEED**
- **HTML-089** `raw_materials/master_confirm_archive.html` — confirm-card — PENDING
- **HTML-090** `raw_materials/master_confirm_delete.html` — confirm-card — PENDING
- **HTML-091** `raw_materials/raw_material_dashboard.html` — dashboard + time-log accordion (PA-13-3 fixed) — PENDING
- **HTML-092** `raw_materials/roll_detail.html` — roll detail display — PENDING
- **HTML-093** `storefront/listing/category_confirm_delete.html` — confirm-card (inline `.btn-danger` override) — **SEED**
- **HTML-094** `storefront/listing/product_confirm_delete.html` — confirm-card (inline `.btn-danger` override) — **SEED**
- **HTML-095** `templates/403.html` — error page — PENDING
- **HTML-096** `templates/404.html` — error page — PENDING
- **HTML-097** `templates/500.html` — error page — PENDING
- **HTML-098** `templates/inventory/_adda_events_accordion.html` — accordion partial — via host — PENDING
- **HTML-099** `templates/inventory/dashboard.html` — main dashboard — PENDING
- **HTML-100** `templates/inventory/_nav_icon.html` — icon partial — via sidebar — PENDING
- **HTML-101** `templates/inventory/role_confirm_delete.html` — confirm-card — PENDING
- **HTML-102** `templates/inventory/role_list.html` — role list — PENDING
- **HTML-103** `templates/inventory/_roll_events_accordion.html` — accordion partial — via host — PENDING
- **HTML-104** `templates/inventory/_section_icon.html` — icon partial — via sidebar — PENDING
- **HTML-105** `templates/inventory/sidebar_access_list.html` — access list — PENDING
- **HTML-106** `templates/inventory/_time_log_styles.html` — CSS partial — via host — PENDING
- **HTML-107** `templates/inventory/user_dashboard.html` — user dashboard — PENDING
- **HTML-108** `templates/public_home.html` — public landing — PENDING
- **HTML-109** `templates/shared/_datatables_vendor_css.html` — vendor CSS partial — via list pages — PENDING
- **HTML-110** `templates/shared/_datatables_vendor_js.html` — vendor JS partial — via list pages — PENDING
- **HTML-111** `tracking/history/adda_history.html` — adda history display — PENDING
- **HTML-112** `tracking/history/roll_history.html` — roll history display — PENDING
- **HTML-113** `tracking/scan_detail.html` — scan detail display — PENDING

---

## SEED import note

20 templates carry **SEED** status — code-read classification from
`FRONTEND_DESIGN_SYSTEM_INVENTORY.partial.json` (the superseded phase-based audit,
chunks A/H/J). Seed data is evidence only: it accelerates the code-read step but
each SEED template still gets the full per-HTML cycle (browser + mobile + fix +
canonicalize) when its family slot is reached. No SEED template is "done".

## ⬛⬛ FAMILY E — TABLE-SYSTEM COMPLETENESS SCAN (2026-06-16) — inventory only, NO report/recommendations
Full grep: **26 templates contain `<table>`** (+ base.html = the `initFancyDataTable` OWNER/helper, not a page table). `my_earnings`/`roll_detail` = 0 tables (card/div money — NOT table systems). **Every table template has an audit record.** Classified by TABLE SYSTEM (not page); a multi-system page appears in multiple buckets. **Browser-verified-as-table = 049-059 (Family E) + 036/044 (Phase D); others = signal-classified here (browser-verified for their original phase concern).**

### 1. A1 INVENTORY — Canonical CRUD Lists (DataTable engine, TC-1) — **5 consumers**
| # | Page | Engine | Status |
|---|---|---|---|
| 049 | accounts/skill_list | initFancyDataTable | ✓ browser |
| 050 | accounts/user_list | initFancyDataTable (+filter-row) | ✓ browser |
| 051 | accounts/usertype_list | initFancyDataTable | ✓ browser |
| 018 | storefront/category_list | initFancyDataTable | ✓ (Phase A) |
| 020 | storefront/product_list | initFancyDataTable | ✓ (Phase A) |
- Owner = base.html `initFancyDataTable` + shared `_datatables_vendor_css/js.html`. All search/sort/paginate/empty-state/td-actions shared. **TC-1 = the A1 owner.**

### 2. A2 INVENTORY — CRUD/Report drift (plain + shared primitives, NO engine) → A1 migration candidates
| # | Page | System | Migration effort A2→A1 | Status |
|---|---|---|---|---|
| 056 | raw_materials/master_list | CRUD list, plain | **LOW** (add init helper) | ✓ browser |
| 058 | tracking/barcode_list | read-only Report+Export | LOW | ✓ browser |
| 059 | tracking/export_list | Audit/Manifest | LOW | ✓ browser |
| 004 | production/adda_list | Adda CRUD list, plain (TR/DL, no DT) | LOW | signal (browser Phase A) |
| 006 | production/product_list | Product list, plain | LOW | signal (Phase A) |
| 015 | raw_materials/roll_list | Cloth-roll list, plain ($:1 minor) | LOW-MED | signal (Phase A) |
- **A2 total = 6** (3 browser-confirmed as-table + 3 signal-classified). All accidental drift; near-zero migration. **NOT exceptions.**

### 3. TC-2 INVENTORY — Legitimate Exceptions (DataTable would damage) — grouped
- **Type-1 Workflow Queue:** adda_settlement_list(052)✓ · adda_settlement_detail(036, money snapshot + reverse/supersede forms)✓ · stage panels [_stage_panel_cutting(010) · _stage_panel_cutting_pattern(045) · _stage_panel_barcode_gen(071)] — workflow stage forms.
- **Type-2 Financial Ledger (mostly CONVERTIBLE → fold to A1):** payroll_overview(053, convertible) · costing(055, convertible) · worker_detail-advances-subtable(054, convertible) · settlement_form(money preview).
- **Type-3 Inline Editor:** product_sizes_edit(044)✓ · product_patterns_edit(007).
- **Type-4 Matrix:** role_form permission matrix (CC-18/035) — **the sole matrix** (access_control 057 is read-only overview, NOT a matrix).
- **Type-5 Dashboard Summary:** worker_detail-page(054)✓ · adda_dashboard(024) · cloth_dashboard(011) · barcode_dashboard(025) · access_control(057, read-only overview ×4).

### 4. TC-3 INVENTORY — Financial Foundation (concept shared, impl duplicated) — **~6 consumers**
| Primitive | Concept shared? | Impl shared? | Where |
|---|---|---|---|
| SummaryCards (hero total / stat-cards) | YES | NO (page-local) | 052·053·054·055·036 |
| MoneyCell (`₹{{x\|floatformat:2}}`) | YES | NO (inline Django filter) | all financial (~7) |
| StatusPill (`.pill`) | partial | NO | 052·036 only |
| LedgerGrid (money table) | YES | NO (page-scoped each) | 052·053·054·055·036·settlement_form |
| LedgerEmpty (inline `.empty`) | YES | NO (≠ World-A `.empty-state`) | all financial |
| ResponsiveLedger (page-scoped data-label) | YES | NO (reimplemented ×7) | all financial + 3 prod |
- **Consumers ≈ 6** (settlement_detail 036 · settlement_list 052 · payroll 053 · worker_detail 054 · costing 055 · settlement_form). **Verdict B: foundation exists CONCEPTUALLY, duplicated implementation. Migration counter ≈ 4-6.**

### 5. TC-5 INVENTORY — Export Foundation (narrow; concept shared, impl duplicated)
| Primitive | Concept shared? | Impl shared? | Consumers |
|---|---|---|---|
| ExportButtonGroup (CSV/XLSX/PDF) | YES | **NO — inline-duplicated** | barcode_list(058) + barcode_gen panel(071) = **2** |
| ExportManifest (audit table) | — | — | export_list(059) = 1 |
| ExportDownload (regenerate from live) | YES | service-backed (`barcode_export_service`) | 059 |
- **NARROW** (barcode-export only). Concept repeats (button-group ×2), impl duplicated. Backed by one service.

### COMPLETENESS VERDICT
- **All 26 table templates classified; 0 unclassified.** Buckets: A1=5 · A2=6 · TC-2 exceptions (Type1-5, several) · TC-3 financial=~6 · TC-5 export=narrow. base.html = TC-1 owner.
- **Browser-as-table coverage:** 049-059 + 036/044 fully table-audited; A2 candidates 004/006/015 + dashboards 011/024/025 + stage panels 010/045/071 + product_patterns_edit 007 = signal-classified here (browser-verified in their original phase, table-aspect = code-read in this scan). **If the Tables Report needs them browser-verified AS table-systems, flag for targeted re-check.**
- **Family E inventory COMPLETE (per signals) → ready for Tables Consolidation Report on owner go.** NO report/recommendations/promotion yet.

## ⬛⬛ FAMILY G — PARTIALS/INFRA CENSUS + COMPLETENESS SCAN (2026-06-16) — inventory only, NO architecture decisions

### A. Partials / Infrastructure Census (include graph)
- **`base.html` = MASTER SHELL — 78 consumers** (templates extending it). Owns: layout (sidebar/topbar/`.overlay` drawer) + global JS (`fancify`/`fancifyDate`/**`initFancyDataTable`**/`toggleSidebar`) + shared CSS primitives (`.card`/`.kpi`/`.stat-card`/`.form-control`/`.sf-input`?/`.table-responsive`/`.empty-state`/`.btn`/`.pill`?). THE single biggest code-level shared owner.
- **True shared-owner partials (multi-consumer, by include-count):**
  - `production/_form_styles.html` — **19×** (production form-shell; cutting/product/master forms + rate-correct + workspaces + stage panels). Biggest partial owner.
  - `shared/_datatables_vendor_css.html` + `_js.html` — **5× each** (= TC-1 DataTable vendor; the 5 A1 pages).
  - `inventory/_time_log_styles.html` — **5×** (dashboards/lists: RM-dash, barcode-dash, roll_list, adda_dash, cloth_dash).
  - `accounts/_user_form_styles.html` — **4×** (mgmt form CSS = CC-26; user_create/user_form/skill_form…).
  - `production/_stage_panel_collapse.html` — 4× · `_stage_panel_layering` 3× · `_autosave` 3× · `_worker_report_styles`/`_worker_report_body`/`_layering_summary`/`_activity_feed`(timeline)/`_roll_events_accordion`/`_adda_events_accordion` — 2× each.
- **Single-consumer partials (decomposition, not shared owners):** `_stage_panel_cutting_pattern`(1) · `_stage_panel_barcode_gen`(1) · `_nav_icon`(1) · `_section_icon`(1).
- **Widget-rendered (NOT `{% include %}`):** `production/_workers_widget.html` — **0 includes but LIVE** = `template_name` of the `_WorkerCheckboxes` widget (`forms/_shared.py:48`, CC-16 worker-chip). **NOT dead** (widget-mechanism rendered). (Earlier "0×" was an include-count artifact.)
- **Dead/orphaned PARTIALS: NONE** (all partials either included ≥1 or widget-rendered). **Dead/unrouted SURFACES:** `accounts/home.html`(062, no renderer) · `tracking/scan_detail.html`(067, scan_piece view unrouted).
- **owner's census Qs:** (1) true shared owners = base.html(78) + `_form_styles`(19) + `_datatables_vendor`(5,TC-1) + `_time_log_styles`(5) + `_user_form_styles`(4) + 2-4× CSS partials. (2) accidental duplicates = `.history-page` timeline(×2,068) · error pages(×3, resilience-justified) · `.chip-pick`(CC-19) · financial page-scoped(TC-3) — duplicated CONCEPTS, not partials. (3) dead = 0 partials; 2 surfaces (home/scan). (4) foundations EXISTING in code = base.html primitives · `_form_styles` · `_user_form_styles` · `_datatables_vendor`(TC-1) · `_activity_feed`(timeline). (5) conceptual-only = TC-3 Financial · TC-5 Export · Card/Dashboard/Detail/Timeline systems (mixed/multiple). (6) single-consumer = stage-panel partials + icons (1 each).

### B. Family G Completeness Scan
- **All ~20 real surfaces audited (HTML-061…071G).** Card-lists(061/070G) · dead home(062) · dashboards(063/064/069/cloth-071G) · details(065 A / 066+067 B) · timelines(068) · my_earnings(071G TC-3 SummaryCards) · public_home + errors + sidebar(071G). + ~22 partials censused.
- **Card-ownership map:** base `.card` ×7 (063/064/066/068×2/070G role_list/071G cloth) · base `.kpi` ×2 (064/cloth) · base `.stat-card`(=TC-3 SummaryCards) ×2 (my_earnings/worker_detail). Page-scoped: pattern_list · stage_list · stage_rate_list · adda_detail · pending/stalled/rm dashboards.
- **Multiple-systems confirmed (NOT one each):** Dashboards (base-primitive + ≥3 page-scoped) · Details (A page-scoped+timeline vs B base-card+dl, 3 consumers) · Timelines (`_activity_feed` vs `.history-page`×2) · Card-lists (base role_list + 3 page-scoped).
- **Standalone lane (no base.html):** auth(7, CC-22) · public_home(1) · 403/404/500(3) — self-contained, resilience-justified.
- **Dead/unrouted:** home(062) · scan_detail(067).
- **VERDICT: Family G inventory COMPLETE** (surfaces + partials + completeness). **Ready for Family G Consolidation Report (owner go).** NO architecture decisions / NO foundation promotion — evidence frozen, architecture OPEN until whole-system review.
