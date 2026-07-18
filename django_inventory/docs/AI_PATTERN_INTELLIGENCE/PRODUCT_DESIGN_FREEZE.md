---
id: docs-ai-pattern-intelligence-product-design-freeze
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# PRODUCT DESIGN FREEZE — the Pattern Intelligence Platform
(2026-07-10 · NO CODE · the definitive design document, built from the
code-level audit + the owner's business vision · honesty rule applied:
"would I design it this way from scratch today?" — every NO is in §18)

**What this is:** the DIGITAL BRAIN of a garment factory. Not CAD, not
an image editor, not a DXF viewer. The company's pattern knowledge —
captured once, verified by a human, owned forever, consumed daily.
Pattern creation is RARE (the Digital Pattern Room). Layout creation is
DAILY (the planning floor). Manufacturing consumes assets. Never mixed.

---

## 1 · OVERALL PLATFORM ARCHITECTURE

```
┌────────────────────────── THE TRUTH LAYER ──────────────────────────┐
│ Verified Geometry (int-µm polygons · versions · contract stamp)     │
│ Approved Layouts (uid · versions · immutable)                       │
│ Layout Usage (the manufacturing timeline — history forever)         │
│ ONE single-writer service per store · append-only · human-gated     │
└──────────────────────────────────────────────────────────────────────┘
        ▲ proposals only                          │ derive-at-read only
┌───────┴──────────────┐              ┌───────────▼──────────────────┐
│ ACQUISITION LAYER    │              │ INTELLIGENCE (read-only)      │
│ Evidence → Adapter → │              │ readiness · metrics · marker  │
│ Proposal → HUMAN     │              │ content · staleness · nest    │
│ REVIEW → Truth       │              │ search · (P8 assistant later) │
└──────────────────────┘              └───────────────────────────────┘
        ▲                                             │
┌───────┴─────────────────────────────────────────────▼───────────────┐
│ SURFACES: Blueprint · Pattern Studio · Pattern Library ·             │
│ Digital Cutting Table · Layout Library · Manufacturing Bridge        │
└──────────────────────────────────────────────────────────────────────┘
Walls: production never imports patterns_ai (ADR-H; crossings = URL
hand-offs + data-only provider registries). Money untouched. ERP =
Heart 1, consumes Heart 2's assets only.
```

**The Acquisition Layer is hereby FIRST-CLASS** (owner question
answered): not a UI inbox but a named architecture layer with one
contract — `Evidence (any source) → Adapter (per type) → Proposal
(append-only, provenance, refusal reasons) → Human Review (one-shot) →
Verified Geometry (the single writer)`. It already exists in embryo
(CaptureAsset → extract adapter → GeometryExtraction → review →
confirm; dxf_io = the second adapter). Every future input — SVG, PDF,
PNG, manual dimensions, Gemini, any API — is a NEW ADAPTER on the SAME
contract. The Studio (§8) is the ROOM; Acquisition is the MACHINERY.

## 2 · FINAL MODULE MAP

| # | Module | Role | State |
|---|---|---|---|
| M1 | Blueprint | structure + rules + counts (the DNA) | ✅ DONE |
| M2 | **Pattern Studio** (+ Acquisition Layer) | the Digital Pattern Room — evidence → verified geometry | 🚧 THE build |
| M3 | **Pattern Library** | the knowledge shelf per Product×Size×Piece | 🔧 consolidate + name |
| M4 | **Digital Cutting Table** | daily planning: Marker Plan → Import Queue → arrange → AI → save | 🔧 queue + colors |
| M5 | Layout Library | the manufacturing-asset store | ✅ DONE |
| M6 | Manufacturing Bridge | choose · display · advisory numbers · layering length · gates | 🔧 finish (layering edge + paused gates) |
| M7 | Intelligence & Assistant | frozen analytics revived on library data (P8) | 🔮 FUTURE |

## 3 · COMPLETE NAVIGATION MAP — one continuous journey

The Dashboard becomes the **6-station rail** (the owner's flow,
verbatim):

```
DASHBOARD (product context locked)
 ├─ 1 BLUEPRINT          "what pieces exist?"
 ├─ 2 PATTERN STUDIO     "digitize + verify"        [desktop]
 ├─ 3 PATTERN LIBRARY    "what do we own?"
 ├─ 4 CUTTING TABLE      "compose the marker"       [desktop]
 ├─ 5 LAYOUT LIBRARY     "our manufacturing assets"
 └─ 6 MANUFACTURING      "what are the Addas cutting?"
Every station header: ← prev station · next station → (the journey
never dead-ends). Entry points unchanged: production Patterns action →
Dashboard; Adda detail → station 6 / choose page.
```

