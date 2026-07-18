---
id: docs-pkals-release-v1
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# PKALS v1 — RELEASE RECORD

> Released 2026-06-13 on branch `new_flask_app`. PKALS = the project's permanent
> knowledge system (docs/LEARNING_2_0 + the canonical overview/front-door/route +
> the AI manifest + the CI guard). This file is the v1 release reference; the
> living front door is [START_HERE.md](START_HERE.md).

## Scope (what v1 is)
- **Front door:** `docs/START_HERE.md` (routes new-dev / owner / AI agent).
- **Overview (canonical):** `docs/PROJECT_KNOWLEDGE_MAP.md`.
- **Learning route (canonical):** `docs/LEARNING_PATH.md` (sequences `docs/LEARNING/` lessons + the academy).
- **Academy:** `docs/LEARNING_2_0/` (94 md) — ARCHITECTURE_EXPLAINED/VALIDATION,
  CHOKEPOINTS, REQUEST_JOURNEYS, DATA_FLOWS, DATABASE_GUIDE, PROJECT_BRAIN,
  DJANGO_GUIDE, APPS, URL_ATLAS, LIVING_DOCUMENTATION_SYSTEM.
- **AI routing:** `docs/LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json` (machine) + AI_AGENT_GUIDE/README (human).
- **Durability mechanism:** `config/core/tests.py::PkalsNavigationGuardTests` (5 checks) + `DocAccuracyTests` (5 checks), run by `scripts/check.sh`.
- **Out of scope (v2+):** automation layers, online-learning, AI-skill phases, script generation, docs website, architecture changes.

## Architecture
Layered, single-source, guarded:
- **One front door → one overview → leaf** navigation (no competing maps).
- **One canonical per concept**, others link (two-truths, settlement, request-flow,
  eras/lever, costing — each banner-marked; settlement lock-order binding spec = ARCHITECTURE_V2 §11.5).
- **Counts are self-counting lists**, never hard-coded numbers.
- **Three app-doc layers** (intentional, orthogonal): `config/<app>/README` (business) ·
  `docs/apps/<app>/GUIDE` (file-by-file) · `docs/LEARNING_2_0/APPS/<app>/` (nav/flow).
- **Drift defense = CI guard**: a renamed/moved/deleted doc, a non-contiguous ADR
  set, a renamed chokepoint service, a broken front-door chain, or an invalid
  manifest route FAILS the build.

## Maintenance contract (summary; full = LIVING_DOCUMENTATION_SYSTEM/MAINTAINING_PKALS)
- **Must maintain (CI-guarded core):** KNOWLEDGE_MAP, START_HERE, AI_AGENT_GUIDE +
  manifest, ARCHITECTURE_V2 + ADRs, CHOKEPOINTS, CHANGE_IMPACT_MATRIX +
  OWNERSHIP_MATRIX, DOCUMENTATION_INDEX.
- **Optional (verify-on-touch periphery, may lag):** APPS×3, URL_ATLAS,
  COVERAGE_REPORT counts, per-model DATABASE_GUIDE, per-flow DATA_FLOWS/JOURNEYS, DJANGO_GUIDE.
- **Every change:** run CHANGE_IMPACT_MATRIX, update listed docs same session, keep `scripts/check.sh` green (CLAUDE rule 12).

## Future-phase integration rules
When TM-1 / MissingPiece / Alter / G1–G7 / Reporting ship: execute that phase's
row in `LIVING_DOCUMENTATION_SYSTEM/CHANGE_IMPACT_MATRIX.md` (future-phase detail
table) — add the journey/flow/DB page/EXPLAINED-why/PROJECT_BRAIN index rows it
lists, drop its "future placeholder" status, add an AI_AGENT_GUIDE manifest route,
update KNOWLEDGE_MAP §10. New decision ⇒ new ADR first (never edit a locked one).
New entity ⇒ one periphery page first (fan-out cap).

## Known limitations (accepted)
- Prose accuracy is human-reviewed — the guard covers references/counts/navigation, not wording.
- Verify-on-touch periphery may lag code between touches (by design; trust code when in doubt).
- COVERAGE_REPORT is a dated snapshot, not a live contract.
- Quality band ~8.5/10; practical max ~9 (the above are the irreducible ceiling for a solo maintainer).

## Upgrade path to PKALS v2 (when/if pursued — NOT part of v1)
Candidate v2 work, each its own opt-in initiative: (a) automate more of the drift
guard (e.g., presence of TL;DR/confidence footers; manifest↔AI_AGENT_GUIDE table
sync); (b) a generated docs site; (c) AI-skill / script-generation layers; (d)
online-learning expansion; (e) re-evaluate APPS-triplet or EXPLAINED/VALIDATION
merge only if a future review shows real redundancy/drift. v2 must not retro-fit
into the v1 freeze; start it as a fresh, evidence-gated initiative.

### Verification Sources
The 5 release commits (71b9f9bd, 407ee646, 3a02651e, 975b9115, 5f1b77c5);
`scripts/check.sh` GATE ✓ PASS post-commit (501 tests, 71% coverage); 10/10 PKALS
guard checks. Commit base f067daf0, 2026-06-13. Confidence: High.
