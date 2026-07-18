# P4 DESIGN — The Cut Advisor (AI Pattern Intelligence era) · 2026-07-07

**One coherent assistant, not isolated features. Design of record for the
P4 milestone; governed by Blueprint V3 Era-2, ADR pack, P1–P3 freezes.**

## 0. The one-sentence architecture

The Advisor is a **pure read-model brain** over the frozen fact streams
(P1 usage/outcomes, P2 geometry/trust, P3 candidates/benchmarks) that
**ranks and explains** cut-planning options, plus **one append-only write**:
the `SuggestionEvent` decision spine that records what was proposed and
what the human decided. No engine, no training, no stored scores.

## 1. What problems does the AI solve?

Cut-planning today runs on memory: *which marker was best for LOWER at
this width? what did we actually consume last month? is the new generated
marker proven yet?* The system already holds the answers as facts; nobody
can see them in one place at decision time. The Advisor solves exactly
that: **evidence-backed answers at the moment of choosing marker, width
and ratio for a product** — and records the human's decision so the
factory's judgment itself becomes knowledge.

## 2. Which decisions remain human-only? (ALL of them)

Choosing the marker/width/ratio for real cutting · recording usage ·
recording outcomes · promoting candidates · confirming geometry ·
void/retire/reject anything. The Advisor adds ZERO write paths into
production truth. Its only write is the suggestion record itself, and
even that row's outcome field can only be set by a human decision
(accepted / accepted-with-modifications / rejected+reason). Nothing
auto-decides, nothing auto-applies — constitutional (Era-2 stance).

## 3. Which recommendations does it generate?

For a chosen product (optional width/ratio context):

1. **Best marker** — ranked by RECORDED REALITY (actual avg m/100,
   honest n) among usable markers; width-compatible first.
2. **Best fabric width** — which width band's best marker consumes least,
   with the evidence per band.
3. **Ratio evidence** — which ratios the winning markers actually ran
   (the Advisor reports ratios with evidence; it does not invent ratios).
4. **Better alternatives** — next-best proven markers with deltas, PLUS
   promising-but-unproven ones (generated markers with only THEORY
   numbers) explicitly labeled *untested — trial to prove*.
5. **Why** — every recommendation carries its evidence rows: marker refs,
   n, outcome dates, numbers, benchmark verdicts, geometry trust grades.
6. **Expected fabric saving** — best vs *current practice* (the product's
   most-used marker), in m/100 and % — and the honest special case
   "you already use the best" when true.
7. **Confidence** — component-visible, weakest-component composite
   (same visual law as P2 gates / P3 verification).

## 4. Which existing data does it consume? (read-only, all of it)

| Source (era) | Used for |
|---|---|
| MarkerUsage/MarkerOutcome + derive_metrics (P1) | reality scores (avg m/100, honest n, last-used recency) |
| Yield Board machinery (P1) | the SAME derivation path — no second math home |
| Marker origin/status/width_band/ratio (P1) | eligibility, width grouping, ratio evidence |
| CaptureAsset→mat chain (P2, via markers'/geometry provenance) | provenance panel |
| PieceSizeGeometry trust grades + confirmed versions (P2) | geometry-trust context per product |
| GeneratedMarkerCandidate metrics + verification (P3) | THEORY numbers for unproven generated markers |
| Benchmark evidence in MarkerTransitionEvent (P3) | "beat the baseline at promotion" context |
| Product / PatternPiece / fabric_group / ProductSize | scoping, ratio labels, piece counts |

## 5. What new models are required? **NONE.**

`SuggestionEvent` (2A schema, product-homed, outcome+reason constrained,
decided_by/decided_at audit) is exactly the landing table Era-2 reserved.
v1 uses `source='advisor:v1'` and a schema_version'd payload holding the
full recommendation snapshot. One hardening (additive, correctness-class):
a save/delete guard making the row append-only with a ONE-SHOT
offered→decided transition — the same guard pattern as
MarkerTransitionEvent/GeometryExtraction. No new tables until a consumer
needs one (F3 discipline).

## 6. Which services own the intelligence?

- **`advisor_service` — READ-ONLY** (the brain): eligibility, scoring,
  ranking, width grouping, saving math, confidence components, evidence
  assembly. SELECT-only test-proven, like every read model here. Reuses
  `marker_query_service.get_marker_summary` (one math home) and P3's
  `derive_candidate_metrics`.
- **`suggestion_service` — SINGLE WRITER for SuggestionEvent** (I-1):
  `record_offer(user, product, payload)` → offered row (the shown
  snapshot, frozen); `decide(user, event, outcome, reason='',
  modified_note='')` → one-shot human decision. Refusals: deciding twice,
  rejecting without reason, deciding someone else's product-mismatched
  payload — all recorded rules.

## 7. Which UI surfaces?

- **`/patterns/advisor/` — the Cut Advisor page** (management-gated,
  mobile-first): product select (+ optional width filter) → hero card
  (best marker + evidence + confidence + saving) · width advice card ·
  alternatives table (proven, then labeled-THEORY untested) · ratio
  evidence · provenance/trust panel · **decision bar** (Accept /
  Accept-with-changes / Reject+reason) writing the SuggestionEvent.
- **Suggestion history panel** on the same page (append-only list:
  offered/decided, by whom, verdicts) — the factory's decision memory.
- Nav links from home + yield board. No other surfaces in P4 (one
  coherent assistant, one door).

## 8. How are confidence and evidence presented?

The established house language (P2/P3): component chips + a
weakest-component composite 0–100, display-only, never an acceptance
authority. Components: `evidence_depth` (n outcomes on the winner),
`recency` (days since last outcome), `consistency` (spread of the
winner's outcomes), `width_match` (exact band vs fallback). Every number
traceable: the why-list names markers, n, dates, values; THEORY numbers
always carry the label; "no facts yet" stays an honest answer.

## 9. How does it learn continuously without violating the constitution?

**The assistant never stores what it learned — it re-derives from a
growing fact base.** Every new usage/outcome row (including outcomes on
promoted generated markers) changes tomorrow's ranking arithmetic
automatically, because rankings are computed AT READ from the same
derive_metrics chain (F6). The recorded SuggestionEvents add the second
loop: what was proposed vs what humans chose vs what reality then did —
append-only fuel for future eras (and P5 reporting), never a trained
parameter store. No jobs, no caches, no drift: the knowledge base IS the
model. (If a future era ever wants statistical learning or a local LLM
(D10), it enters as a NEW ADR with vendored artifacts — this design
neither needs nor forecloses it.)

## Ranking policy (the honesty core, spelled out)

1. Eligible = product's markers in usable status, width-compatible
   (exact band; ±1 band labeled fallback; all bands when no width given).
2. **Proven beats theory:** markers WITH recorded reality (n ≥ 1) rank
   above any theory-only marker, always. Reality ranks by avg m/100
   ascending; ties → higher n, then more recent.
3. Theory-only markers (promoted candidates without outcomes) appear as
   *untested* alternatives with their theoretical number + the label —
   never as "best marker".
4. Saving = current-practice baseline (most-used marker by non-voided
   usage count; tie → most recent) minus best, shown in m/100 and %;
   "already best" stated when delta ≤ 0.
5. No eligible facts at all → the Advisor says exactly that and points
   to what would create facts (record outcomes; trial the untested).
