# P2 ENGINEERING REVIEW — hostile eyes on the geometry era (2026-07-07)

**Method:** self-hostile pass over every new module (compute runtime,
services, views, templates, tests) + live tamper probes during the
browser walk. Two real bugs were found DURING this review and fixed +
test-pinned before delivery (print-scale shrink, grain-prefill units) —
recorded here per the honest-report rule.

## Verdict
**SOUND.** Constitution intact (single-writer, append-only, derived-
regenerable, human-confirmed). No money surface. No manufacturing
contact. Debt register below — nothing critical.

## 1. Architecture
- ADR-F isolation is REAL and test-walled both directions (no cv2 in
  Django; no Django/network in compute; lockfile + manifest existence
  pinned). The bridge is 60 lines, files/argv, timeout-bounded — boring
  by design.
- Single writers hold: `calibration_service` (mat + checks),
  `pattern_geometry_service` (pieces/versions/geometry/extractions/
  labels); I-1 repo-scan covers all 13 models. Views stayed
  parse→gate→delegate (re-read of all 18 endpoints).
- Twin canonical validators (compute + Django) are duplicated BY DESIGN
  (runtime must validate without Django; Django must never trust a
  subprocess). Lockstep note sits in both files + the spec doc. Drift
  risk accepted and documented — a shared-fixture parity test is the
  future hardening if it ever bites.

## 2. Correctness / honesty
- Hold-out residuals: accuracy is measured on corners the fit never saw —
  the reported mm error cannot flatter itself.
- Refusals are FACTS: gate-failed extractions persist with reasons;
  failed commissioning persists its evidence row and the mat stays
  uncommissioned; failed rechecks never auto-retire (human decides).
- Tape acceptance REFUSES confirmation beyond ±2 mm rather than silently
  storing a grade. Trust grades: measured / photo_calibrated /
  uncalibrated — DXF imports start uncalibrated (nobody measured them
  here yet), upgraded only by tape.
- Confidence = weakest component, display-only; the annotator SAYS SO.

## 3. Performance
- Extraction ≈ 1–2 s on goldens (subprocess + detect + segment) —
  inside the master plan's <5 s interactive budget; synchronous by
  design until ADR-B (P3).
- Bridge overhead per call: one venv python spawn (~150 ms). Fine at
  capture cadence; batchable later without API change.
- Version detail renders N size SVGs server-side — trivial strings.

## 4. Security
- All 18 URLs management-gated (worker 403 + anon redirect swept by
  test). Uploads ride the P1 pipeline (magic bytes, caps, hash naming).
- Subprocess args are fixed paths + tempfiles; user input reaches the
  runtime only INSIDE json payloads; no shell=True anywhere.
- DXF uploads parsed by ezdxf inside the ISOLATED venv — a hostile DXF
  crashes a subprocess, not Django (and surfaces as a recorded
  ComputeError → form error).
- Editor POST re-validates everything server-side; drafts only.
- Tampered ids 404 (P1 debt fix, test-pinned).

## 5. Concurrency
- Version/extraction/mat mutations under select_for_update; review +
  confirm are one-shot state machines (DB CHECKs back them).
- `get_or_create_draft` race: two simultaneous captures could try to
  create v(n+1) twice — UNIQUE(piece, version_no) makes the loser error
  raw. LOW (single-user factory), registered.

## 6. Maintainability
- Compute runtime is dependency-light and versioned (PIPELINE_VERSION in
  every result). Future pipeline = new version stamp; old provenance
  stays interpretable.
- Templates follow canon; no new shared CSS; page-scoped styles only.
- Views file is growing (P1+P2 in one module, ~900 lines, still
  rule-free). Splitting into a package is a MECHANICAL refactor for a
  future approved block — not now (frozen-foundation discipline).

## 7. Debt register (P2 additions)

| # | Item | Severity |
|---|---|---|
| 1 | draft-creation race → raw IntegrityError (UNIQUE backstop) | LOW accepted |
| 2 | MatCommission errors return as flash messages (form state lost on refusal) | LOW UX polish |
| 3 | classical backend needs mid-tone pieces; dark/light fabric → honest refusal until SAM weights vendored | documented ladder |
| 4 | validator twins could drift (lockstep notes both sides) | watch; parity test if bitten |
| 5 | views.py size (mechanical split candidate) | cosmetic |
| 6 | multi-piece DXF refused v1 | scope |
| 7 | no capture UI for notches/drills/internal lines (schema+render+DXF ready) | next-era scope |

## 8. Future ADR candidates
- DB-level append-only hardening now spans 4 tables (events, captures,
  checks, extractions) — carried forward, weight growing.
- SAM activation procedure (already written in MANIFEST.md) becomes an
  ADR-F addendum when the owner vendors weights.
- ADR-B worker (P3) — unchanged.

No redesign recommended. **The era is freeze-shaped: additive schema,
walls tested, truth chain human-gated.**
