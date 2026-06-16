# Form-Control Consolidation Report (Phase D)

> **Evidence-based synthesis of the HTML-by-HTML audit, Phase D (Form controls + validation).**
> Source: [HTML_AUDIT_LEDGER.md](HTML_AUDIT_LEDGER.md) (HTML-026…048 + 070/071 + the §Form-Control
> Completeness Inventory) + [HTML_CANONICAL_CANDIDATES.md](HTML_CANONICAL_CANDIDATES.md) (Form-control
> evidence ledger, validation-families tracker, workflow-protection tracker, CC-05/13/16/17/19/20/22/23/24/25/26/27/28/29/30, XC-1).
> Companion: [AUTH_FAMILY_CONSOLIDATION_REPORT.md](AUTH_FAMILY_CONSOLIDATION_REPORT.md) (the auth subset, already accepted).
>
> **Status: EVIDENCE + RECOMMENDATIONS ONLY.** Nothing implemented. **UI_COMPONENTS.md unchanged.**
> No standardization / migration / promotion authorized here. (2 isolated per-page bugs WERE fixed +
> committed during the audit with explicit owner approval — CC-27 `20fccbd7`, CC-29 `2e5910b9`; those are
> not part of this report's recommendations.)
>
> Date 2026-06-16 · Branch `new_flask_app` · browser-verified (real Chromium 1280/320/375/390/414) where
> reachable; dormant/flow-gated surfaces honestly marked. **CC-22 · CC-23 · CC-24 · CC-30A · CC-30B · XC-1 ·
> CC-13 · CC-28 are kept SEPARATE — not merged.**

---

## 0. Coverage + completeness

Full grep of `<form method` app-wide → **59 form-bearing templates**, cross-referenced vs **48 `### HTML`
records** + 070/071. Form-Control **input** inventory CONFIRMED COMPLETE:
- **~23 input-form units audited** (auth 026-032 · management 033/034/001/002 · expense 036/037/016/017 ·
  production 038/039/040/041/042/043/044/045/048/070/071 · storefront 046/019 · raw_materials 047/012/013/014 · inventory 035).
- **CC-20 closed** (both worker-picker surfaces browser-confirmed: cutting_pattern 045 + barcode_gen 071).
- **Bucket C** (11 confirm/delete dialogs) = representative-verified uniform, 0 inputs → covered/out-of-scope.
- **Bucket D** (list/nav POST forms) = action/filter → out-of-scope (Select family / chrome).
- **Dormant/unreachable** (signup 031, signup_otp 032, otp 029) = honestly marked code-read.

---

## 1. How many distinct form-control implementations actually exist?

There is **no single form-control implementation.** The evidence shows **three orthogonal axes**, each with
multiple variants:

### 1a. Form-CSS / shell ownership — ~6 systems
| # | System | Owner | Consumers | Verdict |
|---|---|---|---|---|
| 1 | **Auth standalone** | each page's own inline `<style>` | 7 auth pages | ❌ fragmented (CC-22) |
| 2 | **Management shared** `_user_form_styles.html` (`.field`/`.chip-pick`) | shared partial | user_create/user_form/skill_form | ✅ positive (CC-26) |
| 3 | **Production shared** `production/_form_styles.html` (`.form-shell`/`.panel`/`.form-grid`) | shared partial | **6 — cross-app** (039/042/043/047/048/070) | ✅✅ strongest (CC-26 note) |
| 4 | **base.html global** `.form-card`/`.form-section` | base.html | pattern_form 040 | ⚠ under-built (no `.form-control` → CC-30A) |
| 5 | **Storefront** base-global `.sf-input`/`.sf-error` + page-scoped `.cat-*` | base.html + page | category 046 / product 019 | ⚠ shared primitives + page layout |
| 6 | **Page-scoped one-offs** | each page | `.expense-form` 037 · `.report-review` 038 · `.ps-edit` 044 · `.stage-form` 041 · panels 045/071 | ⚠ drift risk |

Plus a **cross-cutting input primitive**: **`.sf-input`** (base.html-defined) is borrowed across production
(039/042/043/047), expense (036), storefront — a de-facto shared input class (~39–41px).

### 1b. Validation / interaction families — 8 (tracked separately)
1. Auth **messages framework** (6 auth pages) [CC-24-B]
2. Auth **`form.errors` top-aggregate** (signup ONLY) [CC-24-A]
3. **Management per-field inline** `.field-error` + non_field + native (shared `_user_form_styles`) [CC-26]
4. **Expense action-form** (raw POST `name=action` + messages + native-numeric + `confirm()`) [036]
5. **Expense generic-loop** (`{% for field %}` + `.errs` + server cleans + native; page-scoped) [037]
6. **Production raw-POST bulk/per-row** (no Django form, native + server-state lock; +inline-edit 044, +stage-panel 045/071) [038]
7. **Production form-shell** (Django Form, per-field `.field-error`, novalidate→server, shared `_form_styles`; +money-armor 042, +generic-loop 047) [039]
8. **Storefront** (native `required` + per-field `.sf-error` + `.form-errors` list) [046/019]

Rendering reduces to 4 modes: **messages-framework** · **form.errors-aggregate** · **per-field-inline** ·
**action-form (no inline render → messages)**.

### 1c. Touch-target heights — inconsistent (CC-05 inputs / CC-25 buttons)
bare 19px (040) · inline-edit 29px (044) · verified 34px (038) · `.sf-input` 39–41px (most) · CC-20 checkbox
13px (045/071) · permission-matrix 13px (CC-18) · **CC-16 worker-chip 52/44px ✅** · buttons 38–40px ·
confirm-dialog button 44px ✅. **Only the CC-16 chip + confirm-dialog button consistently meet 44px.**

---

## 2. Intentional vs accidental divergence

**Intentional (legitimate):**
- Auth pages **standalone** (pre-auth, no app chrome) — correct.
- **OTP 6-box widget**, **CC-16 chip multiselect**, **money-armor** (settled refusal), **confirm-dialog**
  uniform pattern, **native date/number** inputs, **inline-edit table** (044).

**Accidental / divergent (the findings — kept separate):**
- **CC-22** auth form-system dup (7 copies, login_password drifted from login).
- **CC-23** OTP-widget dup (2-full + 1-reduced drift).
- **CC-24** auth validation split (signup `form.errors` vs everyone-else messages).
- **CC-30A** pattern_form bare 19px inputs (widgets lack `.form-control`).
- **CC-30B / XC-1** custom fixed 2-col grids clip on mobile (040 inline · 041 `.field-grid-2`).
- **CC-13** croppable widget 400px fixed-width clips (019 + 046).
- **CC-28** missing favicon → console 404 app-wide (cosmetic).
- Worker-domain **CC-16(chip) vs CC-20(bare)** split (same task, two renderings).
- **CC-19** `.chip-pick` CSS/JS duplicated (user-forms + stage_form).
- (Fixed during audit: **CC-27** slug-pattern v-mode, **CC-29** field-error swallow.)

---

## 3. Sustainable ownership models

| Owner pattern | Example | Sustainable? |
|---|---|---|
| **Shared partial, responsive** | production `_form_styles.html` (6 consumers, cross-app; `.form-grid` collapses ≤768) | ✅✅ **best — proven** |
| **Shared partial** | management `_user_form_styles.html` (3 consumers) | ✅ good |
| **Base-global primitive** | `.sf-input` (cross-app input class) · `.table-responsive`+data-label · auto-fit grids | ✅ good (responsive) |
| **Base-global shell, incomplete** | base.html `.form-card` (no `.form-control` → bare inputs) | ⚠ under-built |
| **Page-scoped one-off** | `.expense-form` · `.report-review` · `.ps-edit` · `.stage-form` · panel `<style>` | ⚠ drift risk; OK only if truly page-unique |
| **Standalone copy-paste** | auth ×7 | ❌ fragmented (CC-22) |

**Decisive evidence:** pages on the **shared** `_form_styles.html` `.form-grid` (039/043/047) are mobile-safe;
pages that **rolled their own** grid (040/041) hit XC-1. **Shared ownership correlates with correctness;
custom/page-scoped correlates with divergence + bugs.** The production shared foundation is the only owner
proven across multiple domains AND apps.

---

## 4. True defects vs acceptable variants

**True defects — FIXED + committed (owner-approved, not part of recs):**
- **CC-27** `20fccbd7` — slug `pattern` invalid under Chromium `v`-flag (skill_form/usertype) → console error + dropped validation.
- **CC-29** `2e5910b9` — pattern_form swallowed field errors (only non_field rendered).

**True defects — OPEN (record-only, owner-deferred; kept separate):**
- **CC-30A** — pattern_form bare 19px inputs (widgets lack `.form-control`). Styling/touch.
- **CC-30B / XC-1** — custom 2-col grids clip right column on mobile, masked by `overflow-x:hidden` (040 + 041); **XC-1 = 5 occurrences** (CC-08/13/18 + 040 + 041). Mobile-first violation.
- **CC-13** — croppable widget `.cw-preview-box` 400px fixed (no max-width) clips storefront forms (019 + 046); shared-widget defect.
- **CC-28** — missing favicon → `/favicon.ico` 404 every page. Cosmetic.
- **Auth dormant** — signup throttle-message invisible + signup_otp multi-line `{# #}` leak (CC-04); both dormant/unrouted (fix-on-re-enable, per Auth Report).

**Acceptable variants:** native date/number; auth standalone (pre-auth); confirm-dialogs; money-armor;
CC-16 chip; OTP widget; inline-edit table.

---

## 5. What should become canonical vs documented exceptions

> **Recommendations only — not authorized, not implemented. UI_COMPONENTS.md unchanged.**

**Recommended canonical (future, separately-approved standardization phase):**
1. **One shared form foundation = the production `_form_styles.html` model** — `.form-shell` + numbered
   `.panel` + **responsive `.form-grid`** (already collapses ≤768) + per-field `.field-error` + `.sf-input`.
   It is the only owner proven cross-app (6 consumers) AND mobile-safe. Management `_user_form_styles.html`
   aligns with it (per-field-inline). Migrate page-scoped one-offs + base `.form-card` onto it over time.
2. **One input primitive** = `.sf-input` (already cross-app), but **raise to ≥44px** (currently 39–41px) to
   meet touch — resolves the CC-05 input-height spread.
3. **One validation rendering** = per-field inline `.field-error` + top non-field (the management/production
   model). Converge **signup (CC-24)** + the storefront `.sf-error` variant onto it.
4. **One responsive layout rule** = always use the shared `.form-grid` / `.table-responsive` / auto-fit;
   **never a custom fixed 2-col grid** (resolves XC-1 / CC-30B). Give the croppable widget `max-width:100%`
   (resolves CC-13).
5. **One worker-picker** = converge CC-16(chip) vs CC-20(bare) to a single styled, ≥44px, a11y-correct widget.

**Documented exceptions (keep):**
- **Auth standalone** (pre-auth, no app chrome) — but give it ONE shared *auth* foundation (per Auth Report
  CC-22), not 7 copies.
- **Confirm-dialogs** (button family, no inputs) — uniform already; keep as their own minimal pattern.
- **Inline-edit tables** (044) — table-responsive stacking is correct; legitimately page-shaped.
- **Money-armor pages** (036/038/042) — workflow-protection is a separate, valuable track; keep.
- **Native date/number** for appropriate fields (per Date Report: single-value form dates → fancy-date later).

---

## 6. Enterprise architecture direction the evidence supports

**Target:** one canonical component per family · one owner · one styling source · one behavior source ·
documented exceptions only.

**How close is the form-control family today?** **PARTIALLY there — a split picture:**
- **Strong core:** the production `_form_styles.html` foundation already demonstrates the target —
  one shared owner, one responsive grid, per-field validation, reused across 6 surfaces in 3 apps. Management
  mirrors it. The base-global primitives (`.sf-input`, `.table-responsive`, auto-fit) reinforce it.
- **Far from target on the edges:** **8 validation families**, **~6 CSS systems**, **8+ touch heights**, the
  **auth 7-copy fragmentation** (CC-22/23/24), the **base `.form-card`** under-built page (CC-30A/29), and a
  **long tail of page-scoped one-offs** + custom grids (XC-1) + the shared croppable defect (CC-13).

**Direction the evidence supports:** **consolidate onto the production `_form_styles.html` model app-wide** —
adopt it (or its equivalent) as the single form foundation, retire the auth copies + base `.form-card` + the
page-scoped one-offs, standardize `.sf-input` to ≥44px, standardize per-field-inline validation, and forbid
custom fixed grids in favour of the shared responsive grid. The audit's own data (shared = safe, custom =
XC-1) is the argument. This is a **future standardization project**, not this audit.

