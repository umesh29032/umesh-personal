"""patterns_ai URLs — Block 3C adds the read-only library."""
from django.urls import path

from . import views

app_name = 'patterns_ai'

urlpatterns = [
    path('', views.PatternHomeView.as_view(), name='home'),
    # Phase 1: the Pattern Dashboard — permanent home of all pattern work
    # (STEP 1 Blueprint → STEP 2 Manager → STEP 3 Digital Cutting Table).
    path('dashboard/', views.PatternDashboardView.as_view(),
         name='dashboard'),
    # Phase 2: STEP 1 — the Pattern Blueprint module (structure + rules).
    path('blueprint/', views.PatternBlueprintView.as_view(),
         name='blueprint'),
    # M2: the Pattern Intelligence Studio — one room, two modes
    # (BROWSE = the Pattern Library shelf · WORK = one piece × size).
    path('studio/', views.StudioView.as_view(), name='studio'),
    path('studio/work/<int:piece_pk>/<int:size_pk>/',
         views.StudioWorkView.as_view(), name='studio-work'),
    path('studio/work/<int:piece_pk>/<int:size_pk>/evidence-count/',
         views.StudioEvidenceCountView.as_view(),
         name='studio-evidence-count'),
    # Phase 4: STEP 3 — the Digital Cutting Table (shell; the permanent
    # workspace — interactions arrive Phase 5+).
    path('table/<int:pk>/', views.CuttingTableShellView.as_view(),
         name='cutting-table'),
    # Phase 6C: stateless AI optimize (contract: session in → positions
    # out; ZERO writes — the service is test-walled).
    path('table/<int:pk>/optimize/',
         views.CuttingTableOptimizeView.as_view(),
         name='cutting-table-optimize'),
    # Phase 7: the ONE save pipeline (Save Draft ≠ Approve — rules 2/8).
    path('table/<int:pk>/save/', views.CuttingTableSaveView.as_view(),
         name='table-save'),
    # M4: save the session's Marker Plan as a Marker Recipe (knowledge)
    path('table/<int:pk>/recipe/', views.CuttingTableRecipeView.as_view(),
         name='table-recipe'),
    path('table/<int:pk>/approve/<int:cand>/',
         views.CuttingTableApproveView.as_view(), name='table-approve'),
    path('table/<int:pk>/layouts/<int:lid>/archive/',
         views.CuttingTableLayoutArchiveView.as_view(),
         name='table-layout-archive'),
    # Phase 8B: the Adda chooses its manufacturing contract (rule 9).
    path('table-usage/<int:pk>/', views.ChooseLayoutView.as_view(),
         name='choose-layout'),
    path('markers/', views.MarkerListView.as_view(), name='marker-list'),
    path('yield/', views.YieldBoardView.as_view(), name='yield-board'),
    path('markers/manual/new/', views.ManualMarkerCreateView.as_view(),
         name='manual-marker-new'),
    path('markers/<str:reference>/created/',
         views.ManualMarkerCreatedView.as_view(),
         name='manual-marker-created'),
    path('markers/<str:reference>/usage/new/',
         views.MarkerUsageCreateView.as_view(), name='usage-new'),
    path('usages/<int:pk>/void/', views.MarkerUsageVoidView.as_view(),
         name='usage-void'),
    path('usages/<int:pk>/outcome/new/',
         views.MarkerOutcomeCreateView.as_view(), name='outcome-new'),
    path('markers/<str:reference>/', views.MarkerDetailView.as_view(),
         name='marker-detail'),
    path('captures/<int:pk>/thumb/', views.MarkerThumbView.as_view(),
         name='capture-thumb'),
    # ── P2 geometry era ─────────────────────────────────────────────────
    path('mats/', views.MatListView.as_view(), name='mat-list'),
    path('mats/new/', views.MatRegisterView.as_view(), name='mat-new'),
    path('mats/<int:pk>/', views.MatDetailView.as_view(), name='mat-detail'),
    path('mats/<int:pk>/commission/', views.MatCommissionView.as_view(),
         name='mat-commission'),
    path('mats/<int:pk>/retire/', views.MatRetireView.as_view(),
         name='mat-retire'),
    path('mats/<int:pk>/recheck/', views.MatRecheckView.as_view(),
         name='mat-recheck'),
    path('pieces/', views.PieceListView.as_view(), name='piece-list'),
    # piece-new retired (Phase 2): registration lives in the Blueprint
    path('pieces/<int:pk>/', views.PieceDetailView.as_view(),
         name='piece-detail'),
    path('pieces/<int:pk>/capture/', views.PatternCaptureView.as_view(),
         name='pattern-capture'),
    path('pieces/<int:pk>/next-version/',
         views.VersionStartNextView.as_view(), name='version-next'),
    path('pieces/<int:pk>/dxf-import/', views.DxfImportView.as_view(),
         name='dxf-import'),
    path('extractions/<int:pk>/review/',
         views.ExtractionReviewView.as_view(), name='extraction-review'),
    path('versions/<int:pk>/', views.VersionDetailView.as_view(),
         name='version-detail'),
    path('versions/<int:pk>/confirm/', views.VersionConfirmView.as_view(),
         name='version-confirm'),
    path('versions/<int:pk>/reject/', views.VersionRejectView.as_view(),
         name='version-reject'),
    path('geometry/<int:pk>/edit/', views.GeometryEditorView.as_view(),
         name='geometry-edit'),
    path('geometry/<int:pk>/svg/', views.GeometrySvgView.as_view(),
         name='geometry-svg'),
    path('geometry/<int:pk>/dxf/', views.GeometryDxfView.as_view(),
         name='geometry-dxf'),
    path('geometry/<int:pk>/print/', views.GeometryPrintView.as_view(),
         name='geometry-print'),
    # ── P3 marker generation ────────────────────────────────────────────
    path('generate/', views.GenerateMarkerView.as_view(), name='generate'),
    path('runs/<int:pk>/', views.GenerationRunView.as_view(),
         name='generation-run'),
    path('candidates/<int:pk>/', views.CandidateDetailView.as_view(),
         name='candidate-detail'),
    path('candidates/<int:pk>/svg/', views.CandidateSvgView.as_view(),
         name='candidate-svg'),
    # ── Phase 6 M7: the explicit audited Approve act (§3g) ──────────────
    path('candidates/<int:pk>/approve/',
         views.ApproveProductionView.as_view(), name='candidate-approve'),
    # ── Phase 6 M8: production exports (PDF + tiled true-scale print) ───
    path('candidates/<int:pk>/pdf/', views.CandidatePdfView.as_view(),
         name='candidate-pdf'),
    path('candidates/<int:pk>/print/', views.CandidatePrintView.as_view(),
         name='candidate-print'),
    # ── P4 the Cut Advisor ──────────────────────────────────────────────
    path('advisor/', views.AdvisorView.as_view(), name='advisor'),
    # ── P5 management insights ──────────────────────────────────────────
    path('insights/', views.InsightsView.as_view(), name='insights'),
    # ── ROADMAP_V2 Phase 4: interactive marker workspace ────────────────
    path('workspace/<int:pk>/', views.WorkspaceView.as_view(),
         name='workspace'),
    # ── Phase 6 M4: the ONE entry — smart redirect (INTEGRATION_DESIGN §2)
    path('tool/<int:product_pk>/', views.ToolRedirectView.as_view(),
         name='tool'),
]
