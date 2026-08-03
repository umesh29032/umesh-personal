---
id: feature-worker-payroll-admin
type: feature-doc
status: generated
owner: generated
scope: feature — worker-payroll-admin
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:4ed4a2180bcf
---

# Feature — Worker payroll admin (overview · per-worker detail · pay basis · FnF)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `worker-payroll-admin` |
| Label | Worker payroll admin (overview · per-worker detail · pay basis · FnF) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `expense:payroll-overview` | `/expense/payroll/` | `PayrollOverviewView` | [payroll-overview.md](payroll-overview.md) |
| `expense:worker-detail` | `/expense/workers/<int:pk>/` | `WorkerPayrollDetailView` | [worker-detail.md](worker-detail.md) |
| `expense:worker-fnf` | `/expense/workers/<int:pk>/fnf/` | `WorkerFnFView` | [worker-fnf.md](worker-fnf.md) |
| `expense:worker-pay-basis` | `/expense/workers/<int:pk>/pay-basis/` | `WorkerPayBasisUpdateView` | [worker-pay-basis.md](worker-pay-basis.md) |
| `expense:worker-profile` | `/expense/workers/<int:pk>/profile/` | `WorkerProfileEditView` | [worker-profile.md](worker-profile.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `expense.WorkerPayBasisAudit` | `expense_workerpaybasisaudit` | not machine-known |
| `expense.WorkerProfile` | `expense_workerprofile` | not machine-known |

## Apps touched

- `expense` — [config/expense/README.md](../../../config/expense/README.md) · [docs/apps/expense/GUIDE.md](../../apps/expense/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
