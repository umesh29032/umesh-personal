---
id: docs-html-canonical-candidates
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# HTML_CANONICAL_CANDIDATES — staged canonical rules (NOT yet locked)

Companion to [HTML_AUDIT_MASTER.md](HTML_AUDIT_MASTER.md). Staging area for reusable
UI rules **discovered during the per-HTML audit** but **not yet promoted** to the
locked canon ([../UI_COMPONENTS.md](../UI_COMPONENTS.md)).

> ## 🔒 SELECT-FAMILY EVIDENCE FROZEN (2026-06-15)
> Phase A (Selects) COMPLETE — 21/21 units audited. All select-family evidence below
> (CC-01, CC-03, CC-05, CC-06, CC-07, CC-09, CC-10, CC-12, CC-14, CC-15 + the evidence
> table / source-type / visual-owner inventories for HTML-001…022) is **FROZEN** — no
> further select edits unless a later regression is found. Synthesis →
> [SELECT_FAMILY_CONSOLIDATION_REPORT.md](SELECT_FAMILY_CONSOLIDATION_REPORT.md)
> (evidence-based; NO UI_COMPONENTS change until reviewed). Other-family candidates
> (CC-02 dense-grid, CC-04 comment-hygiene, CC-08 Family E, CC-11 Family D, CC-13 Family F)
> are parked for their own phases.

## Why a staging file

Owner rule: **no standard is locked until enough HTML coverage justifies it.** A
candidate here is evidence ("this pattern recurs / this fix would apply elsewhere"),
not a decision. It graduates to UI_COMPONENTS.md only when **proven across templates**.

## Promotion criteria (candidate → UI_COMPONENTS.md)

- The same pattern is observed/fixed in **≥3 templates**, OR
- It is a control-family canonical (select / multiselect / date / table / modal /
  validation / form-layout) confirmed by auditing **all** templates in that family.
- The rule states: standard · required CSS · required JS · required HTML structure ·
  mobile requirement · a11y requirement.
- On promotion: add to UI_COMPONENTS.md, set this candidate's status PROMOTED, link
  the UI_COMPONENTS section.

## Candidate record format

```
### CC-NN — <short title> (family)
- Status: OPEN | PROMOTED | REJECTED
- Observed in: HTML-xxx, HTML-yyy … (count)
- Proposed standard: <one-paragraph rule>
- Required CSS / JS / HTML / mobile / a11y: <specifics>
- Promotion: <UI_COMPONENTS.md section once promoted, or blocker>
```

---

## Candidates

### CC-01 — Keyboard navigation parity for custom dropdown controls (select + date + multiselect)
- Status: OPEN (future enhancement — NOT a blocker)
- Observed in: Step 0 `fancy-date` (committed `7e105b92`); applies equally to the
  existing `fancy-select` (`base.html`) and any future `fancy-multiselect`.
- Proposed standard: the body-anchored custom controls (`.fancy-select-panel`
  family) should share one keyboard model — arrow-key navigation within the panel
  (grid for the calendar, list for selects), Enter/Space to commit, Escape to close
  **and return focus to the trigger**, plus a focus-trap while open. The real input
  is `aria-hidden` so native typing is gone; this restores keyboard parity.
- Required JS/a11y: roving `tabindex` (or `aria-activedescendant`) on cells/options,
  `keydown` handler on the panel, focus-return on close. CSS: visible focus ring on
  the active cell/option. No HTML structure change.
