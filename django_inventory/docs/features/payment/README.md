---
id: feature-payment
type: feature-doc
status: generated
owner: generated
scope: feature — payment
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:f48dc8b77c29
---

# Feature — Payment (cash)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `f48dc8b77c29` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `payment` |
| Label | Payment (cash) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `expense:settlement-create` | `/expense/workers/<int:pk>/settle/` | `SettlementCreateView` | [settlement-create.md](settlement-create.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `expense.PayrollSettlement` | `expense_payrollsettlement` | not machine-known |

## Apps touched

- `expense` — [config/expense/README.md](../../../config/expense/README.md) · [docs/apps/expense/GUIDE.md](../../apps/expense/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
