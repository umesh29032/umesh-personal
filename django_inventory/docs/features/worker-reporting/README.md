---
id: feature-worker-reporting
type: feature-doc
status: generated
owner: generated
scope: feature — worker-reporting
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:4ed4a2180bcf
---

# Feature — Worker reporting

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `worker-reporting` |
| Label | Worker reporting |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `production:adda-snapshot` | `/production/addas/<str:code>/snapshot/` | `AddaSnapshotView` | [adda-snapshot.md](adda-snapshot.md) |
| `production:my-work` | `/production/my-work/` | `MyAssignedWorkView` | [my-work.md](my-work.md) |
| `production:worker-report` | `/production/addas/<str:code>/report/<str:stage_type>/` | `WorkerReportView` | [worker-report.md](worker-report.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `production.WorkerStageContribution` | `production_workerstagecontribution` | `service:production.worker_task_service` |

## Apps touched

- `production` — [config/production/README.md](../../../config/production/README.md) · [docs/apps/production/GUIDE.md](../../apps/production/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
