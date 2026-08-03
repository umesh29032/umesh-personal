"""Production core models — Product, Stage library, per-product WorkflowStage + role rates.

Subdomain of the `production` models package. See production/models/__init__.py
for the package map. These are the top of the production dependency chain (Adda +
stage records reference these).
"""
from django.db import models

# Shared bases — single source in core app (TimeStampedModel + ActiveManager).
from core.models import ActiveManager, TimeStampedModel
from production.constants import (
    ALLOC_DIM_COLOR_SIZE, ALLOC_DIM_NONE, ALLOC_DIM_QUANTITY,
)


class AllocationDimensions(models.TextChoices):
    """Piece-pool grain a WorkflowStage participates at (Foundation S4 / D1).

    Governs PIECE-POOL behaviour ONLY — orthogonal to settlement
    (WorkflowStage.credits_workers) and costing (WorkflowStage.cost_method). A NONE
    stage still settles + pays; it just has no StagePoolSnapshot / allocation bound.
    Owner-locked 2026-06-14: the piece-pool starts at CUTTING; pre-piece stages
    (layering, cutting_pattern, barcode_generation) are NONE.
    """

    NONE = ALLOC_DIM_NONE, 'Not a piece-pool stage'
    QUANTITY = ALLOC_DIM_QUANTITY, 'Quantity (scalar)'
    COLOR_SIZE = ALLOC_DIM_COLOR_SIZE, 'Colour + Size'


class CostMethod(models.TextChoices):
    """How a stage's processing cost is computed. Used by Stage (library
    default), WorkflowStage (binding rate), and AddaStageRecord (frozen
    snapshot). per_piece/per_bundle/per_layer multiply a rate by a quantity
    pulled from the typed stage record; fixed_cost ignores quantity."""

    PER_PIECE = 'per_piece', 'Per Piece'
    PER_BUNDLE = 'per_bundle', 'Per Bundle'
    PER_LAYER = 'per_layer', 'Per Layer'
    FIXED = 'fixed_cost', 'Fixed Cost'


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
    # patterns = ek product ko kitne cut pieces banane hain (e.g. T-Shirt =
    # 1 Front + 1 Back + 2 Sleeve). M2M through `ProductPatternAssignment`
    # taaki `pieces_count` bhi store ho sake. Empty M2M = product ke liye
    # koi pattern data nahi (cutting_pattern stage usko bina checklist ke
    # bhi run karne dega — Section 01 "No patterns assigned" message).
    # String refs — through-model lives in the cutting submodule (resolved lazily).
    patterns = models.ManyToManyField(
        'ProductPattern',
        through='ProductPatternAssignment',
        related_name='products',
        blank=True,
    )

    class Meta:
        ordering = ['name']

    def clean(self):
        """PDD §31.1-F1 (R1): `code` is IMMUTABLE once the product has any Adda.

        Adda codes ('3-PATTI-001') and permanent barcode payloads (ADR-0010)
        embed this prefix; a rename would let a future product reuse the old
        code and collide on Adda.code UNIQUE. The edit form already disables
        the field and update_product never writes code — this model-level guard
        (Django full_clean, so admin/ModelForm paths hit it too) is the
        defense-in-depth backstop (PDD P10).
        """
        super().clean()
        if self.pk:
            old_code = (
                Product.objects.filter(pk=self.pk)
                .values_list('code', flat=True).first()
            )
            if old_code is not None and old_code != self.code and self.addas.exists():
                from django.core.exceptions import ValidationError
                raise ValidationError({
                    'code': f"Product code is locked once Addas exist ('{old_code}' "
                            "is embedded in Adda codes and barcode payloads forever).",
                })

    def __str__(self):
        return self.name


