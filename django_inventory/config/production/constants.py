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
