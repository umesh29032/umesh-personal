---
id: url-card-storefront-product-add
type: url-card
status: generated
owner: generated
scope: route — url:storefront:product_add
anchors: config/config/urls.py
verified: graph:5d159ece1df0
---

# URL card — `product_add`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `5d159ece1df0` · schema: 1.0.1 · template: url-card v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `product_add` |
| Namespace | `storefront` |
| Mount | `/storefront/products/add/` |
| Pattern | `products/add/` |
| Named | true |

## View

| Field | Value |
|---|---|
| View | `ProductCreateView` |
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

None machine-provable — no `belongs_to_feature` edge for this url (fix at source: enrich FEATURE_INDEX, rebuild, regenerate).

## Governing docs

None machine-known at route grain — see the app documentation above.

## Mobile strategy

Not machine-known — the graph carries no mobile-strategy data for this route.
