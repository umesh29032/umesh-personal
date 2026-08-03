"""SEED-D — the remaining registry scenarios (layers 9–11 + feature slices +
edge-case worlds). NO new architecture: every world derives from the wave-1
minimal-money shape (per-tag isolation, the recipes' tag pattern) and every
post-step calls certified services directly. Two registry entries stay
NON-executable BY OWNER RULING: `regression-settlement-225` (spec §12 A1 —
historical evidence) and `performance` (DATA-D6 — volume targets deferred)."""

from decimal import Decimal

from django.apps import apps
from django.core.exceptions import ValidationError

from devseed.scenarios.minimal_money import MINIMAL_MONEY

W = "@test.local"


def _world(slug, tag, **over):
    """Per-tag clone of the deterministic money world (isolation on shared
    scratch DBs = distinct product/masters per scenario; stage library +
    cast converge shared)."""
    w = {**MINIMAL_MONEY, "slug": slug}
    w["dev_prefixes"] = ("dev.", "DEV-", "dev-")  # per-tag handles, family-wide marking
    w["product"] = {"code": f"DEV-{tag}-TEE", "name": f"DEV-{tag} Tee"}
    w["masters"] = {**MINIMAL_MONEY["masters"],
                    "cloth_type": f"DEV-{tag}-COTTON",
                    "cloth_color": f"DEV-{tag}-RED",
                    "storage": f"DEV-{tag}-RACK"}
    w["rolls"] = {"cloth_type": f"DEV-{tag}-COTTON", "storage": f"DEV-{tag}-RACK",
                  "rolls": [{"color": f"DEV-{tag}-RED", "qty": 1}]}
    w["adda_journey"] = {**MINIMAL_MONEY["adda_journey"],
                         "adda_code": f"DEV-{tag}-TEE-001"}
    w.update(over)
    return w


# ── demo (SEED-D2: seed_demo = the minimal-plus single-product journey) ──────
DEMO = _world("demo", "DEMO")

# ── factory (SEED-D2: the full three-product factory = the golden journeys;
#    + the machines slice — spec §7 full-demo row: "cast, machines, rolls") ──
FACTORY = {"slug": "factory",
           "composite": ["regression-lower", "regression-tshirt",
                         "regression-3patti", "feature-machines"]}

# ── feature slices ───────────────────────────────────────────────────────────
F_ALLOCATION = _world("feature-allocation", "ALC")
F_ALLOCATION.pop("settlement")            # layers (2,3,4,6,7) — no money
F_ALLOCATION["adda_journey"] = {**F_ALLOCATION["adda_journey"], "stages": [],
                                "expect_completed": False}
# Pool law: _upstream_pool_sources SKIPS NONE stages — cutting (the source)
# must be a pool participant too, not just the consuming stage.
F_ALLOCATION["grain"] = [{"stage": "cutting", "dimensions": "quantity"},
                         {"stage": "dev-min-stitching", "dimensions": "quantity"}]
F_ALLOCATION["post"] = "allocation"

# FnF world: DEDICATED leaver identity (spec §11 leaver-cast class, dev.hlp.nkb
# pattern) — never the shared dev.min.worker, whose deactivation would poison
# every later world seeded on the same scratch DB.
F_FNF = _world("feature-fnf", "FNF")
F_FNF["cast"] = MINIMAL_MONEY["cast"] + [
    {"handle": "dev.min.leaver" + W, "role": "worker",
     "first_name": "DevMin", "last_name": "Leaver", "skills": "*"}]
F_FNF["adda_journey"] = {**F_FNF["adda_journey"], "worker": "dev.min.leaver" + W}
F_FNF["post"] = "fnf"

F_MACHINES = {
    "slug": "feature-machines",
    "dev_prefixes": ("dev.", "DEV-", "dev-"),
    "cast": MINIMAL_MONEY["cast"],
    "sa_handle": MINIMAL_MONEY["sa_handle"],
    "manager_handle": MINIMAL_MONEY["manager_handle"],
    "masters": {**MINIMAL_MONEY["masters"], "cloth_type": "DEV-MCH-COTTON",
                "cloth_color": "DEV-MCH-RED", "storage": "DEV-MCH-RACK"},
    "machines": {"machine_type": "DEV-MCH Machine",
                 "machines": [{"code": "DEV-MCH-M1", "name": "DEV-MCH Overlock"}]},
    "rolls": {"cloth_type": "DEV-MCH-COTTON", "storage": "DEV-MCH-RACK", "rolls": []},
    "post": "machine_assign",
}

