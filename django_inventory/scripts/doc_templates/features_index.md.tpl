<!-- template: features-index v1.0.0 — consumed by scripts/generate_docs.py (stdlib string.Template) -->
---
id: features-index
type: feature-doc
status: generated
owner: generated
scope: all — the generated features layer master index
anchors: docs/knowledge_graph.json
verified: graph:$graph12
---

# Features — generated master index

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `$graph12` · schema: $schema_version · template: features-index v$template_version
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

One row per feature node in the knowledge graph (seed: FEATURE_INDEX.md). Route/model
membership counts come from `belongs_to_feature` edges — machine-provable membership only;
enriching membership happens at the SOURCE (FEATURE_INDEX), never here.

| Feature | Slug | Routes | Models | Doc |
|---|---|---|---|---|
$feature_rows

## Coverage arithmetic

$coverage
