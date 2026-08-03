---
id: docs-ai-pattern-intelligence-adr-adr-e-calibration-metrology
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR-E — Calibration & Metrology Standard

**Status: DRAFT (Phase 1) — owner sign-off pending. Error tiers become binding
numbers after P0/P2 validation (addendum).**

## Problem
Photo capture turns cardboard patterns into permanent digital truth. Phone
cameras lie (lens distortion, computational photography), paper curls, mats
wear, print shops rescale. Without a metrology chain of custody, silent
dimension errors become permanent company knowledge and eventually cut fabric.

## Decision
1. **Reference = printed ChArUco calibration MAT (~1.5 × 1.0 m) that the piece
   lies ON** — full-field scale + distortion per photo. Never an A4 sheet
   beside the piece.
2. **`CalibrationMat` registry (physical asset):** mat_id, commissioning
   measurements (tape-measured control distances recorded BEFORE first use —
   print-shop scale error is caught here), status, append-only recheck log.
   Every `CaptureAsset` FKs its mat + a device capture profile (phone model,
   app mode).
3. **Per-photo quality gate, hard:** minimum marker count visible, reprojection
   residual threshold, tilt limit, mat self-check (known inter-marker
   distances). Non-compliant frames are REJECTED — including gallery uploads
   without the mat. No silent acceptance path exists.
4. **Tiered honest error spec:** target ≤2 mm for pieces inside the mat cage
   under compliant capture; larger pieces via the fixed capture station
   (preferred) or mat-registered multi-shot; tiers VALIDATED at P0/P2 against
   tape-measured golden pieces and published as an addendum — never claimed
   beforehand.
5. **Numeric acceptance:** auto-measured key dimensions shown beside the
   master's tape numbers; confirmation least-squares-fits the polygon to tape
   values. Human confirmation remains the source of truth.
6. **Provenance stored for reprocessing:** raw marker detections, homography,
   residuals, EXIF, `pipeline_version` — originals immutable, so any future
   better pipeline re-derives NEW drafts for re-confirmation.
7. **Trust grades** (MEASURED / PHOTO-CALIBRATED / UNCALIBRATED) stamp every
   geometry; generation restricted to the first two (ADR-D's D11 carve-out is
   the sole, badged exception).

## Alternatives considered
- **A4 ArUco sheet beside the piece** — rejected: cannot honestly bound error
  on ≥1 m pieces (kickoff review CB-context; V1→V2 metrology blocker).
- **Overhead fixed camera rig only** — deferred: the station is preferred but
  phone-on-mat must work for v1 adoption; the registry + gates make both honest.
- **Trust-the-photo (no gate)** — rejected: silent garbage becomes permanent
  knowledge; violates honest-AI.
- **Professional digitizer tablet hardware** — rejected v1: cost + against
  open-source/commodity philosophy; DXF import covers professionally-digitised
  patterns anyway.

## Tradeoffs
The mat is a physical dependency (cheap, but must be commissioned and
recheck-logged). Hard gates will frustrate users on bad captures — by design;
retake friction is cheaper than wrong cardboard-truth. Multi-shot stitching is
bounded to mat-registered frames only (no feature-panorama guessing).

## Consequences
Every stored dimension has a custody chain: which mat, which device, what
residuals, who confirmed against which tape numbers. "Recall every capture
made on the stretched mat" is one query. Plotter-era (P5) re-tightening has
data to stand on.

## Future evolution
Better segmentation models slot into the ladder (ADR-F vendored) without
touching stored truth; new mats/devices are registry rows; a future site
dimension inherits mats/devices as its natural per-factory anchors (V3 §4.0).

## Why it respects Manufacturing V1
No production involvement; mirrors V1's physical-truth discipline (Packing's
honest count; verification-before-advance) applied to metrology; the registry
copies the machines-app pattern rather than inventing one.

## Why it respects Blueprint V3
Implements C13 and the capture pipeline of V2 §6 verbatim; honest-AI (tiers
validated, never promised); human-confirmed truth; F2 (recheck log = decision
events); F5 (mats retired, never deleted).

---

## ADDENDUM 1 — P0 synthetic closed-loop results (2026-07-06, empirical)

Harness: `poc/patterns_ai/metrology_poc.py` (OpenCV 5.0.0, ChArUco 14×10 ·
100 mm squares · DICT_5X5_1000, 1400×1000 mm virtual mat). Method: hold-out
validation — homography fitted on half the detected corners, error measured
on known distances between held-out corners (59 pairs, spans >100 mm).

| Scenario | Corners | mean err | p95 err | max err |
|---|---|---|---|---|
| flat | 84/84 | 0.003 mm | 0.007 mm | 0.007 mm |
| mild tilt + blur | 84/84 | 0.023 mm | 0.053 mm | 0.060 mm |
| strong tilt + noise + blur | 84/84 | 0.030 mm | 0.071 mm | 0.076 mm |

Findings: the ALGORITHM CHAIN (detect → plane homography → mm measurement)
contributes ≤0.08 mm under simulated worst-case phone geometry — ~25× headroom
under the ≤2 mm physical tier. Physical error will therefore be dominated by
mat print accuracy, paper curl, and lens distortion — exactly what the
commissioning ritual + per-photo gates measure at P2 on the real mat (D7).
The ≤2 mm in-cage tier remains the claim to VALIDATE, now with algorithmic
headroom proven.
