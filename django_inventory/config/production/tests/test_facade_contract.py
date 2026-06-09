"""Facade contract test — M0.3 safety net for the M2 stage-engine refactor.

M2 moves each stage's service/views/models into production/stages/<stage>/ and
replaces the if/elif dispatch with a registry. Callers (views, the expense app,
~37 test imports) all depend on `from production.services import <name>`. This
test FREEZES the set of public entry points, so the refactor cannot silently
drop or rename one — the module a function LIVES in may move, but its facade name
may not. A break here fails loudly at test time instead of at runtime in a caller.

Change EXPECTED only as a deliberate, reviewed public-API change.
"""
from django.test import SimpleTestCase

import production.services as facade

# The frozen public contract (stage lifecycle + costing + flow entry points).
EXPECTED = frozenset({
    # Adda lifecycle
    'create_adda', 'advance_to_next_stage',
    # Product
    'create_product', 'update_product', 'archive_product',
    'add_product_size', 'update_product_size', 'archive_product_size', 'reactivate_product_size',
    # Layering
    'start_layering', 'complete_layering', 'reopen_layering', 'get_layering_snapshot',
    'attach_roll_to_layering', 'detach_roll_from_layering', 'update_layering_roll_entry',
    'save_layering_breakup', 'save_layering_draft', 'record_remaining_cloth',
    'remove_remaining_cloth', 'sync_layering_workers_for_skill',
    # Cutting
    'start_cutting', 'complete_cutting', 'complete_cutting_from_bundles',
    'complete_cutting_legacy', 'reopen_cutting', 'get_cutting_snapshot',
    'upsert_breakup_row', 'delete_breakup_row', 'create_bundle', 'create_bundle_with_pieces',
    'add_bundle_item', 'add_item_to_bundle', 'add_pieces_to_bundle',
    'delete_bundle_item', 'delete_bundle',
    'save_cutting_draft', 'get_suggested_breakup', 'preview_barcode_batches',
    # Cutting-pattern
    'start_pattern_stage', 'complete_pattern_stage', 'reopen_pattern_stage',
    'get_pattern_snapshot', 'get_or_create_pattern_stage_record', 'ensure_pattern_record',
    'save_pattern_record', 'verify_pattern', 'unverify_pattern', 'set_size_allocation',
    'attach_pattern_photo',
    # Barcode generation
    'start_barcode_generation', 'generate_barcodes', 'complete_barcode_generation',
    'reopen_barcode_generation', 'get_barcode_snapshot', 'preview_barcode_counts',
    'get_or_create_barcode_stage_record',
    # Costing / access / activity / flow
    'clear_stage_cost', 'user_can_access_stage', 'stage_access_map',
    'adda_activity', 'user_activity_across_addas',
    'add_stage_to_product_flow', 'remove_stage_from_product_flow',
    'move_stage_in_product_flow', 'set_stage_cost',
})


class FacadeContractTest(SimpleTestCase):
    def test_all_expected_entry_points_importable_and_callable(self):
        missing = sorted(n for n in EXPECTED if not callable(getattr(facade, n, None)))
        self.assertEqual(missing, [], f"production.services dropped/renamed: {missing}")

    def test_all_advertises_the_contract(self):
        # __all__ must advertise every contracted name (tooling + `import *`).
        all_set = set(getattr(facade, '__all__', []))
        self.assertEqual(
            sorted(EXPECTED - all_set), [],
            "names in the frozen contract but missing from production.services.__all__",
        )
