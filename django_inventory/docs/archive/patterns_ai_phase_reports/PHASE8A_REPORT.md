> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PLATFORM · PHASE 8A REPORT — ApprovedLayoutUsage foundation
(2026-07-10)

**Status: ✅ 8A COMPLETE — STOPPED. 8B (the Adda chooses) will not
start without approval.**

The Adda↔library contract exists. Service-level milestone exactly as
planned: **zero production files touched, no UI** — proven entirely by
tests. All four owner refinements + freezes F1–F3 are structural.

## What shipped

**`ApprovedLayoutUsage`** (migration patterns_ai **0011**):
- **F2 pointer-only**: `layout` FK PROTECT · `adda` FK PROTECT ·
  `stage_record` FK (null — 8D stamps it) · `recorded_by` · void pair.
  NO placements/geometry/coordinates/rotation/mirror/polygon/
  utilization columns — a test asserts their absence by field name.
  The one sanctioned denorm: `fabric_group` (constraint key only,
  `editable=False`).
- **F1 + refinement 1 structural**: `delete()` always raises; `save()`
  refuses ALL updates except the service-flagged void / stage-stamp
  transitions — reassigning `layout` on an existing row raises (tested).
  Wrong pick = void (reason MANDATORY, DB CheckConstraint) + record a
  new usage; both rows stay forever.
- **Refinement 2 structural**: partial unique
  `(adda, fabric_group) WHERE voided_at IS NULL` — exactly one ACTIVE
  contract per fabric group; BODY + RIB together proven; voiding
  reopens the slot.

**`layout_usage_service`** (the single writer):
- `record_usage` refuses: non-ACTIVE layouts · **STALE layouts — LAW 11
  now gates manufacturing** (proven: confirm a newer geometry version →
  the layout refuses with the STALE message) · cross-product ·
  duplicate active group (message names the void-first path).
- `void_usage` (mandatory reason, idempotent) ·
  `stamp_stage_record` (stamps once; re-stamp to a different SR
  refused — history never rewrites; idempotent on the same SR).
- **Refinement 3 — derived forever**: `marker_content(layout)` counts
  the stored placements per size (design_key `piece:size`; a mirrored
  instance counts once — tested); `expected_pieces(usage, lay_count)`
  = content × lay_count. Computed on every call, persisted nowhere.
- **Refinement 4 honored by omission**: nothing here touches barcodes;
  the chain stays layout → usage → SR → breakdown → barcode, and
  barcode code was not modified (it keeps consuming Breakdown only).

## Tests
NEW `test_phase8a_usage.py` (8): record + denorm/audit · the four
refusals (incl. the LAW-11 STALE gate) · multi-group OK · void keeps
history + reopens slot + blank-reason refused · never-delete +
never-reassign · stage-record stamps once/idempotent/no-rewrite ·
content math {S:2, M:1} hand-verified · expected ×12/×0 + the
pointer-only field-name assertion.
Conscious update: the model-PIN (+ApprovedLayoutUsage, commented).
Three fixture fixes during the run (my test bugs, not app bugs):
WorkflowStage/AddaStageRecord creation idiom (product+stage+order /
workflow_stage=), unique Adda codes, unique (adda, workflow_stage) for
the second SR.

## Battery (counts from output, serial, fresh)
patterns_ai **413/413** (405+8 exact) · full **1298/1298** (1290+8
exact) · `--check` No changes after 0011 · contracts 1 kept/1 broken
pre-existing baseline · **zero production-file diffs** (the milestone's
core promise — the git status of production/ is untouched).

## Browser
None — per the approved plan (no UI in 8A); the evidence is the suite.

**STOPPED — 8A done. 8B (choose page + LAYOUT_PROVIDER inversion +
the pattern-stage Manufacturing Layout panel) awaits your approval.**
