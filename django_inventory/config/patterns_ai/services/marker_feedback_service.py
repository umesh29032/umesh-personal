"""marker_feedback_service — single writer for MarkerUsage + MarkerOutcome,
and the ONLY home of derived yield math (V3 F6, I-1, readiness N-6).

Why this service exists: the feedback pillar is facts-in, derivations-at-read.
Usage rows are the human act "this Adda cut with marker M"; outcome rows are
raw facts a human explicitly records; every ratio (meters/garment, later ₹)
is computed by VERSIONED pure functions here — never persisted, so a formula
fix can never require a data migration.

INVARIANTS:
  * usage: marker must be usable (candidate/validated/promoted, not
    voided-status); an adda_temporary marker is usable ONLY on its own Adda
    (D11 — excluded from recommendations elsewhere).
  * usage corrections = void(reason) + new row; never edit.
  * outcome: exactly one per usage; created by an explicit human action
    (N-6); facts may be filled null→value later, but a non-null fact NEVER
    changes (correction = void the usage, re-record).
  * derived metrics carry METRICS_VERSION and are never written to any row.
"""
import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.services import MANAGEMENT_ROLES, user_has_role

from patterns_ai.models import Marker, MarkerOutcome, MarkerUsage
from .units import mm_to_m, q2

logger = logging.getLogger(__name__)

METRICS_VERSION = 1

_USABLE = {Marker.Status.CANDIDATE, Marker.Status.VALIDATED, Marker.Status.PROMOTED}
_FACT_FIELDS = ('fabric_in_mm', 'garments_cut', 'garments_packed', 'leftover_mm')


def _ensure_management(user):
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied('Only management may write marker feedback.')


@transaction.atomic
def record_usage(*, user, marker, adda, plies, repeats=1,
                 measured_usable_width_mm=None, stage_record=None, notes=''):
    """The human act: 'this Adda cuts with marker M' (append-only).

    Purpose: THE feedback join key — without it no outcome can ever be
    attributed. Invariants: marker usable; temporary markers only on their
    own Adda; plies/repeats ≥ 1 (DB CHECK backs it).
    """
    _ensure_management(user)
    marker.refresh_from_db(fields=['status', 'status_reason', 'origin', 'adda'])
    if Marker.Status(marker.status) not in _USABLE:
        raise ValidationError(
            f'Marker {marker.reference} is {marker.status} — not usable '
            f'(reason on record: {marker.status_reason!r}).')
    if (marker.origin == Marker.Origin.ADDA_TEMPORARY
            and marker.adda_id != adda.pk):
        raise ValidationError(
            'adda_temporary markers may only be used on their own Adda (D11).')
    usage = MarkerUsage.objects.create(
        marker=marker, adda=adda, stage_record=stage_record,
        plies=int(plies), repeats=int(repeats),
        measured_usable_width_mm=measured_usable_width_mm,
        confirmed_by=user, notes=notes)
    logger.info('usage.record %s adda=%s plies=%s repeats=%s by=%s',
                marker.reference, adda.pk, plies, repeats, user.pk)
    return usage


@transaction.atomic
def void_usage(*, user, usage, reason):
    """Void (never delete) a usage row — the only correction path.

    Derived reads exclude voided usages; an attached outcome stays as
    history bound to a voided usage (excluded the same way).
    """
    _ensure_management(user)
    if not (reason or '').strip():
        raise ValidationError('Voiding requires a reason (F2).')
    if usage.voided_at is not None:
        raise ValidationError('Usage is already voided.')
    usage.voided_at = timezone.now()
    usage.void_reason = reason.strip()
    usage.save(update_fields=['voided_at', 'void_reason', 'updated_at'])
    logger.info('usage.void %s by=%s reason=%r', usage.pk, user.pk, reason)
    return usage


@transaction.atomic
def record_outcome(*, user, usage, fabric_in_mm=None, garments_cut=None,
                   garments_packed=None, leftover_mm=None, quality_flags=None):
    """Explicit human 'record outcome' action (N-6) — raw facts only.

    Purpose: freeze what actually happened (fabric in, garments out,
    leftover) as honest-NULL facts. One outcome per usage (DB OneToOne).
    """
    _ensure_management(user)
    if usage.voided_at is not None:
        raise ValidationError('Cannot record an outcome on a voided usage.')
    if MarkerOutcome.objects.filter(usage=usage).exists():
        raise ValidationError(
            'An outcome already exists for this usage — facts never change; '
            'void the usage and re-record if it was wrong.')
    flags = {'schema_version': 1, 'flags': list(quality_flags or [])}
    outcome = MarkerOutcome.objects.create(
        usage=usage, fabric_in_mm=fabric_in_mm, garments_cut=garments_cut,
        garments_packed=garments_packed, leftover_mm=leftover_mm,
        quality_flags=flags, recorded_by=user)
    logger.info('outcome.record usage=%s by=%s', usage.pk, user.pk)
    return outcome


@transaction.atomic
def update_outcome_facts(*, user, outcome, **facts):
    """Fill honest-NULL facts later (e.g. leftover measured next morning).

    Invariant: null→value ONLY. A non-null fact never changes — the
    correction path is void_usage + record anew (append-only knowledge).
    """
    _ensure_management(user)
    changed = []
    for field, value in facts.items():
        if field not in _FACT_FIELDS:
            raise ValidationError(f'Unknown fact field: {field}')
        if value is None:
            continue
        current = getattr(outcome, field)
        if current is not None:
            raise ValidationError(
                f'{field} is already recorded ({current}) — facts never '
                'change; void the usage and re-record instead.')
        setattr(outcome, field, value)
        changed.append(field)
    if changed:
        outcome.save(update_fields=changed + ['updated_at'])
        logger.info('outcome.fill usage=%s fields=%s by=%s',
                    outcome.usage_id, changed, user.pk)
    return outcome


# ── derived AT READ — versioned pure functions, never persisted (F6) ────────

def derive_metrics(outcome):
    """Compute display metrics from facts. Pure; returns a dict; writes
    NOTHING. Utilization needs piece areas (geometry era) — honest None here.
    """
    facts_ok = outcome.usage.voided_at is None
    fabric_mm = outcome.fabric_in_mm
    cut = outcome.garments_cut
    m = {
        'metrics_version': METRICS_VERSION,
        'valid': facts_ok,
        'fabric_in_m': mm_to_m(fabric_mm) if fabric_mm is not None else None,
        'meters_per_garment': None,
        'meters_per_100': None,
        'utilization_pct': None,   # needs geometry areas — arrives with P2 era
        'leftover_m': mm_to_m(outcome.leftover_mm)
                      if outcome.leftover_mm is not None else None,
    }
    if fabric_mm and cut:
        per = q2(mm_to_m(fabric_mm) / cut)
        m['meters_per_garment'] = per
        m['meters_per_100'] = q2(per * 100)
    return m