F_PATTERNS = _world("feature-patterns-ai", "PAI")
F_PATTERNS.pop("settlement")
F_PATTERNS.pop("adda_journey")
F_PATTERNS["rolls"] = {**F_PATTERNS["rolls"], "rolls": []}  # no journey → no rolls
F_PATTERNS["sizes"] = ["s", "m"]
F_PATTERNS["patterns"] = ["DEV-PAI Front", "DEV-PAI Back"]

F_STOREFRONT = {
    "slug": "feature-storefront",
    "dev_prefixes": ("dev.", "DEV-", "dev-"),
    "cast": MINIMAL_MONEY["cast"],
    "sa_handle": MINIMAL_MONEY["sa_handle"],
    "manager_handle": MINIMAL_MONEY["manager_handle"],
    "masters": {**MINIMAL_MONEY["masters"], "cloth_type": "DEV-SF-COTTON",
                "cloth_color": "DEV-SF-RED", "storage": "DEV-SF-RACK"},
    "rolls": {"cloth_type": "DEV-SF-COTTON", "storage": "DEV-SF-RACK", "rolls": []},
    "storefront": {"category": "DEV-SF Category",
                   "product": {"name": "DEV-SF Featured Tee", "price": "499"}},
}

# tracking-exports: flow WITHOUT barcode_generation ⇒ cutting generates inline
# barcodes via the certified assembly (layer-11 rows = service outcomes).
F_TRACKING = _world("feature-tracking-exports", "TRK")
F_TRACKING.pop("settlement")
F_TRACKING["post"] = "assert_barcodes"

# feature-bod (D8, spec amendment A2 — BOD-F 2026-07-18): the BOD demo world —
# a settled journey (ledger credits → the Outstanding Payments tile) plus one
# DEV factory expense (the This-Month's-Expenses / Categories tiles); the post
# step proves the board's OWNING services light up on this world (window-
# never-engine: the board owns nothing, so the world is proven at the services).
F_BOD = _world("feature-bod", "BOD")
F_BOD["post"] = "bod_board"

# feature-monthly-expense (MEE-E, dated spec amendment A3 — 2026-07-18): the
# Monthly Expense Engine world — templates + a generated period + a voided
# example (PHASE_16 §6.5), everything through the census-ADDENDUM-1 writers.
F_MEE = {
    "slug": "feature-monthly-expense",
    "dev_prefixes": ("dev.", "DEV-", "dev-"),
    "cast": MINIMAL_MONEY["cast"],
    "sa_handle": MINIMAL_MONEY["sa_handle"],
    "manager_handle": MINIMAL_MONEY["manager_handle"],
    "masters": {**MINIMAL_MONEY["masters"], "cloth_type": "DEV-MEE-COTTON",
                "cloth_color": "DEV-MEE-RED", "storage": "DEV-MEE-RACK"},
    "rolls": {"cloth_type": "DEV-MEE-COTTON", "storage": "DEV-MEE-RACK", "rolls": []},
    "post": "monthly_expense_engine",
}

# feature-rm-expense (RMX-F, dated spec amendment A4 — 2026-07-18): the
# Phase-17 proof world — priced/unpriced/damaged rolls + the REAL leftover
# chain, every step through certified writers (PHASE_17 §6.5 fixtures).
F_RMX = _world("feature-rm-expense", "RME")
F_RMX["rolls"] = {"cloth_type": "DEV-RME-COTTON", "storage": "DEV-RME-RACK",
                  "rolls": [{"color": "DEV-RME-RED", "qty": 3}]}
F_RMX["post"] = "rm_expense"

# ── edge-case worlds (the certified hard cases) ──────────────────────────────
E_OVERALLOC = _world("edge-overallocation-m6", "OVR")
E_OVERALLOC.pop("settlement")
E_OVERALLOC["grain"] = [{"stage": "cutting", "dimensions": "quantity"},
                        {"stage": "dev-min-stitching", "dimensions": "quantity"}]
E_OVERALLOC["adda_journey"] = {**E_OVERALLOC["adda_journey"], "stages": [],
                               "expect_completed": False}
E_OVERALLOC["post"] = "overallocation"

E_DAMAGED = _world("edge-damaged-rolls", "DMG")
E_DAMAGED.pop("settlement")
E_DAMAGED.pop("adda_journey")
E_DAMAGED["rolls"]["rolls"] = [{"color": "DEV-DMG-RED", "qty": 2}]
E_DAMAGED["post"] = "damaged_rolls"

