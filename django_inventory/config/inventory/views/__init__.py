# Re-export everything so urls.py can keep using `from . import views` + `views.XxxView`
from .dashboard import dashboard
from .cloth_views import (
    ClothRollListView,
    ClothRollCreateView,
    ClothRollUpdateView,
    ClothRollDeleteView,
)
from .batch_views import (
    BatchListView,
    BatchCreateView,
    BatchUpdateView,
    BatchDeleteView,
    BatchDetailView,
    BatchTransitionView,
    BatchClothAssignmentCreateView,
    BatchClothAssignmentUpdateView,
    BatchUserAssignmentCreateView,
    BatchUserAssignmentUpdateView,
    BatchUserAssignmentDeleteView,
    BatchOperationCreateView,
    BatchOperationUpdateView,
    BatchOperationDeleteView,
)
from .product_views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
)
from .stage_views import (
    StageListView,
    StageCreateView,
    StageUpdateView,
    StageDeleteView,
)
from .machine_views import (
    MachineListView,
    MachineCreateView,
    MachineUpdateView,
    MachineDeleteView,
)

__all__ = [
    'dashboard',
    'ClothRollListView', 'ClothRollCreateView', 'ClothRollUpdateView', 'ClothRollDeleteView',
    'BatchListView', 'BatchCreateView', 'BatchUpdateView', 'BatchDeleteView', 'BatchDetailView', 'BatchTransitionView',
    'BatchClothAssignmentCreateView', 'BatchClothAssignmentUpdateView',
    'BatchUserAssignmentCreateView', 'BatchUserAssignmentUpdateView', 'BatchUserAssignmentDeleteView',
    'BatchOperationCreateView', 'BatchOperationUpdateView', 'BatchOperationDeleteView',
    'ProductListView', 'ProductDetailView', 'ProductCreateView', 'ProductUpdateView', 'ProductDeleteView',
    'StageListView', 'StageCreateView', 'StageUpdateView', 'StageDeleteView',
    'MachineListView', 'MachineCreateView', 'MachineUpdateView', 'MachineDeleteView',
]
