---
id: docs-ai-pattern-intelligence-ui-workflow-freeze
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# UI & WORKFLOW FREEZE — the Pattern Intelligence Platform
(2026-07-10 · NO CODE · companion to PRODUCT_DESIGN_FREEZE.md — this
document freezes every screen, panel, button, action, flow and dialog.
Closes advisor gaps 1–10 explicitly. After owner sign-off: architecture
+ UX are BOTH frozen; implementation resumes.)

## §0 · THE BUSINESS GOAL (gap 9 — now explicit, verbatim law)

> **"The objective of the platform is to permanently digitize the
> company's pattern knowledge so future garments can always be
> manufactured with predictable fabric consumption, repeatable
> layouts, and minimal wastage."**

Every screen below exists to serve this sentence.

**Rename (advisor adopted): "Pattern Studio" → "PATTERN INTELLIGENCE
STUDIO"** (short: the Studio) — acquisition + verification + geometry
management + knowledge + AI assistance + versioning + quality. More
than a drawing tool, and the name now says so.

**The hierarchy law (gap 4 — stated, and reflected in every nav):**
```
PRODUCT  →  SIZE (or Universal)  →  PIECE  →  GEOMETRY
```
The user always descends this way. No screen ever presents
piece-then-size. Studio navigation, Library browsing, Import Queue,
checklists — all size-first within the locked product.

---

## §1 · NAVIGATION — the 5-station rail (gap 1 resolved)

**The Library is NOT a separate station. It is the Studio's BROWSE
MODE.** One room, two modes:

```
DASHBOARD (product locked)
 ├─ 1 BLUEPRINT                     "what pieces exist + their rules?"
 ├─ 2 PATTERN INTELLIGENCE STUDIO   two modes, one room:
 │      BROWSE (default) = the Pattern Library shelf
 │      WORK             = capture · review · verify one piece×size
 ├─ 3 DIGITAL CUTTING TABLE         "compose the marker"     [desktop]
 ├─ 4 LAYOUT LIBRARY                "our manufacturing assets"
 └─ 5 MANUFACTURING                 "what are the Addas cutting?"
```
Mode switch inside the Studio is instant (Browse row → [Open in
Studio] → Work mode for that piece×size; Work → [← Shelf] returns).
Rail headers everywhere: ← prev · next →. Entry points unchanged.

---

## §2 · SCREEN-BY-SCREEN FREEZE

### 2.1 DASHBOARD (the rail)
- Product header (name · code · sizes summary).
- 5 station cards in journey order; each card: one-line question, live
  verdict (Blueprint: n pieces · Studio: sizes ready x/y · DCT: gate ·
  Layouts: n active · Manufacturing: n active contracts), one primary
  button.
- Mobile: stacked cards (exists today; content updates only).

### 2.2 BLUEPRINT (exists — additive only)
- Piece rows: name · REQUIRED/OPTIONAL chip · metadata chips (§3) ·
  rule editors (fabric group, grain, pair, fold, count) · Remove
  (refuse-if-history).
- ADDS with adr-c.2 milestone: notch-count expectation (optional int) +
  declared seam-allowance mm (piece-level metadata slots, §3).
- Atomic “+ Add Pattern Definition”. Unchanged otherwise.

### 2.3 STUDIO — BROWSE MODE (the Pattern Library shelf; gap 1/5)
Layout: product header → **SIZE TABS** (hierarchy law) → per-size:
- **THE CREATION CHECKLIST (gap 5 — new surface, existing truth):** a
  chip row directly under the size tab:
  `✓ Front  ✓ Back  ✓ Sleeve L  ✓ Sleeve R  ✖ Pocket  ○ Label(opt)`
  — mandatory pieces as ✓/✖, optionals as ○/✓. All-mandatory-green =
  “Size READY FOR CUTTING ✓” banner (the SAME readiness law that gates
  the DCT — one truth, now visible where work happens). A size with ✖
  cannot be “complete”; the DCT gate already enforces it.
- **Shelf rows** (one per piece): preview (tap-zoom) · reference thumb ·
  name + metadata chips · version `v3 · Confirmed ✓` + draft chip ·
  dims + trust label · area · grain/fold/pair/group · notch/seam (when
  adr-c.2) · updated · buttons: **[Open in Studio]** (→ Work mode) ·
  [History] (version sheet) · [DXF] [SVG] (derived downloads).
- Bucket order: ✖ Missing → ⚠ Needs work → ✓ Complete (todo-first,
  exists).
- Conveyor entry: **[▶ Digitize next missing piece]** button on the
  size header (gap-driven marathon, §2.4).
- Mobile: browse/view-only (chips, previews, history); [Open in
  Studio] hidden on phones except the CAPTURE hand-off (§2.5).

