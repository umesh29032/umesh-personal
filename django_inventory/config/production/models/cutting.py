"""Cutting subdomain — cutting record, pattern library + per-product assignment,
size chart, pattern-stage record/photos/verification/size-allocation, piece
breakup, bundles + items, and the verified (size, color) breakdown snapshot.

Subdomain of the production models package. References core (Product) +
adda (Adda, AddaStageRecord). raw_materials FKs are string refs (no import cycle).
"""
from django.conf import settings
from django.db import models

from core.models import ActiveManager, TimeStampedModel

from .adda import Adda, AddaStageRecord
from .core import Product


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
# YEH MODELS KYU HAIN?
# Cutting master jab Adda pe layered cloth pe pattern draw karta hai, uska
# digital record yahan store hota hai. 4 cheezein store karte hain:
#
#   1. ProductPattern              → reusable design shape library
#                                     (e.g. Sleeve, Front, Back, Collar)
#   2. ProductPatternAssignment    → Product ko kaunse patterns chahiye +
#                                     kitne pieces (e.g. T-Shirt = 1 Front +
#                                     1 Back + 2 Sleeve)
#   3. CuttingPatternRecord        → ek Adda ke cutting-pattern stage ka
#                                     row (video + notes)
#   4. CuttingPatternPhoto         → us record se attached photos (multiple)
#
# Cutting master sirf cutting_master / cutting_master_helper skill ke saath
# yeh stage chala sakta hai (Stage.access_by_skill mein attached). Photos
# Pillow se compress hote hain — disk save karta hai.

class ProductPattern(TimeStampedModel):
    """Reusable pattern definition — ek design shape jo multiple products
    use kar sakte hain.

    Examples: 'Front Panel', 'Back Panel', 'Sleeve', 'Collar'. Admin iss
    library ko maintain karta hai. Products `ProductPatternAssignment`
    through-model ke through patterns ko refer karte hain.

    Why separate model?
    Pehle har product ke liye duplicate pattern banane padte the. Library
    pattern reuse karne deta hai — Sleeve pattern T-Shirt + Kurta dono mein
    use ho sakta hai with different `pieces_count`.
    """

    # SlugField = URL/database friendly identifier. Services constants pe
    # hardcode kar sakte hain — isliye unique + locked-on-update (form mein).
    code = models.SlugField(
        max_length=48, unique=True,
        help_text="Stable identifier used in URLs/services (e.g. 'sleeve').",
    )
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    # ImageField = Pillow validation. Admin sample drawing upload kar sakta
    # hai — cutting master ko visual reference milta hai.
    reference_image = models.ImageField(
        upload_to='product_patterns/', blank=True, null=True,
    )
    # is_active = soft archive. Direct delete refuse hota hai agar koi
    # ProductPatternAssignment use kar raha ho (PROTECT FK).
    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductPatternAssignment(TimeStampedModel):
    """Through-table: Product ↔ ProductPattern jodne wala join row jo
    `pieces_count` bhi carry karta hai.

    Example data:
        Product=T-SHIRT, Pattern=Front,  pieces_count=1
        Product=T-SHIRT, Pattern=Back,   pieces_count=1
        Product=T-SHIRT, Pattern=Sleeve, pieces_count=2
    Iska matlab T-Shirt ke ek Adda ke liye total 4 cut pieces banane hain
    (3 distinct patterns × respective counts).

    Cutting-pattern stage workspace iss table ko padh kar checklist render
    karta hai.
    """

    # CASCADE on Product = agar product delete (rare) ho to assignments bhi
    # delete (orphan rows na rahein).
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='pattern_assignments',
    )
    # PROTECT on Pattern = pattern delete blocked agar assignments hain.
    # Admin pehle assignments hatae phir pattern delete kare.
    pattern = models.ForeignKey(
        ProductPattern, on_delete=models.PROTECT, related_name='product_assignments',
    )
    # pieces_count = ek Adda ke liye iss pattern ke kitne cut pieces banane
    # hain. PositiveSmallIntegerField = 0–32767 range (>1 bytes ka overhead
    # nahi).
    pieces_count = models.PositiveSmallIntegerField(default=1)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        # Same product mein same pattern do baar attach nahi hona chahiye.
        unique_together = [('product', 'pattern')]
        ordering = ['product', 'pattern__name']

    def __str__(self):
        return f"{self.product.code} · {self.pattern.name} × {self.pieces_count}"


