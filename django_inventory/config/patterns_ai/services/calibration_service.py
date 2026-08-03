"""calibration_service — SINGLE WRITER for CalibrationMat +
CalibrationMatCheck (ADR-E; I-1 discipline).

Lifecycle: register (uncommissioned) -> commission (board spec + tape
control distances + a passing photo check) -> active -> recheck rows over
its life -> retire(reason). Mats never delete (F5).
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.services import MANAGEMENT_ROLES, user_has_role

from patterns_ai.models import CalibrationMat, CalibrationMatCheck
from . import compute_bridge

BOARD_SPEC_KEYS = {'squares_x', 'squares_y', 'square_mm', 'marker_mm',
                   'aruco_dict'}


def _gate(user):
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied('management role required')


def register_mat(*, user, mat_code, name=''):
    _gate(user)
    mat_code = (mat_code or '').strip()
    if not mat_code:
        raise ValidationError('mat code is required (the physical label).')
    if CalibrationMat.objects.filter(mat_code=mat_code).exists():
        raise ValidationError(f'mat {mat_code} is already registered.')
    return CalibrationMat.objects.create(
        mat_code=mat_code, name=name, created_by=user)


def _validate_board_spec(board_spec):
    missing = BOARD_SPEC_KEYS - set(board_spec or {})
    if missing:
        raise ValidationError(
            f'board spec incomplete — missing {sorted(missing)}.')
    if 'schema_version' not in board_spec:
        raise ValidationError('board spec payload needs schema_version (F3).')


def _validate_control_distances(control_distances):
    rows = (control_distances or {}).get('distances') or []
    if not rows:
        raise ValidationError(
            'commissioning needs at least one tape-measured control '
            'distance (ADR-E: print-shop scale error is caught here).')
    if 'schema_version' not in control_distances:
        raise ValidationError('control distances payload needs schema_version (F3).')
    for r in rows:
        if not {'from_id', 'to_id', 'expected_mm'} <= set(r):
            raise ValidationError(
                'each control distance needs from_id, to_id, expected_mm.')


@transaction.atomic
def commission_mat(*, user, mat, board_spec, control_distances,
                   photo_asset=None, notes=''):
    """Commission with the tape truth; when a photo is supplied the compute
    runtime must PASS its gate on this very mat before it goes active."""
    _gate(user)
    mat = CalibrationMat.objects.select_for_update().get(pk=mat.pk)
    if mat.status != CalibrationMat.Status.UNCOMMISSIONED:
        raise ValidationError(
            f'mat {mat.mat_code} is {mat.status} — only uncommissioned mats '
            'commission; register a new mat_code for a new physical mat.')
    _validate_board_spec(board_spec)
    _validate_control_distances(control_distances)

    evidence = {'pipeline_version': None, 'note': 'tape-only commissioning'}
    passed = True
    if photo_asset is not None:
        result = compute_bridge.run_tool('calibrate', {
            'image_path': photo_asset.file.path,
            'board_spec': board_spec,
            'control_distances': control_distances,
        })
        if not result.get('ok'):
            raise ValidationError(f"calibration run failed: {result.get('error')}")
        evidence = result
        passed = result['gate']['passed']

    check = CalibrationMatCheck.objects.create(
        mat=mat, kind=CalibrationMatCheck.Kind.COMMISSIONING,
        capture=photo_asset, evidence=evidence, passed=passed,
        notes=notes, checked_by=user)
    if not passed:
        # evidence row stays (F2); the mat does NOT activate on a failed gate
        raise ValidationError(
            'commissioning check FAILED — evidence recorded (check '
            f'#{check.pk}): ' + '; '.join(evidence['gate']['reasons']))
    mat.board_spec = board_spec
    mat.control_distances = control_distances
    mat.status = CalibrationMat.Status.ACTIVE
    mat.commissioned_at = timezone.now()
    mat.save(update_fields=['board_spec', 'control_distances', 'status',
                            'commissioned_at', 'updated_at'])
    return mat, check


@transaction.atomic
def record_recheck(*, user, mat, photo_asset, notes=''):
    """Append a recheck evidence row from a fresh photo of the mat.
    A FAILED recheck does not auto-retire — humans decide (honest-AI)."""
    _gate(user)
    mat = CalibrationMat.objects.select_for_update().get(pk=mat.pk)
    if mat.status != CalibrationMat.Status.ACTIVE:
        raise ValidationError(f'mat {mat.mat_code} is {mat.status} — '
                              'only active mats recheck.')
    result = compute_bridge.run_tool('calibrate', {
        'image_path': photo_asset.file.path,
        'board_spec': mat.board_spec,
        'control_distances': mat.control_distances,
    })
    if not result.get('ok'):
        raise ValidationError(f"calibration run failed: {result.get('error')}")
    return CalibrationMatCheck.objects.create(
        mat=mat, kind=CalibrationMatCheck.Kind.RECHECK,
        capture=photo_asset, evidence=result,
        passed=result['gate']['passed'], notes=notes, checked_by=user)


@transaction.atomic
def retire_mat(*, user, mat, reason):
    _gate(user)
    reason = (reason or '').strip()
    if not reason:
        raise ValidationError('retirement needs a reason (F2).')
    mat = CalibrationMat.objects.select_for_update().get(pk=mat.pk)
    if mat.status == CalibrationMat.Status.RETIRED:
        raise ValidationError(f'mat {mat.mat_code} is already retired.')
    mat.status = CalibrationMat.Status.RETIRED
    mat.status_reason = reason
    mat.save(update_fields=['status', 'status_reason', 'updated_at'])
    return mat
