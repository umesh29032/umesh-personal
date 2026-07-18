# P4 READINESS REPORT — AI Pattern Intelligence era entry check (2026-07-07)

**Verification only. P4 is NOT started.**

## Verdict: **READY — no architectural blockers.** Blueprint V3's Era-2
(Intelligent Assistant) has every input it was designed to consume.

## 1. What P4 stands on (all live, frozen, tested)
- **Comparable reality data:** manual AND generated markers accumulate
  identical fact streams (usage → outcome → derived m/100 with honest n)
  through ONE frozen machinery. The assistant era's core loop — "suggest,
  human decides, reality scores" — has its scoring half running.
- **The decision spine:** `SuggestionEvent` (schema since 2A, product-homed,
  outcome+reason constrained) is the landing table for assistant
  proposals; `MarkerTransitionEvent` already carries promotion evidence
  payloads — the append-only pattern to copy.
- **Evidence chains:** every generated marker → candidate → run →
  exact geometry rows → captures → mat. "Why did the system suggest
  this?" is FK-walkable end to end.
- **Benchmark verdict data:** beats / does_not_beat / no_baseline
  verdicts with labeled numbers accumulate as training-free heuristic
  fuel (which widths, which ratios, which engines win).
- **Engine independence:** assistant logic will RANK and EXPLAIN, engines
  stay behind the ADR-F bridge; F4 uncompromised.

## 2. Known risks going into P4
| Risk | Standing answer |
|---|---|
| Assistant scope creep toward auto-decisions | Era-2 stance is constitutional: propose + human confirm; SuggestionEvent.outcome requires a human decider |
| Sparse reality data early (few outcomes) | honest-n discipline already built; suggestions must show their n |
| Local-LLM temptation (D10) | stays OFF until owner enables; ADR-F manifest slot exists |
| Suggestion fatigue / noise | design gate for P4 kickoff: every suggestion carries evidence + a shut-up threshold |

## 3. Entry criteria for P4 kickoff
1. **Owner approval** of the P3 package + freeze.
2. **Owner checkpoint commit** (standing N-1 discipline).
3. **P4 design step first** (per the master plan + kickoff contract):
   define WHICH assistant surfaces (marker recommendation at cut-planning?
   width advice? ratio advice?) land first — the blueprint lists the menu;
   the owner picks the first plate.
4. Real-mat D7 validation remains the standing physical-tier ritual for
   rollout (unchanged, orthogonal).

**STOPPED. No P4 work begins without the owner's explicit go.**
