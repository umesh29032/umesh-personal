# Multiselect Family Consolidation Report (Phase B)

> **Evidence-based synthesis of the HTML-by-HTML audit, Phase B (Multiselect).**
> Source: [HTML_AUDIT_LEDGER.md](HTML_AUDIT_LEDGER.md) (HTML-023/034/035/041 + worker-picker control) +
> [HTML_CANONICAL_CANDIDATES.md](HTML_CANONICAL_CANDIDATES.md) (CC-16/17/18/19/20, FROZEN 2026-06-15).
>
> **Status: EVIDENCE + RECOMMENDATIONS ONLY.** Nothing implemented. **UI_COMPONENTS.md unchanged.**
> No standardization / migration / fix authorized here.
>
> Date 2026-06-15 · Branch `new_flask_app` · browser-verified (real Chromium, 1280/320/375/390/414)
> unless marked. **Distinction the owner requires: DOMAIN ≠ IMPLEMENTATION** — tracked separately below.

---

## 0. Coverage + completeness

Full grep of `ModelMultipleChoiceField` / `CheckboxSelectMultiple` / `<select multiple>` →
**0 native `<select multiple>`**; every multiselect surface maps to one of 4 implementations below.
Two non-control mis-files corrected (usertype_form HTML-034 = no multiselect → Family D; like HTML-006).
**Caveat:** the `barcode_gen` worker-picker surface was not browser-loaded (no Adda at that stage); it
uses the identical raw widget as `pattern_stage` (code-confirmed) → same rendering = CC-20.

---

## 1. How many implementations vs domains?

**FOUR implementations. FOUR domains.** (Worker domain has TWO implementations — the key inconsistency.)

### Implementations
| Impl | Rendering | Selection | a11y | Touch | Visual owner | JS dep | Mobile | Where |
|---|---|---|---|---|---|---|---|---|
| **CC-16** worker-chip | `.worker-chip` checkbox **cards** (custom `_WorkerCheckboxes` widget) | multi | **good** (native checkbox in label) | **52px** ✅ | shared `_form_styles` | none | safe | cutting · layering |
| **CC-17** chip-pick | `.chip-pick` **pill**, checkbox `display:none` + JS `.is-on` | multi | **GAP** (display:none → not tabbable) | 31–34px | `_user_form_styles` **+ duplicated in `stage_form`** (CC-19) | yes (toggle) | safe (wraps) | user skills/extra_roles · stage access |
| **CC-18** perm-matrix | section-grouped **CRUD checkbox matrix** + bulk-toggle | multi | partial (native box; column ctx not per-box) | **13px** | page `role_form` | yes (bulk) | **CLIPS @320 (XC-1)** | role_form permissions |
| **CC-20** Django-default | `<div><label for><input>` **unstyled** (raw `CheckboxSelectMultiple`) | multi | **BEST** (native + explicit `label[for]=id`) | 20px | **none** (framework) | none | safe | cutting_pattern · barcode_gen |

### Domains (selection purpose) — distinct from implementations
| Domain | Implementation(s) used |
|---|---|
| **Worker selection** | **CC-16 (cutting/layering) AND CC-20 (cutting_pattern/barcode_gen)** ← same task, 2 impls |
| **Skill / tag selection** | CC-17 (user skills, extra_roles) |
| **Stage access-control selection** | CC-17 (stage_form access_by_skill/role) — CC-19 duplicate |
| **Permission selection** | CC-18 (role_form CRUD matrix) |

So CC-17 serves 2 domains; the worker domain is served by 2 implementations.

---

## 2. Intentional vs accidental

**Intentional:**
- **CC-18 matrix** — permission editing is inherently a model×CRUD grid; the matrix shape is deliberate.
- **CC-16 chip cards + CC-17 chip pills** — deliberate touch-first chips (chosen over native `<select multiple>`, which fancify skips).

**Accidental / divergent:**
- **Worker selection rendered TWO ways (CC-16 vs CC-20):** cutting/layering got the polished custom
  chip widget (`_WorkerCheckboxes`); cutting_pattern/barcode_gen were left on the **bare Django default**.
  Same "assign workers to a stage" task, two completely different renderings — almost certainly era/author
  divergence, not a design choice.
