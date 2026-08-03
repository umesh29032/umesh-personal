---
id: docs-ai-pattern-intelligence-doc-cleanup-report
type: receipt
status: active
owner: append-only
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# DOCUMENTATION CLEANUP REPORT (2026-07-07)

**51 historical files moved to `docs/archive/patterns_ai_enterprise_era/`
(plain moves — repo is pre-checkpoint, nothing was under version
control yet; NOTHING deleted). The main docs location now holds only
what defines the current product.**

## ACTIVE (docs/AI_PATTERN_INTELLIGENCE/ — 15 files + 10 ADRs)

| File | Why active |
|---|---|
| PRODUCT_VISION_V2.md | 🔒 the source of truth |
| ROADMAP_V2.md | the only active roadmap (Phase 6 pending) |
| PRODUCT_INTEGRATION_DESIGN.md | 🔒 permanent ownership/integration ruling (new) |
| PHASE4_WORKSPACE_DESIGN.md / PHASE5_OPTIMIZE_DESIGN.md | behavior contracts of the frozen editor + optimizer (rules 1–10 live here) |
| PHASE4_COMPLETION_REPORT.md / PHASE5_COMPLETION_REPORT.md + M1–M4 reports | freeze receipts of the CURRENT product's phases (limitations + proof) |
| P2_GEOMETRY_PIPELINE.md | the canonical geometry payload SPEC (any tool, any language) |
| D7_VALIDATION_PROTOCOL.md | the standing physical-accuracy gate (blank until measured) |
| P5_DEPLOYMENT_RUNBOOK.md | how to deploy/operate the tool (compute venv, node, crons, backup) |
| ADR-A, C, D, D2, D3, E, F, G, H + pack certification | architecture that GOVERNS running code (nesting engine, geometry format, marker lifecycle, grain, provenance, metrology, isolation, media, boundary) |
| DOC_CLEANUP_REPORT.md | this file |

## ARCHIVED (docs/archive/patterns_ai_enterprise_era/ — 51 files)

Historical reference, superseded framing, kept intact:
- Enterprise vision chain: 01_RESEARCH · 02_DRAFT · 03_PLATFORM_BLUEPRINT ·
  04_HOSTILE_REVIEW · 05_BLUEPRINT_V2 · 06_BLUEPRINT_V3_FINAL ·
  AI_PATTERN_INTELLIGENCE_KICKOFF (all superseded by PRODUCT_VISION_V2).
- Enterprise planning: IMPLEMENTATION_MASTER_PLAN (+certification),
  IMPLEMENTATION_READINESS report+certification, PHASE_1/2/3 (old
  numbering) completion reports.
- Era receipts of the old direction: P0 report · P1 block reports
  (×10) + P1 final/engineering/regression/freeze · P2 receipts
  (completion/design/readiness/regression/engineering) · P3 package
  (completion/engineering/regression/freeze) · P4 package (design/
  completion/engineering/regression/freeze/readiness — the ADVISOR era) ·
  P5 enterprise package (design/completion/engineering/regression/
  freeze/readiness/ROLLOUT_GUIDE — the Insights/integration era).
- ADR-B-background-jobs (worker never built; off the roadmap).

Note: cross-links inside archived files may point at moved siblings —
accepted for historical documents (they archive together as one era).

## OBSOLETE (completely replaced, still archived — not deleted)
The blueprint/kickoff/master-plan chain (superseded by VISION_V2 +
ROADMAP_V2) and the P4-advisor / P5-insights packages (describe surfaces
now off-roadmap). Classified obsolete-in-framing, retained as history.

## DUPLICATES
None found — each file is a distinct artifact.

## SAFE TO REMOVE
**None recommended.** Every archived file documents a real decision or
delivered work; storage cost is trivial. (If the owner ever wants
removal, the blueprint drafts 01/02/04/05 are the least-referenced
candidates.)

## Index
DOCUMENTATION_INDEX's pattern row now points at the ACTIVE set with one
archive pointer (historical chain preserved inside the archive folder).
