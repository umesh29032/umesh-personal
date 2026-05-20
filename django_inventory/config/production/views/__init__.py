from .dashboard import AddaDashboardView
from .product_views import ProductListView, ProductCreateView, ProductUpdateView, ProductArchiveView
from .adda_views import AddaListView, AddaCreateView, AddaDetailView
from .stage_views import (
    CuttingCompleteView,
    LayeringAttachRollView,
    LayeringCompleteView,
    LayeringEntryRemoveView,
    LayeringEntryUpdateView,
    LayeringFullCreateAndAttachView,
    LayeringQuickCreateAndAttachView,
    LayeringRemoveRemainingClothView,
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
    'CuttingCompleteView',
]
