---
id: docs-ai-pattern-intelligence-d7-validation-protocol
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# D7 PHYSICAL VALIDATION PROTOCOL — the real mat (2026-07-07)

**LAW (ADR-E): nothing claims physical accuracy before it is measured on
the real factory table. The tier table at the bottom of this document is
BLANK until this protocol runs. Until then, `photo_calibrated` trust is
PROVISIONAL and tape acceptance at confirm (→ MEASURED) is the only
grade the factory should rely on for cutting decisions.**

## 1. Procure (owner)
- Printed ChArUco mat ≈ 1.4 × 1.0 m (spec: 14×10 squares · 100 mm ·
  DICT_5X5_1000 · matte lamination; print shop told: NO scaling, 100%).
- Phone mount / tripod (top-down) + the dev phone.
- Steel tape (verified against a second tape).

## 2. Commission the mat (the tape ritual — catches print-shop scale lies)
1. Register the mat (`/patterns/mats/new/` — physical label = mat_code).
2. Tape-measure ≥3 control spans between printed corner intersections
   (long diagonals included). Corner ids count row-major on the inner
   grid (13 per row on a 14×10 board).
3. Enter board spec + tape lines; commission. **A failing self-check on
   the first captures = the mat lies; re-print, never "adjust".**

## 3. Capture environment checklists
**Phone:** stock camera app · NO beauty/HDR-enhance modes · lens wiped ·
highest resolution · hold or mount as flat over the mat as possible.
**Lighting:** even, diffuse; no hard shadows across mat or piece; no
direct sun stripes; verify: every board square visibly black/white on
the phone screen.
**Placement:** piece fully inside the 20 mm keep-out; whole mat in frame;
piece flat (weights on curled corners).

## 4. Golden-piece measurement validation
1. Cut 3 test pieces of card: 600×400 rect · 300×300 with one 45° corner ·
   an irregular ~500 mm garment-like shape.
2. Tape-measure each piece's key spans (2 people, independently; record).
3. Capture each piece 5× (vary position/rotation on the mat).
4. Extract via the wizard; record the system's width/height per capture.
5. Compute |system − tape| per span; fill the tier table below.

## 5. Acceptance criteria
- Gate pass-rate ≥ 80% of compliant captures (retakes are normal).
- p95 error ≤ 2.0 mm on in-cage pieces (the ADR-E target tier).
- Self-check deltas ≤ 2.0 mm on every accepted capture.
- FAIL ⇒ do not activate trust policy; investigate (print scale, curl,
  lighting), fix, re-run. The system stays usable meanwhile via
  tape-accepted confirms (MEASURED path).

## 6. Operator validation (the human side)
The cutting master, unaided after one demo: captures a piece → passes the
gate within 3 attempts → reviews the annotator → confirms with grain +
tape within the master plan's ≤90 s/piece budget. Sign-off recorded below.

## 7. Trust-grade activation policy
| Phase | Policy |
|---|---|
| Before D7 passes | photo_calibrated = PROVISIONAL; cutting decisions rely on MEASURED (tape-accepted) rows |
| After D7 passes | photo_calibrated trusted within the published tier; MEASURED remains the gold grade |

## 8. RESULTS ADDENDUM (blank until measured — never filled by assumption)
| Piece | Span | Tape mm | System p50 | System p95 | max err | PASS/FAIL |
|---|---|---|---|---|---|---|
| _(to be measured on the factory table)_ | | | | | | |

Operator sign-off: ______ · Date: ______ · Mat: ______ · Phone: ______
