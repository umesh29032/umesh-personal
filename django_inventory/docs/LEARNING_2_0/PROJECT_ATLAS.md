# PROJECT ATLAS — the INDEX of the PKALS learning system

> **This is the section-index for PKALS (docs/LEARNING_2_0/), not a project
> overview.** It tells you which PKALS subdir holds what. For the project
> OVERVIEW (business → architecture → database → code) read the one canonical
> map: [../PROJECT_KNOWLEDGE_MAP.md](../PROJECT_KNOWLEDGE_MAP.md). For the single
> front door (routes new dev / owner / AI agent) read
> [../START_HERE.md](../START_HERE.md). Every link below is clickable; each
> points one layer deeper into PKALS.

## 0) PROJECT BRAIN — fastest answers (use first)
[PROJECT_BRAIN/](PROJECT_BRAIN/README.md): [FEATURE_INDEX](PROJECT_BRAIN/FEATURE_INDEX.md)
(feature→code+doc) · [SEARCH_INDEX](PROJECT_BRAIN/SEARCH_INDEX.md) (term→file) ·
[DEBUGGING_INDEX](PROJECT_BRAIN/DEBUGGING_INDEX.md) (symptom→where) ·
[DECISION_GRAPH](PROJECT_BRAIN/DECISION_GRAPH.md) (ADR deps) ·
[CHANGE_HISTORY_MAP](PROJECT_BRAIN/CHANGE_HISTORY_MAP.md) (phase→files). This is
the primary navigation layer for humans AND AI.

## 1) Project / architecture / business / domain overview → NOT here
The overview (what the project is, the layered architecture, the business in one
line, and the two truths that are its heart) lives in ONE canonical place — this
index does not duplicate it:
- **The whole picture:** [../PROJECT_KNOWLEDGE_MAP.md](../PROJECT_KNOWLEDGE_MAP.md)
 — §1 business · §2 request flow · §3 architecture · §4 the two truths · §6 ER · §9 ADRs.
- Full current-state design: [../../SYSTEM_DESIGN.md](../../SYSTEM_DESIGN.md).
 Domain words: [../../GLOSSARY.md](../../GLOSSARY.md). Owner vision: [../ERP_MASTER_CONTEXT.md](../ERP_MASTER_CONTEXT.md).

The rest of this file is the PKALS section-index: where each learning subdir lives.

## 5) App index — code + LEARNING_2_0 map (the table is the source; count not hard-coded)
| App | Owns | Business view | File-by-file | LEARNING_2_0 map |
|---|---|---|---|---|
| production | Adda, stages, worker truth, costing freeze | [README](../../config/production/README.md) | [GUIDE](../apps/production/GUIDE.md) | APPS/production/ (P2) |
| expense | settlement, ledger, advances, payment | [README](../../config/expense/README.md) | [GUIDE](../apps/expense/GUIDE.md) | APPS/expense/ (P2) |
| accounts | identity, RBAC, sidebar | [README](../../config/accounts/README.md) | [GUIDE](../apps/accounts/GUIDE.md) | APPS/accounts/ (P2) |
| raw_materials | cloth stock | [README](../../config/raw_materials/README.md) | [GUIDE](../apps/raw_materials/GUIDE.md) | APPS/raw_materials/ (P2) |
| tracking | history + barcode identity | [README](../../config/tracking/README.md) | [GUIDE](../apps/tracking/GUIDE.md) | APPS/tracking/ (P2) |
| inventory | dashboards + access glue (no tables) | [README](../../config/inventory/README.md) | [GUIDE](../apps/inventory/GUIDE.md) | APPS/inventory/ (P2) |
| storefront | public site (commerce future) | [README](../../config/storefront/README.md) | [GUIDE](../apps/storefront/GUIDE.md) | APPS/storefront/ (P2) |
| core | shared kernel (abstract base, no tables) | [README](../../config/core/README.md) | [GUIDE](../apps/core/GUIDE.md) | APPS/core/ (P2) |

