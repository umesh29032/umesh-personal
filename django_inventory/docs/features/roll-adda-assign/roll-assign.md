---
id: url-card-raw-materials-roll-assign
type: url-card
status: generated
owner: generated
scope: route — url:raw_materials:roll-assign
anchors: config/config/urls.py
verified: graph:5d159ece1df0
---

# URL card — `roll-assign`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `5d159ece1df0` · schema: 1.0.1 · template: url-card v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `roll-assign` |
| Namespace | `raw_materials` |
| Mount | `/raw-materials/rolls/<int:pk>/assign/` |
| Pattern | `rolls/<int:pk>/assign/` |
| Named | true |

## View

| Field | Value |
|---|---|
| View | `RollAssignView` |
| Module | `raw_materials.views.assign_views` |
| Defined in | `config/raw_materials/views/assign_views.py` |
| Vendor | false |

## App

Derived from the view module (`raw_materials.views.assign_views` → app `raw_materials`; a render rule, not a graph edge).

App documentation: [config/raw_materials/README.md](../../../config/raw_materials/README.md) · [docs/apps/raw_materials/GUIDE.md](../../apps/raw_materials/GUIDE.md)

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

[Roll→Adda assign](README.md) (`roll-adda-assign`, via `belongs_to_feature`)

## Governing docs

Feature seed: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md`

## Mobile strategy

Not machine-known — the graph carries no mobile-strategy data for this route.
