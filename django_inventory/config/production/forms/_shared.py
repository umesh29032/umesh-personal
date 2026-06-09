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

from accounts.models import User
from accounts.skills import SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER
from accounts.services import PRODUCTION_ROLES


# Common widget attrs — every input across every stage gets same baseline class
_BASE = {'class': 'sf-input', 'autocomplete': 'off'}


def _worker_queryset():
    """Generic worker queryset — every production-role user. Used by stages
    that don't have skill-specific gating (e.g. Cutting).
    """
    return User.objects.filter(role__code__in=list(PRODUCTION_ROLES)).order_by('email')


def _layering_worker_queryset():
    """Layering-specific worker pool — only cutting_master / cutting_master_helper users."""
    return (
        User.objects.filter(
            is_active=True,
            skills__name__in=[SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER],
        )
        .distinct()
        .order_by('email')
    )


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
