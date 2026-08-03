"""Cutting-pattern stage service — yeh file kyu hai?

PRODUCTION FLOW MEIN POSITION:
  Layering → Pattern Design (yahan) → Cutting

CUTTING-PATTERN STAGE MATLAB:
  Cutting master Adda ke layered cloth pe pattern draw karta hai. Yeh
  pattern based hai `Product.pattern_assignments` ki list pe (e.g. T-Shirt
  ko 1 Front + 1 Back + 2 Sleeve chahiye). Phir master:
    - Video record karta hai pattern khinchte hue
    - Multiple photos upload karta hai
    - At least ek (video YA photo) mandatory hai — service enforce karti hai

YEH FILE MEIN FUNCTIONS:
  • start_pattern_stage          → manager workers assign karta hai
  • get_or_create_pattern_...    → AddaStageRecord lazy-create (idempotent)
  • attach_photo                  → ek photo upload, Pillow compress
  • save_pattern_record           → video + notes save / replace
  • complete_pattern_stage        → finalize + agle stage pe advance
  • get_pattern_snapshot          → lightweight snapshot dashboard ke liye
  • _compress_image (private)     → Pillow JPEG q=80 + max 2400px

STORAGE:
  • Photos → Pillow compress karta hai JPEG quality=80, max 2400px long edge,
    EXIF rotation honor (phone se aaye photos sideways nahi dikhte).
  • Video → as-is store hota hai (ffmpeg recompress future me karenge).
  • Dono Django ke `STORAGES['default']` se jaate hain. S3/MinIO switch =
    settings.py mein backend badlo, code zero change.

PERMISSIONS (skill/role gates):
  • Start                       → MANAGEMENT_ROLES (super_admin OR manager)
  • Upload photo / save video   → cutting_master OR cutting_master_helper
                                  skill (management bypass)
  • Complete + advance          → cutting_master_helper skill (OR super_admin)

KYUN SERVICE LAYER MEIN?
  CLAUDE.md rule #4: koi bhi multi-row write service layer mein hi hoga.
  View sirf POST data parse karke service call karta hai. Yahan har mutating
  function `@transaction.atomic` ke andar wrap hai — partial write impossible.
"""
from __future__ import annotations

# io = in-memory binary buffer; Pillow ka compressed JPEG yahan likhte hain
import io
# logging = Python stdlib structured logger; debug ke liye multi-table ops trace
import logging
from typing import Iterable

# Django ke standard exception types — view inhe pakad ke user-friendly
# message dikhata hai.
from django.core.exceptions import PermissionDenied, ValidationError
# ContentFile = ek "bytes" se Django storage compatible File object banane
# ke liye. Pillow ke compressed bytes ko ImageField mein save karne ke liye.
from django.core.files.base import ContentFile
# transaction.atomic = ek block; agar exception aaye to saara DB write rollback.
from django.db import transaction
# Django ka timezone-aware "now" — settings.USE_TZ=True ke saath consistent.
from django.utils import timezone
# Pillow = Python Imaging Library. Image.open + ImageOps.exif_transpose se
# phone photos sideways nahi aate; resize + JPEG re-encode bhi yahin hota.
from PIL import Image, ImageOps

# Skill constants — DB level pe `accounts.Skill.name` matches in raise hote
# hain. user_has_skill helper check karta hai user ke skills mein koi
# overlap hai ya nahi.
from accounts.skills import (
    SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER, user_has_skill,
)
# RBAC helpers — MANAGEMENT_ROLES = {super_admin, manager}. Management bypass
# har skill check pe (super admins always wins).
from accounts.services import MANAGEMENT_ROLES, ROLE_SUPER_ADMIN, user_has_role
# Hardcoded Stage.code constant. Service kis WorkflowStage ko lookup kare —
# wo Stage row jiska code='cutting_pattern'.
from production.constants import STAGE_CUTTING_PATTERN
# Models jo iss service mein read/write hote hain.
from production.models import (
    Adda, AddaStageRecord, CuttingPatternPhoto, CuttingPatternRecord,
    CuttingPatternSizeAllocation, CuttingPatternVerification,
    ProductPatternAssignment, ProductSize, WorkflowStage,
)
# Stage advancement helper — yeh function `adda.current_stage` ko next
# WorkflowStage pe move karta hai (or completes Adda agar last stage).
from production.services.adda_service import advance_to_next_stage
from production.services._shared import downstream_started_guard, reopen_stage_record

