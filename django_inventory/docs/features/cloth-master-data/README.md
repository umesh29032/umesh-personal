---
id: feature-cloth-master-data
type: feature-doc
status: generated
owner: generated
scope: feature — cloth-master-data
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:f48dc8b77c29
---

# Feature — Cloth master data (types · colours · storage locations)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `f48dc8b77c29` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `cloth-master-data` |
| Label | Cloth master data (types · colours · storage locations) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `raw_materials:cloth-color-archive` | `/raw-materials/cloth-colors/<int:pk>/archive/` | `ClothColorArchiveView` | [cloth-color-archive.md](cloth-color-archive.md) |
| `raw_materials:cloth-color-create` | `/raw-materials/cloth-colors/add/` | `ClothColorCreateView` | [cloth-color-create.md](cloth-color-create.md) |
| `raw_materials:cloth-color-delete` | `/raw-materials/cloth-colors/<int:pk>/delete/` | `ClothColorDeleteView` | [cloth-color-delete.md](cloth-color-delete.md) |
| `raw_materials:cloth-color-list` | `/raw-materials/cloth-colors/` | `ClothColorListView` | [cloth-color-list.md](cloth-color-list.md) |
| `raw_materials:cloth-color-update` | `/raw-materials/cloth-colors/<int:pk>/edit/` | `ClothColorUpdateView` | [cloth-color-update.md](cloth-color-update.md) |
| `raw_materials:cloth-type-archive` | `/raw-materials/cloth-types/<int:pk>/archive/` | `ClothTypeArchiveView` | [cloth-type-archive.md](cloth-type-archive.md) |
| `raw_materials:cloth-type-create` | `/raw-materials/cloth-types/add/` | `ClothTypeCreateView` | [cloth-type-create.md](cloth-type-create.md) |
| `raw_materials:cloth-type-delete` | `/raw-materials/cloth-types/<int:pk>/delete/` | `ClothTypeDeleteView` | [cloth-type-delete.md](cloth-type-delete.md) |
| `raw_materials:cloth-type-list` | `/raw-materials/cloth-types/` | `ClothTypeListView` | [cloth-type-list.md](cloth-type-list.md) |
| `raw_materials:cloth-type-update` | `/raw-materials/cloth-types/<int:pk>/edit/` | `ClothTypeUpdateView` | [cloth-type-update.md](cloth-type-update.md) |
| `raw_materials:storage-archive` | `/raw-materials/storage-locations/<int:pk>/archive/` | `StorageLocationArchiveView` | [storage-archive.md](storage-archive.md) |
| `raw_materials:storage-create` | `/raw-materials/storage-locations/add/` | `StorageLocationCreateView` | [storage-create.md](storage-create.md) |
| `raw_materials:storage-delete` | `/raw-materials/storage-locations/<int:pk>/delete/` | `StorageLocationDeleteView` | [storage-delete.md](storage-delete.md) |
| `raw_materials:storage-list` | `/raw-materials/storage-locations/` | `StorageLocationListView` | [storage-list.md](storage-list.md) |
| `raw_materials:storage-update` | `/raw-materials/storage-locations/<int:pk>/edit/` | `StorageLocationUpdateView` | [storage-update.md](storage-update.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `raw_materials.ClothColor` | `raw_materials_clothcolor` | not machine-known |
| `raw_materials.ClothType` | `raw_materials_clothtype` | not machine-known |
| `raw_materials.StorageLocation` | `raw_materials_storagelocation` | not machine-known |

## Apps touched

- `raw_materials` — [config/raw_materials/README.md](../../../config/raw_materials/README.md) · [docs/apps/raw_materials/GUIDE.md](../../apps/raw_materials/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
