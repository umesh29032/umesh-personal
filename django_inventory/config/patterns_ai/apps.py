"""patterns_ai — AI Pattern Intelligence platform (P1 Block 1: foundation only).

Governing chain: MANUFACTURING_V1_FREEZE → 06_BLUEPRINT_V3_FINAL → ADR pack A-H
→ IMPLEMENTATION_MASTER_PLAN. Constitution: proposals-only toward production;
FKs INTO production only; production NEVER imports this app (zero exceptions,
stricter than machines — enforced by import-linter + tests/test_purity.py).
"""
from django.apps import AppConfig


class PatternsAiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'patterns_ai'
    verbose_name = 'AI Pattern Intelligence'

    def ready(self):
        # Phase-3 D-3 (owner-approved): register the confirmed-designs
        # archive guard via production's validator registry — dependency
        # inversion keeps the ADR-H wall (patterns_ai→production allowed,
        # never the reverse).
        from production.services import product_size_service
        from patterns_ai.services.size_guards import (
            refuse_archiving_sole_design_size)
        if (refuse_archiving_sole_design_size
                not in product_size_service.ARCHIVE_VALIDATORS):
            product_size_service.ARCHIVE_VALIDATORS.append(
                refuse_archiving_sole_design_size)
        # Phase 8B: register the READ-ONLY layout panel provider (same
        # inversion — production consumes plain dicts, never our modules).
        from production.stages.cutting_pattern import handler as _cp
        from patterns_ai.services.layout_panel_provider import (
            build_layout_panel)
        if _cp.LAYOUT_PROVIDER is None:
            _cp.LAYOUT_PROVIDER = build_layout_panel
        # M6: the layering edge (ADVISORY recommendation) — same species.
        from production.stages.layering import handler as _lay
        from patterns_ai.services.layout_panel_provider import (
            build_layering_recommendation)
        if _lay.LAYOUT_PROVIDER is None:
            _lay.LAYOUT_PROVIDER = build_layering_recommendation
        # M6: cutting-completion listener — the usage↔stage-record stamp
        # (traceability; production isolates listener failures).
        from production.stages.cutting import service as _cut
        from patterns_ai.services.layout_usage_service import (
            stamp_adda_usages)
        if stamp_adda_usages not in _cut.CUTTING_COMPLETE_LISTENERS:
            _cut.CUTTING_COMPLETE_LISTENERS.append(stamp_adda_usages)
        # Streams redesign 2026-07-11: the Blueprint speaks its fabric
        # groups to Adda creation (lane derivation) — registry #5.
        from production.services import adda_service as _adda
        from patterns_ai.services.fabric_group_provider import (
            fabric_groups_for_product)
        if _adda.FABRIC_GROUPS_PROVIDER is None:
            _adda.FABRIC_GROUPS_PROVIDER = fabric_groups_for_product
        # GAP-1 grain 2026-07-11: the Blueprint speaks which Production
        # Components are MANDATORY (garment-equivalent pool) — registry #6.
        from production.services import pool_service as _pool
        from patterns_ai.services.mandatory_patterns_provider import (
            mandatory_pattern_ids_for_product)
        if _pool.MANDATORY_PATTERNS_PROVIDER is None:
            _pool.MANDATORY_PATTERNS_PROVIDER = mandatory_pattern_ids_for_product
