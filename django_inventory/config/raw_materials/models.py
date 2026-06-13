"""Raw Materials app ke models.

YEH FILE KYU HAI?
─────────────────
Cloth inventory ka data structure yahan define hota hai:
  • Master data : ClothType, ClothColor, StorageLocation
  • Unit        : ClothRoll (ek physical roll)

Discipline rules:
  • Saari master data soft-delete via `is_active` flag — actual DELETE rare hai.
  • Master data FKs PROTECT on_delete — accidental cascade DELETE se data loss bachta hai.
  • Multi-row writes services/ mein hote hain — views/ se DIRECT save nahi (CLAUDE.md rule #4).
"""
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

# Shared bases — single source in core (TimeStampedModel + ActiveManager were
# duplicated in this file; now imported).
from core.models import ActiveManager, TimeStampedModel


class ClothType(TimeStampedModel):
    """Cloth ke types ki master list — Cotton, Polyester, Silk, Linen, vagaira.

    Roll-entry form mein dropdown se yahi options aate hain (is_active=True wale).
    """

    name = models.CharField(max_length=80, unique=True)
    # is_active=False (archived) → dropdown se hide; existing rolls ki FK valid rehti hai
    is_active = models.BooleanField(default=True)

    # Default manager + opt-in `.active` (returns is_active=True only).
    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        ordering = ['name']   # alphabetical — dropdown user-friendly

    def __str__(self):
        return self.name


class ClothColor(TimeStampedModel):
    """Cloth colors master. hex_code optional — UI mein swatch dikhane ke liye."""

    name = models.CharField(max_length=80, unique=True)
    # hex_code blank=True — har color ka hex code zaruri nahi (e.g. mixed patterns).
    # RegexValidator = form-level error; the Meta CheckConstraint is the DB guard.
    # Blank '' skips validators (it's an empty value), so "no hex" stays allowed.
    hex_code = models.CharField(
        max_length=7, blank=True,
        validators=[RegexValidator(
            regex=r'^#[0-9A-Fa-f]{6}$',
            message='Enter a hex colour like #AABBCC.',
        )],
    )
    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        ordering = ['name']
        # Stored hex is either blank or a valid #RRGGBB — no "banana" values.
        constraints = [
            models.CheckConstraint(
                check=models.Q(hex_code='') | models.Q(hex_code__regex=r'^#[0-9A-Fa-f]{6}$'),
                name='rawmat_clothcolor_hex_format',
            ),
        ]

    def __str__(self):
        return self.name


class StorageLocation(TimeStampedModel):
    """Factory ya warehouse jahan rolls physically rakhe hain.

    `code` short uppercase slug — dashboards aur future barcodes mein use ho sakta hai
    (e.g. PACKING, ROHINI).
    """

    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# Width choices = 36..44 inch (1-inch steps). ClothRoll mein dropdown ke liye use hota hai.
WIDTH_CHOICES = [(i, f'{i} inch') for i in range(36, 45)]


