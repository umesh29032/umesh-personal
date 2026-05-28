"""Cutting-pattern stage service.

Stage flow:
  1. Manager (or cutting master) clicks Start → AddaStageRecord row created
     with workers assigned. (Currently auto-creates on first save — see
     `_get_or_start_stage_record`.)
  2. Cutting master uploads video + N photos via the workspace form.
  3. Master clicks Complete → CuttingPatternRecord row persists with
     video file path; per-photo CuttingPatternPhoto rows linked. Advances to
     next stage (cutting, or whatever the product flow defines).

Storage:
  • Photos compressed to JPEG (quality 80) via Pillow on save. Resize down
    to max 2400px on the long edge.
  • Video stored as uploaded (no recompress — server-side ffmpeg deferred).
  • Both go through Django's storage abstraction so swapping to S3/MinIO
    later is a settings-level change (DEFAULT_FILE_STORAGE / STORAGES).

Permissions:
  • Start/Upload → cutting_master OR cutting_master_helper (+ management)
  • Complete     → cutting_master_helper (+ super_admin)
"""
from __future__ import annotations

import io
from typing import Iterable

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageOps

from accounts.skills import (
    SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER, user_has_skill,
)
from inventory.services import MANAGEMENT_ROLES, user_has_role
from production.constants import STAGE_CUTTING_PATTERN
from production.models import (
    Adda, AddaStageRecord, CuttingPatternPhoto, CuttingPatternRecord,
    WorkflowStage,
)
from production.services.adda_service import advance_to_next_stage


PHOTO_MAX_DIM = 2400
PHOTO_QUALITY = 80


def _ensure_pattern_skill(user):
    """cutting_master OR cutting_master_helper. Management bypass."""
    if user_has_role(user, MANAGEMENT_ROLES):
        return
    if not user_has_skill(user, [SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER]):
        raise PermissionDenied(
            "requires cutting_master or cutting_master_helper skill"
        )


def _ensure_can_complete_pattern(user):
    """Advancing past cutting_pattern requires helper skill (or super_admin)."""
    if user_has_role(user, {'super_admin'}):
        return
    if not user_has_skill(user, SKILL_CUTTING_MASTER_HELPER):
        raise PermissionDenied(
            "only cutting_master_helper can complete the cutting_pattern stage"
        )


def _pattern_workflow_stage(adda: Adda) -> WorkflowStage | None:
    return adda.product.workflow_stages.filter(stage__code=STAGE_CUTTING_PATTERN).first()


def get_or_create_pattern_stage_record(adda: Adda, user) -> AddaStageRecord:
    """Return the AddaStageRecord for the cutting_pattern stage, creating it
    on first touch. Pre-condition: adda.current_stage is the pattern stage.
    """
    wf = _pattern_workflow_stage(adda)
    if wf is None:
        raise ValidationError("This product does not include the cutting_pattern stage.")
    if adda.current_stage_id != wf.id:
        raise ValidationError("Adda is not currently at the cutting_pattern stage.")
    sr, created = AddaStageRecord.objects.get_or_create(
        adda=adda, workflow_stage=wf,
        defaults={'started_at': timezone.now()},
    )
    if created and not sr.started_at:
        sr.started_at = timezone.now()
        sr.save(update_fields=['started_at'])
    return sr


def _compress_image(uploaded) -> ContentFile:
    """Read uploaded image, downscale + recompress to JPEG. Returns ContentFile.

    Honors EXIF orientation (avoids sideways photos from phones).
    Falls back to original bytes if Pillow can't decode (e.g. unusual format).
    """
    try:
        img = Image.open(uploaded)
        img = ImageOps.exif_transpose(img)
        img = img.convert('RGB')
        img.thumbnail((PHOTO_MAX_DIM, PHOTO_MAX_DIM))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=PHOTO_QUALITY, optimize=True)
        buf.seek(0)
        # Strip any path components from filename; rename to .jpg for clarity.
        base = (getattr(uploaded, 'name', 'photo') or 'photo').rsplit('.', 1)[0]
        return ContentFile(buf.read(), name=f"{base}.jpg")
    except Exception:
        # Fallback: store as-is. Better than failing the upload entirely.
        uploaded.seek(0)
        return ContentFile(uploaded.read(), name=getattr(uploaded, 'name', 'photo'))