# Module logger — __name__ se per-module namespace milta hai (production.services.*)
logger = logging.getLogger(__name__)


# Pillow tunables — JPEG quality 80 ≈ visually lossless for photos, ~70%
# size reduction. 2400px long edge = retina 12.9" iPad scale (overkill for
# floor camera photos but keeps detail).
PHOTO_MAX_DIM = 2400
PHOTO_QUALITY = 80


def _ensure_pattern_skill(user):
    """Skill gate — upload/edit actions ke liye.

    Pass condition: user ke paas cutting_master ya cutting_master_helper
    skill ho, ya management role (super_admin/manager). Management bypass
    isliye taaki admin floor user ka kaam temporarily kar sake.
    """
    if user_has_role(user, MANAGEMENT_ROLES):
        return
    if not user_has_skill(user, [SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER]):
        raise PermissionDenied(
            "requires cutting_master or cutting_master_helper skill"
        )


def _ensure_can_complete_pattern(user):
    """Complete + advance ka gate — stricter than upload.

    Sirf cutting_master_helper skill OR super_admin role allowed. Reason:
    helper skill matlab quality check pass kar chukka user; wahi finalise
    kar sake. Master photo upload kar sakta hai but advance helper hi karega.
    """
    if user_has_role(user, {ROLE_SUPER_ADMIN}):
        return
    if not user_has_skill(user, SKILL_CUTTING_MASTER_HELPER):
        raise PermissionDenied(
            "only cutting_master_helper can complete the cutting_pattern stage"
        )


def _pattern_workflow_stage(adda: Adda) -> WorkflowStage | None:
    """Iss Adda ke Product ka cutting_pattern WorkflowStage row return.

    Agar product flow mein cutting_pattern attached nahi hai (admin ne
    flow editor mein add nahi kiya) to None. Caller error raise karega.
    """
    return adda.product.workflow_stages.filter(stage__code=STAGE_CUTTING_PATTERN).first()


def get_or_create_pattern_stage_record(adda: Adda, user,
                                       stream=None) -> AddaStageRecord:
    """Iss Adda ka cutting_pattern AddaStageRecord row return (lazy create).

    PRE-CONDITION: Adda abhi cutting_pattern stage pe ho. Iska matlab
    layering already complete + advance ho chuki hai. Agar Adda kahin aur
    hai (e.g. abhi bhi layering pe) to ValidationError.

    Why lazy create?
    User pehli baar workspace open kare to row na bane (sirf preview).
    Pehli baar koi action (start, upload) kare tab row create — disk pe
    junk records nahi banenge.
    """
    wf = _pattern_workflow_stage(adda)
    if wf is None:
        raise ValidationError("This product does not include the cutting_pattern stage.")
    # Streams: the gate is the LANE's readiness, not pointer equality —
    # this lane's LAY must be complete before its pattern work opens.
    from production.services.adda_service import resolve_stream
    lane = resolve_stream(adda, stream)
    from django.db.models import Q as _Q
    lay_done = AddaStageRecord.objects.filter(
        adda=adda, workflow_stage__stage__code='layering',
        completed_at__isnull=False).filter(
        _Q(stream=lane) | _Q(stream__isnull=True)).exists()
    if not lay_done:
        raise ValidationError(
            f"Complete the {lane.label} layering before its pattern work.")
    # lane-scoped SELECT-or-INSERT (adopts legacy NULL-stream rows).
    from production.services.adda_service import lane_stage_record
    sr = lane_stage_record(adda, wf, lane, create=True,
                           defaults={'started_at': timezone.now()})
    created = getattr(sr, '_lane_created', False)
    # Defensive: agar pehle se row tha but started_at NULL (legacy?), set kar do.
    if created and not sr.started_at:
        sr.started_at = timezone.now()
        sr.save(update_fields=['started_at'])
    if created:
        # PA-10-3 (Contract 2): snapshot the payable-rate at creation, like every other
        # SR site. Idempotent; caller is @transaction.atomic.
        from production.services.stage_rate_service import ensure_stage_role_rates
        ensure_stage_role_rates(sr)
    return sr


