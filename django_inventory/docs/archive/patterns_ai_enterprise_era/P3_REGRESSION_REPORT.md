# P3 REGRESSION REPORT (2026-07-07)

| Gate | Result |
|---|---|
| patterns_ai suite | **147/147 OK** (94 P1 + 34 P2 + 19 P3) |
| Full manufacturing suite (serial) | **1032 tests — OK** (200 s; was 1013 at P2 close; +19 = P3) |
| `makemigrations --check` | **No changes detected** (0006 applied; additive only) |
| import-linter | patterns_ai kept; broken = the same PRE-EXISTING `tracking.tests → production` target |
| Model pin | consciously 13 → **15** (run + candidate; documented in test + report) |
| I-1 single-writer scan | extended to both new models; repo-wide green |
| ADR-F walls | re-ran green WITH the new engine files (no cv-stack/django/network leaks) |
| Manufacturing files touched | **ZERO** (patterns_ai/, compute/, docs/ only) |
| Golden ₹225 + journeys | inside the green suite, untouched |
| Enforcement flags | still OFF (owner policy) |

## Conscious changes to prior-era tests (documented, not silent)
- Block-2B `test_strategy_only_for_generated`: now supplies a candidate
  fixture and asserts BOTH new D11 rules (generated⇒candidate required;
  candidate⇒generated only). This is the P1-frozen marker service gaining
  an ADDITIVE parameter — behavior for every existing origin unchanged
  (94 P1 tests otherwise untouched and green).

## P1/P2 surfaces re-verified
- P1: full marker workflow tests green; Yield Board now ALSO renders the
  promoted generated marker (browser-proven, honest-NULL until outcomes).
- P2: geometry suite green; confirmed geometry consumed READ-ONLY by
  generation (service reads latest confirmed version; no P2 write path
  touched — I-1 + immutability guards prove it structurally).

## Browser regression (live 8003)
Login → generate form (ratio/width/engine) → sync run → run comparison
(2 candidates, PASS badges, derived numbers) → candidate detail
(visualization, stat chips, benchmark verdict with THEORY/REALITY labels)
→ promote → MRK-000003 in the P1 library → Yield Board row. Mobile @390 +
desktop screenshots archived (`p3_*`). One papercut found+fixed live
(tall-marker viz height) — restart-after-template-edit lesson reapplied.
