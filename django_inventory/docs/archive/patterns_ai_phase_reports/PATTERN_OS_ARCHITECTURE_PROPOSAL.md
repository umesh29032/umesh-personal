> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# THE GARMENT PATTERN OPERATING SYSTEM — architecture proposal
(2026-07-10 · ARCHITECTURE + ROADMAP ONLY — no code, no module touched ·
consolidates ARCHITECTURE_AUDIT_2026_07_10.md (code truth) +
PATTERN_PLATFORM_VISION_REALIGNMENT.md (vision fit) + the owner/advisor
business direction into ONE foundation document)

## The understanding, confirmed

Two hearts:
- **Heart 1 · Manufacturing ERP** (Product→Adda→Layering→Cutting→
  Bundle→Barcode→Inventory) — built, running.
- **Heart 2 · Pattern Intelligence Platform** — the company's
  differentiator: the cutting-master's knowledge, owned by software.

Two DIFFERENT problems that must never mix:

| | Pattern Capture Studio | Digital Cutting Table |
|---|---|---|
| Does | CREATES geometry | CONSUMES geometry |
| Frequency | rare (one-time per piece×size) | daily |
| User | owner / pattern expert | cutting master |
| Character | AI-heavy, ACCURACY first | manufacturing-heavy, SPEED first |
| Posture | laptop-first | laptop-first canvas; mobile consumption around it |

Verified Geometry = the ONLY truth. Every input (photo, DXF, SVG, PDF,
PNG, manual dimensions, AI APIs) = EVIDENCE. AI assists extraction —
proportionally to input quality (DXF: nearly nothing · SVG/PDF: convert
+ verify · photo: heavy) — and never becomes the truth. Human
verification is the gate, always.

---

## Q1 — What already satisfies this vision (audit-verified, keep as-is)

The spine IS the vision — none of this is re-architected:
- Geometry grain **Product × Size (or Universal) × Piece** — exactly.
- The truth model: human-gated confirm · tape ±2 mm · immutable
  append-only versions · `geometry_contract_version` stamp · single
  writer · reference images structurally banned from being truth.
- DCT consume-only (zero geometry writes, confirmed-of-Ready-sizes
  only), mm world ≠ camera, dynamic length, honest AI verdicts.
- Layout Library: immutable, uid + versions + supersede chains, human
  approval, staleness derived (LAW 11), exports from stored rows only.
- Manufacturing link: usage per fabric group (history forever), marker
  content × lay_count advisory, operator authority.
- Blueprint rules (count/optional/pair/fold/grain/fabric group),
  Universal size machinery, the Dashboard as permanent home, the ADR-H
  wall + dependency-inversion crossings, the ERP chain untouched.

## Q2 — What is mixed today and separates

1. **Creation vs consumption UX**: digitization lives as five scattered
   pages (capture wizard, extraction review, version detail, geometry
   editor, DXF import) reached FROM the preparation pages — no Studio.
   The data layer is already separated; the EXPERIENCE is not.
2. **One name, two meanings**: "Pattern Library" = the DCT's left
   panel (P4 amendment 1) AND the vision's knowledge shelf.
3. **Three layout-knowledge stores** for a newcomer to untangle:
   frozen P1-era Marker library · the generator's ★ designation · the
   ApprovedLayout library. The library must be the one answer.
4. **The legacy generator** still linked inside the DCT.
5. **Import is dumb**: single-piece clicks; `pieces_count` (Blueprint)
   has no DCT consumer; no size colors; no mandatory/optional split.
6. **Layering is blind** to the approved layout (no suggested length).

## Q3 — Screens that belong to PATTERN CAPTURE STUDIO

One module, one journey: `Product → Size (or Universal) → Piece →`
- **Evidence Inbox** (NEW shell): upload/attach ANY evidence — photo ·
  DXF · SVG · PDF · PNG · manual dimensions · AI-API results · "reuse
  existing version" (copy-forward). Each item listed with its type,
  status, and which assist ladder it feeds.
- **Extraction/Assist screens** (EXISTING, re-homed): capture wizard
  (mat photo), extraction review (accept/reject one-shot), the
  geometry editor (vertex refine + grain), DXF import. New siblings
  later: SVG/PDF converters, manual-dimension constructor, AI-API
  adapter results — all landing in the SAME review screen.
- **Verify & Publish** (EXISTING confirm, promoted): tape check →
  confirm → the piece×size becomes Verified Geometry in the Library.
Studio = management/expert-gated (already true of every underlying
page). Nothing in the Studio is reachable from worker flows.

