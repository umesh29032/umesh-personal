"""Expense / payroll app — worker money. Downstream of production + accounts.

YEH APP KYU HAI?
─────────────────
Production app sirf MANUFACTURING COST track karta hai (AddaStageRecord.
processing_cost). Worker ko KITNA milega — yeh alag concern hai aur yahan
rehta hai (CLAUDE.md: production aur payroll responsibilities separated).

Models:
  • StageWorkAssignment — per-worker work allocation (bundle/size/color/qty).
                          Earning = allocated_quantity x rate_snapshot.
                          ALLOCATION-DRIVEN (NOT cost ÷ workers).
  • WorkerLedgerEntry   — append-only immutable money ledger. Balance =
                          SUM(credits) − SUM(debits), NEVER stored.
  • WorkerAdvance       — immutable advance record (+attachment, audit). A
                          SEPARATE loan pool — does NOT post to the payable
                          ledger; recovered at settlement by owner's choice.
  • PayrollSettlement   — on-demand payout event (owner settles anytime).
  • PayrollSettlementItem — per-advance recovery line (owner-controlled).
  • WorkerProfile       — per-worker metadata (bank/UPI/opening advance).
  See docs/production/SETTLEMENT_ARCHITECTURE.md for the full design.

Discipline (mirrors history_service):
  • expense/services/ledger_service is the SOLE writer of WorkerLedgerEntry.
  • Rows are append-only — never UPDATE/DELETE. Corrections = reversal entry.
  • Running balance never stored. No signals. Cross-app FKs string + upstream.
"""
from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class StageWorkAssignment(TimeStampedModel):
    """A worker's allocated slice of a stage's work + the earning it generates.

    Standalone FK model — NOT a ManyToMany `through`. One worker can have MANY
    assignments per stage (Bundle A AND Bundle C), so there is NO uniqueness on
    (stage_record, worker). Earning is frozen at creation:
        earning_amount_snapshot = allocated_quantity × earning_rate_snapshot
    A later rate-card edit never changes historical pay.
    """

    # PROTECT — payroll source row; never orphan it on a stage-record delete.
    stage_record = models.ForeignKey(
        'production.AddaStageRecord', on_delete=models.PROTECT,
        related_name='work_assignments',
    )
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='work_assignments',
    )
    # Work dimensions — nullable so coarse stages (stitching/finishing) can
    # allocate at whatever grain they need. Cutting allocates at bundle level.
    bundle = models.ForeignKey(
        'production.CuttingBundle', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    size = models.ForeignKey(
        'production.ProductSize', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    color = models.ForeignKey(
        'raw_materials.ClothColor', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    pattern = models.ForeignKey(
        'production.ProductPattern', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    # Precise source line (per-bundle-item allocation). size/color/pattern are
    # denormalised from this item; PROTECT so a paid item can't be deleted.
    bundle_item = models.ForeignKey(
        'production.CuttingBundleItem', on_delete=models.PROTECT,
        null=True, blank=True, related_name='work_assignments',
    )
    # The basis this worker is paid on (pieces / bundles / layers).
    allocated_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    # Frozen at allocation time (copied from WorkflowStage.cost_rate).
    earning_rate_snapshot = models.DecimalField(max_digits=10, decimal_places=4)
    earning_amount_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.CharField(max_length=200, blank=True)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+',
    )
    # Soft-void for corrections. The row + its ledger credit are immutable; a
    # void reverses the credit (balance nets to 0) and excludes the row from
    # the item's allocated total + active work lists. Never hard-deleted.
    voided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['worker', '-created_at']),
            models.Index(fields=['stage_record']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.worker} · {self.allocated_quantity} × {self.earning_rate_snapshot} = {self.earning_amount_snapshot}"


class WorkerLedgerEntry(TimeStampedModel):
    """Append-only, immutable money ledger. The financial source of truth.

    Balance (payable) = SUM(credit.amount) − SUM(debit.amount), computed live —
    NEVER stored. Every credit traces to a source row (assignment); every debit
    to an advance/payment. Corrections = a `reversal` entry (opposite direction,
    `reverses` FK) + a fresh correct entry. Rows are never UPDATE/DELETE'd.
    """

    class EntryType(models.TextChoices):
        CREDIT = 'credit', 'Credit'   # increases payable (factory owes worker)
        DEBIT = 'debit', 'Debit'      # reduces payable

    class Category(models.TextChoices):
        STAGE_EARNING = 'stage_earning', 'Stage Earning'
        PRODUCTION_EARNING = 'production_earning', 'Production Earning'
        ADVANCE = 'advance', 'Advance'           # legacy — advances no longer post here
        PAYMENT = 'payment', 'Payment'           # legacy — replaced by settlement_payment
        SETTLEMENT_PAYMENT = 'settlement_payment', 'Settlement Payment'  # cash paid at a settlement
        ADVANCE_RECOVERY = 'advance_recovery', 'Advance Recovery'        # earnings used to repay advance
        DEDUCTION = 'deduction', 'Deduction'
        ADJUSTMENT = 'adjustment', 'Adjustment'
        REVERSAL = 'reversal', 'Reversal'

    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='ledger_entries',
    )
    entry_type = models.CharField(max_length=8, choices=EntryType.choices)
    category = models.CharField(max_length=24, choices=Category.choices)
    # Always POSITIVE — direction comes from entry_type (lets SUM aggregate).
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    # Source FKs — exactly one populated per non-reversal/adjustment entry.
    assignment = models.ForeignKey(
        StageWorkAssignment, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    advance = models.ForeignKey(
        'WorkerAdvance', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    # Settlement that produced this debit (settlement_payment / advance_recovery).
    settlement = models.ForeignKey(
        'PayrollSettlement', on_delete=models.PROTECT,
        null=True, blank=True, related_name='ledger_entries',
    )
    reverses = models.ForeignKey(
        'self', on_delete=models.PROTECT,
        null=True, blank=True, related_name='reversed_by',
    )
    entry_date = models.DateField()
    notes = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+',
    )

    class Meta:
        indexes = [
            models.Index(fields=['worker', '-created_at']),
            models.Index(fields=['worker', 'entry_type']),
            models.Index(fields=['worker', 'category']),
        ]
        ordering = ['-created_at']
        permissions = [
            ('view_all_payroll', 'Can view all workers payroll'),
            ('manage_advances', 'Can record worker advances'),
            ('manage_payments', 'Can record worker payments'),
        ]
        constraints = [
            # An entry can be reversed at most once — DB backstop for the
            # app-level double-reverse guard (race-proof).
            models.UniqueConstraint(
                fields=['reverses'], condition=models.Q(reverses__isnull=False),
                name='uniq_one_reversal_per_entry',
            ),
        ]

    def __str__(self):
        sign = '+' if self.entry_type == self.EntryType.CREDIT else '-'
        return f"{self.worker} {sign}{self.amount} ({self.category})"


class WorkerAdvance(TimeStampedModel):
    """Cash given to a worker before earnings. Immutable + full audit."""

    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='advances',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    advance_date = models.DateField()
    notes = models.TextField(blank=True)
    attachment = models.FileField(upload_to='advances/', null=True, blank=True)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+',
    )

    class Meta:
        indexes = [models.Index(fields=['worker', '-advance_date'])]
        ordering = ['-advance_date', '-created_at']

    def __str__(self):
        return f"Advance {self.amount} → {self.worker} on {self.advance_date}"


class PayrollSettlement(TimeStampedModel):
    """A settlement event — the owner pays a worker on a payroll day. Immutable.

    NOT a fixed monthly cycle. The owner settles whenever they decide. A
    settlement clears (all or part of) the worker's pending payable and may
    recover (all or part of) outstanding advances — the owner chooses both.

    Snapshot fields freeze the state at settlement time for audit; balances are
    still derived live everywhere else (never read these back as the truth).

        amount_paid + advance_deducted == payable_settled   (cash + recovery)
        advance_deducted             == Σ items.amount_recovered
    """

    class Method(models.TextChoices):
        CASH = 'cash', 'Cash'
        BANK = 'bank', 'Bank Transfer'
        UPI = 'upi', 'UPI'
        OTHER = 'other', 'Other'

    reference = models.CharField(max_length=20, unique=True)   # SETL-0001
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='settlements',
    )
    settlement_date = models.DateField()
    # Snapshots at settlement time (audit only; never recomputed).
    payable_before = models.DecimalField(max_digits=12, decimal_places=2)
    advance_outstanding_before = models.DecimalField(max_digits=12, decimal_places=2)
    advance_deducted = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=8, choices=Method.choices, default=Method.CASH)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+',
    )

    class Meta:
        indexes = [models.Index(fields=['worker', '-settlement_date'])]
        ordering = ['-settlement_date', '-created_at']

    def __str__(self):
        return f"{self.reference} · {self.worker} · paid {self.amount_paid}"


