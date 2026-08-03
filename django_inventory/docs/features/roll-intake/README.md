---
id: feature-roll-intake
type: feature-doc
status: generated
owner: generated
scope: feature — roll-intake
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:f48dc8b77c29
---

# Feature — Roll intake

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `f48dc8b77c29` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `roll-intake` |
| Label | Roll intake |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `raw_materials:roll-bulk-create` | `/raw-materials/rolls/bulk-add/` | `RollBulkCreateView` | [roll-bulk-create.md](roll-bulk-create.md) |
| `raw_materials:roll-damage` | `/raw-materials/rolls/<int:pk>/damage/` | `RollDamageView` | [roll-damage.md](roll-damage.md) |
| `raw_materials:roll-detail` | `/raw-materials/rolls/<int:pk>/` | `RollDetailView` | [roll-detail.md](roll-detail.md) |
| `raw_materials:roll-edit` | `/raw-materials/rolls/<int:pk>/edit/` | `RollUpdateView` | [roll-edit.md](roll-edit.md) |
| `raw_materials:roll-list` | `/raw-materials/rolls/` | `RollListView` | [roll-list.md](roll-list.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `raw_materials.ClothRoll` | `raw_materials_clothroll` | not machine-known |

## Apps touched

- `raw_materials` — [config/raw_materials/README.md](../../../config/raw_materials/README.md) · [docs/apps/raw_materials/GUIDE.md](../../apps/raw_materials/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