E_MONTHLY = {
    "slug": "edge-monthly-worker",
    "dev_prefixes": ("dev.", "DEV-", "dev-"),
    "cast": MINIMAL_MONEY["cast"] + [
        {"handle": "dev.min.monthly" + W, "role": "worker",
         "first_name": "DevMin", "last_name": "Monthly", "skills": "*"}],
    "sa_handle": MINIMAL_MONEY["sa_handle"],
    "manager_handle": MINIMAL_MONEY["manager_handle"],
    "masters": {**MINIMAL_MONEY["masters"], "cloth_type": "DEV-MON-COTTON",
                "cloth_color": "DEV-MON-RED", "storage": "DEV-MON-RACK"},
    "rolls": {"cloth_type": "DEV-MON-COTTON", "storage": "DEV-MON-RACK", "rolls": []},
    "post": "monthly_worker",
}

E_INACTIVE = {
    "slug": "edge-inactive-users",
    "dev_prefixes": ("dev.", "DEV-", "dev-"),
    "cast": MINIMAL_MONEY["cast"] + [
        {"handle": "dev.min.inactive" + W, "role": "worker",
         "first_name": "DevMin", "last_name": "Inactive", "active": False}],
    "sa_handle": MINIMAL_MONEY["sa_handle"],
    "manager_handle": MINIMAL_MONEY["manager_handle"],
    "masters": {**MINIMAL_MONEY["masters"], "cloth_type": "DEV-INA-COTTON",
                "cloth_color": "DEV-INA-RED", "storage": "DEV-INA-RACK"},
    "rolls": {"cloth_type": "DEV-INA-COTTON", "storage": "DEV-INA-RACK", "rolls": []},
    "post": "inactive_user",
}

E_REOPEN = _world("edge-reopen-guard", "RPG")
E_REOPEN["post"] = "reopen_guard"

E_COMPOSITE = {
    "slug": "edge-composite-roles",
    "dev_prefixes": ("dev.", "DEV-", "dev-"),
    "cast": MINIMAL_MONEY["cast"] + [
        {"handle": "dev.min.acct.mgr" + W, "role": "manager",
         "first_name": "DevMin", "last_name": "Composite",
         "extra_roles": ["accountant"]}],
    "sa_handle": MINIMAL_MONEY["sa_handle"],
    "manager_handle": MINIMAL_MONEY["manager_handle"],
    "masters": {**MINIMAL_MONEY["masters"], "cloth_type": "DEV-CMP-COTTON",
                "cloth_color": "DEV-CMP-RED", "storage": "DEV-CMP-RACK"},
    "rolls": {"cloth_type": "DEV-CMP-COTTON", "storage": "DEV-CMP-RACK", "rolls": []},
    "post": "composite_roles",
}

E_RERATE = _world("edge-rate-correction", "RRC")
E_RERATE.pop("settlement")   # correction happens PRE-settlement (S1.1 law)
E_RERATE["post"] = "rate_correction"

E_SUPERSEDE = _world("edge-settlement-supersession", "SUP")
E_SUPERSEDE["post"] = "settlement_supersession"


EXTRA_CONTENT = {c["slug"]: c for c in (
    DEMO, FACTORY, F_ALLOCATION, F_FNF, F_MACHINES, F_PATTERNS, F_STOREFRONT,
    F_TRACKING, F_BOD, F_MEE, F_RMX, E_OVERALLOC, E_DAMAGED, E_MONTHLY,
    E_INACTIVE, E_REOPEN, E_COMPOSITE, E_RERATE, E_SUPERSEDE,
)}


# ── post-steps: certified-service calls only; each idempotent (skip when the
#    end-state already holds) and each returns {"created","skipped",facts} ──

def _stitching_sr(adda, create=True):
    from production.services import adda_service
    WS = apps.get_model("production", "WorkflowStage")
    ws = WS.objects.get(product=adda.product, stage__code="dev-min-stitching")
    sr = adda_service.lane_stage_record(adda, ws, None, create=create)
    if create:
        from production.services.stage_rate_service import ensure_stage_role_rates
        ensure_stage_role_rates(sr)
    return sr


