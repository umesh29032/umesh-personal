---
id: docs-ai-pattern-intelligence-phase5-m4-report
type: receipt
status: active
owner: append-only
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# Phase 5 · Milestone 4 REPORT — Undo/Redo + wording pass (2026-07-07)

**Status: ✅ M4 COMPLETE — STOPPED. M5 will not start without approval.**

## Implementation summary (the three clarifications, literally)

- **Rule 1 — layout-only history:** entries are created ONLY by drag
  (when something actually moved), rotate, lock/unlock, and **Keep**.
  Zoom, pan, grid, guides, optimizer settings, strip visibility, card
  highlighting and selection changes create ZERO entries — proven live
  (zoom+grid toggles left the depth untouched). **Return to Current**
  restores the committed layout and never creates an entry (in this UX
  it can only restore, never change, the working layout — satisfying
  "only if it changes" by construction).
- **Rule 2 — lightweight history:** the milestone's core design move —
  each piece's **base geometry is established ONCE at page load and
  never rebuilt**; previews and Kept options (the engine only translates
  and 180°-rotates the same shapes) are applied as pure transforms.
  A history snapshot is therefore just `{dx, dy, rot, locked}` per piece
  — no rings, no thumbnails, no SVG, no geometry copies, ever. Depth
  capped at 100 (≥ the required 50).
- **Rule 3 — preview safety:** proven live with depth probes: **three
  consecutive previews → depth unchanged (2→2)**; Return → still 2;
  **Keep → exactly one entry (3)**; Undo after Keep restored the
  pre-Keep layout (149.5 mm back from 102.5 mm). Undo/Redo are disabled
  while previewing (editing is paused there — M3's rule-3 behavior).

Controls: ↶ Undo / ↷ Redo buttons + **Ctrl-Z / Ctrl-Shift-Z** (⌘
variants); redo clears on new action (standard semantics); buttons
disable at stack edges; `data-undo-depth`/`data-redo-depth` probes on
the root for testing.

**Wording pass (design §0, ships with the phase):** save toast is now
"Layout saved (X mm, verified) — you're now editing the saved version"
(no internal words — pinned by test asserting `candidate #` absent);
the entry button reads "🛠 Open layout editor".

## Changed files
- `config/patterns_ai/templates/patterns_ai/workspace.html` — history
  module (snap/apply/push/undo/redo), transforms-over-base
  `stateFromPlacements`, preview/Keep/Return rewired, buttons + keys,
  init snapshot.
- `config/patterns_ai/views.py` — save toast wording.
- `config/patterns_ai/templates/patterns_ai/candidate_detail.html` —
  button wording.
- `config/patterns_ai/tests/test_phase5_m3_ui.py` — +2 M4 tests
  (controls render; save-toast product language).
- `config/patterns_ai/tests/test_phase4_workspace.py` — ONE conscious
  needle rework (page title is now "Layout editor · #N"), documented.

## Browser validation (live, depth-probed; screenshots `m4_*`)
Drag → depth 1→2; **Undo restored the polygon byte-for-byte**; Redo
re-applied it byte-for-byte · three previews = zero entries; undo
DISABLED during preview; Return = zero entries · Keep = one entry;
**undo-after-Keep returned the working layout exactly** · rotate = one
entry; lock = one entry; **Ctrl-Z twice un-locked then un-rotated;
Ctrl-Shift-Z redid** · zoom + grid toggles = zero entries.

## Mobile validation
@390: Undo/Redo buttons sit in the wrapping toolbar, fully tappable;
the whole M3 flow remains usable (screenshot archived).

## Engineering review (hostile pass)
- The transforms-over-immutable-base model is the milestone's one real
  idea and it kills three risks at once: history weight (rule 2),
  selection survival across Keep, and preview/restore exactness (no
  rebuild drift). It relies on the engine's contract (translate +
  180°-rotate only) — already server-enforced (M2 piece-multiset law)
  and test-pinned in M1.
- History is page-session state, by design (Save remains durability;
  leaving the page ends history — stated in the design).
- No new URLs, no persistence, no server changes beyond one toast
  string. **Zero design deviations; Future Improvements: none proposed.**

## Regression
patterns_ai **225/225 OK** (219 + 6: the M4 test class subclasses the M3 class, re-running its 4 renders alongside the 2 new tests) · full manufacturing suite **1110/1110 OK** (serial,
fresh) · `makemigrations --check` clean (zero schema, pin 15) · import
contracts unchanged. Two documented conscious assertion reworks
(page-title needle; the html-escaped apostrophe in the new toast).

**STOPPED — awaiting approval for M5 (phase close: full fresh
regression + browser E2E + engineering review + completion report +
freeze).**
