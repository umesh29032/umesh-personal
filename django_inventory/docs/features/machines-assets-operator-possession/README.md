---
id: feature-machines-assets-operator-possession
type: feature-doc
status: generated
owner: generated
scope: feature — machines-assets-operator-possession
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:4ed4a2180bcf
---

# Feature — Machines: assets + operator possession (R10-A, 2026-07-05)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `machines-assets-operator-possession` |
| Label | Machines: assets + operator possession (R10-A, 2026-07-05) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `machines:add` | `/machines/add/` | `MachineCreateView` | [add.md](add.md) |
| `machines:assign` | `/machines/<int:pk>/assign/` | `MachineAssignView` | [assign.md](assign.md) |
| `machines:edit` | `/machines/<int:pk>/edit/` | `MachineUpdateView` | [edit.md](edit.md) |
| `machines:list` | `/machines/` | `MachineListView` | [list.md](list.md) |
| `machines:release` | `/machines/assignments/<int:pk>/release/` | `MachineReleaseView` | [release.md](release.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `machines.Machine` | `machines_machine` | not machine-known |

## Apps touched

- `machines` — [config/machines/README.md](../../../config/machines/README.md) · [docs/apps/machines/GUIDE.md](../../apps/machines/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
