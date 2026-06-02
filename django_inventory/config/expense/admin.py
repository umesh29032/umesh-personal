"""Read-mostly admin for payroll inspection. Money rows are append-only —
edits MUST go through the service layer (allocation/ledger/advance/settlement),
so these are view-only here. Deleting via admin would orphan PROTECT'd ledger
debits (e.g. delete a PayrollSettlement → advance_recovery debit stranded →
advance_outstanding overstated), so add/change/delete are all disabled."""
from django.contrib import admin

from .models import (
    PayrollSettlement, PayrollSettlementItem, StageWorkAssignment,
    WorkerAdvance, WorkerLedgerEntry, WorkerProfile,
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
    list_display = ('user', 'phone', 'joining_date', 'opening_advance', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('user__email', 'phone', 'bank_account_name')
    raw_id_fields = ('user',)
