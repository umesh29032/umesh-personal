# AI Pattern Intelligence — Architecture + Roadmap DRAFT (PRE-PROJECT)

> **Status: ⚠️ SUPERSEDED 2026-07-06 by [03_PLATFORM_BLUEPRINT.md](03_PLATFORM_BLUEPRINT.md)**
> after the owner's platform-vision statement + 7-lens adversarial review (12 blockers
> found in this draft — e.g. geometry keyed on cross-product ProductPattern, no per-size
> geometry, placements-as-JSON, missing MarkerUsage, tubular knit absent). Kept for
> history; the risk framing + ADR seeds below fed the blueprint. Original status:
> draft for validation at kickoff; nothing built; open-source-first; integrates INTO
> the ERP; never a separate application.

## 1. Owner workflow (the product, in factory language)

1. **Pattern Library** — every pattern piece of every product lives in one
   place: name, product, piece count per garment, grain line, pair/mirror flag,
   size set, version history, photos, and the digitised outline.
2. **Getting a pattern in** (three doors, same result):
   a. **Camera capture** — lay the cardboard pattern on the table next to the
      printed calibration sheet (ArUco) → photo → auto outline (SAM + OpenCV)
      → worker/master adjusts the outline on screen → dimensions confirmed.
   b. **Gallery upload** — same pipeline from an existing photo.
   c. **Manual dimension entry / file import** — rectangles+curves entered by
      measurements, or SVG/DXF import (Seamly2D/FreeSewing/commercial CAD).
3. **Marker room** — pick product + size ratio (prefill from
   `CuttingPatternSizeAllocation`) + cloth width (prefill from the Adda's
   attached rolls) + constraints (nap? tilt tolerance?) → engine returns
   **multiple marker alternatives** (efficiency %, lay length each) → master
   picks → **marker version saved** and reusable for every future Adda of that
   product/width. Print (tiled PDF) today; plotter (HPGL) later.
4. **The loop closes in the ERP**: chosen marker's lay length + ratio feed the
   Layering stage plan; APSCPB actual-cut vs marker-predicted feeds a
   utilisation report (predicted vs achieved efficiency per Adda).

## 2. Architecture draft (validate at kickoff)

- **New Django app `patterns_ai`** (own service layer, single-writer
  discipline, zero writes into frozen production models). FKs point INTO
  production (`ProductPattern`, `Product`) — same direction rule as machines.
- **Data model (draft):**
  - `PatternPieceGeometry` — FK ProductPattern · version int · outline
    (closed polygon w/ curves, JSON) · grain vector · allow_180 bool (nap) ·
    pair_of FK-self (mirror) · seam allowance mm · source enum
    (photo/manual/import) · calibration metadata · photo FK.
  - `Marker` — product · size_ratio JSON · cloth_width · tilt tolerance ·
    engine params · **placements JSON** (piece→x,y,rotation,flip) · lay_length
    · efficiency % · status (draft/approved) · version chain (ADR-0010-style
    append-only; approved markers immutable).
  - `MarkerRun` — async job record (engine, duration, alternatives produced).
- **Engine service** — `nesting_service` behind ONE interface with two
  backends: `libnest2d` (Python binding, subprocess-isolated → LGPL-clean,
  server-side batch) and `SVGnest` (browser, interactive tweak mode). Garment
  constraints (grain/nap/pairs) compiled to engine rotation/mirror constraints
  BEFORE the engine — the engine stays garment-ignorant.
- **Long jobs**: nesting runs seconds→minutes → needs the project's FIRST
  background-job decision (management command + polling vs a queue) —
  ADR candidate; the ERP has no async worker today and manufacturing must not
  inherit one silently.
- **Integration points (all existing, verified live):** Pattern Design
  checklist/console (UI seam) · `ProductPatternAssignment` (piece counts) ·
  `CuttingPatternSizeAllocation` (ratios) · Layering (lay length, plies,
  roll width) · APSCPB (actual vs predicted) · `Stage.description` hints.

## 3. Roadmap draft

| Phase | Deliverable | Proof |
|---|---|---|
| P0 Feasibility POC | photo → calibrated polygon → nest 3-Patti pieces at real width → SVG marker + efficiency % | ≥75% efficiency on patti pieces; capture error ≤ 0.5cm |
| P1 Pattern Library | `patterns_ai` app: geometry model + versioning + photos + manual entry + SVG/DXF import | library UI, no engine |
| P2 Capture pipeline | camera/gallery → SAM+OpenCV+ArUco → editable outline @mobile | master digitises a real pattern unaided |
| P3 Marker engine | nesting_service + constraints + alternatives + versions + tiled-PDF print | efficiency ≥ manual marker on 2 real products |
| P4 ERP loop | Pattern-Design-stage integration, layering prefill, predicted-vs-actual report | full Adda planned via marker |
| P5 Output evolution | HPGL plotter · fabric-print export | when hardware exists |

## 4. Risks (top 6)

1. **Photo metrology** — lens distortion + paper curl → dimension error;
   mitigations: ArUco board (not single marker), flatness instruction,
   mandatory human confirm of 2 key measurements. If error >0.5cm, manual
   entry stays the trust path.
2. **Nesting quality vs commercial** — Gerber/Lectra have 30 years of garment
   heuristics; expectation-set with the owner: target = beat HIS manual
   markers, not Lectra. Multiple-alternatives UX covers algorithm weakness.
3. **Compute time** — GA nesting is minutes at high piece counts; async-job
   ADR + "draft now, refine overnight" mode.
4. **Grading** — photo-digitised pieces don't grade; per-size capture or
   Seamly2D-import path for graded patterns. Scope P1 clearly.
5. **LGPL hygiene** — libnest2d via subprocess; never static-link.
6. **Scope creep into manufacturing** — the module NEVER writes production
   truth; it proposes plans that Pattern Design/Layering humans accept.
   (Frozen-architecture rule inherited.)

## 5. ADR candidates (write at kickoff)

- ADR-A: nesting engine choice + isolation (libnest2d subprocess + SVGnest
  interactive; benchmark gate from P0).
- ADR-B: background-job architecture for long nesting runs.
- ADR-C: pattern geometry canonical format (internal JSON polygon+curves;
  SVG/DXF as import/export only) + versioning immutability.
- ADR-D: marker immutability + reuse semantics (approved marker = frozen
  artifact referenced by Addas, ADR-0010 style).
- ADR-E: calibration standard (printed ArUco board spec + acceptance error).
