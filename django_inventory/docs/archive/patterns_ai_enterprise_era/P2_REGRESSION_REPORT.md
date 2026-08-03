# P2 REGRESSION REPORT (2026-07-07)

**All gates re-run against the finished Phase-2 tree. Serial only.**

| Gate | Result |
|---|---|
| Full manufacturing + patterns suite | **1013 tests — OK** (161 s; was 979 at P1 close; +34 = P2) |
| patterns_ai suite | **128/128 OK** (94 P1 + 34 P2) |
| `makemigrations --check` | **No changes detected** (0005 applied; all additive) |
| import-linter | patterns_ai layer kept; the 1 broken contract = the PRE-EXISTING aspirational `tracking.tests → production` target (unchanged since before P1) |
| Media sweep | run at P1-final: clean; P2 adds no derived class (renditions reused) |
| Query pins | A360 67 · ADDA_LIST 8 · yield-board ceiling — all inside the green suites; NO pin moved by P2 |
| Model pin | consciously 9 → 13 (documented in test + ADRs) |
| Manufacturing files touched by P2 | **ZERO** (git status: only patterns_ai/, compute/, docs/) |
| Golden ₹225 + journey money totals | inside the green full suite — byte-identical, untouched |
| Enforcement flags | still OFF (owner rollout policy, untouched) |

## New walls added by P2 (now part of every future run)
- Django never imports cv2/numpy/ezdxf/shapely/torch/onnxruntime
  (source-scan).
- Compute runtime never imports django or socket/requests/urllib
  (source-scan).
- Lockfile + artifact manifest must exist (ADR-F vendoring).
- True-scale SVG viewBox/width parity (the print-shrink pin).
- Real-runtime goldens: 150×100 mm truth extracted within ±2 mm; boardless
  photo refused; lying tape refused via self-check; DXF round-trip
  byte-exact; border keep-out refusal.

## P1 surfaces re-verified after P2 changes
P1's 94 tests ran green THREE times during P2 development (they share the
suite); the marker workflow, library, usage/outcome, and Yield Board pages
were untouched except: `_int_or_404` hardening (new 404 tests), dead-var
removal, and the home page gaining two nav links (rendered in the green
view tests). Yield board `?product=abc` now 404s — pinned.

## Browser regression (live server 8003)
Login → home (new nav) → mats registry → commission → piece → capture
upload → annotator → accept → confirm → exports → print → editor →
copy-forward/reject — every P2 page exercised @390 and desktop with 12
archived screenshots; P1 pages spot-checked (home, library links render).

**Zero regressions. Manufacturing untouched and green.**
