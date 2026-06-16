# FORMS AUDIT REPORT (Foundation 3)

> **Status:** Evidence/inventory — **DESIGN ONLY. NO CODE, NO commits.** Counts MEASURED
> 2026-06-16 (`config/**/*.html`). Companions: [FORMS_FOUNDATION_SPEC.md](FORMS_FOUNDATION_SPEC.md) · [FORMS_MIGRATION_MATRIX.md](FORMS_MIGRATION_MATRIX.md).
> **Scope:** in-app forms. **EXCLUDES the 7 standalone auth pages** (login/signup/otp/etc.) →
> handled in Foundation 4 (Auth). **Owner:** Umesh.

## 0. Headline
The form layer has **5 live input/layout systems + 1 dead one**, a `.field` class
**re-defined ~10+ times** with divergent values, **3–4 validation renderings**, and **two
multiselect idioms**. `_form_styles.html` (`.form-shell`) is the richest, most-reused system
(de-facto owner) but accounts/dashboard/stage pages each fork their own. More fragmented than Buttons.

## 1. Input / layout systems

| System | Owner | Input styling | Consumers | State |
|---|---|---|---|---|
| **`.form-shell`** | `production/_form_styles.html` (scoped) | element-scoped `input,select,textarea`: cream bg · `1.5px #cfc0aa` · **r10** · pad **11/14** · fs14 · inset shadow | **22 include / 16 use class** | **canonical candidate** |
| **`.sf-input`** | base.html (class) | cream · r? · class-based | **5** (storefront product/category, _stage_panel_cutting(+pattern), settlement_detail) | live, parallel |
| **Accounts bespoke** | `user_form`/`user_create` (page) | `.user-edit-shell` + `.field`/`.field-row`/`.field-grid-2` | 2 | fork (includes `_form_styles` but uses own shell) |
| **Dashboard filter `.field`** | per-page (bc-dash/cloth-dash/roll-list/adda-list/adda-dash) | `.filter-card .field` layout only, **gap:4px** | 5 | fork (layout-only) |
| **Stage-panel `.field`** | `stage_panel_embedded` / `stage_form` / `layering-ws .inline-form` | own `.field` (gap 4-6, `.inline-form` flex) | 3+ | fork |
| **`.form-*` (form-card)** | base.html | `.form-control` input | **`.form-control` = 0 (DEAD)**; containers: form-card 2 · form-actions 4 · form-errors 2 | **input system dead**, containers vestigial |

## 2. The `.field` problem (core fragmentation)
`class="field"` = **28 usages across many files, but only ever defined SCOPED** — never a
global class. Found **~10+ independent definitions**, divergent:
- `.form-shell .field { gap:6px }` · `.stage-form .field { gap:6px; margin-bottom:16px }` ·
  `.<dash> .filter-card .field { gap:4px }` · `.bulk-roll-create .field {…}` ·
  `.inline-form .field { flex:1 1 100px }` · auth `.field { margin-bottom:20px }` (white inputs) ·
  accounts `.field` inside `.user-edit-shell`.
- **17 files use `class="field"` OUTSIDE `.form-shell`** → rely on a page-local `.field` (or none).
→ `.field` is a **convention, not a component.** No single owner; same name, different rules.

## 3. Input styling divergence (measured)
- **form-shell:** cream / r10 / pad 11px 14px / fs14 / `inset 0 1.5px 4px` + focus `0 0 0 3px copper`.
- **auth (forgot/reset):** **white** bg / **r6** / pad 14/18 or 13/16 / fs14 (different look; auth scope = Foundation 4).
- **sf-input:** base.html class (cream, parallel to form-control).
- Radius spread: r10 ×13 · r8 ×11 · r6 ×8 · r14 ×8 · r12 ×6. Padding spread: 10/14 ×9 · 12/16 ×6 · 9/14 ×5 · 9/12 ×4 · 11/14 (form-shell). **Off-grid-heavy → tokenization mostly exact-match-only (partial), like Buttons.**

## 4. Validation rendering (fragmented)
| Render | Files | Style |
|---|---|---|
| `.field-error` | 16 | red 12px (form-shell + per-field) |
| `.form-error` (single) | 9 | red 11px (base) / red box (form-shell `.form-error`) — **two different `.form-error`!** |
| `.form-errors` (box) | 3 | base errorlist box (3-color) |
| `.sf-error` | 3 | red 12px (sf system) |
Raw Django `.errorlist` = 0 (good — none rely on default). **3–4 renderings for the same concept.**

## 5. Multiselect
- **`.worker-chip` / `.workers-grid`** (in `_form_styles`, 6 files): checkbox-chip grid, cream
  chips, `:has(input:checked)` highlight — the GOOD pattern. Rendered by the `_WorkerCheckboxes`
  widget (`_workers_widget.html`).
- **CC-20 bare** Django `CheckboxSelectMultiple` rendered WITHOUT the chip wrapper (audit: 2
  surfaces — stage start panel `045`, barcode_gen `071`). 7 `.py` files reference
  `CheckboxSelectMultiple`/`_WorkerCheckboxes` (most → chip via widget; bare = where raw).
→ Two idioms: **chip (canonical)** vs **bare (CC-20, retire)**.

## 6. Dead / vestigial code
- **`.form-control`** (base.html input class): **0 consumers** → dead.
- `.form-card`/`.form-actions`/`.form-errors` (base): 2/4/2 light consumers — vestigial container
  system parallel to form-shell `.sticky-actions`/`.form-error`.

## 7. Already-centralized (no Forms work)
- **Selects → `fancify()`** (base.html). **Dates → `fancifyDate()`** (base.html). Both done
  (Foundations recorded). Forms foundation does NOT re-touch them.

## 8. Fragmentation summary (what Foundation 3 must converge)
1. One input styling owner (form-shell cream vs sf-input vs accounts-bespoke).
2. `.field` → one component (kill ~10 page redefs).
3. One validation contract (`.field-error`) (retire form-error dup / form-errors box / sf-error).
4. Multiselect → worker-chip (retire CC-20 bare ×2).
5. Relocate `_form_styles.html` → `shared/` (cross-app; currently under `production/`).
6. Remove dead `.form-control` (+ decide vestigial form-card/actions/errors).
7. Spacing → tokens (exact-match inert; off-grid deferred).

---

**No code. Evidence only.** Contract → [FORMS_FOUNDATION_SPEC.md](FORMS_FOUNDATION_SPEC.md); per-target inert/visual split → [FORMS_MIGRATION_MATRIX.md](FORMS_MIGRATION_MATRIX.md).
