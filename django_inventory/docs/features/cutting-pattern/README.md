---
id: feature-cutting-pattern
type: feature-doc
status: generated
owner: generated
scope: feature — cutting-pattern
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:4ed4a2180bcf
---

# Feature — Cutting-pattern (display: "Pattern Design" — stage-trio spec 2026-07-05)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `cutting-pattern` |
| Label | Cutting-pattern (display: "Pattern Design" — stage-trio spec 2026-07-05) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `production:pattern-complete` | `/production/addas/<str:code>/pattern/complete/` | `PatternCompleteView` | [pattern-complete.md](pattern-complete.md) |
| `production:pattern-photo-remove` | `/production/addas/<str:code>/pattern/photos/<int:pk>/remove/` | `PatternRemovePhotoView` | [pattern-photo-remove.md](pattern-photo-remove.md) |
| `production:pattern-photos-add` | `/production/addas/<str:code>/pattern/photos/add/` | `PatternAddPhotoView` | [pattern-photos-add.md](pattern-photos-add.md) |
| `production:pattern-reopen` | `/production/addas/<str:code>/pattern/reopen/` | `PatternReopenView` | [pattern-reopen.md](pattern-reopen.md) |
| `production:pattern-save` | `/production/addas/<str:code>/pattern/save/` | `PatternSaveVideoView` | [pattern-save.md](pattern-save.md) |
| `production:pattern-set-sizes` | `/production/addas/<str:code>/pattern/sizes/` | `PatternSetSizesView` | [pattern-set-sizes.md](pattern-set-sizes.md) |
| `production:pattern-start` | `/production/addas/<str:code>/pattern/start/` | `PatternStartView` | [pattern-start.md](pattern-start.md) |
| `production:pattern-unverify` | `/production/addas/<str:code>/pattern/unverify/` | `PatternUnverifyView` | [pattern-unverify.md](pattern-unverify.md) |
| `production:pattern-verify` | `/production/addas/<str:code>/pattern/verify/` | `PatternVerifyView` | [pattern-verify.md](pattern-verify.md) |
| `production:pattern-workspace` | `/production/addas/<str:code>/pattern/` | `PatternWorkspaceView` | [pattern-workspace.md](pattern-workspace.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `production.CuttingPatternRecord` | `production_cuttingpatternrecord` | not machine-known |

## Apps touched

- `production` — [config/production/README.md](../../../config/production/README.md) · [docs/apps/production/GUIDE.md](../../apps/production/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
