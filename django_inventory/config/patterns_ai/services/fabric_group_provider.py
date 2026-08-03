"""Streams redesign (2026-07-11) — the Blueprint speaks its fabric
groups to production through the ADR-H registry (same species as
ARCHIVE_VALIDATORS / LAYOUT_PROVIDER: patterns_ai registers, production
calls wrapped, plain dicts cross the wall).

Contract: fabric_groups_for_product(product) ->
    [{'fabric_group': str, 'blocking': bool}]
blocking = the group holds at least one MANDATORY Blueprint piece
(optional-only groups derive non-blocking lanes — they never gate the
pre-production join). Deterministic order: 'body' first, then
alphabetical, so lane displays are stable.
"""
from patterns_ai.models import PatternPiece


def fabric_groups_for_product(product) -> list[dict]:
    groups: dict[str, bool] = {}
    pieces = PatternPiece.objects.filter(product=product).only(
        'fabric_group', 'is_optional')
    for piece in pieces:
        group = (piece.fabric_group or '').strip() or 'body'
        groups[group] = groups.get(group, False) or not piece.is_optional
    ordered = sorted(groups, key=lambda g: (g != 'body', g))
    return [{'fabric_group': g, 'blocking': groups[g]} for g in ordered]
