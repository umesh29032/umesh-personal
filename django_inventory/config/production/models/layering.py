"""Layering-stage models — typed record + per-roll entries + leftover cloth tracker.

Subdomain of the production models package. All hang off adda.AddaStageRecord.
"""
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel

from .adda import Adda, AddaStageRecord


class LayeringRecord(TimeStampedModel):
    """Layering stage ka typed record. Rolls ka M2M snapshot rakhta hai —
    future mein roll edit ho bhi gaya to history intact."""

    # OneToOneField = ek hi LayeringRecord per AddaStageRecord; child cascade delete
    stage_record = models.OneToOneField(
        AddaStageRecord, on_delete=models.CASCADE, related_name='layering',
    )
    lay_count = models.PositiveIntegerField()         # SUM of per-roll layers_on_roll
    total_colors = models.PositiveIntegerField()       # distinct cloth_color count (snapshot)
    duration_minutes = models.PositiveIntegerField()
    # Phase 6: overall layer length (meters). Same for all rolls in this stage.
    # null=True backward compat — purane records mein nahi tha.
    layer_length_meters = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
    )
    # M2M snapshot — completion time pe assigned rolls freeze
    rolls_used = models.ManyToManyField(
        'raw_materials.ClothRoll', related_name='layering_records',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    @property
    def total_fabric_used_meters(self):
        """Derived: lay_count × layer_length_meters.
        Useful for Cutting stage (predict pieces) + revenue calc.
        Returns None if either input missing.
        """
        if self.lay_count is None or self.layer_length_meters is None:
            return None
        from decimal import Decimal
        return Decimal(self.lay_count) * self.layer_length_meters

    @property
    def stage_started_at(self):
        """Wall-clock stage start (not LayeringRecord row creation time).
        Reads from parent stage_record.started_at (set when Adda created).
        """
        return self.stage_record.started_at if self.stage_record_id else None


class LayeringRollEntry(TimeStampedModel):
    """Per-roll verification log inside an active Layering stage.

    YEH MODEL KYU HAI?
    ──────────────────
    Layering workspace mein assigned worker har cloth roll ko attach karte waqt:
      • width verify karta hai (ya correct karta hai),
      • weight measure karta hai (ya correct karta hai),
      • Optional notes likhta hai.

    LayeringRecord (completion summary) ke rolls_used M2M se yeh alag kyun?
      • lifecycle different — entry attach pe banti hai, completion pe nahi
      • per-roll metadata (width_verified, weight_verified, attached_by) ka ghar
      • detach kar sakte ho — completion ke pehle galat roll add kar diya to entry delete

    Stage complete hone pe service ye saari entries ke roll IDs LayeringRecord.rolls_used
    M2M mein freeze karti hai (history snapshot).
    """

    # CASCADE = stage_record delete hote hi saare entries delete
    stage_record = models.ForeignKey(
        AddaStageRecord, on_delete=models.CASCADE, related_name='layering_roll_entries',
    )
    # PROTECT = entry rehne tak ClothRoll delete blocked
    roll = models.ForeignKey(
        'raw_materials.ClothRoll', on_delete=models.PROTECT,
        related_name='layering_entries',
    )
    # Verified values — null=True kyunki worker manually verify karta hai, default empty
    width_verified_inch = models.IntegerField(null=True, blank=True)
    weight_verified_kg = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
    )
    # Per-roll layer count (Phase 6 refined):
    # Number of layers laid FROM this specific roll. Captured at completion time
    # via the Section 04 breakup table (NOT at attach time). Different rolls in
    # same Adda can have different counts. Sum across entries = LayeringRecord.lay_count.
    # layer_length_meters lives on LayeringRecord (overall, one per stage) — NOT here.
    layers_on_roll = models.PositiveIntegerField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    attached_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+',
    )
    attached_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Same roll same stage mein dobara attach na ho (race condition guard)
        unique_together = [('stage_record', 'roll')]
        ordering = ['attached_at']

    def __str__(self):
        return f"{self.stage_record.adda.code} ← {self.roll.roll_id}"


class RemainingClothOfClothRoll(TimeStampedModel):
    """Leftover cloth tracker — Phase 6.

    YEH MODEL KYU HAI?
    ──────────────────
    Layering ke baad cloth roll mein kuch length bach jaata. Pure roll ka use nahi hota:
      total_length_used = (width × layer_length × layers_on_roll) per roll
      remaining_length  = roll.length − total_used  (manual measure)
    Yeh leftover piece WASTE NAHI — future Adda mein use ho sakta. Tracking ke
    liye yeh model rakhna padta.

    Spec D-Phase6:
      • Adda key + Roll key dono store
      • Worker enters weight + length explicitly (system NAHI computes — measure varies)
      • Optional FK to LayeringRollEntry — agar precise source entry pata ho
      • is_consumed = future Adda ne yeh leftover use kar liya (deferred feature)

    Future use:
      • Cloth roll detail pe leftover summary dikhana
      • Per (width, weight, layer_length) → average pieces prediction
      • Revenue / yield tracking
    """

    # PROTECT = roll delete blocked agar leftover entries hain
    roll = models.ForeignKey(
        'raw_materials.ClothRoll', on_delete=models.PROTECT,
        related_name='remaining_pieces',
    )
    # PROTECT = source Adda delete blocked while leftover refs it
    source_adda = models.ForeignKey(
        Adda, on_delete=models.PROTECT, related_name='remaining_cloth_entries',
    )
    # Optional precise link to the layering entry that produced this leftover.
    # SET_NULL kyunki LayeringRollEntry delete (rare) ho bhi gayi to leftover row safe.
    layering_entry = models.ForeignKey(
        LayeringRollEntry, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='remaining_pieces',
    )
    # Manually measured by worker — both required
    remaining_weight_kg = models.DecimalField(max_digits=8, decimal_places=2)
    remaining_length_meters = models.DecimalField(max_digits=8, decimal_places=2)
    # is_consumed flag → future Adda mein use ho gaya (deferred consumption flow)
    is_consumed = models.BooleanField(default=False)
    consumed_in_adda = models.ForeignKey(
        Adda, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    consumed_at = models.DateTimeField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+',
    )

    class Meta:
        # Per-roll filter + is_consumed: dashboard "available leftover" query fast
        # (is_consumed, -remaining_length_meters) = leftover dashboard sort by
        # remaining first, longest pieces top.
        indexes = [
            models.Index(fields=['roll', 'is_consumed']),
            models.Index(fields=['source_adda']),
            models.Index(fields=['is_consumed', '-remaining_length_meters']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.roll.roll_id} leftover · {self.remaining_length_meters}m / {self.remaining_weight_kg}kg"
