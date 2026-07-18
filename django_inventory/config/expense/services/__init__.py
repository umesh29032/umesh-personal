"""Expense service layer — payroll writes + reads.

Single-writer discipline (mirrors tracking.history_service):
  ledger_service     → sole writer of WorkerLedgerEntry
  allocation_service → sole writer of StageWorkAssignment (+ stage_earning credit)
  advance_service    → sole writer of WorkerAdvance (separate loan pool, no debit)
  settlement_service → sole writer of PayrollSettlement (+ settlement debits)
  payroll_service    → aggregations + per-worker access scoping + the ONE
                       pay-basis write (sole writer of WorkerPayBasisAudit, R4)
  expense_service    → sole writer of FactoryExpense (R5; create/void, no edit;
                       ADR-0011: factory-level only, never ledger/costing)
"""
from . import ledger_service  # noqa: F401  — import first; writers depend on it
from .ledger_service import (
    log_credit, log_debit, reverse_entry, worker_balance,
)
from .allocation_service import (
    allocate_stage_work, item_allocation_summary, void_allocation,
)
from .advance_service import record_advance
from .settlement_service import create_settlement
from .payroll_service import (
    advance_outstanding, advance_remaining, can_view_worker, is_monthly,
    outstanding_advances, set_pay_basis, unsettled_contribution_count,
    unsettled_expected, worker_adda_earnings, worker_advances, worker_assignments, worker_ledger,
    worker_production_stats, worker_settlements, worker_stage_earnings,
    worker_summary,
)
from .reconciliation_service import reconcile_stage_pay, summarize as reconcile_summarize
from .expense_service import monthly_totals, record_expense, void_expense
from .fnf_service import fnf_execute, fnf_preview

__all__ = [
    'ledger_service',
    'log_credit', 'log_debit', 'reverse_entry', 'worker_balance',
    'allocate_stage_work', 'item_allocation_summary', 'void_allocation',
    'record_advance',
    'create_settlement',
    'can_view_worker', 'worker_summary', 'worker_ledger', 'worker_assignments', 'unsettled_expected',
    'worker_production_stats', 'worker_stage_earnings', 'worker_adda_earnings',
    'advance_outstanding', 'advance_remaining', 'outstanding_advances',
    'worker_advances', 'worker_settlements',
    # R4 pay basis (PDD §27-D4)
    'is_monthly', 'set_pay_basis', 'unsettled_contribution_count',
    # R5 factory expenses (PDD §21 / ADR-0011)
    'record_expense', 'void_expense', 'monthly_totals',
    # R7 Full & Final (PDD §20/§27-D5) — orchestration, writes nothing itself
    'fnf_preview', 'fnf_execute',
    # PAY-4 reconciliation
    'reconcile_stage_pay', 'reconcile_summarize',
]
