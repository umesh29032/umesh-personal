"""ClothRoll service — bulk intake aur Adda assignment.

YEH FILE KYU HAI?
─────────────────
Cloth roll banaane aur Adda mein assign karne ka SAARA logic yahan hai.
Views direct DB mein nahi likhte — service call karte hain (CLAUDE.md rule #4).

Roll ID kahan se aata hai?
──────────────────────────
Postgres `cloth_roll_seq` sequence se. Migration 0004 mein banaya tha.
Sirf `_next_roll_id()` use karta hai — admin/model/client kabhi roll_id set nahi karte.
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Iterable

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.utils import timezone

from accounts.services import user_can_edit_financials
from django.db.models import Count, Q
from raw_materials.models import ClothRoll, ClothType, StorageLocation


# ── BOD-C step-2 read functions (owner gates G-1/G-2, 2026-07-18) ────────────
# EXTRACTED VERBATIM from ClothDashboardView (the one calculation, now with two
# consumers: that certified view + the BOD tile — INERT to every other caller;
# same filter semantics incl. the half-open to_dt the view already applies).

def stock_status_counts(*, from_dt=None, to_dt=None, color_id=None) -> dict:
    """G-1: roll stock by status (total/available/damaged/used). COUNT of
    rolls, exactly as the cloth dashboard has always shown it — Django COUNT
    aggregates, no weights (no kg truth exists, census R-4)."""
    rolls = ClothRoll.objects.all()
    if from_dt:
        rolls = rolls.filter(created_at__gte=from_dt)
    if to_dt:
        rolls = rolls.filter(created_at__lt=to_dt)
    if color_id:
        rolls = rolls.filter(cloth_color_id=color_id)
    return {
        'total': rolls.count(),
        'available': rolls.filter(status=ClothRoll.Status.NOT_USED).count(),
        # V1.1 item-1: damaged stock is visible, never hidden in 'used'.
        'damaged': rolls.filter(status=ClothRoll.Status.DAMAGED).count(),
        'used': rolls.filter(status=ClothRoll.Status.USED).count(),
    }


def stock_by_location(*, from_dt=None, to_dt=None, color_id=None):
    """G-2: per-StorageLocation roll counts (the 'which warehouse needs
    attention' truth) — the cloth dashboard's own Q-composition, verbatim."""
    return (
        StorageLocation.active
        .annotate(
            roll_count=Count('rolls', filter=(
                (Q(rolls__created_at__gte=from_dt) if from_dt else Q())
                & (Q(rolls__created_at__lt=to_dt) if to_dt else Q())
                & (Q(rolls__cloth_color_id=color_id) if color_id else Q())
            )),
            available=Count('rolls', filter=(
                Q(rolls__status=ClothRoll.Status.NOT_USED)
                & (Q(rolls__created_at__gte=from_dt) if from_dt else Q())
                & (Q(rolls__created_at__lt=to_dt) if to_dt else Q())
                & (Q(rolls__cloth_color_id=color_id) if color_id else Q())
            )),
        )
        .order_by('name')
    )


def material_purchases_in_period(year: int, month: int) -> dict:
    """RMX-C (Phase 17, charter = PDD register entry 8): PURCHASES-in-period —
    cloth bought this month, valued at PURCHASE price (weight_kg × cost_per_kg,
    both intake facts — ADR-0009 Decision 5; never re-priced). Honest-NULL:
    unpriced rolls are COUNTED, never valued (never ₹0). Damaged rolls are
    INCLUDED in the total and separately counted (owner ruling 2026-07-18:
    honest in purchases — they were bought). READ-ONLY: one aggregate query;
    `purchased_date` is a DateField ⇒ exact month boundaries, no tz semantics."""
    from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum

    if not (1 <= month <= 12 and 2000 <= year <= 2100):
        raise ValidationError("Invalid period (expected a real year/month).")
    zero = Decimal('0.00')
    value = ExpressionWrapper(
        F('weight_kg') * F('cost_per_kg'),
        output_field=DecimalField(max_digits=14, decimal_places=4))
    agg = ClothRoll.objects.filter(
        purchased_date__year=year, purchased_date__month=month,
    ).aggregate(
        total=Sum(value, filter=Q(cost_per_kg__isnull=False)),
        priced_rolls=Count('id', filter=Q(cost_per_kg__isnull=False)),
        unpriced_rolls=Count('id', filter=Q(cost_per_kg__isnull=True)),
        total_weight_kg=Sum('weight_kg'),
        damaged_rolls=Count('id', filter=Q(status=ClothRoll.Status.DAMAGED)),
    )
    return {
        'period_key': f"{year:04d}-{month:02d}",
        'total': agg['total'] or zero,
        'priced_rolls': agg['priced_rolls'],
        'unpriced_rolls': agg['unpriced_rolls'],
        'total_weight_kg': agg['total_weight_kg'] or zero,
        'damaged_rolls': agg['damaged_rolls'],
    }
# tracking.services ka import yahan TOP-level pe NAHI hai — circular import bachne ke liye
# functions ke andar lazy-import karte hain.

# Module logger — structured debug trail for multi-row / cross-app roll ops
logger = logging.getLogger(__name__)


# ── Roll ID allocation ──────────────────────────────────────────────────────

def _next_roll_id() -> str:
    """Postgres sequence se next value uthata hai. Postgres-only — jaan-bujh ke.

    Output: 'CR-000142' jaisi 6-digit zero-padded string.
    SQLite mein nextval nahi hota → RuntimeError throw karega.
    """
    # connection.vendor = 'postgresql' check — agar SQLite mein chala rahe ho to fail
    if connection.vendor != 'postgresql':
        raise RuntimeError("ClothRoll IDs require PostgreSQL (cloth_roll_seq sequence)")
    # Raw SQL — Postgres `nextval()` se sequence atomically badhta hai (race-safe)
    with connection.cursor() as cur:
        cur.execute("SELECT nextval('cloth_roll_seq')")
        n = cur.fetchone()[0]
    return f"CR-{n:06d}"


# ── Bulk creation ────────────────────────────────────────────────────────────

@transaction.atomic
def bulk_create_rolls(
    user,
    *,
    cloth_type: ClothType,
    storage_location: StorageLocation,
    purchased_date: date,
    breakup: Iterable[dict],
    supplier: str = '',
    cost_per_kg: Decimal | None = None,
) -> list[ClothRoll]:
    """N rolls ek hi transaction mein banata hai (color, qty) breakup se.

    breakup: [{'color': ClothColor, 'qty': int}, ...]

    Role gating:
        supplier + cost_per_kg sirf ACCOUNTANT/SUPER_ADMIN bhej sakte hain.
        Form layer pe bhi gate hai (defence in depth) — service yahan re-check karta hai
        taa-ke admin / shell / API se bhi koi bypass na kar paaye.

    Side effects:
        • ClothRoll — bulk INSERT of N rows (one per qty in breakup)
        • cloth_roll_seq (Postgres sequence) — advanced once per roll via _next_roll_id()
        • ClothRollHistory — one CREATED row per roll (via tracking.services.log_roll)
    """
    # Financial fields ka first gate — non-financial role ne supplier/cost daal diya to reject
    if (supplier or cost_per_kg is not None) and not user_can_edit_financials(user):
        raise PermissionDenied("Supplier and Cost Per KG require Accountant or Super Admin role")

    rows: list[ClothRoll] = []
    # Har (color, qty) row ke liye qty rolls banao
    for entry in breakup:
        color = entry['color']
        qty = int(entry['qty'])
        if qty < 1:
            raise ValidationError("Each breakup row must have qty >= 1")
        if not color.is_active:
            # Archived color allowed nahi — form level pe bhi filter hota hai
            raise ValidationError(f"Cloth color '{color}' is archived")
        for _ in range(qty):
            rows.append(ClothRoll(
                roll_id=_next_roll_id(),    # har roll ka apna unique ID (sequence se)
                purchased_date=purchased_date,
                cloth_type=cloth_type,
                cloth_color=color,
                storage_location=storage_location,
                supplier=supplier or '',
                cost_per_kg=cost_per_kg,
            ))
    if not rows:
        raise ValidationError("Breakup is empty — add at least one color row")
    if not cloth_type.is_active:
        raise ValidationError(f"Cloth type '{cloth_type}' is archived")
    if not storage_location.is_active:
        raise ValidationError(f"Storage location '{storage_location}' is archived")

    # bulk_create() = single INSERT statement (200 rolls bhi ek hi DB call mein)
    ClothRoll.objects.bulk_create(rows)
    # bulk_create SQLite mein pk set nahi karta; Postgres set karta hai
    # Phir bhi history log ke liye fresh fetch — predictable behavior across DBs
    created = list(ClothRoll.objects.filter(roll_id__in=[r.roll_id for r in rows]))
    # Lazy import — tracking app raw_materials pe depend karta hai (not vice-versa)
    from tracking.services import log_roll
    from tracking.models import ClothRollHistory
    for r in created:
        log_roll(r, ClothRollHistory.ChangeType.CREATED, user, note='Bulk intake')
    logger.info(
        "roll.bulk_create count=%s cloth_type=%s location=%s has_cost=%s user=%s",
        len(created), cloth_type.pk, storage_location.pk,
        cost_per_kg is not None, getattr(user, 'pk', None),
    )
    return created


# ── Assignment to Adda ──────────────────────────────────────────────────────

# ── Stock-level edit ────────────────────────────────────────────────────────

@transaction.atomic
def update_roll_details(
    user,
    *,
    roll: ClothRoll,
    width_inch: int | None = None,
    weight_kg: Decimal | None = None,
    storage_location: StorageLocation | None = None,
    purchased_date: date | None = None,
    supplier: str | None = None,
    cost_per_kg: Decimal | None = None,
) -> ClothRoll:
    """Stock-level field update for a single ClothRoll.

    Guards:
      • roll.status MUST be NOT_USED — once roll attached to a layering, its
        verified width/weight live on LayeringRollEntry, not on the roll itself.
        Updating the source roll would diverge from history. Detach first if
        you really need to fix the stock value.
      • Financial fields (supplier, cost_per_kg) only writable by FINANCIAL_ROLES.

    Each changed field writes a ClothRollHistory row (audit trail). Update is
    field-level — pass None to leave unchanged. Empty string clears supplier;
    None means "no change".

    Side effects:
        • ClothRoll — single-row UPDATE of only the changed columns (save update_fields=dirty)
        • ClothRollHistory — one audit row per changed field (via tracking.services.log_roll)
    """
    # Refresh from DB FIRST. Why?
    # ModelForm caller (RollUpdateView) is an UpdateView. Django's _post_clean()
    # mutates form.instance (= the passed `roll`) with cleaned form data BEFORE
    # this service runs. Without this refresh, every `roll.width_inch` access
    # below returns the NEW value — diff vs the same NEW value is always False —
    # nothing saves, nothing logs.
    roll.refresh_from_db()

    if roll.status != ClothRoll.Status.NOT_USED:
        raise ValidationError(
            f"Roll {roll.roll_id} is already in use. Detach from its Adda before editing."
        )
    # Financial gate — same rule as bulk intake
    if (supplier is not None or cost_per_kg is not None) and not user_can_edit_financials(user):
        raise PermissionDenied("Supplier and Cost Per KG require Accountant or Super Admin role")

    # Track changes for history log + decide which DB columns to UPDATE
    from tracking.services import log_roll
    from tracking.models import ClothRollHistory

    dirty: list[str] = []
    if width_inch is not None and width_inch != roll.width_inch:
        log_roll(
            roll, ClothRollHistory.ChangeType.WEIGHT_UPDATED, user,
            field_name='width_inch',
            old_value=str(roll.width_inch or ''),
            new_value=str(width_inch),
        )
        roll.width_inch = int(width_inch)
        dirty.append('width_inch')

    if weight_kg is not None and Decimal(weight_kg) != (roll.weight_kg or Decimal('0')):
        log_roll(
            roll, ClothRollHistory.ChangeType.WEIGHT_UPDATED, user,
            field_name='weight_kg',
            old_value=str(roll.weight_kg or ''),
            new_value=str(weight_kg),
        )
        roll.weight_kg = Decimal(weight_kg)
        dirty.append('weight_kg')

    if storage_location is not None and storage_location.pk != roll.storage_location_id:
        if not storage_location.is_active:
            raise ValidationError(f"Storage location '{storage_location}' is archived")
        log_roll(
            roll, ClothRollHistory.ChangeType.LOCATION_MOVED, user,
            field_name='storage_location',
            old_value=roll.storage_location.code if roll.storage_location_id else '',
            new_value=storage_location.code,
        )
        roll.storage_location = storage_location
        dirty.append('storage_location')

    if purchased_date is not None and purchased_date != roll.purchased_date:
        log_roll(
            roll, ClothRollHistory.ChangeType.WEIGHT_UPDATED, user,
            field_name='purchased_date',
            old_value=str(roll.purchased_date),
            new_value=str(purchased_date),
        )
        roll.purchased_date = purchased_date
        dirty.append('purchased_date')

    if supplier is not None and supplier != roll.supplier:
        log_roll(
            roll, ClothRollHistory.ChangeType.WEIGHT_UPDATED, user,
            field_name='supplier',
            old_value=roll.supplier,
            new_value=supplier,
        )
        roll.supplier = supplier
        dirty.append('supplier')

    if cost_per_kg is not None and Decimal(cost_per_kg) != (roll.cost_per_kg or Decimal('0')):
        log_roll(
            roll, ClothRollHistory.ChangeType.WEIGHT_UPDATED, user,
            field_name='cost_per_kg',
            old_value=str(roll.cost_per_kg or ''),
            new_value=str(cost_per_kg),
        )
        roll.cost_per_kg = Decimal(cost_per_kg)
        dirty.append('cost_per_kg')

    if dirty:
        roll.save(update_fields=dirty)
    logger.info(
        "roll.update_details roll=%s changed=%s fields=%s user=%s",
        roll.roll_id, len(dirty), ','.join(dirty) or '-', getattr(user, 'pk', None),
    )
    return roll


# ── Assignment to Adda ──────────────────────────────────────────────────────

@transaction.atomic
def assign_roll_to_adda(user, *, roll: ClothRoll, adda, weight_kg: Decimal, width_inch: int):
    """Roll ko Adda mein attach karta hai. Weight + width yahin pe capture hote hain.

    Guards:
        • roll.status NOT_USED hona chahiye (already-used roll re-assign nahi)
        • adda IN_PROGRESS + Layering stage pe hona chahiye
    Saare guards ValidationError throw karte hain — form upar pe message dikhaata hai.

    Side effects:
        • ClothRoll — single-row UPDATE (adda, weight_kg, width_inch, status, used_at, used_by)
        • ClothRollHistory — one STATUS_CHANGED row (via tracking.services.log_roll)
        • AddaHistory — one ROLL_ASSIGNED row (via tracking.services.log_adda)
    """
    # Lazy import — production app ke models import yahan, taa-ke top-level circular na ho
    from production.constants import STAGE_LAYERING
    from production.models import Adda as AddaModel

    if roll.status != ClothRoll.Status.NOT_USED:
        raise ValidationError(f"Roll {roll.roll_id} is already used")
    if adda.status != AddaModel.Status.IN_PROGRESS:
        raise ValidationError(f"Adda {adda.code} is not in-progress")
    # Rolls sirf Layering pe assign hote hain. Streams redesign: the truth
    # is the LANES' state, not the coarse pointer — any live lane with an
    # OPEN (started, incomplete) layering record may still receive rolls.
    from production.models import AddaStageRecord
    open_layering = AddaStageRecord.objects.filter(
        adda=adda, workflow_stage__stage__code=STAGE_LAYERING,
        completed_at__isnull=True).exists()
    if not open_layering:
        raise ValidationError("Rolls can only be assigned during the Layering stage")

    # Saare fields ek hi save() mein update — update_fields se sirf ye columns hit hote hain
    roll.adda = adda
    roll.weight_kg = weight_kg
    roll.width_inch = width_inch
    roll.status = ClothRoll.Status.USED
    roll.used_at = timezone.now()   # timezone.now() = settings.TIME_ZONE aware
    roll.used_by = user
    roll.save(update_fields=[
        'adda', 'weight_kg', 'width_inch', 'status', 'used_at', 'used_by',
    ])
    # History log — dono taraf entry (ClothRollHistory + AddaHistory)
    from tracking.services import log_roll, log_adda
    from tracking.models import AddaHistory, ClothRollHistory
    log_roll(
        roll, ClothRollHistory.ChangeType.STATUS_CHANGED, user,
        field_name='status', old_value='not_used', new_value='used',
        note=f"assigned to {adda.code}",
    )
    log_adda(adda, AddaHistory.ChangeType.ROLL_ASSIGNED, user, roll=roll)
    logger.info(
        "roll.assign_to_adda roll=%s adda=%s weight_kg=%s width_inch=%s user=%s",
        roll.roll_id, adda.code, weight_kg, width_inch, getattr(user, 'pk', None),
    )
    return roll


@transaction.atomic
def consume_leftover(user, *, leftover, adda, notes=''):
    """C-1 (ADR-0009): the SOLE writer of leftover consumption — records that a
    RemainingClothOfClothRoll piece was physically reused in another Adda.

    Rules (locked):
      • whole-piece only — partial use means weigh the new remainder as a CHILD
        leftover row first, then consume this one;
      • valued (for future G1 material costing) at the SOURCE roll's
        cost_per_kg — never re-priced;
      • append-only history: consumption is stamped, never deleted; a mistake
        is corrected by a future un-consume event (not built; same lifecycle
        family as settlement reversal).

    No UI calls this yet — the write semantics exist BEFORE the data pattern
    ossifies (off-book reuse is unrecoverable history).

    Side effects: UPDATE production.RemainingClothOfClothRoll
    (is_consumed/consumed_in_adda/consumed_at) under select_for_update.
    """
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    from production.models import RemainingClothOfClothRoll

    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can record leftover consumption.")
    # Row lock so two concurrent consumes can't both pass the guard.
    # Hinglish: leftover EK hi baar consume ho sakta hai — lock + re-check ka
    # wahi pattern jo void_allocation me hai.
    leftover = (RemainingClothOfClothRoll.objects.select_for_update()
                .get(pk=leftover.pk))
    if leftover.is_consumed:
        raise ValidationError(
            f"Leftover #{leftover.pk} was already consumed in "
            f"{leftover.consumed_in_adda.code if leftover.consumed_in_adda_id else 'another Adda'}.")
    if adda.pk == leftover.source_adda_id:
        raise ValidationError(
            "A leftover cannot be consumed by the Adda that produced it.")
    leftover.is_consumed = True
    leftover.consumed_in_adda = adda
    leftover.consumed_at = timezone.now()
    if notes:
        leftover.notes = (leftover.notes + ' | ' + notes).strip(' |')[:255]
    leftover.save(update_fields=['is_consumed', 'consumed_in_adda',
                                 'consumed_at', 'notes', 'updated_at'])
    # V1.1 item-2: the consuming Adda's timeline carries the provenance —
    # existing ROLL_ASSIGNED vocabulary, the note says it was a leftover.
    from tracking.models import AddaHistory
    from tracking.services import log_adda
    log_adda(adda, AddaHistory.ChangeType.ROLL_ASSIGNED, user,
             roll=leftover.roll,
             note=(f"leftover #{leftover.pk} · "
                   f"{leftover.remaining_weight_kg or '?'} kg from "
                   f"{leftover.source_adda.code}")[:200])
    logger.info(
        "roll.consume_leftover leftover=%s roll=%s from=%s into=%s by=%s",
        leftover.pk, leftover.roll_id, leftover.source_adda_id, adda.code,
        user.pk,
    )
    return leftover


@transaction.atomic
def mark_roll_damaged(user, *, roll: ClothRoll, reason: str) -> ClothRoll:
    """V1.1 item-1: retire a WHOLE unusable roll from available stock —
    management-only, mandatory reason, audited (ClothRollHistory
    STATUS_CHANGED with the reason). Refused on a USED roll (its cloth is
    already production history — damage found later lives on the pieces/
    reports, not the roll). Soft state, never delete."""
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can mark a roll damaged.")
    if not (reason or '').strip():
        raise ValidationError("A reason is required to mark a roll damaged.")
    r = ClothRoll.objects.select_for_update().get(pk=roll.pk)
    if r.status == ClothRoll.Status.USED:
        raise ValidationError(
            "This roll is already consumed by production — record damage on "
            "the affected pieces/reports, not the roll.")
    if r.status == ClothRoll.Status.DAMAGED:
        raise ValidationError("This roll is already marked damaged.")
    old = r.status
    r.status = ClothRoll.Status.DAMAGED
    r.save(update_fields=['status', 'updated_at'])
    from tracking.models import ClothRollHistory
    from tracking.services import log_roll
    log_roll(r, ClothRollHistory.ChangeType.STATUS_CHANGED, user,
             field_name='status', old_value=old, new_value='damaged',
             note=f"damaged: {reason.strip()}"[:200])
    logger.info("roll.mark_damaged roll=%s by=%s reason=%s",
                r.roll_id, getattr(user, 'pk', None), reason.strip())
    return r


@transaction.atomic
def restore_damaged_roll(user, *, roll: ClothRoll, reason: str) -> ClothRoll:
    """V1.1 item-1: the mistake escape — a wrongly-damaged roll returns to
    available stock. Management-only, mandatory reason, audited. Only a
    DAMAGED roll can be restored."""
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can restore a damaged roll.")
    if not (reason or '').strip():
        raise ValidationError("A reason is required to restore a roll.")
    r = ClothRoll.objects.select_for_update().get(pk=roll.pk)
    if r.status != ClothRoll.Status.DAMAGED:
        raise ValidationError("Only a damaged roll can be restored.")
    r.status = ClothRoll.Status.NOT_USED
    r.save(update_fields=['status', 'updated_at'])
    from tracking.models import ClothRollHistory
    from tracking.services import log_roll
    log_roll(r, ClothRollHistory.ChangeType.STATUS_CHANGED, user,
             field_name='status', old_value='damaged', new_value='not_used',
             note=f"restored: {reason.strip()}"[:200])
    logger.info("roll.restore_damaged roll=%s by=%s",
                r.roll_id, getattr(user, 'pk', None))
    return r
