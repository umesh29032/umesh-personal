---
id: docs-ai-pattern-intelligence-phase5-optimize-design
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# Phase 5 DESIGN v4 (FINAL) — AI Layout Optimization (2026-07-07) · DESIGN ONLY

**Governed by PRODUCT_VISION_V2 + ROADMAP_V2 + Phase-5 product rules 1–10
(owner, 2026-07-07). The AI is NOT an assistant and NOT a recommendation
engine — it is a DETERMINISTIC layout optimization TOOL. The human is
always designing the marker; the AI only helps arrange pattern pieces.
No implementation yet — awaiting owner approval.**

## 0. The user experience (product language only)

Inside the **layout editor**:

1. Lock the pieces you want kept exactly where they are.
2. Optionally **select** the pieces you want optimized (rule 7).
3. Set the optimizer controls if you want (or keep the defaults).
4. Press **✨ Optimize** — the AI rearranges only the pieces in scope.
5. The **Layout options strip** appears: **Current Layout · Option 1 ·
   Option 2 …** — thumbnails + utilization/wastage/length with honest
   deltas against your current layout (rule 6).
6. One click previews any option; one click on **Current Layout**
   returns to your original exactly. **Keep this option** makes an
   option your working layout — never automatic (rule 6).
7. **Undo / Redo** cover every editing step, including Keep and Return
   (rule 8) — experiment fearlessly.
8. Lock/unlock, select, drag, optimize again — **unlimited rounds; this
   loop is the heart of the product** (rule 4).
9. **Save layout** stays the ONE explicit act that stores anything.

User words: layout, option, optimize, select, lock, keep, undo, redo,
save, utilization, wastage, length, spacing, mode. No internal
vocabulary anywhere (wording pass on existing toasts ships with the
phase).

## 1. 🔒 Rule 9 — THE OPTIMIZATION PHILOSOPHY (permanent objective order)

Every optimization run, every engine, every future improvement obeys
this priority order. 1–4 are HARD CONSTRAINTS (an option violating any
of them is discarded before the user ever sees it — enforced by the
independent verification of every option); 5–8 are the objectives, in
order:

1. **Never create overlapping pieces.**
2. **Respect the fabric width.**
3. **Respect the fabric height.**
4. **Respect locked and out-of-scope pieces exactly** (byte-identical
   outlines, test-asserted).
5. **Maximize fabric utilization.**
6. **Minimize marker length.** (With a fixed width, 5 and 6 move
   together; when they ever diverge — e.g. equal length, different
   in-cage packing — utilization ranks first.)
7. **Keep the layout practical:** when two options are otherwise
   equivalent, prefer the compact, readable one — the tie-break is a
   simple compactness heuristic (lower total piece-spread / fewer
   isolated islands), never a new objective that fights 5–6.
8. **Return several good layouts instead of chasing one "perfect"
   layout** — the strip exists so the HUMAN picks; distinct good options
   beat marginal extra search for a single optimum.

This order is displayed nowhere and negotiated never — it is how the
optimizer behaves, permanently.

## 2. 🔒 Rule 10 — THE IMPROVEMENT PHILOSOPHY (permanent)

The optimizer improves ONLY through better **search strategies,
heuristics, and nesting algorithms** — deterministic, seeded,
explainable. **No machine learning, LLMs, neural networks, embeddings,
recommendation systems, analytics, prediction engines, or any other AI
technologies — ever — unless the owner explicitly requests them in the
future.** The product remains a deterministic layout optimization tool.

## 3. Rule 1 — simple user controls (no black box)

| Control | UI | Default | Meaning |
|---|---|---|---|
| Layout options | number 1–8 | 3 | how many options come back (rule 9.8) |
| Mode | Fast / Balanced / Best | Balanced | search effort ≈ 3 s / 10 s / 30 s (the mode IS the time limit) |
| Piece spacing | mm input | current layout's spacing | gap kept between pieces |
| Rotation | fixed text "0° / 180° (grain rule)" | — | existing rules only, displayed not configurable |

Nothing else — no engine pickers, no advanced panels.

## 4. Rules 2 + 7 — incremental optimization with locks AND selection

**Scope law:** the optimizer moves `selected ∩ unlocked` when a
selection exists, otherwise ALL unlocked pieces; **everything out of
scope — locked or simply not selected — stays exactly where it is,
treated as a permanent obstacle (rule 9.4).**

- Lock wins over selection (all-locked selection → honest message).
- Multi-select: click / shift-click + "N selected" chip; out-of-scope
  unlocked pieces are immovable for the run, fully editable after.
- Obstacles pre-rasterized into the occupancy mask; scope pieces
  bottom-left-filled around them across K seeded orderings; lock 90% and
  select 2 → exactly those 2 move.
- Width/height respected (9.2/9.3); nothing fits → honest message.
  Mirror state kept; rotation 0/180° only.

