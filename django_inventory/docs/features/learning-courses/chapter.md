---
id: url-card-learning-chapter
type: url-card
status: generated
owner: generated
scope: route — url:learning:chapter
anchors: config/config/urls.py
verified: graph:4ed4a2180bcf
---

# URL card — `chapter`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: url-card v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `chapter` |
| Namespace | `learning` |
| Mount | `/learn/<slug:course>/<slug:chapter>/` |
| Pattern | `<slug:course>/<slug:chapter>/` |
| Named | true |

## View

| Field | Value |
|---|---|
| View | `ChapterView` |
| Module | `learning.views` |
| Defined in | `config/learning/views.py` |
| Vendor | false |

## App

Derived from the view module (`learning.views` → app `learning`; a render rule, not a graph edge).

App documentation: [config/learning/README.md](../../../config/learning/README.md) · [docs/apps/learning/GUIDE.md](../../apps/learning/GUIDE.md)

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

[Learning courses (/learn/)](README.md) (`learning-courses`, via `belongs_to_feature`)

## Governing docs

Feature seed: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md`

## Mobile strategy

Not machine-known — the graph carries no mobile-strategy data for this route.
