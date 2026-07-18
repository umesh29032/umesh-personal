---
id: docs-date-family-consolidation-report
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# Date Family Consolidation Report (Phase C)

> **Evidence-based synthesis of the HTML-by-HTML audit, Phase C (Dates).**
> Source: [HTML_AUDIT_LEDGER.md](HTML_AUDIT_LEDGER.md) (HTML-024/025 + date controls seen in Phase A:
> HTML-011/012/014/016/017 + Step 0 fancy-date) + [HTML_CANONICAL_CANDIDATES.md](HTML_CANONICAL_CANDIDATES.md)
> (CC-21 + Date ledger + CC-01/CC-02 fancy-date a11y/touch notes; FROZEN 2026-06-15).
>
> **Status: EVIDENCE + RECOMMENDATIONS ONLY.** Nothing implemented. **UI_COMPONENTS.md unchanged.**
> No standardization / migration / fix authorized here.
>
> Date 2026-06-15 · Branch `new_flask_app` · browser-verified (real Chromium, 1280/320/375/390/414).

---

## 0. Coverage + completeness

Full grep of `type=date` / `data-fancy-date` / `DateField` / `DateInput` → every date surface maps to
one of **2 implementations** below. **0 third-party date pickers · 0 standalone-document date controls**
(barcode_print_sheet / worker_report have no dates) · **0 auto-submit or min/max date logic.** All
surfaces browser-verified across Phase A + C.

---

## 1. How many date implementations actually exist?

**TWO.**

| Impl | What | Trigger | Surfaces | Touch | a11y | JS / owner |
|---|---|---|---|---|---|---|
| **fancy-date** | custom body-anchored calendar (base.html `fancifyDate` + `.fancy-date*`) | **opt-in `data-fancy-date`** | **1** — user_form birth_date (Step 0, `7e105b92`) | 44px trigger / 38px day-cells | native input kept (`aria-hidden`); **CC-01 keyboard-grid gap** | base.html (single source) |
| **native** `<input type=date>` | browser UA date control | none (default) | range filters adda(024)/cloth(011)/barcode(025) + form dates purchased(012/014)/advance(016)/settlement(017) | 37–43px (page-CSS-dependent) | native (good — real date input) | none; page-css styles the box only |

No third option (no jQuery-UI/flatpickr/etc.).

---

## 2. Intentional vs accidental differences

**Intentional (documented in UI_COMPONENTS):**
- **Dashboard date-RANGE filters stay native.** Range = two `from`/`to` fields; native is fine; fancy-date
  is single-value-oriented. Deliberate.
- **fancy-date is opt-in** (`data-fancy-date`) — so a field stays native unless explicitly converted.

**Accidental / under-applied:**
- **fancy-date has only ONE consumer (birth_date).** The other **single-value form dates**
  (`purchased_date`, `advance_date`, `settlement_date`) are still **native** — they were never opted in.
  These are exactly the single-value fields fancy-date was built to improve (it fixes native's desktop
  icon-only-click + popup-misposition). So the opt-in is **under-rolled-out**: birth_date got it, the
  sibling form dates didn't (incomplete migration, not a deliberate "these must stay native" decision).
- Native heights vary 37–43px (page-CSS-dependent) — same incidental variance as native selects.

---

## 3. Ownership model (native vs fancy-date)

| | fancy-date | native |
|---|---|---|
| Control logic | **base.html** `fancifyDate` (single JS source) | browser (UA) |
| Styling | **base.html** `.fancy-date*` (single source) | page-css styles the box (filter-card / sf-input); heights vary |
| Trigger | `[data-fancy-date]` attr | implicit (`type=date`) |
| Sustainable? | ✅ single base-owned source | ⚠️ control is the browser's; box-styling is per-page (height drift) |

**Conclusion:** fancy-date has the cleaner ownership (one base-owned source, attribute-triggered). Native's
control is the browser (consistent behavior, but the known desktop UX limitation) and its box-styling is
per-page (the 37–43px drift, mirroring the native-select height story).

---

## 4. True defects vs acceptable variants

**No date defects** — native dates pick + submit; fancy-date picks + persists (Step 0: full round-trip to
DB verified) + Clear; 0 console errors anywhere.

**Known limitations (not defects):**
- **Native desktop UX** — on desktop Chromium only the calendar icon is clickable (not the text), and the
  native popup mispositions under transformed/backdrop-filter ancestors. This is the documented reason
  fancy-date exists. Accepted for range filters; a **latent UX gap on the single-value form dates** that
  weren't opted into fancy-date (§2).
- **fancy-date a11y (CC-01):** no in-calendar keyboard grid-nav / focus-trap / focus-return (shared gap
  with fancy-select). **fancy-date touch (CC-02):** 38px day-cells at 320 (7-col grid floor). Observations.
- **Touch <44px** on native (37–43px); fancy-date trigger is 44px ✅ (day-cells 38px).

**Acceptable variants:** native range filters (intentional); fancy-date for birth_date (works).

---

## 5. Recommended canonical path vs documented exceptions

> **Recommendations only — not authorized, not implemented. UI_COMPONENTS.md unchanged.**

**Recommended canonical (future, separately-approved phase):**
1. **Single-value date fields → fancy-date.** It fixes native's desktop icon-click + misposition and is
   body-anchored. **Roll out `data-fancy-date` to the sibling single-value form dates** (`purchased_date`,
   `advance_date`, `settlement_date`) so all single-value date entry is consistent — closes the §2
   under-application. (birth_date already proves the path.)
2. **Add fancy-date keyboard grid-nav (CC-01) before wide rollout** — shared with fancy-select; do once.

**Keep as documented exceptions:**
- **Dashboard date-RANGE filters stay native** (adda/cloth/barcode `from`/`to`) — range is two fields,
  native is appropriate; fancy-date is single-value-oriented. Explicit exception.
- **Standalone documents** (no base.html → no fancify) would stay native — none exist today (mirrors the
  CC-14 standalone-select lane).

**Cross-family:** CC-01 (keyboard a11y) is shared by fancy-date + fancy-select → fix once for both.

---

## 6. Decision asks (nothing happens without these)

1. Approve the **2-implementation map** (fancy-date opt-in · native default) (§1).
2. Decide whether to roll fancy-date out to the sibling single-value form dates + add CC-01 keyboard-nav,
   in a future standardization phase.
3. Only then: any UI_COMPONENTS.md promotion or code change (separate, reviewed work).

**Until then: no changes.** Evidence frozen; UI_COMPONENTS.md untouched.

---

## 7. Architectural direction (owner 2026-06-15) — recorded preference, NOT a rollout

The owner does **not** want a long-term split between native and fancy-date for **standard application
form data entry**. Goal = a **single source of control**: one date component, one JS owner, one CSS owner,
one canonical pattern, one place for bug fixes + a11y improvements. Recorded preference:

- **Preferred future canonical for single-value form dates = fancy-date** (it already has centralized
  base.html ownership — closest to the single-source goal).
- **Native date controls remain DOCUMENTED EXCEPTIONS** until a future standardization phase:
  - dashboard / report **date-range filters** → native (temporary exception);
  - **standalone documents / print surfaces** → native (exception: base.html absent → no fancify).
- **Principle:** *form data entry should have ONE experience everywhere.* Any future date-control
  standardization moves toward a **single date component**, not multiple competing form-date experiences.

**Still NOT authorized:** no implementation, no migration, no UI_COMPONENTS.md change. This section records
the target architecture so a future, explicitly-approved standardization phase has a direction.
