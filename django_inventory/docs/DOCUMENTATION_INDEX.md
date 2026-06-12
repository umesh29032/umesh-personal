# DOCUMENTATION INDEX — every ACTIVE document, one place (2026-06-12)

> Start here if lost. New? → [PROJECT_KNOWLEDGE_MAP.md](PROJECT_KNOWLEDGE_MAP.md)
> then [LEARNING_PATH.md](LEARNING_PATH.md). Archived material (superseded
> reviews/audits/plans, each with a superseded-by banner): [archive/](archive/).

## Entry points
| Doc | What |
|---|---|
| [PROJECT_KNOWLEDGE_MAP.md](PROJECT_KNOWLEDGE_MAP.md) | **first read** — business→architecture→DB→code |
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
| [DOC_AUDIT_2026_06_12.md](DOC_AUDIT_2026_06_12.md) | this consolidation's audit/classification |

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
[tracking/EXPORTS.md](tracking/EXPORTS.md) · [PAGES/](PAGES/) · [FLOWS/](FLOWS/)

## App guides (code-adjacent, dual-register) — deep file maps: [apps/](apps/README.md)
[accounts](../config/accounts/README.md) · [production](../config/production/README.md)
· [expense](../config/expense/README.md) · [inventory](../config/inventory/README.md)
· [raw_materials](../config/raw_materials/README.md) · [tracking](../config/tracking/README.md)
· [storefront](../config/storefront/README.md) · [core](../config/core/README.md)
