> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# IMPLEMENTATION READINESS REVIEW — frozen platform vs CURRENT codebase
(2026-07-08 · REVIEW ONLY — no code, no DB changes · lens: lead architect
joining the existing ERP · input: the owner's frozen business laws §2)

Question under review: *can the frozen Digital Fabric Planning Platform
be implemented cleanly inside the CURRENT codebase without future
technical debt?*

---

## 0. Headline

**YES — and unusually cleanly, because the frozen architecture was
converged toward this codebase's existing good bones across three review
rounds.** The gap between "frozen law" and "already built" is: **two
additive columns, one URL rewiring, one new application (the DCT), one
deferred refactor (Adda).** No destructive migration anywhere on the
path. Evidence below is checked against the actual models this session.

The single most reassuring verification: the frozen laws' hardest
demands **already exist in the schema**:

| Frozen law demand | Current schema reality | |
|---|---|---|
| Blueprint owns fabric group | `PatternPiece.fabric_group` (choices body/rib/collar/trim/other, indexed) with help text *"Markers never mix fabric groups"* | ✅ exists |
| Blueprint owns pair/mirror | `PatternPiece.is_pair` | ✅ |
| Blueprint owns fold | `PatternPiece.on_fold` | ✅ |
| Blueprint owns optional/required | `PatternPiece.is_optional` (default False = required; "validation cannot silently weaken") | ✅ |
| Blueprint owns count | `ProductPatternAssignment.pieces_count` ("never duplicated") | ✅ |
| Geometry contract | ADR-C canonical payload: **integer µm, y-up, CCW outer** + `chord_tolerance_um` + `pipeline_version` on extraction | ✅ exists as ADR |
| Trust level | `PieceSizeGeometry.trust_grade` (measured / photo_calibrated / uncalibrated, stamped at confirm) | ✅ |
| Entry-path-agnostic | `source_extraction` FK is **NULL for DXF imports and manual entry** — by design, in the schema help text | ✅ already built |
| Immutable confirmed geometry | model-level guard: non-draft geometry raises on save/delete | ✅ |
| Version chain + audit | append-only `PatternPieceVersion`, confirmed⇒audit CheckConstraints | ✅ |
| Reference ≠ truth | `reference_image` help text: "NEVER a geometry source; extraction refuses structurally" | ✅ |

**Missing from schema, total: TWO fields.**
1. `grain_rule` on `PatternPiece` (frozen Blueprint law; nothing stores it today).
2. An explicit **`geometry_contract_version`** per geometry row (the
   500-factory stamp). ADR-C is the contract and `pipeline_version`
   exists on extractions — but DXF/manual rows bypass extraction, so the
   row itself must carry the stamp.
Both additive, default-backfillable, zero-risk migrations.

---

## 1–12. The answers

### 1 · Can it be implemented cleanly in the CURRENT codebase?
**YES.** The three-layer split maps to existing app boundaries:
Blueprint+Sizes = `production`, Pattern Manager = `patterns_ai` (built,
tested, frozen writers), DCT = new surface consuming the existing
read-only facade (its `palette` mode was reserved for exactly this),
Adda = existing stage refactored LAST. ADR-H wall (production never
imports patterns_ai; URL-only hand-offs) already enforces the
application separation the platform demands.

### 2 · Models that remain UNCHANGED
`Product` · `ProductSize` · `ProductPattern` · `ProductPatternAssignment`
· `PatternPieceVersion` · `GeometryExtraction` · `CaptureAsset` ·
`ProductFabricProfile` · `ProductionLayout` + saved-layout/export models
· `CuttingPatternRecord`/`SizeAllocation`/`Verification` (legacy-retained
until Adda refactor) · `AddaProductSizeColorPieceBreakdown` · everything
in expense/settlement (money STOP rule — untouchable).
`PatternPiece` and `PieceSizeGeometry` change ONLY by the two additive
fields above.

### 3 · Pages that only get RENAMED (or are already right)
- Manager (`piece_list.html`) — already the frozen Manager; label
  "Open Cutting Table" → "Open **Digital** Cutting Table" (2 strings).
- "Preparing Size X" library — already exact.
- Production `Patterns` row action — same URL name, new destination.

### 4 · Pages that DISAPPEAR (as standalone destinations)
- `ProductPatternsEditView` (legacy assignment editor) — content folds
  into the Manager as the Blueprint section; standalone page retires.
- The standalone Generate/tool page — declared temporary pre-W1;
  absorbed into the DCT when the DCT ships (M4 smart-redirect machinery
  eases the transition, then retires with it).
Nothing else. Both retire AFTER their replacement is live, never before.

### 5 · Services REUSED as-is
All frozen single-writers: `pattern_geometry_service` ·
`fabric_profile_service` · `production_layout_service`. Plus
`resolve_generation_geometry(product, ratio)` (the ratio-aware geometry
collector = the DCT's import primitive), `pattern_design_facade` (THE
contract — Manager/Library/DCT/future-Adda all consume it),
`svg_render`, the M8 export machinery (`pdf_io`, DXF, tiles), the
compute bridge TOOLS, `permission_service`/`access_service`.

### 6 · Views that become thin WRAPPERS
- `PieceListView` — already a thin facade delegate (done in W1).
- `ProductPatternsEditView` — becomes a redirect/include shell during
  transition, then retires (Q4).
- The tool view — becomes the DCT shell's compatibility entry during
  transition (smart-redirect logic reused), then retires.

### 7 · Models that become LEGACY but remain temporarily
- `ProductPatternAssignment`'s **checklist role** at the Adda
  (`CuttingPatternVerification` is one-per-assignment) — stays until the
  Adda refactor; the model itself is permanent (count truth feeds
  generation: `qty = pieces_count × pair`).
- `CuttingPatternSizeAllocation.proportion_pct` (hand-entered size mix)
  — stays until the approved layout's frozen ratio supersedes it.
- `ProductPattern.reference_image` (library-level image) — superseded by
  piece-level reference; harmless, remove never or at leisure.

### 8 · Current APIs that ALREADY satisfy the frozen architecture
- Facade `product_design_library` — design_key, outline_mm, dims,
  checks, tier, area — the DCT Available-Library contract, tested.
- `resolve_generation_geometry(product, ratio)` — cut-plan-aware
  geometry resolution (LAW 13's ratio input already parameterized).
- M7 approve flow (summary-BEFORE-approve) — the Approve-Layout module.
- M8 exports (true-scale tiles, scale bar, summary stamping) — the
  Export module.
- Version-history switcher — the Layout-Library seed.
- The immutability/audit spine (constraints verified in §0).

### 9 · DANGEROUS to modify first (touch late or never)
1. **Adda `cutting_pattern` stage** — feeds production truth →
   settlement chain. LAST, after the DCT is proven on real markers.
2. **`ProductPatternAssignment` deletion** — never (3 live consumers).
3. **`resolve_generation_geometry` contract** — the DCT must CONSUME it,
   not fork it; two geometry resolvers = the debt the platform forbids.
4. **Frozen single-writer services** — extend by new methods only.
5. **expense/settlement anything** — money STOP rule.
6. **Non-additive migrations on populated geometry tables** — the
   platform's asset store; additive-only, forever.

### 10 · Implement FIRST
**M-A "Entry + truth stamp"** — the two additive fields
(`geometry_contract_version`, then `grain_rule` in M-B), Patterns-action
rewiring to the Manager, Blueprint section folded in, DCT label rename,
Universal-size convention + archive guard. Zero-risk, completes the PDM
stage, and gets the contract stamp in BEFORE more geometry data
accumulates (the 500-factory insurance is cheapest today).

### 11 · Implement LAST
**M-H Adda refactor** — consume Approved Layouts (choose-layout +
roll-match check + verification against expected pieces = layout ×
plies), retire proportion hand-entry and the assignment checklist role.
Only after the DCT has produced real approved markers the factory has
actually cut from. It is also the only milestone touching
production-truth writes — one milestone, maximal care, own review.

### 12 · Milestones (proposal only — each gated owner-approve → build → stop)
| # | Milestone | Content | Schema |
|---|---|---|---|
| M-A | Platform entry + truth stamp | contract-version field · Patterns→Manager · Blueprint section (fold assignment editor) · DCT rename · Universal + guard | 1 additive |
| M-B | Blueprint completion | `grain_rule` field · unified piece-rules editing in the Blueprint section · single "Add Pattern Definition" action (pattern+assignment+piece atomically) | 1 additive |
| M-C | DCT shell (read-only) | new page skeleton · fabric-group selection · Available Library via facade `palette` mode · import size → static canvas render | none |
| M-D | Canvas interactions | drag/rotate/flip/lock/snap/zoom/undo · Selected/Placed persistence via saved-layout machinery | none |
| M-E | Layout library + approve | multiple NAMED layouts · reuse M7 approve · LAW-11 staleness flag · LAW-13 freezing (spec/width/ratio stored) | small additive if staleness flag stored |
| M-F | AI optimize (async) | job record + poll UX · nest bridge reuse · Selected-not-Placed only · progress/cancel | 1 small (job) |
| M-G | Marker exports | M8 reuse from DCT layouts · marker sheet | none |
| M-H | **Adda refactor (LAST)** | consume approved layouts · roll-match check · expected-pieces verification · retire proportion% + checklist role | reviewed separately |

Honest open point, decided at M-F not now: the project has **no task
queue** (no Celery; the compute bridge is a synchronous subprocess with
a 60s cap). Async optimize needs a job-record + poll pattern or a queue
— a contained infrastructure decision inside one milestone.

---

## Declaration

Path verified: two additive fields close the entire schema gap; every
frozen law lands on an existing, tested subsystem or the one genuinely
new surface (the DCT canvas); the only dangerous refactor is isolated
as the explicit LAST milestone; nothing on the path requires a
destructive migration or touches the money boundary.

**IMPLEMENTATION READY — BEGIN PHASED ENGINEERING.**

**STOPPED — no code written. Awaiting owner approval of the milestone
sequence (M-A first) under the standing discipline: plan → approve →
implement ONE → tests → browser → battery → report → STOP.**