## 4 · SCREEN INVENTORY (existing → target)

| Station | Screen | Today | Freeze verdict |
|---|---|---|---|
| Home | Pattern Dashboard | 3-step page | REWORK → 6-station rail |
| 1 | Blueprint module | ✅ | keep (add notch/seam rule slots with §18-g) |
| 2 | **Studio shell + Evidence Inbox** | — | NEW |
| 2 | Capture wizard (mat photo) | ✅ scattered | RE-HOME into Studio |
| 2 | Extraction review (proposal accept) | ✅ scattered | RE-HOME (THE review screen for every adapter) |
| 2 | Geometry editor (vertex/grain refine) | ✅ scattered | RE-HOME + reskin |
| 2 | DXF import | ✅ scattered | RE-HOME as an Inbox adapter |
| 2 | SVG/PDF/manual-dims/AI-API adapters | — | NEW (same contract) |
| 2 | Verify & Publish (tape confirm) | ✅ (version detail) | RE-HOME, promoted |
| 3 | Library shelf (per size) | ✅ "Preparing Size X" | RENAME + consolidate (this IS the library) |
| 3 | Sizes verdict page | ✅ Manager | keep as the shelf's index |
| 3 | Piece/version detail | ✅ engineer-grade | reskin inside Library |
| 4 | DCT workspace | ✅ | keep; + Marker Plan opener + Import Queue panel + size colors |
| 4 | Approve review | ✅ | keep |
| 5 | Layout Library section | ✅ | keep; grows into its own station page (list/search/filter when volume demands) |
| 6 | Choose page (Adda contracts) | ✅ | keep |
| 6 | Stage panels (pattern/cutting) | ✅ | keep; + layering suggestion |
| — | Legacy generate tool + ★ designation + Marker research pages | ✅ frozen-era | RETIRE from navigation (recommend; owner confirm) |

## 5 · DESKTOP UX PHILOSOPHY (Studio + DCT — precision workspaces)

Canvas is the hero; everything else serves it. Three-pane grammar:
**context rail (left) · work canvas (center) · inspector (right)**.
Keyboard-first (every canvas action has a key), pointer-precise, dense
information without decoration. No mid-task page reloads. World
coordinates are sacred: fabric width visually stable forever; zoom
moves the CAMERA (already law). The operator always sees: width ·
consumed length · waste · where every piece belongs (the four questions
of §"DCT UI"). Honest states everywhere: disabled controls say why;
refusals name the fix.

## 6 · MOBILE UX PHILOSOPHY (consumption surfaces)

Management, approvals, reference, manufacturing: verdict cards,
one-question pages, 44px targets, summary-first — exactly the built
house style. Geometry/layout previews VIEW-ONLY on phones. CAD
workflows are never forced onto phones (owner law — this RESOLVES the
laptop-first carve-out: scoped amendment to the 2026-06-11 mobile-first
rule for stations 2 and 4 only).

## 7 · PATTERN ACQUISITION WORKFLOW (the layer)

```
EVIDENCE (photo · DXF · SVG · PDF · PNG · manual dims · AI APIs ·
          existing version)          — all optional, all just evidence
  → ADAPTER (per type):
      DXF  → validate only (AI does ~nothing)
      SVG/PDF/PNG → convert → verify
      photo → rectify → segment → contour → polygon (existing CV)
      manual dims → construct/scale
      Gemini/API → external proposal (backend-ladder rules)
  → PROPOSAL (append-only · provenance · confidence DISPLAY-ONLY ·
              refusals recorded · never auto-accepts)
  → HUMAN REVIEW (one-shot accept/reject — the same screen for all)
  → refine (editor) → VERIFY (tape gate) → PUBLISH (single writer)
```
Ladder honesty rules (from the SAM precedent): an unavailable adapter
reports itself unavailable; API failure = a recorded refusal; nothing
silently falls back. Large-piece capture = an ADAPTER problem
(bigger mats / multi-shot stitching / external AI) — the owner picks
the investment; the contract doesn't change either way.

## 8 · PATTERN STUDIO WORKFLOW (the Digital Pattern Room)

