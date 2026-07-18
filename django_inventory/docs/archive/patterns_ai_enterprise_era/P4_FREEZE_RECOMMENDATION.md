# P4 FREEZE RECOMMENDATION (2026-07-07)

## Recommendation: **FREEZE P4 — the Cut Advisor — as delivered.** ✅
(Same law as P1–P3: no refactor/redesign without explicit owner approval;
additive evolution only.)

## What is frozen
- **The assistant contract:** propose + explain + record; humans decide;
  zero production write paths. `advisor_service` stays READ-ONLY
  (test-walled); `suggestion_service` stays the only SuggestionEvent
  writer; the one-shot offered→decided transition is the only update.
- **The ranking law:** proven beats theory, always; reality ranks by
  m/100 with n/recency tie-breaks; theory carries its label; saving is
  measured against actual practice; "already best" and "no facts yet"
  are first-class honest answers.
- **The evidence contract:** offers freeze their full shown snapshot
  (schema_version 1); confidence = weakest-component, display-only.
- **Learning mechanism:** re-derivation from the growing fact base —
  no stored scores, no jobs, no trained parameters. Any learned model /
  local LLM is a NEW ADR (D10), never a silent slide.

## Intentionally deferred (not defects)
Cloth-roll width-stock integration · ratio-space search sweeps ·
suggestion-acceptance analytics (P5 reporting) · full history page ·
derived-metrics cache (volume lever) · views.py split (cosmetic, carried).

## Risks & standing answers
| Risk | Answer |
|---|---|
| Users read confidence as authority | weakest-component + "the human decides" note + low-n honesty (live 20/100) |
| Advice ossifies bad habits (baseline = most-used) | best-proven ALWAYS shown against it; saving quantifies the gap |
| Sparse data early | empty/low states teach the cure; untested options labeled for trials |
| Scope pressure toward auto-apply | structural: the brain cannot write; the writer only records human verdicts |

## Readiness statement
patterns_ai 166/166 · full serial suite green · no schema change ·
contracts unchanged · walls green (incl. the new SELECT-only wall) ·
browser-proven incl. refusal/empty paths. **Safe to freeze. Checkpoint
commit remains the owner's.**
