---
id: feature-adda-register-lifecycle
type: feature-doc
status: generated
owner: generated
scope: feature — adda-register-lifecycle
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:4ed4a2180bcf
---

# Feature — Adda register + lifecycle (list · detail · lanes · cancel · delete)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `adda-register-lifecycle` |
| Label | Adda register + lifecycle (list · detail · lanes · cancel · delete) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `production:adda-add-lane` | `/production/addas/<str:code>/lanes/add/` | `AddaAddLaneView` | [adda-add-lane.md](adda-add-lane.md) |
| `production:adda-bundle-sets` | `/production/addas/<str:code>/bundles/create-sets/` | `AddaBundleSetsView` | [adda-bundle-sets.md](adda-bundle-sets.md) |
| `production:adda-cancel` | `/production/addas/<str:code>/cancel/` | `AddaCancelView` | [adda-cancel.md](adda-cancel.md) |
| `production:adda-cancel-lane` | `/production/addas/<str:code>/lanes/cancel/` | `AddaCancelLaneView` | [adda-cancel-lane.md](adda-cancel-lane.md) |
| `production:adda-delete` | `/production/addas/<str:code>/delete/` | `AddaDeleteView` | [adda-delete.md](adda-delete.md) |
| `production:adda-detail` | `/production/addas/<str:code>/` | `AddaDetailView` | [adda-detail.md](adda-detail.md) |
| `production:adda-list` | `/production/addas/` | `AddaListView` | [adda-list.md](adda-list.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `production.Adda` | `production_adda` | not machine-known |
| `production.AddaStageRecord` | `production_addastagerecord` | not machine-known |

## Apps touched

- `production` — [config/production/README.md](../../../config/production/README.md) · [docs/apps/production/GUIDE.md](../../apps/production/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
