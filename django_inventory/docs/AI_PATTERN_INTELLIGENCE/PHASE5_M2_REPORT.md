---
id: docs-ai-pattern-intelligence-phase5-m2-report
type: receipt
status: active
owner: append-only
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# Phase 5 · Milestone 2 REPORT — Stateless optimize service + endpoint
(2026-07-07)

**Status: ✅ M2 COMPLETE — STOPPED. M3 will not start without approval.**

## Implementation summary

`marker_generation_service.optimize_layout(...)` — **compute-only**, plus
the `action=optimize` AJAX branch on the existing workspace URL. The
three approved clarifications are implemented literally:

- **Clarification 1 — stateless:** every request carries the complete
  current layout, width, height, spacing, locks (inside the placements),
  selection, and optimizer settings (+ seed). Nothing is read from
  session or prior results; identical payload ⇒ identical response
  (test compares full options JSON).
- **Clarification 2 — server remembers nothing:** the service performs
  two bridge calls (verify the submitted layout for honest current
  metrics; run the optimize op) and returns JSON. **Zero writes** —
  query-capture test asserts no INSERT/UPDATE/DELETE; row-count tests
  assert no runs/candidates/suggestions appear. Preview/Keep/Return/Undo
  stay browser state (M3/M4); only the untouched Phase-4 save path ever
  persists.
- **Clarification 3 — stable option identity:** each option carries
  `id: "option-1" … "option-N"` (post-ranking order), valid only within
  its response, never stored.

Also in the response, computed where the numbers are born (rule 6 prep
for M3): the submitted layout's own `current` metrics
(length/utilization/waste + its verification verdict — an invalid
current layout is reported, not hidden) and per-option
`delta_length_mm`, `delta_utilization_pct`,
`worse_than_current` (longer OR lower-utilization ⇒ true; equal ⇒
false — honesty math test-pinned).

Scope law enforced (rule 7): free = `selected ∩ unlocked` when a
selection exists, else all unlocked; everything else passes to the
engine as fixed. Honest refusals: "everything selected is locked —
unlock something or select other pieces" · "every piece is locked —
unlock something to optimize." Controls validated: options 1–8 · mode
whitelist (Fast/Balanced/Best) · spacing 0.5–50 mm · width 300–3000 ·
height bounds · numeric coercion errors friendly. Per-effort bridge
timeouts (60/90/150 s) ride M1's headroom mechanism.

## Changed files
- `config/patterns_ai/services/marker_generation_service.py` —
  `optimize_layout` + `_validate_layout_placements` (additive).
- `config/patterns_ai/views.py` — `action=optimize` branch in
  `WorkspaceView.post` (parse → gate → delegate; JSON errors honest,
  incl. ComputeError surfaced as `ok:false`).
- `config/patterns_ai/tests/test_phase5_m2_service.py` — NEW.

## Test results — **M2 suite 14/14 OK**
Stateless reproducibility (full options JSON equal across identical
calls) · zero-writes wall + zero-rows assertions · stable ids
option-1..N · current metrics + delta honesty math · locked passthrough
byte-identical · **selection-scope law: unselected-unlocked piece
byte-identical in every option** · both honest scope errors · controls
validation sweep (9 bad inputs + bad pair + bad piece) · permission gate ·
height refusal bubbles honestly · endpoint: JSON shape/ids/current ·
persists nothing (row counts) · bad-payload + bad-effort error paths ·
worker 403 / anonymous 302.

## Browser/API validation (live server)
Real fetch from the real workspace page (CSRF included), fully stateless
payload: **`ok=true · options=2 · ids=option-1,option-2 ·
current_len=303 · best_len=303 · delta=0 · worse=false`** — equal
length honestly NOT flagged worse. UI consumption of this JSON is M3.

## Engineering review (hostile pass)
- The endpoint rides the existing management-gated workspace URL — no
  new URL surface; CSRF + role walls inherited and re-tested.
- Two bridge calls per optimize (verify current + optimize) — the
  honest-deltas cost; both timeboxed; acceptable at interactive cadence.
- ComputeError returns `ok:false` with the ops message instead of a 500
  (fail honest, not loud).
- No design deviations; **Future Improvements: none proposed.**
- Limitation carried from M1 (locks ⇒ BLF-only search) unchanged —
  surfaced via `orderings_tried`/`dropped` in the response for the UI.

## Regression
patterns_ai **215/215 OK** (201 + 14 M2) · full manufacturing suite
**1100/1100 OK** (serial, fresh) · `makemigrations --check` clean
(zero schema, pin 15) · import contracts unchanged · vendored code +
Django venv untouched.

**STOPPED — awaiting approval for M3 (workspace optimize UI: settings
row, multi-select, options strip with Current baseline + honest badges +
Preview/Return/Keep).**
