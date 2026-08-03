---
id: url-card-accounts-skill-list
type: url-card
status: generated
owner: generated
scope: route — url:accounts:skill_list
anchors: config/config/urls.py
verified: graph:4ed4a2180bcf
---

# URL card — `skill_list`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: url-card v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `skill_list` |
| Namespace | `accounts` |
| Mount | `/app/skills/` |
| Pattern | `skills/` |
| Named | true |

## View

| Field | Value |
|---|---|
| View | `SkillListView` |
| Module | `accounts.views` |
| Defined in | `config/accounts/views.py` |
| Vendor | false |

## App

Derived from the view module (`accounts.views` → app `accounts`; a render rule, not a graph edge).

App documentation: [config/accounts/README.md](../../../config/accounts/README.md) · [docs/apps/accounts/GUIDE.md](../../apps/accounts/GUIDE.md)

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

[User/role admin](README.md) (`user-role-admin`, via `belongs_to_feature`)

## Governing docs

Feature seed: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md`

## Mobile strategy

Not machine-known — the graph carries no mobile-strategy data for this route.
