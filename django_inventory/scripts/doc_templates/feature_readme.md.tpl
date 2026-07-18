<!-- template: feature-doc v1.0.0 — consumed by scripts/generate_docs.py (stdlib string.Template) -->
---
id: $doc_id
type: feature-doc
status: generated
owner: generated
scope: feature — $slug
anchors: $anchors
verified: graph:$graph12
---

# Feature — $label

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `$graph12` · schema: $schema_version · template: feature-doc v$template_version
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `$slug` |
| Label | $label |
| Seed source | $seed_source |

## Member routes

$routes_section

## Member models

$models_section

## Apps touched

$apps_section

## Governing docs

$governing_docs
