> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PHASE 8 — MANUFACTURING READINESS REVIEW
(2026-07-10 · REVIEW ONLY — no code, no migrations · ground truth from a
4-reader adversarial scout over the Adda stage, the cutting/bundle/
barcode flow, platform-law verification, and the dependency audit)

## 1 · The complete manufacturing flow (as built today)

```
BLUEPRINT (patterns_ai:blueprint)                 structure + rules
    ↓  (facade — read-only)
PATTERN MANAGER (piece-list / size library)       per-size confirmed designs
    ↓  (≥1 Ready gate)
DIGITAL CUTTING TABLE (table/<pk>/)               session: import→arrange→optimize
    ↓  save_table_layout (verify-before-persist)
SAVED DRAFT (immutable run+candidate)             engine='table'
    ↓  approve_table_layout (explicit human act)
APPROVED LAYOUT LIBRARY (ApprovedLayout)          LAY-<code>-NNNNNN · V<n> · chains
    ↓  exports (candidate-pdf/print — stored rows, verified-gated)
════════ the P8 boundary — everything below exists, nothing below
════════ consumes the library YET (that is exactly Phase 8's job)
ADDA "Pattern Design" stage (cutting_pattern)     chalk layout: photos/video ·
    ↓                                             verification checklist (one per
    ↓                                             assignment) · proportion% (Σ=100)
LAYERING (lay_count = Σ layers-on-roll)           the REAL plies count
    ↓
CUTTING (bundles per size · items per pattern×color)
    ↓  _materialize_breakdown (sole writer)
AddaProductSizeColorPieceBreakdown                frozen verified per-(size,color)
    ↓  assembly.generate_from_breakdown
BARCODES (range batches) → INVENTORY/TRACKING
```

## 2 · Source-of-truth verification — PASS (adversarially checked)

| Stage | Its ONE truth | Sole writer | Verified |
|---|---|---|---|
| Blueprint | piece set + rules | `register_pattern_definition` + setters | ✓ |
| Pattern Manager | confirmed `PieceSizeGeometry` (+contract stamp) | `pattern_geometry_service` | ✓ |
| DCT session | runtime object (browser, dies with the page) | n/a — never truth | ✓ |
| Saved Draft | run+candidate (append-only, model-guarded) | `marker_generation_service` ONLY (grep-verified: zero creates elsewhere) | ✓ |
| Approved Layout | `ApprovedLayout` pointer + uid | `layout_library_service` ONLY (`_status_transition` exists in exactly 2 service lines; no admin surface) | ✓ |
| Staleness | **derived** — no column exists (field list checked) | `layout_is_stale()` | ✓ |
| Exports | consume stored rows; GET-only views, zero write verbs | — | ✓ |
| Cutting counts | `AddaProductSizeColorPieceBreakdown` | `_materialize_breakdown` ONLY (zero writes in tracking) | ✓ |
| Barcodes | `BarcodeBatch` ranges, one-shot per Adda | `barcode_generation/assembly` (production-owned) | ✓ |

**No circular dependencies**: 17 FKs patterns_ai→production, ALL
PROTECT; production→patterns_ai = ZERO (imports AND FKs; back-door
`apps.get_model` searched — none). The two legal couplings: URL-name
redirects + the ARCHIVE_VALIDATORS inversion (import flows
patterns_ai→production only).

## 3 · Responsibility + law verification — PASS

- **One responsibility per stage** ✓ (table above; the Adda pattern
  stage today = evidence + checklist + proportions, nothing else).
- **Adda consumes only Approved Layouts / never drafts / never
  sessions**: trivially true today (it consumes NOTHING from
  patterns_ai — grep-verified); P8's design must keep it that way
  (see gap G-4).
- **Approved Layout immutable forever** ✓ — model save() raises unless
  the single writer's status flag; delete() always raises; zero CASCADE
  anywhere in patterns_ai; nothing FKs INTO ApprovedLayout.
- **Law 11 (staleness)** ✓ derived-only, flips on version supersede
  (suite-proven).
- **Law 12 (fabric-group isolation)** ✓ enforced twice: client at
  import + server in `save_table_layout`; `fabric_group` frozen on the
  approved row.
- **Universal Size fits** ✓ — full sweep found NO size-code branching
  anywhere in the chain; ratio/params key by size_id; ApprovedLayout is
  size-agnostic; a Universal-only product flows identically.
- **Version history append-only** ✓ (supersede chain; unique
  (product, version_no); nothing overwrites).
