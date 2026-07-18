---
id: feature-flow-editor
type: feature-doc
status: generated
owner: generated
scope: feature — flow-editor
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:56207d76ed26
---

# Feature — Flow editor (rates/grouping)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `56207d76ed26` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `flow-editor` |
| Label | Flow editor (rates/grouping) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `production:product-flow` | `/production/products/<int:pk>/flow/` | `ProductFlowEditView` | [product-flow.md](product-flow.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `production.WorkflowStage` | `production_workflowstage` | not machine-known |

## Apps touched

- `production` — [config/production/README.md](../../../config/production/README.md) · [docs/apps/production/GUIDE.md](../../apps/production/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
