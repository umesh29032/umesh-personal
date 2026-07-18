> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# M5 — Layout Library polish · report
(2026-07-10 · first product-engineering-mode milestone · opened with
M5_READINESS.md, one page)

**Shipped:** library rows now read like the master's shelf — SVG
thumbnail · 📋 recipe chip · lay chip · 📝 notes · "planned on ⟨roll⟩" ·
"supersedes ⟨uid⟩" lineage · approved by/when (all derive-at-read from
the frozen params) · LIVE search over uid/name/recipe/group/lay/status
with an honest no-results line · Marker Recipes block with Deactivate
(soft-state, never deleted; tamper-wall 404). Recipe enum gained the
M4.5 lay split it had missed (migration 0016, choices-only).

**Proof:** tests 6/6 (rows facts · legacy default-safe · search hooks ·
deactivate one-shot + foreign-404) · battery **1384/1384** (1378+6) ·
final patterns_ai 499 · browser on DEV-NICKAR (both rows rich; search
filtered 2→1 live; recipe deactivated live — kept in DB, off lists)
AND golden T-SHIRT (legacy rows clean, no chips, no crashes). Lower =
no library data by design; its ERP flows covered by the battery.

**Caught during browser (fixed before shipping):** ① dct.js
`piecesOfGroup` still read pre-capabilities fields → "×undefined" in
the plan dialog → moved to `caps.*`, fresh-tab verified ("Back ×1 ·
Body ×2 (pair) · Pocket ×2") ② two more in-block multi-line template
comments leaked as text (the repeat regression) → fixed; a sweep
showed the top-of-file multi-line comments are harmless (template
inheritance discards outside-block content) — the rule that bites is
INSIDE blocks only.

**Out of scope (as declared):** station page (waits for volume) ·
models beyond the choices fix · ERP surfaces · engine.

Debt closed: PLATFORM_STATUS §9 item 7 (notes-on-rows).
**STOPPED — M5 complete, awaiting review. Next work arrives from the
factory (the implementation-driven loop).**
