from .dashboard import AddaDashboardView
from .product_views import ProductListView, ProductCreateView, ProductUpdateView, ProductArchiveView
from .adda_views import AddaListView, AddaCreateView, AddaDetailView
from .access_views import (
    StageListView, StageCreateView, StageUpdateView, StageDeleteView,
)
from .flow_views import ProductFlowEditView
from .pattern_views import (
    ProductPatternListView, ProductPatternCreateView,
    ProductPatternUpdateView, ProductPatternDeleteView,
    ProductPatternsEditView,
)
from .pattern_stage_views import (
    PatternWorkspaceView, PatternStartView, PatternSaveVideoView,
    PatternAddPhotoView, PatternRemovePhotoView, PatternCompleteView,
    _build_pattern_context as _build_pattern_context,
)
from .stage_views import (
    CuttingCompleteView,
    LayeringAttachRollView,
    LayeringCompleteView,
    LayeringEntryRemoveView,
    LayeringEntryUpdateView,
    LayeringFullCreateAndAttachView,
    LayeringQuickCreateAndAttachView,
    LayeringRemoveRemainingClothView,
    LayeringReopenView,
    LayeringStartView,
    LayeringWorkspaceView,
    StagePanelView,
)

__all__ = [
    'AddaDashboardView',
    'ProductListView', 'ProductCreateView', 'ProductUpdateView', 'ProductArchiveView',
    'AddaListView', 'AddaCreateView', 'AddaDetailView',
    'LayeringWorkspaceView',
    'StagePanelView',
    'LayeringStartView',
    'LayeringQuickCreateAndAttachView',
    'LayeringFullCreateAndAttachView',
    'LayeringRemoveRemainingClothView',
    'LayeringAttachRollView',
    'LayeringEntryUpdateView',
    'LayeringEntryRemoveView',
    'LayeringCompleteView',
    'LayeringReopenView',
    'CuttingCompleteView',
    'StageListView', 'StageCreateView', 'StageUpdateView', 'StageDeleteView',
    'ProductFlowEditView',
    'ProductPatternListView', 'ProductPatternCreateView',
    'ProductPatternUpdateView', 'ProductPatternDeleteView',
    'ProductPatternsEditView',
    'PatternWorkspaceView', 'PatternStartView', 'PatternSaveVideoView',
    'PatternAddPhotoView', 'PatternRemovePhotoView', 'PatternCompleteView',
]
