# P4 REGRESSION REPORT (2026-07-07)

| Gate | Result |
|---|---|
| patterns_ai suite | **166/166 OK** (94 P1 + 34 P2 + 19 P3 + 19 P4) |
| Full manufacturing suite (serial) | **1051 tests — OK** |
| `makemigrations --check` | **No changes detected** (P4 adds NO schema — guard is code-level) |
| import-linter | patterns_ai kept; broken = the same pre-existing `tracking.tests → production` target |
| Model pin | UNCHANGED at 15 (P4's design discipline: zero new models) |
| I-1 scan | green (SuggestionEvent writer now exists: suggestion_service) |
| ADR-F walls | green (advisor is pure python; no engine/CV imports) |
| Manufacturing files touched | **ZERO** |
| Golden ₹225 + journeys | inside the green suite |
| Enforcement flags | still OFF (owner policy) |

## New walls added by P4
- advisor_service SELECT-only (query-capture test — the brain cannot write).
- SuggestionEvent append-only + one-shot decision guard (save/delete
  refuse; service transition only).
- Ranking law pinned: proven-beats-theory; saving math; already-best;
  width fallback honesty; no-facts honesty.

## P1–P3 surfaces re-verified
All prior suites ran green unchanged — P4 touched no prior-era test and
no prior-era behavior (the SuggestionEvent guard hardened a zero-row,
writer-less table). Live pages spot-checked: yield board, marker detail,
generation run — all render as frozen.

## Browser regression (live 8003)
Advisor on LOWER (evidence hero, honest 20/100 confidence, UNTESTED
labels, already-best banner, geometry-trust line) → suggestion recorded →
accepted decision with audit trail → honest empty state on 3-PATTI.
Mobile @390 + desktop screenshots (`p4_*`, 4).
