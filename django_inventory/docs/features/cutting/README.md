---
id: feature-cutting
type: feature-doc
status: generated
owner: generated
scope: feature — cutting
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:4ed4a2180bcf
---

# Feature — Cutting

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `cutting` |
| Label | Cutting |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `production:cutting-allocation-delete` | `/production/addas/<str:code>/cutting/allocation/<int:pk>/delete/` | `CuttingAllocationDeleteView` | [cutting-allocation-delete.md](cutting-allocation-delete.md) |
| `production:cutting-breakup-delete` | `/production/addas/<str:code>/cutting/breakup/<int:pk>/delete/` | `CuttingBreakupDeleteView` | [cutting-breakup-delete.md](cutting-breakup-delete.md) |
| `production:cutting-breakup-save` | `/production/addas/<str:code>/cutting/breakup/save/` | `CuttingBreakupSaveView` | [cutting-breakup-save.md](cutting-breakup-save.md) |
| `production:cutting-bundle-add-pieces` | `/production/addas/<str:code>/cutting/bundle/<int:pk>/add-pieces/` | `CuttingBundleAddPiecesView` | [cutting-bundle-add-pieces.md](cutting-bundle-add-pieces.md) |
| `production:cutting-bundle-create` | `/production/addas/<str:code>/cutting/bundle/create/` | `CuttingBundleCreateView` | [cutting-bundle-create.md](cutting-bundle-create.md) |
| `production:cutting-bundle-delete` | `/production/addas/<str:code>/cutting/bundle/<int:pk>/delete/` | `CuttingBundleDeleteView` | [cutting-bundle-delete.md](cutting-bundle-delete.md) |
| `production:cutting-bundle-item-delete` | `/production/addas/<str:code>/cutting/bundle/item/<int:pk>/delete/` | `CuttingBundleItemDeleteView` | [cutting-bundle-item-delete.md](cutting-bundle-item-delete.md) |
| `production:cutting-complete` | `/production/addas/<str:code>/cutting/` | `CuttingCompleteView` | [cutting-complete.md](cutting-complete.md) |
| `production:cutting-draft` | `/production/addas/<str:code>/cutting/draft/` | `CuttingDraftView` | [cutting-draft.md](cutting-draft.md) |
| `production:cutting-item-allocate` | `/production/addas/<str:code>/cutting/bundle/item/<int:pk>/allocate/` | `CuttingBundleItemAllocateView` | [cutting-item-allocate.md](cutting-item-allocate.md) |
| `production:cutting-reopen` | `/production/addas/<str:code>/cutting/reopen/` | `CuttingReopenView` | [cutting-reopen.md](cutting-reopen.md) |
| `production:cutting-start` | `/production/addas/<str:code>/cutting/start/` | `CuttingStartView` | [cutting-start.md](cutting-start.md) |
| `production:cutting-workspace` | `/production/addas/<str:code>/cutting/workspace/` | `CuttingWorkspaceView` | [cutting-workspace.md](cutting-workspace.md) |
| `production:cutting-workspace-complete` | `/production/addas/<str:code>/cutting/workspace/complete/` | `CuttingWorkspaceCompleteView` | [cutting-workspace-complete.md](cutting-workspace-complete.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `production.CuttingRecord` | `production_cuttingrecord` | not machine-known |

## Apps touched

- `production` — [config/production/README.md](../../../config/production/README.md) · [docs/apps/production/GUIDE.md](../../apps/production/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
