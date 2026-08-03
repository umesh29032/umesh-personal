---
id: url-card-storefront-product-delete
type: url-card
status: generated
owner: generated
scope: route — url:storefront:product_delete
anchors: config/config/urls.py
verified: graph:4ed4a2180bcf
---

# URL card — `product_delete`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: url-card v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `product_delete` |
| Namespace | `storefront` |
| Mount | `/storefront/products/<int:pk>/delete/` |
| Pattern | `products/<int:pk>/delete/` |
| Named | true |

## View

| Field | Value |
|---|---|
| View | `ProductDeleteView` |
| Module | `storefront.views.listing_views` |
| Defined in | `config/storefront/views/listing_views.py` |
| Vendor | false |

## App

Derived from the view module (`storefront.views.listing_views` → app `storefront`; a render rule, not a graph edge).

App documentation: [config/storefront/README.md](../../../config/storefront/README.md) · [docs/apps/storefront/GUIDE.md](../../apps/storefront/GUIDE.md)

## Gates

Not machine-known — the graph carries no `gated_by` edges (no certified gate register exists;
Phase-8 residual R-2). Gate truth remains in code.

## Services invoked

Not machine-known — the graph carries no `calls` edges (no certified view→service register
exists; Phase-8 residual R-1).

## Models written

Not machine-known at route grain — single-writer truth is recorded at service grain
(`writes` edges); see the app documentation above.

## Feature

[Storefront listings (featured products · categories)](README.md) (`storefront-listings`, via `belongs_to_feature`)

## Governing docs

Feature seed: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md`

## Mobile strategy

Not machine-known — the graph carries no mobile-strategy data for this route.
