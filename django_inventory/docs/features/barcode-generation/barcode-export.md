---
id: url-card-tracking-barcode-export
type: url-card
status: generated
owner: generated
scope: route — url:tracking:barcode-export
anchors: config/config/urls.py
verified: graph:f48dc8b77c29
---

# URL card — `barcode-export`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `f48dc8b77c29` · schema: 1.0.1 · template: url-card v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `barcode-export` |
| Namespace | `tracking` |
| Mount | `/tracking/barcodes/<str:adda_code>/export/` |
| Pattern | `barcodes/<str:adda_code>/export/` |
| Named | true |

## View

| Field | Value |
|---|---|
| View | `barcode_export_csv` |
| Module | `inventory.views.tracking_dashboard` |
| Defined in | `config/inventory/views/tracking_dashboard.py` |
| Vendor | false |

## App

Derived from the view module (`inventory.views.tracking_dashboard` → app `inventory`; a render rule, not a graph edge).

App documentation: [config/inventory/README.md](../../../config/inventory/README.md) · [docs/apps/inventory/GUIDE.md](../../apps/inventory/GUIDE.md)

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

[Barcode generation](README.md) (`barcode-generation`, via `belongs_to_feature`)

## Governing docs

Feature seed: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md`

## Mobile strategy

Not machine-known — the graph carries no mobile-strategy data for this route.
