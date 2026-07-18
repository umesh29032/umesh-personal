# P1 — BLOCK 3D REPORT: Marker Usage & Outcome Recording (2026-07-07)

**Status: ✅ BLOCK 3D COMPLETE — STOPPED. Block 3E will NOT start without
explicit owner approval.**

## Scope compliance
Usage + outcome recording ONLY, on the existing single-writer services. No
yield board, no dashboards, no product summaries, no AI. Views stay
parse→gate→delegate — the one behavior change this block is a SERVICE fix
(below), exactly where it belongs. No schema change (`makemigrations --check`
clean).

## Workflow summary — the memory loop is now closed, live

- **Record usage** `markers/<ref>/usage/new/` — adda select scoped to the
  marker's product (50 latest), plies, repeats, optional measured width,
  notes. Service owns every rule; its refusal messages (including the
  marker's own retirement reason) render as form errors.
- **Record outcome** `usages/<pk>/outcome/new/` — raw facts only, ALL
  optional (honest-NULL); the UI speaks **metres**, conversion to integer mm
  happens at the edge through the I-4 home (`units.m_to_mm`, HALF_UP —
  45.0005 m → 45001 mm, test-pinned). After save the derived metric is
  **flashed, never stored**: *"96.00 m per 100 garments (derived, not
  stored)"*, or the honest-NULL variant when facts are missing.
- **Void** — prompt-for-reason button on the detail row (the Report-Review
  pattern); voided rows stay visible with their reason.
- **Marker Detail panel 4 "Usage & outcomes"** — one row per usage: adda,
  plies×repeats, width, date; then either its m/100 metric, "facts recorded,
  metrics pending (—)" for honest-NULLs, or a "record outcome →" CTA.
  Biography updates automatically (2C spine — zero new event code).

## Live browser proof (screenshots archived)

`3d_usage_form_390` · `3d_outcome_form_390` · `3d_detail_after_390` ·
`3d_detail_desktop`. Walk: MRK-000002 → usage on **LOWER-001** (40 plies × 2,
width 1088) → outcome (48.00 m, 50 cut, 49 packed, 0.80 m leftover) → flash
**96.00 m per 100 garments** → summary card now shows Avg m/100 = 96.00 with
n=1. The factory's first complete photo→marker→usage→outcome record exists.

## Service fix shipped (caught by this block's tests)

`record_outcome` now refuses a second outcome per usage with a friendly
message ("facts never change; void the usage and re-record") — previously the
OneToOne constraint fired as a raw IntegrityError. Fixed in the SERVICE, not
the view, so every future caller inherits it.

## Test summary — patterns_ai suite now **85 tests, all green**

Usage via UI (+biography row asserted) · unusable-marker reason surfaced in
the form · void via UI: empty reason refused, real reason kept in history ·
outcome via UI with metres→mm conversion pinned · derived metric flashed AND
rendered on detail · honest-NULL outcome renders "metrics pending" ·
double-outcome friendly error · `update_outcome_facts` stays service-only
(null-fill tested; no UI by scope) · worker 403 on GET+POST of every new
endpoint including void (and the void provably did nothing). Full
manufacturing suite serial ✅ · migrations clean ✅ · contracts unchanged ✅.

## Engineering review

1. **Technical debt:** adda dropdown capped at 50 latest — right until real
   volume; fact-fill (`update_outcome_facts`) has no UI by scope — the
   service path is tested and documented as the correction route.
2. **Performance:** detail derives metrics per usage at read — by design
   (F6); trivially cheap at per-marker volumes.
3. **Security:** all three endpoints management-gated (403s proven, void
   verified side-effect-free on refusal); CSRF on all forms; reasons stored
   verbatim, rendered escaped.
4. **Long-term maintenance:** zero business rules in views; the flash message
   explicitly says "(derived, not stored)" — the F6 philosophy is now
   user-visible language.
5. **Future ADR candidates:** none new.

## Findings
The Digital Memory era's full loop (photo → marker → usage → outcome →
honest metrics) is now WORKING SOFTWARE end-to-end. The remaining P1 pieces
from the master plan are the yield board (aggregation over these facts) and
SuggestionEvent/CalibrationMat surfacing.

**Awaiting owner approval for Block 3E.**
