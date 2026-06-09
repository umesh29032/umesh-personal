"""Barcode Generation stage service — Stage 4 of production flow.

YEH FILE KYU HAI?
─────────────────
PR-C 2026-05-29 (BARCODE_STAGE_PLAN.md): barcode generation ab apna alag
stage hai (cutting se extracted). Per-product workflow flexibility: kuch
products yeh stage skip karte hain (back-compat in cutting_service).

FLOW:
  Cutting complete       → AddaProductSizeColorPieceBreakdown rows freeze
  Barcode Gen start      → manager workers assign karte hain
  Barcode Gen generate   → BarcodeBatch rows from breakdown (one-shot atomic)
  Barcode Gen complete   → count match validate + advance to next stage
  Barcode Gen reopen     → mgmt; refuse if any scanned OR exported

PERMISSIONS (mirror cutting):
  • start_barcode_generation     → MANAGEMENT_ROLES (assign workers)
  • generate_barcodes            → cutting_master OR helper (mgmt bypass)
  • complete_barcode_generation  → cutting_master_helper OR super_admin
  • reopen_barcode_generation    → MANAGEMENT_ROLES

ONE-SHOT GUARANTEE:
  Barcode batches ke liye DB-level constraint (BarcodeBatch.adda unique
  range) ensure karta. Re-generate without reopen = IntegrityError.

DOWNSTREAM-SAFE REOPEN:
  • Refuse if any BatchBarcode scanned (lazy-create on scan)
  • Refuse if BarcodeExportBatch exists (vendor printing)
"""
from __future__ import annotations

import logging
from typing import Iterable

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.skills import (
    SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER, user_has_skill,
)
from accounts.services import MANAGEMENT_ROLES, ROLE_SUPER_ADMIN, user_has_role
from production.constants import STAGE_BARCODE_GENERATION, STAGE_CUTTING
from production.models import (
    Adda, AddaProductSizeColorPieceBreakdown, AddaStageRecord,
    BarcodeGenerationRecord, CuttingRecord, WorkflowStage,
)
from production.services.adda_service import advance_to_next_stage
from production.services._shared import reopen_stage_record

# Module logger — debug multi-table / cross-app barcode stage transitions.
logger = logging.getLogger(__name__)


# ── Auth gates ─────────────────────────────────────────────────────────────

def _ensure_barcode_skill(user):
    """Generate barcodes — master or helper skill (mgmt bypass)."""
    if user_has_role(user, MANAGEMENT_ROLES):
        return
    if not user_has_skill(user, [SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER]):
        raise PermissionDenied(
            "requires cutting_master or cutting_master_helper skill"
        )


def _ensure_can_complete_barcode(user):
    """Complete + advance — helper skill OR super_admin (mirrors cutting)."""
    if user_has_role(user, {ROLE_SUPER_ADMIN}):
        return
    if not user_has_skill(user, SKILL_CUTTING_MASTER_HELPER):
        raise PermissionDenied(
            "only cutting_master_helper can complete the barcode_generation stage"
        )


# ── Stage discovery + lazy create ──────────────────────────────────────────

def _barcode_workflow_stage(adda: Adda) -> WorkflowStage | None:
    """Iss Adda ke Product ka barcode_generation WorkflowStage row."""
    return adda.product.workflow_stages.filter(
        stage__code=STAGE_BARCODE_GENERATION,
    ).first()


def _cutting_record_for_adda(adda: Adda) -> CuttingRecord | None:
    """Iss Adda ka completed CuttingRecord (must exist before bg stage)."""
    cutting_sr = AddaStageRecord.objects.filter(
        adda=adda, workflow_stage__stage__code=STAGE_CUTTING,
    ).first()
    if cutting_sr is None:
        return None
    return getattr(cutting_sr, 'cutting', None)


