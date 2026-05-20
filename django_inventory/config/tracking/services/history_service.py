"""History writers — per-domain audit log entries.

YEH FILE KYU HAI?
─────────────────
ClothRollHistory / AddaHistory / ProductHistory rows yahi 3 functions banaate hain.
NA signals, NA model save() overrides, NA views direct create. Sirf services
in helpers ko call karti hain.

CLAUDE.md rule #5 ka equivalent: `StockService.log` jaise single-writer ledger pattern.
"""
from tracking.models import AddaHistory, ClothRollHistory, ProductHistory


def log_roll(roll, change_type, actor, *, field_name='', old_value='', new_value='', note=''):
    """ClothRoll pe koi bhi state change record karta hai.

    change_type = ClothRollHistory.ChangeType enum value
    field_name/old/new = audit-style triple — kya field, kya purani value, kya nayi.
    """
    return ClothRollHistory.objects.create(
        roll=roll, change_type=change_type, actor=actor,
        # str() cast — agar Decimal/int aaye to safe stringification
        field_name=field_name, old_value=str(old_value or ''), new_value=str(new_value or ''),
        note=note,
    )


def log_adda(adda, change_type, actor, *, stage_from=None, stage_to=None, roll=None, note=''):
    """Adda pe event log — stage transition, roll assignment, completion.

    stage_from/stage_to = WorkflowStage FKs (NULL valid hain — e.g. CREATED event mein dono None).
    roll = optional ClothRoll FK — sirf ROLL_ASSIGNED events ke liye populated.
    """
    return AddaHistory.objects.create(
        adda=adda, change_type=change_type, actor=actor,
        stage_from=stage_from, stage_to=stage_to, roll=roll, note=note,
    )


def log_product(product, change_type, actor, *, field_name='', old_value='', new_value=''):
    """Product pe field-level edits ka log — CREATED/UPDATED/ARCHIVED."""
    return ProductHistory.objects.create(
        product=product, change_type=change_type, actor=actor,
        field_name=field_name, old_value=str(old_value or ''), new_value=str(new_value or ''),
    )
