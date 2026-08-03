from .dashboard import ClothDashboardView, RawMaterialDashboardView
from .master_views import (
    ClothTypeListView, ClothTypeCreateView, ClothTypeUpdateView,
    ClothTypeArchiveView, ClothTypeDeleteView,
    ClothColorListView, ClothColorCreateView, ClothColorUpdateView,
    ClothColorArchiveView, ClothColorDeleteView,
    StorageLocationListView, StorageLocationCreateView, StorageLocationUpdateView,
    StorageLocationArchiveView, StorageLocationDeleteView,
)
from .roll_views import RollListView, RollBulkCreateView, RollDamageView, RollDetailView, RollUpdateView
from .assign_views import RollAssignView

__all__ = [
    'RawMaterialDashboardView', 'ClothDashboardView',
    'ClothTypeListView', 'ClothTypeCreateView', 'ClothTypeUpdateView',
    'ClothTypeArchiveView', 'ClothTypeDeleteView',
    'ClothColorListView', 'ClothColorCreateView', 'ClothColorUpdateView',
    'ClothColorArchiveView', 'ClothColorDeleteView',
    'StorageLocationListView', 'StorageLocationCreateView', 'StorageLocationUpdateView',
    'StorageLocationArchiveView', 'StorageLocationDeleteView',
    'RollListView', 'RollBulkCreateView', 'RollDetailView', 'RollUpdateView',
    'RollAssignView',
]
