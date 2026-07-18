---
id: docs-ai-pattern-intelligence-phase5-m3-report
type: receipt
status: active
owner: append-only
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# Phase 5 · Milestone 3 REPORT — Workspace optimize UI (2026-07-07)

**Status: ✅ M3 COMPLETE — STOPPED. M4 will not start without approval.**

## Implementation summary (the four UI rules, literally)

- **Rule 1 — workspace first:** everything lives inline in the layout
  editor: a second toolbar row (Layout options 1–8 · Mode Fast/Balanced/
  Best · Piece spacing · fixed "Rotation: 0°/180° (grain rule)" text ·
  ✨ Optimize) and an inline **options strip** between the toolbars and
  the canvas. No dialogs, no wizards, no side pages, no floating
  windows (`<dialog>` absence test-pinned).
- **Rule 2 — instant:** Optimize disables its button and shows a plain
  "Optimizing…" text (no spinner animation); the strip appears in place;
  clicking an option updates the canvas immediately; clicking **Current
  Layout** returns immediately and exactly; Keep adopts and editing
  continues. Context never leaves the page.
- **Rule 3 — zero surprises:** nothing moves/selects/locks/saves/replaces
  automatically. While PREVIEWING an option, canvas editing is paused
  (visible blue bar: "Previewing Option N — editing is paused…") so a
  stray drag can't silently mutate a preview — proven live: a drag
  during preview changed nothing. Keep or Return re-enables editing.
  Keep dismisses the strip (the round is decided — a fresh Optimize
  builds a new comparison); nothing persists until Save.
- **Rule 4 — visual simplicity:** simple cards, static mini-SVG
  thumbnails, three plain badges, zero animations/transitions. The
  layout stays the hero.

**Multi-select (rule 7 groundwork):** click selects, shift-click
adds/removes, background click clears, "N selected" chip; Rotate/Lock
now act on the whole selection; selection survives preview/keep by piece
identity. **Honest badges (rule 6):** red "Worse than Current", green
"Saves X mm", grey "Same as Current" — driven by the server's delta
fields. Baseline = the exact pre-optimize placements, restored
byte-for-byte on Return.

## Changed files
- `config/patterns_ai/templates/patterns_ai/workspace.html` — settings
  row, strip, preview bar, multi-select, optimize fetch, product-language
  wording pass ("Layout editor", "the server decides at Optimize/Save").
- `config/patterns_ai/tests/test_phase5_m3_ui.py` — NEW (rendered
  controls, product language, no-dialog pin, Phase-4 controls intact).
- `config/patterns_ai/tests/test_phase4_workspace.py` — ONE conscious
  needle rework: the old copy said "server verifier"; the language rule
  bans internal vocabulary in the flow, so the hint (and the test) now
  say "the server decides" — documented here per discipline.

## Browser proof (live server; screenshots `m3_*`, desktop + @390)
- Locked a piece, pressed Optimize with it still selected → the honest
  refusal from M2 rendered inline: *"everything selected is locked —
  unlock something or select other pieces."*
- Cleared selection → Optimize → strip: **Current Layout + Options 1–3,
  every option honestly badged "Worse than Current"** (the source layout
  was already tight — the UI tells the truth instead of pretending).
- Previewed Option 1 → preview bar on, editing frozen (drag provably
  inert), canvas at 102.5 → **Current Layout click → exact 101.0
  restored**, bar off.
- Dragged a piece badly (239.5 mm) → Optimize → **"Saves 137.0 mm"**
  green badges → **Keep Option 1** → strip dismissed, editing live,
  canvas 102.5, message "Option 1 kept — keep editing or save."
- Mobile @390: settings wrap cleanly, strip scrolls horizontally,
  thumbnails + badges + Keep buttons fully usable.

## Test results
- **M3 suite 4/4** (controls render inline · product language + no
  internal vocabulary · multi-select/preview wiring · Phase-4 controls
  intact) — plus M2's 14 and Phase-4's 12 re-ran green with the one
  documented needle rework.
- Full app + serial regression: fresh run, counts below.

## Engineering review (hostile pass)
- All state machines are client-side and small: `previewing` flag +
  `baselineState` snapshot; the only server interaction stays the M2
  stateless endpoint. No new URLs, no persistence, no session use.
- Editing-pause-during-preview is the one behavior ADDED beyond the
  literal design text — it exists to satisfy rule 3 (a drag mid-preview
  would otherwise silently blend a preview with manual edits =
  a surprise). Documented as the implementation of "never surprise",
  not a scope change.
- Thumbnails are dumb string SVGs (no lib); strip capped by
  options_wanted ≤ 8.
- Rotate/Lock on multi-selection replaces the old single-selection
  behavior — strictly more capable, same buttons; Phase-4 tests still
  green.
- **Future Improvements: none proposed. No design deviations.**

## Regression
patterns_ai **219/219 OK** (215 + 4 M3) · full manufacturing suite **1104/1104 OK** (serial,
fresh) · `makemigrations --check` clean (zero schema, pin 15) · import
contracts unchanged.

**STOPPED — awaiting approval for M4 (Undo/Redo + final wording pass).**