class StageCategory(TimeStampedModel):
    """R10 (frozen architecture 2026-07-05): grouping METADATA for stages —
    Pre Production / Stitching / Finishing / Dispatch. Display, reporting and
    filters ONLY: the workflow engine, money paths and access control NEVER
    read categories (rule 2 of the frozen architecture; guard-tested)."""

    code = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=64)
    display_order = models.PositiveSmallIntegerField(default=0)
    # Owner-editable master (data-driven rule): deactivate hides a category
    # from NEW-stage pickers; existing stages keep their FK (PROTECT) and
    # keep grouping under the old name — history never lies.
    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = 'stage categories'

    def __str__(self):
        return self.name


class MachineType(TimeStampedModel):
    """R10: the KIND of machine a stage runs on (Overlock/Flatlock/Sewing…).

    Lives in PRODUCTION (stage-domain metadata beside Stage) so the layering
    stays acyclic: the machines app (physical assets) points DOWN at this and
    at Adda; production keeps no model-level machines imports (3 sanctioned
    function-level reads, see .importlinter). Reusable across ANY number of
    operations (plain FK from Stage — frozen rule 5). NEVER carries ₹ (future
    MachineRate = separate table + ADR, per the frozen architecture §0.2)."""

    code = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    active = ActiveManager()

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
    # ── R10 frozen production model (2026-07-05) ──────────────────────────
    # A Stage = ONE business OPERATION (Overlock, Collar Attach…), never a
    # process ("Stitching" = a StageCategory) and never a machine number.
    class WorkType(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        MACHINE = 'machine', 'Machine'

    work_type = models.CharField(
        max_length=16, choices=WorkType.choices, default=WorkType.MANUAL,
        help_text="HOW the operation is performed. Machine ⇒ pick a Machine Type.",
    )
    machine_type = models.ForeignKey(
        'production.MachineType', null=True, blank=True,
        on_delete=models.PROTECT, related_name='stages',
        help_text="Mandatory when Work Type = Machine; forbidden when Manual.",
    )
    category = models.ForeignKey(
        'production.StageCategory', null=True, blank=True,
        on_delete=models.PROTECT, related_name='stages',
        help_text="Grouping for dashboards/reports ONLY — never workflow logic.",
    )
    access_by_skill = models.ManyToManyField(
        'accounts.Skill', blank=True, related_name='accessible_stages',
        help_text="Users with ANY of these skills can access this stage.",
    )
    access_by_role = models.ManyToManyField(
        'accounts.Role', blank=True, related_name='accessible_stages',
        help_text="Users whose role (or extra_roles) matches any of these.",
    )
    # ── Costing library defaults (nullable seed, NEVER binding) ──────────────
    # Copied into a new WorkflowStage at flow-attach time so admins get a sane
    # starting rate. The BINDING rate lives on WorkflowStage (per-product). A
    # global Stage rate can't price T-SHIRT cutting differently from NIKKAR.
    default_cost_method = models.CharField(
        max_length=16, choices=CostMethod.choices, blank=True,
    )
    default_cost_rate = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
    )

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        ordering = ['name']
        # Library seed rate is never negative (NULL = no default, passes CHECK).
        constraints = [
            models.CheckConstraint(
                check=models.Q(default_cost_rate__gte=0),
                name='prod_stage_defaultrate_nonneg',
            ),
            # R10 frozen rule 4 — THE single enforcement point for Work Type:
            # Machine ⇒ machine_type mandatory; Manual ⇒ machine_type forbidden.
            models.CheckConstraint(
                check=(
                    models.Q(work_type='machine', machine_type__isnull=False)
                    | (~models.Q(work_type='machine') & models.Q(machine_type__isnull=True))
                ),
                name='prod_stage_worktype_machinetype_pair',
            ),
        ]

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
    # ── Costing: BINDING per-product-per-stage rate (price-at-time-of-order) ──
    # cost_rate is editable over time; past Addas are unaffected because the
    # rate is FROZEN onto AddaStageRecord at completion. cost_rate is required
    # in the flow-editor UI (form-level) but nullable in the DB for legacy rows
    # + the succeed-and-flag freeze net (unpriced -> processing_cost stays NULL).
    cost_method = models.CharField(
        max_length=16, choices=CostMethod.choices, default=CostMethod.PER_PIECE,
        # ADR-0009: cost_rate DOUBLE DUTY karta hai — stage ka standard
        # manufacturing rate AUR worker pay ka default (role-rate override ke
        # saath). cost_billed_at set = grouped MEMBER: cost payer pe billed,
        # member kabhi earning rate nahi deta (C-1 guard — double-pay block).
    )
    cost_rate = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
    )
    # Cost grouping: connected stages roll their labour cost up to ONE paying
    # stage. NULL = self-paid. Set = this stage's cost is billed at the target
    # (it freezes processing_cost=0.00; the payer's rate x quantity covers the
    # group). SET_NULL so deleting a payer degrades members to self-paid.
    cost_billed_at = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='billed_stages',
    )
    # PAY-2 (M2.7): does completing this stage credit workers? Data-driven
    # payability — NO hardcoded stage names. When True, the central guard in
    # advance_to_next_stage blocks completion unless >=1 worker is allocated.
    # This is the SOURCE config (binding layer, beside cost_rate); a future
    # Adda-stage snapshot will freeze/copy it (like cost_rate_snapshot), never
    # relocating this field.
    credits_workers = models.BooleanField(default=False)
    # PIECE-POOL grain (S4 / D1). Governs ONLY whether this stage participates in
    # StagePoolSnapshot + the allocation bound, and at what grain. ORTHOGONAL to
    # settlement (credits_workers) and costing (cost_method) — a NONE stage still
    # settles + pays per its cost_method. Default NONE = pool is opt-in (pool starts
    # at cutting). Seeded from the stage handler's pool_grain; flow-editable.
    allocation_dimensions = models.CharField(
        max_length=16, choices=AllocationDimensions.choices,
        default=AllocationDimensions.NONE,
    )

    class Meta:
        # Same product mein 2 stages same order ya same stage na ho
        unique_together = [('product', 'order'), ('product', 'stage')]
        ordering = ['product', 'order']
        # Binding rate is never negative (NULL = unpriced legacy/freeze, passes).
        constraints = [
            models.CheckConstraint(
                check=models.Q(cost_rate__gte=0),
                name='prod_workflowstage_costrate_nonneg',
            ),
        ]

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


