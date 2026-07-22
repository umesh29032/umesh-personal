from .dashboard import AddaDashboardView, StalledAddaListView, PendingReportListView
from .product_views import (
    ProductArchiveView, ProductCreateView, ProductListView,
    ProductSizesEditView, ProductUpdateView,
)
from .adda_views import (AddaAddLaneView, AddaBundleSetsView,
                         AddaCancelLaneView, AddaCancelView, AddaCreateView,
                         AddaDeleteView, AddaDetailView, AddaListView)
from .rate_views import StageRateListView, StageRateCorrectView
from .access_views import (
    MachineTypeCreateView, MachineTypeListView, MachineTypeUpdateView,
    StageCategoryCreateView, StageCategoryListView, StageCategoryUpdateView,
    StageListView, StageCreateView, StageUpdateView, StageDeleteView,
)
from .flow_views import ProductFlowEditView
from .pattern_views import (
    ProductPatternListView, ProductPatternCreateView,
    ProductPatternUpdateView, ProductPatternDeleteView,
    ProductPatternsEntryView, ProductPatternBlueprintRedirectView,
)
from .pattern_stage_views import (
    PatternWorkspaceView, PatternStartView, PatternSaveVideoView,
    PatternAddPhotoView, PatternRemovePhotoView, PatternCompleteView,
    PatternReopenView, PatternVerifyView, PatternUnverifyView,
    PatternSetSizesView,
)
from .barcode_gen_views import (
    BarcodeGenWorkspaceView, BarcodeGenStartView, BarcodeGenGenerateView,
    BarcodeGenCompleteView, BarcodeGenReopenView,
)
from .costing_views import ProductionCostingView
from .worker_report_views import AddaReportReviewView, AddaSnapshotView, MyAssignedWorkView, WorkerReportView
from .generic_stage_views import (
    GenericStageAllocateView, GenericStageAllocationVoidView,
    GenericStageCompleteView, GenericStageReopenView, GenericStageStartView,
)
from .stage_views import (
    CuttingAllocationDeleteView,
    CuttingBreakupDeleteView,
    CuttingBreakupSaveView,
    CuttingBundleAddPiecesView,
    CuttingBundleCreateView,
    CuttingBundleDeleteView,
    CuttingBundleItemAllocateView,
    CuttingBundleItemDeleteView,
    CuttingCompleteView,
    CuttingDraftView,
    CuttingReopenView,
    CuttingStartView,
    CuttingWorkspaceCompleteView,
    CuttingWorkspaceView,
    LayeringAttachRollView, LayeringConsumeLeftoverView,
    LayeringCompleteView,
    LayeringEntryRemoveView,
    LayeringQuickCreateAndAttachView,
    LayeringReopenView,
    LayeringStartView,
    LayeringWorkspaceView,
    StageAdvancedBounceView,
    StagePanelView,
)

__all__ = [
    'AddaDashboardView',
    'StalledAddaListView',
    'PendingReportListView',
    'AddaReportReviewView',
    'AddaSnapshotView',
    'MyAssignedWorkView',
    'WorkerReportView',
    'ProductListView', 'ProductCreateView', 'ProductUpdateView', 'ProductArchiveView',
    'ProductSizesEditView',
    'AddaListView', 'AddaCreateView', 'AddaDetailView', 'AddaBundleSetsView',
    'AddaAddLaneView', 'AddaCancelLaneView', 'AddaCancelView', 'AddaDeleteView',
    'StageRateListView', 'StageRateCorrectView',
    'LayeringWorkspaceView',
    'GenericStageStartView',
    'GenericStageCompleteView',
    'GenericStageReopenView',
    'GenericStageAllocateView',
    'GenericStageAllocationVoidView',
    'StageAdvancedBounceView',
    'StagePanelView',
    'LayeringStartView',
    'LayeringQuickCreateAndAttachView',
    'LayeringAttachRollView',
    'LayeringConsumeLeftoverView',
    'LayeringEntryRemoveView',
    'LayeringCompleteView',
    'LayeringReopenView',
    'CuttingCompleteView',
    'CuttingWorkspaceView',
    'CuttingStartView',
    'CuttingBreakupSaveView',
    'CuttingBreakupDeleteView',
    'CuttingBundleCreateView',
    'CuttingBundleAddPiecesView',
    'CuttingBundleItemDeleteView',
    'CuttingBundleDeleteView',
    'CuttingBundleItemAllocateView',
    'CuttingAllocationDeleteView',
    'ProductionCostingView',
    'CuttingDraftView',
    'CuttingWorkspaceCompleteView',
    'CuttingReopenView',
    'StageListView', 'StageCreateView', 'StageUpdateView', 'StageDeleteView',
    'MachineTypeListView', 'MachineTypeCreateView', 'MachineTypeUpdateView',
    'StageCategoryListView', 'StageCategoryCreateView', 'StageCategoryUpdateView',
    'ProductFlowEditView',
    'ProductPatternListView', 'ProductPatternCreateView',
    'ProductPatternUpdateView', 'ProductPatternDeleteView',
    'ProductPatternsEntryView', 'ProductPatternBlueprintRedirectView',
    'PatternWorkspaceView', 'PatternStartView', 'PatternSaveVideoView',
    'PatternAddPhotoView', 'PatternRemovePhotoView', 'PatternCompleteView',
    'PatternReopenView', 'PatternVerifyView', 'PatternUnverifyView',
    'PatternSetSizesView',
    'BarcodeGenWorkspaceView', 'BarcodeGenStartView', 'BarcodeGenGenerateView',
    'BarcodeGenCompleteView', 'BarcodeGenReopenView',
]