# ── Upload-path callables ────────────────────────────────────────────────────
# `upload_to=callable(instance, filename)` Django ko batata hai ki file disk
# pe kahan save karni hai. Hum per-Adda folder banate hain taaki manually
# debug karna easy ho (`ls media/cutting_pattern/T-SHIRT-001/...`).

def _cutting_pattern_video_path(instance, filename):
    """Per-Adda video storage path.

    instance = CuttingPatternRecord row jo save ho raha hai.
    filename = browser ne jo file name bheja.

    Returns: 'cutting_pattern/<ADDA_CODE>/video_<original_filename>'

    Storage backend (default = FileSystemStorage; can be S3/MinIO later)
    iss path ko apne root pe write karta hai.
    """
    return f"cutting_pattern/{instance.stage_record.adda.code}/video_{filename}"


def _cutting_pattern_photo_path(instance, filename):
    """Per-Adda photos folder. instance = CuttingPatternPhoto row."""
    return f"cutting_pattern/{instance.record.stage_record.adda.code}/photos/{filename}"


class CuttingPatternRecord(TimeStampedModel):
    """Cutting-pattern stage ka typed record — har Adda ka pattern stage
    is row pe hang karta hai.

    Yeh model `OneToOne` se `AddaStageRecord` se juda hai (`stage_record`).
    Matlab har stage_record ke saath ek hi CuttingPatternRecord ho sakta hai.

    Optional fields:
      • video — cutting master pattern draw karte hue ka video. mp4/webm/mov.
      • notes — text-only notes.

    Why both optional?
    User ne explicit confirm kiya: "anyone of them but one of them is
    mandatory". Toh DB level pe dono blank=True, null=True hain. Service
    layer (complete_pattern_stage) at-least-one rule enforce karta hai.
    """

    # OneToOneField = ek stage_record ke saath ek hi record. CASCADE matlab
    # AddaStageRecord delete hote hi yeh row bhi delete (rare, Adda delete
    # ke time).
    # related_name='cutting_pattern' lets us write `sr.cutting_pattern` to
    # fetch the typed record (Django reverse OneToOne).
    stage_record = models.OneToOneField(
        AddaStageRecord, on_delete=models.CASCADE, related_name='cutting_pattern',
    )
    # FileField = generic file (codec/format Django validate nahi karta).
    # UI side <input accept="video/..."> hint deti hai. blank/null = optional
    # at DB. Service complete-time check enforces video-OR-photo.
    video = models.FileField(upload_to=_cutting_pattern_video_path, blank=True, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"CuttingPattern · {self.stage_record.adda.code}"


class CuttingPatternPhoto(TimeStampedModel):
    """Layered cloth + drawn pattern ki ek photo. Ek record ke saath multiple
    photos ho sakti hain (regular FK, not OneToOne).

    Pillow compression service mein hota hai (see
    `production/services/cutting_pattern_service._compress_image`) —
    photos JPEG q=80 + max 2400px tak resize hote hain. EXIF rotation
    bhi honor hoti hai (phone photos sideways nahi aati).
    """

    # FK record = ek record ke under kitni bhi photos. related_name='photos'
    # lets template do `record.photos.all()`.
    record = models.ForeignKey(
        CuttingPatternRecord, on_delete=models.CASCADE, related_name='photos',
    )
    # ImageField = FileField + Pillow validation (width/height accessible).
    image = models.ImageField(upload_to=_cutting_pattern_photo_path)
    caption = models.CharField(max_length=200, blank=True)
    # uploaded_by = audit — kis user ne upload ki. PROTECT = user delete
    # blocked if photos. blank/null = legacy rows / service uploads.
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )

    class Meta:
        # Photos chronological order mein render karte hain (upload-time first).
        ordering = ['created_at']

    def __str__(self):
        return f"Photo for {self.record.stage_record.adda.code}"


# StageAccessRule deleted in migration 0011 — superseded by Stage model.
# Access rules now live on Stage.access_by_skill + Stage.access_by_role.