class WorkflowStageRoleRate(TimeStampedModel):
    """Per-role override of a WorkflowStage's cost rate (Q7 role-based rates).

    A senior cutting_master and a helper can earn different rates on the SAME
    stage. Allocation resolves `role_rate_for(ws, worker.role)` and falls back
    to `WorkflowStage.cost_rate` when no role override exists — so existing
    flows are untouched. The rate is snapshotted onto StageWorkAssignment at
    allocation, so editing this later never rewrites historical pay.
    """

    # CASCADE = role-rate is meaningless without its stage.
    workflow_stage = models.ForeignKey(
        WorkflowStage, on_delete=models.CASCADE, related_name='role_rates',
    )
    # PROTECT = don't lose a configured rate when a role is touched.
    role = models.ForeignKey(
        'accounts.Role', on_delete=models.PROTECT, related_name='+',
    )
    cost_rate = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        unique_together = [('workflow_stage', 'role')]
        ordering = ['workflow_stage', 'role__name']
        constraints = [
            models.CheckConstraint(
                check=models.Q(cost_rate__gte=0),
                name='prod_wsrolerate_costrate_nonneg',
            ),
        ]

    def __str__(self):
        return f"{self.workflow_stage} · {self.role} = {self.cost_rate}"


class AddaStageRoleRate(TimeStampedModel):
    """Frozen RESOLVED payable rate for one (AddaStageRecord, role) — Foundation S2.

    DISTINCT from WorkflowStageRoleRate: that is the per-role TEMPLATE override
    (an INPUT); THIS is the resolved OUTPUT (cost_service.resolved_payable_rate —
    grouped-member→0 / role override / stage base / 0), snapshotted when the
    AddaStageRecord is created (stage-start, addendum D-α), owner-editable until
    that stage's FIRST task completion, then IMMUTABLE (locked_at set in the
    completing transaction — addendum contract 1). complete_worker_task and
    settlement read THIS, never the live workflow, so editing a WorkflowStage rate
    later never moves an in-flight Adda's pay (addendum M-5).

    Race contract: edit_until_lock() and complete_worker_task() both
    select_for_update THIS row in the documented lock order (task →
    AddaStageRoleRate) — whoever wins the row lock decides; a locked row refuses
    edits. Deterministic.
    """
    # CASCADE = a frozen rate is meaningless without its stage record (mirrors
    # WorkflowStageRoleRate). A completed/locked stage record is PROTECTed by its
    # contributions, so CASCADE only ever reaches un-locked snapshots.
    stage_record = models.ForeignKey(
        'production.AddaStageRecord', on_delete=models.CASCADE, related_name='role_rates',
    )
    role = models.ForeignKey(
        'accounts.Role', on_delete=models.PROTECT, related_name='+',
    )
    rate = models.DecimalField(max_digits=10, decimal_places=4)
    # Set in the transaction of this (stage_record, role)'s FIRST task completion.
    # Non-null ⇒ immutable (edit_until_lock refuses).
    locked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('stage_record', 'role')]
        ordering = ['stage_record', 'role__name']
        constraints = [
            models.CheckConstraint(
                check=models.Q(rate__gte=0),
                name='prod_addastagerolerate_rate_nonneg',
            ),
        ]

    def __str__(self):
        return f'AddaStageRoleRate sr={self.stage_record_id} role={self.role_id} rate={self.rate}'


