# AI PATTERN INTELLIGENCE — PROJECT KICKOFF CONTRACT (2026-07-06)

> **Status: 📜 CONTRACT — no implementation. This document + the design of
> record ([AI_PATTERN_INTELLIGENCE/03_PLATFORM_BLUEPRINT.md](AI_PATTERN_INTELLIGENCE/03_PLATFORM_BLUEPRINT.md))
> are what the next session opens with. Manufacturing V1 is FROZEN
> ([MANUFACTURING_V1_FREEZE.md](MANUFACTURING_V1_FREEZE.md)) and is the
> permanent foundation this project builds ON, never INTO.**
> Companion pack: [01_RESEARCH.md](AI_PATTERN_INTELLIGENCE/01_RESEARCH.md)
> (verified open-source stack) · 02 (superseded draft, history) · 03 (blueprint
> v1, owner-accepted, LIVING until kickoff review) — read in that order.

---

## 1. Executive summary

Build the industry's best **open-source AI Pattern Intelligence platform**
inside the ERP: every Product permanently owns its Pattern Library (pieces,
per-size geometry, versions), its Marker Library (many markers, many
alternatives, never overwritten), and its production feedback (which marker
actually ran, what it actually yielded). Deterministic computer vision digitises
the factory's physical cardboard patterns; a nesting engine generates marker
alternatives; humans confirm everything before it becomes truth; the system
recommends markers from real production history without any manual model
training. It is **not a separate application** — it is the intelligence layer
of the Pattern Design stage, which becomes the brain of the manufacturing
pipeline. Largest project in the ERP; same engineering discipline as
Manufacturing V1.

## 2. Objectives

1. Permanent, product-centric Pattern + Marker Libraries (company asset,
   versioned forever, nothing overwritten).
2. Three capture doors — camera, gallery, manual measurements — with honest
   metrology and human confirmation.
3. Marker generation: multiple genuinely-different alternatives per request,
   visual preview, honest utilization numbers, floor-language outputs.
4. Closed production loop: MarkerUsage → Layering/APSCPB actuals →
   MarkerOutcome → ranked recommendations with sample-size honesty.
5. 100% open-source, offline-reproducible from our own repository.

## 3. Assumptions

- Manufacturing V1 frozen; its seams stable (nothing else writes the pattern
  masters — ops-master §11).
- Rate card POSTPONED to pre-production-rollout (owner ruling 2026-07-06) — DEV rates stand for development; checkpoint commit = owner's step.
- Small factory server, CPU-first; phones = Android @390 for capture/preview.
- Solo junior developer + AI pair; phased delivery; every phase ships something
  the factory uses.
- Dummy DEV data authorized (dummy T-Shirt library; 3-PATTI-016 = grounded
  reference world for feedback math — blueprint I-2).

## 4. Integration boundaries & manufacturing interfaces

**New Django app `patterns_ai`.** All FKs point INTO production. Production
never imports it. UI seam = link-out/deep-link only (no production-code import
of the new app); importlinter + a runtime purity test enforce it.

| Manufacturing interface | What patterns_ai does with it |
|---|---|
| `ProductPattern` + `ProductPatternAssignment` (cutting.py:47, :88) | **The permanent integration point.** Identity/name + pieces-per-garment are READ; geometry lives in patterns_ai keyed per (product, pattern) — the shared cross-product library entry is never mutated (frozen-foundation rule). |
| `ProductSize` (cutting.py:242) | per-size geometry key (PROTECT FK) |
| Pattern Design stage (`CuttingPatternRecord` + photos, checklist console) | **The primary workspace.** Physical verification stays; the console links out to the marker room; capture sessions mirror its checklist UX. |
| `CuttingPatternSizeAllocation` (cutting.py:321) | per-Adda size-ratio PREFILL (percent → integer repeat counts conversion rule) |
| Layering (`LayeringRecord`/`LayeringRollEntry`, layering.py:13/:48) | plies × lay length × verified widths = actual fabric-in for outcomes; marker lay-plan is an ADVISORY the human copies into the existing layering UI |
| Cutting / `APSCPB` (cutting.py:500) + `CuttingPieceBreakup` | the cut-piece actuals side of predicted-vs-realized |
| `ClothRoll.width_inch` (raw_materials/models.py:99) | nominal width PREFILL only — marker truth = human-confirmed usable width in mm |
| Adda | `MarkerUsage` FK target (allowed direction); **Adda-level generation** when product data is insufficient (owner vision §OV) |

