# Select Family Consolidation Report (Phase A)

> **Evidence-based synthesis of the HTML-by-HTML audit, Phase A (Selects), 21/21 units.**
> Source evidence: [HTML_AUDIT_LEDGER.md](HTML_AUDIT_LEDGER.md) (HTML-001…022) +
> [HTML_CANONICAL_CANDIDATES.md](HTML_CANONICAL_CANDIDATES.md) (CC-01…CC-15, FROZEN 2026-06-15).
>
> **Status: EVIDENCE + RECOMMENDATIONS ONLY.** Nothing implemented. **UI_COMPONENTS.md
> unchanged** until this report is reviewed. No standardization, no migration, no fixes
> authorized by this document — it informs a future owner decision.
>
> Date: 2026-06-15 · Branch `new_flask_app` · all findings browser-verified (real Chromium,
> 1280/320/375/390/414) unless marked code-read.

---

## 0. Coverage

21 select-family units audited (HTML-001…022; HTML-006 reclassified → Family E as a no-select
table page; HTML-009 covered via its host HTML-008). 1 unit needed a disposable cutting Adda
(HTML-010, owner-provisioned 3-PATTI-004) and 1 needed worker login (HTML-022, utest). Storefront
DataTable/td-actions verified after owner seeded rows. **1 bug fixed in Phase A** — HTML-002
multi-line `{# #}` comment leak (`bcf508f2`), a non-select bug found on a select page.

---

## 1. How many distinct select / selection lanes actually exist?

**FIVE distinct lanes** (browser-confirmed), plus one out-of-scope sibling:

| # | Lane | Markup | Upgraded? | Auto-submit | Height | Visual owner | Seen in |
|---|---|---|---|---|---|---|---|
| L1 | **Form-select** | `<select class>` (literal or Django widget) | fancify → `.fancy-select-trigger` | no (form has a submit btn) | **39px** (sf-input) / 45px (`.field`) | base `.sf-input` **or** shared partial `.field .fancy-select-trigger` | 001·002·003·008·012·013·014·019 |
| L1b | **Form-select, class-less → `--bare`** | `<select>` no class (or page styles it by tag/inline) | fancify → `--bare` fallback | no | **44px** | base `--bare` (PA-14-3 fallback) | 005·007·016·017 |
| L2 | **Native filter-select** | `<select data-no-fancy>` | NO (opt-out) | no (Apply btn) | **37px** | page-scoped `.filter-card select` | 004·011·015 |
| L3 | **Classed filter-select** | `<select class="filter-select" onchange=submit>` | fancify → trigger | **yes** | **40px** | base `.filter-select` | 018·020 (storefront) |
| L4 | **Standalone native** | `<select onchange=submit>`, **no base.html** | NO (fancify absent) | **yes** | **33px** | standalone-doc inline `<style>` | 021 (print sheet) |
| L5 | **Chip single-select** | `<button class=chip>` + hidden input (NOT a `<select>`) | N/A (custom) | no | 34px chips | shared `_worker_report_styles` | 022 (worker report) |
| — | *Multiselect (sibling)* | chip checkbox grid / `<select multiple>` | fancify SKIPS multiple | — | — | `_form_styles` / `_user_form_styles` | _workers_widget, skills/extra_roles → **Family B (deferred)** |

So within "select", L1/L1b/L2/L3/L4 are five `<select>`-or-native variants; L5 is a separate
non-`<select>` paradigm. Auto-submit is orthogonal (works in L3 classed, L4 standalone — CC-09).

---

## 2. Which lanes are intentional vs accidental?

**Intentional (by design, keep):**
- **L2 native filter** — `data-no-fancy` is deliberate; UI_COMPONENTS already says dashboard
  filters keep native. Also the **cloned-row** native (HTML-012 breakup_color) — fancify only
  runs at DOMContentLoaded, so template-cloned `<select>`s must stay native (CC-12). Deliberate.
- **L4 standalone native** — print sheet is a standalone doc (no base.html) by design (CC-14).
- **L5 chip single-select** — deliberate touch-first paradigm for worker capture (CC-15).
- **L1 form-select fancify** — the main intended path.

**Accidental / divergent (not a deliberate design):**
- **L2 vs L3 split for the SAME role (filter a list):** raw_materials/production use native
  `data-no-fancy` in `.filter-card`; storefront uses classed `.filter-select` fancified+auto-submit
  in `.ke-toolbar`. Two idioms, two toolbars, two heights (37 vs 40px), two submit models
  (Apply vs auto) — almost certainly era/author divergence, **not** an intentional distinction (CC-12).
- **L1b `--bare` fallback reached by accident:** pages 005/007 style selects by **tag** (`.scope select`)
  and 016/017 leave them class-less; the fancified `<button>` trigger never receives that CSS, so it
  falls to `--bare`. The page *intended* its own select look; it's silently bypassed (CC-06 (d)).
  Functional (44px) but accidental.

---

## 3. Which styling-owner patterns are sustainable?

