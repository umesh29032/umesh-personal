# DOCUMENTATION INDEX — every ACTIVE document, one place (2026-06-12)

> **Lost? → [START_HERE.md](START_HERE.md)** — the one front door; it routes you
> by who you are. This index is the full catalogue; START_HERE is the short path.
> Archived material (superseded reviews/audits/plans, each with a superseded-by
> banner): [archive/](archive/).

## Entry points (one front door, then specialised maps)
| Doc | What |
|---|---|
| [START_HERE.md](START_HERE.md) | **THE front door** — routes new dev / owner / AI agent to exactly what to read |
| [PROJECT_KNOWLEDGE_MAP.md](PROJECT_KNOWLEDGE_MAP.md) | **the one overview** — business→architecture→DB→code (canonical big picture) |
| [LEARNING_2_0/PROJECT_BRAIN/](LEARNING_2_0/PROJECT_BRAIN/README.md) | **fast-answer nav** — feature/search/debugging indexes + decision graph + change-history |
| [LEARNING_2_0/PROJECT_ATLAS.md](LEARNING_2_0/PROJECT_ATLAS.md) | **PKALS index** — section-index for docs/LEARNING_2_0 (not an overview; points into the subdirs) |
| [LEARNING_2_0/AI_AGENT_GUIDE/](LEARNING_2_0/AI_AGENT_GUIDE/README.md) | **AI-agent entry** — read-4-files + canonical lookup + never-modify (token reduction) |
| [LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/](LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/README.md) | **PKALS-LIVE** — drift=bug; change-impact + ownership matrices, agent workflow, drift prevention |
| [LEARNING_PATH.md](LEARNING_PATH.md) | ordered learning route (dev + owner) |
| [LEARNING/](LEARNING/README.md) | topic lessons (Django, locks, truths, costing…) |
| [apps/](apps/README.md) | per-app file-by-file developer guides (8 apps) |
| [../GLOSSARY.md](../GLOSSARY.md) | domain terms + core ER |
| [../CLAUDE.md](../CLAUDE.md) | working rules (incl. rule 11 mobile-first) |

## Locked decisions
| Doc | Scope |
|---|---|
| [adr/0001–0010](adr/) | the ten ADRs (see KNOWLEDGE_MAP §9 for one-liners) |
| [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md) | worker truth + settlement (V2-1→V2-3 BUILT) |
| [R1_STAGE_DOMAIN_REVIEW.md](R1_STAGE_DOMAIN_REVIEW.md) | Stage Contract, archetypes, scan seam |
| [REQUIREMENT_REVIEW_STAGE_TRACKING.md](REQUIREMENT_REVIEW_STAGE_TRACKING.md) | Tracking Mode TM-1/TM-2 + C-TM |
| [ERP_MASTER_CONTEXT.md](ERP_MASTER_CONTEXT.md) | owner's vision input |

## Live operations & planning
| Doc | What |
|---|---|
| [ROADMAP_REVIEW_POST_C1_2026_06_11.md](ROADMAP_REVIEW_POST_C1_2026_06_11.md) | THE roadmap (11 phases × 10 dims) |
| [PENDING_BACKLOG.md](PENDING_BACKLOG.md) | EVERY open item, one place (deploy decisions → soak-gated → phases → parked debt) |
| [ARCH_READINESS_REVIEW_2026_06_12.md](ARCH_READINESS_REVIEW_2026_06_12.md) | deployment-gate validation (archives post-soak) |
| [SOAK_TRACKER.md](SOAK_TRACKER.md) | soak evidence log |
| [../deploy/README.md](../deploy/README.md) | deployment runbook (compose/Caddy/backups/rollback) |
| [REMEDIATION_PLAN.md](REMEDIATION_PLAN.md) + [TARGET_ARCHITECTURE.md](TARGET_ARCHITECTURE.md) | parked structural backlog (phases 4–13) |
| [archive/audits/DOC_AUDIT_2026_06_12.md](archive/audits/DOC_AUDIT_2026_06_12.md) | the consolidation audit — **archived** (its plan has been executed); history only |
| [archive/reviews/](archive/reviews/) | PKALS review cycle — hostile review, scorecards, H1–H4 fix record, Phase-2 review + longevity hardening, self-review, build log (WORK_LOG). **Archived 2026-06-13** = history, not current. |

## System reference
| Doc | What |
|---|---|
| [../SYSTEM_DESIGN.md](../SYSTEM_DESIGN.md) | full current-built design (V2 wins on conflict) |
| [../UI_COMPONENTS.md](../UI_COMPONENTS.md) | UI vocabulary (money-family canon + production patterns) |
| [../ABOUT_THIS_PROJECT.md](../ABOUT_THIS_PROJECT.md) | why + learning map |
| [../README.md](../README.md) · [../CHANGELOG.md](../CHANGELOG.md) | repo front door |

## Subsystems (docs/production/, docs/tracking/)
OVERVIEW · PRODUCTION_APP · STAGE_FLOW · LAYERING_STAGE · CUTTING_PATTERN ·
BARCODE_GENERATION · RAW_MATERIALS · TRACKING · RBAC · MIGRATIONS ·
[tracking/EXPORTS.md](tracking/EXPORTS.md) · [PAGES/](PAGES/) (per-page contracts).
Flow docs: [LEARNING_2_0/DATA_FLOWS/](LEARNING_2_0/DATA_FLOWS/README.md) (write-path)
+ [LEARNING_2_0/REQUEST_JOURNEYS/](LEARNING_2_0/REQUEST_JOURNEYS/README.md) (call-chain).

## App guides (code-adjacent, dual-register) — deep file maps: [apps/](apps/README.md)
[accounts](../config/accounts/README.md) · [production](../config/production/README.md)
· [expense](../config/expense/README.md) · [inventory](../config/inventory/README.md)
· [raw_materials](../config/raw_materials/README.md) · [tracking](../config/tracking/README.md)
· [storefront](../config/storefront/README.md) · [core](../config/core/README.md)