## 5. Frozen contracts AI cannot violate (inherited, non-negotiable)

1. patterns_ai holds **proposals + its own history only** — it NEVER writes any
   production table; humans accept by entering data through existing UIs.
   (Ops-master §11 wording amendment = owner decision D8 at kickoff.)
2. **No money.** Reports speak meters/%; ₹ only after GSM exists (D3) and then
   read-only, honest-NULL (ADR-0009); money-write STOP rule applies.
3. Nothing becomes production truth without **human confirmation**; confirmed
   artifacts are immutable (supersede, never edit) — Data/History rule.
4. FK direction, single-writer services, RBAC via permission_service +
   SidebarItemRule, mobile-first @390, design-system tokens, docs-sync.
5. Manufacturing V1 modules are frozen — any needed change goes through ADR.

## 6. Domain model (the owner's product language, made precise)

- **Pattern Library** — per Product: `PatternPiece` (fabric_group: body/rib/…;
  pair/mirror; on_fold) → `PatternPieceVersion` (draft→confirmed immutable,
  supersede chain) → `PieceSizeGeometry` (per ProductSize; polygon mm +
  grain arrow + notches/drills/internal lines + seam-allowance semantics;
  provenance captured/graded/scaled/imported/manual; trust grade).
- **Pattern Set** — `PatternSetRevision`: immutable snapshot {piece-version per
  piece} per (product, fabric_group); what markers pin. (Revisions over time;
  fit-variants = owner decision D1.)
- **Marker Library** — `MarkerRequest` (human-confirmed inputs: usable width mm,
  construction open/tubular, ratio as integer repeats, allowances) →
  `MarkerRun` (async job; seed + engine version stored) → `Marker` (immutable;
  strategy enum; honest three numbers) → `MarkerPlacement` rows (PROTECT-pin
  exact geometry versions — never loose JSON).
- **Multiple markers per product is structural:** validity varies by fabric
  group × usable width × ratio × construction — several markers are
  legitimately "active" at once; "active" is a **resolution**, not a column.
- **MarkerUsage** — the human act "this Adda cuts with marker M" (FK→Adda);
  append-only with void. THE join key of the whole feedback pillar.
- **MarkerOutcome** — derived fact per usage: predicted vs realized utilization
  (Σ piece-areas × APSCPB counts ÷ lay length × usable width × plies),
  leftover meters, data-quality flags (honest-NULL, skip-never-guess).
- **Version history everywhere; nothing ever overwritten** — approved markers
  and confirmed geometry are permanent; supersession flags staleness.

## 7. Pipelines (deterministic before AI — locked philosophy)

- **Capture:** printed ChArUco calibration MAT (piece lies ON it; not an A4
  sheet beside it) + capture station for >1 m pieces; per-photo quality gate;
  segmentation LADDER — classical CV first (mat-prior + contours + GrabCut),
  small ONNX SAM-family assist only when classical fails, CPU-only, weights
  vendored; 3-step human annotator (boundary → mandatory grain arrow →
  notch/drill taps); numeric acceptance (auto-measured dims vs the master's
  tape, least-squares fit); phone = capture + coarse accept, fine editing =
  desktop; batch per-size sessions; originals immutable + checksummed +
  reprocessable (pipeline_version).
- **Marker generation:** engine bake-off gate (P0) — pynest2d concave tests,
  Node-headless SVGnest runner budgeted, bottom-left-fill as the always-works
  floor; garment constraints (grain/nap/pairs/on-fold/tubular) compiled BEFORE
  the engine; alternatives = one per STRATEGY (mixed/sectioned/fold-aware),
  never reseeds sold as choice; stored placements ARE the marker
  (reproducible: seed + engine commit pinned); outputs in floor language
  ("X meters per 100 garments"), utilization honest (end allowance, edge
  margins); v1 physical output = dimensioned instruction diagram (master still
  chalks) + short-marker tiled print with the forced 100 mm-square ritual.
