> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PHASE 8 IMPLEMENTATION PLAN — Adda consumes the library
(2026-07-10 · PLAN ONLY — no code, no migrations · four atomic
milestones, each gated by the full discipline · the three owner FREEZES
are load-bearing constraints throughout)

## PERMANENT PLATFORM RULE (owner freeze, recorded post-8A — binding on 8B/8C/8D and every future milestone)

**ApprovedLayoutUsage forms a permanent manufacturing timeline:**

```
Approved Layout → ApprovedLayoutUsage → (void, with reason, if required)
                                       → NEW ApprovedLayoutUsage
```

History is never rewritten. Never reassigned. Never deleted. Every
manufacturing event remains traceable forever. Any future change that
would edit, repoint, or remove a usage row violates this rule — the
correct move is always VOID (reason mandatory) + a new record. The 8A
model enforces this structurally (save/delete guards, tested); this
paragraph makes it a documented LAW so no later milestone can weaken
those guards "for convenience".

## PERMANENT PLATFORM RULE — THE MANUFACTURING COUNT HIERARCHY
(owner freeze, recorded pre-8C — three concepts, never confused)

1. **Marker Content** (Approved Layout →) — "how many pieces of each
   size in ONE marker?" Permanent; derived ONLY from the stored
   approved layout; never edited; never stored elsewhere.
2. **lay_count** (Layering →) — "how many plies are actually laid?"
   The ONLY source of truth for plies. Nothing inside patterns_ai owns
   or duplicates it — the provider returns CONTENT ONLY; production
   multiplies by ITS lay_count.
3. **Expected Pieces** = Marker Content × lay_count — an OPERATIONAL
   EXPECTATION only. NOT manufacturing truth, NOT inventory truth, NOT
   cutting truth, NOT payment truth. It exists solely to help the
   cutting master detect mistakes.

**Expected vs Actual:** the cutting operator always has authority.
Expected numbers are advisory; actual cutting remains the
manufacturing truth. Warnings explain differences — they never
silently modify data, never overwrite operator input.

## The three freezes, mapped to structure
- **F1 · Usage is history forever** → `ApprovedLayoutUsage` is
  append-only: `delete()` raises, "stop using" = soft-void with a
  mandatory reason. Nothing in any milestone deletes manufacturing
  history.
- **F2 · Adda never copies layout data** → the usage row is a POINTER
  ONLY: layout FK + adda FK + audit. NO placements, geometry,
  coordinates, rotation, mirror, polygon or utilization columns —
  every consumer derives from `ApprovedLayout.candidate` at read.
  (One deliberate denorm: `fabric_group`, copied from the layout at
  record time purely to make the one-active-per-(adda, group)
  constraint a DB constraint — it is an immutable attribute of an
  immutable row, frozen twice.)
- **F3 · The manufacturing contract** → once a usage exists, marker
  content → expected pieces → bundles → barcodes → verification all
  DERIVE from the approved layout; nobody re-enters marker information
  (8B/8C wire exactly this consumption chain).

## The wall, solved once (used by 8B–8D)
Production may never import patterns_ai. Two house patterns, both
already owner-approved and in the codebase:
- **URL hand-off** (M4/P1 pattern) for the CHOOSE action — the
  selection page + writer live in patterns_ai.
- **Dependency inversion** (the P3 `ARCHIVE_VALIDATORS` pattern) for
  DISPLAY + gates: production defines a registry
  (`cutting_pattern.LAYOUT_PROVIDER`, default None); patterns_ai
  registers a read-only provider in `apps.ready()`. The provider
  returns plain dicts (uid, name, render URLs, expected counts,
  has_usage) — production consumes data, never modules.

---

## 8A · ApprovedLayoutUsage foundation (patterns_ai only — zero production files)

**Scope**: the model + single writer + derivation helpers. No UI.
- `ApprovedLayoutUsage` (migration patterns_ai 0011): `layout
  FK(ApprovedLayout, PROTECT)` · `adda FK(production.Adda, PROTECT)` ·
  `stage_record FK(production.AddaStageRecord, null, PROTECT)` ·
  `fabric_group` (F2 denorm, above) · `recorded_by/at` ·
  `voided_at/void_reason` · guards: `delete()` raises (F1); `save()`
  update path = service-flagged void/stamp transitions only.
  Constraint: unique active (adda, fabric_group)
  (partial unique, `voided_at IS NULL`) — readiness R-5 structural.
