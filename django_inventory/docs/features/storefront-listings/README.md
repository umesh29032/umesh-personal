---
id: feature-storefront-listings
type: feature-doc
status: generated
owner: generated
scope: feature — storefront-listings
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:4ed4a2180bcf
---

# Feature — Storefront listings (featured products · categories)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `storefront-listings` |
| Label | Storefront listings (featured products · categories) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `storefront:category_add` | `/storefront/categories/add/` | `CategoryCreateView` | [category_add.md](category_add.md) |
| `storefront:category_delete` | `/storefront/categories/<int:pk>/delete/` | `CategoryDeleteView` | [category_delete.md](category_delete.md) |
| `storefront:category_edit` | `/storefront/categories/<int:pk>/edit/` | `CategoryUpdateView` | [category_edit.md](category_edit.md) |
| `storefront:category_list` | `/storefront/categories/` | `CategoryListView` | [category_list.md](category_list.md) |
| `storefront:product_add` | `/storefront/products/add/` | `ProductCreateView` | [product_add.md](product_add.md) |
| `storefront:product_delete` | `/storefront/products/<int:pk>/delete/` | `ProductDeleteView` | [product_delete.md](product_delete.md) |
| `storefront:product_edit` | `/storefront/products/<int:pk>/edit/` | `ProductUpdateView` | [product_edit.md](product_edit.md) |
| `storefront:product_list` | `/storefront/products/` | `ProductListView` | [product_list.md](product_list.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `storefront.Category` | `storefront_category` | not machine-known |

## Apps touched

- `storefront` — [config/storefront/README.md](../../../config/storefront/README.md) · [docs/apps/storefront/GUIDE.md](../../apps/storefront/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
