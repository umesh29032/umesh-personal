---
id: docs-ai-pattern-intelligence-pattern-platform-vision-realignment
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# PATTERN PLATFORM — VISION REALIGNMENT REVIEW
(2026-07-10 · REVIEW ONLY — no code, no phases · first-principles audit
of everything built (Phases 1–8C + the pre-platform capture era)
against the owner's full business vision · companion:
ARCHITECTURE_AUDIT_2026_07_10.md = the code-level ground truth)

The vision in one line: **the company owns the cutting-master's
knowledge — patterns digitized ONCE by an expert, verified geometry as
the only truth, layouts as permanent manufacturing assets, software
that can guide a novice through manufacturing.**

---

## Q1 — What already matches the vision (keep, untouched)

More than the owner may expect. The DEEP layers are vision-correct:

| Vision requirement | As built | Verdict |
|---|---|---|
| Geometry = Product × Size × Piece | `PieceSizeGeometry` = version(piece) × ProductSize; piece is product-scoped | ✅ EXACTLY the vision's grain |
| Verified Geometry = the only truth | human-gated confirm · tape ±2 mm gate · immutable versions · contract stamp · photo structurally banned from being truth | ✅ the strongest part of the build |
| Digitize once, reuse forever | append-only versions, copy-forward, one geometry feeds facade/DCT/exports/marker-content | ✅ |
| Photo = evidence, multi-input | photo + DXF paths exist; reference images display-only | 🟡 two of the vision's ~7 inputs (Q-gaps below) |
| Expert-only digitization | capture/confirm = management-gated; workers never see it | ✅ (already matches "owner or trusted expert") |
| DCT consumes, never creates | facade rows in, zero geometry writes, audit-verified | ✅ structurally true today |
| Fabric table: width fixed, camera separate | 6B frozen (mm world ≠ camera), tested | ✅ |
| Layouts = permanent assets | ApprovedLayout: uid, versions, supersede chains, immutable, human-approved | ✅ |
| Layouts feed manufacturing | usage per fabric group → stage panel → advisory numbers (content × lay_count) | ✅ advisory today (8D gates designed) |
| AI assists, never replaces | extraction proposals human-accepted; AI Optimize = honest better/same/worse; approval human-only | ✅ philosophy already enforced in code |
| Knowledge over people | staleness law, count hierarchy, manufacturing timeline, benchmark/yield (frozen) | ✅ foundations laid |

**First-principles conclusion: the platform's SPINE (truth model,
immutability, consumption chain) is the vision. Nothing below the UI
needs re-architecture.**

## Q2 — What is currently MIXED (the honest list)

1. **Digitization has no home.** The vision's most important activity —
   evidence → AI assist → verify → Verified Geometry — is scattered
   across five surfaces (capture wizard, extraction review, version
   detail, geometry editor, DXF import) hung off the per-size
   Preparing page. It works, but there is no single "Pattern Capture"
   place an expert sits down at. This is the biggest UX/architecture
   mismatch with the vision.
2. **The name "Pattern Library" points at the wrong thing.** The DCT's
   LEFT PANEL is called Pattern Library (P4 amendment 1); the vision's
   Pattern Library is the company's knowledge shelf (what we built as
   Manager + Preparing pages + the facade). One term, two meanings —
   newcomers will be confused exactly where the vision is clearest.
3. **Two marker-knowledge stores.** The P1-era `Marker`/`MarkerUsage`
   library (manual chalk-photo markers, research-frozen) and the new
   `ApprovedLayout` library coexist; plus the ★ `ProductionLayout`
   designation from the generator flow. Three "which layout is real?"
   answers for a new developer. (Frozen/harmless at runtime; mixed
   conceptually.)
4. **The legacy generate tool** is still one tap from the DCT toolbar —
   a pre-platform flow living inside the platform's flagship page.
5. **Input coverage vs vision**: SVG / PDF / PNG / manual-dimensions /
   external-AI (Gemini etc.) inputs: NOT IMPLEMENTED. Photo path is
   mat-bounded (audit: full-size panels unproven; the real T-SHIRT came
   in via DXF).
