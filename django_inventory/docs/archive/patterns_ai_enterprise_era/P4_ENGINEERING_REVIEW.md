# P4 ENGINEERING REVIEW — hostile eyes on the Advisor (2026-07-07)

**Method:** self-hostile re-read (advisor_service, suggestion_service,
AdvisorView, template, the SuggestionEvent guard) + live UI probes.
Solo review (small pure-python surface); recorded per audit-honesty rule.

## Verdict
**SOUND.** The assistant is structurally incapable of deciding anything:
its brain cannot write (SELECT-only proven), its only writer records
offers and HUMAN verdicts, and production write paths are untouched.

## 1. Honesty audit (the era's core risk)
- Proven-beats-theory is a SORT-CLASS property, not a weight — a
  theory-only marker cannot enter `proven` at all. Test-pinned.
- Saving compares against the factory's ACTUAL habit (most-used marker),
  not a strawman; "already best" is a first-class answer. Pinned.
- Confidence composite = weakest component; n=1 evidence honestly reads
  20/100 on the live page. No score inflation path exists.
- Untested generated markers surface WITH their theory number AND the
  label — visibility without false authority.
- Empty state teaches the cure (record outcomes), not an apology.
- The offer snapshot freezes evidence WITH the numbers shown — future
  "why did it say that?" is answerable from the row alone (ADR-D3 spirit).

## 2. Architecture
- `advisor_service` imports only sibling read paths + models; zero ORM
  writes (query-capture test) — the read-model law extended to the brain.
- `suggestion_service` = SuggestionEvent's first and only writer; I-1
  repo-scan already covered the model (2A list) — now it has its service.
- SuggestionEvent gained the same one-shot guard as the other decision
  tables — additive hardening on a zero-row table; P1 freeze respected
  (no behavior existed to change).
- View stays parse→gate→delegate: two actions, both delegating; redirect-
  after-POST keeps refresh-safe.
- **No new models** — the design's discipline held through implementation.

## 3. Performance
- recommend() = markers × summary derivation (the pinned P1 per-marker
  cost) + geometry-trust walk. Same O-shape as the Yield Board, same
  documented ceiling philosophy. Advisor page ≈ board + history query.
- No caching, no jobs — correct at factory volume; a derived-class cache
  remains the pre-designed lever (ADR-G semantics) if products ever hold
  hundreds of markers.

## 4. Security
- Management-gated (403/302 swept); tampered product ids 404; width
  parsed defensively; decision pk parsed via `_int_or_404` and scoped to
  the selected product (cross-product decide = 404).
- Payloads rendered back via template escaping; reasons stored verbatim,
  rendered escaped; CSRF on both forms.
- Worker POST proven side-effect-free.

## 5. Concurrency
- decide() under select_for_update + one-shot check; double-submit safe.
- Two managers offering simultaneously → two offered rows (both FACTS of
  what was shown) — correct, not a race.

## 6. Debt register (P4)
| # | Item | Severity |
|---|---|---|
| 1 | Confidence thresholds fixed in code (documented) | by design; revisit with real data volume |
| 2 | History capped at last 10 on-page | UX lever; full history = future report page |
| 3 | Advisor derivation cost grows with marker count | pinned philosophy; cache lever pre-designed |
| 4 | Decision UI lives only on the advisor page | one-door by design (P4 §7) |
| 5 | views.py split (carried) | cosmetic |

## 7. Future ADR candidates
- D10 gateway (learned ranking / local LLM) — ONLY via new ADR + vendored
  artifacts; today's heuristics are its honest baseline.
- Suggestion-outcome analytics (acceptance rates vs later reality) — P5
  reporting candidate feeding on the spine this phase created.

No redesign recommended.