### 2.4 STUDIO — WORK MODE (one piece × size; the Pattern Room)
Desktop three-pane (per Design Freeze §5):
```
LEFT · EVIDENCE STACK (gap 2)      CENTER · PROPOSAL CANVAS      RIGHT · INSPECTOR
─────────────────────────         ────────────────────────      ─────────────────
[+ Add evidence ▾]                 overlay of the SELECTED        piece metadata (§3)
  Photo (phone hand-off §2.5)      proposal(s):                   dims + tape fields
  DXF file                          · outline render               grain angle dial
  SVG file                          · vertex handles (refine)      notch list (c.2)
  PDF / PNG                         · mm grid + rulers             confidence panel
  Manual dimensions                 · reference ghost underlay     (§4, display-only)
  AI service (Gemini…)             [Compare mode]: 2+ proposals    provenance chain
  Existing version (copy-fwd)      overlaid, color-coded, deltas   audit trail
EVIDENCE LIST (the stack):         listed (§4)
  each item: type icon · name ·
  status (raw / proposed /
  refused+reason / accepted) ·
  confidence badge · [Run] [View]
```
**Buttons/actions (frozen):**
- `[Run adapter]` per evidence → creates a PROPOSAL (append-only,
  provenance, refusal honest).
- `[Compare]` — select 2+ proposals → overlay + delta table (§4).
- `[Use this proposal]` — the one-shot ACCEPT (the existing review law)
  → becomes the working draft outline.
- Refine on canvas: drag vertices · add/remove vertex · set grain angle
  · mark notches (c.2) — the existing editor, re-skinned here.
- `[Verify & Publish…]` → the tape dialog: width/height tape fields →
  ±2 mm gate → CONFIRM (→ trust `measured`) → published to the shelf →
  **conveyor advances**: “Next: Pocket · S →” (gap from §2.3).
- `[Reject proposal]` (reason required) · `[Back to shelf]`.
Explicitly absent from Work mode: layouts, nesting, Addas, exports.

### 2.5 PHONE CAPTURE FLOW (gap 7 — its own chapter)
The ONE mobile-native piece of the Studio (capture is where phones
belong; review/verify stay desktop):
```
Desktop Work mode → [+ Add evidence → Photo]
  → QR code + short link on screen ("open on your phone")
PHONE:
  1 · guided frame: "lay the piece FLAT on the commissioned mat —
      whole piece + mat border in frame" (live viewfinder overlay:
      mat-edge guide box + tilt bubble)
  2 · quality hints AFTER shot (blur? glare? piece off mat?) —
      retake or keep (honest, local heuristics)
  3 · upload → "evidence received ✓ — continue on the desktop"
DESKTOP: the evidence appears in the stack (live) → [Run] → proposal.
```
V1 scope: guided overlay + upload + desktop continuation (the wizard
exists; this freeze re-skins it around the hand-off). Live mat
detection in the viewfinder = FUTURE (marked). Multi-shot large-piece
capture = the open owner decision — its UI slot is reserved in this
flow (shot 1/2/3 stepper) whichever direction is picked.

### 2.6 DIGITAL CUTTING TABLE (exists + the frozen additions)
**Opening dialog — MARKER PLAN (every session):**
`Fabric group ▾ (LAW 12) · Width (profile default, editable) · size
checklist ☑S ☑M ☑L with garments-per-size steppers (default 1) →
[Start composing]`. The plan drives the queue AND fills the layout's
ratio at save.
**Left panel = IMPORT QUEUE (renamed; gap: was “Pattern Library”):**
grouped size-first (hierarchy law): per size, per mandatory piece:
`Front — required 1 · imported 1 · remaining 0  [Import] [—]` ·
size-total progress `S: 6/8` · `[Import all remaining]` per size ·
OPTIONAL list separate (opt-in) · over-import refused with the count.
**Canvas:** pieces tinted by SIZE (S blue · M green · L orange · XL
purple · fixed cycle; legend chip row in workspace meta), labels
`S · Front`. All existing physics/AI/save/approve unchanged.
**Interaction map (gap 8 — frozen):**
| Action | Mouse/touch | Keyboard |
|---|---|---|
| select | click/tap piece | — |
| multi-select | FUTURE (marquee/shift) — marked | — |
| move | drag (pointer capture) | arrows 1 mm · Shift 10 mm |
| rotate (grain-gated) | selbar ⟳ | R |
| mirror (pair-gated) | selbar ⇋ | M |
| lock/unlock | selbar 🔒 | L |
| delete | selbar ✕ | Del |
| undo (session, ≤60) | header ↶ | Ctrl+Z |
| zoom (camera only) | wheel-at-pointer · toolbar | 0 = reset |
| pan (camera only) | drag empty fabric | — |
| snap toggle (10 mm) | toolbar Grid | — |
| compact / auto place | header buttons | — |
| align/group | FUTURE — marked | — |
Touch: 44 px selbar buttons; drag works; pinch-zoom FUTURE-marked.
Undo scope law: session ops only; persisted work is never editable.

### 2.7 LAYOUT LIBRARY (station 4 — exists; grows)
Rows: uid · name · V · group · width · length/util · status · STALE ·
[View(ro)] [Duplicate] [PDF] [Print] [Archive]. When volume demands:
its own station page with search/filter by group/status/size-content
(reserved, not built now).

