---
id: feature-settlement-queue
type: feature-doc
status: generated
owner: generated
scope: feature — settlement-queue
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:56207d76ed26
---

# Feature — Settlement queue

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `56207d76ed26` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `settlement-queue` |
| Label | Settlement queue |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `expense:adda-settlement-list` | `/expense/settlements/` | `AddaSettlementListView` | [adda-settlement-list.md](adda-settlement-list.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `expense.AddaSettlement` | `expense_addasettlement` | `service:expense.adda_settlement_service` |

## Apps touched

- `expense` — [config/expense/README.md](../../../config/expense/README.md) · [docs/apps/expense/GUIDE.md](../../apps/expense/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
