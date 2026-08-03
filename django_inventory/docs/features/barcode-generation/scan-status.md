---
id: url-card-tracking-scan-status
type: url-card
status: generated
owner: generated
scope: route — url:tracking:scan-status
anchors: config/config/urls.py
verified: graph:4ed4a2180bcf
---

# URL card — `scan-status`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: url-card v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `scan-status` |
| Namespace | `tracking` |
| Mount | `/tracking/scan/<str:value>/status/` |
| Pattern | `scan/<str:value>/status/` |
| Named | true |

## View

| Field | Value |
|---|---|
| View | `update_piece_status` |
| Module | `inventory.views.tracking_barcodes` |
| Defined in | `config/inventory/views/tracking_barcodes.py` |
| Vendor | false |

## App

Derived from the view module (`inventory.views.tracking_barcodes` → app `inventory`; a render rule, not a graph edge).

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
