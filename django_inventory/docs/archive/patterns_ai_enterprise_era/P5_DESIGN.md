# P5 DESIGN — Factory Integration & Production Readiness (2026-07-07)

**The final planned core phase. Governed by all prior freezes; additive
only; contradiction ⇒ STOP.**

## 1. Workflow integration — the boundary ruling (ADR-H applied)

**Sanctioned mechanism: project-level composition, python-import-free.**
Production templates may reference `patterns_ai:` URL names exactly as
they already reference `expense:` and `tracking:` (precedent in
`adda_detail.html`; the sidebar rule referencing `patterns_ai:home` set
it earlier). The import-direction walls (source-scan + import-linter)
stay the law: **no production PYTHON ever imports patterns_ai**; no
patterns_ai business data is computed inside production views. Links,
not embeds — the Advisor keeps its one door.

Integration points (management-gated, minimal):
- **Adda detail (the cut-planning hub):** a "Pattern Intelligence" action
  row — Cut Advisor (prefilled with the Adda's product), Yield Board,
  Pattern Library. The decision loop already lands back in patterns_ai
  (usage records against the Adda since P1).
- Nothing else in P5: one decision point done properly beats five links
  scattered.

## 2. Management Intelligence — the Insights layer

**`intelligence_service` — READ-ONLY (SELECT-only test-walled), composing
EXISTING derive paths only:** advisor_service.recommend (saving/practice),
marker_query_service summaries (yield truth), SuggestionEvent counts
(acceptance), P3 candidate metrics (theory), P2 trust grades. No new
math homes, no stored aggregates, no jobs.

Surface: **`/patterns/insights/` — one executive dashboard** (mgmt-gated):
- Factory KPI chips: markers by origin, outcomes recorded, confirmed
  pieces by trust grade, generation runs/promotions, suggestion
  acceptance rate.
- Per-product table: best-proven m/100 (n) · current practice ·
  **potential saving** (labeled POTENTIAL — per 100 garments; never a
  fantasy ROI multiplication) · untested count.
- Manual vs Generated panel: proven averages + counts by origin.
- Suggestion spine panel: offered/accepted/modified/rejected + for each
  ACCEPTED suggestion, the shown-best marker's outcomes SINCE the
  decision (suggestion vs actual, derived live).
- Recent-activity trend: outcomes per month (simple buckets, CSS bars).
Every number explainable to fact rows; honest-NULL everywhere.

## 3. Production readiness (code + runbook)

- **`manage.py patterns_ai_health`** — the ops truth command: compute
  venv + tool inventory, node presence, engine smoke flags, media root
  writability, integrity-sweep summary counts, knowledge-row census,
  pending (offered) suggestions. Exit code 0/1; cron-friendly output.
- **compute_bridge hardening:** per-call timeout override (nest runs with
  its timebox + buffer instead of the flat 120 s) — correctness-class fix.
- **[P5_DEPLOYMENT_RUNBOOK](P5_DEPLOYMENT_RUNBOOK.md):** install (Django
  venv untouched · compute venv from lockfile · node 18 · migrations ·
  sidebar seed), crons (media sweep + health), backup/restore
  (DB + `media/patterns_ai/**/originals/` = knowledge; derived
  regenerable), disaster recovery drill, monitoring/logging map,
  maintenance calendar (ADR-F annual rebuild drill).

## 4. Real factory validation (docs; NOTHING claims accuracy early)

**[D7_VALIDATION_PROTOCOL](D7_VALIDATION_PROTOCOL.md):** mat print +
tape commissioning ritual · phone/lighting/camera checklists · golden-
piece measurement procedure · acceptance criteria · **a BLANK results
addendum template** (tiers get published only when measured — ADR-E law) ·
trust-grade activation policy (photo_calibrated = provisional until D7
passes) · operator validation sign-off.

## 5. Rollout ([P5_ROLLOUT_GUIDE](P5_ROLLOUT_GUIDE.md))

Role mapping (management sees Pattern Intelligence; workers see nothing —
sidebar rule already scopes it) · onboarding sequence · SOPs (capture /
outcome recording / advisor decisions) · 4-week adoption plan ·
production acceptance checklist.

## 6. Hardening pass

Hostile re-read of the whole app with production eyes; fix ONLY
correctness/readiness items (timeout fix above; anything found during the
pass gets fixed + documented). No redesigns of frozen eras.

## 7. Schema impact: **ZERO migrations.** Model pin stays 15.
