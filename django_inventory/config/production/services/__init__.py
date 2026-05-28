"""Production services — per-stage isolation.

Pattern (Phase 6+):
  services/_shared.py             — auth helpers shared across stages
  services/layering_service.py    — Stage 1 (Layering) state transitions
  services/cutting_service.py     — Stage 2 (Cutting) state transitions
  services/adda_service.py        — Adda lifecycle (create + advance)
  services/product_service.py     — Product CRUD
  services/activity_service.py    — Activity timeline derivation
  services/stage_service.py       — back-compat shim re-exporting everything

Future stages = drop in services/<stage>_service.py + re-export here.
"""
from .adda_service import create_adda, advance_to_next_stage
from .product_service import create_product, update_product, archive_product
from .layering_service import (
    attach_roll_to_layering,
    complete_layering,
    detach_roll_from_layering,
    get_layering_snapshot,
    record_remaining_cloth,
    remove_remaining_cloth,
    reopen_layering,
    save_layering_breakup,
    save_layering_draft,
    start_layering,
    sync_layering_workers_for_skill,
    update_layering_roll_entry,
)
from .cutting_service import complete_cutting
from .cutting_pattern_service import (
    attach_photo as attach_pattern_photo,
    complete_pattern_stage,
    get_or_create_pattern_stage_record,
    get_pattern_snapshot,
    save_pattern_record,
    start_pattern_stage,
)
from .activity_service import adda_activity, user_activity_across_addas
from .access_service import user_can_access_stage, stage_access_map
from .flow_service import (
    add_stage_to_product_flow,
    move_stage_in_product_flow,
    remove_stage_from_product_flow,
)

__all__ = [
    'create_adda',
    'advance_to_next_stage',
    'create_product',
    'update_product',
    'archive_product',
    # Layering stage
    'start_layering',
    'sync_layering_workers_for_skill',
    'attach_roll_to_layering',
    'update_layering_roll_entry',
    'detach_roll_from_layering',
    'save_layering_breakup',
    'save_layering_draft',
    'record_remaining_cloth',
    'remove_remaining_cloth',
    'complete_layering',
    'reopen_layering',
    'get_layering_snapshot',
    # Cutting stage
    'complete_cutting',
    # Cutting-pattern stage
    'start_pattern_stage',
    'attach_pattern_photo',
    'save_pattern_record',
    'complete_pattern_stage',
    'get_or_create_pattern_stage_record',
    'get_pattern_snapshot',
    # Activity
    'adda_activity',
    'user_activity_across_addas',
    # Stage access control (DB-driven)
    'user_can_access_stage',
    'stage_access_map',
    # Product flow management
    'add_stage_to_product_flow',
    'remove_stage_from_product_flow',
    'move_stage_in_product_flow',
]