## 6) Data-flow overview
How a row is born + every model + write-flow + ER:
[../LEARNING/02_DATABASE_RELATIONSHIPS.md](../LEARNING/02_DATABASE_RELATIONSHIPS.md).
Per-flow input→validation→writes→constraints: [DATA_FLOWS/](DATA_FLOWS/README.md).

## 7) Request-flow overview
One click's path (browser → middleware → view → service → model → history):
KNOWLEDGE_MAP §2. Full per-workflow journeys with exact files/classes/functions:
[REQUEST_JOURNEYS/](REQUEST_JOURNEYS/README.md). Every URL: [URL_ATLAS.md](URL_ATLAS.md).

## 8) The chokepoints (where the system's integrity lives)
[CHOKEPOINTS/](CHOKEPOINTS/README.md) — the single-writer services (canonical list:
[../PROJECT_KNOWLEDGE_MAP.md](../PROJECT_KNOWLEDGE_MAP.md) §7). Read these
to understand why the system can't be corrupted: worker_task, adda_settlement,
allocation, ledger/payment, cost.

## 8b) Architecture EXPLAINED (the WHY — read early)
[ARCHITECTURE_EXPLAINED/](ARCHITECTURE_EXPLAINED/README.md) — 11 "why does this
exist" teaching files (WorkerStageTask, settlement≠payment, two truths,
append-only, reversals, verified_quantity, eras, open-closed…). For a junior,
read this right after §4.

## 8c) Architecture VALIDATION (senior review) + onboarding
[ARCHITECTURE_VALIDATION/](ARCHITECTURE_VALIDATION/README.md) — decisions +
rejected alternatives (for senior devs). Onboarding route (incl. 7-day pacing):
[../LEARNING_PATH.md](../LEARNING_PATH.md). [COVERAGE_REPORT.md](COVERAGE_REPORT.md)
— measured coverage snapshot.

## 9) Learning path
Ordered route (owner + dev tracks, with do-this-on-dev exercises):
[../LEARNING_PATH.md](../LEARNING_PATH.md). Topic lessons:
[../LEARNING/](../LEARNING/README.md) (Django, locks, truths, costing,
SQL beginner→advanced, online resources). Django-as-used-here:
[DJANGO_GUIDE/](DJANGO_GUIDE/README.md). Models deep: [DATABASE_GUIDE/](DATABASE_GUIDE/README.md).

## 9b) For AI agents (zero-context entry)
[AI_AGENT_GUIDE/](AI_AGENT_GUIDE/README.md) — read-4-files path, canonical-doc
lookup table, never-modify list, safe bug/feature flow. Built so a future Claude
understands the project WITHOUT scanning the repo (token reduction).

## 9c) Living Documentation System (PKALS-LIVE)
[LIVING_DOCUMENTATION_SYSTEM/](LIVING_DOCUMENTATION_SYSTEM/README.md) — drift =
architecture bug. Change-impact matrix (file→docs), ownership matrix, 7-step
agent workflow, drift prevention, Maintaining-PKALS.

## 9d) Coverage
[COVERAGE_REPORT.md](COVERAGE_REPORT.md) (dated coverage snapshot + gap report).
PKALS's review cycle (hostile review, scorecards, hardening, self-review) is
archived under [../archive/reviews/](../archive/reviews/) — history, not current.

## 10) Navigation index (where is X?)
- Every active doc: [../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)
- What's still to build: [../PENDING_BACKLOG.md](../PENDING_BACKLOG.md)
- The roadmap (11 phases): [../ROADMAP_REVIEW_POST_C1_2026_06_11.md](../ROADMAP_REVIEW_POST_C1_2026_06_11.md)
- Working rules (mobile-first, docs-sync): [../../CLAUDE.md](../../CLAUDE.md)
- How PKALS was built (history): [../archive/reviews/WORK_LOG.md](../archive/reviews/WORK_LOG.md)
- History (superseded, never truth): [../archive/](../archive/)

## How to use this atlas
Lost → here. Going deeper on a topic → follow its link down one layer. Touching
code in app X → open APPS/X (P2) + that app's GUIDE + README. Debugging a
workflow → its REQUEST_JOURNEY (exact call chain). Confused why → the ADR.
