---
id: l2-living-documentation-system-drift-prevention
type: topic-canonical
status: active
owner: handwritten
scope: documentation system (PKALS-LIVE)
anchors: —
verified: 2026-07-13
---

# DRIFT PREVENTION — rules + detection

## TL;DR
Stale docs cost every future reader (human + AI) tokens and risk wrong decisions.
Treat drift as a bug with the same severity as a failing test.

## Rules (never)
- Never leave ARCHITECTURE docs stale after a design change.
- Never leave a REQUEST_JOURNEY stale after its URL/view/service/model changed.
- Never leave AI_AGENT_GUIDE / canonical lookup stale after adding a canonical doc.
- Never leave an app README/GUIDE stale after adding/renaming files.
- Never leave canonical OWNERSHIP unclear — one topic, one canonical (DOCUMENTATION_INDEX).
- Never silently edit an ADR — supersede with a new one.

## Detection (how stale docs get caught)
- **CI doc-accuracy guard** (`core/tests.py:DocAccuracyTests`) — machine-checks
 SYSTEM_DESIGN + PROJECT_KNOWLEDGE_MAP for version/claim drift; FAILS the build.
- **CI PKALS navigation guard** (`core/tests.py:PkalsNavigationGuardTests`, C-1
 hardening) — FAILS the build on: a dangling internal link anywhere in
 LEARNING_2_0 (+ START_HERE), a non-contiguous ADR sequence, a renamed canonical
 chokepoint service, or a broken README→START_HERE→overview front-door chain.
 This automates what used to be a periodic manual link sweep.
- **CHANGE_IMPACT_MATRIX** — the checklist that makes "did I update the docs?"
 mechanical, not memory.
- **COVERAGE_REPORT** — measured numerators vs denominators reveal undocumented areas.
- **Archived = never truth** — every archived file carries a superseded-by banner.

## Escalating a drift
Found a doc that contradicts code? Fix the doc (it's the memory), note it in
WORK_LOG/commit, and if it was a canonical doc, double-check the CHANGE_IMPACT
row that should have caught it.
