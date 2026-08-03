---
id: feature-layering
type: feature-doc
status: generated
owner: generated
scope: feature — layering
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:f48dc8b77c29
---

# Feature — Layering

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `f48dc8b77c29` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `layering` |
| Label | Layering |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `production:layering-attach-roll` | `/production/addas/<str:code>/layering/attach-roll/` | `LayeringAttachRollView` | [layering-attach-roll.md](layering-attach-roll.md) |
| `production:layering-complete` | `/production/addas/<str:code>/layering/complete/` | `LayeringCompleteView` | [layering-complete.md](layering-complete.md) |
| `production:layering-entry-remove` | `/production/addas/<str:code>/layering/entries/<int:pk>/remove/` | `LayeringEntryRemoveView` | [layering-entry-remove.md](layering-entry-remove.md) |
| `production:layering-quick-create-roll` | `/production/addas/<str:code>/layering/quick-create-roll/` | `LayeringQuickCreateAndAttachView` | [layering-quick-create-roll.md](layering-quick-create-roll.md) |
| `production:layering-reopen` | `/production/addas/<str:code>/layering/reopen/` | `LayeringReopenView` | [layering-reopen.md](layering-reopen.md) |
| `production:layering-start` | `/production/addas/<str:code>/layering/start/` | `LayeringStartView` | [layering-start.md](layering-start.md) |
| `production:layering-workspace` | `/production/addas/<str:code>/layering/` | `LayeringWorkspaceView` | [layering-workspace.md](layering-workspace.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `production.LayeringRecord` | `production_layeringrecord` | not machine-known |

## Apps touched

- `production` — [config/production/README.md](../../../config/production/README.md) · [docs/apps/production/GUIDE.md](../../apps/production/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
