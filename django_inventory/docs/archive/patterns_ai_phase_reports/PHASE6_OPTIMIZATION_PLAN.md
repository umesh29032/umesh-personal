> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PHASE 6 PLAN — the Layout Optimization Engine
(2026-07-09 · PLAN ONLY — no code until approval · owner order honored:
manual manufacturing workflow FIRST, AI LAST)

## Shape: three gated sub-milestones (smallest-milestone precedent)

Your engineering order 1–7 groups naturally into three deliverable,
individually-reviewable milestones — each one follows the full
discipline (plan is this doc; each sub-milestone stops for approval):

### 6A — PHYSICS (your steps 1–4) · session-only, still ZERO writes
1. **Collision detection** — client-side polygon intersection on the
   transformed outlines (the proven ROADMAP-era workspace already did
   client collision highlight — same approach, no geometry fork).
   Colliding pieces highlight red; count shown in status.
2. **Spacing rule** — minimum gap from the product's fabric profile
   (`default_spacing_mm`, already a stored default); enforced as
   collision-with-margin (outline dilated by gap/2 — honest
   approximation, labeled). Violations = same red channel.
3. **Grid snap** — toolbar **Grid** button goes LIVE (its phase has
   arrived): toggle 10 mm snap on drag.
4. **Utilization + Canvas Length** — the "--" slots come alive:
   length = max piece extent (mm, rounded up); utilization = Σ piece
   area (facade `area_cm2`, no recompute) ÷ (width × length). Display
   only — no persistence, no model.
   Status bar + Layout Information update live; Undo covers snap moves.

### 6B — MANUAL OPTIMIZATION (your step 5) · still ZERO writes
- **Compact ←** one-click: shelf-pack the CURRENT pieces left-down,
  respecting collision + spacing + each piece's grain rule (never
  rotates beyond its allowed set) and manual lock: pieces the operator
  has placed by hand stay put (lock toggle on selection bar — the
  locked/manual-first law from the frozen 4-state model).
- **Nudge** — arrow keys move selection by 1 mm (Shift = 10 mm).
- **Zoom** — toolbar Zoom goes live (wheel + buttons; viewBox camera,
  same mechanism as the proven workspace). Composing on 1700 mm fabric
  without zoom is a real operator pain — UX fix inside the frozen
  layout, no structural change.

### 6C — AUTO PLACEMENT + AI (your steps 6–7, AI LAST)
- **Auto Place** — deterministic BLF floor (EXISTING engine, reused via
  the compute bridge) over the imported pieces honoring grain/spacing/
  width; manual/locked pieces = obstacles.
- **AI Optimize** — toolbar button goes LIVE: the EXISTING
  `op:'optimize'` engine (obstacles · seeded · ranking rules), reused
  verbatim through a **stateless compute endpoint**
  (`table/<pk>/optimize/`, POST in → placements out, ZERO DB writes —
  the exact pattern the ROADMAP-era optimize already proved). Results
  land in the session as movable pieces; Worse-than-current honesty
  badge reused. Synchronous with the existing timebox + honest timeout
  message; a job queue only if real usage demands it (no
  over-engineering now).

## Constants across all of Phase 6
Zero persistence (save/approve = Phase 7) · zero models · frozen layout
untouched (buttons only go LIVE as their phase arrives — Grid/Zoom/AI
Optimize; Import/Select/Rotate/Mirror stay as-is) · facade untouched ·
single writer untouched · money untouched · LAW 12 + grain + pair rules
keep governing everything the engine does.

## Tests + proof per sub-milestone
6A: collision math unit-tested in JS-mirroring Python? NO — collision
lives client-side; server tests pin the payload additions (spacing
default, area per row) + chrome; browser proof = scripted overlap →
red highlight + count, snap-drag coordinates, live utilization math
checked against hand-computed value.
6B: compact respects grain/lock (scripted); nudge; zoom.
6C: endpoint = stateless (DB row-count identical before/after, tested
server-side) · engine reuse (no new engine code) · browser: AI result
lands movable + honesty badge.
Battery + screenshots + report each sub-milestone; STOP each time.

---
**STOP — Phase-6 plan delivered. Awaiting your approval of the
6A → 6B → 6C split (or adjust), then 6A implementation begins.**