**Engine job (isolated runtime, new `op:"optimize"` in nest.py):**
```
{ op:"optimize", width_mm, height_mm, spacing_mm, seed,
  options_wanted, effort,
  fixed: [ {polygon_mm} ... ],                   // locked + out-of-scope, IMMOVABLE
  free:  [ {key, instance, mirrored, polygon_mm(local), allow_180} ... ] }
→ { ok, options:[ {placements(fixed+free), length_mm, verification} ], errors }
```
Every option **independently verified** (the ONE existing verifier —
this is where hard constraints 9.1–9.4 are enforced), ranked by the 9.5–
9.7 order, de-duplicated, best `options_wanted` returned. Deterministic
per seed (rule 10). Nothing locked AND nothing selected → the full
generation engines join the pool; otherwise the obstacle-aware optimizer
(the vendored nesting core cannot seed pre-placed parts without
modifying vendored code — we do not touch vendored code; stated
trade-off).

## 5. Rules 3 + 6 — visual, honest, never destructive comparison

- **Current Layout = permanent baseline**: first card, always present,
  one click returns to it exactly.
- Option cards: utilization/wastage/length + **delta vs Current**
  ("−120 mm · +3.1% utilization").
- **Honest labels:** worse than Current (higher wastage OR longer) ⇒ red
  **"Worse than Current"**; better ⇒ "Saves 120 mm"; equal ⇒ "Same as
  Current". Never hidden, never pretended.
- Nothing ever auto-replaces the working layout — only the human's Keep;
  only Save stores.

## 6. Rule 8 — editing confidence: Undo / Redo

Session-level snapshot history (piece transforms + lock flags), ≥50
steps: **drag · rotate · lock/unlock · Keep option · Return to
Current** (selection changes don't alter the layout → not history).
Buttons + Ctrl-Z / Ctrl-Shift-Z (⌘ variants); redo clears on new action;
live numbers + collision highlights recompute on every step. Save = the
durability act, unchanged, itself not an undoable canvas op.

## 7. Rule 4 — unlimited optimize loop

No limits, no cooldowns: optimize → preview → keep-or-return →
undo/redo → edit → lock/select → optimize again, forever. **Previews are
transient — ZERO database rows until Save.** Save = unchanged Phase-4
machinery (single writer, server re-verification, immutable stored
layout, lock flags persisted); the stored payload records internally
that it came from an optimize round — invisible in the UI.

## 8. Rule 5 — focus (hard boundaries)

ONLY layout optimization. **NOT built:** analytics · learning systems ·
recommendation engines · background/async optimization · enterprise
features · automatic decision-making · auto-apply · preview persistence ·
scoring beyond utilization/wastage/length (+ the 9.7 tie-break) ·
vendored-code modification · anything on the rule-10 forbidden list.

## 9. Surface changes (small, all inside the existing flow)

| Piece | Change |
|---|---|
| nest.py | `op:"optimize"` — BLF-obstacle mode + K-seed loop + per-option verify + 9.5–9.7 ranking (reuses BLF internals + `verify_layout`) |
| marker_generation_service | `optimize_layout(...)` — compute-only (gate, controls validation, scope build, effort mapping, honest errors); **writes nothing** |
| WorkspaceView | `action=optimize` AJAX POST → JSON options with deltas |
| workspace template | settings row · multi-select + chip · ✨ Optimize · options strip (Current baseline, honest badges, Keep/Return) · Undo/Redo · wording pass |
| Everything else | untouched (canvas, collision UX, save path, exports) |

Zero new models. Zero migrations. Model pin stays 15.

## 10. Architecture review (why this is still the simple version)

One engine mode + one compute-only service function + one AJAX branch +
strip/undo UI in the existing page-scoped JS. No persistence for
previews or history, no queue, no websockets, no frameworks, nothing
from the rule-10 forbidden list. Human control structural: optimize
returns data; only Keep changes the canvas; only Save writes; the
philosophy (rule 9) is enforced where options are BORN (verifier +
ranking), not promised in UI copy.

## 11. Test plan (for the implementation step)

Engine: hard constraints 9.1–9.4 (overlap discarded · width · height ·
fixed byte-identical incl. out-of-scope) · ranking follows 9.5–9.7
(crafted equal-length case prefers compact) · several distinct options
(9.8) · seed-deterministic (rule 10) · effort maps to search size ·
spacing honored. Service/view: permissions · controls validation
(options 1–8, mode whitelist, spacing bounds) · scope resolution
(selection∩unlocked; all-locked honest error; empty selection = all
unlocked) · delta/worse-than-current math · JSON shape · **zero rows
created by optimize** · keep→save round trip with locks intact.
Browser: select 2 of 4, lock 1 → Optimize → strip (Current + options,
delta badges incl. a crafted worse case) → preview → Return exact →
Keep → Undo (pre-Keep) → Redo → drag + undo → optimize again → Save →
reload. Mobile @390. Full serial regression.

**DESIGN v4 FINAL — STOPPED. Awaiting owner approval before any
implementation.**