class RateCorrectionAudit(TimeStampedModel):
    """Append-only financial audit of a super-admin re-rate (S1.1, owner 2026-06-14).

    A rate correction is a FINANCIAL event — it must survive log rotation and be
    queryable (e.g. all re-rates in the soak window, Σ delta). So it gets its own
    typed, immutable row rather than a free-text AddaHistory note. Written ONLY by
    stage_rate_service.rerate_stage_role, in the same transaction as the recalc, so
    audit and money move together. `reason` is mandatory (service enforces non-empty).
    """
    # PROTECT everywhere — a financial audit must never be cascaded away.
    stage_record = models.ForeignKey(
        'production.AddaStageRecord', on_delete=models.PROTECT, related_name='rate_corrections',
    )
    role = models.ForeignKey('accounts.Role', on_delete=models.PROTECT, related_name='+')
    old_rate = models.DecimalField(max_digits=10, decimal_places=4)
    new_rate = models.DecimalField(max_digits=10, decimal_places=4)
    # How many completed-but-unsettled contributions were re-priced by this action.
    recalc_count = models.PositiveIntegerField(default=0)
    reason = models.TextField()
    actor = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='+')

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(old_rate__gte=0) & models.Q(new_rate__gte=0),
                name='prod_ratecorrection_rates_nonneg',
            ),
        ]

    def __str__(self):
        return (f'RateCorrection sr={self.stage_record_id} role={self.role_id} '
                f'{self.old_rate}->{self.new_rate} by={self.actor_id}')


class StagePoolSnapshot(TimeStampedModel):
    """Frozen per-(colour,size) good a DOWNSTREAM pool-producing stage makes available
    to allocate (Foundation S4 / D2-D3, Option B).

    Owner-locked 2026-06-14: CUTTING does NOT get a row — its pool good is
    `AddaProductSizeColorPieceBreakdown` (the single source of truth, C1/B), never
    duplicated here. This table exists ONLY for downstream pool-producing stages that
    lack an equivalent frozen artifact (e.g. a future stitching stage that self-reports).
    The pool SOURCE is handler-dispatched (`handler.pool_good`); this model is the base
    handler's source.

    Immutable: `good` is materialized write-once at the producing stage's complete
    (`handler.materialize_pool` → `pool_service`); reopen clears + refreezes. Only `good`
    is stored — `available` (= good + recovered − Σ non-voided allocations) is DERIVED at
    draw-down under the D2 advisory lock. `created_at` (TimeStampedModel) = materialized-at.
    """
    # CASCADE: a pool snapshot is meaningless without its stage record.
    stage_record = models.ForeignKey(
        'production.AddaStageRecord', on_delete=models.CASCADE, related_name='pool_snapshots',
    )
    # Grain dims (NULL for a QUANTITY-grain stage). PROTECT mirrors WorkerStageContribution.
    color = models.ForeignKey(
        'raw_materials.ClothColor', on_delete=models.PROTECT, null=True, blank=True, related_name='+',
    )
    size = models.ForeignKey(
        'production.ProductSize', on_delete=models.PROTECT, null=True, blank=True, related_name='+',
    )
    good = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = [('stage_record', 'color', 'size')]
        ordering = ['stage_record', 'color', 'size']
        constraints = [
            models.CheckConstraint(
                check=models.Q(good__gte=0),
                name='prod_stagepoolsnapshot_good_nonneg',
            ),
        ]

    def __str__(self):
        return f'pool sr={self.stage_record_id} c={self.color_id} s={self.size_id} good={self.good}'


