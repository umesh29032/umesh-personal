# P5 ENGINEERING REVIEW — production eyes on the whole platform (2026-07-07)

**Method:** hostile re-read of the P5 additions + a production-readiness
sweep across the whole patterns_ai surface (architecture, scalability,
performance, concurrency, deployment, security, maintainability, docs,
debt). Solo review, recorded per the audit-honesty rule. Two
production-class issues were found DURING this phase and fixed + tested
before delivery (recorded honestly below).

## Verdict
**PRODUCTION-READY at factory scale**, with the D7 physical validation as
the explicit, protocol-governed gate before trusting photo-calibrated
dimensions on real fabric. No architectural change recommended.

## 1. Found-and-fixed this phase (correctness/readiness class)
1. **compute_bridge flat 120 s timeout** would have killed nest runs with
   timeboxes ≥ ~90 s → per-call override; generation passes
   timebox + 90 s. (Latent P3 bug surfaced by production eyes.)
2. **Unbounded dashboard scans** over append-only tables (suggestion
   full-scan; all-outcomes trend) → ONE aggregate COUNT query + windowed
   trend + follow-ups limited to the 10 most recent accepted. Dashboards
   must never grow O(history).

## 2. Architecture & boundary
- The integration mechanism is the weakest point BY NATURE and it held:
  three template links, `is_management`-gated, zero python imports —
  P5-local wall test + the standing purity scan + import-linter all
  assert the direction. No production context processor, no shared code.
- intelligence_service composes advisor/query/candidate derive paths —
  ZERO new math homes (grep-verifiable: no arithmetic on fact fields
  outside the established services beyond counts/averages of already-
  derived values).
- Single-writer census (final): marker_service · marker_feedback_service ·
  capture_service · calibration_service · pattern_geometry_service ·
  marker_generation_service · suggestion_service — 7 writers, 15 models,
  I-1 repo-scan green. advisor + intelligence + marker_query = read-only,
  each SELECT-only test-walled.

## 3. Scalability & performance
- Insights = KPI counts (indexed COUNTs) + per-product advisor derivation
  (the pinned O(markers) philosophy) + bounded spine/trend queries.
  Fine to thousands of outcomes; the derived-cache lever (ADR-G
  semantics) stays pre-designed for the day a product holds hundreds of
  markers.
- health command re-hashes all originals — O(media bytes); correct for a
  daily cron at factory scale; runbook notes it.
- Generation remains the only long request (timeboxed, sync by recorded
  scope decision; ADR-B lever).

## 4. Concurrency
Nothing new writes concurrently in P5 (insights read-only; health
read-only + a probe file). All prior locks/one-shots re-verified by the
green suites.

## 5. Security
- New surfaces mgmt-gated (403/302 in tests); insights leaks nothing a
  manager cannot already derive from existing pages.
- Health command is ops-CLI only (no URL).
- Adda links render only under `is_management` (visibility) AND the
  target URLs 403 workers regardless (enforcement) — the standing
  two-layer rule.

## 6. Deployment & ops readiness
Runbook covers install/crons/backup/restore/DR/monitoring/maintenance;
the health command makes "is it deployed right?" a one-liner; the ADR-F
rebuild drill is the annual proof of the offline promise. Django venv
unchanged through five phases — the strongest deployment property the
platform has.

## 7. Documentation
Four living ops docs (runbook, D7 protocol, rollout guide, design) +
per-era packages + GUIDE + pipeline spec + ADRs. The DOCUMENTATION_INDEX
row chains every era. Debt: none blocking.

## 8. Consolidated debt register (platform-wide, final)
| # | Item | Class |
|---|---|---|
| 1 | D7 physical tiers unvalidated (protocol ready, addendum blank) | rollout gate |
| 2 | SAM weights not vendored (honest ladder) | enhancement |
| 3 | on-fold generation (needs fold-edge annotation era) | enhancement |
| 4 | ADR-B async worker | lever when volume demands |
| 5 | holes-aware nesting / deeper search / multi-width sweeps | quality levers |
| 6 | cloth-roll width-stock integration | enhancement |
| 7 | derived-metrics cache | volume lever |
| 8 | views.py mechanical split | cosmetic |
| 9 | validator-twins drift watch (P2) | watch |
| 10 | fixed advisor heuristics thresholds | revisit with data volume |

## 9. Future ADR candidates (unchanged, consolidated)
DB-level append-only hardening (now 5 guarded tables) · ADR-B activation ·
D10 learned-ranking/local-LLM gateway · search-profile ADR · MinIO media
move (ADR-G option).

No redesign recommended. The constitution held through five phases.