6. **Smart import doesn't exist yet**: the DCT palette lists designs
   but knows nothing of Required/Imported/Remaining (the Blueprint's
   `pieces_count` has NO DCT consumer today) and has no per-size
   colors.
7. **Layering never sees the layout**: the vision's "Approved Layout →
   suggested fabric length" edge (length_mm × plies) is absent — today
   only CUTTING consumes the contract.

## Q3 — Should Pattern Capture be its own module? **YES.**

It is the vision's center of gravity and the audit's declared missing
front door. Proposal (no code yet): a **Pattern Studio** module — one
laptop-first surface per (piece × size) with an EVIDENCE INBOX:
- accepts photo / DXF / SVG / PDF / PNG / manual dimensions / future AI
  APIs — each just EVIDENCE;
- runs the right assist ladder per input type (DXF → validate only;
  SVG/PDF → convert + verify; photo → the existing CV pipeline; manual
  dims → construct/scale);
- ends at the SAME gate every time: human verification → Verified
  Geometry via the existing single writer (nothing about the truth
  model changes).
It joins the Dashboard as a module — the owner froze exactly this
extension path ("future modules join the dashboard; navigation never
changes"). Blueprint/Manager/DCT keep their steps; the Studio is where
STEP 2's "Add geometry" actions LEAD instead of five scattered pages.

## Q4 — Should Pattern Library be THE single source of truth? It already IS — name it.

Data-layer truth is already singular (confirmed geometry + facade).
What the vision adds is IDENTITY: consolidate the per-size Preparing
pages + facade + exports under the explicit name **Pattern Library**
(the shelf: geometry, area, grain, fold, reference, SVG/DXF-on-demand,
metrics, version history — every field the owner listed already exists
or derives). Deliberate recommendation AGAINST one vision detail:
do NOT store SVG/DXF blobs — deriving them on demand from the one
geometry truth is strictly better (no stale copies); the Library
PRESENTS them as always-available (it already does). Decision needed:
the DCT panel rename (frozen amendment 1) — suggest "Verified Pieces"
so "Pattern Library" means the shelf alone.

## Q5 — Should the DCT only consume verified geometry? It DOES — finish the separation.

Structurally done (audit-verified: zero writes, confirmed-only,
ready-sizes-only). Two cleanups complete the vision: (a) remove the
legacy Generate link from the DCT (retire the pre-platform tool flow
into the frozen research area); (b) resolve the ★-vs-library duality
in the library's favor (the Adda side already consumes ONLY the
library; the generator's ★ is the last holdout).

## Q6 — The complete user journey (vision-mapped, with today's status)

```
1  Product create (ERP)                                          ✅
2  Sizes — Universal default, archive-guarded                    ✅
3  Dashboard (the permanent home)                                ✅
4  STEP 1 · BLUEPRINT — pieces + count + rules (grain/pair/fold/
   fabric group/optional)                                        ✅
5  STEP 2 · PATTERN STUDIO (per size) — evidence inbox → AI
   assist ladder → human verify → VERIFIED GEOMETRY              🟡 exists
   as scattered pages; photo mat-bounded; SVG/PDF/dims inputs missing
6  PATTERN LIBRARY — the knowledge shelf (browse/version/export) 🟡 exists
   as Manager/Preparing; needs identity + naming
7  STEP 3 · DIGITAL CUTTING TABLE — choose sizes → SMART IMPORT
   (Required/Imported/Remaining from Blueprint counts; optional
   opt-in; per-size colors) → arrange/rotate/mirror/lock →
   AI Optimize → Save                                            🟡 table
   complete; smart import + size colors NOT IMPLEMENTED
8  APPROVE → LAYOUT LIBRARY (uid, versions, stale law)           ✅
9  ADDA chooses contract (per fabric group, history forever)     ✅
10 LAYERING — suggested fabric length from the layout
   (length × plies)                                              ❌ edge absent
11 CUTTING — marker-fed suggestion + advisory reconciliation     ✅ (8C)
12 Enforcement gates (flags, default OFF)                        ⏸ designed (8D)
13 Bundles → Barcodes → Inventory                                ✅ (ERP)
```

## Q7 — How imports should work (the smart-import contract)

Per selected size(s): auto-list MANDATORY pieces with
`Required = Blueprint pieces_count · Imported = live session count ·
Remaining` — the Blueprint's count finally gets its DCT consumer.
Optional pieces = explicit opt-in list. Over-import beyond Required =
REFUSED with the honest count (prevents the three-pockets mistake;
deliberate imports of extra copies belong to a future cut-plan/ratio
input — the known registered gap, not smuggled in here). LAW 12 group
lock unchanged. Per-size COLOR assigned at import (stable palette:
S/M/L/XL…), painted on canvas pieces + palette badges + a legend in
the workspace meta.

## Q8 — UI posture (an amendment to the mobile-first standing rule — owner sign-off needed)

- **Pattern Studio + DCT = LAPTOP-FIRST** (the owner's own words for
  capture; the DCT is a CAD surface). Dense layouts, keyboard,
  precision pointers; mobile stays FUNCTIONAL (view/verify) but is not
  the design target. This is a scoped carve-out from the 2026-06-11
  mobile-first rule — it needs the owner's explicit line.
- **Manufacturing consumption stays MOBILE-FRIENDLY** (already built
  that way): dashboard, Manager verdicts, choose page, stage panels,
  library rows, warnings.

## Q9 — Reuse unchanged (the do-not-touch list)

Geometry models + the single writer + contract stamp · version chains ·
canonical validators (both runtimes) · calibration-mat metrology · the
compute bridge + runtime (EXTEND with new input ladders; never fork) ·
DXF io · svg_render · the facade (additive-only, as always) · DCT
physics/camera/engine-frame/AI endpoint · ApprovedLayout + Usage + F1–F3
+ the count hierarchy + the manufacturing timeline rule · Blueprint
module · Universal size machinery · Dashboard shell · choose page +
provider inversion · exports · ERP chain. **The spine survives this
rethink completely intact — that is the meaning of Q1.**

## Q10 — Reorganize for humans: MODULES, not phases

40 phase reports are history, not a map. Propose ONE living map,
organized the way the company thinks:

| Module | = today's | State |
|---|---|---|
| M1 Blueprint | Phase-2 module | DONE |
| M2 Pattern Studio | capture wizard + extraction + editor + DXF import, UNIFIED + multi-input + large-piece answer | THE next build |
| M3 Pattern Library | Manager/Preparing pages + facade, renamed + consolidated | mostly done |
| M4 Digital Cutting Table | the table + smart import + size colors | table done; import UX next |
| M5 Layout Library | Phase 7 | DONE |
| M6 Manufacturing Link | 8A–8C (+ 8D gates when resumed) | advisory done |
| M7 Knowledge & Analytics | frozen advisor/yield/insights, revived LATER against library data | FROZEN |

Docs move the same way: MODULE_MAP.md as the living index; phase
reports remain as receipts.

---

## The decisions I need from the owner (nothing proceeds without them)

1. **Pattern Studio module** — approve as the next build (the front
   door: evidence inbox, input ladders, large-piece answer).
2. **Large-piece capture direction** (inside the Studio): bigger
   commissioned mats vs multi-shot stitching vs lean-on-DXF/pro-
   digitizer imports — pick the investment.
3. **Naming**: "Pattern Library" = the shelf; DCT panel → "Verified
   Pieces" (amends frozen P4 amendment 1 — your call).
4. **Legacy generator flow**: retire the DCT link + fold the ★
   designation story into the library (or keep both, explicitly).
5. **Smart import**: approve the Required/Imported/Remaining contract +
   refuse-over-required + per-size colors.
6. **Laptop-first carve-out** for Studio + DCT (amends the mobile-first
   standing rule, scoped).
7. **Layering edge**: approve "suggested fabric length from the
   approved layout" as part of M6.
8. **8D fate**: resume as designed after the above, or fold its gates
   into M6's completion — either is clean; it stays approved-but-paused
   until you say.

**STOPPED — realignment review delivered. No code, no phases started.
When you rule on the eight decisions, we lock the module map and only
then continue implementation.**
