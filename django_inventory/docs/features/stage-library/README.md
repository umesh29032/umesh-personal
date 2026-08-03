---
id: feature-stage-library
type: feature-doc
status: generated
owner: generated
scope: feature — stage-library
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:4ed4a2180bcf
---

# Feature — Stage library (stages · categories · machine types)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `stage-library` |
| Label | Stage library (stages · categories · machine types) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `production:machine-type-add` | `/production/machine-types/add/` | `MachineTypeCreateView` | [machine-type-add.md](machine-type-add.md) |
| `production:machine-type-edit` | `/production/machine-types/<int:pk>/edit/` | `MachineTypeUpdateView` | [machine-type-edit.md](machine-type-edit.md) |
| `production:machine-type-list` | `/production/machine-types/` | `MachineTypeListView` | [machine-type-list.md](machine-type-list.md) |
| `production:stage-add` | `/production/stages/add/` | `StageCreateView` | [stage-add.md](stage-add.md) |
| `production:stage-advanced` | `/production/addas/<str:code>/stage-advanced/` | `StageAdvancedBounceView` | [stage-advanced.md](stage-advanced.md) |
| `production:stage-category-add` | `/production/stage-categories/add/` | `StageCategoryCreateView` | [stage-category-add.md](stage-category-add.md) |
| `production:stage-category-edit` | `/production/stage-categories/<int:pk>/edit/` | `StageCategoryUpdateView` | [stage-category-edit.md](stage-category-edit.md) |
| `production:stage-category-list` | `/production/stage-categories/` | `StageCategoryListView` | [stage-category-list.md](stage-category-list.md) |
| `production:stage-delete` | `/production/stages/<int:pk>/delete/` | `StageDeleteView` | [stage-delete.md](stage-delete.md) |
| `production:stage-edit` | `/production/stages/<int:pk>/edit/` | `StageUpdateView` | [stage-edit.md](stage-edit.md) |
| `production:stage-list` | `/production/stages/` | `StageListView` | [stage-list.md](stage-list.md) |
| `production:stage-panel` | `/production/addas/<str:code>/stage/<str:stage_type>/` | `StagePanelView` | [stage-panel.md](stage-panel.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `accounts.Skill` | `accounts_skill` | not machine-known |
| `production.MachineType` | `production_machinetype` | not machine-known |
| `production.Stage` | `production_stage` | not machine-known |
| `production.StageCategory` | `production_stagecategory` | not machine-known |

## Apps touched

- `production` — [config/production/README.md](../../../config/production/README.md) · [docs/apps/production/GUIDE.md](../../apps/production/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
