"""Well-known Stage.code values.

These constants used to live as `WorkflowStage.StageType` enum entries. After
the Stage model became a first-class CRUD-managed table, the enum was
retired but services + tests still need stable string keys to look up the
right Stage row. Don't add new entries here unless the service layer truly
hard-codes against a specific stage (most code should use the Stage table).
"""

STAGE_LAYERING = 'layering'
STAGE_CUTTING = 'cutting'