def get_or_create_barcode_stage_record(adda: Adda, user) -> AddaStageRecord:
    """Lazy-create AddaStageRecord for barcode_generation stage.

    Pre-conditions:
      • Product workflow mein barcode_generation hai
      • Adda abhi iss stage pe ho (current_stage == bg_wf)
      • Cutting record exists (upstream)
    """
    wf = _barcode_workflow_stage(adda)
    if wf is None:
        raise ValidationError(
            "This product does not include the barcode_generation stage."
        )
    if adda.current_stage_id != wf.id:
        raise ValidationError("Adda is not currently at the barcode_generation stage.")
    sr, created = AddaStageRecord.objects.get_or_create(
        adda=adda, workflow_stage=wf,
        defaults={'started_at': timezone.now()},
    )
    if created and not sr.started_at:
        sr.started_at = timezone.now()
        sr.save(update_fields=['started_at'])
    return sr


def _get_or_create_record(sr: AddaStageRecord) -> BarcodeGenerationRecord:
    """OneToOne BarcodeGenerationRecord lazy-create."""
    rec, _ = BarcodeGenerationRecord.objects.get_or_create(stage_record=sr)
    return rec


# ── Read-only snapshot for dashboards ──────────────────────────────────────

def preview_barcode_counts(adda: Adda) -> dict:
    """Dashboard preview — kitne barcodes generate honge, breakdown by (size, color).

    Returns:
      {
        'rows': [{'size': str, 'color': str, 'count': int}, ...],
        'total': int,
        'already_generated': bool,
      }
    """
    cr = _cutting_record_for_adda(adda)
    if cr is None:
        return {'rows': [], 'total': 0, 'already_generated': False}

    rows = []
    total = 0
    for r in (
        AddaProductSizeColorPieceBreakdown.objects
        .filter(cutting_record=cr)
        .select_related('size', 'color')
        .order_by('size__display_order', 'size__code', 'color__name')
    ):
        rows.append({
            'size': r.size.label if r.size else '—',
            'color': r.color.name if r.color else '—',
            'count': r.verified_piece_count,
        })
        total += r.verified_piece_count

    from tracking.models import BarcodeBatch
    already_generated = BarcodeBatch.objects.filter(adda=adda).exists()

    return {'rows': rows, 'total': total, 'already_generated': already_generated}


def get_barcode_snapshot(adda: Adda) -> dict:
    """Embedded panel snapshot — mirror of get_layering_snapshot shape."""
    wf = _barcode_workflow_stage(adda)
    if wf is None:
        return {'state': 'absent'}
    sr = AddaStageRecord.objects.filter(adda=adda, workflow_stage=wf).first()
    if sr is None:
        return {'state': 'not_started', 'workflow_stage': wf}
    record = getattr(sr, 'barcode_generation', None)

    from tracking.models import BarcodeBatch
    batches = list(BarcodeBatch.objects.filter(adda=adda).order_by('start_seq'))
    total_in_batches = sum(b.total_pieces for b in batches)

    return {
        'state': 'completed' if sr.completed_at else 'in_progress',
        'workflow_stage': wf,
        'stage_record': sr,
        'record': record,
        'batches': batches,
        'total_in_batches': total_in_batches,
        'started_at': sr.started_at,
        'completed_at': sr.completed_at,
        'completed_by': sr.completed_by,
    }


# ── Mutating actions ───────────────────────────────────────────────────────

@transaction.atomic
def start_barcode_generation(
    *, adda: Adda, worker_ids: Iterable[int], user,
) -> AddaStageRecord:
    """Mgmt assigns workers → stage formally started.

    Side effects:
      • AddaStageRecord row get_or_create + started_at set
      • AddaStageRecord.workers M2M set
      • BarcodeGenerationRecord row lazy-create (OneToOne)
      • tracking.services.log_adda → AddaHistory (WORKERS_ASSIGNED)
    """
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied(
            "only management can start the barcode_generation stage"
        )
    sr = get_or_create_barcode_stage_record(adda, user)
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed.")
    sr.workers.set(list(worker_ids))
    if not sr.started_at:
        sr.started_at = timezone.now()
        sr.save(update_fields=['started_at'])
    _get_or_create_record(sr)
    from tracking.services import log_adda
    from tracking.models import AddaHistory
    log_adda(adda, AddaHistory.ChangeType.WORKERS_ASSIGNED, user,
             stage_record=sr, metadata={'worker_ids': list(worker_ids)})
    worker_id_list = list(worker_ids)
    logger.info(
        "barcode.start adda=%s sr_id=%s worker_count=%s worker_ids=%s user=%s",
        adda.code, sr.id, len(worker_id_list), worker_id_list, getattr(user, 'id', None),
    )
    return sr