# ── Cutting Pattern validation + Cutting Stage breakup models ───────────────
# YEH MODELS KYU HAIN?
# Phase-1 (Cutting Pattern) ke liye per-assignment verification + per-size
# proportion entry chahiye. Phase-2 (Cutting Stage) ke liye per-(size, color,
# pattern) piece breakup chahiye taaki barcodes mein metadata bhar sake.
#
#   1. ProductSize                       → per-Product size chart (S/M/L ya 1/2/3/4)
#   2. CuttingPatternVerification        → per-ProductPatternAssignment verified row
#   3. CuttingPatternSizeAllocation      → per-size proportion_pct (sum=100)
#   4. CuttingPieceBreakup               → per-(size, color, pattern) piece count
#
# Design doc: docs/production/CUTTING_DESIGN.md

class ProductSize(TimeStampedModel):
    """Per-Product size chart entry.

    Each Product apna size set rakhta hai — global library nahi.
    Examples:
        T-SHIRT → S, M, L, XL
        KIDS-1  → 1, 2, 3, 4
    Same `code='M'` on two products = do alag rows (unique_together).
    """

    # CASCADE = product delete hone par sizes bhi delete (rare; only soft archives normally)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='sizes',
    )
    # SlugField = URL/service friendly identifier ('s', 'm', 'l', '1'). Lowercase
    # store karte hain; labels ('Small', 'Size 1') alag field mein.
    code = models.SlugField(max_length=16)
    label = models.CharField(max_length=40)
    # display_order = UI mein render order. PositiveSmallIntegerField = 0..32767
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        # Same product mein same code do baar nahi
        unique_together = [('product', 'code')]
        ordering = ['product', 'display_order', 'code']

    def __str__(self):
        return f"{self.product.code} · {self.label}"


class CuttingPatternVerification(TimeStampedModel):
    """Cutting master ne ek ProductPatternAssignment ko physically verify kiya
    hai uska row.

    Spec rule: complete_pattern_stage tabhi succeed karta hai jab
    `product.pattern_assignments.count() == record.verifications.count()`.

    Optional `photo` FK — wo CuttingPatternPhoto jo iss pattern ko prove karti
    hai. Photo upload alag flow se hoti hai (multi-photo upload); verification
    sirf ek existing photo ko reference karti hai.
    """

    # CASCADE on record = pattern stage record delete ho to verifications bhi
    record = models.ForeignKey(
        'CuttingPatternRecord', on_delete=models.CASCADE,
        related_name='verifications',
    )
    # PROTECT on assignment = assignment delete blocked agar verified ho chuka.
    # Admin pehle verification hatae, phir assignment edit/delete.
    assignment = models.ForeignKey(
        ProductPatternAssignment, on_delete=models.PROTECT, related_name='+',
    )
    # verified_by = audit. PROTECT = user delete blocked if verifications hain.
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+',
    )
    # verified_at separate from created_at? Nahi — auto_now_add kaam karta hai.
    # Naam alag isliye ki audit display mein "Verified at" semantic clear ho.
    verified_at = models.DateTimeField(auto_now_add=True)
    # Optional pointer to a CuttingPatternPhoto (already uploaded) that
    # demonstrates this assignment. SET_NULL = photo delete ho to verification
    # row preserve (sirf reference cleared).
    photo = models.ForeignKey(
        'CuttingPatternPhoto', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+',
    )
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        # Ek record + assignment combo sirf ek baar verify ho sakta hai.
        # Re-verify = unverify (delete) then verify again.
        unique_together = [('record', 'assignment')]
        ordering = ['assignment__pattern__name']

    def __str__(self):
        return f"Verified {self.assignment} on {self.record.stage_record.adda.code}"


class CuttingPatternSizeAllocation(TimeStampedModel):
    """Pattern designer ne is batch ke liye ek size ka proportion lock kiya.

    Example: T-Shirt Adda mein
        Size S → 20%
        Size M → 40%
        Size L → 30%
        Size XL → 10%
    Sum across one record = 100 (service complete_pattern_stage validate karta hai).

    Drafts mein sum != 100 allowed; complete pe strict.
    """

    record = models.ForeignKey(
        'CuttingPatternRecord', on_delete=models.CASCADE,
        related_name='size_allocations',
    )
    # PROTECT on size = size delete blocked agar allocation hai (admin pehle
    # remove kare). Cross-product mismatch tabhi possible jab admin galat size
    # pick kare — service layer validate karta hai (size.product == adda.product).
    size = models.ForeignKey(
        ProductSize, on_delete=models.PROTECT, related_name='+',
    )
    # 0..100 range. PositiveSmallIntegerField fine.
    proportion_pct = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = [('record', 'size')]
        ordering = ['size__display_order', 'size__code']
        # Percentage by definition caps at 100 (PositiveSmallInt floors it at 0).
        constraints = [
            models.CheckConstraint(
                check=models.Q(proportion_pct__lte=100),
                name='prod_sizealloc_pct_max100',
            ),
        ]

    def __str__(self):
        return f"{self.size.label} = {self.proportion_pct}% on {self.record.stage_record.adda.code}"


