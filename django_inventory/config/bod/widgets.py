"""bod.widgets — PRESENTATION adapters (BOD-C).

WINDOW-NEVER-ENGINE: every function here is a THIN adapter — it calls the
owning module's certified service and maps the result onto the generic tile
shape `{"value", "sub": [(label, value)...], "note"}`. Zero business logic,
zero calculations beyond the census-recorded presentation conventions
(presentation-sums/-distincts over owner rows). The `cache` dict is per-request
so shared owner calls (operations_digest · settlement_queue) run ONCE per page
regardless of how many tiles consume them (BOD-D6 budget discipline).

Ladder provenance per adapter = the BOD-B census row (BOD_BUILD_LOG §BOD-B.1).
"""


def _digest(cache):
    if "digest" not in cache:
        from production.services.operations_digest import operations_digest
        cache["digest"] = operations_digest()
    return cache["digest"]


def _queue(cache):
    if "queue" not in cache:
        from expense.services import adda_settlement_service
        cache["queue"] = adda_settlement_service.settlement_queue()
    return cache["queue"]


# ── Wave 1 — digest-backed L1 (census rows A3 · A4 · P1 · P3) ────────────────

def stalled_addas(cache):
    d = _digest(cache)
    return {"value": d["stalled_count"],
            "sub": [("threshold", f"> {d['stalled_threshold_days']} days")],
            "note": None}


def pending_reports(cache):
    return {"value": _digest(cache)["pending_reports"], "sub": [], "note": None}


def active_addas(cache):
    return {"value": _digest(cache)["active_addas"], "sub": [], "note": None}


def completed_today(cache):
    # Owner P4 ruling (Option A): today's production = completed ADDAS today;
    # pieces-today is deferred until a certified aggregate exists.
    return {"value": _digest(cache)["completed_today"], "sub": [], "note": None}


# ── Wave 1 — settlement queue COUNTS (A1 · A2; ₹ tiles belong to BOD-D) ──────

def settlements_ready(cache):
    return {"value": len(_queue(cache)["ready"]), "sub": [], "note": None}


def settlements_blocked(cache):
    waiting = _queue(cache)["waiting"]
    # The blocking stage names come from the owner service's own rows.
    top = waiting[0]["incomplete"][:2] if waiting else []
    return {"value": len(waiting),
            "sub": [("waiting on", ", ".join(top))] if top else [],
            "note": None}


# ── Wave 2 — materials (M1 · M3 via the owner-gated G-1/G-2 extractions) ─────

def roll_stock(cache):
    from raw_materials.services import roll_service
    c = roll_service.stock_status_counts()
    return {"value": c["available"],
            "sub": [("total", c["total"]), ("damaged", c["damaged"]),
                    ("used", c["used"])],
            "note": None}


def stock_by_warehouse(cache):
    from raw_materials.services import roll_service
    rows = roll_service.stock_by_location()
    return {"value": len(rows),
            "sub": [(loc.name, f"{loc.available}/{loc.roll_count}")
                    for loc in rows][:4],
            "note": None}


# ── Wave 1 — machines (MC1; owner taste: COUNTS ONLY, no holder lists) ───────

def _machines(cache):
    if "machines" not in cache:
        from machines.services import machine_service
        cache["machines"] = machine_service.register_counts()
    return cache["machines"]


def machine_counts(cache):
    c = _machines(cache)
    return {"value": c["total"],
            "sub": [("active", c["active"]), ("maintenance", c["maintenance"]),
                    ("assigned now", c["assigned_now"])],
            "note": None}


# ── Wave 3 — production extras (P2 · P5 via the owner-gated G-4 extraction) ──

def on_hold_addas(cache):
    # fields subset: this tile needs ONE of the four G-4 counts (BOD-D6) —
    # same owning function, same expression, just the others skipped.
    from production.services.operations_digest import adda_status_counts
    return {"value": adda_status_counts(fields=("on_hold",))["on_hold"],
            "sub": [], "note": None}


