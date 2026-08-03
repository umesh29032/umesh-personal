---
id: feature-operations-dashboards
type: feature-doc
status: generated
owner: generated
scope: feature — operations-dashboards
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:4ed4a2180bcf
---

# Feature — Operations dashboards (adda · raw material · cloth · personal · BOD)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `operations-dashboards` |
| Label | Operations dashboards (adda · raw material · cloth · personal · BOD) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `bod:dashboard` | `/bod/` | `BODDashboardView` | [bod__dashboard.md](bod__dashboard.md) |
| `inventory:inventory_dashboard` | `/inventory/dashboard/` | `dashboard_redirect` | [inventory_dashboard.md](inventory_dashboard.md) |
| `inventory:my_dashboard` | `/inventory/my-dashboard/` | `user_dashboard` | [my_dashboard.md](my_dashboard.md) |
| `inventory:styleguide` | `/inventory/styleguide/` | `TemplateView` | [styleguide.md](styleguide.md) |
| `inventory:user_dashboard` | `/inventory/my-dashboard/legacy/` | `dashboard_redirect` | [user_dashboard.md](user_dashboard.md) |
| `production:dashboard` | `/production/` | `AddaDashboardView` | [production__dashboard.md](production__dashboard.md) |
| `production:pending-reports` | `/production/pending-reports/` | `PendingReportListView` | [pending-reports.md](pending-reports.md) |
| `production:stalled-addas` | `/production/stalled/` | `StalledAddaListView` | [stalled-addas.md](stalled-addas.md) |
| `raw_materials:cloth-dashboard` | `/raw-materials/cloth/` | `ClothDashboardView` | [cloth-dashboard.md](cloth-dashboard.md) |
| `raw_materials:dashboard` | `/raw-materials/` | `RawMaterialDashboardView` | [raw_materials__dashboard.md](raw_materials__dashboard.md) |

## Member models

No machine-provable member models (`belongs_to_feature` model edges: 0).

## Apps touched

- `bod` — [config/bod/README.md](../../../config/bod/README.md) · [docs/apps/bod/GUIDE.md](../../apps/bod/GUIDE.md)
- `inventory` — [config/inventory/README.md](../../../config/inventory/README.md) · [docs/apps/inventory/GUIDE.md](../../apps/inventory/GUIDE.md)
- `production` — [config/production/README.md](../../../config/production/README.md) · [docs/apps/production/GUIDE.md](../../apps/production/GUIDE.md)
- `raw_materials` — [config/raw_materials/README.md](../../../config/raw_materials/README.md) · [docs/apps/raw_materials/GUIDE.md](../../apps/raw_materials/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
