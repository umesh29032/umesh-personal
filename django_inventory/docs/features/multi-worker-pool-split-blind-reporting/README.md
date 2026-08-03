---
id: feature-multi-worker-pool-split-blind-reporting
type: feature-doc
status: generated
owner: generated
scope: feature — multi-worker-pool-split-blind-reporting
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:f48dc8b77c29
---

# Feature — Multi-worker pool split + blind reporting (OP-1, 2026-07-05)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `f48dc8b77c29` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `multi-worker-pool-split-blind-reporting` |
| Label | Multi-worker pool split + blind reporting (OP-1, 2026-07-05) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `production:generic-stage-alloc-void` | `/production/addas/<str:code>/stage/<str:stage_type>/alloc-void/` | `GenericStageAllocationVoidView` | [generic-stage-alloc-void.md](generic-stage-alloc-void.md) |
| `production:generic-stage-allocate` | `/production/addas/<str:code>/stage/<str:stage_type>/allocate/` | `GenericStageAllocateView` | [generic-stage-allocate.md](generic-stage-allocate.md) |
| `production:generic-stage-complete` | `/production/addas/<str:code>/stage/<str:stage_type>/complete/` | `GenericStageCompleteView` | [generic-stage-complete.md](generic-stage-complete.md) |
| `production:generic-stage-reopen` | `/production/addas/<str:code>/stage/<str:stage_type>/reopen/` | `GenericStageReopenView` | [generic-stage-reopen.md](generic-stage-reopen.md) |
| `production:generic-stage-start` | `/production/addas/<str:code>/stage/<str:stage_type>/start/` | `GenericStageStartView` | [generic-stage-start.md](generic-stage-start.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `production.StagePoolSnapshot` | `production_stagepoolsnapshot` | not machine-known |
| `production.WorkerStageAllocation` | `production_workerstageallocation` | not machine-known |

## Apps touched

- `production` — [config/production/README.md](../../../config/production/README.md) · [docs/apps/production/GUIDE.md](../../apps/production/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
