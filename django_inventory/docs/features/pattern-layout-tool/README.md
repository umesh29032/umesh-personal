---
id: feature-pattern-layout-tool
type: feature-doc
status: generated
owner: generated
scope: feature — pattern-layout-tool
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:4ed4a2180bcf
---

# Feature — Pattern layout tool (blueprint → usage → outcome/void; READY gate; exports)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `4ed4a2180bcf` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `pattern-layout-tool` |
| Label | Pattern layout tool (blueprint → usage → outcome/void; READY gate; exports) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `patterns_ai:advisor` | `/patterns/advisor/` | `AdvisorView` | [advisor.md](advisor.md) |
| `patterns_ai:blueprint` | `/patterns/blueprint/` | `PatternBlueprintView` | [blueprint.md](blueprint.md) |
| `patterns_ai:candidate-approve` | `/patterns/candidates/<int:pk>/approve/` | `ApproveProductionView` | [candidate-approve.md](candidate-approve.md) |
| `patterns_ai:candidate-detail` | `/patterns/candidates/<int:pk>/` | `CandidateDetailView` | [candidate-detail.md](candidate-detail.md) |
| `patterns_ai:candidate-pdf` | `/patterns/candidates/<int:pk>/pdf/` | `CandidatePdfView` | [candidate-pdf.md](candidate-pdf.md) |
| `patterns_ai:candidate-print` | `/patterns/candidates/<int:pk>/print/` | `CandidatePrintView` | [candidate-print.md](candidate-print.md) |
| `patterns_ai:candidate-svg` | `/patterns/candidates/<int:pk>/svg/` | `CandidateSvgView` | [candidate-svg.md](candidate-svg.md) |
| `patterns_ai:capture-thumb` | `/patterns/captures/<int:pk>/thumb/` | `MarkerThumbView` | [capture-thumb.md](capture-thumb.md) |
| `patterns_ai:choose-layout` | `/patterns/table-usage/<int:pk>/` | `ChooseLayoutView` | [choose-layout.md](choose-layout.md) |
| `patterns_ai:cutting-table` | `/patterns/table/<int:pk>/` | `CuttingTableShellView` | [cutting-table.md](cutting-table.md) |
| `patterns_ai:cutting-table-optimize` | `/patterns/table/<int:pk>/optimize/` | `CuttingTableOptimizeView` | [cutting-table-optimize.md](cutting-table-optimize.md) |
| `patterns_ai:dashboard` | `/patterns/dashboard/` | `PatternDashboardView` | [dashboard.md](dashboard.md) |
| `patterns_ai:dxf-import` | `/patterns/pieces/<int:pk>/dxf-import/` | `DxfImportView` | [dxf-import.md](dxf-import.md) |
| `patterns_ai:extraction-review` | `/patterns/extractions/<int:pk>/review/` | `ExtractionReviewView` | [extraction-review.md](extraction-review.md) |
| `patterns_ai:generate` | `/patterns/generate/` | `GenerateMarkerView` | [generate.md](generate.md) |
| `patterns_ai:generation-run` | `/patterns/runs/<int:pk>/` | `GenerationRunView` | [generation-run.md](generation-run.md) |
| `patterns_ai:geometry-dxf` | `/patterns/geometry/<int:pk>/dxf/` | `GeometryDxfView` | [geometry-dxf.md](geometry-dxf.md) |
| `patterns_ai:geometry-edit` | `/patterns/geometry/<int:pk>/edit/` | `GeometryEditorView` | [geometry-edit.md](geometry-edit.md) |
| `patterns_ai:geometry-print` | `/patterns/geometry/<int:pk>/print/` | `GeometryPrintView` | [geometry-print.md](geometry-print.md) |
| `patterns_ai:geometry-svg` | `/patterns/geometry/<int:pk>/svg/` | `GeometrySvgView` | [geometry-svg.md](geometry-svg.md) |
| `patterns_ai:home` | `/patterns/` | `PatternHomeView` | [home.md](home.md) |
| `patterns_ai:insights` | `/patterns/insights/` | `InsightsView` | [insights.md](insights.md) |
| `patterns_ai:manual-marker-created` | `/patterns/markers/<str:reference>/created/` | `ManualMarkerCreatedView` | [manual-marker-created.md](manual-marker-created.md) |
| `patterns_ai:manual-marker-new` | `/patterns/markers/manual/new/` | `ManualMarkerCreateView` | [manual-marker-new.md](manual-marker-new.md) |
| `patterns_ai:marker-detail` | `/patterns/markers/<str:reference>/` | `MarkerDetailView` | [marker-detail.md](marker-detail.md) |
| `patterns_ai:marker-list` | `/patterns/markers/` | `MarkerListView` | [marker-list.md](marker-list.md) |
| `patterns_ai:mat-commission` | `/patterns/mats/<int:pk>/commission/` | `MatCommissionView` | [mat-commission.md](mat-commission.md) |
| `patterns_ai:mat-detail` | `/patterns/mats/<int:pk>/` | `MatDetailView` | [mat-detail.md](mat-detail.md) |
| `patterns_ai:mat-list` | `/patterns/mats/` | `MatListView` | [mat-list.md](mat-list.md) |
| `patterns_ai:mat-new` | `/patterns/mats/new/` | `MatRegisterView` | [mat-new.md](mat-new.md) |
| `patterns_ai:mat-recheck` | `/patterns/mats/<int:pk>/recheck/` | `MatRecheckView` | [mat-recheck.md](mat-recheck.md) |
| `patterns_ai:mat-retire` | `/patterns/mats/<int:pk>/retire/` | `MatRetireView` | [mat-retire.md](mat-retire.md) |
| `patterns_ai:outcome-new` | `/patterns/usages/<int:pk>/outcome/new/` | `MarkerOutcomeCreateView` | [outcome-new.md](outcome-new.md) |
| `patterns_ai:pattern-capture` | `/patterns/pieces/<int:pk>/capture/` | `PatternCaptureView` | [pattern-capture.md](pattern-capture.md) |
| `patterns_ai:piece-detail` | `/patterns/pieces/<int:pk>/` | `PieceDetailView` | [piece-detail.md](piece-detail.md) |
| `patterns_ai:piece-list` | `/patterns/pieces/` | `PieceListView` | [piece-list.md](piece-list.md) |
| `patterns_ai:studio` | `/patterns/studio/` | `StudioView` | [studio.md](studio.md) |
| `patterns_ai:studio-evidence-count` | `/patterns/studio/work/<int:piece_pk>/<int:size_pk>/evidence-count/` | `StudioEvidenceCountView` | [studio-evidence-count.md](studio-evidence-count.md) |
| `patterns_ai:studio-work` | `/patterns/studio/work/<int:piece_pk>/<int:size_pk>/` | `StudioWorkView` | [studio-work.md](studio-work.md) |
| `patterns_ai:table-approve` | `/patterns/table/<int:pk>/approve/<int:cand>/` | `CuttingTableApproveView` | [table-approve.md](table-approve.md) |
| `patterns_ai:table-layout-archive` | `/patterns/table/<int:pk>/layouts/<int:lid>/archive/` | `CuttingTableLayoutArchiveView` | [table-layout-archive.md](table-layout-archive.md) |
| `patterns_ai:table-recipe` | `/patterns/table/<int:pk>/recipe/` | `CuttingTableRecipeView` | [table-recipe.md](table-recipe.md) |
| `patterns_ai:table-save` | `/patterns/table/<int:pk>/save/` | `CuttingTableSaveView` | [table-save.md](table-save.md) |
| `patterns_ai:tool` | `/patterns/tool/<int:product_pk>/` | `ToolRedirectView` | [tool.md](tool.md) |
| `patterns_ai:usage-new` | `/patterns/markers/<str:reference>/usage/new/` | `MarkerUsageCreateView` | [usage-new.md](usage-new.md) |
| `patterns_ai:usage-void` | `/patterns/usages/<int:pk>/void/` | `MarkerUsageVoidView` | [usage-void.md](usage-void.md) |
| `patterns_ai:version-confirm` | `/patterns/versions/<int:pk>/confirm/` | `VersionConfirmView` | [version-confirm.md](version-confirm.md) |
| `patterns_ai:version-detail` | `/patterns/versions/<int:pk>/` | `VersionDetailView` | [version-detail.md](version-detail.md) |
| `patterns_ai:version-next` | `/patterns/pieces/<int:pk>/next-version/` | `VersionStartNextView` | [version-next.md](version-next.md) |
| `patterns_ai:version-reject` | `/patterns/versions/<int:pk>/reject/` | `VersionRejectView` | [version-reject.md](version-reject.md) |
| `patterns_ai:workspace` | `/patterns/workspace/<int:pk>/` | `WorkspaceView` | [workspace.md](workspace.md) |
| `patterns_ai:yield-board` | `/patterns/yield/` | `YieldBoardView` | [yield-board.md](yield-board.md) |

## Member models

No machine-provable member models (`belongs_to_feature` model edges: 0).

## Apps touched

- `patterns_ai` — [config/patterns_ai/README.md](../../../config/patterns_ai/README.md) · [docs/apps/patterns_ai/GUIDE.md](../../apps/patterns_ai/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).
