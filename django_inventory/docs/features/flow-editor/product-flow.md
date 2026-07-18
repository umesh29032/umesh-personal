---
id: url-card-production-product-flow
type: url-card
status: generated
owner: generated
scope: route — url:production:product-flow
anchors: config/config/urls.py
verified: graph:56207d76ed26
---

# URL card — `product-flow`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `56207d76ed26` · schema: 1.0.1 · template: url-card v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `product-flow` |
| Namespace | `production` |
| Mount | `/production/products/<int:pk>/flow/` |
| Pattern | `products/<int:pk>/flow/` |
| Named | true |

## View

| Field | Value |
|---|---|
| View | `ProductFlowEditView` |
| Module | `production.views.flow_views` |
| Defined in | `config/production/views/flow_views.py` |
| Vendor | false |

## App

Derived from the view module (`production.views.flow_views` → app `production`; a render rule, not a graph edge).

App documentation: [config/production/README.md](../../../config/production/README.md) · [docs/apps/production/GUIDE.md](../../apps/production/GUIDE.md)

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

[Flow editor (rates/grouping)](README.md) (`flow-editor`, via `belongs_to_feature`)

## Governing docs

Feature seed: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md`

## Mobile strategy

Not machine-known — the graph carries no mobile-strategy data for this route.