def post_allocation(ctx):
    from production.services import pool_service
    WSA = apps.get_model("production", "WorkerStageAllocation")
    adda, worker = ctx["adda"], ctx["actors"]["dev.min.worker" + W]
    sr = _stitching_sr(adda)
    if WSA.objects.filter(stage_record=sr, voided_at__isnull=True).exists():
        return {"created": 0, "skipped": 1}
    pool_service.allocate(sr, worker, qty=Decimal("30"), actor=ctx["mgr"])
    return {"created": 1, "skipped": 0,
            "available_after": str(pool_service.available(sr))}


def post_overallocation(ctx):
    from production.services import pool_service
    adda, worker = ctx["adda"], ctx["actors"]["dev.min.worker" + W]
    sr = _stitching_sr(adda)
    WSA = apps.get_model("production", "WorkerStageAllocation")
    created = 0
    if not WSA.objects.filter(stage_record=sr, voided_at__isnull=True).exists():
        pool_service.allocate(sr, worker, qty=Decimal("50"), actor=ctx["mgr"])
        created = 1
    # THE M-6-class evidence: the always-on refusal fires beyond the pool.
    try:
        pool_service.allocate(sr, worker, qty=Decimal("999"), actor=ctx["mgr"])
        raise AssertionError("over-allocation was NOT refused")
    except ValidationError as e:
        refusal = str(e)
    return {"created": created, "skipped": 1 - created, "refusal": refusal[:160]}


def post_fnf(ctx):
    from expense.services import fnf_service
    worker = ctx["actors"]["dev.min.leaver" + W]
    worker.refresh_from_db()
    if not worker.is_active:
        return {"created": 0, "skipped": 1}
    receipt = fnf_service.fnf_execute(worker, user=ctx["sa"])
    worker.refresh_from_db()
    assert not worker.is_active, "FnF must deactivate the leaver"
    return {"created": 1, "skipped": 0, "receipt_keys": sorted(receipt)[:6]}


def post_machine_assign(ctx):
    from machines.services import machine_service
    Machine = apps.get_model("machines", "Machine")
    MA = apps.get_model("machines", "MachineAssignment")
    m = Machine.objects.get(code="DEV-MCH-M1")
    if MA.objects.filter(machine=m, end_at__isnull=True).exists():
        return {"created": 0, "skipped": 1}
    machine_service.assign(machine=m, worker=ctx["actors"]["dev.min.worker" + W],
                           user=ctx["mgr"])
    return {"created": 1, "skipped": 0}


def post_assert_barcodes(ctx):
    BB = apps.get_model("tracking", "BarcodeBatch")
    n = BB.objects.filter(adda=ctx["adda"]).count()
    assert n > 0, "inline barcode generation produced no batches"
    return {"created": 0, "skipped": 1, "barcode_batches": n}


def post_damaged_rolls(ctx):
    from raw_materials.services import roll_service
    ClothRoll = apps.get_model("raw_materials", "ClothRoll")
    rolls = list(ClothRoll.objects.filter(
        cloth_type__name="DEV-DMG-COTTON").order_by("pk"))
    target = rolls[-1]
    H = apps.get_model("tracking", "ClothRollHistory")
    # restore audits as STATUS_CHANGED + the reason in `note` — probe the note
    if H.objects.filter(roll=target, note__icontains="restore case").exists():
        return {"created": 0, "skipped": 1}
    roll_service.mark_roll_damaged(ctx["mgr"], roll=target, reason="DEV edge world: damage case")
    target.refresh_from_db()
    assert target.status == "damaged"
    roll_service.restore_damaged_roll(ctx["mgr"], roll=target, reason="DEV edge world: restore case")
    target.refresh_from_db()
    return {"created": 1, "skipped": 0, "final_status": target.status}


def post_monthly_worker(ctx):
    from expense.services import payroll_service
    worker = ctx["actors"]["dev.min.monthly" + W]
    WP = apps.get_model("expense", "WorkerProfile")
    if WP.objects.filter(user=worker, pay_basis=WP.PayBasis.MONTHLY).exists():
        return {"created": 0, "skipped": 1}
    payroll_service.set_pay_basis(worker, WP.PayBasis.MONTHLY,
                                  actor=ctx["sa"], confirmed=True)
    return {"created": 1, "skipped": 0}


def post_inactive_user(ctx):
    u = ctx["actors"]["dev.min.inactive" + W]
    u.refresh_from_db()
    assert not u.is_active, "edge cast member must be inactive"
    return {"created": 0, "skipped": 1}