@transaction.atomic
def generate_barcodes(*, adda: Adda, user) -> BarcodeGenerationRecord:
    """Read breakdown rows → bulk_create BarcodeBatch rows.

    One-shot: dobara call IntegrityError (BarcodeBatch already exists).
    Use reopen_barcode_generation to re-run after correction.

    Updates BarcodeGenerationRecord.total_barcodes + generated_at.

    Side effects:
      • tracking.services.generate_from_breakdown → bulk_create BarcodeBatch rows (cross-app)
      • BarcodeGenerationRecord.total_barcodes + generated_at updated
      • tracking.services.log_adda → AddaHistory (BARCODES_GENERATED)
    """
    _ensure_barcode_skill(user)
    wf = _barcode_workflow_stage(adda)
    if wf is None:
        raise ValidationError(
            "This product does not include the barcode_generation stage."
        )
    if adda.current_stage_id != wf.id:
        raise ValidationError("Adda is not at the barcode_generation stage.")
    try:
        sr = AddaStageRecord.objects.get(adda=adda, workflow_stage=wf)
    except AddaStageRecord.DoesNotExist:
        raise ValidationError("Stage not started — assign workers first.")
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed.")

    rec = _get_or_create_record(sr)
    if rec.generated_at is not None:
        raise ValidationError("Barcodes already generated for this Adda.")

    from tracking.services import generate_from_breakdown
    total = generate_from_breakdown(rec)

    rec.total_barcodes = total
    rec.generated_at = timezone.now()
    rec.save(update_fields=['total_barcodes', 'generated_at', 'updated_at'])

    from tracking.services import log_adda
    from tracking.models import AddaHistory
    log_adda(adda, AddaHistory.ChangeType.BARCODES_GENERATED, user,
             stage_record=sr, metadata={'total_barcodes': total})
    logger.info(
        "barcode.generate adda=%s sr_id=%s rec_id=%s total_barcodes=%s user=%s",
        adda.code, sr.id, rec.id, total, getattr(user, 'id', None),
    )
    return rec