`Product → Size → Piece` (or the CONVEYOR: "next missing piece" — the
one-time digitization marathon runs piece after piece without
navigation). Per piece×size: Inbox → run adapter → review proposal →
refine → tape-verify → publish → next. Output: Verified Geometry.
Explicitly NOT in the Studio: manufacturing, Addas, layouts, nesting.
Users: owner/pattern expert (management-gated, as today).

## 9 · PATTERN LIBRARY WORKFLOW (the shelf)

Browse product → size → the shelf rows: preview · dims (+trust) ·
area · grain/fold/pair/group · reference · version + full history ·
SVG/DXF (derived on demand — deliberately never stored; one truth, no
stale copies) · notches/seam metadata (once §18-g lands) · staleness
visibility. Supersede = "reopen in Studio" (copy-forward). The Library
answers "what does the company own?" — it never edits.

## 10 · DIGITAL CUTTING TABLE WORKFLOW (daily)

```
Open (ready-gated) →
MARKER PLAN (the session opener — NEW):
   ☑ sizes + garments-per-size (default 1)      ← this IS the missing
   fabric group (LAW 12) · width (profile)         ratio/cut-plan input,
                                                    landed where it belongs
→ IMPORT QUEUE (auto-built from Blueprint × plan):
   "Front S — required 1 · imported 0"  [Import] [Import all remaining]
   per-size COLORS (S blue · M green · L orange · XL purple · fixed
   cycle) · optional pieces = separate opt-in list · over-import
   REFUSED with the honest count (no third pocket, ever)
→ ARRANGE (physics: boundary/collision/spacing · grain-gated rotate ·
   pair-gated mirror · lock · compact · auto-place)
→ AI OPTIMIZE (proposal; honest better/same/worse)
→ SAVE DRAFT (verify-then-persist, verbatim)
→ APPROVE (human review page) → Layout Library
```
Canvas piece labels become `S · Front` (size-colored). The operator
imports MANUFACTURING KNOWLEDGE, not shapes.

## 11 · LAYOUT LIFECYCLE

`Session Draft → Saved Draft (immutable candidate) → APPROVED
(uid LAY-…-NNNNNN · V<n>) → Active / Superseded / Archived · STALE
derived, never stored (Law 11) → chosen as an Adda's contract (usage:
one per fabric group, history forever, void-with-reason only)`.
Many layouts per product is the PERMANENT assumption — seasonal,
fabric-specific, size-combination, export-order layouts all coexist;
nothing anywhere assumes one. The generator-era ★ single-designation
retires (recommendation, §18-d).

## 12 · MANUFACTURING INTEGRATION

Adda chooses per fabric group (stale/inactive refused) → stage panel
shows the contract → **LAYERING: "Recommended layer length: ⟨marker
length⟩ mm" from the approved layout (operator may change)** — the
missing edge, now frozen into the design → CUTTING: marker-content ×
lay_count advisory suggestion + reconciliation WARN ("your numbers
stand") → gates (REQUIRE_APPROVED_LAYOUT · ENFORCE_LAYOUT_
RECONCILIATION, flags default OFF) → Breakdown = manufacturing FACT →
barcodes → inventory. The count hierarchy stays law: content (layout) ·
plies (layering) · expected (derived, advisory).

## 13 · AI INTEGRATION PHILOSOPHY

**AI never creates truth. AI creates proposals. Humans approve truth.**
Everywhere: geometry (extraction proposals, one-shot review), layouts
(optimize = better/same/worse, never auto-apply-worse, never approve),
verification (confidence display-only, never a gate). Adapters/backends
follow the ladder rules (§7). In the Studio AI serves the EXPERT
(accuracy); in the DCT it serves the OPERATOR (speed); in P8 the
assistant READS the library and recommends — it writes nothing.

## 14 · DESIGN SYSTEM PHILOSOPHY

Keep the house system (ink/copper/cream, Cormorant headers, card
tokens) — it already reads "craft workshop", which IS the brand. Add
the WORKSPACE SKIN for stations 2/4: denser rhythm, monospace for uids
and mm, and a FROZEN semantic color law: green = confirmed/clear ·
amber = attention/spacing · red = violation/refusal · violet =
boundary · grey = locked/archived · the size palette (§10) reserved for
size identity only. One component vocabulary everywhere: verdict card ·
design-row atom · queue row · contract row · library row · honest-hint.

## 15 · INTERACTION PHILOSOPHY

