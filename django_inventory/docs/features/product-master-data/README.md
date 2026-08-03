---
id: feature-product-master-data
type: feature-doc
status: generated
owner: generated
scope: feature — product-master-data
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:f48dc8b77c29
---

# Feature — Product master data (products · sizes · pattern register)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `f48dc8b77c29` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `product-master-data` |
| Label | Product master data (products · sizes · pattern register) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `production:pattern-add` | `/production/patterns/add/` | `ProductPatternCreateView` | [pattern-add.md](pattern-add.md) |
| `production:pattern-delete` | `/production/patterns/<int:pk>/delete/` | `ProductPatternDeleteView` | [pattern-delete.md](pattern-delete.md) |
| `production:pattern-edit` | `/production/patterns/<int:pk>/edit/` | `ProductPatternUpdateView` | [pattern-edit.md](pattern-edit.md) |
| `production:pattern-list` | `/production/patterns/` | `ProductPatternListView` | [pattern-list.md](pattern-list.md) |
| `production:product-archive` | `/production/products/<int:pk>/archive/` | `ProductArchiveView` | [product-archive.md](product-archive.md) |
| `production:product-create` | `/production/products/add/` | `ProductCreateView` | [product-create.md](product-create.md) |
| `production:product-list` | `/production/products/` | `ProductListView` | [product-list.md](product-list.md) |
| `production:product-pattern-blueprint` | `/production/products/<int:pk>/patterns/blueprint/` | `ProductPatternBlueprintRedirectView` | [product-pattern-blueprint.md](product-pattern-blueprint.md) |
| `production:product-patterns` | `/production/products/<int:pk>/patterns/` | `ProductPatternsEntryView` | [product-patterns.md](product-patterns.md) |
| `production:product-sizes` | `/production/products/<int:pk>/sizes/` | `ProductSizesEditView` | [product-sizes.md](product-sizes.md) |
| `production:product-update` | `/production/products/<int:pk>/edit/` | `ProductUpdateView` | [product-update.md](product-update.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `production.Product` | `production_product` | not machine-known |
| `production.ProductPattern` | `production_productpattern` | not machine-known |
| `production.ProductSize` | `production_productsize` | not machine-known |

## Apps touched

- `production` — [config/production/README.md](../../../config/production/README.md) · [docs/apps/production/GUIDE.md](../../apps/production/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
