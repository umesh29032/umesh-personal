# AI Pattern Intelligence — Research (PRE-PROJECT, 2026-07-06)

> **Status: 📚 RESEARCH ONLY — nothing implemented.** Owner order: prepare the
> project while manufacturing finishes; implementation starts only AFTER the
> manufacturing freeze + validation. Open-source-first is a hard constraint.

## 1. The domain — what professional garment CAD actually does

**Marker making** = arranging all pattern pieces of an order (every size in its
ratio) onto a rectangle of fabric (the *marker*) whose width = usable cloth
width and whose length = the lay length, minimising wasted cloth. Commercial
tools (Gerber AccuMark, Lectra Diamino, Optitex) treat this as their crown
jewel. Key domain facts the module must respect:

- **Marker efficiency** = Σ piece areas ÷ (width × lay length). Manual markers
  run ~75-85%; good automated nesting reaches 80-92% depending on garment.
  Every 1% efficiency on a 10,000-pc order is real money — this is THE metric.
- **Nesting** = 2D irregular-shape bin packing (NP-hard). The industry-standard
  approach is **NFP (no-fit polygon)** placement driven by a metaheuristic
  (genetic algorithm / simulated annealing) over placement order + rotations.
- **Constraints that make garments different from laser-cutting**:
  - **Grain direction**: every piece carries a grain line; pieces may usually
    rotate only 0°/180° (± small tilt tolerance), NOT freely.
  - **Nap / one-way fabrics** (brushed, printed direction): 180° rotation
    forbidden → all pieces face one way.
  - **Pair pieces**: left/right mirrored pieces (sleeves, legs) — either cut
    mirrored or flipped placement allowed only when fabric is non-directional.
  - **Size ratios**: a marker is cut over a multi-ply lay, so it contains the
    SIZE MIX (e.g. S:2 M:2 L:1 per marker repeat) — marker planning and lay
    planning are coupled (our Layering stage records plies).
  - **Fabric width variance**: knits vary roll-to-roll; markers are made for a
    nominal usable width (our ClothRoll records width already).
  - **Splice marks / defects**: advanced; out of scope initially.
- **Grading**: generating the same pattern in multiple sizes. Parametric CAD
  (Seamly2D-style) grades from measurement tables; photo-digitised patterns
  grade poorly — for photos, each size is captured or scaled per size chart.

## 2. Open-source technology survey (licenses verified via sources below)

### Nesting engines (the core)
| Tech | What | License / notes |
|---|---|---|
| **SVGnest** ([github](https://github.com/Jack000/SVGnest), [site](https://svgnest.com/)) | JS, NFP + genetic algorithm, concave + holes support — the reference OSS implementation | MIT; browser/Node; battle-tested concept |
| **Deepnest** ([deepnest.io](https://deepnest.io/)) | Desktop nesting app built on SVGnest lineage (laser/CNC) | open source; good UX reference for "multiple alternatives + iterate" |
| **libnest2d** ([github](https://github.com/tamasmeszaros/libnest2d), [Ultimaker fork](https://github.com/Ultimaker/libnest2d)) | Modern C++ NFP nesting library (used inside 3D-printer slicers), boost::geometry + polyclipping | LGPL; fast; **[nest2D](https://github.com/VovaStelmashchuk/nest2D) = Python binding** |
| Athlici/Packing ([github](https://github.com/Athlici/Packing)) | continuous-rotation research nesting | reference only |

**Assessment:** none of these natively speak "grain/nap/pairs" — but all
accept per-piece rotation constraints (0/180 restriction expresses grain+nap)
and mirrored duplicates express pairs. The garment semantics live in OUR data
model; the engine just gets constrained polygons. A Python-side engine
(nest2D/libnest2d) fits Django naturally; SVGnest fits a browser-side
interactive fallback. POC should benchmark both on real patti/tee pieces.

### Pattern sources
| Tech | What | License |
|---|---|---|
| **Seamly2D** ([github](https://github.com/FashionFreedom/Seamly2D)) | parametric pattern CAD (Qt), multi-size measurement grading, active | GPLv3+ (desktop tool — we exchange FILES with it, no code linking) |
| **FreeSewing** | parametric patterns from body measurements (JS) | MIT |
| SVG/DXF-AAMA | interchange formats — Seamly2D exports; commercial CAD exports DXF-AAMA/ASTM | our internal piece format should import SVG + DXF |

### Photo digitization (the owner's camera workflow)
| Tech | What | License |
|---|---|---|
| **OpenCV** ([docs](https://docs.opencv.org/4.13.0/d5/dae/tutorial_aruco_detection.html)) | contour extraction, perspective correction, **ArUco markers** for scale calibration (print an A4 calibration sheet, lay it next to the pattern piece → pixels→cm) | Apache-2.0 |
| **SAM (Segment Anything)** ([github](https://github.com/facebookresearch/segment-anything)) | one-click piece segmentation from a photo of a paper/cardboard pattern on the table | Apache-2.0 (code + weights) |
| Simplification | OpenCV `approxPolyDP` / Douglas-Peucker → editable polygon + spline smoothing | — |

### Output
| Need | Tech |
|---|---|
| Marker print (paper, tiled A4/A0) | SVG → PDF (CairoSVG/WeasyPrint, LGPL/BSD) |
| Future plotter | HPGL generation from SVG paths (plotters speak HPGL/DMPL — simple path-to-pen-moves translation, no library dependency needed) |
| Future fabric printing | same SVG source |

**License verdict: a fully open-source stack exists end-to-end.** Only
watch-item: libnest2d is LGPL (dynamic-link or subprocess keeps us clean);
Seamly2D GPL is irrelevant (file exchange, not linking).

## 3. What our ERP already captures (the integration head-start)

Pattern Design stage already owns: `ProductPattern` (+`ProductPatternAssignment`
pieces-per-garment), `CuttingPatternRecord` + verification **photos** (camera
capture exists on the checklist flow), `CuttingPatternSizeAllocation`
(size-mix proportions!), Layering records (plies, lay length, roll widths),
APSCPB (actual cut truth per colour×size — the feedback loop for predicted vs
actual utilisation). The AI module READS these masters; writes are
PROPOSALS ONLY — humans re-enter via existing UIs (blueprint §5.1 supersedes
the original reads/writes framing). It is an upgrade of the Pattern Design
stage's brain, not a parallel app.

Sources: [SVGnest](https://github.com/Jack000/SVGnest) · [svgnest.com](https://svgnest.com/) · [Deepnest](https://deepnest.io/) · [libnest2d](https://github.com/tamasmeszaros/libnest2d) · [Ultimaker/libnest2d](https://github.com/Ultimaker/libnest2d) · [nest2D](https://github.com/VovaStelmashchuk/nest2D) · [Seamly2D](https://github.com/FashionFreedom/Seamly2D) · [Valentina (Wikipedia)](https://en.wikipedia.org/wiki/Valentina_(software)) · [OpenCV ArUco](https://docs.opencv.org/4.13.0/d5/dae/tutorial_aruco_detection.html) · [segment-anything](https://github.com/facebookresearch/segment-anything)
