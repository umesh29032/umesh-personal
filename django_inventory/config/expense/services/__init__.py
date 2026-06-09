"""Expense service layer — payroll writes + reads.

Single-writer discipline (mirrors tracking.history_service):
  ledger_service     → sole writer of WorkerLedgerEntry
  allocation_service → sole writer of StageWorkAssignment (+ stage_earning credit)
  advance_service    → sole writer of WorkerAdvance (separate loan pool, no debit)
  settlement_service → sole writer of PayrollSettlement (+ settlement debits)
  payroll_service    → read-only aggregations + per-worker access scoping
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
    advance_outstanding, advance_remaining, can_view_worker, outstanding_advances,
    worker_adda_earnings, worker_advances, worker_assignments, worker_ledger,
    worker_production_stats, worker_settlements, worker_stage_earnings,
    worker_summary,
)
from .reconciliation_service import reconcile_stage_pay, summarize as reconcile_summarize

__all__ = [
    'ledger_service',
    'log_credit', 'log_debit', 'reverse_entry', 'worker_balance',
    'allocate_stage_work', 'item_allocation_summary', 'void_allocation',
    'record_advance',
    'create_settlement',
    'can_view_worker', 'worker_summary', 'worker_ledger', 'worker_assignments',
    'worker_production_stats', 'worker_stage_earnings', 'worker_adda_earnings',
    'advance_outstanding', 'advance_remaining', 'outstanding_advances',
    'worker_advances', 'worker_settlements',
    # PAY-4 reconciliation
    'reconcile_stage_pay', 'reconcile_summarize',
]