- **Production models production-owned / patterns_ai owns geometry** ✓.
- **No writer duplication** ✓ (census above).
- **No frozen law violated by any later phase** ✓ — the adversarial
  pass returned five ALL-CLEARs with line-level evidence.

## 4 · Remaining production risks (real, from ground truth)

- **R-1 · Nothing records WHICH layout an Adda cuts.** The pattern
  stage completes today with photos+checklist only. Until P8 adds the
  link, the library is truth nobody consumes — the known state, but
  now it's the ONLY missing edge in the chain.
- **R-2 · Two unconnected plies concepts.** `LayeringRecord.lay_count`
  (derived from per-roll layer counts — the REAL number) vs
  `MarkerUsage.plies` (manual entry, never validated). P8 must not
  create a third; it should read `lay_count` as the plies truth.
- **R-3 · Expected-vs-actual reconciliation absent.** Cutting completion
  validates MEMBERSHIP only (sizes ∈ allocations, patterns ∈
  assignments) — never counts. The prefill formula
  (`lay_count × pieces_count × proportion%`, equal color split) is a
  hint the master can fully override. Honest gap, was always the plan.
- **R-4 · Bypass is currently legal.** No code path forces an Adda
  through the library — correct during transition, but P8 needs an
  explicit, gated answer (precedent exists: `ENFORCE_*` flags, default
  False, soak-then-enable).
- **R-5 · Multi-group products need MULTIPLE layouts per Adda**
  (body marker + rib marker — LAW 12). Any Adda↔layout link must be
  one-per-fabric-group, not one-per-Adda.
- **R-6 · ★ vs library duality** (known, recorded): `ProductionLayout`
  (generator flow) and `ApprovedLayout` (DCT library) coexist. P8 is
  where the Adda picks a side: it must pick the LIBRARY (rule 9).

## 5 · Final additive recommendations (P8 scope — nothing pre-required)

1. **`ApprovedLayoutUsage`** — ONE new append-only patterns_ai model
   mirroring the already-designed `MarkerUsage` shape (the codebase's
   own template for this exact join): `layout FK(ApprovedLayout,
   PROTECT)` · `adda FK(production.Adda, PROTECT)` · `stage_record
   FK(AddaStageRecord, null)` · `recorded_by/at` · soft-void. Allowed
   FK direction (patterns_ai→production, like the 17 existing). Its
   single writer REFUSES: non-ACTIVE layouts, **STALE layouts** (the
   Law-11 derived check finally gets its enforcement point), layouts of
   another product, and a second active usage for the same
   (adda, fabric_group) — R-5 solved structurally.
2. **Surface the layout in the pattern stage** via the existing seams
   (scouted): `panel_context` dict + the checklist item `image` slot —
   the cutting master sees the approved marker render instead of only
   chalk photos; `CuttingPatternPhoto` stays as floor evidence.
3. **Expected pieces without a cut-plan input**: derive per-size marker
   content by COUNTING the stored placements per size
   (`design_key = piece:size`) — no new data needed; expected(size) =
   marker_count(size) × `LayeringRecord.lay_count` (R-2: lay_count is
   the plies truth). Feed `get_suggested_breakup` (replacing the flat
   proportion heuristic when a usage exists) + a WARN-level
   reconciliation at `complete_cutting_from_bundles` behind
   **`REQUIRE_APPROVED_LAYOUT` / recon flags, default OFF** (the
   house pattern) — R-3/R-4 answered without breaking any running Adda.
4. **No new identifiers needed** — `layout_uid` already exists for
   Adda/barcode/audit references (the P7 recommendation paying off);
   bundles/barcodes need nothing from the layout (they key off
   size/color counts, which recon covers).
5. **Freeze before implementation**: the ★ designation stays for the
   generator tool only; the ADDA path = library-only (rule 9 made
   code-law by recommendation 1's writer refusing anything else).

## 6 · GO / NO-GO

**GO.** Every frozen law verified in code with line-level evidence;
the chain has exactly one missing edge (Adda→library), and the
codebase already contains the designed pattern for it (`MarkerUsage`),
the enforcement seams (`get_suggested_breakup`,
`complete_cutting_from_bundles`, `panel_context`), the plies truth
(`lay_count`), and the reference key (`layout_uid`). No pre-work, no
migrations, no redesign required before Phase 8 — recommendations 1–5
ARE the Phase-8 scope, all additive, all flag-gated where they touch
running production.

---
**STOPPED — readiness review delivered. No code. Phase 8
implementation begins only after you approve this review (and its §5
scope).**
