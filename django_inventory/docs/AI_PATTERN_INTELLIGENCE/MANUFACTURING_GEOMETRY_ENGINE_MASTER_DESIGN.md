---
id: docs-ai-pattern-intelligence-manufacturing-geometry-engine-master-design
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# MANUFACTURING GEOMETRY ENGINE — MASTER DESIGN
(2026-07-10 · the living master reference the advisor demanded ·
REVIEW ONLY, no code · companion constitution: PRODUCT_DESIGN_FREEZE.md
+ UI_WORKFLOW_FREEZE.md · evidence = main-thread code reads this
session; the 8-agent verification workflow FAILED on session rate
limits and its findings were NOT used — every file:line below was read
directly, per the audit-honesty standing rule.)

## §0 · THE VERDICT (read this first)

**This is NOT a pivot. The Manufacturing Geometry Engine the advisor
describes is ~80% BUILT, FROZEN and TESTED — under the constitution's
names.** The advisor's message reads like a review of the system as it
looked months ago. Almost every "change" it demands is already law:

- "Final truth must NEVER be the image" — **already structural law**,
  not aspiration (§2 row I).
- "Geometry + manufacturing metadata, not image properties" — the
  Blueprint IS exactly that (§2 row A).
- "Deterministic first, AI as enhancement" — **already the frozen
  build order AND a locked owner rule** (optimization rules ⑨⑩:
  deterministic, seeded, no ML ever without explicit owner order).
- The proposed build order 1→5 (Rules → Geometry → Marker →
  Optimization → AI) **is the order it was actually built in**
  (M1 Blueprint → Studio/truth → DCT → engines → AI-proposals-last).

**What the advisor message genuinely adds: 5 real gaps (§3)** —
fold-as-placement, roll-aware marker input, double-layer semantics,
roll metadata, nap handling. All five EXTEND the frozen M4/M6
milestones. Nothing gets replaced; nothing gets thrown away; the
constitution stands and this document becomes its manufacturing-
physics companion.

## §1 · NAME MAPPING (advisor language → built system)

| Advisor says | Built as | State |
|---|---|---|
| Manufacturing Geometry Engine | the Pattern Intelligence Platform spine (truth model + engines) | ✅ frozen |
| Pattern Library + metadata | Blueprint (M1) + Studio shelf (M2) + `PieceSizeGeometry` truth | ✅ |
| Pattern digitization pipeline | the Studio's Acquisition Layer + compute runtime (ADR-F) | ✅ (M2) |
| Marker Engine | Digital Cutting Table + nest engines + Marker Plan (M4, designed) | 🔶 M4 |
| Marker replaces manual chalk decision; worker follows layout | ApprovedLayout = the Adda's cutting CONTRACT (8B) + advisory numbers (8C) + gates (M6, flags OFF) | 🔶 M6 |
| Optimization Engine | BLF + vendored SVGnest, op verify/optimize, honest better/same/worse | ✅ |
| AI Assistant last | M7 Pattern Assistant (frozen scope: proposals only) | 🔮 M7 |

## §2 · REQUIREMENT-BY-REQUIREMENT EVIDENCE MATRIX