## Q4 — Screens that belong to the DIGITAL CUTTING TABLE

Exactly what exists, minus creation leaks:
- The workspace (palette · fabric canvas · layout info · library
  section · status) with physics, Compact, Auto Place, AI Optimize,
  Save Draft, Approve review, view/duplicate.
- The Adda-side consumption screens (choose page, stage panel) stay
  manufacturing-side.
- LEAVES the DCT: the legacy Generate link (retire to the frozen
  research area). The DCT never links into the Studio except a
  read-only "piece not ready → see Library" hint.

## Q5 — The complete UI flow (Product → Approved Layout)

```
Product create (ERP) → Sizes (Universal default)
   → PATTERN DASHBOARD (permanent home)
      STEP 1 BLUEPRINT      pieces + counts + rules            [DONE]
      STEP 2 PATTERN STUDIO evidence → assist → verify →
                            Verified Geometry                  [BUILD: unify 5 pages + new inputs]
      (shelf) PATTERN LIBRARY per size: preview/version/history/
                            SVG/DXF/metrics                     [TUNE: consolidate + name]
      STEP 3 DIGITAL CUTTING TABLE
             choose sizes → SMART IMPORT (mandatory auto-listed,
             Required/Imported/Remaining, optional opt-in,
             refuse-over-required) → per-size COLORS + piece
             labels → arrange/rotate/mirror/lock → AI Optimize
             → Save Draft                                        [TUNE: import UX + colors]
   → APPROVE (human) → LAYOUT LIBRARY (uid · V · stale law)     [DONE]
   → ADDA chooses contract (per fabric group)                   [DONE]
   → LAYERING: “Recommended layer length: 5820 mm” from the
     approved layout (operator can change)                      [NEW EDGE]
   → CUTTING: marker-fed suggestion + advisory reconciliation   [DONE]
   → (gates, flags OFF — designed)                              [PAUSED 8D]
   → Bundles → Barcodes → Inventory                             [ERP]
```

## Q6 — Import that prevents mistakes (the contract)

Choose Product (URL-locked) → tick Sizes (☑S ☑M ☑L) → the system
computes from the BLUEPRINT:
- **Mandatory pieces** auto-listed per size — `Required =
  pieces_count`, `Imported` = live session count, `Remaining` derived;
  import buttons disable at Remaining 0 and REFUSE beyond it with the
  honest count ("Pocket: required 2, already imported 2"). No third
  pocket, ever.
- **Optional pieces** = separate opt-in list (never counted against
  readiness, exactly like generation).
- One-tap **"Import all remaining"** per size (the daily-speed path).
- LAW 12 unchanged (one fabric group per table); deliberate extra
  copies beyond Required = the future cut-plan/ratio input, not
  smuggled in.

## Q7 — Multi-size visualization

- Stable size palette (S blue · M green · L orange · XL purple ·
  further sizes from a fixed cycle), assigned at import: piece FILL
  tint + palette badge + a legend chip row in the workspace meta.
- Piece labels on canvas become `⟨SIZE⟩ · ⟨Piece⟩` ("S · Front").
- The counters (Q6) live in the palette next to each piece name.

## Q8 — Metadata captured at digitization (per piece × size)

Already captured: geometry (int-µm polygon + holes) · dims + tape
truth · trust grade · grain ANGLE (payload feature) + grain RULE
(Blueprint) · fold/pair/optional/fabric group (Blueprint) · area
(derived) · reference image · version history · contract version ·
SVG/DXF on demand (deliberately derived, never stored — one truth).
**To ADD (Studio scope):**
- **Notches** — NOT IMPLEMENTED today; belongs in the payload as
  `features.notches` (additive payload extension ⇒ a conscious
  `geometry_contract_version` bump to `adr-c.2` when introduced — the
  stamp exists for exactly this).
- **Seam allowance** — today DECLARED (contract says cut-ready), never
  modeled. Add as capture-time metadata (declared allowance mm +
  which line was digitized), still cut-line truth; computing offsets
  stays future.
- **Curve fidelity** — chord tolerance exists; curve detection
  (arc/bezier awareness in extraction) = assist-quality improvement,
  payload stays polygon.
- Evidence provenance: which inbox item(s) produced this geometry
  (extraction custody exists for photo; extend the same idea to every
  input type).

## Q9 — AI (Gemini / other APIs) without becoming truth

The codebase already contains the EXACT pattern to copy — twice:
- the segmentation **backend ladder** (`classical` always; `sam`
  activates only when artifacts exist, reports itself unavailable
  honestly);