def _compress_image(uploaded) -> ContentFile:
    """Upload ki gayi image ko Pillow se compress karke ContentFile return.

    Steps:
      1. Image.open() — Pillow file ko parse karta hai
      2. exif_transpose() — phone photos ke EXIF "Orientation" tag honor
         (warna 90° sideways aati hain)
      3. convert('RGB') — PNG/RGBA channel JPEG ke compatible nahi, RGB me
      4. thumbnail() — aspect ratio preserve karke max 2400px tak shrink
      5. save(buf, JPEG, q=80) — buffer mein write
      6. ContentFile(bytes, name='*.jpg') — Django storage compatible

    Failure mode:
      Agar Pillow file decode nahi kar paaya (RAW, HEIC etc.), fallback
      = original bytes as-is. User ki upload kabhi reject nahi hoti.
    """
    try:
        img = Image.open(uploaded)
        img = ImageOps.exif_transpose(img)
        img = img.convert('RGB')
        img.thumbnail((PHOTO_MAX_DIM, PHOTO_MAX_DIM))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=PHOTO_QUALITY, optimize=True)
        buf.seek(0)
        # Filename mein .jpg lagao taaki disk pe consistent extension dikhe.
        base = (getattr(uploaded, 'name', 'photo') or 'photo').rsplit('.', 1)[0]
        return ContentFile(buf.read(), name=f"{base}.jpg")
    except Exception:
        # Fallback: as-is. seek(0) zaroori — Pillow ne pointer aage badha
        # diya hoga, original bytes phir se start se padhne hain.
        uploaded.seek(0)
        return ContentFile(uploaded.read(), name=getattr(uploaded, 'name', 'photo'))


@transaction.atomic
def start_pattern_stage(*, adda: Adda, worker_ids: Iterable[int], user,
                        stream=None) -> AddaStageRecord:
    """Manager workers assign karta hai → stage formally start.

    Workers M2M is reset (`workers.set(...)`) — call again with different
    list to swap workers. started_at sirf pehli baar set hota hai.

    Side effects:
      • AddaStageRecord — lazy get_or_create + started_at set
      • WorkerStageTask set — full replace via worker_task_service.set_stage_workers
      • AddaHistory (tracking app) — WORKERS_ASSIGNED entry via log_adda
    """
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("only management can start the cutting_pattern stage")
    sr = get_or_create_pattern_stage_record(adda, user, stream=stream)
    # .set() = M2M replace (delete extras + add missing). Idempotent.
    from production.services.worker_task_service import set_stage_workers
    set_stage_workers(sr, worker_ids)   # dual-write: M2M (authoritative) + WorkerStageTask
    if not sr.started_at:
        sr.started_at = timezone.now()
        sr.save(update_fields=['started_at'])
    from tracking.services import log_adda
    from tracking.models import AddaHistory
    log_adda(adda, AddaHistory.ChangeType.WORKERS_ASSIGNED, user,
             stage_record=sr, metadata={'worker_ids': list(worker_ids)})
    worker_id_list = list(worker_ids)
    logger.info(
        "cutting_pattern.start adda=%s stage_record=%s worker_count=%s worker_ids=%s user=%s",
        adda.id, sr.id, len(worker_id_list), worker_id_list, getattr(user, 'id', None),
    )
    return sr


@transaction.atomic
def ensure_pattern_record(*, stage_record: AddaStageRecord, user) -> CuttingPatternRecord:
    """CuttingPatternRecord lazy-create — verify / size-allocation flows ke liye.

    Verify aur size-allocation dono ko ek record FK chahiye, par video/notes
    ki zaroorat nahi. attach_photo aur save_pattern_record dono internally
    same get_or_create karte hain — yahan thin wrapper service-level pe
    expose karte hain taaki views direct CuttingPatternRecord.objects.create
    na karen (CLAUDE.md rule #4).
    """
    _ensure_pattern_skill(user)
    if stage_record.completed_at is not None:
        raise ValidationError("Stage already completed.")
    record, _created = CuttingPatternRecord.objects.get_or_create(stage_record=stage_record)
    return record


