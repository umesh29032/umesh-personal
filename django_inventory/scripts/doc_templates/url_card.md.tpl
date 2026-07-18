<!-- template: url-card v1.0.0 — consumed by scripts/generate_docs.py (stdlib string.Template) -->
---
id: $card_id
type: url-card
status: generated
owner: generated
scope: route — $url_id
anchors: $anchors
verified: graph:$graph12
---

# URL card — `$route_name`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `$graph12` · schema: $schema_version · template: url-card v$template_version
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `$route_name` |
| Namespace | $namespace |
| Mount | `$mount` |
| Pattern | $pattern |
| Named | $named |

## View

| Field | Value |
|---|---|
| View | `$view_name` |
| Module | `$view_module` |
| Defined in | $view_anchor |
| Vendor | $vendor |

## App

$app_section

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

$feature_section

## Governing docs

$governing_docs

## Mobile strategy

Not machine-known — the graph carries no mobile-strategy data for this route.
