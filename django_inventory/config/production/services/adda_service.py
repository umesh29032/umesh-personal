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

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.skills import SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER
from inventory.services import PRODUCTION_ROLES, user_has_role
from production.models import Adda, AddaStageRecord, Product, WorkflowStage


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
    if first_stage.stage_type == WorkflowStage.StageType.LAYERING:
        sr = AddaStageRecord.objects.create(
            adda=adda, workflow_stage=first_stage,
            started_at=timezone.now(),
        )
        sr.workers.set(skilled_pks)   # M2M snapshot — manager refine kar sakta

    # tracking app ka lazy import — production pe ulta depend karta hai
    from tracking.services import log_adda
    from tracking.models import AddaHistory
    log_adda(adda, AddaHistory.ChangeType.CREATED, user)
    return adda


@transaction.atomic
def advance_to_next_stage(adda: Adda, user) -> Adda:
    """Adda ko next WorkflowStage pe move karta hai. Last stage ke baad COMPLETED.

    stage_service.complete_layering / complete_cutting iss helper ko call karte hain
    typed record save hone ke baad.

    Last-stage handling:
        nxt=None    → Adda completed, current_stage=None set, completed_at stamp
        nxt set hai → current_stage update
    """
    cur = adda.current_stage
    if cur is None:
        raise ValidationError("Adda has no current stage")

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
    log_adda(adda, AddaHistory.ChangeType.STAGE_ADVANCED, user, stage_from=cur, stage_to=nxt)
    if nxt is None:
        log_adda(adda, AddaHistory.ChangeType.COMPLETED, user)
    return adda
