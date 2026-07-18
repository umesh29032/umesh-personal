---
id: l2-living-documentation-system-ownership-matrix
type: topic-canonical
status: active
owner: handwritten
scope: documentation system (PKALS-LIVE)
anchors: —
verified: 2026-07-13
---

# DOCUMENTATION OWNERSHIP MATRIX

## TL;DR
Every doc has an OWNER concept + an UPDATE TRIGGER. "Owner" = the code/decision
whose change forces the doc's update (this is a personal project — owner = Umesh
+ whichever agent makes the change; the point is the TRIGGER).

| Doc | Owner concept | Update trigger (event) |
|---|---|---|
| ADR-0001..0011 | locked decisions | only a NEW superseding ADR (never edit silently) |
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
| docs/campaign_contracts/* | campaign procedure (frozen contracts + framework) | ONLY Appendix-A Design-Record fills + dated amendments at each contract's own mechanism (FFD-B family row, 2026-07-18) |
| docs/*_LOG.md | per-phase evidence (append-only) | that phase's sub-phase closes append sections; never rewritten |
| docs/*_2026_* | dated receipts/audits/reviews (append-only) | never edited; superseded via banner + archive |
| docs/*_STATUS.md | live campaign/stream state anchors | every sub-phase close updates its anchor |
| docs/AI_PATTERN_INTELLIGENCE/* | the pattern-tool doc set (visions/designs/ADRs/receipts) | patterns_ai code or roadmap changes; its ADRs only via new superseding ADRs |
| docs/pkals_v2/* | the PKALS v2 design set | knowledge-pipeline (P8/P9/P14) changes |
| docs/audit_phases/* | audit-phase receipts (append-only) | never edited |
| docs/production/* + docs/tracking/* | subsystem canonicals | the subsystem's models/services/flows change |
| docs/LEARNING/* | numbered lessons | the illustrated pattern's project usage changes |
| docs/PAGES/* | per-page contracts | that page's behavior changes |
| docs/*VISION*.md + docs/RELEASE_CERTIFICATION_PROGRAM.md | owner-approved vision/program docs | ONLY owner-approved revisions (supersede-with-banner) |
| ABOUT_THIS_PROJECT / CHANGELOG / GLOSSARY / SYSTEM_DESIGN / UI_COMPONENTS / README | root front-door canonicals | structural/system changes per each doc's own header rules |
| docs/DOC_STANDARDS.md + docs/knowledge_graph.json + docs/features/* | the KOS pipeline set (standard=frozen; graph+cards=generated) | standard via §20 amendments; graph/cards ONLY via P8 build/P9 regeneration |
| docs/DOCUMENTATION_INDEX.md + docs/START_HERE.md + docs/apps/* | navigation + file maps | any new/renamed doc or code file (U6 same-session) |
| MissingPiece docs (when built) | the MissingPiece module | MissingPieceCase model/service/flow ships (see CHANGE_IMPACT_MATRIX row) |
| docs/features/** (⚙️ generated layer, Phase 9) | knowledge_graph.json + scripts/doc_templates (ownership class `generated`) | graph rebuild or template version bump ⇒ regenerate the WHOLE tree (`env/bin/python scripts/generate_docs.py --out docs/features`); NEVER hand-edit — fix source → rebuild graph → regenerate |
| Alter/Rework docs (when built) | the Alter module | AlterCase + rework-pay (ADR-0010 §4) ships |
| G1–G7 growth docs (when built) | each growth phase | commerce/orders/SKU/stock/variance/planning ships (ADR-0008/0009/0010 fences) |

### Families added 2026-07-13 (Phase-7 DOCCLEAN-B, F-C-01 — extend-not-replace; triggers mirror existing conventions, no new ownership invented)

| Doc / family | Owner concept | Update trigger (event) |
|---|---|---|
| PDD (PRODUCT_DESIGN_DOCUMENT) | 🔒 product/business truth | owner-approved PDD revision or new ADR only (frozen; amendments register at its top) |
| MANUFACTURING_V1_FREEZE · FACTORY_OPERATIONS_MASTER · PRE_S1_DESIGN_ADDENDUM · REQUIREMENT_REVIEW_STAGE_TRACKING | 🔒 frozen truth-locks | owner ruling / new ADR only (FOM: in-body owner ruling per its change control, DOC_STANDARDS §11 A1) |
| DOC_STANDARDS | the documentation constitution | owner-gated §20 Amendments register only (frozen-v1) |
| KOS_TARGET_VISION | long-term KOS end-state (draft) | owner edits; binds nothing until a phase -0 gate adopts it |
| machines app docs (config/machines/README + apps/machines/GUIDE) | machines app | machine models/services/possession-window logic change |
| patterns_ai app docs (config/patterns_ai/README + apps/patterns_ai/GUIDE + AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS) | pattern layout tool | patterns_ai models/services change; PLATFORM_STATUS §8a = state doc of record |
| deploy/README | the deployment runbook | infra/deploy-procedure change (PHASE_19 refresh venue) |
| campaign contracts (campaign_contracts/PHASE_NN) | frozen execution contracts | dated amendment / designated fill sections only (never rewrite) |
| campaign evidence (DEPLOYMENT_CAMPAIGN_STATUS · *_CERTIFICATION · CONFIRMED_FINDINGS_LEDGER · DOCUMENT_DISCOVERY_REPORT · DOCUMENT_CLEANUP_LOG) | append-only campaign record | each sub-phase close appends; closed sections never edited |
| AI_PATTERN_INTELLIGENCE receipts (archive-bound) | historical PI-era records | none — archived in Phase-7 DOCCLEAN-D (history only) |

Worked examples:
- **WorkerStageTask changes** → ARCHITECTURE_V2 + CHOKEPOINTS/worker_task_service
 + DATABASE_GUIDE/worker_stage_task + REQUEST_JOURNEYS/worker_reporting.
- **Settlement changes** → ADR-0005/0007 + ARCHITECTURE_V2 §11 +
 REQUEST_JOURNEYS/settlement_finalize + CHOKEPOINTS/adda_settlement_service +
 KNOWLEDGE_MAP §4.
