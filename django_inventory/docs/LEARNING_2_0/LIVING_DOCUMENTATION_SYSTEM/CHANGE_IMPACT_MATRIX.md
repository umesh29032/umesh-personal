---
id: l2-living-documentation-system-change-impact-matrix
type: topic-canonical
status: active
owner: handwritten
scope: documentation system (PKALS-LIVE)
anchors: —
verified: 2026-07-13
---

# CHANGE IMPACT MATRIX — changed file → docs to review

## TL;DR
Find the file you touched; update the listed docs SAME session. If a listed doc
truly needs no change, say why in your summary. This table is the token-saver:
it tells you exactly where knowledge already lives so you update instead of
rediscover.

| Changed file/area | Docs to review & update |
|---|---|
| `production/services/worker_task_service.py` | ARCHITECTURE_V2 (production truth) · CHOKEPOINTS/worker_task_service · APPS/production/FILE_MAP · REQUEST_JOURNEYS/worker_reporting · ARCHITECTURE_EXPLAINED 01/02/09 · PROJECT_KNOWLEDGE_MAP §3,§7 · config/production/README |
| `expense/services/adda_settlement_service.py` | ADR-0005/0007 · ARCHITECTURE_V2 §11 · CHOKEPOINTS/adda_settlement_service · REQUEST_JOURNEYS/settlement_finalize(+reverse) · ARCHITECTURE_EXPLAINED 03/05/08/10 · KNOWLEDGE_MAP §4,§7 · config/expense/README · AI_AGENT_GUIDE (canonical table) |
| `expense/services/ledger_service.py` | ADR-0002 · CHOKEPOINTS/ledger_and_payment · ARCHITECTURE_EXPLAINED 04/07 · LEARNING/02 · KNOWLEDGE_MAP §4 |
| `expense/services/settlement_service.py` | CHOKEPOINTS/ledger_and_payment · REQUEST_JOURNEYS/payment · ARCHITECTURE_EXPLAINED 05 · config/expense/README |
| `expense/services/allocation_service.py` | ADR-0007 · CHOKEPOINTS/allocation_service · ARCHITECTURE_EXPLAINED 10 · COSTING (LEARNING/07) |
| `production/services/cost_service.py` | ADR-0009 · CHOKEPOINTS/cost_service · LEARNING/07 · costing journey · KNOWLEDGE_MAP §7 |
| `expense/models.py` (ledger/SWA/ADST/PSI) | LEARNING/02 · DATABASE_GUIDE/<model> · CHOKEPOINTS (relevant) · ARCHITECTURE_EXPLAINED (relevant) · APPS/expense/FILE_MAP |
| `production/models/worker_task.py` (WST/WSC) | LEARNING/02 · DATABASE_GUIDE/worker_stage_* · CHOKEPOINTS/worker_task_service · ARCHITECTURE_EXPLAINED 01/02/09 · ARCHITECTURE_V2 |
| `production/models/core.py` (WorkflowStage) | ADR-0009 · cost_service chokepoint · DATABASE_GUIDE/workflow_stage · REQUIREMENT_REVIEW_STAGE_TRACKING (TM-1 field) · flow editor journey |
| `production/models/adda.py` (Adda/SR) | LEARNING/02 · DATABASE_GUIDE/adda · REQUEST_JOURNEYS/adda_creation · KNOWLEDGE_MAP §5,§6 |
| `raw_materials/models.py` / `roll_service.py` | ADR-0009 §5 · APPS/raw_materials · DATABASE_GUIDE/cloth_roll · material data flow |
| `tracking/` (history/barcode) | ADR-0004/0010 §3 · APPS/tracking · CHOKEPOINTS (history note) |
| any `*/urls.py` | URL_ATLAS · the app's REQUEST_MAP · affected REQUEST_JOURNEY |
| any `*/views/*.py` | the app's FILE_MAP + REQUEST_MAP · affected REQUEST_JOURNEY |
| any template (.html) | UI_COMPONENTS (if pattern/vocab) · CLAUDE rule 11 (3-viewport verify) · app GUIDE if page list changed |
| a new ADR | adr/README · KNOWLEDGE_MAP §9 · AI_AGENT_GUIDE (decisions) · ARCHITECTURE_VALIDATION · PENDING_BACKLOG if it changes the plan |
| a new app/model/migration | SYSTEM_DESIGN §5 · LEARNING/02 · APPS/<app>/* · DATABASE_GUIDE · COVERAGE_REPORT counts |
| `config/devseed/*` (dev-only DEV TOOLING: seeder P12 + knowledge_sync P14) | docs/apps/devseed/GUIDE.md · config/devseed/README.md · SEEDER_ENGINE_LOG + KNOWLEDGE_SYNC_LOG (append-only evidence) · DEV_DATASET_ARCHITECTURE.md is 🔒frozen-v1 — spec gaps = dated §12 amendments, never silent divergence · scenario/registry changes must keep test_guard registry pins green · `knowledge/` = PURE DETECTOR (never repairs; single write site = var/ reports; no --fix ever — pins in test_knowledge_purity) |
| `config/bod/*` (owner command center, Phase 15 — WINDOW never engine) | docs/apps/bod/GUIDE.md · config/bod/README.md · BOD_BUILD_LOG (append-only evidence) · PDD register entry 6 = the product charter (owner change-control) · every KPI needs a closed Metric Resolution Ladder row (BOD-D3; step-3 = owner STOP) · read-only law: any write path/POST route = red battery + campaign stop · sidebar MenuItem changes bump per-render SidebarItemRule lookups (see the a360 76-query pin) |
| `config/verification/*` (read-only verify engine, Phase 13 — CERTIFIED 1.0.0) | docs/apps/verification/GUIDE.md · config/verification/README.md · VERIFICATION_ENGINE_LOG (append-only evidence) · READ-ONLY law: any write path = red purity battery + campaign stop · checks need citations (VER-D4); new invariants = owner/ADR · `assertions.py` = the SEED-D6 single implementation (devseed imports it — never fork) · **report schema is CERTIFIED (test_certification.py tripwire): changing envelope/body keys = new engine version + dated Design-Record amendment** · deployment consumers (P19/20/21) cite the schema — coordinate before touching report.py |
| roadmap/phase change | ROADMAP_REVIEW · PENDING_BACKLOG · KNOWLEDGE_MAP §10 |
| **TM-1 / Tracking Mode lands** | WorkflowStage row (above) · REQUIREMENT_REVIEW_STAGE_TRACKING · DATABASE_GUIDE/workflow_stage · flow-editor journey · CHOKEPOINTS/worker_task_service (C-TM convergence) · future-phase detail (this file, below) |
| **MissingPiece module lands** | new APPS/production additions · REQUEST_JOURNEY + DATA_FLOW + DATABASE_GUIDE/MissingPieceCase · ARCHITECTURE_EXPLAINED "why" · PROJECT_BRAIN FEATURE/SEARCH/DEBUGGING_INDEX · settlement pre-fill note · drop "future placeholder" in FEATURE_INDEX · future-phase detail (this file, below) |
| **Alter / Rework module lands** | DATABASE_GUIDE/AlterCase · new REQUEST_JOURNEY · rework-pay decision (ADR-0010 §4) · CHOKEPOINTS note (case-scoped, WSC untouched) · PROJECT_BRAIN indexes · future-phase detail (this file, below) |
| **G1–G7 growth phase ships** (commerce/orders/SKU/stock/variance/planning) | new APPS sections + DATABASE_GUIDE pages + journeys/flows · relevant ADR fences (0008/0009/0010) · AI_AGENT_GUIDE canonical rows · KNOWLEDGE_MAP §10 · PROJECT_BRAIN indexes · drop "future placeholder" status · future-phase detail (this file, below) |

## Future-phase integration detail (what each planned phase needs in PKALS)
The rows above tell you a phase landed; this table is the per-phase doc checklist
(the canonical home — the future-phase rows above point here).

| Phase | PKALS work required when built |
|---|---|
| TM-1 (Tracking Mode) | WorkflowStage DB page + flow-editor journey + REQUIREMENT_REVIEW link; the WorkflowStage row above already anticipates the field |
| MissingPiece | production additions + a REQUEST_JOURNEY + DATA_FLOW + DB page (MissingPieceCase) + ARCHITECTURE_EXPLAINED "why" + DEBUGGING_INDEX rows; settlement pre-fill note |
| Alter / Rework | AlterCase DB page + journey + rework-pay decision (ADR-0010 §4) + chokepoint note (case-scoped, WSC untouched) |
| G1 material costing | DATABASE_GUIDE/cloth_roll + costing journey/flow + ADR-0009 + costing-era stamp |
| G3 variance valuation | new journey/flow + DB note; consumes MissingPiece counts |
| G6 SKU / G5 stock / G2 orders | new APPS sections + DB pages (SKU, FinishedGood, Order) + journeys + ADR-0008/0010 fences + AI_AGENT_GUIDE canonical rows |
| G7 planning | new section when built |

Every one, on ship: add to FEATURE_INDEX + SEARCH_INDEX, drop its "future
placeholder" status, update KNOWLEDGE_MAP §10.

### Verification Sources
Built from the service→doc mapping verified across installments 1–5 + the
CHOKEPOINTS/ARCHITECTURE_EXPLAINED structure; future-phase detail relocated here
from the archived FINAL_PKALS_REVIEW (2026-06-13). Confidence: High.
