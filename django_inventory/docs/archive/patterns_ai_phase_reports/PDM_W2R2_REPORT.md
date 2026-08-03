> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PDM · W2R2 REPORT — the final preparation-page refinement
(2026-07-08)

**Status: ✅ W2R2 COMPLETE — STOPPED. On the owner's confirmation the
PDM stage design FREEZES PERMANENTLY; W3 (acceptance + close) next;
then all engineering effort moves to the Cutting Table.**

The owner's final refinement, implemented exactly: **both pages now
feel like preparation (task completion), not information display.**

## Manager — task-board cards (Trello feel)
- **Traffic-light tiers** (deterministic rule, facade-computed):
  🟢 `Ready for Cutting ✓` = zero required gaps ·
  🟡 `Needs Attention` = 1–2 required gaps (and something confirmed) ·
  🔴 `Missing Designs` = 3+ required gaps or nothing confirmed yet.
  Missing names listed on the card; progress bar colours follow the
  tier. Button stays the owner's label: **[Manage Pattern Designs]**.

## Library — "Preparing Size L" (psychology: preparing, not browsing)
- Page renamed: title + heading = **`Preparing Size ⟨X⟩`**; subtitle
  "prepare every Pattern Design this size needs, top to bottom".
- **Task buckets with headers, todo-first (Trello order):**
  `✖ Missing (n)` → `⚠ Needs Work (n)` → `✓ Completed (n)` — empty
  buckets hide; the operator reads only the top until it's green.
- **Per-row "can-I-cut" mini-checklist** (the owner's strongest ask):
  `Geometry ✓/✖ · Reference ✓/✖ · Confirmed ✓/✖ · DXF ✓/✖` on every
  row, honest booleans from the facade (`checks` — contract-additive):
  geometry = drawn at all · confirmed = design truth · dxf =
  exportable (= confirmed) · reference = piece illustration present.
  Contextual primary action unchanged (+ Add geometry / Confirm → /
  Edit →).

## Live proof (DEV-HUB, real gaps)
`Preparing Size M`: **✖ MISSING 1** (Pocket — `Geometry ✖ Reference ✖
Confirmed ✖ DXF ✖` + [+ ADD GEOMETRY]) → **⚠ NEEDS WORK 1** (Cuff —
`Geometry ✓ Confirmed ✖` + [CONFIRM →]) → **✓ COMPLETED 2** (Back/Front
— `Geometry ✓ Confirmed ✓ DXF ✓`, dims + area + updated + DXF link)
(`w2r2_preparing_m.png`). Manager tiers live (`w2r2_manager_tiers.png`).
The screenshot IS the owner's sketch.

## Tests
+3 W2R2 (traffic-light tiers incl. 🔴→🟡 transition on data change ·
bucket order todo-first · per-row checklist ✓/✖ both ways) — suite now
17; affected block green. One test-fixture fix (bucket-order probe
needed a size having both buckets). Battery: **345/345 OK** ·
**1230/1230 OK** (serial, fresh) · migrations **No changes detected** · contracts **unchanged — 1 kept, 1 broken (pre-existing target)**.
Facade change = contract-ADDITIVE only (`tier`, `checks`);
`design_key` and all prior keys untouched — the CT contract stands.

**STOPPED — awaiting: (1) the owner's PERMANENT PDM FREEZE
confirmation, (2) W3 approval (General-size hand-off polish · perf
unify · vocabulary sweep · PDM acceptance on the real T-SHIRT · stage
close). After W3: the Cutting Table.**
