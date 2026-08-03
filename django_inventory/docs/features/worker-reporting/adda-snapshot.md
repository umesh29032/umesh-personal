---
id: url-card-production-adda-snapshot
type: url-card
status: generated
owner: generated
scope: route — url:production:adda-snapshot
anchors: config/config/urls.py
verified: graph:4ed4a2180bcf
---

# URL card — `adda-snapshot`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: url-card v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `adda-snapshot` |
| Namespace | `production` |
| Mount | `/production/addas/<str:code>/snapshot/` |
| Pattern | `addas/<str:code>/snapshot/` |
| Named | true |

## View

| Field | Value |
|---|---|
| View | `AddaSnapshotView` |
| Module | `production.views.worker_report_views` |
| Defined in | `config/production/views/worker_report_views.py` |
| Vendor | false |

## App

Derived from the view module (`production.views.worker_report_views` → app `production`; a render rule, not a graph edge).

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

[Worker reporting](README.md) (`worker-reporting`, via `belongs_to_feature`)

## Governing docs

Feature seed: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md`

## Mobile strategy

Not machine-known — the graph carries no mobile-strategy data for this route.
