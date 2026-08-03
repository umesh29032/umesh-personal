---
id: feature-factory-expenses-recurring-engine
type: feature-doc
status: generated
owner: generated
scope: feature — factory-expenses-recurring-engine
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:4ed4a2180bcf
---

# Feature — Factory expenses + recurring engine (record · register · generate · material spend)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `factory-expenses-recurring-engine` |
| Label | Factory expenses + recurring engine (record · register · generate · material spend) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `expense:expense-generate` | `/expense/generate/` | `GenerateExpensesView` | [expense-generate.md](expense-generate.md) |
| `expense:expense-template-add` | `/expense/templates/add/` | `ExpenseTemplateCreateView` | [expense-template-add.md](expense-template-add.md) |
| `expense:expense-template-list` | `/expense/templates/` | `ExpenseTemplateListView` | [expense-template-list.md](expense-template-list.md) |
| `expense:factory-expense-add` | `/expense/expenses/add/` | `FactoryExpenseCreateView` | [factory-expense-add.md](factory-expense-add.md) |
| `expense:factory-expense-list` | `/expense/expenses/` | `FactoryExpenseListView` | [factory-expense-list.md](factory-expense-list.md) |
| `expense:material-spend` | `/expense/material-spend/` | `MaterialSpendView` | [material-spend.md](material-spend.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `expense.ExpenseGenerationRecord` | `expense_expensegenerationrecord` | not machine-known |
| `expense.ExpenseTemplate` | `expense_expensetemplate` | not machine-known |
| `expense.FactoryExpense` | `expense_factoryexpense` | not machine-known |

## Apps touched

- `expense` — [config/expense/README.md](../../../config/expense/README.md) · [docs/apps/expense/GUIDE.md](../../apps/expense/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
