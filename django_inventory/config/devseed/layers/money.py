"""Layer 8 — expenses + money (writer-map rows: adda_settlement_service ·
advance_service · expense_service — the single-writer money boundary; every
WorkerLedgerEntry below is a SERVICE OUTCOME of finalize, never a direct write).

Ledger recount discipline (owner Wave-1 mandate): count + Σ captured BEFORE and
AFTER every money step; the executor returns the reconciliation — an
unexplained delta is an assertion failure upstream.
"""

from decimal import Decimal

from django.apps import apps
from django.db.models import Sum

from expense.services import adda_settlement_service, advance_service, expense_service

from devseed.layers import DivergenceError


def ledger_snapshot():
    L = apps.get_model("expense", "WorkerLedgerEntry")
    agg = L.objects.aggregate(s=Sum("amount"))
    return {"count": L.objects.count(), "sum": str(agg["s"] or Decimal("0"))}


def settle_adda(adda, *, manager, expected_total):
    """create_draft → finalize via the single writer; returns reconciliation."""
    AS_ = apps.get_model("expense", "AddaSettlement")
    existing = AS_.objects.filter(adda=adda, status="finalized").first()
    if existing is not None:
        return {"created": 0, "skipped": 1, "settlement": existing,
                "ledger_before": ledger_snapshot(), "ledger_after": ledger_snapshot(),
                "ledger_delta_expected": "0"}

    before = ledger_snapshot()
    settlement = adda_settlement_service.create_draft(adda=adda, user=manager)
    settlement = adda_settlement_service.finalize_adda_settlement(
        settlement=settlement, user=manager)
    after = ledger_snapshot()

    if Decimal(str(settlement.expected_total)) != Decimal(expected_total):
        raise DivergenceError(
            f"settlement {settlement.reference}: expected_total "
            f"{settlement.expected_total} != scenario golden {expected_total}")
    return {"created": 1, "skipped": 0, "settlement": settlement,
            "ledger_before": before, "ledger_after": after,
            "ledger_delta_expected": expected_total}


def seed_advance(*, manager, worker, amount, advance_date):
    """WorkerAdvance via advance_service (the loan pool's sole writer)."""
    WA = apps.get_model("expense", "WorkerAdvance")
    if WA.objects.filter(worker=worker, amount=Decimal(amount)).exists():
        return {"created": 0, "skipped": 1}
    advance_service.record_advance(
        user=manager, worker=worker, amount=Decimal(amount),
        advance_date=advance_date, notes="devseed")
    return {"created": 1, "skipped": 0}


def seed_factory_expense(*, actor, category, amount, expense_date):
    """FactoryExpense via expense_service (R5 sole writer; never per-Adda)."""
    FE = apps.get_model("expense", "FactoryExpense")
    if FE.objects.filter(category=category, amount=Decimal(amount),
                         expense_date=expense_date).exists():
        return {"created": 0, "skipped": 1}
    expense_service.record_expense(
        category=category, amount=Decimal(amount),
        expense_date=expense_date, actor=actor, notes="devseed")
    return {"created": 1, "skipped": 0}