- Single writer `layout_usage_service`: `record_usage(*, user, adda,
  layout)` REFUSES non-ACTIVE layouts · **STALE layouts (Law 11's
  enforcement point — `layout_is_stale` finally gates something)** ·
  layout.product ≠ adda.product · duplicate active (adda, group).
  `void_usage(*, user, usage, reason)` — reason mandatory, history
  kept. `stamp_stage_record(*, usage, stage_record)` (used by 8D).
- Read helpers (derive-at-read, F2/F3): `marker_content(layout)` →
  per-size piece counts by COUNTING stored placements (`design_key =
  piece:size`; no cut-plan input needed — readiness §5.3) ·
  `expected_pieces(usage, lay_count)` = content × lay_count.

**Files (~5 + 1 migration)**: `models/layouts.py` (+usage model) ·
migration 0011 · `services/layout_usage_service.py` (NEW writer) ·
models `__init__` + purity-pin conscious update · NEW
`tests/test_phase8a_usage.py`.
**Reused**: `layout_is_stale` · placements JSON · MarkerUsage as the
design template (shape only — no code shared, different model).
**Tests**: refusals ×4 (stale/inactive/cross-product/dup-group) ·
void-not-delete + delete-raises + reason-mandatory · second group OK ·
content math (multi-instance, multi-size, mirrored counted once) ·
expected × lay_count · model-pin conscious update.
**Browser**: none (no UI) — service-level milestone; report shows test
evidence only.
**Risks**: partial-unique index syntax (Django `UniqueConstraint(
condition=...)` — supported; NOTE house lesson: Django 5.0.1 uses
`condition=` for UniqueConstraint but `check=` for CheckConstraint) ·
purity pin update (conscious, commented).
**Acceptance**: all writer refusals proven · history immutable ·
content math hand-verified · battery green · zero production changes.

## 8B · The Adda chooses (consume + display — still zero enforcement)

**Scope**: the choose flow + the pattern-stage panel showing the
contract.
- patterns_ai **choose page** `table-usage/<adda>/` (management-gated):
  lists ACTIVE, non-stale layouts of the Adda's product grouped by
  fabric group (uid · V · name · width · length/util · render link);
  POST → `record_usage`; existing usages shown with [Void…]
  (reason field, F1). Layouts render via the EXISTING candidate-svg.
- **`LAYOUT_PROVIDER` registry** in the cutting_pattern handler
  (production, ~6 lines, imports nothing) + patterns_ai registers the
  provider at `apps.ready()`. `panel_context` (the scouted seam) gains
  a "Manufacturing Layout" section: per group — chosen layout uid/V +
  SVG render link + choose/change link (URL hand-off), or "no layout
  chosen". Worker checklist untouched.
- Adda detail page: template-level link block (the P5-era
  adda_detail pattern — links only).

**Files (~7)**: patterns_ai `views.py` (+ChooseLayoutView) · `urls.py` ·
NEW `choose_layout.html` · `apps.py` (register provider) · NEW
`services/layout_panel_provider.py` (read-only dict builder) ·
production `stages/cutting_pattern/handler.py` (registry + section) ·
stage workspace template (render the plain dict).
**Reused/writers**: `record_usage`/`void_usage` (8A — the ONLY
writers) · candidate-svg render · panel_context seam.
**Tests**: choose page lists only ACTIVE+non-stale+same-product ·
POST records + duplicate-group refused with honest message · void flow ·
provider returns has_usage/uids and production panel renders it ·
worker 403 · ADR-H sweep still green (the registry is data-only).
**Browser**: DEV Adda (dev product w/ approved layouts — create via DCT
on a DEV product, NOT T-SHIRT goldens): choose → panel shows the
contract + render; change → void+choose; screenshots desktop+mobile.
**Risks**: provider failures must never break the stage page (wrap:
provider errors → section absent + log) · sidebar rule for the new URL.
**Acceptance**: an Adda can be linked to its manufacturing contract(s)
per fabric group; the stage workspace SHOWS the approved marker; zero
completion-behavior change anywhere.

