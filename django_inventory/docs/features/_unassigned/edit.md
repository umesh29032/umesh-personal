---
id: url-card-machines-edit
type: url-card
status: generated
owner: generated
scope: route — url:machines:edit
anchors: config/config/urls.py
verified: graph:5d159ece1df0
---

# URL card — `edit`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `5d159ece1df0` · schema: 1.0.1 · template: url-card v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `edit` |
| Namespace | `machines` |
| Mount | `/machines/<int:pk>/edit/` |
| Pattern | `<int:pk>/edit/` |
| Named | true |

## View

| Field | Value |
|---|---|
| View | `MachineUpdateView` |
| Module | `machines.views` |
| Defined in | `config/machines/views.py` |
| Vendor | false |

## App

Derived from the view module (`machines.views` → app `machines`; a render rule, not a graph edge).

App documentation: [config/machines/README.md](../../../config/machines/README.md) · [docs/apps/machines/GUIDE.md](../../apps/machines/GUIDE.md)

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