@transaction.atomic
def attach_photo(*, stage_record: AddaStageRecord, uploaded_image,
                 caption: str = '', user) -> CuttingPatternPhoto:
    """Ek photo attach karna — compress karke DB + storage mein save.

    Flow:
      1. Skill gate (cutting_master/helper, ya management)
      2. Stage completed nahi hona chahiye (warna locked)
      3. CuttingPatternRecord exist nahi karta to lazy create — video field
         null=True isliye possible
      4. Image Pillow se compress
      5. CuttingPatternPhoto row create karke return

    User explicit decision (2026-05-28): video first hone ki zaroorat nahi.
    Master photos OR video alone OR both upload kar sakta hai. Complete
    check at-least-one enforce karta hai.
    """
    _ensure_pattern_skill(user)
    if stage_record.completed_at is not None:
        raise ValidationError("Stage already completed — photos locked.")

    # OneToOne reverse access — None agar abhi record nahi bana.
    record = getattr(stage_record, 'cutting_pattern', None)
    if record is None:
        # No video required to create record — blank FileField OK.
        record = CuttingPatternRecord.objects.create(stage_record=stage_record)

    compressed = _compress_image(uploaded_image)
    return CuttingPatternPhoto.objects.create(
        record=record, image=compressed, caption=caption[:200], uploaded_by=user,
    )


@transaction.atomic
def save_pattern_record(*, adda: Adda, video_file, notes: str, user,
                        stream=None) -> CuttingPatternRecord:
    """Video + notes save/replace karna — independent (kisi ek se kaam chal jaata).

    Idempotent:
      • Pehli baar    → CuttingPatternRecord create + fields set
      • Dobara call  → existing record update (purani video ka file disk
                       par orphan reh sakti hai — cleanup future task)

    Photos attach_photo se aate hain, yahan se nahi. Photo collection
    replay ke beech preserved rehti hai (record FK same).
    """
    _ensure_pattern_skill(user)
    sr = get_or_create_pattern_stage_record(adda, user, stream=stream)
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed.")

    record, _created = CuttingPatternRecord.objects.get_or_create(stage_record=sr)
    # update_fields = sirf changed fields ko DB write. Performance + safer.
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
def verify_pattern(
    *, record: CuttingPatternRecord, assignment: ProductPatternAssignment,
    photo: CuttingPatternPhoto | None = None, note: str = '', user,
) -> CuttingPatternVerification:
    """Pattern assignment verify karna — ek row create/update.

    Idempotent: same (record, assignment) pe phir se call karo to existing
    row return; photo/note update kar dega.

    Cross-product safety: agar `assignment.product` aur
    `record.stage_record.adda.product` match nahi karte to ValidationError.
    """
    _ensure_pattern_skill(user)
    if record.stage_record.completed_at is not None:
        raise ValidationError("Stage already completed — verifications locked.")
    if assignment.product_id != record.stage_record.adda.product_id:
        raise ValidationError(
            "Pattern assignment does not belong to this Adda's product.",
        )
    # Photo, agar di gayi hai, isi record se attached honi chahiye.
    if photo is not None and photo.record_id != record.id:
        raise ValidationError("Photo does not belong to this pattern record.")

    obj, created = CuttingPatternVerification.objects.get_or_create(
        record=record, assignment=assignment,
        defaults={
            'verified_by': user,
            'photo': photo,
            'note': note[:200] if note else '',
        },
    )
    if not created:
        # Update photo + note + re-stamp verifier on re-verify (audit shows
        # latest reviewer).
        obj.photo = photo
        obj.note = note[:200] if note else ''
        obj.verified_by = user
        obj.save(update_fields=['photo', 'note', 'verified_by', 'updated_at'])
    return obj


@transaction.atomic
def unverify_pattern(
    *, record: CuttingPatternRecord, assignment: ProductPatternAssignment, user,
) -> None:
    """Verified row hatao — toggle-off semantics.

    No-op agar already absent. Stage completed hone ke baad lock.
    """
    _ensure_pattern_skill(user)
    if record.stage_record.completed_at is not None:
        raise ValidationError("Stage already completed — verifications locked.")
    CuttingPatternVerification.objects.filter(
        record=record, assignment=assignment,
    ).delete()


