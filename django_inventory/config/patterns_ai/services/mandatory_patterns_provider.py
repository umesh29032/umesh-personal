"""GAP-1 grain (production-hardening 2026-07-11) — the Blueprint tells
production WHICH ProductPatterns (Production Components) are MANDATORY,
through the ADR-H registry (same species as fabric_group_provider: patterns_ai
registers, production calls the hook, plain ids cross the wall).

Contract: mandatory_pattern_ids_for_product(product) -> set[int]
A pattern is mandatory when ANY of its Blueprint pieces is non-optional
(mirror of the lane-blocking rule). Patterns with no Blueprint pieces are
absent from the result — pool_service treats an empty/short answer as
"grain unknown" and falls back to the legacy per-dimension read (fail-open:
never stricter than pre-GAP-1 behaviour on provider failure).
"""
from patterns_ai.models import PatternPiece


def mandatory_pattern_ids_for_product(product) -> set[int]:
    mandatory: set[int] = set()
    optional_only: set[int] = set()
    for pattern_id, is_optional in (
            PatternPiece.objects.filter(product=product)
            .values_list('pattern_id', 'is_optional')):
        if is_optional:
            optional_only.add(pattern_id)
        else:
            mandatory.add(pattern_id)
    return mandatory
