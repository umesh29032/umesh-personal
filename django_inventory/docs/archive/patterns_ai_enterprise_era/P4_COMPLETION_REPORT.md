# P4 COMPLETION REPORT — AI Pattern Intelligence: The Cut Advisor (2026-07-07)

**Status: ✅ PHASE 4 COMPLETE — design first, then one coherent milestone,
as ordered. STOPPED. Phase 5 (Factory Integration & Production Readiness)
will NOT start without explicit owner approval.**

Companions: [P4_DESIGN](P4_DESIGN.md) (the 9 answers) ·
[P4_ENGINEERING_REVIEW](P4_ENGINEERING_REVIEW.md) ·
[P4_REGRESSION_REPORT](P4_REGRESSION_REPORT.md) ·
[P4_FREEZE_RECOMMENDATION](P4_FREEZE_RECOMMENDATION.md) ·
[P5_READINESS_REPORT](P5_READINESS_REPORT.md)

## 1. What shipped — one coherent assistant

**The Cut Advisor** (`/patterns/advisor/`): a cutting master picks a
product (optional fabric width) and receives, on one page:

- **Best marker** — ranked by RECORDED REALITY (avg m/100, honest n);
  **proven beats theory, always** — a spectacular theoretical number can
  never outrank one real recorded outcome.
- **Expected fabric saving** vs *current practice* (the marker the factory
  actually uses most), in m/100 and % — or the honest "you already cut
  with the best-proven marker".
- **Confidence** — component chips (evidence_depth · recency ·
  consistency · width_match) + weakest-component composite; display-only,
  the page says "the human decides".
- **Why** — evidence lines: recorded numbers, n, dates, usage counts,
  width match, geometry trust grades (P2 provenance) — every claim
  traceable.
- **Alternatives** — next-best proven markers, then promising-but-unproven
  generated ones explicitly labeled **UNTESTED — theory only**.
- **Width advice** — best proven consumption per width band.
- **Ratio evidence** — the ratios the winning markers actually ran
  (reported, never invented).
- **The decision spine** — "Record suggestion" freezes the exact shown
  snapshot (evidence included) as an append-only `SuggestionEvent`; a
  human then records the ONE-SHOT verdict (accept / accept-with-changes /
  reject+reason). **Nothing auto-decides — constitutionally.**
- **Suggestion history** — the factory's decision memory, append-only.

## 2. The 9 design questions — answered and implemented

See [P4_DESIGN](P4_DESIGN.md). Headlines: problems = evidence at decision
time; human-only = ALL production decisions (Advisor adds zero production
write paths); **new models = NONE** (SuggestionEvent, reserved since 2A,
gained only a one-shot append-only guard); intelligence lives in
**`advisor_service` (READ-ONLY, SELECT-only test-proven)** + 
**`suggestion_service` (single writer of the spine, I-1)**; learning =
**re-derivation from a growing fact base** — every new outcome shifts
tomorrow's ranking automatically, no stored scores, no jobs, no drift.

## 3. Data consumed (all of it, read-only)

P1 usage/outcomes via the ONE math home (get_marker_summary /
derive_metrics) · marker origins/status/width bands/ratios · P2 confirmed
geometry trust grades (provenance panel) · P3 candidate theory metrics +
benchmark evidence · products/pieces/sizes/fabric groups.

## 4. Live browser proof (screenshots archived)

LOWER: **"Best marker: MRK-000002 · 96.00 m/100 recorded · n=1 · 20/100
confidence"** (evidence_depth 0.2 honestly caps the composite — one
outcome is thin evidence and the Advisor says so) · geometry-trust line
("1 confirmed piece — measured 1") · "You already cut with the best-proven
marker" · **MRK-000003 listed UNTESTED — theory only · 2.53 (theory)** ·
suggestion #1 recorded via UI → **Accepted** decision recorded (decider +
timestamp in history) · 3-PATTI shows the honest empty state ("No proven
facts yet… record outcomes to create evidence"). Mobile @390 + desktop:
`p4_advisor_{desktop,390}`, `p4_advisor_decided_desktop`,
`p4_advisor_nofacts_390`.

## 5. Test summary — patterns_ai **166/166** (+19 P4)

Ranking honesty: proven beats spectacular theory · reality orders by
m/100 with n/recency tie-breaks · saving math vs most-used baseline
(20.00 m/100 = 20.00% pinned) · already-best honesty · width scoping
(exact band wins; honest fallback flag when nothing matches) · width-band
advice table · no-facts honesty · confidence components (n=5 ⇒ depth 1.0;
identical outcomes ⇒ consistency 1.0) · **advisor_service SELECT-only
(query-capture)** · offer payload JSON-safe with schema_version.
Decision spine: offer→one-shot decide · reject needs reason ·
worker/permission walls · non-human outcomes refused · rows guarded
(save/delete refuse). Views: 403/302 sweep, tampered ids 404, page
renders evidence + honesty language, offer+decide through the UI,
reject-without-reason stays offered, worker POST changes nothing.

## 6. Honest limitations

- Confidence components are fixed, transparent heuristics (documented
  thresholds) — deliberately NOT statistical learning; D10 (local LLM /
  learned models) stays off until the owner opens that door via ADR.
- Ratio advice reports evidence; it does not search ratio space
  (a future P3-engine sweep could feed it).
- Cloth-roll stock integration (recommend widths you actually have) is a
  named future lever — advisor reads pattern-era data only in P4.
- With n=1 data the composite reads low by design — the cure is recorded
  outcomes, and the page says exactly that.

## 7. What P5 stands on

A complete propose→human-decide→reality-scores loop with its decision
memory; every advisory number derived from facts that P5's factory
integration (cut-planning surfaces, rollout, runbooks) can trust.
