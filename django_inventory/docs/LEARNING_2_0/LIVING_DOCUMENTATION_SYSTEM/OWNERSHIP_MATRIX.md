# DOCUMENTATION OWNERSHIP MATRIX

## TL;DR
Every doc has an OWNER concept + an UPDATE TRIGGER. "Owner" = the code/decision
whose change forces the doc's update (this is a personal project — owner = Umesh
+ whichever agent makes the change; the point is the TRIGGER).

| Doc | Owner concept | Update trigger (event) |
|---|---|---|
| ADR-0001..0010 | locked decisions | only a NEW superseding ADR (never edit silently) |
| ARCHITECTURE_V2 | worker-truth + settlement design | any WST/WSC/settlement/era change |
| R1_STAGE_DOMAIN_REVIEW | stage contract/archetypes | new stage archetype / scan-seam change |
| REQUIREMENT_REVIEW_STAGE_TRACKING | Tracking Mode | TM-1/TM-2 build, C-TM change |
| config/<app>/README | app business view | app's models/services/flows change |
| docs/apps/<app>/GUIDE | app file map | files added/renamed in the app |
| LEARNING_2_0/APPS/<app>/* | app flow/request/file map | same as GUIDE + URL changes |
| CHOKEPOINTS/<svc> | a single-writer service | that service's logic/locks/writes change |
| REQUEST_JOURNEYS/<flow> | a workflow's call chain | URL/view/form/service/model/template in that flow change |
| DATA_FLOWS/<flow> | a write-path | the flow's validation/writes change |
| DATABASE_GUIDE/<model> | a model | the model's fields/FKs/writers/readers change |
| DJANGO_GUIDE/<topic> | a Django pattern as used here | the pattern's project usage changes |
| ARCHITECTURE_EXPLAINED / VALIDATION | the "why" | a design decision changes (→ new ADR first) |
| PROJECT_KNOWLEDGE_MAP | whole-system summary | any structural change (apps/flows/phases) |
| AI_AGENT_GUIDE | agent navigation | new canonical doc / new chokepoint / boundary change |
| URL_ATLAS | all routes | any urls.py change |
| COVERAGE_REPORT | measurable coverage | any new URL/model/service/doc |
| PENDING_BACKLOG / ROADMAP | open work | phase ships / new phase |
| CLAUDE.md | working rules | a new standing rule |
| CHANGE_IMPACT_MATRIX future-phase detail | per-phase PKALS doc work (TM-1, MissingPiece, Alter, G1–G7) | the phase ships → execute its row, then drop "future placeholder" status |
| MissingPiece docs (when built) | the MissingPiece module | MissingPieceCase model/service/flow ships (see CHANGE_IMPACT_MATRIX row) |
| Alter/Rework docs (when built) | the Alter module | AlterCase + rework-pay (ADR-0010 §4) ships |
| G1–G7 growth docs (when built) | each growth phase | commerce/orders/SKU/stock/variance/planning ships (ADR-0008/0009/0010 fences) |

Worked examples:
- **WorkerStageTask changes** → ARCHITECTURE_V2 + CHOKEPOINTS/worker_task_service
 + DATABASE_GUIDE/worker_stage_task + REQUEST_JOURNEYS/worker_reporting.
- **Settlement changes** → ADR-0005/0007 + ARCHITECTURE_V2 §11 +
 REQUEST_JOURNEYS/settlement_finalize + CHOKEPOINTS/adda_settlement_service +
 KNOWLEDGE_MAP §4.
