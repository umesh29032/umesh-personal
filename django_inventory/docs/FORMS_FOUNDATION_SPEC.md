---
id: docs-forms-foundation-spec
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# FORMS FOUNDATION SPEC (Foundation 3)

> **Status:** Contract — **DESIGN ONLY. NO CODE, NO commits.** The single-source contract for
> every in-app form. Evidence: [FORMS_AUDIT_REPORT.md](FORMS_AUDIT_REPORT.md). Rules baseline: [DESIGN_SYSTEM_SPEC.md](DESIGN_SYSTEM_SPEC.md) §3.
> **Scope:** in-app forms. **Auth pages = Foundation 4 (excluded here).** Selects/dates already
> centralized (`fancify`/`fancifyDate`) — untouched. **Owner:** Umesh · Created 2026-06-16.

## 1. Single owner
**`shared/_form_styles.html`** (relocated from `production/_form_styles.html`) = the canonical
form system, scoped under **`.form-shell`**: hero · numbered panels · `.field` · element-scoped
inputs · `.field-error` · `.form-error` box · `.worker-chip` multiselect · `.sticky-actions` ·
`.breakup-table`. One CSS owner. Selects→`fancify`, dates→`fancifyDate` (base.html, unchanged).

## 2. Shared input classes (the contract)
**Two delivery mechanisms, ONE visual language (identical token values):**
- **Element-scoped** (default for `.form-shell` pages): raw `<input>/<select>/<textarea>` inside
  `.form-shell` → styled automatically. No class needed.
- **`.sf-input`** (class-based, for pages that can't element-scope or need per-field control):
  MUST resolve to the SAME values as form-shell inputs (cream `--surface-input` · `1.5px
  --border-card` · `--radius-md` · pad 11/14 · fs `--fs-md` · inset shadow · copper focus ring).
- **Canonical input values:** bg `var(--surface-input)` · border `1.5px var(--border-card)` ·
  `border-radius: var(--radius-md)` (10) · padding `11px 14px` (off-grid → literal until rationalized)
  · `font-size: var(--fs-md)` (14) · `box-shadow: var(--shadow-input-inset)` · focus border
  `--copper` + `var(--shadow-focus)`.
- **`.field`** = the ONE field-wrapper component (flex column, `gap: var(--space-2)`(8) or 6 —
  see D3): label + control + error. Promoted to a documented owned class; **page-local `.field`
  redefs retired.**
- **Forbidden:** `.form-control` (dead — remove) · inline input CSS · new page-local `.field`
  definition · white-on-white inputs · re-styling inputs per page.

## 3. Validation states (ONE contract)
- **`.field-error`** = per-field error (red `--danger`, fs `--fs-sm` 12). The single per-field render.
- **`.form-error`** = ONE non-field/form-level error **box** (the form-shell box: `--danger-bg` /
  `--danger` / r10 / pad 12/16). Retire the *other* base `.form-error` (11px inline) + `.sf-error`
  + `.form-errors` (errorlist box) → all converge to `.field-error` (per-field) + `.form-error` (box).
- Every field renders its own error (CC-29 rule: never swallow). Errors associated to field.
- **Forbidden:** raw Django `.errorlist` · multiple error-render styles · swallowing field errors.

## 4. Multiselect strategy
- **Canonical = `.worker-chip` / `.workers-grid`** (checkbox-chip grid, cream chips,
  `:has(input:checked)` highlight) rendered via the `_WorkerCheckboxes` widget (`_workers_widget.html`).
- **Retire CC-20 bare** `CheckboxSelectMultiple` on its ~2 surfaces (stage-start `045`,
  barcode_gen `071`) → route through the chip widget. **VISUAL change** (bare → chips).
- **Forbidden:** bare Django multiselect; per-page chip CSS (use the shared `.worker-chip`).

## 5. Spacing / token usage
- Inputs/labels/gaps/panels consume tokens: `--space-*` (gaps/margins on-grid), `--radius-md`
  (inputs), `--radius-lg`/`--radius-xl` (panels 12/14), `--fs-*`, `--surface-input`,
  `--border-card`, `--shadow-input-inset`, `--shadow-focus`, `--danger`/`--danger-bg`.
- **Exact-match → token (INERT).** Off-grid literals (pad 11/14, panel pad 18/22, hero 26/30) =
  **DEFER** (not snapped; future scale rationalization, like Buttons off-grid).

## 6. Responsive contract
- `.form-grid` → 1 column ≤768. `.sticky-actions` → column-reverse + full-width buttons ≤600.
- `.breakup-table` → card-stack ≤600 (data-label). `.workers-grid` auto-fill, chips wrap.
- Inputs full-width; touch ≥`--touch-min` deferred to the touch pass (consistent with Buttons B-6).
- **The shared partial owns its own responsive CSS** (gotcha: must not assume an ancestor it lacks).

## 7. Naming
`.form-shell` (root) · `.field`/`.field.full`/`.field-error` · `.form-error` (box) ·
`.worker-chip`/`.workers-grid` · `.sticky-actions` · `.panel`/`.panel-head`/`.panel-num`/`.panel-title`/`.panel-body`.
`.sf-input` retained as the class-based input alias. No new page-local form classes.

## 8. Decisions needing owner sign-off (before implementation)
- **D1** Owner = `shared/_form_styles.html` (`.form-shell`). *(recommend yes)*
- **D2** Keep `.sf-input` as the class-based input (same values) vs converge everything to
  element-scoping. *(recommend keep — some pages need class-based)*
- **D3** `.field` gap: unify to **6px** (form-shell) or **4px** (dashboard-filter)? Either is a
  VISUAL change on the other set. *(recommend 6px = form-shell canonical; dashboards shift 4→6)*
- **D4** Validation: collapse to `.field-error` + one `.form-error` box. VISUAL on the 9+3+3
  divergent pages. *(recommend yes)*
- **D5** Multiselect CC-20 → chip (VISUAL, 2 surfaces). *(recommend yes)*
- **D6** Accounts bespoke (`user_form`/`user_create` `.user-edit-shell`): converge to `.form-shell`
  (VISUAL, 2 pages) or keep as a documented exception? *(recommend keep AS-IS this round —
  bespoke hero; revisit later — to bound Forms scope)*
- **D7** Remove dead `.form-control` + vestigial `.form-card`/`.form-actions`/`.form-errors`? *(recommend remove form-control; keep form-card/actions/errors until their 2-4 consumers migrate)*

## 9. INERT vs VISUAL (preview; full split in the matrix)
- **INERT:** relocate `_form_styles.html`→`shared/` (path-only, value-identical) · tokenize
  form-shell spacing where exact-match · remove dead `.form-control` (0 consumers).
- **VISUAL/rationalization:** `.field` redef convergence (D3) · validation unification (D4) ·
  multiselect chip (D5) · `.sf-input` value alignment if any drift (D2) · accounts/dashboard
  field convergence (D3/D6).

---

**No code. No commits.** Same discipline as Buttons. Per-target plan → [FORMS_MIGRATION_MATRIX.md](FORMS_MIGRATION_MATRIX.md).
Implementation begins only after these decisions (D1–D7) are approved, INERT stages first.