- `GeometryExtraction` (append-only PROPOSAL row + one-shot human
  review + hard gate + confidence display-only).
**AI APIs = new extraction backends**: a Gemini adapter takes the
evidence image → returns a polygon/dimension PROPOSAL → lands as a
GeometryExtraction (backend='gemini', full provenance, refusal reasons
recorded) → the SAME human review → the SAME writer. Rules that make
it safe: proposals never auto-accept · confidence never gates ·
API failures are recorded refusals · offline/unconfigured = honestly
unavailable (the SAM precedent) · the truth model is untouched. This
also answers "photo pipeline at panel scale": external AI becomes one
more ladder rung ALONGSIDE bigger mats / multi-shot — an evidence
problem, not a truth problem.

## Q10 — Reuse unchanged vs reorganize

**Unchanged (the do-not-touch spine):** geometry models + single
writer + contract stamp · version chains · validators (both runtimes) ·
calibration metrology · compute bridge/runtime (EXTEND with ladders,
never fork) · dxf_io · svg_render · facade (additive-only) · DCT
physics/camera/engine-frame/optimize endpoint · ApprovedLayout + Usage
+ freezes F1–F3 + count hierarchy + manufacturing timeline · Blueprint
module · Universal machinery · Dashboard shell · choose page + provider
inversion · exports · the whole ERP.
**Reorganized:** the five digitization pages → the Studio ·
Manager/Preparing naming → Pattern Library identity · DCT panel rename
("Verified Pieces" proposed — amends frozen P4 amendment 1, owner
call) · legacy generator retired from the DCT + ★ folded into the
library story · import UX rebuilt on the Blueprint counts · the
layering suggested-length edge added · docs re-indexed by MODULE
(phase reports remain receipts).

---

## THE ROADMAP (adopting the owner/advisor 8-phase frame, reconciled with what exists)

| Phase | Name | Content | State |
|---|---|---|---|
| **P1** | Blueprint | structure + rules + counts | ✅ DONE |
| **P2** | Pattern Capture Studio | the Studio shell + Evidence Inbox + re-home the 5 existing screens + input ladders (SVG/PDF/manual-dims) + the large-piece answer (mats/multi-shot/AI-API — owner decision) | 🚧 THE next build |
| **P3** | Geometry Verification | the existing review/confirm/tape machinery PROMOTED to its own explicit surface inside the Studio (+ notches/seam metadata + contract bump when payload extends) | 🚧 with P2 (same writer, same gates — split for clarity, not new truth) |
| **P4** | Pattern Library | consolidation + naming + search + everything-per-piece view | 🔧 TUNE (mostly built) |
| **P5** | Digital Cutting Table | smart import (Q6) + size colors/labels (Q7) + legacy-link retirement | 🔧 TUNE (table done) |
| **P6** | Layout Library | draft/approve/history/versions | ✅ DONE (minor polish only) |
| **P7** | Manufacturing Integration | choose/display/advisory ✅ + the layering suggested-length edge + the paused 8D gates (flags OFF) | 🔧 mostly done |
| **P8** | AI Manufacturing Assistant | photo→geometry→layout suggestion→cost→fabric estimate→efficiency→analytics (revives the frozen advisor/yield/insights against library data) | 🔮 FUTURE |

Order of work once approved: **P2+P3 (the Studio, one build) → P5
(smart import) → P4 (library identity) → P7 completion → P6 polish →
P8 later.** Every step additive; the spine untouched; same milestone
discipline (plan → approve → one → tests → browser → report → STOP).

## Open owner decisions (consolidated — supersedes the realignment's list)

1. Approve this module split + roadmap order.
2. Large-piece capture investment: bigger commissioned mats ·
   multi-shot stitching · AI-API ladder · lean-on-DXF — pick (can be
   staged).
3. Naming: DCT panel → "Verified Pieces"; the shelf = "Pattern
   Library" (amends frozen P4 amendment 1).
4. Retire the legacy generator link + fold ★ into the library story.
5. Laptop-first carve-out for Studio + DCT (scoped amendment to the
   mobile-first standing rule; manufacturing consumption stays mobile).
6. Notches/seam metadata + the `adr-c.2` contract bump land with P3.
7. 8D gates: fold into P7 completion (recommended) or resume as-is.

**STOPPED — architecture + roadmap delivered. No code. When these
seven are ruled, the module map freezes and implementation resumes at
P2 with the standard discipline.**
