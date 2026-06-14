"""Well-known Stage.code values.

These constants used to live as `WorkflowStage.StageType` enum entries. After
the Stage model became a first-class CRUD-managed table, the enum was
retired but services + tests still need stable string keys to look up the
right Stage row. Don't add new entries here unless the service layer truly
hard-codes against a specific stage (most code should use the Stage table).
"""

STAGE_LAYERING = 'layering'
STAGE_CUTTING_PATTERN = 'cutting_pattern'
STAGE_CUTTING = 'cutting'
# Barcode generation = stage AFTER cutting (PR-A 2026-05-29). Optional per
# product workflow — some products skip it entirely. Cutting completion
# materializes verified breakdown; barcode_generation consumes that breakdown.
STAGE_BARCODE_GENERATION = 'barcode_generation'

# ── Piece-pool grain (Foundation S4 / D1) ────────────────────────────────────
# Canonical values for WorkflowStage.allocation_dimensions + each handler's
# pool_grain. Governs PIECE-POOL behaviour ONLY — orthogonal to settlement
# (WorkflowStage.credits_workers) and costing (WorkflowStage.cost_method).
#   NONE       = not a piece-pool stage (pre-piece: layering/cutting_pattern/barcode).
#   QUANTITY   = piece-pool at scalar grain (a future downstream piece stage).
#   COLOR_SIZE = piece-pool at (color,size) grain — the pool SOURCE (cutting).
# Leaf module → handlers import these without importing models. Owner-locked
# 2026-06-14: pool starts at CUTTING; pre-piece stages are NONE.
ALLOC_DIM_NONE = 'none'
ALLOC_DIM_QUANTITY = 'quantity'
ALLOC_DIM_COLOR_SIZE = 'color_size'
