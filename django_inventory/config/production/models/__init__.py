"""Production app models — domain-split package (was a single 1200-line models.py).

YEH PACKAGE KYU HAI?
────────────────────
Models ab subdomain ke hisaab se files mein bate hain (navigation + merge-conflict
surface chhota). Ye __init__ public facade hai — sab models yahan se re-export
hote hain, taaki `from production.models import X` (aur purani migrations jo
`production.models._cutting_pattern_video_path` reference karti hain) bina change
ke chalti rahein. App label + table names same hain → koi schema migration nahi
(sirf upload_to callable ka path move ek no-SQL AlterField generate karta hai).

Subdomain map:
  core.py      → CostMethod, Product, Stage, WorkflowStage, WorkflowStageRoleRate,
                 AddaStageRoleRate, RateCorrectionAudit
  adda.py      → Adda, AddaStageRecord  (polymorphic stage-execution parent)
  layering.py  → LayeringRecord, LayeringRollEntry, RemainingClothOfClothRoll
  cutting.py   → CuttingRecord, ProductPattern(+Assignment), CuttingPatternRecord(+Photo),
                 ProductSize, CuttingPatternVerification/SizeAllocation,
                 CuttingPieceBreakup, CuttingBundle(+Item), AddaProductSizeColorPieceBreakdown
  barcode.py   → BarcodeGenerationRecord, LabelPrintQueue
"""
from .core import (
    CostMethod,
    Product,
    Stage,
    WorkflowStage,
    WorkflowStageRoleRate,
    AddaStageRoleRate,
    RateCorrectionAudit,
)
from .adda import (
    Adda,
    AddaStageRecord,
)
from .layering import (
    LayeringRecord,
    LayeringRollEntry,
    RemainingClothOfClothRoll,
)
from .cutting import (
    CuttingRecord,
    ProductPattern,
    ProductPatternAssignment,
    CuttingPatternRecord,
    CuttingPatternPhoto,
    ProductSize,
    CuttingPatternVerification,
    CuttingPatternSizeAllocation,
    CuttingPieceBreakup,
    CuttingBundle,
    CuttingBundleItem,
    AddaProductSizeColorPieceBreakdown,
    # Upload-path callables — re-exported so existing migrations that reference
    # `production.models._cutting_pattern_video_path` keep resolving.
    _cutting_pattern_video_path,
    _cutting_pattern_photo_path,
)
from .barcode import (
    BarcodeGenerationRecord,
    LabelPrintQueue,
)
from .worker_task import (
    WorkerStageTask,
    WorkerStageContribution,
)

__all__ = [
    'CostMethod',
    'Product',
    'Stage',
    'WorkflowStage',
    'WorkflowStageRoleRate',
    'AddaStageRoleRate',
    'RateCorrectionAudit',
    'Adda',
    'AddaStageRecord',
    'LayeringRecord',
    'LayeringRollEntry',
    'RemainingClothOfClothRoll',
    'CuttingRecord',
    'ProductPattern',
    'ProductPatternAssignment',
    'CuttingPatternRecord',
    'CuttingPatternPhoto',
    'ProductSize',
    'CuttingPatternVerification',
    'CuttingPatternSizeAllocation',
    'CuttingPieceBreakup',
    'CuttingBundle',
    'CuttingBundleItem',
    'AddaProductSizeColorPieceBreakdown',
    'BarcodeGenerationRecord',
    'LabelPrintQueue',
    'WorkerStageTask',
    'WorkerStageContribution',
    '_cutting_pattern_video_path',
    '_cutting_pattern_photo_path',
]
