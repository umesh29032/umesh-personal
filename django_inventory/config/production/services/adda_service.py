"""Adda service — batch banane + stage advance karne ka logic.

YEH FILE KYU HAI?
─────────────────
Adda creation aur stage transition yahan se hote hain.
Critical: Per-product counter atomically badhna chahiye — warna 2 threads collide kar sakti hain.

Race-safe kaise?
────────────────
`SELECT … FOR UPDATE` Postgres ka row-level lock. Jab tak ye transaction commit nahi hoti,
doosri transaction usi Product row pe wait karti hai. Counter increment kabhi double-count nahi.

Phase 4 (2026-05-20):
────────────────────
`create_adda` ab Layering stage_record bhi auto-create karta hai aur workers M2M
ko `cutting_master` + `cutting_master_helper` skill wale saare users se populate
karta hai. Agar koi skilled user system mein nahi to creation reject.
Reason: helpers ko Adda ban-te hi visible hona chahiye + system stuck-Addas se
bachna chahiye (spec D1 + D5 + D6).
"""
from __future__ import annotations

import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.skills import SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER
from accounts.services import PRODUCTION_ROLES, user_has_role
from production.constants import STAGE_LAYERING
from production.models import Adda, AddaStageRecord, Product

logger = logging.getLogger(__name__)


def _ensure_can_manage(user):
    """Production roles ka gate — service-side authorization check."""
    if not user_has_role(user, PRODUCTION_ROLES):
        raise PermissionDenied("requires production role")


def _skilled_user_pks() -> list[int]:
    """All active users with cutting_master or cutting_master_helper skill.

    Returns plain pk list to keep the SELECT FOR UPDATE transaction small —
    full User rows fetched later only by the M2M setter.
    """
    from accounts.models import User
    return list(
        User.objects.filter(
            is_active=True,
            skills__name__in=[SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER],
        ).distinct().values_list('pk', flat=True)
    )


@transaction.atomic
def create_adda(user, *, product: Product) -> Adda:
    """Naye Adda ka code allocate kar ke row create karta hai + Layering kick off.

    Per-product counter atomic kaise hai?
        Product row pe `select_for_update()` lagaate hain — doosri concurrent
        create_adda(SAME_PRODUCT) call lock release hone tak ruk jaati hai.
        Counter increment + Adda insert dono ek hi transaction mein → no collision.

    Phase 4 changes:
        • Skilled-user pool fetch (cutting_master + cutting_master_helper).
        • Pool empty → ValidationError ("no skilled users") — Adda nahi banta.
        • Adda create ke baad Layering ka AddaStageRecord auto-create with
          started_at=now + workers M2M = skilled-user pool snapshot.
        • Helpers ko ye Adda dashboard pe turant dikhega (spec D1).

    Resulting code: {Product.code}-{counter:03d}  e.g. 'T-SHIRT-001'.

    Side effects:
        • UPDATE Product.adda_counter (locked row, atomic increment).
        • INSERT Adda (new batch row).
        • INSERT AddaStageRecord + set workers M2M — only when first stage is Layering.
        • tracking.services.log_adda → INSERT AddaHistory (CREATED, + WORKERS_ASSIGNED if Layering).
    """
    _ensure_can_manage(user)
    if not product.is_active:
        raise ValidationError(f"Product '{product.code}' is archived")

    skilled_pks = _skilled_user_pks()
    if not skilled_pks:
        # Spec D6 — block creation; helpers wouldn't have anyone to execute it.
        raise ValidationError(
            "No cutting_master or cutting_master_helper users exist. "
            "Add at least one user with that skill before creating an Adda."
        )

    # Yahi line race-safety deti hai — Product row lock ho jaati hai
    prod = Product.objects.select_for_update().get(pk=product.pk)
    prod.adda_counter += 1
    prod.save(update_fields=['adda_counter'])   # sirf counter column UPDATE

    # First stage pick — Product ka workflow_stages reverse FK queryset (order ASC)
    first_stage = prod.workflow_stages.order_by('order').first()
    if first_stage is None:
        # Defensive — seed migration ye guarantee karti hai
        raise ValidationError(f"Product '{prod.code}' has no workflow stages defined")

    adda = Adda.objects.create(
        code=f"{prod.code}-{prod.adda_counter:03d}",   # 3-digit zero padded
        product=prod,
        current_stage=first_stage,
        created_by=user,
    )

    # Auto-create stage_record + tag skilled workers if first_stage is Layering.
    # Future stages (cutting, etc.) ke liye legacy "manager-driven start" flow rehta hai.
    if first_stage.stage_type == STAGE_LAYERING:
        sr = AddaStageRecord.objects.create(
            adda=adda, workflow_stage=first_stage,
            started_at=timezone.now(),
        )
        sr.workers.set(skilled_pks)   # M2M snapshot — manager refine kar sakta

    # tracking app ka lazy import — production pe ulta depend karta hai
    from tracking.services import log_adda
    from tracking.models import AddaHistory
    log_adda(adda, AddaHistory.ChangeType.CREATED, user)
    if first_stage.stage_type == STAGE_LAYERING:
        log_adda(adda, AddaHistory.ChangeType.WORKERS_ASSIGNED, user,
                 stage_record=sr, metadata={'worker_ids': list(skilled_pks)})
    logger.info(
        "adda.create code=%s adda_id=%s product=%s first_stage=%s worker_count=%d",
        adda.code, adda.pk, prod.code, first_stage.stage_type, len(skilled_pks),
    )
    return adda


