"""Stage-engine framework (not a stage).

StageHandler contract + the dispatch registry. See handler.py for the R1 earnings
decision (handlers stay pure; the base service owns the one production->expense
booking edge).
"""
from .credit import ensure_worker_credit, stage_is_payable
from .handler import CompletionResult, ReopenResult, StageHandler, WorkerAllocation
from .registry import all_handlers, autodiscover, clear, get, has, register

__all__ = [
    'StageHandler', 'CompletionResult', 'ReopenResult', 'WorkerAllocation',
    'register', 'get', 'has', 'all_handlers', 'clear', 'autodiscover',
    'stage_is_payable', 'ensure_worker_credit',
]