class ClothRoll(TimeStampedModel):
    """Ek physical cloth roll.

    Roll ID kahan se aata?
      Postgres `cloth_roll_seq` sequence → roll_service._next_roll_id() → 'CR-000142'
      Sirf service set karta hai (editable=False) — admin/model/client kabhi nahi.

    Weight + width kab aate?
      Intake time pe NHI — Adda assignment time pe (roll_service.assign_roll_to_adda).
      Isliye dono fields null=True hain.
    """

    class Status(models.TextChoices):
        # TextChoices = Django ka enum pattern. DB mein 'not_used'/'used' string store hota hai.
        NOT_USED = 'not_used', 'Not Used'
        USED = 'used', 'Used'

    # editable=False → admin form mein bhi nahi dikhega (sequence-generated)
    roll_id = models.CharField(max_length=20, unique=True, editable=False)
    purchased_date = models.DateField()
    # PROTECT FK = ClothType delete karne ki koshish karoge to Django blocked karega
    cloth_type = models.ForeignKey(
        ClothType, on_delete=models.PROTECT, related_name='rolls',
    )
    cloth_color = models.ForeignKey(
        ClothColor, on_delete=models.PROTECT, related_name='rolls',
    )
    width_inch = models.IntegerField(choices=WIDTH_CHOICES, null=True, blank=True)
    # DecimalField financial-grade precision (Decimal, not Float — rounding errors avoid)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    # Role-gated fields — form pop kar deta hai non-finance users ke liye (defence in depth)
    supplier = models.CharField(max_length=200, blank=True)
    # ADR-0009 §5: PURCHASE price — ek FACT (corrections only), market/replacement
    # rate kabhi nahi. NULL allowed (honest-NULL: 'pata nahi' ≠ ₹0) — unpriced
    # consumed rolls costing dashboard pe LOUD banner ke saath dikhte hain.
    cost_per_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    storage_location = models.ForeignKey(
        StorageLocation, on_delete=models.PROTECT, related_name='rolls',
    )
    # TextChoices field — DB mein 'not_used'/'used' string; default = not_used (intake time)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.NOT_USED,
    )
    # 'production.Adda' = string FK (lazy reference) — production app circular import avoid
    adda = models.ForeignKey(
        'production.Adda', on_delete=models.PROTECT,
        null=True, blank=True, related_name='rolls',
    )
    used_at = models.DateTimeField(null=True, blank=True)
    # related_name='+' = reverse accessor mat banao (User pe `clothroll_set` clutter avoid)
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    # Phase 6: populated at Layering completion time. NULL when roll never used.
    # layers_on_roll = how many layers were laid from THIS roll in its Adda.
    # layer_length_meters = overall layer length used in the Adda this roll was attached to.
    # Both copied from LayeringRollEntry + LayeringRecord into the roll itself so
    # future Addas can query "what's the average pieces yield for a cotton 42 inch roll
    # at 1.5m layer length" without joining through stage history.
    layers_on_roll = models.PositiveIntegerField(null=True, blank=True)
    layer_length_meters = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
    )
    # Denormalized leftover — kept in sync with primary RemainingClothOfClothRoll
    # row (most recent non-consumed). Service layer maintains. Dashboards/tables
    # read directly off the roll without joining RemainingClothOfClothRoll.
    remaining_length_meters = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
    )
    remaining_weight_kg = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
    )

    class Meta:
        # Indexes = common queries ko fast banate hain (dashboard filter, status check)
        # (adda, status) = "kis Adda pe kaunse status ke rolls hain" — common per-Adda query
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['cloth_type', 'cloth_color']),
            models.Index(fields=['storage_location', 'status']),
            models.Index(fields=['adda', 'status']),
        ]
        ordering = ['-created_at']   # latest pehle dikhe
        # Money + physical measures are never negative (NULL = not-yet-measured,
        # passes CHECK; these are set at Adda-assignment time, not intake).
        constraints = [
            models.CheckConstraint(
                check=models.Q(cost_per_kg__gte=0),
                name='rawmat_clothroll_costperkg_nonneg',
            ),
            models.CheckConstraint(
                check=models.Q(weight_kg__gte=0),
                name='rawmat_clothroll_weight_nonneg',
            ),
            models.CheckConstraint(
                check=models.Q(remaining_length_meters__gte=0),
                name='rawmat_clothroll_remlen_nonneg',
            ),
            models.CheckConstraint(
                check=models.Q(remaining_weight_kg__gte=0),
                name='rawmat_clothroll_remwt_nonneg',
            ),
        ]

    def __str__(self):
        return self.roll_id

    @property
    def display_summary(self) -> str:
        """Human-friendly identifier for logs, chips, and activity feeds.

        Format: 'CR-000142 · Cotton · Red - 42 inch'. Dot separates id/type/color;
        dash separates width to visually distinguish physical dimension from
        identity. Width omitted entirely if NULL.
        """
        base = [self.roll_id]
        if self.cloth_type_id:
            base.append(self.cloth_type.name)
        if self.cloth_color_id:
            base.append(self.cloth_color.name)
        summary = ' · '.join(base)
        if self.width_inch:
            summary += f" - {self.width_inch} inch"
        return summary