class CuttingPieceBreakup(TimeStampedModel):
    """Cutting stage ka per-(size, color, pattern) piece count row.

    Total `cutting_record.pieces_cut = SUM(breakup.count)` — denormalized at
    complete_cutting() time. Barcode generator iss table ko iterate karta hai
    aur har row se `count` BatchBarcode rows banata hai with size/color/pattern
    FKs populated.

    Roll FK optional — agar ek (size, color, pattern) row multiple rolls se
    aata hai to null rehta hai; warna source roll point karta hai.
    """

    cutting_record = models.ForeignKey(
        'CuttingRecord', on_delete=models.CASCADE, related_name='breakup',
    )
    # PROTECT on size/color/pattern = master data delete blocked agar pieces
    # exist hain. Audit-friendly.
    size = models.ForeignKey(
        ProductSize, on_delete=models.PROTECT, related_name='+',
    )
    # String FK = raw_materials import avoid (no cycle risk). ClothColor in
    # raw_materials app.
    color = models.ForeignKey(
        'raw_materials.ClothColor', on_delete=models.PROTECT, related_name='+',
    )
    pattern = models.ForeignKey(
        ProductPattern, on_delete=models.PROTECT, related_name='+',
    )
    count = models.PositiveIntegerField()
    # PR10 (2026-05-28): denormalized "how many pieces of this (pattern, color)
    # row have been consumed into bundles". Recomputed by service when bundle
    # items added/deleted. available_count = count - consumed_count.
    consumed_count = models.PositiveIntegerField(default=0)
    # Optional source roll — agar pata ho ki yeh pieces kis roll se aaye.
    roll = models.ForeignKey(
        'raw_materials.ClothRoll', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )

    class Meta:
        # Ek cutting record mein same (size, color, pattern) combo do baar nahi.
        # Same combo ko aur add karna ho to count badhao, nayi row mat banao.
        unique_together = [('cutting_record', 'size', 'color', 'pattern')]
        ordering = ['pattern__name', 'size__display_order', 'color__name']

    @property
    def available_count(self) -> int:
        return max(self.count - self.consumed_count, 0)

    def __str__(self):
        return f"{self.pattern.name}/{self.size.code}/{self.color.name} × {self.count}"


class CuttingBundle(TimeStampedModel):
    """Manufacturing bundle — size-grouped container of cut pieces.

    PR8 (2026-05-28) restructure:
      • PR7: row per (pattern, size, color, count)
      • PR8: row per (size) — header. Items inside via CuttingBundleItem.

    User definition (spec §3):
      "5 patterns together = 1 Size-1 Bundle"
    So one bundle per size, holding all pattern × color × count items
    needed for that size.

    Barcode generator aggregates items by (size, color) — pattern collapsed.
    """

    cutting_record = models.ForeignKey(
        'CuttingRecord', on_delete=models.CASCADE, related_name='bundles',
    )
    size = models.ForeignKey(
        ProductSize, on_delete=models.PROTECT, related_name='+',
    )
    # Denormalized = SUM(items.count). Updated on item save/delete via service.
    total_pieces = models.PositiveIntegerField(default=0)
    # Optional human-readable label — e.g. "Bundle-A1", "Lot 3".
    bundle_number = models.CharField(max_length=40, blank=True)

    class Meta:
        # Ek cutting_record + size combo = ek bundle. Multiple bundles per
        # size required ho to bundle_number free-text field use karo (or
        # extend later with subset logic).
        unique_together = [('cutting_record', 'size')]
        ordering = ['size__display_order', 'size__code']

    def __str__(self):
        bn = f" [{self.bundle_number}]" if self.bundle_number else ''
        return f"Bundle {self.size.code.upper()} × {self.total_pieces}{bn}"


