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
    save_layering_breakup,
    save_layering_draft,
    start_layering,
    sync_layering_workers_for_skill,
    update_layering_roll_entry,
)
from .cutting_service import complete_cutting
from .activity_service import adda_activity, user_activity_across_addas

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
    'get_layering_snapshot',
    # Cutting stage
    'complete_cutting',
    # Activity
    'adda_activity',
    'user_activity_across_addas',
]
