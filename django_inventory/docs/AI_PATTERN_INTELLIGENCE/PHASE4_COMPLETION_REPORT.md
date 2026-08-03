---
id: docs-ai-pattern-intelligence-phase4-completion-report
type: receipt
status: active
owner: append-only
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# PHASE 4 COMPLETION REPORT — Interactive Marker Workspace (2026-07-07)

**ROADMAP_V2 Phase 4. Status: ✅ COMPLETE + frozen. STOPPED — awaiting
owner approval before any further work.**

## Scope compliance — the 18 ordered items, nothing else

| Item | Delivered as |
|---|---|
| Infinite canvas | SVG viewBox camera — pan anywhere, world unbounded |
| Zoom | wheel + ＋/－/Fit buttons (cursor-anchored) |
| Pan | background drag (grab cursor) |
| Grid | 10/50 mm `<pattern>`, toggleable |
| Guides | +V/+H draggable guide lines |
| Fabric width control | live input → boundary + metrics recompute |
| Fabric height control | live input (NEW dimension — generation was width-only) |
| Marker boundary visualization | white fabric rect (height × width) on the grid |
| Drag pieces | pointer-drag (the P2 editor technique) |
| Rotate pieces | **180° toggle only — the standing grain rule enforced; 90° stays impossible** |
| Lock/Unlock | per piece (button/L key); locked = undraggable, dashed style; flag persists into the saved layout |
| Snap | bbox corner → grid step; guides win within 8 mm |
| Collision highlighting | client bbox-prefilter + segment-intersection/containment → red pieces + live count |
| Live utilization % | Σ piece areas ÷ (length × width), on every drop |
| Live wastage % | 100 − utilization |
| Live marker length | max-x of real outlines + fits-height flag |
| Save current layout | POST → `save_manual_layout` (single writer) → **NEW immutable run+candidate, `engine='manual'`** — verified server-side by THE generation verifier (nest.py gained a verify-only op) before anything persists; overlap/oversize/piece-set-mismatch REFUSED with numbers |
| Reload saved layout | workspace opens ANY candidate; save redirects into the saved one |

**Zero new models, zero migrations** (pin stays 15). Client numbers are
display-only — the server verifier is authoritative (the page says so).

## Live browser proof (screenshots archived, `ph4_*`)
Candidate #2 opened: 4 pieces, live 101.0 mm / 65.68% — **exactly the
server's stored numbers** (client math agrees with the verifier).
Dragged a piece onto its neighbour → 1 collision, 2 red pieces →
dragged clear → 0. Rotated 180°, locked it (dashed style), height
control 800 → "fits fabric", live 219.5 mm / 30.22%. Saved → **"candidate
#3 (manual, verified 219.5 mm)"** — server verifier agreed with the
client estimate to the decimal. Reload: 4 pieces, lock intact, 219.5.
Candidate #3 renders on the standard candidate page with its own
visualization + "Open in workspace". Mobile @390: toolbar wraps, canvas
full-width, touch pointer events native.

## Test summary — patterns_ai **188/188** (+12 Phase 4)
Verify op: agrees with generation's stored length; crafted overlap
refused. Service: happy save (manual run params carry source id, height,
ratio; locked flag inside the immutable payload; derived metrics work;
immutability inherited) · overlap refused with numbers, nothing persisted ·
height-exceeded refused · width-escape refused · piece add/remove refused ·
width/height bounds · worker blocked. Views: 403/302/404 sweep · canvas +
all controls render · save→reload round-trip with lock · bad payload and
refused save leave zero rows. Full serial suite fresh-run green.

## Engineering review (hostile pass)
- One verification home preserved: the workspace save runs the SAME
  shapely verifier as generation (new op = 8 lines around it).
- Save path is the only write; it lands in the existing single-writer
  and inherits every guard. Client cannot author trusted numbers.
- Collision JS is advisory UX; the verifier decides. Concave rings
  handled (segment intersection + containment); grid snap uses bbox
  min-corner (predictable).
- Rotation constraint enforced structurally (only a 180° toggle exists).
- Debt (small, honest): no undo (reload the source candidate = the
  recovery path, stated); no multi-select drag; canvas keyboard nudge
  absent — none ordered, none built. Template JS ≈ 300 lines page-scoped
  vanilla — no framework, no build step.
- Boundary walls unchanged; ADR-F untouched (verify op lives in the
  runtime).

## Regression (fresh)
patterns_ai 188/188 · full manufacturing suite **1073/1073 OK** (serial,
fresh, 220 s) · `makemigrations --check` clean · import contracts
unchanged · prior-era pages spot-checked (candidate detail gained one
button).

## Freeze
Phase 4 = FROZEN as delivered: the workspace contract (open any
candidate → adjust → server-verified immutable manual save → reload),
the verify op, the save service rules, the grain-rule rotation limit.
Additive evolution only.

**STOPPED. No further work until the owner approves.**
