---
id: docs-family-f-modals-report
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# Family F — Modals Consolidation Report (Phase F)

> **Evidence-based synthesis of the HTML-by-HTML audit, Phase F (Modals).** Short by design — the modal
> landscape is intentionally small. Source: [HTML_AUDIT_LEDGER.md](HTML_AUDIT_LEDGER.md) (§Modal-System
> Discovery Inventory + HTML-060). **Evidence + recommendations only. No code / no migration / no UI_COMPONENTS / no promotion.** Date 2026-06-16.

## Headline

**One app-owned modal. No modal fragmentation. No modal foundation required.** (This is a SUCCESS outcome — not every family needs a foundation.)

## 1. Inventory (complete)

Hard signals: **0 `<dialog>`, 0 `showModal()`, 0 bottom-sheet.** Five overlay/dialog systems, but only ONE is an app-owned content modal:

| System | What | Owner | Status |
|---|---|---|---|
| **Crop Modal** (`.cw-crop-modal`) | **the only app-owned custom modal** | `croppable_image.html` widget (2 consumers: category_form 046 + product_form 019) | **HTML-060 audited** |
| Native `confirm()` | destructive-action confirms, 9 pages | **browser** (no app UI) | browser-owned exception — leave as-is |
| fancy-select / fancy-date panels | body-anchored popovers (`role=dialog`) | base.html | **belongs to Select / Date Foundations** — not reopened |
| Mobile sidebar `.overlay` + drawer | nav drawer + backdrop | base.html | **belongs to Navigation / Layout** — not reopened |
| Confirm-DELETE pages (11) | server-rendered confirm PAGES | per-page (uniform) | not overlay modals (Form-Control bucket C) |

## 2. Crop Modal (HTML-060) — verdict

- **Behavior: SOLID.** ESC ✓ · overlay-click ✓ · X ✓ · Cancel ✓ · Apply ✓ · scroll-lock ✓ (body overflow) · z-index 10000.
- **Responsive: GOOD.** Dialog `width:95vw; max-width:720px; max-height:90vh` — browser-verified fits 320/375/414/1280 with **no clip, no overflow**. (The widget's separate inline **preview-box** is the CC-13 mobile-clip — a different part, off-modal.)
- **Relationship: WIDGET-PRIVATE** (only the croppable widget uses it, 2 consumers, same widget). **Not a standalone modal foundation.**

## 3. Finding — MOD-A11Y (modal accessibility/focus gaps; record-only)

The crop modal lacks: **`role="dialog"` · `aria-modal="true"` · `aria-labelledby`** (the "Crop Image" h3 isn't linked) · **focus-trap · focus-return.** Close button has `aria-label="Close crop dialog"` ✓. Effect: assistive tech doesn't announce it as a modal; keyboard focus can escape the dialog and isn't returned to the trigger on close. Same a11y-gap theme as **CC-01** (fancy-panel keyboard). **Recorded only — not fixed, no fix authorized.**

## 4. Recommendation

- **Keep the Crop Modal as a WIDGET-OWNED EXCEPTION.** **Do NOT create a Modal Foundation (TC-6)** — there is only one app-owned modal; a foundation needs a second consumer to justify. Reopen only if a 2nd app-owned modal appears.
- Native `confirm()` = browser-owned; do not replace.
- MOD-A11Y is a candidate fix (add role/aria-modal/aria-labelledby + focus-trap/return to the widget) for a future, separately-approved a11y pass — **not now.**

## 5. Decision asks

1. Approve **"one app-owned modal, no foundation required"** as the Family F outcome.
2. Acknowledge **MOD-A11Y** (record-only; fix deferred to a future a11y pass).
3. Confirm **no TC-6** (no Modal Foundation) unless a 2nd app-owned modal appears.

**Family F evidence FROZEN 2026-06-16.** No promotion / no code. Next family on owner go: **G — Remaining surfaces.**