def post_reopen_guard(ctx):
    from production.stages.layering import service as layering_service
    try:
        layering_service.reopen_layering(adda=ctx["adda"], user=ctx["sa"])
        raise AssertionError("reopen was NOT refused despite downstream truth")
    except ValidationError as e:
        return {"created": 0, "skipped": 1, "refusal": str(e)[:200]}


def post_composite_roles(ctx):
    from accounts.services import permission_service
    u = ctx["actors"]["dev.min.acct.mgr" + W]
    assert permission_service.user_has_role(u, ["manager"])
    assert permission_service.user_has_role(u, ["accountant"])
    return {"created": 0, "skipped": 1}


def post_rate_correction(ctx):
    from production.services.stage_rate_service import rerate_stage_role
    Audit = apps.get_model("production", "RateCorrectionAudit")
    Role = apps.get_model("accounts", "Role")
    sr = _stitching_sr(ctx["adda"], create=False)
    role = Role.objects.get(code="worker")
    if Audit.objects.filter(stage_record=sr).exists():
        return {"created": 0, "skipped": 1}
    rerate_stage_role(sr, role, Decimal("4"), actor=ctx["sa"],
                      reason="DEV edge world: S1.1 correction case")
    ASRR = apps.get_model("production", "AddaStageRoleRate")
    assert ASRR.objects.get(stage_record=sr, role=role).rate == Decimal("4")
    return {"created": 1, "skipped": 0}


def post_settlement_supersession(ctx):
    from expense.services import adda_settlement_service
    AS_ = apps.get_model("expense", "AddaSettlement")
    if AS_.objects.filter(adda=ctx["adda"], supersedes__isnull=False,
                          status="finalized").exists():
        return {"created": 0, "skipped": 1}
    original = AS_.objects.get(adda=ctx["adda"], status="finalized")
    # single writer returns (reversed_settlement, successor_draft)
    _, successor = adda_settlement_service.reverse_adda_settlement(
        settlement=original, user=ctx["sa"], supersede=True,
        notes="DEV edge world: supersession chain")
    adda_settlement_service.finalize_adda_settlement(settlement=successor, user=ctx["mgr"])
    original.refresh_from_db()
    assert original.status in ("superseded", "reversed")
    return {"created": 1, "skipped": 0, "chain": f"{original.reference}→{successor.reference}"}


def post_bod_board(ctx):
    """feature-bod evidence: the dashboard's owning services all run on this
    world and report the seeded facts. Idempotent: the DEV expense row is
    created once (note-probed), later runs converge to skip."""
    from django.utils import timezone as djtz
    from expense.services import expense_service
    from production.services.operations_digest import operations_digest
    FE = apps.get_model("expense", "FactoryExpense")
    today = djtz.localtime().date()
    created = 0
    if not FE.objects.filter(notes__startswith="DEV feature-bod",
                             voided_at__isnull=True).exists():
        expense_service.record_expense(
            category="rent", amount=Decimal("100.00"), expense_date=today,
            actor=ctx["mgr"], notes="DEV feature-bod: board expense fact")
        created = 1
    digest = operations_digest()
    month = expense_service.monthly_totals(today.year, today.month)
    assert month["total"] >= Decimal("100.00"), "F1 tile fact missing"
    assert digest["pending_payable"] > 0, "settled world must show Earned-not-paid"
    return {"created": created, "skipped": 1 - created,
            "month_total": str(month["total"]),
            "pending_payable": str(digest["pending_payable"])}


