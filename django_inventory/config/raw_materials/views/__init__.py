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
    # RollDamageView was missing from __all__ while being imported above and used by
    # urls.py as `views.RollDamageView` — attribute access works regardless of __all__,
    # so the URL functioned, but the declared public API was wrong and ruff (F401) read
    # the import as unused. Deleting the import — ruff's other suggestion — would have
    # broken the roll-damage route. Adding it here is the correct half of the fix.
    'RollListView', 'RollBulkCreateView', 'RollDamageView', 'RollDetailView',
    'RollUpdateView',
    'RollAssignView',
]
