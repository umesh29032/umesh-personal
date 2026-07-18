"""Shared form primitives — widgets, label helpers, querysets.

YEH FILE KYU HAI?
─────────────────
Multiple stage form files (layering.py, cutting.py, future packing.py, ...) ko
common bits chahiye: worker checkbox widget, roll labeller, _BASE input attrs.
Yahan rakhna = stage files small + focused.

Pattern (per-stage forms file):
    from production.forms._shared import _BASE, _WorkerMultipleChoiceField, _RollChoiceField, _worker_label, _roll_label

Stage files SHOULD NOT define their own copy of these.
"""
from __future__ import annotations

from django import forms


# Common widget attrs — every input across every stage gets same baseline class
_BASE = {'class': 'sf-input', 'autocomplete': 'off'}


def _stage_worker_queryset(stage_code: str):
    """THE picker population for a stage — delegates to the single source
    `access_service.eligible_stage_workers` (F-4 polish 2026-07-05): active
    users holding the stage's access skills, i.e. exactly who the access gate
    admits. Lazy queryset — safe at form class-definition time.
    """
    # Lazy import: forms load early; production.services pulls model modules.
    from production.services import eligible_stage_workers
    return eligible_stage_workers(stage_code)


def _worker_queryset():
    """Cutting picker (legacy name kept for callers) — now stage-gated via the
    shared source instead of the old every-production-role list."""
    from production.constants import STAGE_CUTTING
    return _stage_worker_queryset(STAGE_CUTTING)


def _layering_worker_queryset():
    """Layering picker — same shared source (was a local skill filter)."""
    from production.constants import STAGE_LAYERING
    return _stage_worker_queryset(STAGE_LAYERING)


class _WorkerCheckboxes(forms.CheckboxSelectMultiple):
    """Chip-style multi-select. Template at production/_workers_widget.html."""
    template_name = 'production/_workers_widget.html'


def _worker_label(user) -> str:
    """User checkbox label = 'Full Name (email)' if name set, else just email."""
    full = (user.get_full_name() or '').strip()
    return f"{full} ({user.email})" if full else user.email


class _WorkerMultipleChoiceField(forms.ModelMultipleChoiceField):
    """ModelMultipleChoiceField with the name+email label."""
    def label_from_instance(self, obj):
        return _worker_label(obj)


def _roll_label(roll) -> str:
    """Roll select option label — delegates to ClothRoll.display_summary."""
    return roll.display_summary


class _RollChoiceField(forms.ModelChoiceField):
    """ModelChoiceField with the verbose roll label."""
    def label_from_instance(self, obj):
        return _roll_label(obj)
