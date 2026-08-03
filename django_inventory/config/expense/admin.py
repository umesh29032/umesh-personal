"""Read-mostly admin for payroll inspection. Money rows are append-only —
edits MUST go through the service layer (allocation/ledger/advance/settlement),
so these are view-only here. Deleting via admin would orphan PROTECT'd ledger
debits (e.g. delete a PayrollSettlement → advance_recovery debit stranded →
advance_outstanding overstated), so add/change/delete are all disabled."""
from django.contrib import admin

from .models import (
    ExpenseGenerationRecord, ExpenseTemplate, ExpenseTemplateAmountAudit,
    FactoryExpense, PayrollSettlement, PayrollSettlementItem,
    StageWorkAssignment,
    WorkerAdvance, WorkerLedgerEntry, WorkerPayBasisAudit, WorkerProfile,
    AddaSettlement, AddaSettlementItem,
)


class _MoneyReadOnlyAdmin(admin.ModelAdmin):
    """View-only: money rows are written ONLY by services, never hand-edited.

    Prevents admin from bypassing the sole-writer discipline or orphaning
    PROTECT'd ledger rows by deleting a settlement/advance/assignment."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StageWorkAssignment)
class StageWorkAssignmentAdmin(_MoneyReadOnlyAdmin):
    list_display = ('worker', 'stage_record', 'allocated_quantity',
                    'earning_rate_snapshot', 'earning_amount_snapshot', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('worker__email',)
    raw_id_fields = ('stage_record', 'worker', 'bundle', 'size', 'color', 'entered_by')


@admin.register(WorkerLedgerEntry)
class WorkerLedgerEntryAdmin(_MoneyReadOnlyAdmin):
    list_display = ('worker', 'entry_type', 'category', 'amount', 'entry_date', 'created_at')
    list_filter = ('entry_type', 'category', 'entry_date')
    search_fields = ('worker__email',)
    raw_id_fields = ('worker', 'assignment', 'advance', 'settlement', 'reverses', 'created_by')


@admin.register(WorkerAdvance)
class WorkerAdvanceAdmin(_MoneyReadOnlyAdmin):
    list_display = ('worker', 'amount', 'advance_date', 'entered_by', 'created_at')
    list_filter = ('advance_date',)
    search_fields = ('worker__email',)
    raw_id_fields = ('worker', 'entered_by')


class PayrollSettlementItemInline(admin.TabularInline):
    """View-only: the parent settlement is read-only, but a TabularInline
    defaults to add/change/delete=True — without these overrides an admin could
    mutate/delete recovery rows and break advance_deducted == Σ amount_recovered."""
    model = PayrollSettlementItem
    extra = 0
    raw_id_fields = ('advance',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PayrollSettlement)
class PayrollSettlementAdmin(_MoneyReadOnlyAdmin):
    list_display = ('reference', 'worker', 'settlement_date', 'amount_paid',
                    'advance_deducted', 'method', 'created_at')
    list_filter = ('method', 'settlement_date')
    search_fields = ('reference', 'worker__email')
    raw_id_fields = ('worker', 'created_by')
    inlines = [PayrollSettlementItemInline]


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'pay_basis', 'phone', 'joining_date',
                    'opening_advance', 'is_active')
    list_filter = ('is_active', 'pay_basis')
    search_fields = ('user__email', 'phone', 'bank_account_name')
    raw_id_fields = ('user',)
    # R4: pay_basis changes ONLY via payroll_service.set_pay_basis (audited,
    # super-admin-gated) — admin must not offer an unaudited side door.
    readonly_fields = ('pay_basis',)


@admin.register(FactoryExpense)
class FactoryExpenseAdmin(_MoneyReadOnlyAdmin):
    """R5: create/void ONLY via expense_service (append-only posture) —
    admin is inspection-only, same as every money table."""
    list_display = ('expense_date', 'category', 'amount', 'worker',
                    'entered_by', 'voided_at')
    list_filter = ('category',)
    search_fields = ('notes', 'worker__email', 'entered_by__email')
    raw_id_fields = ('worker', 'entered_by', 'voided_by')


@admin.register(WorkerPayBasisAudit)
class WorkerPayBasisAuditAdmin(_MoneyReadOnlyAdmin):
    """R4: append-only audit — inspection only, sole writer is
    payroll_service.set_pay_basis."""
    list_display = ('worker', 'old_basis', 'new_basis', 'changed_by',
                    'unsettled_lines_at_change', 'created_at')
    list_filter = ('new_basis',)
    search_fields = ('worker__email',)
    raw_id_fields = ('worker', 'changed_by')


@admin.register(AddaSettlement)
class AddaSettlementAdmin(_MoneyReadOnlyAdmin):
    """V2-2: financial event — read-only in admin; all writes via
    adda_settlement_service (single-writer rule)."""
    list_display = ('reference', 'adda', 'status', 'expected_total',
                    'variance_total', 'settled_at')
    list_filter = ('status',)
    search_fields = ('reference', 'adda__code')


@admin.register(AddaSettlementItem)
class AddaSettlementItemAdmin(_MoneyReadOnlyAdmin):
    """Frozen per-worker snapshot — append-only, never edited (owner Q3)."""
    list_display = ('adda_settlement', 'worker', 'expected_earning',
                    'advance_recovered', 'final_payable', 'settled_at')
    search_fields = ('adda_settlement__reference', 'worker__email')


# ── Monthly Expense Engine (MEE-A) — same inspection-only posture: the three
#    engine tables are written ONLY by the expense_service family (MEE-B). ──

@admin.register(ExpenseTemplate)
class ExpenseTemplateAdmin(_MoneyReadOnlyAdmin):
    """Recurring-expense config — lifecycle + audited amount changes via the
    service only; admin inspects."""
    list_display = ('label', 'category', 'amount', 'frequency', 'worker',
                    'start_date', 'end_date', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('label', 'worker__email')
    raw_id_fields = ('worker', 'created_by')


@admin.register(ExpenseGenerationRecord)
class ExpenseGenerationRecordAdmin(_MoneyReadOnlyAdmin):
    """Idempotency coverage (template × period → generated FactoryExpense)."""
    list_display = ('template', 'period_key', 'expense', 'generated_by',
                    'superseded_at', 'created_at')
    list_filter = ('period_key',)
    search_fields = ('template__label', 'period_key')
    raw_id_fields = ('template', 'expense', 'generated_by', 'supersedes')


@admin.register(ExpenseTemplateAmountAudit)
class ExpenseTemplateAmountAuditAdmin(_MoneyReadOnlyAdmin):
    """Append-only amount-change trail (owner ruling 2026-07-18)."""
    list_display = ('template', 'old_amount', 'new_amount', 'changed_by',
                    'reason', 'created_at')
    search_fields = ('template__label', 'reason')
    raw_id_fields = ('template', 'changed_by')