class PayrollSettlementItem(models.Model):
    """One advance-recovery line of a settlement — owner-controlled (D3).

    The settlement screen lists every outstanding advance; the owner types how
    much to recover from EACH. One row per advance touched. The header's
    `advance_deducted` equals the sum of these rows.
    """

    settlement = models.ForeignKey(
        PayrollSettlement, on_delete=models.PROTECT, related_name='items',
    )
    advance = models.ForeignKey(
        WorkerAdvance, on_delete=models.PROTECT, related_name='recoveries',
    )
    amount_recovered = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        indexes = [models.Index(fields=['advance'])]

    def __str__(self):
        return f"{self.settlement.reference}: −{self.amount_recovered} from adv#{self.advance_id}"


class WorkerProfile(TimeStampedModel):
    """Per-worker payroll metadata (D4). NO stored totals — those stay derived.

    Auto-created on demand (`get_or_create`) so existing workers need no backfill.
    `opening_advance` seeds Advance Outstanding for loans given before the system.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='worker_profile',
    )
    phone = models.CharField(max_length=20, blank=True)
    bank_account_name = models.CharField(max_length=120, blank=True)
    bank_account_number = models.CharField(max_length=40, blank=True)
    bank_ifsc = models.CharField(max_length=20, blank=True)
    upi_id = models.CharField(max_length=80, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    # Advances given before the system existed — part of total outstanding.
    opening_advance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Profile · {self.user}"