class WorkerStageAllocation(TimeStampedModel):
    """A worker's allocated slice of a CONSUMING stage's available upstream pool
    (Foundation S4 / Phase 3, addendum C2 — Option B).

    PRODUCTION-TRUTH ONLY — capacity/quantity control. It carries NO money: no rate, no
    earning, no ledger, no settlement FK. Money lives solely at settlement
    (`StageWorkAssignment`, born at finalize, = good × frozen rate); this model never
    influences earning/rate/settlement/costing math (see allocation_service decoupling
    note + the `WorkerStageAllocation`-has-no-money test). Distinct from the settlement
    earning line `StageWorkAssignment`.

    Born when management allocates work (pre-work); draws down the upstream pool
    (`allocation_service.allocate`, under the D2 advisory lock). Append-only: corrected by
    `voided_at` (never deleted — owner data-history rule); voiding returns the qty to the
    pool's derived `available`. `stage_record` = the CONSUMING stage; the pool SOURCE is
    resolved upstream by the service. `color`/`size` NULL for a QUANTITY-grain stage.
    """
    # PROTECT: an allocation is production history — never orphaned/lost.
    stage_record = models.ForeignKey(
        'production.AddaStageRecord', on_delete=models.PROTECT, related_name='worker_allocations',
    )
    worker = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='+')
    color = models.ForeignKey(
        'raw_materials.ClothColor', on_delete=models.PROTECT, null=True, blank=True, related_name='+',
    )
    size = models.ForeignKey(
        'production.ProductSize', on_delete=models.PROTECT, null=True, blank=True, related_name='+',
    )
    allocated_quantity = models.DecimalField(max_digits=12, decimal_places=2)

    # AE-1 (owner-approved bundle model 2026-07-20): the manager's INTENT at
    # allocation time. WHOLE = "assign the whole remaining bundle" (one click, no
    # qty typed); PARTIAL = "assign N pieces" (explicit exception). Stored (not
    # derived) for audit/analytics/debugging — the numbers stay authoritative from
    # `allocated_quantity`. Default PARTIAL so pre-AE-1 rows read truthfully (they
    # were typed quantity slices). TextChoices = DB string + human label.
    class Mode(models.TextChoices):
        WHOLE = 'whole', 'Whole bundle'
        PARTIAL = 'partial', 'Partial'
    allocation_mode = models.CharField(
        max_length=8, choices=Mode.choices, default=Mode.PARTIAL)

    created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='+')
    # Set = voided (correction); never deleted. Voided rows leave the `available` sum.
    voided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['stage_record', 'worker', 'pk']
        indexes = [models.Index(fields=['stage_record', 'worker'])]
        constraints = [
            models.CheckConstraint(
                check=models.Q(allocated_quantity__gt=0),
                name='prod_workerstageallocation_qty_positive',
            ),
        ]

    def __str__(self):
        v = ' voided' if self.voided_at else ''
        return f'alloc sr={self.stage_record_id} w={self.worker_id} qty={self.allocated_quantity}{v}'
