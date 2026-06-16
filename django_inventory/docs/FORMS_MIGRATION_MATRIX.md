# FORMS MIGRATION MATRIX (Foundation 3)

> **Status:** Per-target plan — **DESIGN ONLY. NO CODE, NO commits.** Evidence: [FORMS_AUDIT_REPORT.md](FORMS_AUDIT_REPORT.md) ·
> Contract: [FORMS_FOUNDATION_SPEC.md](FORMS_FOUNDATION_SPEC.md). Auth pages excluded (Foundation 4).
> **Owner:** Umesh · Created 2026-06-16. After Buttons B-1/B-2/B-3 (`138dafab`).

## 1. INERT vs VISUAL (the required separation)
- **INERT** = value-identical, computed-style/pixel proof (like Buttons B-1/B-2/B-3): relocate
  partial · tokenize exact-match spacing · remove dead code.
- **VISUAL / rationalization** = intentional appearance change, needs before/after + owner
  sign-off (like Buttons B-4): validation unification · `.field` convergence · multiselect chip.

## 2. Per-target matrix

| # | Target | Files | Current → Target | INERT / VISUAL | Risk | Stage |
|---|---|---|---|---|---|---|
| 1 | Relocate `_form_styles.html` | 1 partial + **22 include paths** | `production/_form_styles.html` → `shared/_form_styles.html` | **INERT** (path only; value-identical) | MED (miss an include → broken form) | **F-1** |
| 2 | Tokenize form-shell spacing | `shared/_form_styles.html` | r10→`--radius-md` · fs14→`--fs-md` · on-grid gaps→`--space-*` · panels r14/r12→tokens; off-grid pad (11/14, 18/22, hero 26/30) **DEFER** | **INERT** (exact-match) | LOW | **F-2** |
| 3 | Remove dead `.form-control` system | base.html | delete `.form-control`(+select) — **0 consumers** | **INERT** (no consumer) | LOW | **F-2** |
| 4 | `.sf-input` value alignment | 5 (storefront ×2, _stage_panel_cutting ×2, settlement_detail) | confirm sf-input == canonical input values; tokenize | **INERT if no drift** / VISUAL if drift (verify per-file) | LOW-MED | **F-2** (verify) |
| 5 | Validation unification | ~15 (`field-error` 16 ok · `form-error` single 9 · `form-errors` box 3 · `sf-error` 3) | → `.field-error` (per-field) + one `.form-error` box; retire base inline `.form-error`, `.sf-error`, `.form-errors` | **VISUAL** | MED | **F-3** |
| 6 | `.field` convergence | ~10 redefs (dash-filter ×5 gap4 · stage-panel ×3 · bulk-roll · stage-form) | one owned `.field` (gap per D3); kill page redefs | **VISUAL** (gap/spacing shifts) | MED | **F-4** |
| 7 | Multiselect CC-20 → chip | 2 surfaces (stage-start `045`, barcode_gen `071`) | bare `CheckboxSelectMultiple` → `.worker-chip` via widget | **VISUAL** (adds chips) | MED | **F-5** |
| 8 | Accounts bespoke `.user-edit-shell` | 2 (user_form, user_create) | **KEEP AS-IS this round** (documented exception, D6) → revisit later | — (deferred) | — | deferred |
| 9 | Vestigial `.form-card`/`.form-actions`/`.form-errors` | 2 / 4 / 2 | **KEEP until consumers migrate** | — (deferred) | — | deferred |

## 3. Stage sequence (each: implement → browser-verify 320/375/390/414/1280 → STOP → approve → 1 commit)
| Stage | Work | Kind | Gate |
|---|---|---|---|
| **F-1** | Relocate partial → `shared/`, fix 22 includes | INERT | grep 0 stale `production/_form_styles` refs; every form page computed-identical; render unchanged |
| **F-2** | Tokenize form-shell spacing (exact-match) + remove dead `.form-control` + verify `.sf-input` values | INERT | computed-style before==after on form pages; off-grid untouched; 0 visual |
| **F-3** | Validation → one `.field-error` + one `.form-error` box | VISUAL | before/after the ~15 pages; errors still render per-field (CC-29); owner sign-off |
| **F-4** | `.field` → one owned class; kill page redefs | VISUAL | before/after dashboards + stage panels + bulk-roll; gap delta accepted |
| **F-5** | Multiselect CC-20 → chip (2 surfaces) | VISUAL | before/after stage-start + barcode_gen; chip toggles work; owner sign-off |

**Order:** F-1 → F-2 (both INERT, unblock) → F-3 → F-4 → F-5 (VISUAL, owner-accepted each).
Deferred: accounts bespoke (#8), vestigial form-* (#9).

## 4. Risk hotspots
- **F-1 (22 includes):** mechanical but wide — miss one → form loses all styling. Mitigate:
  grep-verify 0 remaining `production/_form_styles.html` refs after move; smoke every form page.
- **F-3/F-4 (validation + `.field`):** widest VISUAL surface; per-page before/after required;
  some pages currently rely on a page-local `.field`/error style → converging changes their look.
- **F-5 (multiselect):** behavioral (chip toggle + form submit must still post correct values) —
  verify POST payload unchanged (backend untouched).

## 5. Rollback
Per-stage single commit → `git revert`. F-1 relocate: revert restores `production/` path + 22
includes. F-2 inert: value-identical → revert is visual no-op. F-3/F-4/F-5: per-file `git checkout`.
**0 `.py`** except the multiselect F-5 (widget wiring may touch a form/widget `.py`?) → **if F-5
needs a `.py` change it is FLAGGED and split out** (template-first; backend only if unavoidable,
separately approved). All else template/CSS only.

## 6. Backend note
Forms foundation is presentation-only. **Exception risk: F-5 multiselect** — routing CC-20
through the chip widget *may* require a form/widget `.py` edit (set `widget=_WorkerCheckboxes`).
That is the ONLY place backend might be touched; it will be surfaced + separately approved, not
bundled silently. F-1..F-4 = 0 `.py`.

---

**No code. No commits.** Decisions D1–D7 ([SPEC §8](FORMS_FOUNDATION_SPEC.md)) gate implementation.
On approval, **F-1 (INERT relocate)** starts first, browser-verified, STOP, one commit.
