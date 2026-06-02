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

from datetime import date
from decimal import Decimal
from typing import Iterable

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.utils import timezone

from inventory.services import user_can_edit_financials
from raw_materials.models import ClothRoll, ClothType, StorageLocation
# tracking.services ka import yahan TOP-level pe NAHI hai — circular import bachne ke liye
# functions ke andar lazy-import karte hain.


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
    return roll


# ── Assignment to Adda ──────────────────────────────────────────────────────

@transaction.atomic
def assign_roll_to_adda(user, *, roll: ClothRoll, adda, weight_kg: Decimal, width_inch: int):
    """Roll ko Adda mein attach karta hai. Weight + width yahin pe capture hote hain.

    Guards:
        • roll.status NOT_USED hona chahiye (already-used roll re-assign nahi)
        • adda IN_PROGRESS + Layering stage pe hona chahiye
    Saare guards ValidationError throw karte hain — form upar pe message dikhaata hai.
    """
    # Lazy import — production app ke models import yahan, taa-ke top-level circular na ho
    from production.constants import STAGE_LAYERING
    from production.models import Adda as AddaModel

    if roll.status != ClothRoll.Status.NOT_USED:
        raise ValidationError(f"Roll {roll.roll_id} is already used")
    if adda.status != AddaModel.Status.IN_PROGRESS:
        raise ValidationError(f"Adda {adda.code} is not in-progress")
    # Rolls sirf Layering stage pe assign hote hain — Cutting/baaki stages pe nahi
    if adda.current_stage is None or adda.current_stage.stage_type != STAGE_LAYERING:
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
    return roll