---

## 7. Decision asks (nothing happens without these)

1. Approve the **3-axis map** (§1: ~6 CSS systems · 8 validation families · inconsistent touch) as the agreed
   Form-Control picture.
2. Confirm **CC-22 · CC-23 · CC-24 · CC-30A · CC-30B · XC-1 · CC-13 · CC-28 stay separate** findings (this
   report keeps them separate).
3. Endorse (or not) **production `_form_styles.html` as the recommended canonical form foundation** for a
   future standardization phase.
4. Decide disposition of the **open defects**: CC-30A (bare inputs), CC-30B/XC-1 (custom grids → shared grid),
   CC-13 (croppable max-width), CC-28 (favicon) — fix now per-page, batch later, or defer to standardization.
5. Decide whether to pursue, in a future separately-approved phase: a single input primitive (≥44px), single
   validation rendering, single worker-picker (CC-16/CC-20), and the auth shared foundation (Auth Report).
6. Only then: any UI_COMPONENTS.md promotion or code change (separate, reviewed work).

**Until then: no changes. Form-Control evidence FROZEN. UI_COMPONENTS.md untouched.**

---

## Owner decisions — RECORDED 2026-06-16 (report ACCEPTED)

1. ✅ Approved the **3-axis Form-Control map** (CSS ownership systems · validation families · touch-target variance).
2. ✅ **Keep findings separate:** CC-22 · CC-23 · CC-24 · CC-30A · CC-30B · XC-1 · CC-13 · CC-28.
3. ✅ **Architectural direction approved:** `production/_form_styles.html` = **preferred future canonical form-foundation candidate**.
4. ❌ No standardization work yet. 5. ❌ No UI_COMPONENTS.md update. 6. ❌ No merging findings. 7. ❌ No broad refactors. **Audit phase = evidence collection still.**

**Recorded approved candidate foundations (cross-family, future canonical — NOT yet implemented):**
- **Forms → `production/_form_styles.html`**
- **Dates → fancy-date** (Date Report §7)
- **Selects → class-owned `fancify` path** (Select Report)
- **Multiselects → shared checkbox-chip direction** (future candidate; Multiselect Report)
- **Auth → one shared auth foundation** (Auth Report CC-22; still 7 copies today)

No implementation phase authorized. Next family: **E — Tables**.

## Form-Control evidence — FROZEN 2026-06-16

Inventory complete (input forms + confirm-dialog rep). Findings kept separate: CC-22/23/24 (auth) ·
CC-30A/30B (pattern_form) · XC-1 (×5) · CC-13 (×2) · CC-28 · plus CC-05/16/17/19/20/25/26 + workflow-protection
+ validation-families trackers. Fixed: CC-27 `20fccbd7`, CC-29 `2e5910b9`. Boundaries stable. No promotion /
no standardization until owner decision asks (§7) are answered. Next family on owner go: **E — Tables**.