class CuttingBundleItem(TimeStampedModel):
    """Bundle ke andar ek pattern + color line item.

    Example (Size-M Bundle):
        Front × Red × 10
        Front × Blue × 8
        Back  × Red × 10
        Sleeve × Red × 20

    Total bundle pieces = SUM of all item counts.
    """

    bundle = models.ForeignKey(
        CuttingBundle, on_delete=models.CASCADE, related_name='items',
    )
    pattern = models.ForeignKey(
        ProductPattern, on_delete=models.PROTECT, related_name='+',
    )
    color = models.ForeignKey(
        'raw_materials.ClothColor', on_delete=models.PROTECT, related_name='+',
    )
    count = models.PositiveIntegerField()
    # PR10: Source CuttingPieceBreakup row this item was consumed from. Used
    # to restore consumed_count when item is deleted. Nullable for legacy /
    # manually-added items (no source tracking).
    source_breakup = models.ForeignKey(
        CuttingPieceBreakup, on_delete=models.PROTECT,
        null=True, blank=True, related_name='consumed_into',
    )

    class Meta:
        # Same (bundle, pattern, color) do baar nahi — same combo ko aur add
        # karna ho to count update karo, naya row mat banao.
        unique_together = [('bundle', 'pattern', 'color')]
        ordering = ['pattern__name', 'color__name']

    def __str__(self):
        return f"{self.pattern.name}/{self.color.name} × {self.count}"


# ── Verified breakdown (PR-A 2026-05-29) ────────────────────────────────────
# Cutting stage complete hone par "verified production breakdown" yahan freeze
# hota hai. Per-(size, color) piece count = manufacturing truth. Barcode
# Generation aur future stages (Stitching, Packing) isse hi consume karenge —
# recompute nahi. CuttingBundleItem (pattern × color × count) source data,
# yeh aggregate (size × color × count) materialized snapshot.

class AddaProductSizeColorPieceBreakdown(TimeStampedModel):
    """Cutting stage ka final verified per-(size, color) piece count snapshot.

    PURPOSE:
    Cutting master ne actual bundles bana liye → service `CuttingBundleItem`
    rows ko (size, color) pe aggregate karke is table mein freeze karta hai
    (cutting completion ke andar atomic). Future stages bina recompute is
    table ko query karte hain.

    Why denormalised storage?
        • Barcode Generation stage stable input chahiye
        • Cutting reopen aur regenerate ke beech audit trail
        • Future Stitching/Packing stages bhi same aggregate consume karenge
        • Read-heavy dashboards bina JOIN aggregate dikha sakte

    Lifecycle:
        cutting complete  → bulk_create rows for this cutting_record
        cutting reopen    → delete all rows for this cutting_record
        barcode reopen    → preserve (barcode stage doesn't touch breakdown)

    Relationships:
        cutting_record  CASCADE  → cutting reopen ke saath rows delete
        bundle          SET_NULL → bundle delete pe row safe (legacy NULL bhi)
        size + color    PROTECT  → master data archive blocked
    """

    # PROTECT = Adda delete blocked; manufacturing truth audit-critical
    adda = models.ForeignKey(
        Adda, on_delete=models.PROTECT, related_name='size_color_breakdowns',
    )
    # Denormalised Product FK — fast filter for dashboards without JOIN
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='+',
    )
    # CASCADE = cutting reopen rows clean up automatically
    cutting_record = models.ForeignKey(
        'CuttingRecord', on_delete=models.CASCADE,
        related_name='size_color_breakdowns',
    )
    # SET_NULL = bundle delete OK (rare); legacy non-bundle products NULL
    bundle = models.ForeignKey(
        CuttingBundle, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='size_color_breakdowns',
    )
    # nullable for legacy products that did not have ProductSize attached
    size = models.ForeignKey(
        ProductSize, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    # nullable for legacy products (no per-color tracking)
    color = models.ForeignKey(
        'raw_materials.ClothColor', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    # Final verified count — barcode generation will produce this many barcodes
    verified_piece_count = models.PositiveIntegerField()
    # Audit fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+',
    )

    class Meta:
        # Ek cutting_record + size + color combo do baar nahi
        unique_together = [('cutting_record', 'size', 'color')]
        indexes = [
            # Dashboard query: "is Adda ka size-wise breakdown"
            models.Index(fields=['adda', 'size', 'color']),
            # Per-cutting aggregate
            models.Index(fields=['cutting_record']),
        ]
        ordering = ['adda', 'size__display_order', 'color__name']

    def __str__(self):
        size_label = self.size.code.upper() if self.size_id else '—'
        color_label = self.color.name if self.color_id else '—'
        return f"{self.adda.code} · {size_label} · {color_label} × {self.verified_piece_count}"
