---
id: url-card-patterns-ai-piece-list
type: url-card
status: generated
owner: generated
scope: route — url:patterns_ai:piece-list
anchors: config/config/urls.py
verified: graph:f48dc8b77c29
---

# URL card — `piece-list`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `f48dc8b77c29` · schema: 1.0.1 · template: url-card v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `piece-list` |
| Namespace | `patterns_ai` |
| Mount | `/patterns/pieces/` |
| Pattern | `pieces/` |
| Named | true |

## View

| Field | Value |
|---|---|
| View | `PieceListView` |
| Module | `patterns_ai.views` |
| Defined in | `config/patterns_ai/views.py` |
| Vendor | false |

## App

Derived from the view module (`patterns_ai.views` → app `patterns_ai`; a render rule, not a graph edge).

App documentation: [config/patterns_ai/README.md](../../../config/patterns_ai/README.md) · [docs/apps/patterns_ai/GUIDE.md](../../apps/patterns_ai/GUIDE.md)

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

[Pattern layout tool (blueprint → usage → outcome/void; READY gate; exports)](README.md) (`pattern-layout-tool`, via `belongs_to_feature`)

## Governing docs

Feature seed: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md`

## Mobile strategy

Not machine-known — the graph carries no mobile-strategy data for this route.