@transaction.atomic
def advance_to_next_stage(adda: Adda, user, *, enforce_worker_credit: bool = True) -> Adda:
    """Adda ko next WorkflowStage pe move karta hai. Last stage ke baad COMPLETED.

    enforce_worker_credit: PAY-2 (M2.7c). When True (default), a PAYABLE stage being
    left (WorkflowStage.credits_workers + self-paid) must have >=1 non-voided worker
    allocation or completion is blocked. Legacy paths pass False to opt out
    (compatibility-only flow, per the payroll architecture decision).

    Stage services (complete_layering / complete_cutting, in layering_service /
    cutting_service) iss helper ko call karte hain typed record save hone ke baad.

    Last-stage handling:
        nxt=None    → Adda completed, current_stage=None set, completed_at stamp
        nxt set hai → current_stage update

    Side effects:
        • production.services.cost_service.freeze_stage_cost → writes frozen
          processing_cost + cost_*_snapshot on the leaving AddaStageRecord (MONEY).
        • UPDATE Adda (current_stage; + status/completed_at when last stage).
        • tracking.services.log_adda → INSERT AddaHistory (COST_FROZEN if leaving record,
          STAGE_ADVANCED, + COMPLETED on final stage).
    """
    cur = adda.current_stage
    if cur is None:
        raise ValidationError("Adda has no current stage")

    # FREEZE manufacturing cost of the stage being LEFT, before advancing.
    # This is the single choke point every complete_* funnels through
    # (price-at-time-of-order). The caller has already stamped completed_at and
    # finalized the typed record (pieces_cut/lay_count/total_barcodes) inside
    # the same atomic block, so the quantity is authoritative here.
    from production.services.cost_service import freeze_stage_cost
    leaving_sr = AddaStageRecord.objects.filter(adda=adda, workflow_stage=cur).first()
    # PAY-2 (M2.7c): block completing a payable stage with zero worker allocations.
    # Runs BEFORE the freeze so nothing is mutated on rejection. No-op for
    # non-payable stages; legacy callers opt out via enforce_worker_credit=False.
    if enforce_worker_credit and leaving_sr is not None:
        from production.stages.base import ensure_worker_credit
        ensure_worker_credit(leaving_sr)
    if leaving_sr is not None:
        freeze_stage_cost(leaving_sr, user=user)

    # Next stage = order > current ke saare stages mein se sabse pehla
    nxt = adda.product.workflow_stages.filter(order__gt=cur.order).order_by('order').first()
    if nxt is None:
        # Aakhri stage thi — Adda complete mark
        adda.status = Adda.Status.COMPLETED
        adda.completed_at = timezone.now()
        adda.current_stage = None
        adda.save(update_fields=['status', 'completed_at', 'current_stage'])
    else:
        adda.current_stage = nxt
        adda.save(update_fields=['current_stage'])

    # History entry — transition record + agar completed to extra event bhi
    from tracking.services import log_adda
    from tracking.models import AddaHistory
    # Audit the freeze (logged even when cost is NULL — 'unpriced completion' signal).
    if leaving_sr is not None:
        log_adda(
            adda, AddaHistory.ChangeType.COST_FROZEN, user, stage_from=cur,
            stage_record=leaving_sr,
            metadata={
                'method': leaving_sr.cost_method_snapshot or None,
                'rate': str(leaving_sr.cost_rate_snapshot) if leaving_sr.cost_rate_snapshot is not None else None,
                'qty': str(leaving_sr.cost_quantity_snapshot) if leaving_sr.cost_quantity_snapshot is not None else None,
                'cost': str(leaving_sr.processing_cost) if leaving_sr.processing_cost is not None else None,
            },
        )
    log_adda(adda, AddaHistory.ChangeType.STAGE_ADVANCED, user, stage_from=cur, stage_to=nxt)
    if nxt is None:
        log_adda(adda, AddaHistory.ChangeType.COMPLETED, user)
    logger.info(
        "adda.advance code=%s adda_id=%s stage_from=%s stage_to=%s frozen_cost=%s status=%s",
        adda.code, adda.pk, cur.stage_type, (nxt.stage_type if nxt is not None else None),
        (str(leaving_sr.processing_cost) if leaving_sr is not None else None),
        adda.status,
    )
    return adda
