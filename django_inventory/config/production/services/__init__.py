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
from .product_size_service import (
    add_product_size, archive_product_size, reactivate_product_size,
    update_product_size,
)
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
from .cutting_service import (
    add_bundle_item,
    add_item_to_bundle,
    add_pieces_to_bundle,
    complete_cutting,
    create_bundle,
    create_bundle_with_pieces,
    delete_breakup_row,
    delete_bundle,
    delete_bundle_item,
    get_cutting_snapshot,
    get_suggested_breakup,
    preview_barcode_batches,
    reopen_cutting,
    save_cutting_draft,
    start_cutting,
    upsert_breakup_row,
)
from .cutting_pattern_service import (
    attach_photo as attach_pattern_photo,
    complete_pattern_stage,
    ensure_pattern_record,
    get_or_create_pattern_stage_record,
    get_pattern_snapshot,
    reopen_pattern_stage,
    save_pattern_record,
    set_size_allocation,
    start_pattern_stage,
    unverify_pattern,
    verify_pattern,
)
from .barcode_generation_service import (
    complete_barcode_generation,
    generate_barcodes,
    get_barcode_snapshot,
    get_or_create_barcode_stage_record,
    preview_barcode_counts,
    reopen_barcode_generation,
    start_barcode_generation,
)
from .activity_service import adda_activity, user_activity_across_addas
from .access_service import user_can_access_stage, stage_access_map
from .flow_service import (
    add_stage_to_product_flow,
    move_stage_in_product_flow,
    remove_stage_from_product_flow,
    set_stage_cost,
)

__all__ = [
    'create_adda',
    'advance_to_next_stage',
    'create_product',
    'update_product',
    'archive_product',
    'add_product_size',
    'update_product_size',
    'archive_product_size',
    'reactivate_product_size',
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
    'start_cutting',
    'upsert_breakup_row',
    'delete_breakup_row',
    'create_bundle',
    'create_bundle_with_pieces',
    'add_bundle_item',
    'add_item_to_bundle',
    'delete_bundle_item',
    'delete_bundle',
    'save_cutting_draft',
    'complete_cutting',
    'reopen_cutting',
    'get_cutting_snapshot',
    'get_suggested_breakup',
    'preview_barcode_batches',
    # Cutting-pattern stage
    'start_pattern_stage',
    'attach_pattern_photo',
    'ensure_pattern_record',
    'save_pattern_record',
    'verify_pattern',
    'unverify_pattern',
    'set_size_allocation',
    'complete_pattern_stage',
    'reopen_pattern_stage',
    'get_or_create_pattern_stage_record',
    'get_pattern_snapshot',
    # Barcode Generation stage (PR-C 2026-05-29)
    'start_barcode_generation',
    'generate_barcodes',
    'complete_barcode_generation',
    'reopen_barcode_generation',
    'get_or_create_barcode_stage_record',
    'preview_barcode_counts',
    'get_barcode_snapshot',
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
    'set_stage_cost',
]
