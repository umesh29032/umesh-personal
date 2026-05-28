"""Production app ke models — Product, WorkflowStage, Adda + stage records.

YEH FILE KYU HAI?
─────────────────
Production lifecycle ke data structures yahan hain:
  • Product           = factory ka product (T-SHIRT, NIKKAR)
  • WorkflowStage     = product ka ordered stage list (layering → cutting)
  • Adda              = ek production batch (T-SHIRT-001)
  • AddaStageRecord   = polymorphic parent — har stage type ka common record
  • LayeringRecord    = OneToOne stage record — layering ke specific fields
  • CuttingRecord     = OneToOne stage record — cutting ke specific fields

Atomic counter pattern:
─────────────────────
Adda.code service-side atomically banta hai (`SELECT FOR UPDATE` on Product row).
Concurrent create_adda(SAME_PRODUCT) calls race-safe hain.
"""
from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base — created_at + updated_at har row pe automatic."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Product(TimeStampedModel):
    """Factory product — 3-PATTI, T-SHIRT, NIKKAR vagaira.

    `code` short uppercase slug — Adda codes (`{CODE}-001`) aur barcodes
    (`{ADDA_CODE}-0001`) iss code se ban-te hain. Slug ki tarah treat karo.

    `adda_counter` per-product Adda numbering ka source — sirf AddaService
    isko increment karta hai, wo bhi `SELECT FOR UPDATE` ke andar (race-safe).
    """

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    # adda_counter = ab tak kitne Addas iss product ke ban chuke. Sirf service increment kare.
    adda_counter = models.PositiveIntegerField(default=0)
    # Patterns required to cut one Adda of this product. Through-model carries
    # pieces_count (e.g. 2 sleeves per T-Shirt). Empty = no cutting_pattern stage
    # data needed for this product even if its workflow includes the stage.
    patterns = models.ManyToManyField(
        'ProductPattern',
        through='ProductPatternAssignment',
        related_name='products',
        blank=True,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Stage(TimeStampedModel):
    """Global library of stages — admin-managed, reusable across Products.

    Pehle stages WorkflowStage.StageType ka hardcoded enum tha. Ab Stage model
    ek table hai — admin CRUD karta hai (add/edit/delete) aur access controls
    (skills + roles) yahan store hote hain. Product ki flow define karte
    waqt WorkflowStage ke through Product → Stage mapping aur order set
    hoti hai.

    Access rule (OR semantics):
      Super Admin / Manager  → always (built-in defense, not in DB)
      Else                   → user role overlap with access_by_role OR
                               user skill overlap with access_by_skill
    """

    code = models.SlugField(
        max_length=32, unique=True,
        help_text="Stable identifier used in URLs + services (e.g. 'layering').",
    )
    name = models.CharField(
        max_length=64,
        help_text="Display label shown in flow pipeline (e.g. 'Layering').",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    access_by_skill = models.ManyToManyField(
        'accounts.Skill', blank=True, related_name='accessible_stages',
        help_text="Users with ANY of these skills can access this stage.",
    )
    access_by_role = models.ManyToManyField(
        'inventory.Role', blank=True, related_name='accessible_stages',
        help_text="Users whose role (or extra_roles) matches any of these.",
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class WorkflowStage(TimeStampedModel):
    """Per-Product stage in its production flow — join table linking
    Product → Stage with an ordering position.

    Pehle yahan stage_type CharField tha. Ab `stage` FK Stage library
    ko point karta hai — admin Stage library mein naya stage add karta hai
    aur per-product flow page se attach karta hai.

    Back-compat: stage_type / get_stage_type_display() Python-level alias
    properties hain (Stage.code aur Stage.name return karte hain) — taaki
    purani templates aur URLs (`/stage-panel/<stage_type>/`) bina change ke
    chalti rahein.
    """

    # CASCADE = product delete hote hi stages bhi delete (rare event — usually archive hota hai)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='workflow_stages',
    )
    order = models.PositiveIntegerField()
    # PROTECT = stage record delete na ho jab tak koi product use kar raha ho
    stage = models.ForeignKey(
        Stage, on_delete=models.PROTECT, related_name='workflow_stages',
    )

    class Meta:
        # Same product mein 2 stages same order ya same stage na ho
        unique_together = [('product', 'order'), ('product', 'stage')]
        ordering = ['product', 'order']

    def __str__(self):
        return f"{self.product.code} · {self.stage.name} (order {self.order})"

    # ── Back-compat shim ────────────────────────────────────────────────
    # Old code reads `s.stage_type` (string) + `s.get_stage_type_display()`.
    # Stage FK arrived in migration 0011; both reads keep working via these
    # properties so templates/URLs don't break.

    @property
    def stage_type(self) -> str:
        return self.stage.code if self.stage_id else ''

    def get_stage_type_display(self) -> str:
        return self.stage.name if self.stage_id else ''


class Adda(TimeStampedModel):
    """Ek production batch.

    Code format: '{Product.code}-{adda_counter:03d}' — e.g. 'T-SHIRT-001'.
    Status IN_PROGRESS rehta hai jab tak last WorkflowStage complete na ho jaaye.
    """

    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'In Progress'
        ON_HOLD = 'on_hold', 'On Hold'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    # editable=False → admin form mein nahi dikhega; sirf service banata hai
    code = models.CharField(max_length=40, unique=True, editable=False)
    # PROTECT = product delete blocked agar koi Adda use kar raha ho
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='addas',
    )
    # current_stage NULL hota hai jab Adda COMPLETED (saare stages khatm)
    current_stage = models.ForeignKey(
        WorkflowStage, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.IN_PROGRESS,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )

    class Meta:
        indexes = [
            # Dashboards mein in_progress filter common → status index
            models.Index(fields=['status']),
            # Per-product filtered queries (product=X, status=in_progress)
            models.Index(fields=['product', 'status']),
            # Stage-wise grouping
            models.Index(fields=['current_stage']),
        ]
        ordering = ['-started_at']

    def __str__(self):
        return self.code


class AddaStageRecord(TimeStampedModel):
    """Stage records ka polymorphic parent.

    Har Adda + WorkflowStage combination ka EK row banta hai (unique_together).
    Typed records (LayeringRecord, CuttingRecord) OneToOne se hang karte hain.

    `workers` M2M kyun parent pe?
        Har stage type mein workers same shape mein store karne ki zarurat.
        Future `expense.StageWorkAssignment` `through=` model isi M2M ko convert karega
        (hours, rate, paid/unpaid track karne ke liye).
    """

    # CASCADE = Adda delete hote hi saare stage records delete (rare event)
    adda = models.ForeignKey(Adda, on_delete=models.CASCADE, related_name='stage_records')
    workflow_stage = models.ForeignKey(WorkflowStage, on_delete=models.PROTECT, related_name='+')
    # M2M to User — Django auto join table banata hai (production_addastagerecord_workers)
    workers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='stage_assignments', blank=True,
    )
    # started_at = jab manager ne workers assign kar ke stage kick off ki.
    # null=True kyun? Legacy rows (pre-layering-workspace) sirf complete pe banti thi —
    # unhe NULL hi rakhna safe hai. Naye rows mein service hamesha set karti hai.
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    # Draft state for the stage form. Persisted before completion so user can
    # leave and return. Cleared after complete advances the Adda. Generic enough
    # to be reused by future stages (cutting, packing, ...) — each stage's
    # service reads what it needs.
    draft_layer_length_meters = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
    )
    draft_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    draft_notes = models.TextField(blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+',
    )

    class Meta:
        unique_together = [('adda', 'workflow_stage')]
        ordering = ['adda', 'workflow_stage__order']

    @property
    def is_active(self) -> bool:
        """In-progress (started but not yet completed)."""
        return self.started_at is not None and self.completed_at is None


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
        indexes = [
            models.Index(fields=['roll', 'is_consumed']),
            models.Index(fields=['source_adda']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.roll.roll_id} leftover · {self.remaining_length_meters}m / {self.remaining_weight_kg}kg"


class CuttingRecord(TimeStampedModel):
    """Cutting stage ka typed record. `pieces_cut` save hote hi BatchBarcode rows
    auto-generate hote hain (tracking.services.generate_for_cutting)."""

    stage_record = models.OneToOneField(
        AddaStageRecord, on_delete=models.CASCADE, related_name='cutting',
    )
    # pieces_cut = barcode count trigger; cutting form submit pe set hota hai
    pieces_cut = models.PositiveIntegerField()
    notes = models.TextField(blank=True)


# ── Cutting-Pattern stage models ────────────────────────────────────────────
# A ProductPattern is a reusable design "shape" (front panel, back panel,
# sleeve, ...). Each Product has a curated list of these via the explicit
# through-model `ProductPatternAssignment` which also carries `pieces_count`
# (e.g. T-Shirt = 1 Front + 1 Back + 2 Sleeve). Cutting master uses this
# during the cutting_pattern stage to draw the layout, then records a video
# + photos of the layered cloth.

class ProductPattern(TimeStampedModel):
    """Reusable pattern definition — a single design shape used across products.

    Examples: 'Front Panel', 'Back Panel', 'Sleeve', 'Collar'. Admin maintains
    this library; Products reference patterns via ProductPatternAssignment.
    """

    code = models.SlugField(
        max_length=48, unique=True,
        help_text="Stable identifier used in URLs/services (e.g. 'sleeve').",
    )
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    # Optional reference image — admin uploads a sample drawing so the cutting
    # master has a visual on the workspace page.
    reference_image = models.ImageField(
        upload_to='product_patterns/', blank=True, null=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductPatternAssignment(TimeStampedModel):
    """Through-model: how many of `pattern` does `product` need per Adda.

    Existence of any assignment for a product == that product needs the
    cutting_pattern stage. Service layer can read these to derive total
    expected pieces before cutting begins.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='pattern_assignments',
    )
    pattern = models.ForeignKey(
        ProductPattern, on_delete=models.PROTECT, related_name='product_assignments',
    )
    # pieces_count = how many cut pieces of this pattern per layered Adda (e.g.
    # T-Shirt uses 2 sleeves → pieces_count=2 for the Sleeve pattern row).
    pieces_count = models.PositiveSmallIntegerField(default=1)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = [('product', 'pattern')]
        ordering = ['product', 'pattern__name']

    def __str__(self):
        return f"{self.product.code} · {self.pattern.name} × {self.pieces_count}"


def _cutting_pattern_video_path(instance, filename):
    """Per-Adda video storage path. Slug-safe code keeps OS-friendly filenames."""
    return f"cutting_pattern/{instance.stage_record.adda.code}/video_{filename}"


def _cutting_pattern_photo_path(instance, filename):
    return f"cutting_pattern/{instance.record.stage_record.adda.code}/photos/{filename}"


class CuttingPatternRecord(TimeStampedModel):
    """Cutting-pattern stage typed record. One per Adda's pattern-stage.

    Hosts the single mandatory video (drawn pattern on the layered cloth) +
    free-form notes. Multiple photos hang off via CuttingPatternPhoto FK so
    a master can attach as many shots as needed.
    """

    stage_record = models.OneToOneField(
        AddaStageRecord, on_delete=models.CASCADE, related_name='cutting_pattern',
    )
    # video = mp4/webm/mov; Django doesn't validate codec — we trust UI accept=.
    # blank/null so cutting master can submit photos OR video alone (at least one
    # required at complete-time — enforced in service layer, not at the DB).
    video = models.FileField(upload_to=_cutting_pattern_video_path, blank=True, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"CuttingPattern · {self.stage_record.adda.code}"


class CuttingPatternPhoto(TimeStampedModel):
    """One photo of the layered cloth with pattern drawn. Many-per-record.

    Compressed to JPEG via Pillow on save (see production/services/cutting_pattern_service.py)
    to keep disk + future-cloud-egress costs sane.
    """

    record = models.ForeignKey(
        CuttingPatternRecord, on_delete=models.CASCADE, related_name='photos',
    )
    image = models.ImageField(upload_to=_cutting_pattern_photo_path)
    caption = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Photo for {self.record.stage_record.adda.code}"


# StageAccessRule deleted in migration 0011 — superseded by Stage model.
# Access rules now live on Stage.access_by_skill + Stage.access_by_role.