def post_monthly_expense_engine(ctx):
    """feature-monthly-expense: templates + a generated period + a voided
    example — every write through the census-ADDENDUM-1 service functions.
    Converging: each sub-step probes its own end-state first."""
    from datetime import date as _date
    from decimal import Decimal as _D
    from expense.models import ExpenseGenerationRecord, ExpenseTemplate
    from expense.services.expense_service import (
        create_expense_template, generate_monthly_expenses, void_expense)

    sa, mgr = ctx["sa"], ctx["mgr"]
    worker = ctx["actors"]["dev.min.worker" + W]
    created = 0
    if not ExpenseTemplate.objects.filter(label="DEV-MEE Rent").exists():
        create_expense_template(label="DEV-MEE Rent", category="rent",
                                amount=_D("100.00"),
                                start_date=_date(2026, 7, 1), actor=sa)
        created += 1
    if not ExpenseTemplate.objects.filter(label="DEV-MEE Salary").exists():
        create_expense_template(label="DEV-MEE Salary", category="salary",
                                amount=_D("9000.00"), worker=worker,
                                start_date=_date(2026, 7, 1), actor=sa)
        created += 1
    receipt = generate_monthly_expenses(2026, 7, actor=mgr, confirm=True)
    created += len(receipt["created"])
    # the voided example: the rent cover of 2026-07, voided once (probe first)
    rent_cover = (ExpenseGenerationRecord.objects
                  .select_related("expense")
                  .get(template__label="DEV-MEE Rent", period_key="2026-07",
                       superseded_at__isnull=True))
    if rent_cover.expense.voided_at is None:
        void_expense(rent_cover.expense, actor=sa,
                     reason="DEV feature world: the voided example")
        created += 1
    covers = ExpenseGenerationRecord.objects.filter(
        template__label__startswith="DEV-MEE", period_key="2026-07",
        superseded_at__isnull=True).count()
    assert covers >= 1, "engine world produced no coverage"
    return {"created": created, "skipped": 1 if created == 0 else 0,
            "covers_2026_07": covers,
            "generated_now": len(receipt["created"]),
            "gen_skips": len(receipt["skipped"])}


def post_rm_expense(ctx):
    """feature-rm-expense (A4): the Phase-17 one-rupee-once fixtures — every
    step a certified writer; converging (each sub-step probes its end-state).
    Leaves: roll#1 CONSUMED+unpriced (the banner world) · roll#2 PRICED but
    unconsumed (purchases fixture) · roll#3 DAMAGED (purchases-only fixture) ·
    the journey's 2.5kg leftover CONSUMED into a second adda (the chain)."""
    from decimal import Decimal as _D
    from production.models import RemainingClothOfClothRoll
    from production.services import adda_service
    from raw_materials.models import ClothRoll
    from raw_materials.services.roll_service import (
        consume_leftover, mark_roll_damaged, update_roll_details)

    sa, mgr = ctx["sa"], ctx["mgr"]
    created = 0
    rolls = list(ClothRoll.objects.filter(
        cloth_type__name="DEV-RME-COTTON").order_by("pk"))
    # Fixtures selected by STATE (the journey consumes ONE roll of the three;
    # which pk it takes is the journey's business — probe, don't index).
    priced = next((r for r in rolls if r.cost_per_kg is not None), None)
    if priced is None:
        priced = next(r for r in rolls
                      if r.status == ClothRoll.Status.NOT_USED)
        update_roll_details(sa, roll=priced, cost_per_kg=_D("100.00"),
                            supplier="DEV-RME Mills")
        created += 1
    damaged = next((r for r in rolls
                    if r.status == ClothRoll.Status.DAMAGED), None)
    if damaged is None:
        damaged = next(r for r in rolls
                       if r.status == ClothRoll.Status.NOT_USED
                       and r.pk != priced.pk)
        mark_roll_damaged(mgr, roll=damaged,
                          reason="DEV rm-expense world: damaged fixture")
        created += 1
    lo = (RemainingClothOfClothRoll.objects
          .filter(source_adda=ctx["adda"]).order_by("pk").first())
    assert lo is not None, "the journey must have weighed a leftover"
    if not lo.is_consumed:
        target = adda_service.create_adda(mgr, product=ctx["adda"].product)
        consume_leftover(mgr, leftover=lo, adda=target,
                         notes="DEV rm-expense world: the reuse chain")
        created += 2
    lo.refresh_from_db()
    return {"created": created, "skipped": 1 if created == 0 else 0,
            "priced_roll": priced.roll_id, "damaged_roll": damaged.roll_id,
            "leftover_consumed": lo.is_consumed,
            "chain_target": lo.consumed_in_adda.code if lo.consumed_in_adda else None}


EXTRA_STEPS = {
    "allocation": post_allocation,
    "bod_board": post_bod_board,
    "monthly_expense_engine": post_monthly_expense_engine,
    "rm_expense": post_rm_expense,
    "overallocation": post_overallocation,
    "fnf": post_fnf,
    "machine_assign": post_machine_assign,
    "assert_barcodes": post_assert_barcodes,
    "damaged_rolls": post_damaged_rolls,
    "monthly_worker": post_monthly_worker,
    "inactive_user": post_inactive_user,
    "reopen_guard": post_reopen_guard,
    "composite_roles": post_composite_roles,
    "rate_correction": post_rate_correction,
    "settlement_supersession": post_settlement_supersession,
}