def stage_chips(cache):
    # P5 (owner-approved chips): in-progress Addas per stage, straight from the
    # G-4 extraction. kind="chips" → the template renders sub as a chip row.
    from production.services.operations_digest import stage_breakdown
    chips = stage_breakdown()
    return {"value": len(chips),
            "sub": [(c["label"], c["count"]) for c in chips],
            "kind": "chips", "note": None}


# ── Wave 3 — workers (W1; counts only — W2/W3 deferred/BOD-D by owner) ───────

def workers_active(cache):
    # Presentation-DISTINCT over pending_report_tasks rows (the census
    # convention) — workers currently on the hook for an open stage.
    from production.services.operations_digest import pending_report_tasks
    n = pending_report_tasks().values("worker").distinct().count()
    return {"value": n,
            "sub": [("machines out", _machines(cache)["assigned_now"])],
            "note": None}


# ── BOD-D — FINANCIAL (owner-authorized money wave 2026-07-18) ───────────────
# Every ₹ below is the OWNING expense service's number, untouched: no
# derivation, no combination across sources, no Python re-aggregation of
# anything the service already totals. Rendering uses the {% money %} tag
# (core.templatetags.finance — the single owner of currency display), so
# adapters pass Decimals through as-is. Tiles marked "money": True /
# "money_sub" render via that tag. FINANCIAL widgets additionally gate on
# FINANCIAL_ROLES in the view (charter D1.6).

def _payroll(cache):
    # payroll_totals() was "built FOR the digest" (census F5/F6) and
    # operations_digest() already carries its two numbers verbatim — reuse
    # that same call instead of running the identical aggregation twice per
    # page (BOD-D6). Digest absent (never on this page) → call the owner
    # service directly; either path = the ONE certified source.
    if "digest" in cache:
        return cache["digest"]
    if "payroll" not in cache:
        from expense.services import payroll_service
        cache["payroll"] = payroll_service.payroll_totals()
    return cache["payroll"]


def _month_expenses(cache):
    if "month_expenses" not in cache:
        from django.utils import timezone
        from expense.services import expense_service
        now = timezone.localtime()
        cache["month_expenses"] = expense_service.monthly_totals(now.year, now.month)
        cache["month_label"] = now.strftime("%b %Y")
    return cache["month_expenses"]


def month_expenses(cache):
    # F1: current month's FactoryExpense total (void-aware) — the CERTIFIED
    # factory-expense truth (ADR-0011: factory-level, NEVER per-Adda).
    m = _month_expenses(cache)
    return {"value": m["total"], "money": True,
            "sub": [("entries", m["count"]), ("month", cache["month_label"])],
            "note": None}


def expense_categories(cache):
    # F2: the same monthly_totals call's by_category split (PDD §21 locked
    # category set). Ordering = presentation only (largest first).
    m = _month_expenses(cache)
    cats = sorted(m["by_category"].values(),
                  key=lambda v: (-v["total"], v["label"]))
    return {"value": None,
            "money_sub": [(v["label"], v["total"]) for v in cats],
            "sub": [], "note": "No expenses this month." if not cats else None}


def outstanding_payments(cache):
    # F5: Σ ledger credits − Σ debits (Earned-not-yet-paid) — payroll_totals,
    # the exact payroll-overview definition. Never combined with Expected.
    return {"value": _payroll(cache)["pending_payable"], "money": True,
            "sub": [], "note": None}


def outstanding_advances(cache):
    # F6: Σ advances given − Σ non-reversed recoveries (PA-12-A) — the
    # certified advance system's own exposure number.
    return {"value": _payroll(cache)["advance_exposure"], "money": True,
            "sub": [], "note": None}


def expected_payouts(cache):
    # F3/W3: Σ of the queue's per-Adda `expected` (each computed by the owning
    # settlement funnel incl. the PA-11-2 grouped→0 guard). The Σ-of-ready is
    # the census-R-2 sanctioned presentation-sum of owner rows — the service
    # exposes no factory-wide total. Expected ≠ Earned: separate tile, never
    # combined with pending_payable.
    from decimal import Decimal
    ready = _queue(cache)["ready"]
    total = sum((r["expected"] for r in ready), Decimal("0.00"))
    return {"value": total, "money": True,
            "sub": [("addas ready", len(ready))], "note": None}