**A. Pattern manufacturing properties** (advisor: "NOT image
properties" — correct, and none live on images):

| Property | Where | State |
|---|---|---|
| Mirror allowed / pair type | `PatternPiece.is_pair` (pieces.py:44); DCT mirror is pair-GATED | ✅ |
| Fold allowed | `PatternPiece.on_fold` (pieces.py:64) — flag EXISTS; placement MISSING (§3 G1) | 🔶 |
| Rotation allowed | `PatternPiece.grain_rule` STRICT/TWO_WAY/FREE (pieces.py:48); enforced in DCT + engine `allow_180` | ✅ |
| Grain direction | payload `features.grain.angle_cdeg` — MANDATORY at confirm (pattern_geometry_service confirm_version) | ✅ |
| Quantity per product | `ProductPatternAssignment.pieces_count` (single count truth; `set_piece_count`) | ✅ |
| Seam allowance | `PatternPiece.seam_allowance_mm` (M2, migration 0012) — declared metadata; geometry stays the CUT line (ADR-C) | ✅ |
| (+ notches) | adr-c.2 `features.notches` + `expected_notches` (M2) | ✅ |

**B. Pattern Library record** (advisor's field list): id ✅ · product ✅
(product-scoped grain, pieces.py:28) · geometry ✅ (int-µm canonical
payload) · mirror/fold/grain/rotation ✅ (above) · quantity ✅ ·
size ✅ (`PieceSizeGeometry` per version×size, ADR-D2) · revision ✅
(`PatternPieceVersion` append-only chain + copy-forward +
`geometry_contract_version` stamps) · reference_images ✅
(`reference_image`, display-only, structurally banned from geometry) ·
measurements ✅ (tape_acceptance ±2 mm gate; trust grades
measured/photo_calibrated/uncalibrated).

**C. Digitization pipeline** (advisor's chain): perspective correction
✅ (ChArUco → RANSAC homography w/ hold-out residuals, extract.py) ·
scale calibration ✅ (commissioned mats + control distances; the
metrology loop) · edge detection/segmentation ✅ (classical ladder +
honest SAM slot) · contour extraction ✅ (findContours → approxPolyDP)
· **Bezier curves — MISSING BY DESIGN**: ADR-C stores
polyline-at-chord-tolerance (0.5 mm), the manufacturing-grade choice
(§3 G6) · geometry ✅ · measurements ✅ (tape) · "images rarely needed
after" ✅ — payload self-contained; nothing downstream reads pixels.

**D. DXF/SVG/validation**: DXF-AAMA import+export ✅ (dxf_io +
import_dxf/export_dxf_bytes + M2 evidence adapter) · SVG import ✅
(M2 `svg_import.py`) + export ✅ (svg_render, true-scale) · validation
✅ (canonical validator TWINS, units.py + runtime canonical.py,
lockstep).

**E. Marker engine I/O** (advisor's list): pattern placement ✅ ·
mirror placement ✅ (pair-gated) · rotation ✅ (grain-gated) · waste % /
utilization / length ✅ (`layoutMetrics`, engine buckets) · piece
count ✅ (`marker_content` derive-at-read) · **fold placement MISSING
(G1) · roll/layering input MISSING (G2/G3)** — today's width input =
fabric-profile default, hand-editable.

**F. ERP integration**: Layering → **MISSING edge, already frozen into
M6** ("Recommended layer length from the approved layout") · Cutting ✅
(8C advisory suggestion + reconciliation WARN; operator numbers stand)
· Bundles/Barcodes/Inventory ✅ (Breakdown = fact → ERP chain) ·
Production planning 🔶 (choose page + timeline; gates = M6, flags OFF)
· Worker assignment / Costing — **deliberately NOT wired**: frozen
foundation law (settlement-only money, ADR-0009; manager-assignment
rosters). Any costing link = read-only consumption later, never a new
money path (Money-Write STOP rule).

**G. Roll + layering data** (main-thread verified today):
`ClothRoll.width_inch` ✅ (raw_materials/models.py:129) ·
`LayeringRecord` ✅ = the real layering stage (lay_count =
Σ per-roll `layers_on_roll` (layering.py:21,86), `layer_length_meters`,
`rolls_used` M2M, per-roll length math) · usable width — the CONCEPT
already existed on the legacy `Marker` ("human-confirmed usable lay
width — never trusted from ClothRoll nominal inches") · stretch / nap /
edge info / layering-type — **MISSING (G4/G5)** · marker path reading
roll/layering — **MISSING (G2)**.

**H. "System replaces the worker's marker decision"** — the frozen
manufacturing timeline already encodes the honest version: layout =
the contract the Adda CHOOSES; numbers advisory; enforcement gates
(REQUIRE_APPROVED_LAYOUT / ENFORCE_LAYOUT_RECONCILIATION) ship OFF and
flip only after soak (M6). Replacing the decision = flipping flags,
not new architecture.

**I. "Image never truth"** — structural, five layers deep:
reference-image kind refused by extraction (capture.py Kind +
run_extraction guard) · proposals human-accepted one-shot ·
confidence display-only · geometry immutable after confirm ·
tape gate to measured. Nothing to change.

## §3 · THE REAL GAPS (what the advisor message actually contributes)

**G1 · FOLD AS A PLACEMENT STRATEGY** — the biggest one. Today
`on_fold` is an HONEST BLOCKER ("on-fold pieces cannot be generated
yet", pattern_design_facade) — flagged, refused, never faked. Target:
a fold-line placement mode — the half-piece sits ON the fold edge;
engine + DCT treat it as half-width geometry with a fold-edge
constraint; unfolded piece = derived. Touches: payload (fold_edge slot
already reserved in the canonical features!), DCT physics, engine,
readiness law (on_fold stops blocking). = the largest single work item.

**G2 · ROLL/LAYERING-AWARE MARKER PLAN.** M4's frozen Marker Plan
(sizes × garments) gains the fabric reality: width from the actual
roll (usable width, human-confirmed — the legacy Marker's own
discipline) + layering type. Read-only consumption of raw_materials/
production data across the wall = provider/URL patterns, never
imports.

**G3 · LAYERING-TYPE SEMANTICS (single / double / tubular).** Double
lay ⇒ every placement yields 2 pieces (mirrored pair free) ⇒ marker
content × 2 × lay_count. Extends the frozen COUNT HIERARCHY (content ·
plies · advisory) with a per-layout layer-multiplier — recorded ON the
layout at save, consumed by 8C math. Pairs stop being placed twice on
double lay.

**G4 · ROLL METADATA** (raw_materials, additive): usable_width_mm ·
stretch class · nap/one-way flag · edge/selvedge note. ERP-app change
⇒ own docs-sync + care; small.

**G5 · NAP DIRECTION** as placement constraint: one-way fabric ⇒ no
180° flips even for TWO_WAY pieces. Maps cleanly onto the existing
grain machinery (a lay-level override narrowing rotation sets).

**G6 · BEZIER — CONSCIOUSLY REJECTED.** ADR-C's
polyline-at-chord-tolerance (0.5 mm) IS the manufacturing answer: the
cut line at cutting accuracy, simple validators, exact DXF-AAMA
interchange, engine-consumable. Beziers add math surface with zero
manufacturing benefit at this tolerance. Revisit ONLY with evidence of
insufficient fidelity on a real piece. (adr-c.3 would be the vehicle —
the stamp exists for exactly that.)

## §4 · REUSE vs REPLACE (the advisor's direct question)

**REPLACE: nothing.** **REUSE: the entire spine** — truth model,
single writers, append-only versions + contract stamps, acquisition
contract (M2), validator twins, metrology loop, DCT physics +
mm-world/camera split, nest engines + frame swap, ApprovedLayout
library + usage timeline + freezes F1–F3 + count hierarchy, ADR-H wall
+ provider inversions, ERP chain. **EXTEND: G1–G5** inside the frozen
milestone order.

## §5 · PHASE A–E ↔ FROZEN ROADMAP (no new roadmap needed)

| Advisor phase | = | State |
|---|---|---|
| A · Geometry engine + library + metadata + DXF/SVG + measurement + validation | M1+M2+M3 (+G4 roll fields ride M4) | ✅ DONE |
| B · Digitization (photos → vectors) | Studio Acquisition Layer (M2); large-piece decision still owner-open | ✅ DONE (v1) |
| C · Marker engine (roll+layering+product+size → layout) | **M4 EXTENDED: Marker Plan v2 = sizes×garments + roll/usable-width + layering type (G2/G3) + Import Queue + size colors; FOLD G1 = M4.5 (own sub-milestone — engine work)** | 🔶 next |
| D · ERP integration (layering→marker→cutting→bundles) | M6 (layering edge + stamp + gates-OFF→soak→flip) | 🔶 designed |
| E · AI optimization/analytics | existing AI-optimize (done) + M7 assistant + frozen analytics revived on library data | 🔮 later |

Build order stays **M4 (incl. G2/G3/G4/G5) → M4.5 (G1 fold) → M6 →
M5 → M7**. The constitution (both freezes) is unchanged; this document
is registered as its manufacturing-physics companion + amendment
(M4 scope growth), pending owner sign-off below.

## §6 · LAWS THAT BIND EVERY GAP
Image never truth (structural) · geometry = cut line, integer µm,
contract-stamped · single writers only · derive-at-read (expected
numbers persisted nowhere) · operator numbers always stand; warnings
explain, never modify · settlement = the only money boundary (costing
= read-only consumption, never a new writer) · production never
imports patterns_ai · flags ship OFF · deterministic before AI, AI =
proposals forever.

## §7 · OWNER DECISIONS (nothing proceeds without them)
1. **Accept the verdict:** no pivot — advisor's engine = the built
   platform + gaps G1–G5. This doc = master reference/amendment, the
   freezes stay constitution.
2. **M4 scope grows** to Marker Plan v2 (roll + layering type +
   double-lay math, G2/G3/G4/G5) — confirm.
3. **G1 fold placement = M4.5**, its own planned sub-milestone
   (engine + payload + DCT + readiness law) — confirm, or defer.
4. **G6 bezier rejection** — confirm polylines stand.
5. Roll metadata fields land in raw_materials (ERP-side additive
   migration) — confirm.

**Verification honesty note:** the 8-agent audit workflow errored out
(session rate limit) — zero agent findings used. Every evidence line
above = main-thread file reads (this session) or the owner-reviewed
ARCHITECTURE_AUDIT_2026_07_10. STOPPED — no code until rulings.