@transaction.atomic
def start_pattern_stage(*, adda: Adda, worker_ids: Iterable[int], user) -> AddaStageRecord:
    """Manager assigns workers + starts the stage."""
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("only management can start the cutting_pattern stage")
    sr = get_or_create_pattern_stage_record(adda, user)
    sr.workers.set(list(worker_ids))
    if not sr.started_at:
        sr.started_at = timezone.now()
        sr.save(update_fields=['started_at'])
    return sr


@transaction.atomic
def attach_photo(*, stage_record: AddaStageRecord, uploaded_image,
                 caption: str = '', user) -> CuttingPatternPhoto:
    """Compress + attach one photo to the stage. Lazily bootstraps a
    CuttingPatternRecord with no video if none exists yet — masters can post
    photos without a video, video without photos, or both."""
    _ensure_pattern_skill(user)
    if stage_record.completed_at is not None:
        raise ValidationError("Stage already completed — photos locked.")

    record = getattr(stage_record, 'cutting_pattern', None)
    if record is None:
        record = CuttingPatternRecord.objects.create(stage_record=stage_record)

    compressed = _compress_image(uploaded_image)
    return CuttingPatternPhoto.objects.create(
        record=record, image=compressed, caption=caption[:200], uploaded_by=user,
    )


@transaction.atomic
def save_pattern_record(*, adda: Adda, video_file, notes: str, user) -> CuttingPatternRecord:
    """Save or replace the video + notes on this Adda's pattern record.

    Idempotent — calling twice replaces the video file (old one orphaned on
    disk; cleanup deferred). Photos attached via attach_photo persist across
    replays. Either video_file or notes alone is fine — both optional.
    """
    _ensure_pattern_skill(user)
    sr = get_or_create_pattern_stage_record(adda, user)
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed.")

    record, _created = CuttingPatternRecord.objects.get_or_create(stage_record=sr)
    update_fields = ['updated_at']
    if video_file is not None:
        record.video = video_file
        update_fields.append('video')
    if notes is not None:
        record.notes = notes or ''
        update_fields.append('notes')
    record.save(update_fields=update_fields)
    return record


@transaction.atomic
def complete_pattern_stage(*, adda: Adda, user) -> CuttingPatternRecord:
    """Finalize the stage → advance to next.

    Requires: video uploaded AND >=1 photo. Helper-skill (or super_admin) gate.
    """
    _ensure_can_complete_pattern(user)

    wf = _pattern_workflow_stage(adda)
    if wf is None:
        raise ValidationError("Product does not include the cutting_pattern stage.")
    if adda.current_stage_id != wf.id:
        raise ValidationError("Adda is not at the cutting_pattern stage.")

    try:
        sr = AddaStageRecord.objects.get(adda=adda, workflow_stage=wf)
    except AddaStageRecord.DoesNotExist:
        raise ValidationError("Stage record missing — upload video + photos first.")
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed.")

    # Allow proceeding with EITHER video OR ≥1 photo — at least one required.
    record = getattr(sr, 'cutting_pattern', None)
    has_video = bool(record and record.video)
    has_photo = bool(record and record.photos.exists())
    if not (has_video or has_photo):
        raise ValidationError(
            "Upload at least one photo or a video of the pattern before completing."
        )

    sr.completed_at = timezone.now()
    sr.completed_by = user
    sr.save(update_fields=['completed_at', 'completed_by', 'updated_at'])

    advance_to_next_stage(adda, user)
    return record


def get_pattern_snapshot(adda: Adda) -> dict:
    """Lightweight snapshot — drives the embedded panel state without
    blocking imports. Mirrors get_layering_snapshot's shape."""
    wf = _pattern_workflow_stage(adda)
    if wf is None:
        return {'state': 'absent'}
    sr = AddaStageRecord.objects.filter(adda=adda, workflow_stage=wf).first()
    if sr is None:
        return {'state': 'not_started', 'workflow_stage': wf}
    record = getattr(sr, 'cutting_pattern', None)
    return {
        'state': 'completed' if sr.completed_at else 'in_progress',
        'workflow_stage': wf,
        'stage_record': sr,
        'record': record,
        'photo_count': record.photos.count() if record else 0,
        'started_at': sr.started_at,
        'completed_at': sr.completed_at,
        'completed_by': sr.completed_by,
    }
