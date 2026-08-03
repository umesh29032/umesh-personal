# AI Pattern Intelligence — Platform Blueprint v1 (2026-07-06)

> **Status: ⚠️ SUPERSEDED chain → [06_BLUEPRINT_V3_FINAL.md](06_BLUEPRINT_V3_FINAL.md) (the certified design of record, pending owner sign-off). V1 kept for history; C1-C20 + F1-F8 changelogs record every change since.**
> Original status: 📐 V1 OWNER-ACCEPTED 2026-07-06 — NOTHING implemented.
> Owner rulings: (1) **honest-AI philosophy LOCKED** — deterministic stays deterministic,
> CV is called CV, optimization is called optimization; real ML only if production data
> ever justifies it (§1 glossary is binding vocabulary). (2) **Permanence LOCKED** —
> Product → Pattern Sets → Marker generations → alternatives; nothing overwritten,
> everything versioned, available forever (§2/§3 append-only design is binding).
> (3) **Fully open-source, no cloud AI, no paid APIs; reproducible from our own repo** —
> any future training scripts live inside this project (ADR-F vendoring covers this).
> (4) Project starts ONLY after manufacturing production freeze + stable checkpoint
> commit; until then ideas accumulate in **§12** (improve architecture, never implement).
> One more blueprint review happens at kickoff before any code.
> Supersedes the architecture + roadmap sections of [02_PROJECT_PLAN_DRAFT.md](02_PROJECT_PLAN_DRAFT.md)
> (research in [01_RESEARCH.md](01_RESEARCH.md) stays valid). Produced from the owner's
> 2026-07-06 vision statement put through a 7-lens adversarial review
> (data-model · CV/metrology · nesting · frozen-architecture · factory-floor 4-role ·
> 2-5-year futurist · AI-scope skeptic; every code claim verified file:line) plus
> main-thread synthesis. *Review provenance note: the two automated cross-examiner
> agents failed on a session limit; their pass was done manually — recorded per the
> audit-honesty rule.*

---

## 0. Verdict on the vision

**The direction is right and buildable.** Product-centric library, many pattern sets /
many markers / alternatives / permanent history, human-confirm-before-truth,
open-source-first, feedback from ERP actuals — all confirmed against the real codebase.
Every integration seam the vision assumes exists today:
`ProductPattern` (cutting.py:47), `ProductPatternAssignment` (:88),
`CuttingPatternRecord`+photos (:152, :192), `ProductSize` (:242),
`CuttingPatternSizeAllocation` (:321), `CuttingPieceBreakup` (:362), APSCPB (:500),
`LayeringRecord` (layering.py:13), `LayeringRollEntry` (:48),
`RemainingClothOfClothRoll` (:103), `ClothRoll.width_inch` (raw_materials/models.py:129; WIDTH_CHOICES 36-44 at :99).

But the review found **12 blockers** that would have made the drafted schema wrong on
day one. This blueprint resolves all of them. The three that change the vision itself:

1. **Sizes and fabric groups are missing dimensions.** A marker nests a SIZE MIX, so
   geometry must exist per (piece, size) — and rib/collar pieces cut from different
   fabric can never share a marker with body pieces. "One Pattern Set" is really
   *(product × fabric-group × revision)*, and "the active Product Marker" is really
   a *resolution* per (product, fabric-group, usable-width, ratio) — never a single
   pointer. Several markers are legitimately "active" at once.
2. **Tubular knit / cut-on-fold is absent from the vision — and it is this factory's
   main fabric.** Open-width vs tube-flat width changes every utilization number by
   up to 2×. Fabric construction, usable width (≠ nominal roll width), and on-fold
   piece semantics enter the schema in v1.