## 8C · Expected pieces + advisory reconciliation (derive, never block)

**Scope**: the contract becomes the numbers source — advisory only.
- `get_suggested_breakup`: when the provider reports an active usage →
  expected(size) = marker_content × `LayeringRecord.lay_count`
  (readiness R-2: lay_count IS the plies truth; `MarkerUsage.plies`
  untouched/unused here), colors split across layering roll colors as
  today; NO usage → existing proportion% formula unchanged (fallback
  forever — running Addas unaffected).
- `complete_cutting_from_bundles`: WARN-level reconciliation — Σ bundle
  counts per size vs expected; mismatches reported in the completion
  message + admin snapshot (derive-at-read; nothing persisted, F6 law).
  NEVER blocks in 8C.
**Files (~4)**: cutting `service.py` (suggestion branch + warn) ·
cutting_pattern handler (provider passes expected) · stage view
message · NEW `tests/test_phase8c_expected.py`.
**Reused**: provider (8B) · `expected_pieces` (8A) · the existing
suggestion/prefill plumbing — the formula swaps INPUT, not shape.
**Tests**: suggestion uses marker content when usage exists (hand-math)
· fallback intact without usage · warn fires on mismatch, absent on
match · completion never blocked · per-size grain (colors summed).
**Browser**: DEV chain — layering (known lay_count) → choose layout →
cutting prefill shows marker-derived counts → complete w/ deliberate
mismatch → WARN visible; screenshots.
**Risks**: expected grain is per-size while bundles are per-(size,
color) — recon sums colors (stated, from readiness) · suggestion must
label its source honestly ("from approved layout LAY-… × N plies").
**Acceptance**: F3 chain live end-to-end as ADVICE; no behavior forced.

## 8D · Enforcement + closure (flags default OFF — the house pattern)

**Scope**: the gates + the audit stamp + E2E.
- **`REQUIRE_APPROVED_LAYOUT`** (settings, default False): when ON,
  `complete_pattern_stage` refuses completion without ≥1 active usage
  (honest message names the choose page). Provider supplies
  `has_usage` — production still imports nothing.
- **`ENFORCE_LAYOUT_RECONCILIATION`** (default False): when ON,
  `complete_cutting_from_bundles` refuses per-size mismatches beyond a
  tolerance setting (0 default) with the numbers in the message
  (settlement-flag precedent; audited-override variant NOTED as a
  future option, not built).
- **Stage-record stamp**: pattern-stage completion fires the registered
  callback → `stamp_stage_record` (8A writer) — usage now points at
  the exact SR, completing the audit chain (MarkerUsage's designed
  join, realized).
- **Full-chain browser E2E** on DEV data, both flags ON:
  choose → pattern stage complete (gate) → layering → cutting
  (marker-derived prefill) → bundles → complete (recon) → breakdown →
  barcodes. Then flags OFF re-verified (default behavior unchanged).
**Files (~5)**: settings base (2 flags) · cutting_pattern service
(gate) · cutting service (enforce branch) · handler callback wiring ·
NEW `tests/test_phase8d_enforcement.py`.
**Tests**: both gates ON refuse w/ honest messages · OFF = byte-same
behavior (the soak guarantee) · stamp lands on completion · tolerance ·
override-absence documented.
**Risks**: touching two production completion paths — mitigated: both
changes are flag-gated additive branches; full battery + the E2E both
flag states; deploy OFF → soak → owner enables (the frozen rollout
runbook pattern).
**Acceptance**: rule 9 is code-law when the owner flips the flags; OFF
= today's behavior exactly; manufacturing history complete
(layout → usage → SR → breakdown → barcodes, all by reference — F2).

---

## Sequence + stop points
8A → STOP/report → 8B → STOP/report → 8C → STOP/report → 8D →
STOP/report. Each: plan-delta if any → tests → battery (counts from
output) → browser (where UI exists) → screenshots → report. All DEV
Addas/products for browser proofs — golden T-SHIRT untouched except
its existing library rows.

**STOP — plan delivered. No code. Awaiting your approval of 8A (or the
split as a whole) — implementation begins on your word.**
