"""Presentation helpers (R10-B, frozen UI philosophy).

StageCategory = the SINGLE source of truth for presentation grouping. This is
the ONE grouping implementation every surface uses — no page may hardcode
category names, and NOTHING below the template layer may read categories
(the category-fence test pins the engine; this module is views-layer only).
"""
from __future__ import annotations


def group_stages_by_category(items, *, stage_of=lambda x: x):
    """Group an ORDERED iterable by its stages' category, preserving workflow
    order (the engine's order is never re-sorted — categories only wrap it).

    `items` = WorkflowStage-like objects (or dicts) in flow order;
    `stage_of(item)` returns the production.Stage row (for .category).
    Returns [{'category': StageCategory|None, 'label': str, 'items': [...]}]
    — consecutive same-category runs become one group, so an exotic flow that
    interleaves categories still renders truthfully in execution order.
    """
    groups: list[dict] = []
    for item in items:
        stage = stage_of(item)
        cat = getattr(stage, 'category', None)
        label = cat.name if cat is not None else 'Other'
        if groups and groups[-1]['label'] == label:
            groups[-1]['items'].append(item)
        else:
            groups.append({'category': cat, 'label': label, 'items': [item]})
    return groups


def grouped_or_flat(items, *, stage_of=lambda x: x):
    """The owner's degenerate-case rule: grouping headers appear ONLY when the
    flow spans >1 category — a single-category flow renders exactly as today
    (no header noise). Returns (groups, use_groups)."""
    groups = group_stages_by_category(items, stage_of=stage_of)
    return groups, len(groups) > 1