3. **The feedback loop has no join key.** Nothing records which marker an Adda
   actually cut with. `MarkerUsage` (a human act at cut planning: "this Adda cuts
   with marker M") is the load-bearing missing entity — without it the entire
   "production feedback" pillar is unimplementable.

## 1. Honest mechanism glossary (owner-facing — set at kickoff)

Every "AI" claim restated as its buildable open-source mechanism. This prevents the
year-2 trust collapse when someone looks under the hood.

| Vision phrase | Actual mechanism |
|---|---|
| "AI suggests expected pattern pieces for a new product" | **Garment-type template library** (`GarmentTemplate`: T-Shirt → front/back/sleeve/neck-rib/cuff with counts, grain, pair flags), seeded from FreeSewing/Seamly2D taxonomies + backfilled from our own `ProductPatternAssignment` history, plus "copy from Product X". Deterministic. Optional flag-gated local-LLM (Ollama) as an admin-only template-drafting aid — never a runtime dependency. |
| "AI detects the pattern boundary" | Classical CV first (calibration-mat background prior + contours + GrabCut), small segmentation model as assist (MobileSAM/EfficientSAM-class, ONNX, CPU-viable) only when classical fails. Weights vendored, pinned. |
| "AI calibrates scale and dimensions" | OpenCV + printed **ChArUco calibration mat** homography math with per-photo quality gates. Not learning — measurement. |
| "AI generates multiple markers" | NFP nesting engine + metaheuristic, one candidate per **strategy** (mixed / sectioned-by-size / fold-aware), stored seed = reproducible. Stochastic search, not intelligence. |
| "AI learns automatically from ERP data, no manual training" | **"The system remembers and compares"**: append-only `MarkerUsage`+`MarkerOutcome` facts, predicted-vs-realized utilization ranking with minimum-sample guards (n ≥ 3 Addas), recency tie-breaks, visible "based on N Addas" badge. Deterministic analytics. Real ML earns a slot only if hundreds of (marker, outcome) pairs ever exist AND ranking can't do the task — at single-factory volume, likely never. That sentence goes in the owner spec. |

## 2. Corrected concept model (owner language)

```
Product ("T-SHIRT")
 ├─ Pattern Library (permanent asset, owned by the product)
 │   ├─ Fabric group: BODY (main knit)          ── one marker never mixes fabric groups
 │   │   ├─ Piece: Front   ├─ Piece: Back   ├─ Piece: Sleeve
 │   │   │    └─ Version v1, v2… (immutable once confirmed; supersede, never edit)
 │   │   │         └─ Geometry PER SIZE (S/M/L/XL) — captured / graded / imported,
 │   │   │            each with provenance + trust grade + who-confirmed-when
 │   │   └─ Pattern Set Revision R1, R2… = frozen snapshot {piece-version per piece}
 │   └─ Fabric group: RIB (collar/cuff fabric)  ── same structure
 ├─ Markers (per fabric group; immutable artifacts)
 │   ├─ Marker M1: rev R1 · tube-flat 17″ usable · ratio S2:M2:L1 · strategy=mixed
 │   │    ├─ alternatives A/B/C from ONE run (different strategies, honest numbers)
 │   │    ├─ placements = rows pinning exact size-geometry (never loose JSON)
 │   │    └─ validation receipts (Gate 1/2/3 below)
 │   └─ Marker M2: open-width 40″ · different ratio … (many "active" markers coexist)
 ├─ Marker Usage history: "Adda 3-PATTI-016 cut with M1" (human act, append-only)
 └─ Outcomes: predicted vs realized per usage → ranking ("based on N Addas")
```

"Multiple Pattern Sets per product" = **revisions over time** by default; if the owner
also means *fit variants* (slim/regular), that is a labelled sibling dimension —
owner decision D1 below.

## 3. Data model (app `patterns_ai` — all FKs point INTO production, never back)

New Django app, own `services/` (single-writer), own views/URLs/templates, own media
tree. Production code never imports it (§5). Key entities — names final at ADR:

| Entity | Grain + load-bearing fields | Why this shape |
|---|---|---|
| `GarmentTemplate` (+pieces) | garment_type → expected pieces (name, count, grain, pair, fabric_group) | W2 suggestion mechanism. `garment_type` key lives HERE (Product stays untouched — core.py:53). |
| `PatternPiece` | UNIQUE(product, pattern); FK `Product` + FK `ProductPattern` (name-link only) + optional 1:1 `ProductPatternAssignment`; `fabric_group`; pair/mirror flag; `on_fold` | **Blocker fix:** draft hung geometry on the CROSS-product `ProductPattern` (cutting.py:47-58 — sleeve shared by T-Shirt+Kurta). Geometry must be product-scoped or the second product reusing "sleeve" corrupts the first. `pieces_count` is READ from ProductPatternAssignment (cutting.py:116), never duplicated. |
| `CaptureAsset` | original file, byte-immutable, checksum at upload; EXIF/device; calibration provenance (homography, residuals, mm/px); `pipeline_version` on every derived artifact | Originals forever + reprocessable. NEVER reuses the destructive compress-in-place `CuttingPatternPhoto` path. Better model later = batch re-derive from originals → NEW draft versions → human re-confirm. |
| `PatternPieceVersion` | status draft→confirmed (confirm freezes, service-enforced); superseded_by chain; voided_at; confirmed_by/at | Append-only history rule made schema-visible. Supersede = new row; approved markers PROTECT old geometry so nothing orphans. |
| `PieceSizeGeometry` | FK version + FK `ProductSize` (PROTECT); polygon (`schema_version`, **units = mm**, documented origin/axis/rotation spec); grain arrow (mandatory human annotation); **notches, drill points, internal lines** as first-class features; fold-edge; seam-allowance semantics flag (cardboard = cut line w/ allowance, default "as-cut"); provenance enum captured/graded/scaled/imported/manual; trust grade MEASURED / PHOTO-CALIBRATED / UNCALIBRATED; stored area | **Blocker fixes:** per-size geometry is what markers nest; segmentation cannot see grain/notches/drills — they are human annotations with CV proposals; DXF-AAMA entity list shapes this schema from day one (fields may be empty in year 1, absent never). Marker generation restricted to MEASURED/PHOTO-CALIBRATED. |
| `PatternSetRevision` (+members) | immutable snapshot {piece-version} per (product, fabric_group) | Gives "Pattern Set" precise semantics; markers pin a revision. |
| `MarkerRequest` | human-confirmed input snapshot: usable_width_mm (taped at table — never trusted from `ClothRoll.width_inch` nominal integer 36-44), construction open/tubular, end allowance, edge margin, spacing/kerf, ratio as INTEGER repeat counts (CPSA percentages are prefill hints only — cutting.py:321 stores per-Adda whole %), constraints | **Blocker fix:** tubular/usable-width semantics live here in v1 — no production model widened without owner approval (D2). |
| `MarkerRun` | async job row: engine + commit + seed + params, progress, timeout, cancel | The ERP's first background worker (ADR-B) — decided as an ERP-level primitive, not a module hack. |
| `Marker` | immutable; FK PatternSetRevision + MarkerRequest; **strategy enum** (mixed/sectioned/fold-aware); three honest numbers: geometric utilization %, **meters per garment** (floor language), total lay consumption incl. end losses; status candidate→approved; staleness = derived query when pinned geometry superseded | **Blocker fixes:** alternatives = one per strategy (never 3 GA reseeds sold as choice); stored placements ARE the marker — regeneration is a NEW marker. |
| `MarkerPlacement` | child rows: FK marker CASCADE + FK `PieceSizeGeometry` **PROTECT**, x/y/rotation/flip; piece-label kept addressable (future barcode piece-identity, ADR-0010 D3) | **Blocker fix:** draft's placements-JSON = 2-year orphaned-reference bug. JSON kept only as render cache. |
| `MarkerValidationEvent` | append-only trust receipts for Gates 1-3 (§6) | Trust is data. |
| `MarkerUsage` | FK Marker + FK `production.Adda` (allowed direction) + optional stage-record; plies; measured usable width at lay; confirmed_by/at; voided_at | **THE missing entity.** Written at cut planning as a human act. Feedback joins MarkerUsage → LayeringRecord (lay_count, layer_length_meters — layering.py:21-28) → APSCPB. |
| `MarkerOutcome` | derived fact per usage: predicted vs realized = Σ(piece_area(size) × APSCPB count × pieces-per-garment) ÷ (lay_length × usable_width × plies); leftover meters; data-quality flags (honest-NULL — never guess) | Powers ranking with guards (§7). Rib/trim fabric groups have NO actuals source today (APSCPB = garments only, ops-master §2 rule 6) — stated, not papered over. |

Single-writer services: `capture_service`, `pattern_geometry_service`, `marker_service`,
`marker_feedback_service`. Canonical internal units: **mm** (ERP mixes inches + meters;
convert at the edges).

## 4. Capture pipeline (metrology honesty)

- **Calibration mat, not A4 sheet.** A banner-printed ChArUco/coded-grid mat
  (~1.5×1.0 m, print-shop cheap) the piece lies ON — full-field scale + distortion.
  **Blocker fix:** an A4 sheet *beside* a 1 m Lower panel cannot honestly deliver
  ≤0.5 cm. Honest tiered error spec: ≤2 mm inside the mat cage under compliant
  capture; larger pieces via fixed capture station (phone mount above table —
  preferred) or mat-registered multi-shot; every capture passes a quality gate
  (min markers visible, reprojection residual, tilt limit) or is REJECTED —
  including gallery photos without the mat. Mat self-check per photo (known
  inter-marker distances) so mat wear can't rot calibration silently.
- **Segmentation ladder,** cheapest first: mat-prior background subtraction →
  GrabCut → ONNX small-SAM point-prompted assist. Interactive loop < 5 s CPU-only;
  no GPU on the critical path.
- **Confirm screen = 3-step annotator,** not a polygon check: (1) boundary
  confirm/correct, (2) mandatory grain arrow, (3) notch/drill tapping (CV proposes
  from raw contour curvature, human confirms). The real acceptance gate is
  **numeric**: auto-measured key dimensions shown beside the master's tape numbers;
  confirm least-squares-fits the polygon to the tape values.
- **Phone = capture + coarse accept/retake** (big buttons, hinglish hints);
  fine vertex editing = desktop/tablet (allowed: management flows are
  desktop-first-class under the mobile-first rule). If phone editing ships:
  loupe magnifier + ≥44 px handles + paint-to-correct brush, and the mandated
  design-system extension audit runs BEFORE build (no canvas component exists
  in the frozen system).
- **Per-size burden attacked, not denied** (~30-40 captures/product is the real
  adoption cliff): batch capture (all pieces of one size in one mat photo,
  auto-split), checklist-driven capture sessions (mirrors `CuttingPatternVerification`
  UX — cutting.py:273), shape-matching against sibling sizes. Graded cardboard sets
  are the factory reality — capture each size. **Scaled sizes = draft only**, usable
  in markers solely after tape-confirmation upgrades them (D9). Friction gate:
  ≤ 90 s per piece, measured like §6 of the ops master measures manager split-time.
- **Physical master wins.** Cardboard gets trimmed on the floor; recapture triggers
  (e.g. alter spikes at Checking on a product) re-open the digital twin.

## 5. Frozen-architecture compliance contract (the module's constitution)

1. `patterns_ai` tables hold **PROPOSALS + its own history only**. It never writes
   any production table. Humans accept suggestions by entering data through
   existing production UIs/services. (The ops-master §11 row's wording "proposing
   markers/size-allocations back into the SAME masters" is amended to say this —
   owner decision D8.)
2. **UI seam = link-out only.** Production templates get `{% url 'patterns_ai:…' %}`
   links (URLconf resolution, no module import); "prefill" = user-initiated
   deep-link carrying query params. `config/.importlinter` gains patterns_ai in
   root_packages + contracts, PLUS a FoundationPurityTests-style runtime test
   (contract 2 is report-only today — .importlinter would not catch creep).
3. FK direction: patterns_ai → production only (same rule as machines, core.py:127).
4. **No money.** Reports speak meters and % — never ₹ until GSM exists (D3), and
   even then read-only presentation honoring ADR-0009 honest-NULL. Any ₹-saved
   widget drifting toward costing dashboards trips the Money-Write STOP rule.
5. RBAC: capture/correct = cutting_master skill (or new skill — D4); geometry
   approve = cutting_master with receipt; **marker activation = manager/owner**;
   low-literacy workers never see geometry screens. Every URL gets its
   `SidebarItemRule` row.
6. Media: own tree `media/patterns_ai/<product>/…`; originals immutable +
   checksummed; derived renditions regenerable and excluded from forever-retention;
   periodic DB↔disk integrity job; S3/MinIO switch point + restore-time target
   declared in the runbook (ADR-G).
7. Compute isolation: SAM/nesting run as pinned subprocess/container runtimes with
   own lockfiles — Django's venv never imports torch; weights + engine forks
   vendored into owned storage, checksummed, never fetched at deploy (ADR-F);
   LGPL libnest2d stays subprocess-isolated permanently.
8. Governance: PDD v1.0 is frozen — this module enters via ADR + PDD amendment
   BEFORE P1. DEV-marked dummy data per the standing test-data authorization.

## 6. Trust & adoption ladder (the master trusts cardboard, not screens)

- **Gate 1 — polygon approval:** 1:1 overlay print of each digitised piece
  (4-12 A4 sheets per piece — feasible); master lays his cardboard ON the print;
  match = approved receipt (who/when/photo).
- **Gate 2 — marker activation:** *cut one lay both ways.* First Adda on a new
  marker cuts one ply from the AI layout beside one ply of the master's manual
  layout; compare piece dims + end-of-lay leftover; stored as
  `MarkerValidationEvent`; only then status = approved.
- **Gate 3 — first-ply check** on later Addas: measure 2 key dims of the first cut
  piece before cutting the stack.
- **v1 output = marker as instruction diagram.** The master keeps hand-drawing on
  the top ply (today's actual floor practice — cutting.py:30-33) but copies the AI
  layout from a dimensioned one-page diagram: zero taping, zero scale risk,
  immediate utilization benefit. Full-size tiled printing allowed only for SHORT
  markers (3-Patti) with a hard ritual: 100 mm calibration square + crop marks on
  EVERY sheet, app refuses to mark the print usable until the measured square is
  confirmed = 100 mm (printer fit-to-page is a permanent, recurring threat).
  Plotter (HPGL) re-cost happens after the library proves value (D5).
- **Floor language:** marker cards say *"X meters per 100 garments"*; efficiency %
  is secondary; no rupees on floor screens.
- **The daily seam:** a recommendation surface at the Pattern Design stage panel —
  ranked stored markers matching THIS Adda's rolls + ratio, fit warnings, explicit
  "no match → request new marker / proceed manual" path; picking one writes
  `MarkerUsage`. Composes from canon: `.panel` + `.stat-grid`/`.stat-card` per
  alternative + inline SVG preview + `.sticky-bar` CTA + FancySelect (reference
  family: settlement stat-card screens).
- **Succession:** capture skill deliberately spread to ≥2 people (D4); versions
  carry notes so the asset is knowledge, not just shapes.

## 7. Feedback = "the system remembers and compares"

- Facts: `MarkerUsage` (+plies, measured width) → `LayeringRecord` lay_count ×
  layer_length_meters (nullable — honest-NULL, skip never guess) →
  APSCPB garment actuals (+ `CuttingPieceBreakup` for piece-grain checks).
- Cheap consistency guard the data already enables: nested pieces × plies vs
  `pieces_count` × garment count.
- Ranking guards (anti-fake-ML, in the spec not the backlog): paired comparisons
  only within identical (product, fabric_group, width-band, ratio); minimum n ≥ 3
  Addas before any "recommend" text renders; visible "based on N Addas" badge;
  recency tie-break; **exploration policy** so the first marker ever used doesn't
  rich-get-richer forever; confounders acknowledged (cutter skill, shade lots,
  relaxation, splices) — data-quality flags on every outcome row.
- **Measurement foundation ships EARLY** (backfill-only-known-facts rule: unmeasured
  history is unrecoverable): GSM on ClothType (D3), measured usable width at lay,
  end-loss/splice count per lay — each an owner-gated additive decision.

## 8. 2-5 year risk register (top items, each with its mitigation already in §3-§7)

| Year | Risk | Mitigation anchor |
|---|---|---|
| 1-2 | Brand sends DXF-AAMA pattern; import lossy → platform loses to a pen drive | AAMA entities in schema v1; **import promoted to P1/P2**, export by P4 with round-trip tests |
| 2-3 | First confidently-wrong "marker B wastes less" (n=3, unmeasured width) destroys owner trust | §7 guards + honest badges |
| 2-3 | /media tens of GB; restore drills exceed downtime tolerance | ADR-G tiers + S3 switch point + integrity job |
| 2-4 | Torch/SAM link-rot or libnest2d fails to compile on new GCC; capture down for weeks | ADR-F vendoring + annual rebuild-from-vendored drill + engine-agnostic stored format + bottom-left-fill heuristic as always-works floor |
| 2-4 | Plotter arrives; placements JSON has undocumented units/origin → every marker re-verified by hand | mm units + written spec + `schema_version` from first row (ADR-C = P1 gate) |
| 3-5 | Factory #2 (ADR-0010): product-level "active marker" forces schema migration | recommendation context key + documented (not built) site slot; library stays global |
| any | Uncalibrated legacy gallery photos silently trusted in markers | trust grades + marker generation restricted to calibrated geometry |
| any | Production→patterns_ai import creeps in and calcifies (contracts report-only) | runtime purity test (§5.2) |
| any | "Optimize by embedding" refactor inlines LGPL engine | ADR-F isolation rule, restated in module README |
| 3+ | Pattern master leaves; shapes without knowledge | receipts, notes, provenance, ≥2 trained people |

## 9. Roadmap (each phase leaves something the factory uses)

| Phase | Deliverable | Gate (proof) |
|---|---|---|
| **ADR pack** (kickoff, ~days) | ADR-A engine bake-off protocol · ADR-B async worker (ERP-level) · ADR-C geometry spec + versioning (**P1 gate**) · ADR-D marker immutability/reuse/staleness · ADR-E calibration mat + tiered error spec · ADR-F vendoring/isolation · ADR-G media lifecycle · ADR-H app boundary + read-only contract + PDD amendment | owner signs; §11 ops-master row amended (D8) |
| **P0 Feasibility** | hostile engine bake-off (fixed harness: real digitised T-shirt front/back/sleeve + patti polygons, concave, 0/180 grain, real widths, wall-clock budget; pynest2d concave-adjacency specifically tested; Node-headless SVGnest runner budgeted as likely primary; bottom-left-fill floor) + metrology POC | ≥75-80% utilization; **must include one >1 m piece, one curved-heavy piece, one on-fold tubular piece** (the draft's patti-only gate was rigged toward the easy case); per-tier error published |
| **P1 Library core** | `patterns_ai` app: full schema §3 (incl. MarkerUsage skeleton), asset store (immutable originals), manual entry + SVG import, **DXF-AAMA import**, geometry spec doc + SVG export, DEV dummy T-Shirt library (owner-authorized) | a real pattern lives in the library end-to-end; spec doc checked in |
| **P2 Capture** | mat + capture station + wizard + segmentation ladder + 3-step annotator + trust grades + Gate-1 overlay prints; batch/session capture | master digitises a real graded set unaided; ≤90 s/piece; error tiers met on factory table |
| **P3 Marker room** | async worker (ADR-B build), strategy alternatives + honest three-numbers cards (floor language), instruction-diagram output + short-marker tiled print with 100 mm ritual, Adda recommendation surface + `MarkerUsage`, Gate-2 ritual | marker beats the master's manual layout on 2 real products, proven by cut-one-lay-both-ways receipts |
| **P4 Feedback** | measurement foundation (GSM/lay measurements — owner-gated additives) + `MarkerOutcome` + predicted-vs-realized report with §7 guards; DXF-AAMA export | report renders honest numbers for ≥3 Addas; no recommendation without n≥3 |
| **P5 Hardware/exchange** | HPGL plotter · projector · (fabric-print SVG) behind one output interface with per-output validation rituals; **tightened error spec re-proven before plotter ever cuts** | when hardware exists |
| **P6 (probably never)** | real ML, only if hundreds of outcome pairs exist AND ranking can't do the task | written gate, not a promise |

## 10. Open owner decisions (kickoff agenda — like ops-master §5)

| # | Decision | Default recommendation |
|---|---|---|
| D1 | "Multiple Pattern Sets" = revisions over time, or also fit variants (slim/regular)? | revisions; variants = labelled sibling dimension if ever needed |
| D2 | Additive `fabric_construction` (tubular/open) field on ClothType/roll intake? (frozen-foundation touch) | yes, additive nullable; per-cloth-type owner ruling like Phase-2 decisions |
| D3 | GSM capture — on ClothType at intake? (prerequisite for any ₹ number) | yes, early (P4 measurement foundation); until then meters/% only |
| D4 | Who digitises + approves? (no pattern capability exists in RBAC today) capture skill spread to ≥2 people? | capture=cutting_master skill, activate=manager/owner |
| D5 | Accept v1 output = instruction diagram (master still chalks)? plotter re-cost when? | yes; plotter after P4 proves value |
| D6 | Print path for short markers: office printer + ritual, or plot-shop A0? | office printer + forced 100 mm confirm |
| D7 | Approve small purchases: banner-printed calibration mat + phone mount (capture station)? | yes — the honest metrology answer, trivial cost |
| D8 | Amend FACTORY_OPERATIONS_MASTER §11 AI-row wording to "proposals only; humans re-enter via existing UIs"? | yes (doc-sync; removes a locked-rule contradiction) |
| D9 | Scaled-size geometry policy: draft-only until tape-confirmed? | yes — never nest unconfirmed scaled knitwear |
| D10 | Optional local-LLM (Ollama) for template drafting? | skip for now; flag-gated later |

## 11. Dummy-data plan (authorized by standing test-data rule)

DEV-marked dummy T-Shirt Pattern Library: 4 body pieces + 2 rib pieces, synthetic
but realistic polygons (mm-true), 4 sizes, fake capture photos clearly watermarked
DEV, one PatternSetRevision, 3 sample markers (one per strategy) with placements,
one dummy MarkerUsage against a DEV Adda. Purpose: build + demo + practice mode
for the capture wizard before any real cardboard is photographed. Never a
future-phase dependency.

## 12. V1.x idea register (living — append while manufacturing continues)

Owner mandate 2026-07-06: while manufacturing runs, any discovery that would improve
this platform is appended HERE with date + trigger + which section it would amend.
Never implemented before kickoff; the kickoff review folds accepted entries into V2.

| # | Date | Idea | Trigger / evidence | Amends |
|---|---|---|---|---|
| I-1 | 2026-07-06 | **Freeze-at-start via a named service is load-bearing, and bypass paths are the failure mode.** The ERP freezes stage rates only through `ensure_stage_role_rates(sr)` at stage start; a fixture that bypassed it silently produced "std unpriced" costing until backfilled. For patterns_ai: `MarkerRequest` input snapshots and `Marker` artifacts must be creatable ONLY through `marker_service` (single writer) — and the design should state that import/backfill tooling goes through the same chokepoint, never raw ORM. | 3-PATTI-016 journey fixture (A360 "std unpriced") | §3 (services), ADR-D |
| I-4 | 2026-07-06 | **One quantization home from line one.** Manufacturing's paisa rounding rule survived as 3 identical copies only by luck (engineering sweep consolidated them into `q_paisa`). patterns_ai gets ONE precision helper (mm rounding, area, utilization %, placement coords) in its service layer from the first commit — geometry must never have two rounding rules. | Engineering sweep: q_paisa consolidation | §3 services, ADR-C |
| I-3 | 2026-07-06 | **Offer concrete existing options, never abstract dimension pickers.** The manufacturing allocate form originally exposed separate colour+size dropdowns (duplicate entries, impossible pairs) and was replaced by ONE "cut lot" select listing actual pool rows with availability — instantly clearer. The marker room must do the same: list real candidate markers ("M1 · tube 17″ · S2:M2:L1 — 84.8% · used on 3 Addas"), never width/ratio form fields beside a lookup table. | Excellence-audit fix E-1 (_stage_panel_generic pair-select) | §6 (marker room UI) |
| I-2 | 2026-07-06 | **3-PATTI-016 = the reference world for P1 dummy data + the first MarkerOutcome worked example.** Real numbers now exist end-to-end: 30 plies × 1.50 m lay on a 37″ tubular roll → APSCPB 60 pcs (Red S1 24 / Red S2 18 / Blue S1 18) → packed 54. A worked predicted-vs-realized utilization example in the blueprint should use THIS Adda so the feedback math is grounded in owned data (and it exercises the tubular + multi-dim case §0.2 demands). | 3-Patti real-flow journey settled ADST-0006 | §7, §11 |
