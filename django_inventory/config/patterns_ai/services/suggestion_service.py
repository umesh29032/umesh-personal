"""suggestion_service — SINGLE WRITER for SuggestionEvent (I-1; P4 §6).

The decision spine: record_offer freezes the shown recommendation
snapshot; decide() applies the ONE-SHOT human verdict. The Advisor never
decides — a human outcome is the only path off 'offered' (Era-2 law).
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.services import MANAGEMENT_ROLES, user_has_role

from patterns_ai.models import SuggestionEvent


def _gate(user):
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied('management role required')


def record_offer(*, user, product, payload, source):
    """Persist what was SHOWN (append-only fact). payload must carry
    schema_version (F3)."""
    _gate(user)
    if not isinstance(payload, dict) or 'schema_version' not in payload:
        raise ValidationError('offer payload needs schema_version (F3).')
    return SuggestionEvent.objects.create(
        product=product, source=source, payload=payload, created_by=user)


DECIDABLE = {SuggestionEvent.Outcome.ACCEPTED,
             SuggestionEvent.Outcome.MODIFIED,
             SuggestionEvent.Outcome.REJECTED}


@transaction.atomic
def decide(*, user, event, outcome, reason=''):
    """ONE-SHOT human decision on an offered suggestion."""
    _gate(user)
    event = SuggestionEvent.objects.select_for_update().get(pk=event.pk)
    if event.outcome != SuggestionEvent.Outcome.OFFERED:
        raise ValidationError(
            f'suggestion #{event.pk} was already decided '
            f'({event.get_outcome_display()}) — decisions are one-shot.')
    outcome = SuggestionEvent.Outcome(outcome)
    if outcome not in DECIDABLE:
        raise ValidationError('outcome must be a human decision '
                              '(accepted / modified / rejected).')
    reason = (reason or '').strip()
    if outcome == SuggestionEvent.Outcome.REJECTED and not reason:
        raise ValidationError('rejection needs a reason (F2).')
    event.outcome = outcome
    event.outcome_reason = reason
    event.decided_by = user
    event.decided_at = timezone.now()
    event._decision_transition = True
    event.save(update_fields=['outcome', 'outcome_reason', 'decided_by',
                              'decided_at', 'updated_at'])
    return event