@transaction.atomic
def set_size_allocation(
    *, record: CuttingPatternRecord, allocations: list[dict], user,
) -> list[CuttingPatternSizeAllocation]:
    """Pattern designer size proportions lock kare — full replace semantics.

    allocations = [{'size_id': int, 'proportion_pct': int}, ...]

    Behavior:
      • Existing rows delete kar dete hain
      • Naya set bulk-insert
      • Drafts mein sum != 100 allowed (UI shows red badge);
        complete_pattern_stage at completion strict check karta hai
      • Each size product-match validate hota hai
    """
    _ensure_pattern_skill(user)
    if record.stage_record.completed_at is not None:
        raise ValidationError("Stage already completed — size allocations locked.")

    product = record.stage_record.adda.product
    cleaned = []
    seen_ids: set[int] = set()
    for entry in allocations or []:
        size_id = int(entry.get('size_id') or 0)
        pct = int(entry.get('proportion_pct') or 0)
        if size_id <= 0:
            raise ValidationError("Invalid size selection.")
        if size_id in seen_ids:
            raise ValidationError("Duplicate size in allocation list.")
        seen_ids.add(size_id)
        if pct < 0 or pct > 100:
            raise ValidationError(
                f"Proportion must be between 0 and 100 (got {pct}).",
            )
        try:
            size = ProductSize.objects.get(pk=size_id, product=product)
        except ProductSize.DoesNotExist:
            raise ValidationError(
                f"Size {size_id} is not configured on product {product.code}.",
            )
        cleaned.append((size, pct))

    # Full replace — atomic.
    CuttingPatternSizeAllocation.objects.filter(record=record).delete()
    rows = [
        CuttingPatternSizeAllocation(record=record, size=s, proportion_pct=p)
        for s, p in cleaned
    ]
    CuttingPatternSizeAllocation.objects.bulk_create(rows)
    return list(record.size_allocations.select_related('size').all())


