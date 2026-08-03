# P0 IMPLEMENTATION REPORT — Feasibility (2026-07-06)

**Status: ✅ P0 COMPLETE — STOPPED. P1 (Digital Memory) will NOT start without
explicit owner approval.**
Scope honored: everything inside `poc/patterns_ai/` + ADR addenda + this
report. **Zero manufacturing changes · zero Django apps/models/migrations/
services · zero production-settings changes · frozen engine untouched**
(read-only DB access only, for the yield walk).

## 1. Bake-off numbers (full detail: ADR-A Addendum 1; raw: `poc/patterns_ai/results/`)

| Harness set | BLF-grid floor | SVGnest core headless |
|---|---|---|
| T-SHIRT S2:M2:L1 (20 pcs, 1100 mm) | 79.86 % · 172 s | **80.11 %** · 106 s |
| 3-PATTI S2:M2:L1 (15 pcs, 940 tube-flat) | 73.90 % · 11 s | **79.30 %** · 15 s |
| stress (>1 m leg, curves, on-fold; 940 mm) | **76.78 %** (fold-pinned) · 29 s | 75.91 % (unfolded) · 3 s |

- **Gate ≥75–80 %: MET.** All pieces placed on every set, including the
  1080 mm leg panel and mirrored pairs.
- **pynest2d eliminated** (no PyPI distribution; Qt/SIP source build fails
  the maintainability criterion) — the hostile review's suspicion, now fact.
- **Engine selection: SVGnest core (headless, vendored @1248dc2) primary +
  BLF-grid floor forever.** The floor is honest competition — it WON the
  T-shirt set against a 201-trial search; deeper search is known upside.
- Readiness condition N-3 satisfied early: the runner already executes from
  the vendored tree; Node v18 joins the ADR-F manifest.

## 2. Metrology POC (full detail: ADR-E Addendum 1)

Synthetic closed loop (ChArUco 14×10 · hold-out corner validation, 59 pairs):
**algorithm-chain error ≤0.08 mm** even under strong tilt + noise + blur
(84/84 corners detected in all scenarios). The ≤2 mm physical tier now has
~25× algorithmic headroom; remaining error sources (mat print, curl, lens)
are exactly what P2's commissioning ritual measures on the real mat.

## 3. Yield-board data walk (real 3-PATTI-016, read-only)

`45.0 linear m` laid (30 plies × 1.5 m on 37″ tube CR-000004) → 60 garments
cut (APSCPB) → 54 packed ⇒ **75.0 m/100 garments**, est. utilization 22.9 %
(harness garment area). The bake-off marker for the same ratio needs
**≈21.6 m/100** — a 3.5× gap the yield board would surface instantly.
(Honest footnote: the lay numbers are DEV-fixture values, so the gap
demonstrates the board's DIAGNOSTIC POWER, not real factory waste.) The P1
yield-board math is proven end-to-end on owned data.

## 4. Empirical lessons banked (cost already paid)

clipper.js needs a `navigator` shim headless · grain axis must be normalized
to the lay axis (bug caught BY the >1 m stress piece) · missing pair-NFPs make
PlacementWorker silently overlap — the Minkowski/Clipper path is mandatory ·
fold-pinning is absent from the SVGnest core (P3 adapter work item, BLF
already does it) · OpenCV 5.0 ChArUco API returns flat id arrays.

## 5. GO / NO-GO

**GO.** All three P0 exit criteria met: utilization gate cleared by the
selected engine · tiered error spec published with algorithmic headroom
proven · yield walk reproduces the settled journey's fabric math. Risk moved
from "can this work?" to "execute P1 as planned."

## 6. Deliverables

`poc/patterns_ai/` (README, manifest, lockfile, harness, engines, results
JSONs) · ADR-A Addendum 1 · ADR-E Addendum 1 · this report.

**Awaiting owner approval for P1 — DIGITAL MEMORY** (manual markers + usage/
outcomes + yield board; D2/D3 mini-ADRs at phase start per master plan).