### 2.8 MANUFACTURING (station 5 — exists + one addition)
Choose page · stage contract panel (unchanged) ·
**LAYERING addition (frozen):** the layering workspace shows
`Recommended layer length: ⟨marker length⟩ mm — from ⟨LAY-uid⟩`
(provider-fed, advisory, operator edits freely) · cutting suggestion +
WARN (exists) · gates = flags OFF (folds into M6).

### 2.9 DIALOG INVENTORY (all of them)
Marker Plan (2.6) · Verify & Publish tape dialog (2.4) · Reject-reason ·
Void-usage reason (exists) · Approve review page (exists) · Archive
confirm (exists) · Remove-piece refuse (exists) · phone hand-off QR
(2.5) · compare-proposals overlay (2.4). Every dialog: one question,
explicit verb button, honest refusal text.

---

## §3 · THE PATTERN METADATA CATALOGUE (gap 6 — one section, one truth)

All of this belongs to the PATTERN (Blueprint/piece/geometry) — never
to the Layout:

| Metadata | Lives on | State |
|---|---|---|
| Fabric group | Blueprint piece rule | ✅ |
| Pair / mirror allowed | Blueprint (`is_pair`) | ✅ |
| Mandatory / optional | Blueprint (`is_optional`) | ✅ |
| Grain RULE (rotation allowed) | Blueprint (`grain_rule`) | ✅ |
| Grain ANGLE | geometry payload `features.grain` | ✅ |
| Fold | Blueprint (`on_fold`) | ✅ |
| Cut count per garment | Blueprint (`pieces_count`) | ✅ |
| Dims + trust + tape truth | geometry row | ✅ |
| Area | derived (shoelace) | ✅ |
| Reference image | piece (display-only) | ✅ |
| Version history + provenance | version chain + extraction custody | ✅ |
| Contract version | geometry row stamp | ✅ |
| **Notches** | geometry payload `features.notches` | ➕ adr-c.2 |
| **Seam allowance (declared mm + digitized-line statement)** | piece/geometry metadata | ➕ adr-c.2 |
| Piece display color | NOT pattern metadata — size-color is a LAYOUT-session visual (§2.6); pieces have no stored color | ✋ by design |

## §4 · EVIDENCE, COMPARISON & CONFIDENCE (gaps 2 + 3)

**The Evidence Stack:** every piece×size holds MANY evidence items
simultaneously (photo + DXF + Gemini + manual dims + a previous
version). Each runs its adapter independently → each yields its own
PROPOSAL with provenance + per-run metrics.

**The Confidence Panel (display-only — the philosophy holds):**
| Source | Base confidence | Per-run adjustments |
|---|---|---|
| Manual dimensions | 100% (human-stated) | — |
| DXF | 99% | scale-check, single-boundary check |
| SVG/PDF | 95% | conversion fidelity checks |
| Photo (mat CV) | ~90–95% | homography residuals · segmentation stability · gate checks (ALL of this already computed by the runtime) |
| External AI (Gemini…) | ~85–90% | API self-score + local validation |
Confidence NEVER auto-selects. It informs the expert's choice.

**Compare mode:** overlay 2+ proposals color-coded on the canvas +
a delta table (width Δ, height Δ, area Δ, vertex count, max local
deviation mm). The expert picks ONE as the working draft
(`[Use this proposal]`).

**“Merge” (honest scope):** v1 = COMPARE & CHOOSE (+ refine by hand
against the others as ghost underlays). Automatic geometric fusion of
multiple proposals = FUTURE, explicitly not promised now.

## §5 · THE PATTERN ASSISTANT (gap 10 — M7's real scope)

The future AI is an ASSISTANT across the whole platform, not an
extraction tool: suggest missing notches · suggest seam values ·
suggest grain from shape · “this photo is too blurred — retake” ·
“Pocket M is missing while all other sizes have it” · “this geometry
is 99% identical to Front-M v2 — duplicate?” · layout suggestions ·
marker recommendations (the frozen advisor revived). ALL of it obeys
the one law: proposals in, human approval only, writes nothing.

## §6 · RESOLVED / OPEN LEDGER

**Resolved by this freeze:** gap 1 (Library = Studio browse mode; rail
= 5 stations) · gap 2 (Evidence Stack + compare) · gap 3 (confidence
panel) · gap 4 (hierarchy law everywhere) · gap 5 (creation checklist
surface) · gap 6 (metadata catalogue) · gap 7 (phone capture chapter)
· gap 8 (interaction map) · gap 9 (the goal sentence) · gap 10
(Pattern Assistant scope) · rename → Pattern Intelligence Studio.

**Still open (owner):** large-piece capture direction (UI slot
reserved either way) · §18-d retirements confirm · adr-c.2 rides the
Studio build (assumed yes — say the word) · 8D gates fold into M6
(assumed yes) · build order M2→M4→M3-polish→M6→M5→M7 (M3 shrinks: the
shelf ships INSIDE M2 now).

**STOPPED — UI & Workflow Freeze delivered. No code. Architecture +
UX both frozen on your sign-off; implementation resumes at M2 (the
Studio) under the standard discipline.**