@transaction.atomic
def complete_pattern_stage(*, adda: Adda, user, stream=None,
                           override_pending_reason: str | None = None) -> CuttingPatternRecord:
    """Finalize karke agle stage pe advance.

    Validation chain:
      1. Helper skill ya super_admin?
      2. Cutting_pattern stage iss product mein hai?
      3. Adda abhi cutting_pattern pe hai?
      4. AddaStageRecord row exist karta hai?
      5. Pehle se completed nahi hua?
      6. has_video OR has_photo (at least one)
      7. Saari ProductPatternAssignment rows verified hain
      8. ≥1 CuttingPatternSizeAllocation row hai
      9. Allocations ka proportion_pct sum = 100

    Pass hone par:
      • sr.completed_at + completed_by stamp
      • advance_to_next_stage → adda.current_stage agle WorkflowStage pe
        (e.g. cutting) OR Adda COMPLETED agar last stage tha

    Side effects:
      • AddaStageRecord — completed_at + completed_by stamp (this stage)
      • Adda — current_stage advanced (+ status/completed_at if last) via
        adda_service.advance_to_next_stage (cross-service)
      • AddaHistory (tracking app) — stage-advance entry logged inside
        advance_to_next_stage
      • Stage processing cost freeze happens inside advance_to_next_stage
        (cost_service) when configured
    """
    _ensure_can_complete_pattern(user)

    wf = _pattern_workflow_stage(adda)
    if wf is None:
        raise ValidationError("Product does not include the cutting_pattern stage.")
    from production.services.adda_service import resolve_stream
    lane = resolve_stream(adda, stream)

    try:
        # WF-4: lock the stage row so a concurrent completer blocks here and then
        # sees completed_at set below — prevents double-advance / double-freeze.
        from production.services.adda_service import lane_stage_record
        sr = lane_stage_record(adda, wf, lane, for_update=True)
        if sr is None:
            raise AddaStageRecord.DoesNotExist
    except AddaStageRecord.DoesNotExist:
        raise ValidationError("Stage record missing — upload video + photos first.")
    if sr.completed_at is not None:
        raise ValidationError("Stage already completed.")

    # EITHER video OR ≥1 photo (existing relaxed rule).
    record = getattr(sr, 'cutting_pattern', None)
    has_video = bool(record and record.video)
    has_photo = bool(record and record.photos.exists())
    if not (has_video or has_photo):
        raise ValidationError(
            "Upload at least one photo or a video of the pattern before completing."
        )

    # New rule 7: all ProductPatternAssignment rows for this product must
    # have a matching CuttingPatternVerification row on this record.
    if record is None:
        raise ValidationError(
            "Record missing — verify each pattern before completing.",
        )
    expected_assignment_ids = set(
        adda.product.pattern_assignments.values_list('id', flat=True)
    )
    verified_assignment_ids = set(
        record.verifications.values_list('assignment_id', flat=True)
    )
    missing = expected_assignment_ids - verified_assignment_ids
    if missing:
        raise ValidationError(
            f"{len(verified_assignment_ids)} of {len(expected_assignment_ids)} "
            f"patterns verified — verify all before completing."
        )

    # New rule 8/9: sizes-in-batch + proportion sum.
    allocations = list(record.size_allocations.all())
    if not allocations:
        raise ValidationError(
            "Select at least one size for this batch and lock proportions."
        )
    total_pct = sum(a.proportion_pct for a in allocations)
    if total_pct != 100:
        raise ValidationError(
            f"Size proportions sum to {total_pct}%, must be 100%."
        )

    sr.completed_at = timezone.now()
    sr.completed_by = user
    sr.save(update_fields=['completed_at', 'completed_by', 'updated_at'])

    # R8 WP-5 (spec §3, ANALYTICS ONLY — no payment reads this): lead time =
    # Pattern Design complete − Layering complete, minutes, on the typed record.
    from django.db.models import Q
    layering_sr = (AddaStageRecord.objects
                   .filter(adda=adda, workflow_stage__stage__code='layering',
                           completed_at__isnull=False)
                   .filter(Q(stream=lane) | Q(stream__isnull=True))
                   .order_by('-completed_at').first())
    if layering_sr is not None:
        delta = sr.completed_at - layering_sr.completed_at
        record.lead_minutes_from_layering = max(0, int(delta.total_seconds() // 60))
        record.save(update_fields=['lead_minutes_from_layering', 'updated_at'])

    # advance_to_next_stage = adda_service mein defined helper. Yeh
    # adda.current_stage ko agle WorkflowStage pe set karta hai aur
    # tracking.AddaHistory entry log karta hai.
    # R3: C3 guard + override live at the funnel (passthrough only).
    # Streams: the LANE finished its pattern check — lane funnel.
    from production.services.adda_service import advance_lane
    advance_lane(adda, stream=lane, leaving_sr=sr, user=user,
                 override_pending_reason=override_pending_reason)
    logger.info(
        "cutting_pattern.complete adda=%s stage_record=%s from_stage=%s "
        "verified=%s/%s allocations=%s user=%s",
        adda.id, sr.id, wf.id,
        len(verified_assignment_ids), len(expected_assignment_ids),
        len(allocations), getattr(user, 'id', None),
    )
    return record


@transaction.atomic
def reopen_pattern_stage(*, adda: Adda, user) -> AddaStageRecord:
    """Admin-only: completed Pattern Design stage ko unlock for correction.

    Mirror of `layering_service.reopen_layering` — same rules apply:
      • Management role required (super_admin / manager)
      • Refuse if any downstream stage already started
      • Rolls back sr.completed_at + completed_by → cleared
      • Adda.current_stage → pattern WorkflowStage
      • Adda.status → IN_PROGRESS (in case it had reached COMPLETED)
      • CuttingPatternRecord + photos preserved (master re-completes with
        corrected uploads which simply replace/append on existing record)
      • Audit via AddaHistory.STAGE_REOPENED

    Side effects:
      • AddaStageRecord — completed_at + completed_by cleared (this stage)
      • Frozen stage processing cost cleared via cost_service.clear_stage_cost
        (cross-service, money)
      • Adda — current_stage reset to pattern wf, status → IN_PROGRESS,
        completed_at cleared
      • AddaHistory (tracking app) — STAGE_REOPENED entry via log_adda
    """
    # Pattern stage keeps its CuttingPatternRecord (video + notes) + photos on
    # reopen — the master can replace them on re-complete — so there is NO
    # teardown. Its only delta from the shared skeleton is the downstream guard.
    return reopen_stage_record(
        adda=adda, stage_code=STAGE_CUTTING_PATTERN, stage_label='Pattern Design',
        user=user, guard=downstream_started_guard,
    )


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
    verified_count = record.verifications.count() if record else 0
    expected_count = adda.product.pattern_assignments.count()
    alloc_sum = (
        sum(a.proportion_pct for a in record.size_allocations.all())
        if record else 0
    )
    return {
        'state': 'completed' if sr.completed_at else 'in_progress',
        'workflow_stage': wf,
        'stage_record': sr,
        'record': record,
        'photo_count': record.photos.count() if record else 0,
        'verified_count': verified_count,
        'expected_pattern_count': expected_count,
        'allocation_sum_pct': alloc_sum,
        'started_at': sr.started_at,
        'completed_at': sr.completed_at,
        'completed_by': sr.completed_by,
    }