- Promotion: blocked until built + verified across fancy-select AND fancy-date in
  one shared pass (don't fork the keyboard logic). Tradeoff currently accepted +
  documented in UI_COMPONENTS.md (fancy-select, fancy-date "Known limitations").

### CC-02 — Day-cell touch-target floor on dense grids (note)
- Status: OPEN (documentation note, likely WONTFIX)
- Observed in: `fancy-date` day cells 38px at 320px (7-column grid floor), mirroring
  the OTP 6-box residual already documented in UI_COMPONENTS.md.
- Proposed standard: accept <44px where a fixed column count makes 44px impossible
  at 320px (7 cols → ~38px floor); document the residual rather than redesign. Keep
  ≥44px wherever the column count allows.
- Promotion: this is a documented exception pattern, not a new component. Likely
  folds into UI_COMPONENTS.md's existing multi-box touch-target note rather than a
  standalone rule.

### CC-03 — Select canonical: native/widget `<select>` + `fancify()` + page co-styles `.fancy-select-trigger`
- Status: OPEN (evidence-gathering — Phase A; do NOT promote until all 22 select templates audited)
- Observed in: HTML-001 (`user_create.html`) — both a literal `<select>` and a
  Django widget select, each auto-upgraded by base.html `fancify()`.
- Proposed standard (provisional): the canonical select = write a plain `<select>`
  (native or `{{ form.field }}`), let `fancify()` upgrade it, and have the page/partial
  CSS target **`.fancy-select-trigger` alongside `select`** in the same rule (as
  `_user_form_styles.html` does: `.field input, .field select, .field .fancy-select-trigger { … }`)
  so the trigger matches sibling inputs. Inline `onchange` on the native select still
  fires (fancify dispatches native `change`).
- Required CSS/JS/mobile/a11y: covered by base.html `.fancy-select*` + `fancify()`;
  page only co-styles the trigger; 44px trigger; panel body-anchored fits 320–414;
  keyboard-nav gap = CC-01.
- Promotion: blocked until the Select Family Consolidation Report (after HTML-022)
  confirms this is the dominant/cleanest pattern across all select templates.

---

## Select Family — evidence ledger (Phase A, per Control-Family Discovery Rule)

Evidence only. One row per select implementation encountered. Consolidation Report
produced after HTML-022.

Columns include DEPENDENCY DISCOVERY (CSS owner / JS owner / hidden page-dep).

| HTML | Select variant(s) | CSS owner | JS owner | Hidden page-dep | Mobile | a11y | Browser issues |
|---|---|---|---|---|---|---|---|
| HTML-001 user_create | native `<select name=role>` (inline `onchange`) + `{{ form.user_type }}` widget | shared partial `_user_form_styles.html` (`.field select` + co-styled `.field .fancy-select-trigger`) + base `.fancy-select*` | base `fancify()` + page-inline `updateRolePreview()` | **YES** — role drives inline `updateRolePreview()` via `onchange`; canonicalization must keep native `change` firing | 45px; panel body-anchored fits 320–414; stacks 920/560 | button aria-haspopup; CC-01 gap | none (real-click pick fires `change`; 0 console errors) |
| HTML-002 user_form | native `<select name=role>` (**no** onchange) + `{{ form.user_type }}` widget | same shared partial + base (identical to HTML-001 — confirms `_user_form_styles.html` is the shared select CSS owner for accounts forms) | base `fancify()` only — **no** page-specific select JS | **NO** (selects) — edit form dropped the create's role-preview; selects are pure base-owned | 45px; stacks 920/560; fits 320–414 | button aria-haspopup; CC-01 gap | none for selects (real-click pick sets value; 0 console errors). NB: a separate non-select bug on this page was FIXED — see CC-04 |
| HTML-003 adda_form | `{{ form.product }}` widget (class `sf-input`) | **base.html global `.sf-input`** (class copied onto the `<button>` trigger) + form-shell `_form_styles.html` | base `fancify()` only | **NO** | trigger **39px** (sf-input baseline <44px → CC-05); panel fits 320–414 | button aria-haspopup; CC-01 gap | none (opens/picks/fits; 0 console errors) |
| HTML-004 adda_list | ×2 `<select data-no-fancy>` (status, stage) — **NATIVE** (fancify opt-out) | **page-specific** `.adda-list .filter-card select` (3rd styling owner — not base, not shared partial) | **none** (native; Apply btn, no onchange) | none | native 37px (<44px → CC-07); filter-card stacks ≤600; table data-label stacks | native UA `<select>` picker | none (usable; 0 console errors; no overflow) |
| HTML-005 product_flow | ×9 literal `<select>` (cost_method, cost_billed_at, stage_id) — fancified | **page-tag CSS `.product-flow select` does NOT reach the `<button>` trigger** (class-less) → base `--bare` fallback (PA-14-3 confirmed live) | base `fancify()` only | none | `--bare` **44px** (best touch so far); flow-row collapses ≤600; panel fits; no overflow @9 selects | button aria-haspopup; CC-01 gap | none (picks; 0 console errors) |
| HTML-007 product_patterns_edit | ×1 literal `<select name=pattern>` (inline-`style`d, class-less) — fancified | **inline `style=` on native select does NOT reach the `<button>` trigger** → base `--bare` | base `fancify()` | none | `--bare` **44px**; inline-edit table stacks (PA-15-2); td-actions 1-btn no clip | button aria-haspopup; CC-01 gap | none (picks; 0 console errors) |
| HTML-008 layering_workspace (host of `_stage_panel_layering`) | 9 selects: fc/ft/fw **auto-submit** literal + roll/cloth_*/width_verified_inch widgets — all fancified | mostly fallback `--bare`; width_verified_inch = base `sf-input` | base `fancify()`; fc/ft/fw inline `onchange=this.form.submit()` | fc/ft/fw depend on onchange→submit (survives fancify ✓) | 8×44px `--bare` + 1×39px sf-input; panels fit 320; no overflow | button aria-haspopup; CC-01 gap | none (**auto-submit fires post-fancify**; 0 console errors) |
| HTML-010 _stage_panel_cutting (via cutting_workspace; disposable Adda 3-PATTI-004) | bulk-size + size_id (literal `sf-input`) **browser-verified**; worker_id (sf-input) code-read (deeper per-bundle form) | **base** (`sf-input`) | base `fancify()`; `data-bulk-size`/`data-mselect-take` JS hooks | JS hooks survive fancify | **39px** sf-input (**CC-05 browser-confirmed**); panel fits 320; no overflow | button aria-haspopup; CC-01 gap | none (size_id pick works; 0 console errors) |
| HTML-011 cloth_dashboard | `color` `<select data-no-fancy>` NATIVE (filter) + 2 native date inputs (range, by-design) | **page-specific css** (`.cloth-dash .filter-card select`) | none (native; Apply btn) | none | native **37px** (CC-07); native dates 37px; filter-card stacks ≤600; 2 tables stack | native UA picker | none (usable; 0 console errors; no overflow) |
| HTML-012 roll_bulk_form | cloth_type/storage (sf-input, fancified) + breakup_color (native `data-no-fancy`, JS-cloned rows) + purchased_date (native date) | base `sf-input` (cloth_type/storage); page-css native (breakup_color) | base `fancify()` | breakup_color `data-no-fancy` = **JS-cloned rows** (new reason) | sf-input **39px** · native breakup_color **42px** · native date 43px; form+breakup-row stack ≤600 | button aria-haspopup; CC-01 gap | none (picks; 0 console errors; no overflow) |
| HTML-013 roll_assign_form | adda_code (eligibility picker) + width_inch — Django widget `sf-input`, fancified | base `sf-input` | base `fancify()` | none (adda_code scoped to layering Addas) | **39px** both; form-grid stacks ≤600; panel fits | button aria-haspopup; CC-01 gap | none (adda pick works; 0 console errors; no overflow) |
| HTML-014 roll_edit_form | width_inch + storage_location — Django widget `sf-input`, fancified | base `sf-input` | base `fancify()` | none | **39px** both; native date 43px; form-grid stacks ≤600; panel fits | button aria-haspopup; CC-01 gap | none (storage pick works; 0 console errors; no overflow; in-use warning = good UX) |
| HTML-016 advance_form (money) | `worker` (16-opt Django widget, fancified) | **fallback `--bare`** (class-less; `.expense-form select` tag-CSS bypassed = situation d) | base `fancify()` | none | `--bare` **44px**; **long-list panel max-h 260px + scroll**, fits 320; native date | button aria-haspopup; CC-01 gap | none (worker pick works; 0 console errors; no overflow) |
| HTML-017 settlement_form (money) | `method` (4-opt Django widget, fancified) | **fallback `--bare`** (class-less; `.settle select` tag-CSS bypassed) | base `fancify()` | none (select); **page JS: amount_paid → live preview + submit-gating, see CC-11** | `--bare` **44px**; stat-grid stacks ≤640; native date 42px | button aria-haspopup; CC-01 gap | none (method --bare; 0 console errors; no overflow) |
| HTML-018 category_list (storefront) | `active` filter — `<select class=filter-select>` **fancified + auto-submit** (NOT native, unlike CC-07) | **base.html** (`.filter-select`, class copied) | base `fancify()`; inline `onchange=this.form.submit()` | onchange→submit (survives fancify ✓) | **40px** (new tier, `.filter-select`); `.ke-toolbar` fits 320 | button aria-haspopup; CC-01 gap | none (auto-submit→?active=1; 0 console errors). **DT + td-actions BLOCKED (0 categories → empty-state)** |
| HTML-019 product_form (storefront) | `category` + `badge` (`sf-input`, fancified) | base `sf-input` | base `fancify()` | none (selects) | **39px** (CC-05); selects fine BUT **page clipped at mobile → CC-13** | button aria-haspopup; CC-01 gap | selects CLEAN; **REAL mobile bug CC-13 (croppable widget fixed-width clips form)** |
| HTML-020 product_list (storefront) | `badge` + `active` filters — `.filter-select` fancified+auto-submit (CC-12, 2nd surface) | base.html (`.filter-select`) | base `fancify()`; inline onchange-submit | onchange→submit | **40px**; .ke-toolbar fits 320 | button aria-haspopup; CC-01 gap | selects CLEAN (0 console errors). **DT + td-actions BLOCKED (0 products)** |
| HTML-021 barcode_print_sheet (STANDALONE, no base.html) | `size` + `status` — **NATIVE** (no fancify; base.html absent) + auto-submit | **standalone-doc inline `<style>`** (`.toolbar select`) | **none** (no base.html JS; native onchange-submit) | bypasses fancy ecosystem entirely → CC-14 | native **33px** (smallest); toolbar stacks ≤768; sheet fills 320 | native UA picker | none (?size auto-submit works; 105 stickers; 0 console errors; no overflow) |
| HTML-022 _worker_report_body (chip single-select, via worker_report) | **custom chip-picker** (NOT `<select>`, no fancify) — single-select | **shared partial `_worker_report_styles`** (`.chip`) | inline JS (chip→hidden sync; schema-driven; single-select enforce) | single-select enforced ✓; hidden sync ✓; keyboard-operable ✓ | chip **34px** (<44, worker surface); flex-wrap; mobile tap works | `<button tabindex=0>` chips, **NO radiogroup/aria-pressed** (gap) | none (single-select+sync verified; 0 console errors) |

> Operational note: fancy-select **option** clicks need a real pointer event —
> synthetic JS `element.click()` does NOT trigger the pick (gave a false "value
> unchanged"). Always verify select picks with a real browser click.

> Dependency insight (cross-row): the accounts create+edit forms share ONE select
> CSS owner (`_user_form_styles.html`) + base `fancify()`. The ONLY hidden
> page-specific select behavior found so far is HTML-001's `updateRolePreview`
> (`onchange`). The chip-picker **multiselect** (skills/extra_roles) on BOTH pages
> carries page-inline JS (`.chip-pick input` change → `.is-on`) + view-supplied
> context (`user_skill_ids`/`user_extra_role_ids` for initial checked state) — a
> hidden dependency to carry into any Family-B multiselect canonical.

### Select source-type inventory (SELECT SOURCE TYPE field, owner 2026-06-15)

Inventory only. Categories: Literal HTML select · Django form-widget select ·
Dynamic/AJAX select · Multiselect · Chip-picker · Other.

| HTML | Control | Source type | Interaction model | Fancified? |
|---|---|---|---|---|
| HTML-001 | role | Literal HTML `<select>` | single-select (form) | yes |
| HTML-001 | user_type | Django form-widget select | single-select (form) | yes |
| HTML-001 | skills, extra_roles | Chip-picker (multiselect) | chip-toggle / multi-select | n/a (Family B) |
| HTML-002 | role | Literal HTML `<select>` | single-select (form) | yes |
| HTML-002 | user_type | Django form-widget select | single-select (form) | yes |
| HTML-002 | skills, extra_roles | Chip-picker (multiselect) | chip-toggle / multi-select | n/a (Family B) |
| HTML-003 | product | Django form-widget select | single-select (form) | yes |
| HTML-004 | status, stage | Literal HTML `<select data-no-fancy>` (native) | filter-select (native) | **NO** (opt-out) |
| HTML-005 | cost_method | Literal HTML `<select>` | single-select (form) | yes (`--bare`) |
| HTML-005 | cost_billed_at | Literal HTML `<select>` | single-select (form) | yes (`--bare`) |
| HTML-005 | stage_id | Literal HTML `<select>` | single-select (form) | yes (`--bare`) |
| HTML-007 | pattern | Literal HTML `<select>` (inline-styled) | single-select (form) | yes (`--bare`) |
| HTML-008 | fc, ft, fw (filters) | Literal HTML `<select>` | **auto-submit select** | yes (`--bare`) |
| HTML-008 | roll, cloth_type, cloth_color, width_inch, storage_location | Django form-widget select | single-select (form) | yes (`--bare`) |
| HTML-008 | width_verified_inch | Django form-widget select (`sf-input`) | single-select (form) | yes (sf-input, 39px) |
| HTML-010 | bulk-size, size_id | Literal HTML `<select class=sf-input>` | single-select (form) | yes (sf-input, 39px, **browser-verified**) |
| HTML-010 | worker_id | Literal HTML `<select class=sf-input>` | single-select (form) | yes (sf-input; code-read, deeper per-bundle form) |
| HTML-011 | color (filter) | Literal HTML `<select data-no-fancy>` (native) | filter-select (native) | **NO** (opt-out) |
| HTML-012 | cloth_type, storage_location | Django form-widget select (`sf-input`) | single-select (form) | yes (sf-input, 39px) |
| HTML-012 | breakup_color | Literal HTML `<select data-no-fancy>` (native; **JS-cloned rows**) | single-select (form, dynamic) | **NO** (opt-out) |
| HTML-013 | adda_code, width_inch | Django form-widget select (`sf-input`) | single-select (form; adda_code eligibility-scoped) | yes (sf-input, 39px) |
| HTML-014 | width_inch, storage_location | Django form-widget select (`sf-input`) | single-select (form) | yes (sf-input, 39px) |
| HTML-015 | status, cloth_type, location, color (×4 filters) | Literal HTML `<select data-no-fancy>` (native) | filter-select (native) | **NO** (opt-out: filter behavior) |
| HTML-016 | worker (16 opts) | Django form-widget select | single-select (form, long list) | yes (`--bare`, 44px) |
| HTML-017 | method | Django form-widget select | single-select (form) | yes (`--bare`, 44px) |
| HTML-018 | active (filter) | Literal `<select class=filter-select>` | **filter-select + auto-submit** | yes (`.filter-select`, 40px) |
| HTML-019 | category, badge | Literal `<select class=sf-input>` | single-select (form) | yes (sf-input, 39px) |
| HTML-020 | badge, active (filters) | Literal `<select class=filter-select>` | **filter-select + auto-submit** | yes (`.filter-select`, 40px) |
| HTML-021 | size, status (print sheet) | Literal `<select>` (standalone doc) | **filter-select + auto-submit** | **NO** (no base.html → no fancify; native, 33px) |
| HTML-022 | color_id, size_id (worker report) | **Custom chip-picker** (NOT `<select>`) | **chip-toggle single-select** | N/A (custom, no fancify; 34px chips) |

So far: Dynamic/AJAX select = none · **auto-submit select = HTML-008 fc/ft/fw** (class-less,
`--bare`) **+ HTML-018 active** (classed `.filter-select`) — both fire `onchange=this.form.submit()`
post-fancify · Other = none. **TWO filter-select implementations:** (i) native `data-no-fancy`
(CC-07) · (ii) classed `.filter-select` fancified+auto-submit (CC-12).
Splits observed: (1) **form selects fancify, filter selects stay native** (`data-no-fancy`);
(2) interaction = single-select (form) · chip-toggle multi (Family B) · filter-select (native).

> HTML-006 (`production/product_list.html`) carried **no select** — reclassified to
> Family E (Tables). Surfaced a real `.td-actions` mobile bug → CC-08. (Classification
> error: confused with the storefront product_list which does have filter selects.)

### Visual-owner inventory (VISUAL OWNER field — who controls the RENDERED look)

| HTML | Control(s) | Visual owner |
|---|---|---|
| HTML-001/002 | role, user_type | **shared partial** — `_user_form_styles.html` co-styles `.field .fancy-select-trigger` (+ base core) |
| HTML-001/002 | skills, extra_roles | **shared partial** — `.chip-pick` in `_user_form_styles.html` |
| HTML-003 | product | **base.html** — `sf-input` class copied → global `.sf-input` rule (+ form-shell partial = mixed) |
| HTML-004 | status, stage | **page-specific css** — native `.adda-list .filter-card select` |
| HTML-005 | cost_method/billed_at/stage_id | **fallback** (`--bare`) — page tag-CSS misses the trigger |
| HTML-007 | pattern | **fallback** (`--bare`) — inline-`style` misses the trigger |
| HTML-008 | fc/ft/fw + roll + cloth_* (8) | **fallback** (`--bare`) |
| HTML-008 | width_verified_inch | **base.html** (`sf-input` class) |
| HTML-010 | bulk-size, size_id, worker_id | **base.html** (`sf-input` class) |
| HTML-011 | color (filter) | **page-specific css** (native, `.cloth-dash .filter-card select`) |
| HTML-012 | cloth_type, storage_location | **base.html** (`sf-input`) |
| HTML-012 | breakup_color | **page-specific css** (native, `.bulk-roll-create select`) |
| HTML-013 | adda_code, width_inch | **base.html** (`sf-input`) |
| HTML-014 | width_inch, storage_location | **base.html** (`sf-input`) |
| HTML-015 | status, cloth_type, location, color | **page-specific css** (native, `.roll-list .filter-card select`) |
| HTML-016 | worker | **fallback (`--bare`)** (class-less, `.expense-form select` tag-CSS bypassed) |
| HTML-017 | method | **fallback (`--bare`)** (class-less, `.settle select` tag-CSS bypassed) |
| HTML-018 | active (filter) | **base.html** (`.filter-select` class copied to trigger) |
| HTML-019 | category, badge | **base.html** (`sf-input`) |
| HTML-020 | badge, active (filters) | **base.html** (`.filter-select`) |
| HTML-021 | size, status (print sheet) | **standalone-doc inline `<style>`** (no base.html — native selects) |
| HTML-022 | color_id, size_id (chip-picker) | **shared partial `_worker_report_styles.html`** (`.chip`, custom — not a `<select>` at all) |

Key pattern: the trigger's real visual owner depends on HOW the page reaches it —
by **class** (`sf-input` → base global · `.field .fancy-select-trigger` → partial) it
IS styled; by **tag or inline** it is NOT (falls to `--bare`). Only class-based styling
controls a fancified trigger. Central CC-03/CC-06 finding.

### CC-04 — Template-hygiene: multi-line `{# #}` comments leak as visible text
- Status: OPEN (a recurring, owner-reported regression class — track project-wide)
- Observed in: HTML-002 (`user_form.html:44`) — **FIXED** this audit (→ `{% comment %}`).
  Browser-confirmed the raw `{# … #}` text was rendering on every Edit-User page.
  Also confirmed: `signup_otp.html:74-76` (HTML-032, Family D) — a 3-line `{# … #}`;
  **template-render VERIFIED to leak** (` #}` + comment text renders as visible body text).
  **BUT dormant/unrouted (PA-02-OPEN-SIGNUP) → not user-facing today.** Per owner's dormant-bug
  doctrine (cf. signup throttle-message): **logged, NOT fixed, NOT elevated** — only reachable if
  signup is re-enabled. (HTML-002 was the live instance and was fixed.)
- Rule (already in UI_COMPONENTS.md + feedback memory): `{# #}` is **single-line
  only**; multi-line MUST use `{% comment %}…{% endcomment %}` or Django renders the
  text. Already canon — this is an enforcement/audit-check candidate, not a new component.
- Promotion: no UI_COMPONENTS change needed (already documented). Candidate action =
  a cheap grep guard (`{#` without `#}` on same line) as a per-template audit check.

### CC-05 — `.sf-input` touch-target < 44px (classed fancy-select triggers + native sf-inputs)
- Status: OPEN (global form-baseline candidate — do NOT fix per-page)
- Observed in (browser-confirmed, multiple surfaces): HTML-003 (`adda_form` product) **39px**;
  HTML-008 (`width_verified_inch`) **39px**; HTML-010 (cutting `bulk-size`/`size_id`) **39px**;
  HTML-012 (`cloth_type`/`storage_location`) **39px**; HTML-013 (`adda_code`/`width_inch`) **39px**; HTML-014 (`width_inch`/`storage_location`) **39px**. Native `.sf-input` text probe **41px**. HTML-039 (cutting `pieces_cut` `.sf-input` NumberInput) **41px** — confirms `.sf-input` text/number inputs land ~41px in production form-shell too.
  Affects EVERY `sf-input`-class fancified trigger — a uniform **39px** (the trigger ignores
  page tag-CSS and uses global `.sf-input`, so it's 39px even on bulk-roll where native selects
  are 42px). Native selects' own height is page-CSS-dependent (37px filter-card · 42px bulk-roll).

> data-no-fancy (native opt-out) reasons seen: (1) **filter selects** kept native by choice
> (HTML-004, HTML-011); (2) **JS-cloned rows** — fancify runs only at DOMContentLoaded, so
> `<template>`-cloned selects stay native to avoid half-upgrade (HTML-012 breakup_color). Both deliberate.
- Background: PA-14-3 gave the `--bare` fallback `min-height:44px`, but **classed**
  triggers (`sf-input`) inherit the class height (~39–41px) → below the 44px touch
  standard (owner mobile-first rule). Accounts `.field` triggers are 45px (fine);
  the gap is specific to the `sf-input` baseline.
- Proposed standard: `min-height:44px` on `.sf-input` in base.html (one global rule),
  matching the `--bare` fallback + touch rule.
- Migration impact: every production + storefront form (visual: ~3–5px taller inputs).
- Promotion: GLOBAL change → blocked until the Select/Form Consolidation Report
  quantifies impact + owner approves. Evidence only.

### CC-06 — Select-styling situations across the app (4 so far; consolidation input for CC-03)
- Status: OPEN (evidence — feeds the Select Consolidation Report, NOT a fix)
- Finding: the trigger box gets styled (or not) FOUR different ways so far:
  - **(a) accounts forms** (HTML-001/002) — page/partial co-styles `.field .fancy-select-trigger`
    alongside `.field select` (`_user_form_styles.html`). Tag+descendant rule. Trigger 45px.
  - **(b) production/storefront forms** (HTML-003) — widget carries class `sf-input`;
    `fancify()` copies it to the trigger; base global `.sf-input` styles it. Trigger 39px (CC-05).
  - **(c) filter selects** (HTML-004) — `data-no-fancy` → stays **native**; page-tag CSS
    styles the native `<select>` directly. 37px (CC-07).
  - **(d) styling that misses the trigger → `--bare`** — class-less select styled by
    TAG (HTML-005 `.product-flow select`) OR by **inline `style=`** (HTML-007 `<select style=…>`):
    fancify makes a `<button>`, so tag/inline CSS **misses** it → trigger falls to base
    `--bare` (44px). The PA-14-3 anti-pattern; `--bare` saves it but the intended look is lost.
- Provisional lean: (b) class-based is cleanest IF the class is styled to reach the trigger
  AND meets 44px. (d) accidentally gets the best touch (44px via `--bare`) but loses the
  page's intended select look. Worth a single canonical: class on the select + a styled
  44px trigger rule.
- Promotion: decided in the Select Consolidation Report (after HTML-022), not now.

### CC-07 — Filter-card native selects 37px < 44px (repeated across dashboards)
- Status: OPEN (repeated-pattern candidate — do NOT fix one page)
- Observed (browser-confirmed): HTML-004 (`adda_list`) status+stage = 37px; HTML-011
  (`cloth_dashboard`) color = 37px; HTML-015 (`roll_list`) status+cloth_type+location+color
  (×4) = 37px. The `.filter-card` pattern (page-scoped native-select
  CSS) repeats across ~5 dashboards (roll_list, cloth_dashboard ✓, adda_dashboard,
  tracking/barcode_dashboard per PA-14-2's mobile-stack fix). NB also: native date
  range inputs (`from`/`to`) on these dashboards = 37px too (Family C, native-by-design).
- Background: filter selects are `data-no-fancy` (native) by choice; their page-scoped
  CSS (`padding:9px 12px`) yields ~37px, below the 44px touch standard.
- Proposed standard: a filter-control canonical (min-height 44px on filter selects),
  OR converge filter selects onto the fancy path. Decide in the Filter family (Phase E)
  / Select Consolidation Report.
- Promotion: repeated across pages → family decision, not per-page. Evidence only.
- Related: CC-05 (form `sf-input` <44px). Together = an app-wide control-height theme
  (native filter selects 37px · sf-input 39–41px · only `--bare` got 44px in PA-14-3).

### CC-08 — `.td-actions` action-row overflows off-screen at 320 with many buttons
- **Severity: HIGH**
- **Status: DEFERRED TO FAMILY E** (owner decision 2026-06-15 — do NOT fix during Select audit)
- **Scope: shared base component (`.td-actions`, base.html:974)**
- **Known affected surface: HTML-006** (`production/product_list.html` — 5 action links;
  at 320, base `.td-actions` `flex; justify-content:flex-end; flex-wrap:nowrap` → row ~389px
  in ~296px cell → **Edit (x −97) + Flow (x −35) off-screen left, unreachable**; page-level
  overflow false because clipped past the left edge).
- **Additional affected templates: determine during Family E audit.** Candidate set (uses
  `.td-actions`, verify each at 320): export_list, barcode_dashboard, master_list,
  product_sizes_edit, product_patterns_edit, product_list, skill_list, user_list,
  storefront product_list + category_list. (Worst with ≥4–5 buttons; 2–3 likely fit.)
- Verified data points (from Select audit): **HTML-006** product_list = 5 buttons → FAILS (clips off-screen). **HTML-007** product_patterns_edit = 1 button (Remove) → SAFE at 320 (no clip, 44px). Confirms button-count dependence; Family E must check each by its button count.
- DataTable + td-actions verification was BLOCKED on both storefront lists (0 rows) → **owner seeded 1 category + 1 product (2026-06-15); now browser-VERIFIED:** HTML-018 + HTML-020 DataTables init (search/pagination/DOM-detach, 0 console errors), rows stack to data-label cards at 320, and td-actions = **2 `.action-link`s (Edit/Delete) that FIT at 320** (146→288 within cell 12→308, NOT clipped). → **CC-08 is NOT present on storefront lists** (2 small action-links fit). Confirms CC-08 is **button-count + button-type dependent**: 5 wide `.btn`s (HTML-006) clip; 2 `.action-link`s fit. NB `.action-link` row-actions are **23px** (sub-44 touch — separate pre-existing pattern, both reachable). Family E still owns the base `.td-actions` fix for the failing case (HTML-006-class).
- Proposed fix (Family E only): `flex-wrap: wrap` on the base `.td-actions` mobile rule
  (one line; wrap > clip; right-alignment preserved).
- **Family E procedure (owner-locked):** 1. build the complete `.td-actions` inventory ·
  2. verify every affected template at 320px · 3. apply the base fix only AFTER inventory
  + verification · 4. re-verify ALL affected templates before commit.
- **Narrowed scope (owner 2026-06-15):** CC-08 is NOT a universal td-actions failure. It depends on
  **(1) action count · (2) action width · (3) action style (`.btn` vs `.action-link`) · (4) available
  cell width.** Browser-CONFIRMED on the HTML-006 class (5 wide `.btn`s → clip off-screen);
  browser-REFUTED on the storefront-list class (2 `.action-link`s → fit). Family E ownership unchanged.
- Reason for deferral: family-wide shared-base change → must be handled holistically in the
  Tables Family audit, not patched per-page mid-Select-phase.

### Row-action accessibility observation (NOT a bug, NOT CC-08) — keep separate
- `.action-link` row-actions (Edit/Delete in storefront list td-actions) render at **23px** tall
  (text+icon links). Sub-44 touch target, but both **visible, reachable, and not clipped** at 320.
- Distinct dimensions kept separate per owner: **row-action visibility** (✓ shown) · **row-action
  clipping** (✗ none here = not CC-08) · **row-action accessibility** (23px < 44px touch = this note).
- Pre-existing `.action-link` pattern (many list pages). Evidence only — Family E may consider a
  touch-target floor for row-actions; not a Family-A action, not a bug.

### CC-09 — Auto-submit filter selects survive fancify (VERIFIED EVIDENCE — not a fix)
- Status: VERIFIED EVIDENCE (HTML-008) — input for the filter-select / Select canonical
- Finding: a `<select onchange="this.form.submit()">` (fc/ft/fw layering filters), once
  upgraded by `fancify()`, still auto-submits on pick. Browser-verified live:
  - **native select value updated** (fc → `5`)
  - **`change` event preserved** (fancify dispatches native `change`)
  - **inline `onchange="this.form.submit()"` preserved** (fires → GET submit)
  - **fancify does NOT break auto-submit filters** (URL `?fc=5` applied; trigger label "Black")
- Why it matters: a filter-select canonical can rely on fancify for auto-submit filters —
  no JS change needed to preserve submit-on-change. (Pairs with HTML-001's `updateRolePreview`
  onchange evidence: arbitrary inline `onchange` survives fancify.)
- No action in Family A (evidence only).

### CC-10 — Long-option-list fancy-select: panel caps + scrolls (VERIFIED EVIDENCE — not a fix)
- Status: VERIFIED EVIDENCE (HTML-016) — supporting input for the Select canonical
- Finding: the first long-option-list select (`worker`, 16 opts) — fancy-select panel caps at
  **max-height 260px + internal scroll**, fits the viewport at 1280 AND 320 (panel bottom within
  `window.innerHeight`). So fancify handles long option lists without viewport overflow.
- Why it matters: confirms the canonical select scales to long lists (no per-page handling
  needed). NB still no typeahead/search inside the panel (CC-01-adjacent; a long list is
  scroll-only) — note for future searchable-select consideration, not a Family-A action.
- No action (evidence only).

### CC-11 — Money-form live-preview + submit-gating (NEW interaction model — Family D evidence)
- Status: VERIFIED EVIDENCE (HTML-017) — NOT a select behavior; a form-validation/dependency pattern
- Finding (`settlement_form`): `amount_paid` pre-fills the full payable (₹225); page JS recomputes
  a "Payable after" preview live, shows a ⚠ over-warning when paid>payable, and **disables the
  Confirm button** when paid is over OR ≤0. Verified: 100→"₹125" enabled · 300→"₹-75" warn+disabled ·
  works at 320 (50→"₹175"). Dependency chain: `#amount_paid` input → `recalc()` →
  `{pvPaid, pvAfter, pvWarnRow, settleBtn.disabled}`.
- Why it matters: first **client-side computed-preview + submit-gating** interaction in the audit —
  a reusable money-form pattern (input drives a live invariant + gates submit). Server re-validates
  (JS is UX only). Candidate reference for the **Form-controls family (Family D)**, not Selects.
- No action in Family A (evidence only; surfaced here, belongs to Family D).

### CC-12 — TWO filter-select implementations across the app (NEW — Select/Filter consolidation input)
- Status: OPEN (evidence — distinct from CC-07; feeds Select + Filter family)
- Finding: "filter select" is built two different ways:
  - **(i) native** (CC-07): `<select data-no-fancy>`, page-css owner, **37px**, NO auto-submit
    (explicit Apply button) — raw_materials/production (HTML-004/011/015) in `.filter-card`.
  - **(ii) classed + fancified** (HTML-018): `<select class="filter-select" onchange="this.form.submit()">`,
    base.html `.filter-select` owner (class copied to trigger), **40px**, **auto-submit** —
    storefront in `.ke-toolbar`.
- So the same functional role (filter a list) has divergent: opt-out (native vs fancified),
  visual owner (page-css vs base.filter-select), height (37 vs 40px), submit (Apply vs auto),
  and toolbar idiom (`.filter-card` vs `.ke-toolbar`). A core Filter-family consolidation question.
- Promotion: decided in the Select/Filter Consolidation Report — NOT now. Evidence only.
- NB: storefront DataTable + td-actions could NOT be browser-verified (0 categories → empty-state);
  carry DT/td-actions verification to a storefront list WITH rows.

### CC-13 — Croppable-image widget fixed-width preview clips storefront forms on mobile
- **Classification: SHARED-WIDGET bug / mobile-rendering failure / hidden-content (overflow-x:hidden masking)** — NOT a Select issue, NOT a page bug, NOT a base-component bug. Same failure class as the production audit's "content present but unreachable" (PA-14-1).
- **Severity: HIGH** (real, browser-verified mobile clip; storefront not yet live → lower urgency)
- **Status: DEFERRED** (shared component → Family F / dedicated croppable-widget fix; NOT a Family-A or per-page fix)
- **Scope: shared `croppable_image` widget** — preview box `croppable_image.html:50` has inline
  `style="width:{preview_width}px; …"` (≈400px, **no `max-width`**) → doesn't shrink below ~400px.
- **Known affected surface: HTML-019 `product_form`** — at 320 the widget forces the form column to
  ~450px; `main.content overflow-x:hidden` masks the overflow (so `scrollWidth` reads clean) but the
  form inputs (PRODUCT NAME / CATEGORY / etc.) are **clipped off the right + unreachable** at every
  mobile width (320–414). Browser-confirmed at 320 (screenshot). PA-14-1 clip class.
- **Additional affected — `category_form` (HTML-046) NOW BROWSER-CONFIRMED (2026-06-16):** same shared widget — `.cw-preview-box` measures **400px / right-edge 435px at vw 320**, overflows ~115px, masked by `main.content overflow-x:hidden` (documentElement.scrollWidth reads clean — false-negative trap; found via wide-element scan). **CC-13 GENERALIZES beyond HTML-019 → confirmed SHARED-WIDGET defect** (every croppable consumer clips), NOT a one-page issue. The form's own `.cat-inline-grid` collapses fine; the clip is purely the widget. **2 confirmed occurrences (019 + 046).**
- Proposed fix (deferred): preview box `max-width:100%` (responsive) so it shrinks on mobile; re-verify
  BOTH storefront forms at 320/375/390/414. Crop modal already uses `width:95vw` (responsive) — only the
  inline preview box is fixed.
- Reason for deferral: shared component (mirrors CC-08 td-actions handling); storefront not live.
- The category/badge **selects themselves are CLEAN** (sf-input 39px, CC-05) — CC-13 is a layout bug, not a select bug.

### CC-14 — Standalone-doc selects bypass the fancy-select ecosystem (NEW select context)
- Status: VERIFIED EVIDENCE (HTML-021) — a distinct select context for the Select consolidation
- Finding: `barcode_print_sheet` is a **standalone print document** (own DOCTYPE/head/body, **no base.html**)
  → `window.fancifySelects` is undefined → its `size`/`status` selects are **NATIVE, never fancified**,
  styled by the doc's **own inline `<style>`** (`.toolbar select`, **33px**), and **auto-submit**
  (`onchange=this.form.submit()`, verified → `?size=large`).
- Why it's distinct from CC-07 and CC-12: native here is **not** a `data-no-fancy` opt-out (CC-07) and
  **not** a classed fancify (CC-12) — it's native **because base.html (and thus fancify) is entirely absent**.
  New visual owner (standalone inline `<style>`), new height (33px, smallest), no fancy ecosystem at all.
- Implication for canonicalization: any "all selects are fancy-select" assumption is FALSE for standalone
  docs (print sheets, chromeless embeds). The canonical must acknowledge a **standalone/native lane**.
- No action (evidence only). Print-specific (window.print/@page/@media print) noted; not a select concern.

### CC-15 — Custom chip single-select model (the non-`<select>` selection model)
- Status: VERIFIED EVIDENCE (HTML-022) — a distinct selection model, NOT a `<select>`, NOT fancify
- Finding (`_worker_report_body`, the worker capture surface): schema-driven chip picker —
  `kind='choice'` renders a `.chip-row` of `<button class=chip data-value>` backed by a hidden
  `<input data-key>`; inline JS enforces **single-select** (clear siblings' `.selected` → set this
  + `hidden.value`). Browser-verified: single-select enforced (count=1), hidden sync (color="1"/size="4"),
  rows independent, **keyboard-operable** (focus + Enter selects), mobile chips flex-wrap + tap works.
- **It IS a select-replacement** — functional single-select, hidden input submits the value; the
  touch-first mobile alternative to `<select>` for worker capture (no fancify dependency).
- a11y gap: chips are `<button tabindex=0>` (operable) but lack `role=radiogroup`/`role=radio`/
  `aria-pressed`/`aria-checked` → AT can't convey single-select semantics or selection state.
  Touch height **34px** (<44) on a worker-facing mobile-first surface. (Both notes evidence-only.)
- Consolidation implication: the Select canonical must recognize a **chip single-select lane** distinct
  from `<select>`/fancify — used where touch capture beats a dropdown (worker flows). NOT to be merged
  with the `<select>` lanes; different control entirely. Visual owner = shared `_worker_report_styles`.
- No action (evidence only).

---

# ═══ MULTISELECT FAMILY (Phase B) — evidence (separate from frozen Select evidence) ═══

> ## 🔒 MULTISELECT-FAMILY EVIDENCE FROZEN (2026-06-15)
> Phase B audit COMPLETE — **4 distinct implementations** (CC-16/17/18/20) across 4 domains; all
> ModelMultipleChoiceField/CheckboxSelectMultiple surfaces accounted for (0 native `<select multiple>`).
> CC-16/17/18/19/20 + the Multiselect ledger FROZEN. Synthesis →
> [MULTISELECT_FAMILY_CONSOLIDATION_REPORT.md](MULTISELECT_FAMILY_CONSOLIDATION_REPORT.md).
> Caveat: barcode_gen surface not browser-loaded (no Adda there) — same raw widget as pattern_stage = CC-20.

Phase B audit complete. Same rules: browser-first, evidence only, no fixes/promotion/UI_COMPONENTS.

**Full multiselect inventory (scan 2026-06-15) — bigger than first estimate; ≥4 implementations, 0 native `<select multiple>`:**
1. **`_workers_widget` worker-chip grid** (CC-16 ✓) — `_WorkerMultipleChoiceField`/`_WorkerCheckboxes`; renders on cutting/layering/pattern/barcode-gen stage panels (same widget).
2. **`.chip-pick` grid** (CC-17 ✓) — skills/extra_roles on user_create/user_form (hand-rolled).
3. **stage_form access checkboxes** (PENDING) — `access_by_skill` + `access_by_role` `CheckboxSelectMultiple` (production/views/access_views.py) → HTML-041 (Family D page).
4. **role_form permissions checkboxes** (PENDING) — `permissions` `CheckboxSelectMultiple` (inventory/forms/role_forms.py) → HTML-035.
- Also verify: usertype_form permissions (HTML-034 — mechanism TBD, may be a manual checkbox loop). Display-only skill chips (sidebar_access_list/adda_detail/user_dashboard) are NOT form multiselects — exclude.
- **Conclusion deferred until all ≥4 form-multiselect impls audited** (owner: full inventory before conclusions). 2 done, ≥2 (stage_form, role_form) + usertype_form remain.

### Multiselect evidence ledger

| HTML | Control | Source | Multi? | Visual owner | Touch h | a11y | Hidden deps |
|---|---|---|---|---|---|---|---|
| HTML-023 `_workers_widget` | `.worker-chip` checkbox grid | Django ModelMultipleChoice widget | ✅ (3 checked OK) | shared `_form_styles` `.worker-chip` | **52px** ✅ | **GOOD** (native checkbox in label, Tab+Space) | none (native checkboxes submit directly) |
| HTML-001/002 `.chip-pick` (skills, extra_roles) | `.chip-picker` of `.chip-pick` label+checkbox | hand-rolled template loop over `form.<field>.choices` | ✅ (2 checked OK) | shared `_user_form_styles` `.chip-pick` | **31px** ✗ | **GAP** (checkbox `display:none` → NOT tabbable; no keyboard toggle) | **JS** (`.chip-pick input` change → `.is-on` class; visual depends on JS) |
| HTML-035 `role_form` permissions | **section-grouped CRUD checkbox matrix** (fieldset→model→4-col) + bulk-toggle | `CheckboxSelectMultiple` curated (`perm_sections`), 80 boxes | ✅ (2 checked OK) + section checkall | **page-specific** `role_form .form-section` | **13px** ✗✗ | partial (native checkbox tabbable ✓; CRUD column context likely not per-box) | page-inline JS (section bulk-toggle); native checkboxes |
| HTML-041 `stage_form` access_by_skill/role | `.chip-pick` chip grid (= **CC-17 pattern reused**) | `CheckboxSelectMultiple` (BoundField loop) | ✅ (0→2 confirmed) | **page-specific `.stage-form .chip-pick` (DUP of `_user_form_styles`)** | 34px ✗ | **GAP** (display:none → not tabbable) | JS `.is-on` (page-inline, dup); checkbox display:none |
| pattern_stage + barcode_gen workers (via `_stage_panel_cutting_pattern` HTML-045 / barcode_gen HTML-070) | **Django-default `CheckboxSelectMultiple`** (`<div><label for><input checkbox></label></div>`, UNSTYLED) | raw `forms.CheckboxSelectMultiple` (NOT `_WorkerCheckboxes`) | ✅ (0→2 confirmed, pattern_stage) | **none** (framework default; ambient panel CSS only) | 20px label ✗ | **BEST** (native checkbox + explicit `label[for]=id`) | **none** (no JS; native submit) → CC-20 |

### CC-16 — Checkbox-chip multiselect (`_workers_widget`) — native, a11y-correct
- Status: VERIFIED EVIDENCE (HTML-023) — first multiselect implementation
- Finding: `<select multiple>` is SKIPPED by fancify, so multiselect = a **checkbox-chip grid**
  (`.workers-grid` of `<label class=worker-chip><input type=checkbox>`). Browser-verified: true
  multi-select (3 checked simultaneously), copper-tint `:checked` visual, keyboard (Tab+Space),
  **52px** touch (≥44 ✅), native checkbox semantics (label-wrapped) = **a11y-correct**.
- Distinct from CC-15 (chip *single*-select): CC-15 = custom `<button>` + hidden input + JS single-select
  enforcement, no native semantics (a11y gap); CC-16 = native checkboxes, multi, proper semantics, bigger touch.
- Visual owner = shared `_form_styles.html` (sustainable, class-based). No hidden-input/JS dependency.
- Provisional (for the Multiselect Consolidation Report, NOT now): this is the strong multiselect
  canonical candidate. Compare against the `.chip-pick` impl (HTML-001/002) next before concluding.
- No action (evidence only).

### CC-17 — `.chip-pick` multiselect (skills/extra_roles, HTML-001/002) — hidden-checkbox + JS visual
- Status: VERIFIED EVIDENCE (HTML-001/002, Phase-B revisit) — 2nd multiselect implementation
- Finding: `.chip-picker` of `<label class=chip-pick>` wrapping `<input type=checkbox>` with the
  **checkbox `display:none`**; an inline JS listener toggles a `.is-on` class on change for the
  visual. Browser-verified: multi-select works (2 checked, `.is-on` matches `:checked`), mobile wraps,
  tap works, 0 console errors.
- **Weaker than CC-16 on a11y + touch:** checkbox is `display:none` → **NOT keyboard-focusable/tabbable**
  (keyboard users can't toggle it); **31px** touch (<44); the selected visual **depends on JS** (`.is-on`)
  rather than native `:checked` CSS. CC-16 (`.worker-chip`) has a **visible checkbox, `:checked` CSS,
  52px, tabbable** — a11y-correct without JS.
- **Two multiselect implementations confirmed** (parallel to the Select-family lane split):
  | | CC-16 `.worker-chip` | CC-17 `.chip-pick` |
  |---|---|---|
  | checkbox | visible, tabbable | `display:none`, NOT tabbable |
  | visual | CSS `:checked` (no JS) | JS `.is-on` class |
  | touch | 52px ✅ | 31px ✗ |
  | a11y | native semantics ✅ | keyboard gap ✗ |
  | owner | `_form_styles` | `_user_form_styles` |
- Both are deliberate `<select multiple>` replacements; both multi-select correctly. Divergence in
  a11y/touch/visual-mechanism is the Multiselect-family consolidation question (decide in the report,
  NOT now). No action (evidence only).

### CC-18 — Permission CRUD-matrix multiselect (`role_form`) + mobile-clip finding
- Status: VERIFIED EVIDENCE (HTML-035) — 3rd multiselect implementation (a matrix, not a chip grid)
- Finding: `role_form` renders a **section-grouped CRUD permission matrix** — `CheckboxSelectMultiple`
  (`name=permissions`, 80 native checkboxes) curated into 7 `<fieldset>` sections → model rows → 4
  CRUD columns (view/add/change/delete) + per-section bulk-toggle JS. Multi-select ✓, bulk-toggle ✓,
  keyboard ✓ (native checkbox tabbable), 0 console errors. Distinct from CC-16/CC-17 (those are flat
  chip grids; this is a 2-D matrix).
- **Mobile-clip finding (real, browser-verified):** at 320 the fieldsets are **365px wide** (matrix
  min-content) → clipped ~74px on the right (PA-14-1 class — `overflow-x:hidden` masks, `page_overflow`
  reads false, but the right CRUD columns are cut off + unreachable). The matrix has no mobile
  stack/scroll strategy. **Severity MEDIUM** (admin-only RBAC editor, low blast radius). Page-specific
  layout (role_form; possibly shared with usertype_form HTML-034 if same matrix). Deferred — Phase B is
  evidence-only; fix = Family D / dedicated (stack or horizontal-scroll the matrix at ≤600). NOT fixed.
- Touch: 13px native checkboxes (smallest of any control; the matrix prioritizes density over touch).
- a11y: native-checkbox + fieldset/legend grouping is semantic, but CRUD column meaning is a header row
  (likely not associated per-checkbox) → screen-reader context partial.
- 3 of ≥4 multiselect impls now inventoried. No conclusion until stage_form (HTML-041) + usertype_form
  (HTML-034) audited. No action (evidence only).

### CC-19 — `.chip-pick` multiselect pattern is DUPLICATED across owners (fragmentation)
- Status: VERIFIED EVIDENCE (HTML-041 vs HTML-001/002) — maintainability/consolidation signal
- Finding: the `.chip-pick` chip-multiselect (hidden checkbox + JS `.is-on`, = CC-17) is implemented in
  **≥2 separate owners** with copy-pasted CSS + JS: `_user_form_styles.html` (6 `.chip-pick` rules, user
  skills/extra_roles) AND `stage_form.html` page CSS (7 rules, stage access_by_skill/role) + duplicate
  inline toggle JS in each. Same pattern, no single source.
- `stage_form` is therefore NOT a new implementation — it's **CC-17 reused** for a different domain
  (stage access-control selection), just with its own duplicated styling/script.
- Mobile note: stage_form chip grids **wrap and do NOT clip** at 320 (chips are mobile-safe) — unlike the
  role_form CRUD matrix (CC-18). So the chip-pick pattern is mobile-resilient; the matrix is not.
- Promotion: a single shared chip-multiselect partial would dedupe CC-17+CC-19 — Multiselect-family
  consolidation candidate, NOT now. No action (evidence only).

### CC-20 — Django-default `CheckboxSelectMultiple` worker picker (4th multiselect impl)
- Status: **VERIFIED — COMPLETE (both surfaces browser-confirmed):** pattern_stage/cutting_pattern (browser Phase B + Phase D HTML-045) + **barcode_gen (browser-confirmed HTML-071, 2026-06-16)** — both render the same bare Django-default `<input type=checkbox name=workers>` (native 13px, no chip). The Multiselect-report code-only caveat is **fully closed.** 4th distinct multiselect implementation.
- Finding: `pattern_stage` (cutting-pattern start) + `barcode_gen` worker pickers use a **raw
  `forms.CheckboxSelectMultiple`** (NOT `_WorkerCheckboxes`). `{{ start_form.workers }}` renders
  Django 5's **default** widget: `<div><label for="id_workers_N"><input type=checkbox name=workers></label></div>`
  per option, **UNSTYLED** (no chip, no grid). Browser-verified on pattern_stage (3-PATTI-003).
- Determination (per owner's ask — is it new / variant / default / wrapper?): **Django-default
  implementation.** NOT CC-16 (CC-16 = custom `_WorkerCheckboxes` widget → chip grid), NOT a rendering
  variant of CC-16, NOT a wrapper — it is the framework's untouched default output.
- 10-dim: rendering = Django default `<div><label><input>` (unstyled) · selection = multi (native) ·
  keyboard = ✅ (native, Tab+Space) · SR = **BEST** (explicit `label[for]=id` + native checkbox) ·
  touch = **20px** label (smallest tap of the worker pickers) · mobile = stacks (block), **no clip** ·
  dependency = **none** (no JS) · hidden-vs-native = native visible · CSS owner = **none** (framework
  default) · JS owner = **none**.
- Relationship to CC-16 — **same DOMAIN (worker selection), two IMPLEMENTATIONS:** cutting/layering use
  CC-16 chip grid (styled, 52px); cutting_pattern/barcode_gen use CC-20 Django-default (unstyled, 20px).
  **Accidental inconsistency** — the same "assign workers to a stage" task rendered two completely
  different ways depending on the stage. (Worker-selection consistency = a Multiselect consolidation point.)
- Caveat: `barcode_gen` surface not browser-loaded (no Adda at barcode_gen stage); it uses the identical
  raw widget (code-confirmed) → same Django-default rendering. Implementation characterized via pattern_stage.
- No action (evidence only).

---

## Cross-cutting trackers (NOT consolidated — track occurrences across phases, owner 2026-06-15)

### XC-1 — "content present but unreachable on mobile" (overflow-x:hidden masking) class
Recurring failure: a child is wider than the viewport; `main.content overflow-x:hidden` clips it so
`scrollWidth` reads clean, but the content is cut off + unreachable (no scroll). Occurrences so far:
- **CC-08** — `.td-actions` 5-button row off-screen left (HTML-006). [Family E]
- **CC-13** — croppable-image widget fixed-width clips storefront forms (HTML-019). [Family F]
- **CC-18** — role_form permission CRUD-matrix fieldsets 365px clip right (HTML-035). [Family D]
- **HTML-040** — pattern_form inline `grid-template-columns:1fr 1fr` (no media collapse) → **right column (Code field + Active) clipped past viewport at 320** (code right-edge 479px vs vw 320), masked by `main{overflow-x:hidden}`. Browser+screenshot confirmed. [Family D · also CC-30]
- **HTML-041** — stage_form `.field-grid-2 {grid-template-columns:1fr 1fr}` (page CSS, no media collapse) → **name field (right column) clipped past viewport ≤414** (name right-edge 535px @320), masked by `main{overflow-x:hidden}`. Browser+screenshot confirmed. [Family D]
Same diagnostic class as the production audit's PA-14-1. Do NOT consolidate yet; keep counting across
phases — if it keeps recurring it argues for a global "no fixed-width child inside `.content`" guard.
**5 occurrences now (CC-08/13/18 + HTML-040 + HTML-041).** Sub-pattern emerging: **2-col form grid (`1fr 1fr`) with no mobile collapse** (HTML-040 + HTML-041) — argues for a shared responsive form-grid once Form inventory done.
- **POSITIVE counter-evidence (HTML-039 + HTML-043):** the SHARED `_form_styles.html` `.form-grid` **already has a `@media(max-width:768px)` collapse to 1col** (`_form_styles.html:141`) → cutting_form (039) + product_form (043) use it and **do NOT clip** (browser-confirmed 1col@320). **XC-1 correlates with pages rolling their OWN grid** (040 inline, 041 page-scoped `.field-grid-2`) instead of the shared one. → the fix direction is "use the shared responsive `.form-grid`", not a new guard. Record; no action yet.
- **XC-1 ROOT-CAUSE REFINEMENT (owner 2026-06-16):** XC-1 is **NOT a framework-level / global-layout problem** and **NOT the absence of a global safeguard.** Evidence: SAFE = 039 cutting_form + 043 product_form (shared responsive `.form-grid`) + **045 cutting_pattern panel (auto-fit/auto-fill grids reflow; breakup-table fits)**; BROKEN = 040 pattern_form + 041 stage_form (both roll their OWN independent fixed 2-col grids, both clip). → **XC-1 is primarily caused by BYPASSING an existing responsive shared grid / using FIXED-column layouts.** Auto-fit/auto-fill + shared `.form-grid` + canonical `.table-responsive` all reflow correctly. This strengthens the shared infrastructure as the positive ownership example. Evidence only — no fix/consolidate/promote.

### Selection DOMAINS (distinct from implementations — owner 2026-06-15)
Multiselect spans ≥4 selection DOMAINS, not one bucket: **worker selection** (CC-16) · **skill/tag
selection** (CC-17 user forms) · **stage access-control selection** (CC-17 pattern, stage_form) ·
**permission-matrix selection** (CC-18). Domains ≠ implementations: CC-17's pattern serves 2 domains.
Keep domains and implementations tracked separately in the Multiselect Consolidation Report.

---

# ═══ DATE FAMILY (Phase C) — evidence ═══

> ## 🔒 DATE-FAMILY EVIDENCE FROZEN (2026-06-15)
> Phase C COMPLETE — **2 date implementations** (fancy-date opt-in · native default); all `type=date`/
> `data-fancy-date` surfaces accounted for (0 third-party pickers, 0 standalone-doc dates, 0 auto-submit/
> min-max logic). CC-21 + Date ledger (+ CC-01/CC-02 fancy-date notes) FROZEN. Synthesis →
> [DATE_FAMILY_CONSOLIDATION_REPORT.md](DATE_FAMILY_CONSOLIDATION_REPORT.md) (evidence + recs; NO UI_COMPONENTS change).
> **Owner architectural preference (recorded, NOT a rollout, report §7):** future canonical for single-value
> form dates = **fancy-date** (single source of control); native = documented exceptions (range filters +
> standalone docs) until a future standardization phase. No implementation/migration/UI_COMPONENTS change yet.

Phase C audit complete. Same rules: browser-first, evidence only, no fixes/promotion/UI_COMPONENTS.
**2 date implementations** (completeness scan 2026-06-15; 0 third-party date pickers):
(1) **fancy-date** custom calendar (opt-in `data-fancy-date`) · (2) **native `<input type=date>`** (default).

### Date evidence ledger

| HTML / surface | Impl | Trigger | Visual owner | Touch | Mobile | a11y | JS dep |
|---|---|---|---|---|---|---|---|
| user_form birth_date (HTML-002, Step 0 `7e105b92`) | **fancy-date** (custom body-anchored calendar) | `data-fancy-date` opt-in | base.html `.fancy-date*` (committed) | 44px trigger / 38px day-cells | body-fixed panel, flips, fits 320 | CC-01 gap (no grid keyboard-nav) | base `fancifyDate` |
| HTML-024 adda_dashboard from/to | **native** `<input type=date>` | none (UA) | page `.adda-dashboard .filter-card` | 37px | filter stacks, OS picker | native (good) | none |
| HTML-025 barcode_dashboard from/to | **native** `<input type=date>` | none (UA) | page `.bc-dash .filter-card` | 37px | filter stacks, OS picker | native (good) | none (no onchange/min/max) |
| (Phase A seen) cloth_dashboard from/to (HTML-011) · roll purchased_date (012/014) · advance_date (016) · settlement_date (017) | **native** | none | page-css / sf-input | 37–43px | native | native | none |

### CC-21 — Native `<input type=date>` is the default date implementation
- Status: VERIFIED EVIDENCE (HTML-024 + Phase-A surfaces) — the default date lane
- Finding: every date control EXCEPT user_form birth_date is a plain native `<input type=date>` (no
  fancify): dashboard range filters (adda/cloth/barcode) + form dates (purchased/advance/settlement).
  Heights 37–43px (page-CSS-dependent, same as native selects). Native picker, native a11y, no JS.
- Intentional: dashboard date-RANGE filters are deliberately native (UI_COMPONENTS); fancy-date is opt-in
  for single-value fields. So native is the by-design default, NOT a gap.
- Known tradeoff (the reason fancy-date exists): desktop Chromium only the icon is clickable; native popup
  mispositions under transformed ancestors. Accepted for range filters; fancy-date opt-in fixes single fields.
- Relationship to fancy-date: same DOMAIN (pick a date), two implementations — native (default, range
  filters + most form dates) vs fancy-date (opt-in custom, only birth_date). 1 opt-in consumer so far.
- No action (evidence only). Consolidation (which date fields, if any, should adopt fancy-date) = the
  Date Consolidation Report after the family is audited.

---

# ═══ FORM-CONTROL FAMILY (Phase D) — evidence ═══

Phase D in progress. Same rules: browser-first, evidence only, no fixes/promotion/UI_COMPONENTS.
Scope: text/number/textarea/checkbox/radio + **validation rendering**. (Select/multiselect/date already
done in A/B/C — not re-audited here.) Capture per form: form system · control types · validation rendering ·
keyboard/a11y · touch · mobile · CSS owner · JS owner.

**Form-SYSTEMS scan (2026-06-15) — multiple (mirrors the Select multi-owner story):**
- `.field` (accounts + production) — ~23 templates.
- `.sf-*` (`.sf-field`/`.sf-input`, storefront forms).
- `form-shell` / `.form-shell` (production) — ~26 templates.
- generic `{% for field in form %}` loop (expense: advance/settlement forms).
- **standalone auth** (no base.html; own inline styles) — the auth set (forgot/login/otp/signup…).

**VALIDATION-rendering scan — multiple patterns:** `.field-error` (16) · `.sf-error` (3) · `.form-error`/`.form-errors`
(12) · `messages`/`.alert` banners (24) · `.flash` (2) · per-field `{% for e in field.errors %}` loops
(signup, user_form). Inventory which form uses which before any conclusion.

> ## 🔒 FORM-CONTROL EVIDENCE FROZEN (2026-06-16)
> Form-Control input inventory complete (026-048 + 070/071 + confirm-dialog rep). Findings kept SEPARATE:
> CC-22/23/24 (auth) · CC-30A/30B · XC-1 (×5) · CC-13 (×2) · CC-28 + CC-05/16/17/19/20/25/26 + validation-families
> + workflow-protection trackers. Fixed+committed: CC-27 `20fccbd7`, CC-29 `2e5910b9`. Synthesis →
> [FORM_CONTROL_CONSOLIDATION_REPORT.md](FORM_CONTROL_CONSOLIDATION_REPORT.md). No promotion / no standardization
> until owner decision asks (report §7). Next family: E — Tables.

### Form-control evidence ledger

| HTML | Form system | Control types | Validation rendering | Touch | a11y | CSS owner | JS owner |
|---|---|---|---|---|---|---|---|
| HTML-026 forgot_password | standalone auth | email | `.alert` messages banner (form-level, **no per-field**) | 46–47px ✅ | good (`label[for]`, required, autocomplete) | standalone inline (own copy) | none |
| HTML-027 login | standalone auth (split-screen) | email | `.alert-item` messages banner (form-level, **no per-field**) | 49px ✅ | good (`label[for]`, required, autocomplete, filled-state) | standalone inline (**own `.field` copy**) | minimal (Google onclick) |
| HTML-028 login_password | standalone auth (split-screen) | email + password | `.alert` messages banner (form-level, **no per-field**) | 47px ✅ both | good (`label[for]` both, required) | standalone inline (**own `.field` copy** — copy of login w/ drift) | minimal |
| HTML-029 otp (render BLOCKED — flow-gated; code-read) | standalone auth | 6× `.otp-digit` (numeric, maxlength=1) + hidden | `.alert` messages (no per-field) | 52px ≤480 (code) | numeric inputmode; step chips; btn-verify-disabled-until-6 | standalone inline (own copy) | **page-inline OTP controller (own copy → CC-23 3-copy dup)** |
| HTML-030 reset_otp (render VERIFIED — reachable) | standalone auth | 6× `.otp-digit` (numeric) **+ new_password** (combined) | `.field-error` (pw) + `.alert` messages | OTP 63px/52px ✅, pw 44px ✅ | numeric; auto-advance ✓; **paste-fill ✓**; **NO countdown/resend = CC-23 drift (browser-confirmed)** | standalone inline (own copy) | **page-inline OTP controller (own copy, REDUCED) → CC-23** |
| HTML-031 signup (render BLOCKED — DISABLED/unrouted; code-read) | standalone auth (split-screen) | email + password + confirm_password | **`form.errors` top-aggregated** (`field.errors` + `non_field_errors` → `.alert-error`); **NO messages block → CC-24 outlier + latent invisible-throttle bug** | n/a (unrouted) | good (`label[for]`); top-block errors not inline | standalone inline (own copy) | none |
| HTML-032 signup_otp (render BLOCKED — DORMANT/unrouted; template-render-verified) | standalone auth | 6× `.otp-digit` (numeric) — **FULL OTP** (countdown+resend+auto-submit) | **messages framework ONLY** (`form.errors`=False) → **follows OTP family, NOT signup → CC-24 isolated to signup.html** | OTP 64px/52px ✅ (code) | numeric; auto-advance/paste/arrow/auto-submit (render-confirmed) | standalone inline (own copy) | **page-inline OTP controller (own copy, FULL) → CC-23.** Also `{# #}` leak @74-76 (CC-04, dormant) |
| HTML-033 skill_form (browser-VERIFIED) — **management, extends base.html** | `.field` + `.panel` form-shell + `.user-hero` (mgmt shell, NOT auth) | label·name(+slug `pattern`)·description = 3 text/textarea (no select/date/multiselect) | **per-field inline `.field-error`** (browser-confirmed: dup-name → "…already exists.") + `non_field_errors` + native required; **⚠ native `pattern` BROKEN → CC-27** (`v`-flag SyntaxError, console err, constraint dropped) → **3rd validation pattern (mgmt), shared via `_user_form_styles.html`** | inputs **45px** ✅; **submit `.btn-primary` 39px <44px** ⚠ | good (`label[for]` all); native required OK, **pattern broken (CC-27)** | **SHARED `_user_form_styles.html`** (same as user_create/user_form — positive shared owner) | page-inline preview-chip only (label→chip); no select JS |
| HTML-036 adda_settlement_detail (finalized browser-VERIFIED; draft code-read) — **expense, extends base.html, money actions** | expense-app inline (`.panel`/`.totals`/`.sticky-bar`) + **borrows `.sf-input`/`.field`** for override textarea | DRAFT: variance + recover **number inputs** (native min/max/step) · `reconciliation_override` textarea · finalize/discard btns · FINALIZED: `notes` textarea + reverse/supersede btns; money `.table-responsive`+data-label | **action-form** (raw POST `name=action`, NOT ModelForm) → errors via **messages framework** on redirect; client = `confirm()` + native numeric → **4th validation/interaction family** | `notes` textarea 56px ✅; **reverse `.btn-danger` 40px @414 <44px** ⚠ CC-25 | native number min/max/step; confirm() guards | **expense-app inline** (own) + cross-borrows `.sf-input`/`.field` | none (server-action form; no client JS beyond confirm) |
| HTML-037 worker_profile_form (browser-VERIFIED) — **expense, extends base.html, page-scoped** | **page-scoped `.expense-form`** (extra_head; NOT shared partial / NOT sf / NOT auth / NOT 036-inline) | 9 fields: phone·bank name·bank acct·IFSC·UPI·**native `type=date`**·opening_advance(number min=0)·is_active·notes | **generic `{% for field in form %}` loop** + per-field `.errs` + `non_field_errors`; **server-side cleans** (IFSC/acct/bank-set/advance≥0); client = native number min=0 (verified) + native date → **5th family (generic-loop, page-scoped)** | inputs 40px; save `.btn-copper` 40px (<44px) ⚠ CC-25 | native min=0 (−5 rejected ✓); no HTML pattern (no CC-27 risk) | **page-scoped `.expense-form`** (own; expense app's 2nd distinct form-CSS approach) | none (no client JS) |
| HTML-038 adda_report_review (browser-VERIFIED, GET-only) — **production, extends base.html, money-adjacent** | **page-scoped `.report-review`** (extra_head; NOT shared / NOT sf) | per-row **verified number input** (min=0 step=0.01); **settled rows LOCKED → text not input** (server-state guard); empty-state | **raw-POST bulk-save** (no Django form) → messages on redirect; client = native number min=0 (verified neg-rejected) + **server-state row-lock** → **6th family (raw-POST bulk + native-numeric + state-lock)** | verified input **34px** (smallest yet, <44px) ⚠ CC-25 | native min=0 (−3 rejected ✓); settled-line lock | **page-scoped `.report-review`** (own; production's form-CSS) | none (no client JS) |
| HTML-039 cutting_form (browser-VERIFIED, GET-only) — **production form-shell, SHARED owner** | **SHARED `production/_form_styles.html`** (`.form-shell`/`.hero`/`.panel`) + borrows `.sf-input` | pieces_cut (number min=1, `.sf-input` 41px) · notes (Textarea `.sf-input`) · **workers = CC-16 chip** (12 @52/44px) | **Django Form** render, per-field `.field-error` + top `.form-error`, **novalidate → server-side**; CC-16 multiselect → **7th family (production form-shell per-field-inline, shared owner, novalidate)** | **worker-chip 44-52px ✅**; pieces_cut **41px → CC-05**; btn-primary **38px → CC-25** | native min=1 present but novalidate (server enforces) | **SHARED `production/_form_styles.html`** (positive shared owner #2, after mgmt) + `.sf-input` borrow | none page-specific (CC-16 chip = native checkboxes) |
| HTML-040 pattern_form (browser-VERIFIED) — **production, base `.form-card`, ⚠ 3 findings** | **base.html global `.form-card`/`.form-section`** (3rd shared form-CSS; base-owned) | code·name (text, req) · description (Textarea) · reference_image (file) · is_active (checkbox) | **⚠ field-error SWALLOW (CC-29 — FIXED)** — was only `non_field_errors`; fix added per-field `.form-error` (verified). novalidate → server-side | **⚠ name input 19px bare (CC-30A — no `.form-control` class)**; btn 38px (CC-25) | native validation off (novalidate, no `.form-control`); **⚠ 2-col grid clips right col on mobile (CC-30B/XC-1)** | **base.html `.form-card`** but widgets lack `.form-control` → unstyled | none |
| HTML-041 stage_form (browser-VERIFIED, GET-only; Phase B chips + Phase D full) — **production, page-scoped** | **page-scoped `.stage-form`** (own `.field-grid-2`/`.chip-pick`/`.errors`) | code·name (**manual** text, req+maxlength, cream **39px**) · description (Textarea) · is_active · **access_by_skill/role = CC-17/CC-19 chips** | top `.form-alert` + **per-field `.errors` (code/name) — NO swallow** (contrast 040); native required+maxlength (no novalidate) | code/name **39px** (CC-05); chips 34px (CC-17) | native required+maxlength ✓; **⚠ `.field-grid-2` clips name on mobile (XC-1 5th)** | **page-scoped `.stage-form`** (+ `.chip-pick` dup of `_user_form_styles` = CC-19) | page-inline chip-toggle JS (CC-19 dup) |
| HTML-042 stage_rate_correct (form-branch browser-VERIFIED; settled branch code-only) — **production, MONEY-workflow** | **SHARED `production/_form_styles.html`** + page-scoped `.rate-correct` | new_rate (number step=0.0001, `.sf-input` 41px) · reason (Textarea, mandatory) · confirm (checkbox gate) · readonly current-strip | top `.form-error` + **per-field `.field-error` — NO swallow**; novalidate→server; **MONEY-ARMOR: settled→`.settled-note` + submit `disabled` + server `_is_settled` refuse + RateCorrectionAudit** (code-verified) | new_rate **41px** (CC-05); btn **38px** (CC-25); confirm 20px | native number; **`.form-grid cols-1` → NO XC-1 ✓**; before-settlement-only | **SHARED `production/_form_styles.html`** (reuse, positive) + page-scoped `.rate-correct` | none (Django form; no client JS) |
| HTML-043 product_form (browser-VERIFIED) — **production, SHARED owner; POSITIVE** | **SHARED `production/_form_styles.html`** + `.sf-input` | code·name (text, req, `.sf-input` 41px) · description (Textarea, full) | top `.form-error` + **per-field `.field-error` — NO swallow** (live: 2 "required" shown, no create); novalidate→server | code/name **41px** (CC-05); btn ~38px (CC-25) | **shared `.form-grid` collapses ≤768 → 1col@320, NO XC-1 ✓** (positive counter-example) | **SHARED `production/_form_styles.html`** (3rd consumer; positive) | none |
| HTML-044 product_sizes_edit (browser-VERIFIED, GET-only) — **production, inline-edit table** | **page-scoped `.ps-edit`** + canonical `.table-responsive`/`data-label` | inline-edit per-row: label (text req max40, 29px) + display_order (number min0, 29px); add/archive/reactivate forms | **raw-POST per-row action forms** (update/archive/add/reactivate) + native (req/max/min) + `confirm()`; messages on redirect | inline inputs **29px** (CC-05, smallest styled) | native req/max/min; `confirm()` archive guard | **page-scoped `.ps-edit`** (table editor; uses canonical `.table-responsive`) | none (raw-POST forms) |
| HTML-045 _stage_panel_cutting_pattern (browser-VERIFIED, GET-only) — **production cutting-pattern panel (526-line partial)** | **mix:** wrapper includes `_form_styles.html` + partial's OWN inline `<style>` + `.sf-input` | **workers = CC-20 bare checkboxes (13px)** · video/photos (file `.sf-input`) · notes/caption (`.sf-input`) · `.breakup-table`+data-label · auto-fit grids · raw-POST action forms | raw-POST per-section action forms + `confirm()` + native (file accept/required); no per-field render | worker checkbox **13px** (CC-20, tied-smallest); sf-input ~41px | native; auto-fit grids reflow → **no XC-1**; breakup-table fits @320 | mix (`_form_styles` + own inline + sf-input) | none (raw-POST; CC-20 native checkboxes) |
| HTML-047 master_form (browser-VERIFIED) — **raw_materials, SHARED owner cross-app; positive** | **SHARED `production/_form_styles.html`** (4th consumer, cross-app) + `.sf-input` | generic loop: name + hex_code (text `.sf-input` 41px, `pattern ^#[0-9A-Fa-f]{6}$` vOK/not CC-27) | top `.form-error` + per-field `.field-error` (loop) — **NO swallow** (live: 1 "required", no create); novalidate→server | `.sf-input` **41px** (CC-05); btn ~38px (CC-25) | shared `.form-grid` collapses ≤768 → 1col@320, **NO XC-1 ✓** | **SHARED `production/_form_styles.html`** (cross-app reuse; positive) | none |
| HTML-070/071 barcode_gen workspace+panel (browser-VERIFIED, GET-only) — **production; closes CC-20** | host includes `_form_styles.html` (6th consumer) + panel own `<style>` + sf-input | raw-POST forms (reopen/start/generate/complete) + **`{{ start_form.workers }}` = CC-20 bare 13px** + barcode tables (data-label) + auto-fit grid | raw-POST action forms + native; no per-field render | worker checkbox **13px** (CC-20) | barcode tables stack (tr→block) @mobile; auto-fit reflows → **no XC-1** | shared `_form_styles.html` + own `<style>` | none (raw-POST; CC-20 native) |
| HTML-048 pattern_workspace (browser-VERIFIED, GET-only) — **HOST wrapper for 045 panel** | base + includes `_form_styles.html` (5th consumer) + **host-local PA-15-3 breakup `<style>`** + inline hero | NONE new (hosts the 045 panel: workers CC-20 / sf-input / breakup-table) | inherits 045 (no host controls) | inherits 045 (CC-20 13px etc.) | **PA-15-3 breakup-table stacks ≤600 (tr→block/td→flex/data-label::before) — VERIFIED, no clip** | thin host layer: inline hero + host-local breakup-stacking (dup of embedded path; ≥2 owners) | inherits 045 |
| HTML-046 category_form (browser-VERIFIED) — **storefront; CC-13 reproduces** | base-global `.sf-input`/`.sf-error` + page-scoped `.cat-*` | name·subtitle·item_count_label (text `.sf-input` 39px) · display_order (number) · is_active (checkbox toggle) · **image = CroppableImageWidget (CC-13)** | top `.form-errors` list + per-field `.sf-error` (markup) + **native required** (blocks empty, browser-confirmed); NO swallow | `.sf-input` **39px** (CC-05); checkbox toggle | `.cat-inline-grid` collapses ≤media → no XC-1 in layout; **⚠ CC-13 `.cw-preview-box` 400px clips @mobile (right 435@320, masked)** | base-global `.sf-*` (shared) + page-scoped `.cat-*` | croppable widget JS | ⚠ **audit-induced stray category id2 (unresolved)** |

> ## 🔒 AUTH-FAMILY EVIDENCE FROZEN (2026-06-16)
> Auth inventory complete (HTML-026…032). CC-22 (form-system) · CC-23 (OTP-widget) · CC-24 (validation)
> + CC-04 (comment leak, dormant) FROZEN — boundaries stable, kept SEPARATE (not merged).
> Synthesis → [AUTH_FAMILY_CONSOLIDATION_REPORT.md](AUTH_FAMILY_CONSOLIDATION_REPORT.md). No changes /
> no UI_COMPONENTS promotion until owner decision asks (report §9) are answered.

### CC-22 — Auth-cluster form-system DUPLICATION (ownership fragmentation)
- Status: OPEN — FROZEN 2026-06-16 (evidence — Form-control / ownership-fragmentation; auth inventory complete)
- Finding: each auth page carries its **own local copy** of the `.field` form system + `.alert` validation
  styling, standalone (no base.html). Confirmed: forgot_password (HTML-026) + login (HTML-027) each define
  `.field` + `.alert*` inline, distinct from base, `_user_form_styles`, AND from each other (SEED drift:
  login input border `#b8a48e`/Inter font vs siblings' `--cream-2`/Syne). Same class of finding as CC-19
  (chip-pick duplication) — multiple owners for one pattern.
- **Share-vs-copy DETERMINATION (CONFIRMED — structural scan of all 7 auth pages, 2026-06-15):**
  every auth page has **`extends` = NONE · `include` = NONE · its OWN local `<style>` block · its OWN
  local `.field`/`.alert` rules** (login 15 · login_password 13 · otp 6 · reset_otp 10 · signup 10 ·
  signup_otp 4 · forgot_password 10). → **COPY-PASTED separate copies — NOT a shared foundation, NOT
  partial-share.** 7 independent owners of one conceptual auth form system, with drift. This is the
  enterprise-architecture concern branch (not the "shared base, cosmetic-only diff" branch).
- Scope: all 7 auth pages — forgot ✓ · login ✓ · login_password ✓ (028) · otp (029) · reset_otp (030) ·
  signup (031) · signup_otp (032). Browser-audited so far: 026·027·028; structural scan covers all 7.
- Validation sub-finding: auth = **messages-only** (`.alert` banner, no per-field errors) — except signup
  (031) which uses a per-field `form.errors` loop (the one divergent validation in the cluster, per Phase-A SEED).
- No action (evidence only). Consolidation (shared auth form partial) = Form-control / auth decision after the family.

### CC-23 — OTP widget JS duplication (3 inline copies, behavioral drift) — hidden fragmentation
- Status: OPEN (evidence — code-confirmed; render browser-blocked. Sub-finding of the auth-family fragmentation)
- Finding: the 6-box OTP entry widget (6 `.otp-digit` numeric inputs + hidden field + JS controller:
  sync/auto-advance, keydown/backspace, paste-fill, autofocus, 60s resend countdown, btn-verify gating)
  is **duplicated inline in all 3 OTP pages with NO shared partial** — otp.html (21 JS hooks) ·
  signup_otp.html (22, full) · **reset_otp.html (7, REDUCED — missing the countdown/resend/auto-submit
  the others have = behavioral drift)**. 3 copies of one widget; one is feature-incomplete.
- Why it matters (owner's hidden-JS-fragmentation interest): this is a duplicated JS WIDGET, not just CSS —
  bug fixes, a11y, paste/keyboard behavior must be maintained in 3 places, and reset_otp already drifted
  (fewer features). A classic hidden frontend-fragmentation source.
- Ownership: CSS + JS owner = **per-page inline (own copy)** for each of the 3. No shared OTP component.
- Render evidence (update HTML-030): **reset_otp.html IS reachable** (`/app/reset-password/verify/` renders
  directly, not flow-gated) → the OTP-widget **render is browser-VERIFIED via reset_otp**: 6 boxes 63px/52px,
  numeric, **auto-advance ✓, paste-fill ✓**, and **NO countdown/resend element in the live render** = the
  CC-23 behavioral drift, **browser-confirmed**. otp.html (`/app/verify-otp/`) + signup_otp remain
  flow-gated/dormant (render not loaded), but they share the same widget family (code-confirmed) and reset_otp
  is the render proxy. So CC-23 is now: structural dup (3 copies) **+ browser-confirmed drift** (reset_otp reduced).
- Drift now fully mapped (HTML-032, template-render-confirmed): the 3 copies = **2 FULL (otp.html + signup_otp.html: countdown + resend + auto-submit) + 1 REDUCED (reset_otp.html: none of those)**. signup_otp render-confirmed FULL (6 otp-digit, `id=countdown`, `id=resendLink`, `form.submit()` auto-submit). reset_otp is the lone feature-incomplete copy. All 3 = own inline JS, no shared partial.
- Relationship to CC-22: CC-22 = auth FORM-system duplication (`.field`/`.alert`, 7 copies); CC-23 = the
  auth OTP WIDGET duplication (JS, 3 copies). Same fragmentation theme, different layer (CSS vs JS widget).
- No action (evidence only).

### CC-24 — Auth validation fragmentation (two competing validation strategies in auth) — confirmed
- Status: OPEN (evidence — code-confirmed; signup render-blocked/unrouted, but the divergence is grep-proven).
- Type: **Frontend Validation Fragmentation** · Layer: **error-rendering ownership** (per owner: distinct from
  CC-22 form-system + CC-23 OTP-widget — do not merge).
- Finding: the auth cluster surfaces form validation **two different ways**:
  - **Strategy A — `form.errors` (signup.html ONLY):** `{% if form.errors %}` → `{% for field in form %}{% for error in field.errors %}` + `non_field_errors`, rendered as `.alert-error` blocks **at the top** of the form (not inline per-field). signup.html:108-113.
  - **Strategy B — Django messages framework (every OTHER auth page):** login · login_password · forgot_password · reset_otp · otp · signup_otp all render `{% for message in messages %}` and rely on the view pushing `messages.error/success`; **0 `form.errors`**.
  - Grep proof (7 auth pages): signup = messages-fw **0** / form.errors **3**; all 6 others = messages-fw **1** / form.errors **0**. signup is the **sole** `form.errors` page.
- Why it matters: same family, two validation contracts → no single error-rendering owner; a dev fixing
  validation display must know which page uses which. signup is the outlier the owner predicted.
- **Latent bug (dormant):** signup.html has **no messages block**, yet `SignupView` (views.py:448) calls
  `messages.error()` on throttle → that message is **invisible** if signup is re-enabled. Logged, not fixed
  (signup unrouted = PA-02-OPEN-SIGNUP; surfaces only at re-enable).
- Ownership: per-page (each auth page owns its own validation render; no shared error component) — same
  per-page-ownership root as CC-22/CC-23.
- Auth-family picture now: **CC-22** (form-system dup, 7 owners) · **CC-23** (OTP-widget dup, 3 copies + drift) ·
  **CC-24** (validation strategy split, A vs B). Three distinct fragmentation findings, one family.
- **Scope locked (HTML-032, render-confirmed):** signup_otp.html (step 2 of the signup flow) uses the **messages framework**, NOT `form.errors` — so the signup FLOW is internally split (step 1 form.errors → step 2 messages). The `form.errors` strategy is therefore **isolated to signup.html ALONE** — a single page across the entire auth surface. Every other auth page (incl. signup's own OTP step) = messages. CC-24 = **one-page outlier**, not a flow-wide pattern. (This is the split-evidence the owner asked for.)
- No action (evidence only). **Auth-family inventory now COMPLETE** (026·027·028·029·030·031·032). Auth findings = CC-22 (form-system, 7 owners) · CC-23 (OTP-widget, 2-full+1-reduced) · CC-24 (validation split, signup.html-isolated). Ready for owner decision: Auth Consolidation Report or not.

### CC-25 — Form/Button touch-target: `.btn-primary` < 44px (SEPARATE from CC-05)
- Status: OPEN (evidence — Form/Button-family touch-target signal; owner-directed 2026-06-16: **do NOT merge into CC-05**).
- Finding: the management form submit `.btn-primary` measures **39px** (browser, HTML-033 skill_form, all viewports 320-1280) — below the 44px touch minimum.
- **Why separate from CC-05:** CC-05 = `.sf-input` / fancy-select-trigger **input** height (39px). CC-25 = **button** height. Select-height and button-height are **distinct concerns** with distinct owners; owner explicitly wants them tracked apart. Same numeric value (39px) ≠ same root cause.
- Observed: HTML-033 (`.btn-primary` 39px, all viewports) · HTML-036 (`.btn-danger` reverse = **40px @414**, varies 68px@320 wrap→40px@414) · HTML-037 (`.btn-copper` save **40px** + inputs 40px) · HTML-038 (verified **number input 34px**) · HTML-040 (`.btn-primary` 38px + **name input 19px bare** — see CC-30A) · HTML-041 (stage_form code/name inputs **39px**, chips 34px) · HTML-042 (new_rate `.sf-input` 41px, btn 38px, confirm checkbox 20px) · HTML-043 (code/name `.sf-input` 41px) · HTML-044 (inline-edit label/order **29px** — smallest styled input) · HTML-045 (CC-20 worker checkbox **13px** native — tied-smallest tap with role_form CC-18) · HTML-046 (storefront `.sf-input` 39px) · HTML-047 (`.sf-input` 41px). To be widened as more `.btn`/input surfaces are audited (build the touch-height inventory across Family D before any recommendation).
- No action (evidence only; per-page fix forbidden — button-family touch is a baseline concern, future standardization phase).

### CC-27 — BUG: HTML `pattern` attr invalid under Chromium `v`-flag (leading `-` in char class)
- Status: **FIXED + browser-verified + COMMITTED `20fccbd7` (2026-06-16).** Discovered during HTML-036.
- **FIX APPLIED:** `accounts/forms.py:28 + :43` → `r'[a-z0-9_\-]+'` (escaped dash). **⚠ Deviation from owner's literal spec:** owner approved `[a-z0-9_-]+`, but browser testing showed **that also fails `v`-mode** (a *trailing* `-` is likewise illegal in unicodeSets) — only the **escaped** `\-` compiles. Same char set (lower/digit/underscore/hyphen), so behavior-identical to intent. Verified: skill_form name + usertype code → `new RegExp(p,'v')` compiles; anchored `checkValidity()` accepts `stitching_master`/`with-hyphen`/`franchise_owner`, **rejects** `Bad Slug!`/`BAD CODE`; **no new console SyntaxError** (pre-fix 18:55/19:04/19:11 errors are history). Native slug validation RESTORED.
- Finding: two management slug fields use `pattern=r'[-a-z0-9_]+'` — **accounts/forms.py:43 (SkillForm.name, skill_form HTML-033)** + **accounts/forms.py:28 (UserTypeForm.code, usertype_form HTML-034)**. Modern Chromium compiles the HTML `pattern` attribute with the **`v` (unicodeSets) flag**, where a **leading unescaped `-` in a character class is a SyntaxError**. Browser-confirmed: `new RegExp('[-a-z0-9_]+','v')` THROWS "Invalid character in character class" (`'u'` flag is fine); skill_form's `checkValidity()` logs `Uncaught SyntaxError: /[-a-z0-9_]+/v: Invalid character in character class` (live, ts 19:04).
- Impact: (1) **console error** on every validity check; (2) **native pattern validation is silently dropped** → the slug constraint does NOT enforce client-side (any input passes the pattern check; only server-side `clean`/model validation, if any, would catch a bad slug).
- Fix (NOT applied): reorder dash to end → `r'[a-z0-9_-]+'` (or escape `r'[\-a-z0-9_]+'`) — valid in both `u` and `v` mode, identical semantics. Two one-line edits.
- Scope bound (grep): only these 2 `pattern` attrs have a leading-dash class; `raw_materials/forms/master_forms.py:44` hex pattern `^#[0-9A-Fa-f]{6}$` is unaffected. So **exactly 2 instances**.
- Honesty note: HTML-033 was first reported "0 console errors / native pattern confirmed" — RETRACTED; the initial console read pre-dated the validity trigger. Corrected in the HTML-033 ledger record.

### CC-28 — App-wide: missing favicon → `/favicon.ico` 404 on every page (cosmetic)
- Status: OPEN (evidence — app-wide cosmetic; discovered HTML-037).
- Finding: `base.html` declares **no `<link rel="icon">`**, and `/favicon.ico` returns **404** → browsers that auto-request the favicon log one `[error] Failed to load resource: 404` on **every** page. Confirmed: curl `/favicon.ico`→404; base.html has no favicon link; exactly 1 fresh 404 per isolated page load.
- Impact: **cosmetic only** — a console-noise 404, no functional effect, no missing UI. App-wide (not page-specific).
- Honesty note re earlier pages: earlier units used `console --errors` which did not surface resource-load 404s; `console` (all) does. The favicon 404 was present app-wide all along — not a regression and not a per-page bug.
- No action (evidence only; trivial future fix = add a favicon + `<link rel=icon>` to base.html — base-chrome, not a form-control concern).

### CC-29 — BUG: pattern_form swallows field-level validation errors
- Status: **FIXED + browser-verified + COMMITTED `2e5910b9` (2026-06-16, owner-approved).** Fix: added per-field `{% if form.X.errors %}<div class="form-error">…</div>{% endif %}` to all 5 fields in `pattern_form.html` (base-defined `.form-error` class — base.html:1303). Template-only (10+/2−); no styling/widget/CSS change. Re-verified: empty submit → 2 visible "This field is required." under name+code; optionals show none; non_field block untouched; console clean.
- Finding: `production/pattern_form.html` renders **only `{% if form.non_field_errors %}`** (top `.form-alert`). It renders **no per-field `{{ form.X.errors }}`** for any field. ProductPatternForm has required `code` + `name` (and unique `code`) — these produce **field-level** errors. Browser-confirmed: empty submit (name+code blank, `<form novalidate>` so client doesn't block) → form_invalid, stays on `/production/patterns/add/`, **zero visible error text** (`anyVisibleErrorText=NONE`, 0 errorlists, no `.form-alert`), no row created (count 1→1). User gets NO feedback — form silently re-renders.
- Impact: MEDIUM (user-facing) — invalid/duplicate pattern submit gives no guidance; looks like nothing happened. Perm-gated management page.
- Fix (NOT applied): add per-field error rendering to each `.form-group` (e.g. `{% if form.X.errors %}<div class="field-error">{{ form.X.errors|join:" " }}</div>{% endif %}`) — template-only. (Contrast cutting_form HTML-039, which DOES render `.field-error`.)

### CC-30 — pattern_form inputs unstyled (bare 19px) + 2-col grid clips on mobile
- Status: OPEN (evidence — browser+screenshot confirmed HTML-040); NOT fixed (recommend; await owner).
- Finding A (unstyled inputs): base.html styles inputs via the **`.form-control` class** (line 1212), NOT bare `input`; `.form-card` styles only the card container. **ProductPatternForm widgets carry no `.form-control` class** → text inputs render **bare ~19px** (screenshot: thin line vs the rows=3 textarea). Below the owner's UI bar ("basic" reject) and far under 44px touch.
- Finding B (mobile clip): the inline `style="grid-template-columns:1fr 1fr"` has **no media collapse** → at ≤~414 the right column (Code + Active) is pushed past the viewport and **clipped/unreachable** (masked by `main{overflow-x:hidden}`). → logged in **XC-1** (4th occurrence). Mobile-first functional-rule violation.
- Fix (NOT applied): A = add `.form-control` to ProductPatternForm widgets (forms.py) ; B = collapse grid to 1 col ≤600 (template/base). Both small.
- Note: pattern_form is an **under-built `.form-card` template** — missing the `.form-control` class, per-field errors (CC-29), and responsive grid that the form-shell/sf-input pages have. Likely predates those conventions.

### CC-26 — POSITIVE: management form system has a SHARED owner (counter-example to auth fragmentation)
- Status: OPEN (evidence — **positive shared-owner pattern**, recorded as carefully as fragmentation per owner 2026-06-16).
- Finding: unlike the auth cluster (CC-22 = 7 independent copies), the **management forms share one CSS owner** — `accounts/_user_form_styles.html` (the `.field` + `.chip-pick` + form-shell styles) is `{% include %}`-ed by **user_create · user_form (HTML-001/002) · skill_form (HTML-033)**, and these pages **extend base.html** (shared app chrome). One owner, multiple consumers.
- **Key distinction (owner-directed):** *not all duplication findings generalize across the app.* Auth = fragmented (standalone, copy-paste, 7 owners). Management = **partially centralized** (shared partial + shared base). The audit's job is to surface exactly this difference — fragmentation is **localized to auth**, not app-wide.
- Validation sub-note: management uses a **3rd validation strategy** = **per-field inline `.field-error` + `non_field_errors` + native (`required`/`pattern`)**, browser-confirmed on skill_form (dup-name → "…already exists.") and earlier user_form. This is **owned by the shared partial** (not per-page) — the positive counterpart to CC-24.
- **Strongest future form-canonical candidate** — BUT: do **not** promote, standardize, or conclude. Need the rest of the Form-family pages (`.sf-*` storefront, generic expense forms) before any canonical decision.
- **Update (HTML-039): production ALSO has a shared form owner** — `production/_form_styles.html` (`.form-shell`/`.panel`), parallel to management's `_user_form_styles.html`. So there are now **TWO positive shared form-shell owners** (management + production), both per-field-inline. Strengthens "fragmentation is auth-localized, not app-wide." Still NOT a canonical decision — page-scoped one-offs (expense-037, production-038) also exist.
- No action (evidence only).

### Validation-families tracker (Phase D — keep SEPARATE until Form inventory complete)
- Owner-directed 2026-06-16: track the distinct validation **families** separately; do not converge/conclude until the whole Form family is inventoried. Known so far:
  1. **Auth — Django messages framework** (login·login_password·forgot_password·otp·reset_otp·signup_otp). [CC-24 strategy B]
  2. **Auth — `form.errors` top-aggregate** (signup.html ONLY). [CC-24 strategy A]
  3. **Management — per-field inline `.field-error` + `non_field_errors` + native** (user_form, skill_form; shared `_user_form_styles.html` owner). [CC-26]
  4. **Expense action-form — raw POST `name=action` + messages-framework + native-numeric + `confirm()`** (settlement-detail HTML-036; expense-inline CSS, borrows `.sf-input`). [HTML-036]
  5. **Expense generic-loop — `{% for field in form %}` + per-field `.errs` + heavy server-side cleans + native** (worker_profile HTML-037; **page-scoped `.expense-form`** CSS owner, distinct from #4). [HTML-037]
  6. **Production raw-POST bulk — per-row inputs, no Django form, messages-on-redirect + native-numeric + server-state row-lock** (adda_report_review HTML-038; **page-scoped `.report-review`** CSS owner). [HTML-038]
  7. **Production form-shell — Django Form, per-field `.field-error` + top `.form-error`, novalidate (server-side) + CC-16 multiselect** (cutting_form HTML-039; **SHARED `production/_form_styles.html`** owner). [HTML-039]
  8. **Storefront — native `required` + per-field `.sf-error` + top `.form-errors` list** (category_form HTML-046; base-global `.sf-input`/`.sf-error` + page-scoped `.cat-*` layout). [HTML-046]
- **Form-CSS ownership map so far:** auth standalone ×7 (CC-22, fragmented) · **management SHARED `_user_form_styles.html` (CC-26, positive)** · **production SHARED `production/_form_styles.html` (HTML-039/042/043 + raw_materials 047 — positive #2, 4 consumers incl. CROSS-APP; responsive `.form-grid`)** · base.html global `.form-card` (HTML-040, under-built) · production page-scoped `.stage-form` (HTML-041) · expense settlement-detail inline+borrows-sf (HTML-036) · expense `.expense-form` page-scoped (HTML-037) · production `.report-review` page-scoped (HTML-038). **`.sf-input` = cross-app borrowed input primitive** (036, 039, storefront). **Nuance: non-auth = MIX — two proper shared form-shell owners (mgmt, production) + several page-scoped one-offs; NOT uniformly fragmented (unlike auth) and NOT uniformly shared.** Record, do not conclude.
- Still to inventory: storefront `.sf-*` forms, production `form-shell`/`_form_styles`, more expense forms — each may add or reuse a family. **No validation conclusion until then.**

### Workflow-protection (money-armor) tracker — SEPARATE from validation families (owner 2026-06-16)
- Owner-directed: a **workflow-protection pattern** (guarding money/settlement state) is **distinct from form-validation** — track separately, do not fold into the validation families.
- The pattern = **UI refusal + server refusal + audit trail** on money-locked state. Occurrences so far:
  1. **HTML-036** settlement-detail — finalize/reverse/supersede actions + `confirm()` guards + reconciliation-override audit (settlement = the money boundary).
  2. **HTML-038** adda_report_review — **settled rows LOCKED** (text not input) + server-state guard (can't edit settled verified-qty without reversing).
  3. **HTML-042** stage_rate_correct — **before-settlement-only**: settled → `.settled-note` UI refusal + submit `disabled` + server `_is_settled` refusal + mandatory reason + `RateCorrectionAudit`.
- Common shape: defense-in-depth (client disable/hide **and** server refuse) + audit + "reverse/supersede first" recovery path. **Positive pattern** — record as carefully as failures. No promotion / no consolidation yet.

---

# ═══ TABLE FAMILY (Phase E) — evidence ═══

> ## 🔒 TABLE-FAMILY EVIDENCE FROZEN (2026-06-16)
> Family E inventory + completeness scan complete (26 table systems classified). TC-1 (DataTable engine) ·
> A1/A2 split · TC-2 (5-type exceptions) · TC-3 (Financial Foundation, Evidence B) · TC-4 (not opened) ·
> TC-5 (Export, narrow) — all kept SEPARATE. Synthesis → [TABLES_CONSOLIDATION_REPORT.md](TABLES_CONSOLIDATION_REPORT.md).
> No promotion / no standardization until owner decision asks (report §8). Next family: F — Modals.

Per-unit table audit. DISCOVERY dims: type · init owner · vendor owner · responsive strategy · features ·
row-actions · empty-state · CSS owner · JS owner · mobile+touch. **Inventory before conclusions; findings
separate; no consolidation yet.**

### Table-family evidence ledger
| HTML | Table | Init / vendor owner | Responsive strategy | Features | Row-actions | Empty | Touch | Console |
|---|---|---|---|---|---|---|---|---|
| HTML-049 skill_list (browser-VERIFIED) | `#skills-dt` DataTable (3 col) | **base.html `initFancyDataTable` + shared `_datatables_vendor_css/js.html`** (single-source) | **data-label card-stack** (@320 td=flex, ::before label, 0-overflow; NOT scroll) | search ✓ (filter live) · sort (Skill Name only) · paginate(25) · info "X of Y skills" | `.td-actions` + `.action-link`/`-danger` | `.empty-state`+`.empty-icon` | action-link **≈23px** (<44px) | clean |
| HTML-050 user_list (browser-VERIFIED) | `#users-dt` DataTable (6 col) | **SAME base.html `initFancyDataTable` + shared vendor** (TC-1 REUSE, 2nd consumer) | **data-label card-stack** (@320 6-col td=flex, 0-overflow) + **filter-row horizontal-scroll** (overflowX:auto) | search · sort · paginate · info "members" · **skill-filter chips (GET, `filterRowId` JS-inject; ?skills=1→2 rows; PA-13-4 ?skills=abc→200)** | `.td-actions` + `.action-link`/`-danger` | **filter-aware** `.empty-state` | action-link 23px · filter-chip 29px (<44px) | clean |
| HTML-051 usertype_list (browser-VERIFIED) | `#utypes-dt` DataTable (5 col) | **SAME base.html `initFancyDataTable` + shared vendor** (TC-1 REUSE, 3rd consumer) | **data-label card-stack** (@320 td=flex, ::before "Label", 0-overflow) | search · sort · paginate · info "user types" · no filter row | **bare `.action-link`/`-danger` (NO `.td-actions` wrapper — variance)** | `.empty-state` | action-link 23px | clean |
| HTML-052 adda_settlement_list (browser-VERIFIED) — **WORLD B plain, legit exception** | **3 sectioned plain tables; NO DataTable** (`initFancy` exists but not called) | **page-scoped `.adst-list` own data-label stack** (NOT shared `.table-responsive`; @320 td=flex, 0-overflow) | none (no search/sort/paginate) — **workflow queue** | **per-row POST `settlement-start` form** (queue) + `a.ref` (history); no `.td-actions` | inline `.empty` per section (NOT shared `.empty-state`) | n/a (no ready rows now) | clean |
| HTML-053 payroll_overview (browser-VERIFIED) — **WORLD B plain, BORDERLINE/convertible** | **1 flat plain table; NO DataTable** | **page-scoped `.payroll-overview` own data-label** (@320 td=flex "Worker", 0-overflow) | none — but **flat list → DataTable-compatible** (sort/search would help) | `<a>` nav links only (worker-detail/settle); **no row forms** | inline `.empty` `<td colspan>` | n/a | clean |
| HTML-054 worker_detail (browser-VERIFIED) — **WORLD B: Type-5 page + Type-2 sub-table** | stat-cards + `table.adv` (code-read, no live data) + div-list history; NO DataTable | page-scoped (`.stat-card`/`.adv`); local | none (dashboard summary) | `<a>` nav only; no row forms | inline `.empty` / div-lists | stat-cards stack @320 | clean |
| HTML-055 costing (browser-VERIFIED) — **WORLD B Type-2 Financial Ledger, CONVERTIBLE** | 1 flat plain table (8 rows); NO DataTable | **page-scoped `.costing` own data-label** (@320 td=flex "Adda", 0-overflow) | none — **flat per-Adda list → DataTable grid-engine compatible** (hero total stays outside) | `a.adda` nav; **no row forms**; `.cost`/`.unpriced` (ADR-0009 NULL) | inline `.empty` | n/a | clean |
| HTML-056 master_list (browser-VERIFIED) — **CRUD List PLAIN; World-A ACCIDENTAL DIVERGENCE (A2)** | 1 plain `.tbl` (4 rows); **NO DataTable** (dtWrapper=0, no search) | **SHARED `.table-responsive` + data-label** (@320 td=flex "Name", 0-overflow) | none — flat CRUD list (like 049/050/051 which ARE DataTables) → World-A candidate | `.td-actions` (shared) | `{% empty %}` inline | n/a | clean |
| HTML-057 access_control (browser-VERIFIED) — **READ-ONLY OVERVIEW ×4; NOT matrix** | 4 read-only plain tables; **NO DataTable, 0 checkboxes** | page-scoped data-label (@320 td=flex "Stage", 0-overflow) | none — read-only state overview (sidebar/stages/users/roles) | none (read-only; badges/chips) | inline | n/a | clean |
| HTML-058 barcode_list (browser-VERIFIED) — **read-only Report/Export; A2-adjacent** | plain `.tbl` (batch ranges); **NO DataTable** | **SHARED `.table-responsive` + data-label** (@320 td=flex "Size", 0-overflow) | none — flat read-only list → DataTable-compatible (sort/search) | **page-level export forms ×3 (CSV/XLSX/PDF)**; no row actions | `{% empty %}` inline | export btn 38px | clean |
| HTML-059 export_list (browser-VERIFIED) — **AUDIT/Manifest table; A2-adjacent + TC-5 evidence** | plain `.tbl` (export log); **NO DataTable** | **SHARED `.table-responsive` + data-label** (@320 td=flex "Code", 0-overflow) | none — read-only audit log → DataTable-compatible | `.td-actions` Download (re-generate) | `.empty-state-row` | n/a | clean |

### TC-1 (candidate, POSITIVE) — shared DataTable foundation
- Status: OPEN (evidence — first Family E data point; **do NOT conclude — inventory incomplete**).
- Finding: HTML-049 uses a **shared DataTable foundation** — `initFancyDataTable` (base.html, single JS owner) +
  shared vendor partials (`templates/shared/_datatables_vendor_*.html`) + `.table-responsive`+`data-label`
  stacking + `.td-actions`/`.action-link` + `.empty-state`. One owner, responsive-by-default (data-label stack).
- Why it matters: mirrors the form `_form_styles.html` positive — a real shared foundation, the canonical
  candidate for the Table family. **Verify reuse across the rest of Family E before any conclusion.**
- **REUSE +1 (HTML-050 user_list):** same `initFancyDataTable` + shared vendor partials, 6-col table, browser-verified — **2nd consumer**. Adds a shared **DataTable filter-row** sub-element (`.dt-filter-row` + `.skill-filter-chip`, base.html-owned, injected via `filterRowId` config) — a shared FEATURE, not a divergence. Strengthens TC-1 (still candidate; inventory incomplete).
- **REUSE +1 (HTML-051 usertype_list):** **3rd consumer**, browser-verified live (5 rows). **Q1/Q2 ANSWERED:** `initFancyDataTable` = **sole bootstrapper** (5 callers; only raw `.DataTable(` is inside the helper, `base.html:2819`); **no page-specific wrappers / no config drift.** Q5: 5 DataTable pages = 049/050/051 + storefront 018/020.
- **⚠ Q3 (separate inventory finding, NOT part of TC-1):** **plain non-DataTable tables ARE present + numerous (~19 templates)** — money/settlement/payroll/dashboard/detail/inline-edit/access-control. **TWO table approaches.** Some are legit-non-list; some are lists that could be DataTables but aren't → **consistency question, resolve across 052-059.** Keep separate from TC-1.
- **Action-column variance (Q4 inventory):** 049/050 use `.td-actions` wrapper + `.action-link`; **051 uses bare `.action-link` (no `.td-actions`)** — minor divergence to track.
- Touch note: table **`.action-link` ≈23px** + **`.skill-filter-chip` 29px** row-action/filter links (<44px) — new touch sub-category (relate to CC-25 button/input touch theme; tables row-actions/filters are their own). Record; widen across Family E.

### TC-2 (tracker) — World A (DataTable) vs World B (plain) table classification
- Status: OPEN (inventory in progress — World B = legitimate exceptions, NOT debt by default; per owner 2026-06-16).
- **World A (canonical DataTable family, TC-1):** CRUD/list pages — skill_list(049) · user_list(050) · usertype_list(051) · storefront product_list(020)/category_list(018). Shared `initFancyDataTable` + vendor + table-responsive data-label + (mostly) `.td-actions`/`.action-link` + `.empty-state`.
- **World B (plain tables) — classify each (intentional-exception vs accidental):**
  - **HTML-052 adda_settlement_list → LEGITIMATE EXCEPTION** — 3 grouped workflow sections (ready/waiting/history) + per-row action forms (Start settlement) + money/status/chain. DataTable inappropriate. ✓ intentional.
  - (052 also shows a **minor responsive-owner variance**: own page-scoped `.adst-list` data-label stack instead of shared `.table-responsive` — reimplemented, not divergent-broken.)
  - REMAINING World B to classify (052-059 + the ~19 grep): payroll_overview(053), worker_detail(054), settlement_detail(036 money — done), inline-edit(044 done), dashboards(adda/cloth/barcode), master_list, roll_list, adda_list, barcode_list, access_control, costing, export_list.
- **Why-test per World-B table (owner A–D 2026-06-16):** A. fundamentally what (CRUD-list/workflow-queue/financial-ledger/settlement-history/payroll/inline-editor/matrix/dashboard-summary)? · B. would DataTable IMPROVE or DAMAGE? · C. requires grouped-sections/row-forms/sticky-totals/money-locks/workflow-state/approval-chains/inline-edit/expandable-rows? · D. legit-exception vs accidental — and for legit: shared owner/responsive/empty/action/styling?
- **STRICT 5-TYPE TAXONOMY (owner 2026-06-16) — a table is an exception ONLY if DataTable would BREAK the workflow (NOT because it has money/totals/badges/pills):**
  - **TYPE-1 Workflow Queue** (grouped sections · row actions · state transitions · NOT DataTable candidates) — **settlement_list (052) ✓ LEGIT exception** (3 sections + per-row Start-settlement forms + status/chain → DataTable would damage).
  - **TYPE-2 Financial Ledger** (money cols · totals · balances · sorting useful) — **convertibility test: can DataTable be the GRID ENGINE while totals/cards stay outside? If yes → World-B CONVERTIBLE, NOT a true exception.** payroll_overview (053) → **CONVERTIBLE** · worker_detail advances sub-table (054) → **CONVERTIBLE** (code-read) · **costing (055) → CONVERTIBLE** (8-row flat per-Adda cost list + hero grand-total outside). **3 convertibles so far → these fold into World A, not exceptions.**
  - **TYPE-3 Inline Editor** (inputs/forms in rows · archive/reactivate · inline save; DataTable usually DAMAGES UX) — **product_sizes_edit (044) ✓ LEGIT exception**.
  - **TYPE-4 Matrix** (row×col checkbox editing) — **role_form permission matrix (CC-18) + access_control ✓ LEGIT exception** (pending browser confirm in Family E).
  - **TYPE-5 Dashboard Summary** (aggregates FIRST, table second) — **worker_detail (054) page ✓** (5 stat-cards + history div-lists; not tabular at page level) — investigate-separately category.
  - (pending: settlement-history, adda/cloth/barcode dashboards, master_list, roll_list, adda_list, barcode_list, costing, export_list.)
- **⚠ World-B OWNERSHIP observation (separate finding):** each World-B table rolls its **OWN page-scoped CSS + own data-label stack + own `.empty`** (052 `.adst-list`, 053 `.payroll-overview`, 054 `.adv`/`.stat-card`) — **NO shared World-B foundation** (contrast World A's shared TC-1). Even *legitimate* exceptions lack a shared owner → the enterprise gap is not "convert to DataTable" but "**World-B exceptions need a shared owner / responsive strategy too**".

### TC-3 (candidate) — Shared Financial Table Foundation — STATUS: **EVIDENCE B (hidden foundation EMERGING, implemented as duplicates)**
- Status: OPEN. Updated HTML-055. **Two evidence questions (owner): A = no foundation exists · B = hidden foundation emerging. → Evidence points to B.**
- **CODE-LEVEL (partials): no shared owner** — expense financial pages have **0 shared `{% include %}` partials**; each = own page-scoped CSS (`.adst-list` 052 · `.payroll-overview` 053 · `.adv` 054 · `.costing` 055). (This was the initial "absent" read @054.)
- **CONCEPT-LEVEL (repeated patterns) — a foundation IS emerging (per owner: a foundation can exist conceptually even when implementation is duplicated):**
  - **Hero grand-total summary (`.total .v`)** — **4 pages** (costing · payroll_overview · settlement_detail · roll_detail).
  - **Money columns + ₹ currency + money-col classes** (`.cost`/`.payable`/`.amt-credit`/`.num`) — **7 pages** (settlement_detail/list · payroll · worker_detail · settlement_form · my_earnings · costing).
  - **Page-scoped data-label responsive stacking** (`td::before content:attr(data-label)`) — **≥7 templates** reimplement it (costing · payroll · settlement_list + _form_styles · pattern_workspace · stage_panel_embedded; base.html `.table-responsive` has the canonical one) → the responsive-stack concept is duplicated, not shared.
  - **Status pills** (`.pill`) — 2 settlement pages (narrower reuse).
  - **`.empty` inline empty-state** — repeated page-locally (NOT the shared World-A `.empty-state`).
- **Verdict: B — a financial-table FOUNDATION exists CONCEPTUALLY (consistent recurring pattern: hero grand-total + money cols + ₹ + data-label stack + `.empty`) but is IMPLEMENTED as ~7 DUPLICATED page-scoped one-offs (no shared code owner).** The enterprise opportunity = extract the shared concept into one owner. Keep separate from TC-1 (DataTable) + TC-2 (exception taxonomy). Widen across remaining financial units to finalize the count.
- **TC-3 = a BUSINESS COMPONENT SYSTEM (owner 2026-06-16), NOT DataTable** — `FinancialFoundation ├ SummaryCards ├ MoneyCell ├ StatusPill ├ LedgerGrid ├ TotalsBar ├ EmptyState └ ResponsiveRules`. May USE DataTable internally (TC-1 as a dependency of the LedgerGrid) but TC-3 ≠ TC-1. **Per-financial-page 6-primitive scorecard (shared YES/NO) — building:**
  - **SummaryCards:** present 052(hero)/053(hero)/054(5 stat-cards)/055(hero)/036(stat row) — **concept shared, code NO** (each page-local).
  - **MoneyCell (₹ fmt):** all financial pages use `₹{{ x|floatformat:2 }}` — **concept shared, NO shared component** (Django filter, inline).
  - **StatusPill:** `.pill` in 052+036 only — **partial; NO across all**.
  - **LedgerGrid:** money tables in 052/053/054/055/036 — **concept shared, code NO** (page-scoped each).
  - **EmptyState:** inline `.empty`/`{% empty %}` page-local — **NOT shared** (≠ World-A `.empty-state`).
  - **ResponsiveRules:** page-scoped data-label reimplemented ×7 — **NOT shared** (base `.table-responsive` exists but financial pages roll their own).
  - → **every primitive = shared CONCEPT, duplicated IMPLEMENTATION. TC-3 migration counter (pages that could adopt a Financial Foundation w/o business-logic change): 053·054·055·036 (+052 partial) = ~4-5.**
- **World-A migration counter (separate — plain CRUD lists → DataTable, no logic change): master_list(056)** [+ pending adda_list/roll_list/barcode_list]. (master_list = accidental World-A divergence, not a TC-3 financial case.)

### World-A SPLIT (owner 2026-06-16) — A1 canonical vs A2 accidental-divergence
- **A1 — Canonical CRUD Lists (TC-1):** full shared stack — `initFancyDataTable` + search/sort + shared `.empty-state` + `.td-actions` + table-responsive. → **skill_list(049) · user_list(050) · usertype_list(051) · storefront product_list(020)/category_list(018).**
- **A2 — CRUD Lists with shared primitives but MISSING ENGINE (accidental divergence, NOT an exception):** have table-responsive + data-label + `.td-actions` but **NO `initFancyDataTable` / no search / no sort.** → **master_list(056)** · **barcode_list(058 — A2-ADJACENT: read-only Report/Export, not strict CRUD, but same plain+shared-primitives+no-engine shape; export forms page-level)** [+ pending adda_list/roll_list]. **A2 = canonical pages that DRIFTED (implemented-incorrectly), distinct from TC-2 legit exceptions (implemented-correctly).** **Migration A2→A1 = safe, near-zero (just add the init helper).** **DO NOT merge A2 into TC-2.**
- **Architectural distinction (owner):** Canonical-but-wrong (A2) ≠ Exception-but-right (TC-2). Different outcomes.

### TC-4 (candidate slot) — Matrix Foundation — STATUS: NOT OPENED (only 1 matrix exists)
- **How many matrix implementations? → ONE** = role_form permission CRUD matrix (CC-18, HTML-035). access_control(057) is **read-only overview, NOT a matrix** (0 checkboxes). No other row×col checkbox matrix in the app (grep = role_forms.py only).
- → **TC-4 NOT justified** — a foundation needs ≥2 implementations to share; only 1 matrix exists. No duplication → no foundation candidate. (role_form matrix keeps its CC-18 mobile-clip / page-scoped bulk-toggle findings.) Reopen only if a 2nd matrix appears.

### TC-5 (candidate) — Export Foundation — STATUS: OPENED (NARROW; concept shared, impl duplicated)
- Status: OPEN (evidence appeared @059 — export behavior repeats). NARROW scope (barcode-export only).
- Finding: **export-TRIGGER button-group (CSV/XLSX/PDF, 3 POST forms) DUPLICATED inline in 2 pages** — barcode_list(058) + `_stage_panel_barcode_gen`(071), 3 forms each, **no shared partial** — plus the **export MANIFEST/audit table** (export_list 059) + **Download (re-generate from live data)**. → a small Export subsystem: shared CONCEPT (export-action button-group + manifest + download/regenerate), **duplicated IMPLEMENTATION** (button-group copy-pasted ×2).
- Components: `ExportButtonGroup` (CSV/XLSX/PDF) · `ExportManifest` (audit table) · `ExportDownload` (regenerate). Backed by `barcode_export_service`.
- Separate from TC-1 (export ≠ DataTable engine). Migration: dedupe the export-button-group into one partial; manifest table = A2-adjacent (could be DataTable). **Widen only if more export surfaces appear; do NOT force broader than the evidence (2 trigger pages + 1 manifest).**

### Migration counters (consolidated, owner enterprise Q)
- **A2 → TC-1 (DataTable engine):** master_list(056) + **barcode_list(058)** + **export_list(059, A2-adjacent/audit)** [+pending adda_list/roll_list].
- **Export → TC-5 (Export Foundation, narrow):** export-button-group duplicated in 058 + 071; manifest 059.
- **Financial → TC-3 (Financial Foundation):** payroll(053) · worker_detail-advances(054) · costing(055) · settlement_detail-money(036) [+ settlement_list(052) partial] ≈ 4-5.
- **Workflow → Workflow Foundation:** settlement_list(052) [only 1 so far].
- **Matrix → Matrix Foundation:** role_form(CC-18) [only 1 → no foundation].
- **Enterprise target (recorded, not concluded):** ONE canonical table family (World A / TC-1) **+ documented exception families (Type-1/3/4/5) each with a shared owner** + **Type-2 convertibles folded into World A**. Sort each World-B table by strict type + convertibility. NO conclusion until Family E inventory complete.

---

# ═══ MODAL FAMILY (Phase F) — evidence ═══

> ## 🔒 MODAL-FAMILY EVIDENCE FROZEN (2026-06-16)
> Family F inventory + HTML-060 complete. **One app-owned modal (Crop Modal, widget-private, 2 consumers); no modal fragmentation; NO modal foundation required (TC-6 NOT opened).** Native confirm()=browser-owned; fancy-panels=Select/Date; sidebar=Nav. Synthesis → [FAMILY_F_MODALS_REPORT.md](FAMILY_F_MODALS_REPORT.md). No promotion until owner decision asks (report §5).

### Modal-family findings
- **Crop Modal (HTML-060)** — `.cw-crop-modal`, owner = `croppable_image.html` widget, 2 consumers (category_form 046 + product_form 019). Behavior SOLID (ESC/overlay/X/Cancel/Apply close · scroll-lock · z-10000) · responsive GOOD (95vw/max-720, fits 320-1280 no clip) · **WIDGET-PRIVATE exception, NOT a foundation.**
- **MOD-A11Y (finding, record-only)** — crop modal lacks `role="dialog"` · `aria-modal` · `aria-labelledby` · focus-trap · focus-return (close `aria-label` ✓). AT/keyboard gap; same theme as CC-01. Fix deferred to a future a11y pass.
- **TC-6 Modal Foundation — NOT opened** (only 1 app-owned modal; reopen only if a 2nd appears).

---

# ═══ CARD / LAYOUT FAMILY (Phase G) — evidence ═══

> ## 🔒 FAMILY G EVIDENCE FROZEN (2026-06-16)
> Family G inventory complete (surfaces 061-071G + partials census + completeness). Card/Dashboard/Detail/Timeline systems = MULTIPLE (shared base primitives + page-scoped variants), kept SEPARATE. base.html=master shell(78). Dead/unrouted: home(062), scan_detail(067). Synthesis → [FAMILY_G_REMAINING_SURFACES_REPORT.md](FAMILY_G_REMAINING_SURFACES_REPORT.md). **NO foundation/promotion/canonical/migration — architecture OPEN until whole-system review.**

Per-surface card audit. **Inventory before conclusions; no card-foundation named until inventory complete (owner 2026-06-16).** DISCOVERY dims: card type · owner (shared base `.card`/`.kpi`/`.stat-card` vs page-scoped) · responsive · actions · empty.

### Card-ownership (cross-cutting)
- **Shared base.html primitives:** `.kpi`(648) · `.card`(676) · `.stat-card`(1523). Real shared owner exists.
- **Page-scoped / own-card redefinitions:** error 403/404/500 (standalone) · auth (standalone) · costing · payroll_overview · adda_report_review · pattern_list(`.pattern-list`). → **MIXED ownership** (shared base + page-scoped variants), same theme as forms/tables. **Count consumers of base `.card`/`.kpi`/`.stat-card` vs page-scoped across G before any conclusion.**

### Card-family evidence ledger
| HTML | Surface | Card type | Owner | Responsive | Console |
|---|---|---|---|---|---|
| HTML-061 pattern_list | card-LIST (CRUD-as-cards) | card-list | **page-scoped `.pattern-list`** (NOT base `.card`) | 0-overflow @320, cards fit | clean |
| HTML-062 accounts/home | KPI dashboard — **⚠ DEAD/ORPHANED** (no renderer; HomeView redirects; hardcoded ₹2.4L) | base `.kpi` (in dead file) | n/a (never rendered) | code-read |
| HTML-063 user_dashboard | generic-`.card` dashboard (4 sections, collapsible details-card) | **base `.card` (SHARED)** + page-scoped `<style>` | 0-overflow @320, cards fit, auto-fit grid | clean |
| HTML-064 adda_dashboard (=production:dashboard) | **multi-system:** KPI tiles ×4 + generic cards ×2 + Type-5 table + date filter | **base `.kpi` + base `.card` (SHARED)** + page-scoped | 0-overflow @320, KPI stack | clean |
| HTML-065 adda_detail (Adda-360) | detail-360 sections + status badge + display chips (roll/worker) + activity timeline | **FULLY page-scoped `.adda-detail`** (0 base card/kpi/stat) + **shared `_activity_feed.html` timeline** | 0-overflow @320, chips wrap | clean |
| HTML-066 roll_detail | cloth-roll detail: base `.card`×2 + `<dl>` attrs (Cost/KG ₹) + status badge; NO timeline, 0 tables | **base `.card` (SHARED)** + page-scoped `.roll-detail` wrapper | 0-overflow @320, cards fit | clean |
| HTML-067 scan_detail | barcode scan detail: base `.card` + `<dl>` (no timeline/money/table) — **System B (code)** | **base `.card` (SHARED)** + page-scoped `.scan-detail` | ⚠ UNROUTED (scan_piece not in urls.py) — code-read | n/a |
| HTML-068 adda_history + roll_history | audit-TIMELINE: base `.card` + `<ul><li>` events (ts/actor); no `_activity_feed`, 0 tables | **base `.card` (SHARED)** + **page-scoped `.history-page` (DUPLICATED ×2)** | 0-overflow @320, li fits | clean |
| HTML-069 pending_reports + stalled_addas + raw_material_dashboard | 3 dashboard summaries; NO base `.kpi`/`.card` | **3 DISTINCT page-scoped** (`.pending-card` · `.stalled-card` · `.rm-cloth-card`+`.stat-num`) | 0-overflow @1280 (320 deferred) | n/a |
| HTML-070G stage_list + role_list + stage_rate_list | card-LIST trio | **MIXED:** role_list **base `.card`**; stage_list/stage_rate_list **page-scoped `.stage-card`** (+pills) | 0-overflow @320 all | clean |
| HTML-071G my_earnings + cloth_dashboard + public_home + 403/404/500 + sidebar_access_list | mixed batch | my_earnings **base `.stat-card`×7 (=TC-3 SummaryCards)** · cloth_dashboard **base `.kpi`+`.card`** (Dash-A)+2 tables · public_home + error-pages **STANDALONE** · sidebar config-form | 0-overflow | clean |

### ⚠ Dead/orphaned surface tracker (Family G)
- **accounts/home.html (HTML-062)** — rendered by NOTHING (HomeView unconditionally redirects → production:dashboard / inventory:user_dashboard). Hardcoded `₹2.4L` placeholder. **Dead-code/cleanup candidate.** Live KPI landings = **production:dashboard + inventory:user_dashboard** (both use base `.kpi` — shared primitive; production:dashboard browser-confirmed). Add these to the Family G surface list (audit them, not home.html).
KPI tiles (`.kpi`) · generic `.card` · stat-card (money summary, TC-3 SummaryCards overlap) · **card-LIST** (061) · detail/360 cards (adda_detail) · timeline cards (history). Owners mixed (shared base vs page-scoped). **Whether a "Card Foundation" exists = decided ONLY after Family G inventory complete.**

**DASHBOARD systems (multiple, evidence — owner: don't unify):** **System A = base-primitive** (adda_dashboard 064 `.kpi`+`.card`; user_dashboard 063 `.card`). **Systems B/C/D = page-scoped per-page** (pending_reports `.pending-card` · stalled_addas `.stalled-card` · raw_material_dashboard `.rm-cloth-card`+`.stat-num`). → dashboards = NOT one system; 2 base + ≥3 page-scoped divergent.
- **Family E census-gap → RESOLVED (false alarm):** stalled_addas.html has **0 `<table>`** (read-confirmed: `.stalled-card` anchor-cards + `<dl>`); browser `tables=1` was spurious (base chrome/stale). Family E census stands correct. stalled_addas = card-list dashboard (Dashboard System C).

**Card-ownership consumer counts (building — base shared vs page-scoped):**
- **base `.card` (SHARED) consumers:** user_dashboard(063) · adda_dashboard(064) · roll_detail(066) · adda_history(068) · roll_history(068) · role_list(070G) · **cloth_dashboard(071G)** = **7**.
- **base `.kpi` consumers:** adda_dashboard(064) · **cloth_dashboard(071G)** = 2.
- **base `.stat-card` (= TC-3 SummaryCards primitive) consumers:** my_earnings(071G) · worker_detail(054) = 2. → **TC-3 SummaryCards ↔ base `.stat-card` CONFIRMED** (my_earnings = financial summary as `.stat-card` money cards, no table).
- **STANDALONE surfaces (no base.html, self-contained):** public_home(071G, 1311L marketing) · 403/404/500(071G, ×3 near-identical, resilience-justified) · auth pages(CC-22). Distinct from in-app card/dashboard systems.
- **CARD-LIST implementations = MIXED (≥4):** base `.card` (role_list 070G) vs page-scoped (pattern_list 061 · stage_list 070G · stage_rate_list 070G). NOT one card-list system.
- **`.pill` status-badges (multiple owners):** production stage pills (stage_list ×31, stage_rate_list ×9, page-scoped) · financial pills (settlement_list/detail 052/036). Recurring concept, NOT one owner.
- **TIMELINE systems (multiple, evidence):** **System 1 = `_activity_feed.html`** (shared partial; adda_detail 065). **System 2 = `.history-page` audit-timeline** (`<ul><li>`+base `.card`; adda_history + roll_history = **2 DUPLICATED copies**, each own `.history-page` `<style>`, no shared `_history_timeline` partial). → ≥2 timeline systems; System 2 internally duplicated ×2.
- **MULTIPLE DETAIL SYSTEMS (evidence):** **System A** (adda_detail 065) = page-scoped `.adda-detail` + chips + `_activity_feed` timeline (complex 360). **System B** (lightweight: base `.card` + `<dl>` attribute list, no timeline) = roll_detail(066) + **scan_detail(067, code; unrouted)** → **2 consumers.** → detail pages = ≥2 distinct systems. `_activity_feed` timeline consumers = adda_detail only.
- **⚠ Dead/unwired surface tracker:** accounts/home(062, no renderer) · **scan_detail(067, scan_piece view UNROUTED — not in any urls.py; test-only)**. Owner decides dead-vs-pending-wiring. **base `.kpi`:** adda_dashboard(064, ×4, browser-confirmed) + accounts/home(062 DEAD, excluded). **base `.stat-card`:** worker_detail / financial pages (TC-3 overlap, page-scoped redefinitions).
- **page-scoped own-card:** pattern_list(061 `.pattern-list`) · **adda_detail(065 `.adda-detail`, detail-360, 0 base cards)** · error 403/404/500 · auth · costing · payroll · adda_report_review.
- **Shared TIMELINE partial:** `production/_activity_feed.html` — included by adda_detail(065) [+ likely history pages]; a real shared-owner timeline (distinct from cards). Track consumers.
- **Display chips** (`.roll-chip`/`.worker-chip`, adda_detail 065) = page-scoped DISPLAY badges, distinct from form-control chips CC-16/CC-17.
- **Ownership varies by surface-TYPE:** dashboards (063/064) = base-shared `.card`/`.kpi`; detail-360 (065) + card-list (061) = page-scoped. NOT one uniform card ownership.
- → base primitives ARE reused (shared owner real) AND page-scoped variants coexist = **MIXED**. Final count + foundation question after Family G complete.