Four visual-owner mechanisms observed (CC-06):

| Owner mechanism | Reaches the fancified `<button>` trigger? | Sustainable? |
|---|---|---|
| **(a) base class** — `sf-input` / `.filter-select` (class copied to trigger) | **YES** (class-based) | ✅ sustainable |
| **(b) shared partial co-style** — `.field .fancy-select-trigger` (explicit) | **YES** (targets the trigger) | ✅ sustainable |
| **(c) base `--bare` fallback** — auto-applied when class-less | YES (fallback) | ⚠️ safety net, not a design choice |
| **(d) page tag-CSS / inline style** — `.scope select` / `style="…"` | **NO** (hits the hidden native, not the button) | ❌ unsustainable — silently bypassed |

**Conclusion:** only **class-based** ownership (a/b) reliably styles the trigger. Tag/inline (d) is the
anti-pattern (the trigger falls to `--bare`). The `--bare` fallback (c) is the reason (d) never *breaks*
visibly — but it means the page's intended styling is lost. Sustainable canonical owner = **a class on
the `<select>` + base/partial class-based CSS**.

---

## 4. True defects vs acceptable variants

**True defects in the select controls: NONE.** Every select/selection across all 21 units
fancifies (or stays native by design), opens, picks, submits, and fires `onchange`/auto-submit
correctly, with 0 console errors and no select-caused overflow. The only Phase-A *bug* (HTML-002
comment leak) was non-select (fixed). CC-08 (td-actions clip) and CC-13 (croppable clip) are a
**table** bug and a **shared-widget** bug respectively — not select defects.

**Acceptable variants (legitimate, keep):** L2/L4/L5 (intentional, §2); L1b `--bare` (works, and at
**44px is actually the best touch target of any lane**).

**Consistent shortfalls (improvable, not defects):**
- **Touch height < 44px** is systemic for the class-styled lanes: L1 sf-input **39px** (CC-05, 9
  instances), L2 native filter **37px** (CC-07), L3 classed filter **40px**, L4 standalone **33px**.
  Only L1b `--bare` meets 44px (PA-14-3 set it). The owner's mobile-first rule wants ≥44px.
- **a11y gaps (observations, not bugs):** fancy-select panel has no keyboard grid-nav / focus-trap /
  type-ahead (CC-01); chip single-select has no `role=radiogroup`/`radio`/`aria-pressed` (CC-15).

---

## 5. What should become canonical, what stays an exception?

> **Recommendations only — not authorized, not implemented. UI_COMPONENTS.md unchanged.**

**Recommended canonical (for a future, separately-approved standardization phase):**
1. **Form-select canonical = `<select>` + a styling CLASS (`sf-input`) + fancify.** Class-based owner
   (a/b) reaches the trigger; deprecate tag-CSS/inline select styling (lane d) → migrate those pages to
   put a class on the `<select>` (or co-style `.fancy-select-trigger`). Removes the accidental `--bare` cases.
2. **One touch-height standard = 44px.** Raise `.sf-input` (and classed `.filter-select`) `min-height`
   to 44px to match the `--bare` fallback + the mobile-first rule. Single base.html rule; affects every
   form/filter select. (This is the CC-05/CC-07 resolution — global, owner-gated.)
3. **Converge the filter-select split (L2 vs L3).** Pick ONE filter-select lane app-wide (recommend the
   class-based fancified path with auto-submit, since auto-submit is verified safe (CC-09) and class-based
   styling is sustainable), OR formally bless the native `.filter-card` lane and make storefront match it.
   Decide in the **Filter family (Phase E)** — it spans `.filter-card` vs `.ke-toolbar` too.

**Keep as documented exceptions (do NOT force into the `<select>` canonical):**
- **L4 standalone native** (print sheet / chromeless embeds) — no base.html, so no fancify; native is
  correct. Document the standalone/native lane explicitly.
- **L5 chip single-select** — its own canonical (touch-first worker capture); not a `<select>`.
  If standardized, give it `role=radiogroup`/`radio` + 44px chips (addresses CC-15 a11y/touch).
- **Cloned-row native** (data-no-fancy for JS-cloned rows) — keep; a fancify-after-clone helper
  (`window.fancifySelects` on clone) could remove the opt-out later, but native is safe today.

**Cross-family items (out of this report, owner-tracked):** CC-08 (Family E td-actions, narrowed),
CC-11 (Family D money-form interaction), CC-13 (Family F shared croppable widget), CC-01 (keyboard
a11y — shared by fancy-select + fancy-date), CC-04 (template-hygiene `{# #}`, signup_otp pending).

---

## 6. Decision asks for the owner (nothing happens without these)

1. Approve/adjust the **5-lane model** (§1) as the agreed Select-family map.
2. Decide which recommendations in §5 become a future **standardization phase** vs stay evidence.
3. Only after that: any UI_COMPONENTS.md promotion + any code change (separate, reviewed work).

**Until then: no changes.** Evidence frozen; UI_COMPONENTS.md untouched.