- **Feedback ("the system remembers and compares"):** deterministic analytics —
  ranking within identical (product, fabric_group, width-band, ratio); n ≥ 3
  before any recommendation renders; "based on N Addas" badge; exploration
  policy against rich-get-richer; confounders flagged, never guessed. **No
  manual training. Real ML earns a slot only if hundreds of outcome pairs ever
  exist AND ranking can't do the task — at single-factory volume, likely never.**

## 8. Honest-AI dictionary (owner-locked vocabulary)

| Owner phrase | Buildable mechanism |
|---|---|
| "AI suggests pieces for a new product" | GarmentTemplate library (seeded from FreeSewing/Seamly2D taxonomies + our own ProductPatternAssignment history) + "copy from Product X" — deterministic; optional flag-gated LOCAL LLM (Ollama) as an admin drafting aid, never a runtime dependency |
| "AI detects the boundary" | classical CV, small-model assist (called computer vision) |
| "AI calibrates dimensions" | ChArUco homography math (called measurement) |
| "AI generates markers" | NFP nesting + strategies (called optimization) |
| "AI learns from production" | append-only facts + guarded ranking (called analytics) |

## 9. Open-source-only · offline-first policy

No cloud AI, no paid APIs, no proprietary CAD dependency. Stack (licenses
verified in 01_RESEARCH): OpenCV (Apache) · SAM-family weights (Apache,
vendored, ONNX CPU) · SVGnest (MIT) / libnest2d (LGPL, subprocess-isolated
forever) · Seamly2D/FreeSewing as FILE exchange · SVG + DXF-AAMA interchange ·
CairoSVG/WeasyPrint print path. Everything reproducible from our repository:
weights + engine forks vendored with checksums; isolated pinned compute runtime
(Django's venv never imports torch); annual rebuild-from-vendored drill; if
training scripts are ever needed they are generated, stored, and documented
in-repo. Geometry format = versioned written spec (mm, origin, rotation
semantics) with guaranteed SVG export from P1 and DXF-AAMA round-trip — data
never trapped. **Local model support** (Ollama-class) is an optional
enhancement slot, never a dependency.

## 10. Owner Vision (canonical — captured from the 2026-07-04→06 discussions)

Everything below is the owner's stated vision, binding on the design:

- **Completely product-centric pattern management.** Every Product owns its
  Pattern Library, multiple Pattern Pieces, multiple Pattern Versions, multiple
  Marker generations, multiple approved Marker alternatives, its pattern
  history, its production feedback, and its future optimization knowledge.
- **Multiple markers per product** — never one-marker-per-product.
- **Different markers for different fabric widths, lay lengths, size ratios,
  and fabric groups** (body vs rib/collar), plus customer and production
  requirements.
- **Pattern capture from gallery** (existing photos).
- **Pattern capture directly from camera** (factory table, phone).
- **Manual dimension entry** as a first-class door (and the trust fallback).
- **AI-assisted boundary detection** (auto outline, scale, dimensions,
  polygons) — assisting, never replacing the user.
- **Human confirmation before truth** — nothing becomes production truth
  without explicit confirmation; manual correction always possible.
- **Marker generation using the uploaded patterns** with real constraints
  (width, lay length, grain, rotation/mirror, quantities, ratios, order).
- **Many marker alternatives per generation** (A 83.4% · B 84.8% · C 85.3%…).
- **Preview every generated marker visually** before choosing.
- **Save marker history forever; never overwrite approved markers.**
- **Marker recommendation based on previous production** — which marker
  historically wasted less, yielded better utilization, should run next.
- **Learning from actual production without manual training** — the ERP already
  captures marker-used, layering, roll width, actual production, wastage,
  APSCPB, historical utilization; knowledge grows from production history
  automatically.
- **Suggested pattern list for completely new products** (T-shirt → front,
  back, sleeve, neck, cuff…) from open knowledge; user uploads/creates; AI
  assists.
- **`ProductPattern` as the permanent integration point** into manufacturing.
- **Pattern Design stage as the primary workspace** — this stage becomes the
  brain of the manufacturing pipeline.
- **Adda-level generation when product data is insufficient** (clarified
  2026-07-06): the Adda may generate a TEMPORARY marker for that production run;
  after human approval it can be **PROMOTED back into the Product library** —
  the Adda only CONSUMES product assets; the Product is the permanent home.
  (Design note: `MarkerRequest` may bind to an Adda context with a promotion
  path; decision D11 rules the mechanics at kickoff review.)
- **The Product is the permanent home of ALL of it** (owner emphasis
  2026-07-06): Pattern Library · Pattern Pieces · Pattern Versions · Pattern
  Sets · Marker Library · Marker Alternatives · Marker History · Marker Usage ·
  Marker Outcomes · AI Suggestions · Capture Assets · Generated layouts.
- **Future plotter support** (HPGL) and **future fabric-printing support** —
  data model stores physical units + conventions from day one so hardware
  bolts on without redesign.
- **Complete offline reproducibility using open-source software only** —
  independent of Claude/OpenAI and every paid API, forever.

## 11. Owner decisions ALREADY MADE (do not re-litigate)

1. **Honest-AI philosophy LOCKED** — deterministic stays deterministic; CV is
   called CV; optimization is called optimization; real ML only if data
   justifies it (§8 vocabulary binding).
2. **Permanence LOCKED** — versioned forever, nothing overwritten.
3. **Open-source-only / repo-reproducible LOCKED** (§9).
4. Blueprint 03 accepted as V1, LIVING until kickoff review; idea register
   §12 carries I-1..I-4 (single-writer freeze discipline · 3-PATTI-016
   reference world · concrete-options-not-pickers UI law · one quantization
   home from line one).
5. Project starts ONLY after Manufacturing V1 freeze + checkpoint commit
   (this package) — then it is the HIGHEST priority.
6. Same engineering discipline as Manufacturing V1: phased, hostile-reviewed,
   4-role audited, docs-synced, single-writer, append-only.

## 12. Decisions REQUIRED at kickoff (owner agenda — blueprint §10)

D1 Pattern Sets = revisions vs fit-variants · D2 additive tubular/open field on
ClothType (frozen-foundation touch) · D3 GSM capture (₹ prerequisite) ·
D4 who digitises + roles (≥2 people) · D5 v1 output = instruction diagram;
plotter re-cost timing · D6 short-marker print path · D7 calibration mat +
capture-station purchase · D8 ops-master §11 wording amendment (proposals-only)
· D9 scaled-size geometry = draft-only until tape-confirmed · D10 local-LLM
template aid now/later. **New: D11 — Adda-level marker generation contract** (owner vision §10,
clarified 2026-07-06): when product data is insufficient, an Adda may generate
a TEMPORARY marker for that production run; after human approval it can be
PROMOTED back into the Product library (promotion = the human-confirm gate;
nothing product-permanent without it). D11 rules the binding, prefill, and
promotion mechanics.

## 13. ADRs required BEFORE coding (write at kickoff)

ADR-A engine choice + bake-off protocol · ADR-B background-job architecture
(ERP's FIRST async worker — decided as ERP-level infrastructure) · ADR-C
canonical geometry format + versioning (P1 GATE: schema_version, mm, AAMA
entity coverage, guaranteed export) · ADR-D marker immutability/reuse/staleness
· ADR-E calibration standard + tiered honest error spec · ADR-F vendoring +
runtime isolation (weights, forks, LGPL subprocess) · ADR-G media/asset
lifecycle (immutable originals, tiers, integrity job, S3 switch point, restore
SLA) · ADR-H app boundary + read-only contract + PDD amendment + RBAC surface.

## 14. Roadmap (proof-gated; each phase leaves something the factory uses)

| Phase | Deliverable | Gate |
|---|---|---|
| ADR pack | A–H signed + PDD amendment + D1–D11 ruled | owner sign-off |
| P0 Feasibility | hostile engine bake-off + metrology POC | ≥75-80% utilization; MUST include one >1 m piece, one curved-heavy piece, one on-fold tubular piece; per-tier error published |
| P1 Library core | patterns_ai app, full schema (incl. MarkerUsage), immutable asset store, manual entry + SVG import, **DXF-AAMA import**, geometry spec + SVG export, DEV dummy T-Shirt library | real pattern end-to-end; spec doc checked in |
| P2 Capture | mat + station + wizard + ladder + 3-step annotator + trust grades + Gate-1 overlay prints | master digitises a graded set unaided; ≤90 s/piece; error tiers met |
| P3 Marker room | async worker (ADR-B), strategy alternatives, floor-language cards, instruction-diagram + ritual print, Adda recommendation surface + MarkerUsage, Gate-2 cut-one-lay-both-ways | marker beats the master's manual layout on 2 real products, receipt-proven |
| P4 Feedback | measurement foundation (GSM/lay measurements — owner-gated additives) + MarkerOutcome + predicted-vs-realized report with guards; DXF-AAMA export | honest numbers on ≥3 Addas; no recommendation below n=3 |
| P5 Hardware/exchange | HPGL plotter · projector · fabric-print SVG behind one output interface | when hardware exists; error spec re-proven first |
| P6 (probably never) | real ML | written gate (§7) |

Trust ladder throughout: Gate 1 cardboard-on-print overlay · Gate 2
cut-one-lay-both-ways · Gate 3 first-ply check — append-only receipts.

## 15. Risks (top, with owned mitigations)

Photo metrology on big pieces (→ mat + station + tiered honest spec + manual
door) · engine immaturity/abandonment (→ bake-off, swappable backends, own-the-
fork budget, BLF floor) · per-size capture burden = adoption cliff (→ batch
sessions, ≤90 s gate, D9 policy) · feedback confounding + tiny samples (→ §7
guards; "remembers and compares" framing) · dependency rot (→ ADR-F vendoring +
annual drill) · media growth/asset loss (→ ADR-G) · DXF-AAMA arriving early
(→ import in P1/P2, schema AAMA-shaped from day one) · scope creep into frozen
manufacturing (→ §5 contracts; STOP rule) · trust collapse from over-promised
"AI" (→ §8 dictionary, owner-facing) · print mis-scale (→ forced 100 mm ritual).

## 16. Success metrics

- **Capture:** ≤90 s + ≤N taps per piece (measured, P2 gate); calibrated error
  within published tier (≤2 mm in-cage) on golden tape-measured pieces; 100%
  of confirmed geometry carries provenance + trust grade + confirmer.
- **Markers:** utilization ≥ the master's manual marker on ≥2 real products
  (Gate-2 receipts); every approved marker reproducible (seed+engine pinned);
  zero orphaned geometry references (PROTECT-pinned placements).
- **Feedback:** predicted-vs-realized report live on ≥3 real Addas; every
  recommendation shows its n; zero recommendations below n=3.
- **Discipline:** zero production-table writes from patterns_ai (purity test);
  zero cloud/API calls (network-isolation test); rebuild-from-vendored drill
  passes; docs-synced every session; 4-role + hostile reviews per phase.
- **Business:** the owner plans a real Adda from a stored marker and the
  leftover fabric matches prediction within the stated tolerance — the moment
  the platform earns its name.


## 17. THE KICKOFF REVIEW SESSION (owner-ordered 2026-07-06 — the next session's agenda)

Implementation does NOT start at kickoff. The next session is a fresh-eyes,
first-principles review — challenge everything, even if it changes the
blueprint. The goal: solve the REAL factory problem, not build a technically
impressive system. Agenda (owner's words, binding):

1. Re-read the complete Owner Vision (§10) — every point.
2. Re-read the Manufacturing V1 freeze contracts
   ([MANUFACTURING_V1_FREEZE.md](MANUFACTURING_V1_FREEZE.md) §7).
3. Verify every integration point again (§4 table, against live code).
4. Challenge the architecture from a FACTORY-OWNER perspective (daily use,
   trust, floor reality — not developer elegance).
5. Suggest anything missed — blueprint changes are allowed and expected.
6. Think 5–10 years ahead: optimize for a PERMANENT platform, not a quick
   implementation.
7. Respect all frozen manufacturing contracts (§5) throughout.

Deliverables of that session: blueprint v2 (or re-certified v1), rulings on
D1–D11 + the §11 ops-master wording (D8), the ADR pack A–H drafted for owner
sign-off. Only after that review completes does **Phase P0 (feasibility +
engine bake-off)** begin.