- **CC-17 CSS+JS DUPLICATION (CC-19):** the `.chip-pick` pattern is copy-pasted (6 rules in
  `_user_form_styles` + 7 in `stage_form` + duplicate inline JS). No single source.

---

## 3. Sustainable ownership

| Owner pattern | Example | Sustainable? |
|---|---|---|
| **Shared partial** (one source) | CC-16 `_form_styles .worker-chip` | ✅ best |
| **Framework default** (no CSS) | CC-20 (Django default) | ⚠️ sustainable but **unstyled → visually inconsistent** with CC-16 |
| **Page-specific, duplicated** | CC-17 (`_user_form_styles` **+** `stage_form` copy) | ❌ fragmented (CC-19) |
| **Page-specific, single-page** | CC-18 (`role_form`) | ⚠️ ok if the matrix stays role-form-only |

**Conclusion:** shared-partial (CC-16) is the only fully sustainable owner. CC-17's duplication and the
CC-16/CC-20 worker split are the maintainability problems.

---

## 4. True defects vs acceptable variants

**No FUNCTIONAL multiselect defects** — all four implementations multi-select correctly, submit, and
(except CC-17) are keyboard-operable; 0 console errors anywhere.

**Real findings (improvable, owner-tracked, NOT fixed here):**
- **CC-18 mobile-clip (XC-1, MEDIUM):** role_form CRUD matrix (365px) clips right at ≤~365px — admin-only,
  deferred. Part of the recurring "content present but unreachable on mobile" class (XC-1: CC-08/13/18).
- **CC-17 keyboard/a11y gap:** checkbox `display:none` → not tabbable, no native checkbox semantics for AT.
  The weakest a11y of the four. (vs CC-20's explicit `label[for]` = best.)
- **CC-19 duplication:** maintainability, not user-facing.
- **Touch < 44px** on three of four: CC-18 13px, CC-20 20px, CC-17 31–34px; only **CC-16 52px** ✅.

**Acceptable variants:** CC-16, CC-18 (matrix is its own thing), CC-20-functionality (native, a11y-good).

---

## 5. What should become canonical, what stays an exception?

> **Recommendations only — not authorized, not implemented. UI_COMPONENTS.md unchanged.**

**Recommended canonical (future, separately-approved phase):**
1. **One chip-checkbox multiselect** — combine the best traits: **native checkbox + explicit `label[for]`
   (CC-20's a11y) + styled chip (CC-16's look) + ≥44px (CC-16's 52px)**. Drop CC-17's `display:none`
   (kills keyboard/AT). Ship it as **one shared partial** → dedupe CC-19 and replace CC-17.
2. **Worker selection = ONE implementation everywhere.** Resolve the CC-16/CC-20 split: make
   cutting_pattern + barcode_gen use the same widget as cutting/layering (`_WorkerCheckboxes`), so the
   worker-roster control is consistent across all stages.
3. **Keep the permission matrix (CC-18) as its own control** (CRUD grid ≠ chip list), but give it a mobile
   strategy (stack/scroll at ≤600 — resolves the XC-1 clip) and larger touch.

**Exceptions (legitimate, keep):**
- The permission CRUD matrix as a distinct pattern (not a chip grid).
- Native `<select multiple>` + fancify is NOT a lane here (fancify skips it; none exist) — the checkbox-chip
  approach is correct for this app.

**Cross-family / owner-tracked:** XC-1 (mobile overflow-masking class, now CC-08/13/18 — 3 occurrences).

---

## 6. Decision asks (nothing happens without these)

1. Approve the **4-implementation / 4-domain map** (§1) as the agreed Multiselect picture.
2. Decide whether to converge worker selection (CC-16 vs CC-20) + dedupe CC-17 (CC-19) in a future
   standardization phase.
3. Only then: any UI_COMPONENTS.md promotion or code change (separate, reviewed work).

**Until then: no changes.** Evidence frozen; UI_COMPONENTS.md untouched.