Direct manipulation + keyboard on desktop; one-tap honest actions on
mobile. Every mutation is explicit (no hidden work — Rule I lives on).
Every refusal names the fix ("void that usage first"). Session work is
always undoable; persisted work is never editable — only superseded
(the immutability religion). Warnings explain, never modify (operator
authority). Progressive disclosure: each screen answers ONE question;
detail lives one tap deeper, never crowding the verdict.

## 16 · SCREEN HIERARCHY

`Dashboard (rail) → Station (index/verdicts) → Work surface
(Studio room / DCT canvas / shelf) → Detail sheet (version history,
review, approve)` — maximum depth 3 from the rail. Cross-links only
along the journey (prev/next) and to evidence (SVG/PDF/DXF views).

## 17 · FUTURE EXTENSIBILITY

Built-in extension points, all proven this build: new evidence
ADAPTERS (the acquisition contract) · new extraction BACKENDS (the
ladder + honest-unavailable) · new Dashboard MODULES (the frozen rule)
· payload extensions via `geometry_contract_version` bumps · new
manufacturing consumers via provider registries (never imports) · P8
intelligence over library data. Commercial-platform note: uid scheme,
metrology loop, provenance chains and contract stamps are already
license-grade; multi-tenancy is the known future step, not designed
now.

## 18 · WHAT I WOULD REDESIGN TODAY (the brutally honest list)

**a. The scattered Studio.** Five digitization pages hung off
preparation flows — I would NEVER build it that way today. (Genesis:
capture came in P2-era before the platform existed.) → M2 fixes it.
**b. The Dashboard.** 3 steps was right for its moment; the real
product is a 6-station journey. Rebuild the rail.
**c. The name "Pattern Library".** Giving the DCT panel that name was
a mistake visible only once the vision matured. Panel → **"Import
Queue"** (truer than "Verified Pieces" — it's a work queue now);
"Pattern Library" = station 3, alone.
**d. The pre-platform trio.** Generate tool, ★ ProductionLayout,
the Marker/chalk-photo research library — the platform GREW out of
them; a fresh build wouldn't contain them. Retire from navigation,
fold ★'s job into the Layout Library, keep the data as history.
(Owner confirm.)
**e. Ratio as an afterthought.** `ratio: {}` with an honest comment was
correct discipline, but a fresh design puts MARKER PLAN (sizes ×
garments) at the DCT session start — it drives the Import Queue AND
fills the layout's ratio for manufacturing math. That is the design
now (§10).
**f. DCT JavaScript in the template.** ~700 inline lines was fine at
Phase 5; it is past the threshold. Move to a static file at the next
DCT milestone — organization, not architecture.
**g. Notches + seam allowance.** Should have been in the first
payload. They ride the Studio build as `features.notches` + declared
seam metadata with a CONSCIOUS `adr-c.2` contract bump — the stamp was
built for exactly this moment.
**h. Engineer-grade detail pages.** Version detail / extraction review
work but read like admin tools; the Studio reskin makes them the
expert's room.
**i. What I would build EXACTLY the same** (and this list is the
audit's verdict, not nostalgia): the truth model · single writers ·
append-only versions + contract stamps · the ADR-H wall + inversion
crossings · the canonical validator twins · the metrology loop · the
mm-world/camera split · the engine reuse + frame swap · the Layout
Library + usage timeline + freezes F1–F3 + the count hierarchy · the
honest-refusal culture in every service. The spine needs no apology.

---

## RESOLVED by this freeze (previously open)
- Desktop-first for Studio + DCT (owner's words) — the mobile-first
  rule gains its scoped carve-out.
- The 6-station journey = the navigation truth; "Pattern Library"
  names the shelf.
- The ratio gap = MARKER PLAN at DCT session start.
- The layering suggested-length edge = frozen into M6.

## STILL OPEN (owner rulings)
1. Large-piece capture investment (mats / multi-shot / external AI —
   stageable).
2. Confirm §18-d retirements (generate tool · ★ · Marker research
   pages out of navigation).
3. `adr-c.2` (notches/seam) rides the Studio build — confirm.
4. Paused 8D gates fold into M6 completion — confirm.
5. Build order confirm: **M2 Studio → M4 queue/plan/colors → M3
   library identity → M6 completion → M5 polish → M7 later.**

**STOPPED — the Product Design Freeze is delivered. No code. On your
rulings, this document becomes the platform's constitution and
implementation resumes under the standard discipline.**