@transaction.atomic
def complete_barcode_generation(*, adda: Adda, user) -> BarcodeGenerationRecord:
    """Validate count match + finalize + advance.

    Validation:
      1. Stage record + barcode_generation record exist
      2. generated_at set (generate_barcodes ran successfully)
      3. SUM(BarcodeBatch.total_pieces) == SUM(breakdown.verified_piece_count)
         AND == BarcodeGenerationRecord.total_barcodes

    Refuses on mismatch — operator must reopen + regenerate.

    Side effects:
      • AddaStageRecord.completed_at + completed_by set
      • production.services.adda_service.advance_to_next_stage (advances Adda;
        freezes stage cost + writes AddaHistory cross-stage)
    """
    _ensure_can_complete_barcode(user)

    wf = _barcode_workflow_stage(adda)
    if wf is None:
        raise ValidationError(
            "This product does not include the barcode_generation stage."
        )
    if adda.current_stage_id != wf.id:
        raise ValidationError("Adda is not at the barcode_generation stage.")

    try:
        # WF-4: lock the stage row so a concurrent completer blocks here and then
        # sees completed_at set below — prevents double-advance / double-freeze.
        sr = AddaStageRecord.objects.select_for_update().get(adda=adda, workflow_stage=wf)
    except AddaStageRecord.DoesNotExist:
        raise ValidationError("Stage record missing — generate barcodes first.")
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed.")
    rec = getattr(sr, 'barcode_generation', None)
    if rec is None or rec.generated_at is None:
        raise ValidationError("Generate barcodes before completing the stage.")

    # Count match validation
    from tracking.models import BarcodeBatch
    batch_total = sum(
        b.total_pieces for b in BarcodeBatch.objects.filter(adda=adda)
    )
    cr = _cutting_record_for_adda(adda)
    breakdown_total = sum(
        r.verified_piece_count for r in
        AddaProductSizeColorPieceBreakdown.objects.filter(cutting_record=cr)
    ) if cr else 0

    if batch_total != breakdown_total:
        raise ValidationError(
            f"Count mismatch: {batch_total} barcodes vs {breakdown_total} "
            f"verified pieces. Reopen stage to regenerate."
        )
    if batch_total != rec.total_barcodes:
        raise ValidationError(
            f"Internal counter drift: barcodes={batch_total}, denorm="
            f"{rec.total_barcodes}. Reopen and regenerate."
        )

    sr.completed_at = timezone.now()
    sr.completed_by = user
    sr.save(update_fields=['completed_at', 'completed_by', 'updated_at'])

    advance_to_next_stage(adda, user)
    logger.info(
        "barcode.complete adda=%s sr_id=%s batch_total=%s breakdown_total=%s "
        "from_stage=%s user=%s",
        adda.code, sr.id, batch_total, breakdown_total, wf.id, getattr(user, 'id', None),
    )
    return rec


@transaction.atomic
def reopen_barcode_generation(*, adda: Adda, user) -> AddaStageRecord:
    """Mgmt-only: completed barcode_generation stage ko unlock.

    Refusal conditions:
      • Any BatchBarcode scanned (last_scanned_at NOT NULL)
      • Any BarcodeExportBatch exists (vendor already exporting)

    On reopen:
      • Clear sr.completed_at + completed_by
      • Adda.current_stage → barcode_gen wf, status → IN_PROGRESS
      • Delete all BarcodeBatch rows (one-shot regeneration rule)
      • Reset BarcodeGenerationRecord (clear generated_at + total_barcodes)
      • AddaHistory.STAGE_REOPENED log

    Side effects:
      • BarcodeBatch rows deleted (cross-app tracking)
      • BarcodeGenerationRecord reset (total_barcodes=0, generated_at=None)
      • AddaStageRecord.completed_at + completed_by cleared
      • production.services.cost_service.clear_stage_cost (unfreeze stage cost)
      • Adda.current_stage / status / completed_at updated
      • tracking.services.log_adda → AddaHistory (STAGE_REOPENED)
    """
    def _guard(adda, sr, wf):
        # Refuse if any piece was scanned, or any export exists (vendor has labels).
        from tracking.models import BatchBarcode, BarcodeExportBatch
        if BatchBarcode.objects.filter(adda=adda).exists():
            raise ValidationError(
                "Cannot reopen — at least one barcode has been scanned in production."
            )
        if BarcodeExportBatch.objects.filter(adda=adda).exists():
            raise ValidationError(
                "Cannot reopen — barcode exports exist. Cancel exports first."
            )

    def _teardown(sr):
        # One-shot regeneration rule: drop all batches + reset the gen record so
        # re-complete regenerates from scratch.
        from tracking.models import BarcodeBatch
        BarcodeBatch.objects.filter(adda=sr.adda).delete()
        rec = getattr(sr, 'barcode_generation', None)
        if rec is not None:
            rec.total_barcodes = 0
            rec.generated_at = None
            rec.save(update_fields=['total_barcodes', 'generated_at', 'updated_at'])
        return []

    return reopen_stage_record(
        adda=adda, stage_code=STAGE_BARCODE_GENERATION, stage_label='Barcode generation',
        user=user, guard=_guard, teardown=_teardown,
    )
