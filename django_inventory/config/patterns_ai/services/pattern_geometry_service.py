"""pattern_geometry_service — SINGLE WRITER for PatternPiece,
PatternPieceVersion, PieceSizeGeometry, GeometryExtraction and
PatternSetLabel (P2; ADR-C/D/D2/D3, I-1 discipline).

Truth chain: capture (immutable photo) -> extraction (append-only proposal
+ recorded gate verdict) -> HUMAN accept -> draft version geometry ->
HUMAN confirm (grain mandatory, tape acceptance, trust grade) -> immutable
knowledge. Confidence is display-only; nothing auto-accepts (Era-2 stance).
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.services import MANAGEMENT_ROLES, user_has_role

from patterns_ai.models import (CalibrationMat, CaptureAsset,
                                GeometryExtraction,
                                PatternPiece, PatternPieceVersion,
                                PatternSetLabel, PieceSizeGeometry)
from . import compute_bridge
from .units import mm_to_um, validate_canonical_geometry

TAPE_TOLERANCE_MM = 2.0          # ADR-E in-cage tier


# Phase-1 frozen-platform law: the semantic contract every stored geometry
# payload satisfies (ADR-C: integer µm, y-up, CCW outer, cut-ready contour).
# Bumping this constant is the ONLY way a new contract enters the system —
# single-writer-controlled, never a stray model default.
# adr-c.2 (M2, CONSCIOUS bump per PRODUCT_DESIGN_FREEZE §18-g): c.1 +
# optional typed features.notches + piece-level declared seam metadata.
# adr-c.3 (M4.5, CONSCIOUS bump per the fold plan §Q2): c.2 + optional
# typed features.fold_edge (straight vertical outline segment — the
# half-pattern's fold line). Every c.2 payload is a valid c.3 payload.
GEOMETRY_CONTRACT_VERSION = 'adr-c.3'


def _gate(user):
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied('management role required')


# ---- pieces ---------------------------------------------------------------

def create_piece(*, user, product, pattern, fabric_group, is_pair=False,
                 on_fold=False, notes=''):
    _gate(user)
    if not product.pattern_assignments.filter(pattern=pattern).exists():
        raise ValidationError(
            f'pattern {pattern} is not assigned to {product.code} — assign '
            'it in the product pattern library first.')
    if PatternPiece.objects.filter(product=product, pattern=pattern).exists():
        raise ValidationError(
            f'a piece row for {product.code} · {pattern} already exists.')
    assignment = product.pattern_assignments.filter(pattern=pattern).first()
    return PatternPiece.objects.create(
        product=product, pattern=pattern, assignment=assignment,
        fabric_group=fabric_group, is_pair=is_pair, on_fold=on_fold,
        notes=notes, created_by=user)


def set_piece_optional(*, user, piece, is_optional):
    """🔒 M3 frozen API. Flip the pattern-set semantics flag: optional
    pieces with missing designs are skipped WITH a warning at generation;
    required pieces keep blocking by name (rule 6 — never silent)."""
    _gate(user)
    is_optional = bool(is_optional)
    if piece.is_optional == is_optional:
        return piece                      # idempotent no-op
    piece.is_optional = is_optional
    # auto_now updated_at only refreshes when named in update_fields
    piece.save(update_fields=['is_optional', 'updated_at'])
    return piece


def set_piece_rules(*, user, piece, is_pair=None, on_fold=None,
                    grain_rule=None, fabric_group=None,
                    expected_notches=..., seam_allowance_mm=...):
    """Phase-2 Blueprint writer: edit the piece's placement RULES
    (pair · fold · grain · fabric group; M2 adr-c.2: notch expectation +
    declared seam mm). None/... = leave unchanged (the two metadata slots
    use ... as the sentinel because None = "clear the value").
    Rules are constraint metadata — geometry rows are never touched."""
    _gate(user)
    changed = []
    if is_pair is not None and bool(is_pair) != piece.is_pair:
        piece.is_pair = bool(is_pair); changed.append('is_pair')
    if on_fold is not None and bool(on_fold) != piece.on_fold:
        piece.on_fold = bool(on_fold); changed.append('on_fold')
    if grain_rule is not None and grain_rule != piece.grain_rule:
        if grain_rule not in PatternPiece.GrainRule.values:
            raise ValidationError(f'unknown grain rule: {grain_rule!r}')
        piece.grain_rule = grain_rule; changed.append('grain_rule')
    if fabric_group is not None and fabric_group != piece.fabric_group:
        if fabric_group not in PatternPiece.FabricGroup.values:
            raise ValidationError(f'unknown fabric group: {fabric_group!r}')
        piece.fabric_group = fabric_group; changed.append('fabric_group')
    if expected_notches is not ...:
        val = None
        if expected_notches not in (None, ''):
            try:
                val = max(0, int(expected_notches))
            except (TypeError, ValueError):
                raise ValidationError('notch expectation must be a number.')
        if val != piece.expected_notches:
            piece.expected_notches = val; changed.append('expected_notches')
    if seam_allowance_mm is not ...:
        from decimal import Decimal, InvalidOperation
        val = None
        if seam_allowance_mm not in (None, ''):
            try:
                val = Decimal(str(seam_allowance_mm)).quantize(Decimal('0.1'))
            except (InvalidOperation, ValueError):
                raise ValidationError('seam allowance must be millimetres.')
            if val < 0:
                raise ValidationError('seam allowance cannot be negative.')
        if val != piece.seam_allowance_mm:
            piece.seam_allowance_mm = val
            changed.append('seam_allowance_mm')
    if changed:
        piece.save(update_fields=changed + ['updated_at'])
    return piece


def register_pattern_definition(*, user, product, name, pieces_count=1,
                                fabric_group='body', is_pair=False,
                                on_fold=False, grain_rule=None,
                                is_optional=False, notes=''):
    """Phase-2: THE ONLY public write API for creating a Pattern
    Definition (owner-approved). One transaction replaces the old
    3-step dance: ProductPattern (get-or-create by name) → assignment
    (with pieces_count) → PatternPiece (with rules)."""
    from django.utils.text import slugify
    from production.models import ProductPattern, ProductPatternAssignment
    _gate(user)
    name = (name or '').strip()
    if not name:
        raise ValidationError('piece name is required.')
    pieces_count = max(1, int(pieces_count or 1))
    with transaction.atomic():
        # Phase-3 D-1 (owner-approved): structure begins ⇒ the preparation
        # universe exists — a sizeless product gets the REAL Universal size
        # in the SAME transaction (production-owned writer, D-2).
        if not product.sizes.filter(is_active=True).exists():
            from production.services.product_size_service import (
                ensure_universal_size)
            ensure_universal_size(product)
        pattern = ProductPattern.objects.filter(name__iexact=name).first()
        if pattern is None:
            code = slugify(name)[:50] or f'piece-{product.pk}'
            if ProductPattern.objects.filter(code=code).exists():
                code = f'{code}-{product.pk}'[:50]
            pattern = ProductPattern.objects.create(code=code, name=name)
        if PatternPiece.objects.filter(product=product,
                                       pattern=pattern).exists():
            raise ValidationError(
                f'"{name}" is already in this product\'s Blueprint.')
        ProductPatternAssignment.objects.get_or_create(
            product=product, pattern=pattern,
            defaults={'pieces_count': pieces_count})
        piece = create_piece(user=user, product=product, pattern=pattern,
                             fabric_group=fabric_group, is_pair=is_pair,
                             on_fold=on_fold, notes=notes)
        if grain_rule is not None or is_optional:
            if is_optional:
                set_piece_optional(user=user, piece=piece, is_optional=True)
            if grain_rule is not None:
                set_piece_rules(user=user, piece=piece,
                                grain_rule=grain_rule)
    return piece


def set_piece_count(*, user, piece, pieces_count):
    """Phase-2 Blueprint writer: pieces-per-garment lives on the
    assignment row (single count truth — never duplicated per size)."""
    _gate(user)
    if piece.assignment_id is None:
        raise ValidationError('this piece has no assignment row — '
                              're-register it via the Blueprint.')
    pieces_count = max(1, int(pieces_count or 1))
    if piece.assignment.pieces_count != pieces_count:
        piece.assignment.pieces_count = pieces_count
        piece.assignment.save(update_fields=['pieces_count'])
    return piece


def remove_pattern_definition(*, user, piece):
    """Phase-2: remove a definition ONLY while it has no design history.
    Any version/geometry = append-only knowledge → refuse with the
    honest action (mark it optional instead)."""
    _gate(user)
    if piece.versions.exists():
        raise ValidationError(
            f'"{piece.pattern.name}" already has design history — history '
            'is never deleted. Mark the piece optional instead.')
    with transaction.atomic():
        assignment = piece.assignment
        piece.delete()
        if assignment is not None:
            assignment.delete()


def set_reference_image(*, user, piece, asset):
    """🔒 M3 frozen API. Attach/clear (asset=None) the DISPLAY-ONLY
    illustration. Documentation only — extraction structurally refuses
    non-pattern_capture kinds, so a reference image can never enter
    geometry, verification, generation, optimization or exports."""
    _gate(user)
    if asset is not None:
        if asset.kind != CaptureAsset.Kind.REFERENCE_IMAGE:
            raise ValidationError(
                'only reference_image captures can illustrate a piece — '
                'geometry photos stay in the capture wizard.')
        if asset.product_id != piece.product_id:
            raise ValidationError(
                'that image belongs to a different product.')
        if asset.status != CaptureAsset.Status.STORED:
            raise ValidationError(
                'retired or corrupt captures cannot illustrate a piece.')
    new_id = asset.pk if asset is not None else None
    if piece.reference_image_id == new_id:
        return piece                      # idempotent no-op
    piece.reference_image = asset
    piece.save(update_fields=['reference_image', 'updated_at'])
    return piece


def create_set_label(*, user, product, code, label, notes=''):
    _gate(user)
    code = (code or '').strip()
    if not code:
        raise ValidationError('set code is required.')
    if PatternSetLabel.objects.filter(product=product, code=code).exists():
        raise ValidationError(f'set label {code} already exists for '
                              f'{product.code}.')
    return PatternSetLabel.objects.create(
        product=product, code=code, label=label or code, notes=notes,
        created_by=user)


# ---- versions (ADR-D piece-level chain; ADR-D2 grain) ----------------------

@transaction.atomic
def _copy_forward_rows(*, source, draft, user):
    """ADR-D2 §3 copy-forward: every geometry row of `source` lands on
    `draft` with copied_from provenance; trust/tape/contract carried."""
    for row in source.size_geometries.select_related('size'):
        PieceSizeGeometry.objects.create(
            version=draft, size=row.size, geometry=row.geometry,
            chord_tolerance_um=row.chord_tolerance_um,
            trust_grade=row.trust_grade,
            source_extraction=row.source_extraction, copied_from=row,
            tape_acceptance=row.tape_acceptance, created_by=user,
            # copy-forward carries the ORIGINAL contract — payload unchanged
            geometry_contract_version=row.geometry_contract_version)


@transaction.atomic
def get_or_create_draft(*, user, piece, set_label=None):
    """One working draft per piece at a time (sanity rule): reuse the open
    draft or append version_no = max+1. M8.1 bare-draft safety: on a piece
    with a CONFIRMED version, the new draft ALWAYS copy-forwards its rows —
    accepting one size must never open a draft that would publish away the
    others (ADR-D2 §3 applies to every draft-creating path, not just the
    explicit Reopen button)."""
    _gate(user)
    piece = PatternPiece.objects.select_for_update().get(pk=piece.pk)
    draft = piece.versions.filter(
        status=PatternPieceVersion.Status.DRAFT).first()
    if draft:
        return draft
    last = piece.versions.order_by('-version_no').first()
    source = (piece.versions.filter(
        status=PatternPieceVersion.Status.CONFIRMED)
        .order_by('-version_no').first())
    draft = PatternPieceVersion.objects.create(
        piece=piece, version_no=(last.version_no + 1 if last else 1),
        set_label=set_label or (source.set_label if source else None),
        created_by=user)
    if source is not None:
        _copy_forward_rows(source=source, draft=draft, user=user)
    return draft


@transaction.atomic
def start_next_version(*, user, piece):
    """The EXPLICIT Reopen-in-Studio act (kept distinct: refuses when a
    draft is already open / nothing confirmed); the copy itself is the
    shared `_copy_forward_rows` — one copy-forward routine everywhere."""
    _gate(user)
    piece = PatternPiece.objects.select_for_update().get(pk=piece.pk)
    if piece.versions.filter(status=PatternPieceVersion.Status.DRAFT).exists():
        raise ValidationError('a draft already exists for this piece — '
                              'finish (confirm/reject) it first.')
    source = (piece.versions.filter(
        status=PatternPieceVersion.Status.CONFIRMED)
        .order_by('-version_no').first())
    if source is None:
        raise ValidationError('no confirmed version to copy forward — use '
                              'the plain draft flow.')
    draft = PatternPieceVersion.objects.create(
        piece=piece, version_no=source.version_no + 1,
        set_label=source.set_label, created_by=user)
    _copy_forward_rows(source=source, draft=draft, user=user)
    return draft


# ---- extraction (capture -> proposal; ADR-E hard gate) ---------------------

def run_extraction(*, user, capture, piece, size, backend='classical',
                   chord_tolerance_um=500, evidence=None):
    """Run the isolated pipeline on a stored capture. The row is created
    even when the gate REFUSES — refusal reasons are recorded facts.
    `evidence` (M2) links the proposal into the piece×size Evidence Stack."""
    _gate(user)
    if capture.kind != capture.Kind.PATTERN_CAPTURE:
        raise ValidationError('capture is not a pattern capture.')
    if capture.product_id != piece.product_id:
        raise ValidationError('capture and piece belong to different products.')
    if size.product_id != piece.product_id:
        raise ValidationError('size belongs to a different product.')
    if capture.status != capture.Status.STORED:
        raise ValidationError(f'capture is {capture.status} — only stored '
                              'captures extract.')
    if capture.mat_id is None:
        raise ValidationError('capture has no calibration mat — pattern '
                              'photos must lie ON a commissioned mat (ADR-E).')
    # fresh row, never a caller-cached instance (stale-instance hardening,
    # the Block-2B lesson): status/board_spec must be CURRENT truth
    mat = CalibrationMat.objects.get(pk=capture.mat_id)
    if mat.status != CalibrationMat.Status.ACTIVE or not mat.board_spec:
        raise ValidationError(f'mat {mat.mat_code} is not active/commissioned.')

    result = compute_bridge.run_tool('extract', {
        'image_path': capture.file.path,
        'board_spec': mat.board_spec,
        'control_distances': mat.control_distances,
        'params': {'backend': backend,
                   'chord_tolerance_um': int(chord_tolerance_um)},
    })
    if not result.get('ok'):
        raise ValidationError(f"extraction failed: {result.get('error')}")
    geometry = result.get('geometry')
    if geometry is not None:
        problems = validate_canonical_geometry(geometry)
        if problems:
            raise ValidationError(f'compute returned invalid canonical '
                                  f'geometry: {problems}')
    return GeometryExtraction.objects.create(
        capture=capture, piece=piece, size=size, backend=backend,
        evidence=evidence,
        pipeline_version=result['provenance']['pipeline_version'],
        params=result['provenance']['params'],
        result={k: result.get(k) for k in
                ('metrics', 'checks', 'segmentation', 'provenance')},
        gate=result['gate'], geometry=geometry,
        confidence=result.get('confidence') or {}, created_by=user)


# ---- M2 acquisition adapters (UI freeze §7): every evidence kind runs
# through the SAME contract — adapter -> GeometryExtraction proposal
# (append-only, gate verdict recorded, honest refusals) -> one-shot human
# review -> draft row. This module stays the ONE writer of proposals.

# base display confidence per source (UI freeze §4 — DISPLAY ONLY, never
# auto-selects; photo keeps its per-run computed component confidence)
ADAPTER_BASE_CONFIDENCE = {'manual_dims': 100, 'dxf': 99, 'svg': 95}


def _proposal(*, evidence, user, backend, pipeline_version, geometry,
              refusal=None, checks=None):
    """Shared proposal writer for non-photo adapters: refusals are recorded
    facts (gate.passed=False + reasons), exactly like the photo gate."""
    gate = {'passed': refusal is None,
            'reasons': [refusal] if refusal else []}
    confidence = ({'overall': ADAPTER_BASE_CONFIDENCE.get(backend)}
                  if refusal is None else {})
    return GeometryExtraction.objects.create(
        capture=None, evidence=evidence, piece=evidence.piece,
        size=evidence.size, backend=backend,
        pipeline_version=pipeline_version, params=evidence.params or {},
        result={'checks': checks or {}}, gate=gate,
        geometry=geometry if refusal is None else None,
        confidence=confidence, created_by=user)


def run_evidence_adapter(*, user, evidence):
    """M2 dispatch: run the right adapter for a non-photo EvidenceItem and
    record its proposal (or honest refusal). Photo evidence keeps its own
    richer path (store_capture + run_extraction). Returns the proposal."""
    _gate(user)
    kind = evidence.kind
    if kind == 'dxf':
        return _run_dxf_adapter(user=user, evidence=evidence)
    if kind == 'svg':
        return _run_svg_adapter(user=user, evidence=evidence)
    if kind == 'manual_dims':
        return _run_dims_adapter(user=user, evidence=evidence)
    raise ValidationError(f'no adapter runs for kind {kind!r} — photo uses '
                          'the capture path; pdf/png/ai_api are not '
                          'available yet (honest-unavailable).')


def _run_dxf_adapter(*, user, evidence):
    """DXF → validate/convert via the isolated runtime → proposal."""
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory(prefix='pai_dxfev_') as td:
        p = Path(td) / 'evidence.dxf'
        with evidence.file.open('rb') as fh:
            p.write_bytes(fh.read())
        result = compute_bridge.run_tool('dxf', {'op': 'import',
                                                 'dxf_path': str(p)})
    if not result.get('ok'):
        return _proposal(evidence=evidence, user=user, backend='dxf',
                         pipeline_version='dxf-1', geometry=None,
                         refusal=f"DXF import failed: {result.get('error')}")
    pieces = result['pieces']
    if len(pieces) != 1:
        return _proposal(
            evidence=evidence, user=user, backend='dxf',
            pipeline_version='dxf-1', geometry=None,
            refusal=f'DXF contains {len(pieces)} boundary pieces — '
                    'one piece per file (split the file).')
    geometry = pieces[0]
    problems = validate_canonical_geometry(geometry)
    if problems:
        return _proposal(evidence=evidence, user=user, backend='dxf',
                         pipeline_version='dxf-1', geometry=None,
                         refusal=f'invalid geometry: {problems}')
    return _proposal(evidence=evidence, user=user, backend='dxf',
                     pipeline_version='dxf-1', geometry=geometry,
                     checks={'boundary_pieces': 1})


def _run_svg_adapter(*, user, evidence):
    """SVG → pure-python convert (straight segments; curves refuse
    honestly) → proposal."""
    from .svg_import import svg_to_canonical
    with evidence.file.open('rb') as fh:
        raw = fh.read()
    geometry, refusal = svg_to_canonical(raw)
    if refusal is None:
        problems = validate_canonical_geometry(geometry)
        if problems:
            geometry, refusal = None, f'invalid geometry: {problems}'
    return _proposal(evidence=evidence, user=user, backend='svg',
                     pipeline_version='svg-1', geometry=geometry,
                     refusal=refusal)


def _run_dims_adapter(*, user, evidence):
    """Manual dimensions → constructed rectangle starting shape (human
    refines in the editor); human-stated numbers = confidence 100."""
    params = evidence.params or {}
    try:
        w_um = mm_to_um(params['width_mm'])
        h_um = mm_to_um(params['height_mm'])
    except (KeyError, ValueError, TypeError, ArithmeticError):
        return _proposal(evidence=evidence, user=user, backend='manual_dims',
                         pipeline_version='dims-1', geometry=None,
                         refusal='width_mm/height_mm numbers required.')
    if w_um <= 0 or h_um <= 0:
        return _proposal(evidence=evidence, user=user, backend='manual_dims',
                         pipeline_version='dims-1', geometry=None,
                         refusal='dimensions must be positive millimetres.')
    geometry = {
        'schema_version': 1, 'units': 'um', 'origin': 'bbox_min',
        'axes': 'x_right_y_up', 'chord_tolerance_um': 500,
        'outer': [[0, 0], [w_um, 0], [w_um, h_um], [0, h_um]],
        'holes': [], 'features': {'grain': None, 'notches': []},
        'grade_rule': None}
    return _proposal(evidence=evidence, user=user, backend='manual_dims',
                     pipeline_version='dims-1', geometry=geometry,
                     checks={'constructed': 'rectangle'})


# ---- M8 Evidence-SET adapter (owner-frozen capture workflow) ---------------

def _collect_set_measurements(piece, size, primary):
    """Merge stated tape numbers across the WHOLE plain-photo stack —
    the primary's numbers win a name clash, then newest-first fills."""
    from patterns_ai.models import EvidenceItem
    items = list(EvidenceItem.objects.filter(
        piece=piece, size=size,
        kind=EvidenceItem.Kind.PHOTO_PLAIN).order_by('-id'))
    merged, sources = {}, {}
    ordered = [primary] + [e for e in items if e.pk != primary.pk]
    for ev in ordered:
        for name, mm in ((ev.params or {}).get('measurements')
                         or {}).items():
            if name not in merged:
                merged[name] = float(mm)
                sources[name] = ev.pk
    return merged, [e.pk for e in items]


def run_set_adapter(*, user, piece, size, primary):
    """ONE proposal from the whole Evidence Stack: primary plain photo →
    isolated extract_plain (Otsu, no mat); human tape width/height = the
    scale truth per axis; every other stated measurement is recorded as a
    cross-check (advisory — display at review, never a silent gate).
    Refusals (missing numbers, edge-touch, instability) come back as
    RECORDED proposals, ladder-honest."""
    import math
    _gate(user)
    measurements, evidence_ids = _collect_set_measurements(
        piece, size, primary)
    set_prov = {'primary_evidence_id': primary.pk,
                'evidence_ids': evidence_ids,
                'measurements': measurements}

    def _refusal(reason, pipeline_version='plain-1'):
        return GeometryExtraction.objects.create(
            capture=None, evidence=primary, piece=piece, size=size,
            backend='photo_plain', pipeline_version=pipeline_version,
            params={'set': set_prov},
            result={'set': set_prov},
            gate={'passed': False, 'reasons': [reason]},
            geometry=None, confidence={}, created_by=user)

    width_mm = measurements.get('width_mm')
    height_mm = measurements.get('height_mm')
    if not width_mm or not height_mm:
        return _refusal('state width_mm and height_mm on the evidence '
                        'measurements first — the tape numbers ARE the '
                        'scale (no mat in the photo).')
    result = compute_bridge.run_tool('extract_plain', {
        'image_path': primary.file.path,
        'width_mm': width_mm, 'height_mm': height_mm,
        'params': {'chord_tolerance_um': 2000}})
    if not result.get('ok'):
        return _refusal(f"extraction failed: {result.get('error')}")
    pipeline_version = result['provenance']['pipeline_version']
    if not result['gate'].get('passed'):
        return GeometryExtraction.objects.create(
            capture=None, evidence=primary, piece=piece, size=size,
            backend='photo_plain', pipeline_version=pipeline_version,
            params={'set': set_prov},
            result={**{k: result.get(k) for k in
                       ('metrics', 'checks', 'segmentation', 'provenance')},
                    'set': set_prov},
            gate=result['gate'], geometry=None, confidence={},
            created_by=user)
    geometry = result['geometry']
    problems = validate_canonical_geometry(geometry)
    if problems:
        return _refusal(f'compute returned invalid canonical geometry: '
                        f'{problems}', pipeline_version)

    # cross-checks: what CAN be derived from the outline is compared;
    # the rest is recorded as stated-only. bbox diagonal ≥ any on-piece
    # tape diagonal, so deltas are ADVISORY for the human review.
    xs = [p[0] for p in geometry['outer']]
    ys = [p[1] for p in geometry['outer']]
    bw_mm = (max(xs) - min(xs)) / 1000.0
    bh_mm = (max(ys) - min(ys)) / 1000.0
    cross = {}
    for name, stated in measurements.items():
        derived = {'width_mm': bw_mm, 'height_mm': bh_mm,
                   'diagonal_mm': math.hypot(bw_mm, bh_mm)}.get(name)
        cross[name] = ({'stated': stated, 'derived': round(derived, 1),
                        'delta_mm': round(derived - stated, 1)}
                       if derived is not None
                       else {'stated': stated, 'derived': None})
    set_prov['cross_checks'] = cross
    return GeometryExtraction.objects.create(
        capture=None, evidence=primary, piece=piece, size=size,
        backend='photo_plain', pipeline_version=pipeline_version,
        params={'set': {'primary_evidence_id': primary.pk,
                        'width_mm': width_mm, 'height_mm': height_mm}},
        result={**{k: result.get(k) for k in
                   ('metrics', 'checks', 'segmentation', 'provenance')},
                'set': set_prov},
        gate=result['gate'], geometry=geometry,
        confidence=result.get('confidence') or {}, created_by=user)


@transaction.atomic
def accept_extraction(*, user, extraction):
    """HUMAN acceptance: proposal -> draft-version geometry row. One-shot."""
    _gate(user)
    extraction = GeometryExtraction.objects.select_for_update().get(
        pk=extraction.pk)
    if extraction.status != GeometryExtraction.Status.PROPOSED:
        raise ValidationError(f'extraction already {extraction.status} — '
                              'review decisions are one-shot.')
    if not extraction.gate.get('passed') or extraction.geometry is None:
        raise ValidationError('this extraction was REFUSED by the quality '
                              'gate — it cannot be accepted; retake the photo.')
    # M2: trust grade BY ADAPTER — only mat-calibrated photo proposals earn
    # photo_calibrated; dxf/svg/manual stay uncalibrated until a
    # tape-accepted confirm upgrades them (the ONE path to measured).
    trust = (PieceSizeGeometry.TrustGrade.PHOTO_CALIBRATED
             if extraction.capture_id is not None
             else PieceSizeGeometry.TrustGrade.UNCALIBRATED)
    draft = get_or_create_draft(user=user, piece=extraction.piece)
    row = draft.size_geometries.filter(size=extraction.size).first()
    if row:
        # draft-time replace: newer accepted capture supersedes the working row
        row.geometry = extraction.geometry
        row.chord_tolerance_um = extraction.geometry['chord_tolerance_um']
        row.trust_grade = trust
        row.source_extraction = extraction
        row.copied_from = None
        row.tape_acceptance = {}
        # new payload replaces the old one → stamp the CURRENT contract
        row.geometry_contract_version = GEOMETRY_CONTRACT_VERSION
        row.save()
    else:
        row = PieceSizeGeometry.objects.create(
            version=draft, size=extraction.size,
            geometry=extraction.geometry,
            chord_tolerance_um=extraction.geometry['chord_tolerance_um'],
            trust_grade=trust,
            source_extraction=extraction, created_by=user,
            geometry_contract_version=GEOMETRY_CONTRACT_VERSION)
    extraction.status = GeometryExtraction.Status.ACCEPTED
    extraction.reviewed_by = user
    extraction.reviewed_at = timezone.now()
    extraction._review_transition = True
    extraction.save(update_fields=['status', 'reviewed_by', 'reviewed_at',
                                   'updated_at'])
    return row


@transaction.atomic
def reject_extraction(*, user, extraction, reason):
    _gate(user)
    reason = (reason or '').strip()
    if not reason:
        raise ValidationError('rejection needs a reason (F2).')
    extraction = GeometryExtraction.objects.select_for_update().get(
        pk=extraction.pk)
    if extraction.status != GeometryExtraction.Status.PROPOSED:
        raise ValidationError(f'extraction already {extraction.status} — '
                              'review decisions are one-shot.')
    extraction.status = GeometryExtraction.Status.REJECTED
    extraction.status_reason = reason
    extraction.reviewed_by = user
    extraction.reviewed_at = timezone.now()
    extraction._review_transition = True
    extraction.save(update_fields=['status', 'status_reason', 'reviewed_by',
                                   'reviewed_at', 'updated_at'])
    return extraction


# ---- draft editing (drafts only; confirmed geometry is immutable) ----------

@transaction.atomic
def edit_draft_geometry(*, user, version, size, outer_um, grain_cdeg=None,
                        notches=None, fold_edge=...):
    """Human refinement of a DRAFT row: replace the outer polyline (integer
    um vertices, already piece-local), optionally set the grain angle,
    (adr-c.2) the notch markers and (adr-c.3) the FOLD EDGE.
    notches=None leaves them unchanged; a list replaces them.
    fold_edge: ... = unchanged · None = clear · dict {p1_um,p2_um} = set
    (validated by fold_service; re-anchored with the outline)."""
    _gate(user)
    version = PatternPieceVersion.objects.select_for_update().get(
        pk=version.pk)
    if version.status != PatternPieceVersion.Status.DRAFT:
        raise ValidationError('only draft geometry is editable (ADR-D); '
                              'start a new version to change confirmed truth.')
    row = version.size_geometries.select_for_update().filter(
        size=size).first()
    if row is None:
        raise ValidationError('no geometry recorded for that size yet.')
    payload = dict(row.geometry)
    # re-anchor to bbox-min so hand-dragged vertices stay canonical
    if (not isinstance(outer_um, list)) or len(outer_um) < 3:
        raise ValidationError('outer polyline needs at least 3 vertices.')
    try:
        pts = [[int(x), int(y)] for x, y in outer_um]
    except (TypeError, ValueError):
        raise ValidationError('vertices must be integer micrometre pairs.')
    minx = min(p[0] for p in pts); miny = min(p[1] for p in pts)
    payload['outer'] = [[x - minx, y - miny] for x, y in pts]
    if _signed_area(payload['outer']) < 0:
        payload['outer'] = list(reversed(payload['outer']))
    if grain_cdeg is not None:
        feats = dict(payload.get('features') or {})
        feats['grain'] = {'angle_cdeg': int(grain_cdeg) % 36000}
        payload['features'] = feats
    if notches is not None:
        # adr-c.2: notch markers live in the SAME frame as the outline —
        # shift by the same re-anchor offset the vertices just took.
        if not isinstance(notches, list):
            raise ValidationError('notches must be a list.')
        clean = []
        for n in notches:
            try:
                clean.append({'x_um': int(n['x_um']) - minx,
                              'y_um': int(n['y_um']) - miny,
                              **({'label': str(n['label'])[:40]}
                                 if n.get('label') else {})})
            except (TypeError, ValueError, KeyError):
                raise ValidationError('each notch needs integer x_um/y_um.')
        feats = dict(payload.get('features') or {})
        feats['notches'] = clean
        payload['features'] = feats
    if fold_edge is not ...:
        from .fold_service import validate_fold_edge
        feats = dict(payload.get('features') or {})
        if fold_edge is None:
            feats.pop('fold_edge', None)
        else:
            try:
                fe = {'p1_um': [int(fold_edge['p1_um'][0]) - minx,
                                int(fold_edge['p1_um'][1]) - miny],
                      'p2_um': [int(fold_edge['p2_um'][0]) - minx,
                               int(fold_edge['p2_um'][1]) - miny]}
            except (TypeError, ValueError, KeyError, IndexError):
                raise ValidationError('fold_edge needs integer '
                                      'p1_um/p2_um pairs.')
            problems = validate_fold_edge(payload, fe)
            if problems:
                raise ValidationError(f'fold edge refused: {problems}')
            feats['fold_edge'] = fe
        payload['features'] = feats
    problems = validate_canonical_geometry(payload)
    if problems:
        raise ValidationError(f'edited geometry invalid: {problems}')
    row.geometry = payload
    # manual edit rebuilds the payload → it satisfies the CURRENT contract
    row.geometry_contract_version = GEOMETRY_CONTRACT_VERSION
    row.save()
    return row


def _signed_area(pts):
    s = 0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return s / 2.0


# ---- confirm / reject (the human truth boundary) ---------------------------

@transaction.atomic
def confirm_version(*, user, version, grain_by_size=None, tape_by_size=None):
    """Confirm = permanent knowledge. Grain vector MANDATORY per row
    (ADR-C §5). Tape acceptance (ADR-E §5): provided numbers must match the
    stored geometry within the tier or confirmation REFUSES; matching tape
    upgrades that row's trust grade to MEASURED."""
    _gate(user)
    version = PatternPieceVersion.objects.select_for_update().get(
        pk=version.pk)
    if version.status != PatternPieceVersion.Status.DRAFT:
        raise ValidationError(f'version is {version.status} — only drafts '
                              'confirm.')
    rows = list(version.size_geometries.select_for_update()
                .select_related('size'))
    if not rows:
        raise ValidationError('nothing to confirm — no size geometry '
                              'recorded on this draft.')
    # M8.1 backstop: confirming must never silently DROP a size the
    # current confirmed version covers. Copy-forward (get_or_create_draft
    # / Reopen) makes this unreachable in normal flows; it guards exotic
    # and future paths forever. Archived sizes are exempt — deliberate
    # size retirement stays possible.
    prev = (version.piece.versions
            .filter(status=PatternPieceVersion.Status.CONFIRMED)
            .order_by('-version_no').first())
    if prev is not None:
        draft_size_ids = {r.size_id for r in rows}
        dropped = [g.size.label for g in
                   prev.size_geometries.select_related('size')
                   if g.size_id not in draft_size_ids and g.size.is_active]
        if dropped:
            raise ValidationError(
                f'confirming would drop size(s) {", ".join(sorted(dropped))} '
                f'currently published on v{prev.version_no} — carry them '
                'forward (Reopen in Studio copies every size) or archive '
                'the size first.')
    grain_by_size = grain_by_size or {}
    tape_by_size = tape_by_size or {}
    for row in rows:
        payload = dict(row.geometry)
        feats = dict(payload.get('features') or {})
        grain = grain_by_size.get(row.size_id, feats.get('grain'))
        if isinstance(grain, int):
            grain = {'angle_cdeg': grain % 36000}
        if not grain or grain.get('angle_cdeg') is None:
            raise ValidationError(
                f'grain direction missing for size {row.size.code} — grain '
                'is mandatory at confirm (ADR-C §5).')
        feats['grain'] = grain
        payload['features'] = feats
        problems = validate_canonical_geometry(payload)
        if problems:
            raise ValidationError(
                f'size {row.size.code}: geometry invalid: {problems}')
        tape = tape_by_size.get(row.size_id)
        if tape:
            xs = [p[0] for p in payload['outer']]
            ys = [p[1] for p in payload['outer']]
            gw, gh = max(xs) / 1000.0, max(ys) / 1000.0
            dw = abs(gw - float(tape['width_mm']))
            dh = abs(gh - float(tape['height_mm']))
            if dw > TAPE_TOLERANCE_MM or dh > TAPE_TOLERANCE_MM:
                raise ValidationError(
                    f'size {row.size.code}: tape says '
                    f"{tape['width_mm']}x{tape['height_mm']} mm but geometry "
                    f'measures {gw:.1f}x{gh:.1f} mm — beyond the '
                    f'{TAPE_TOLERANCE_MM} mm tier. Re-measure or retake; '
                    'confirmation refused (honest-AI).')
            row.tape_acceptance = {
                'schema_version': 1, 'width_mm': float(tape['width_mm']),
                'height_mm': float(tape['height_mm']),
                'delta_w_mm': round(dw, 2), 'delta_h_mm': round(dh, 2),
                'tolerance_mm': TAPE_TOLERANCE_MM}
            row.trust_grade = PieceSizeGeometry.TrustGrade.MEASURED
        row.geometry = payload
        # confirm normalizes the payload → stamp the CURRENT contract
        row.geometry_contract_version = GEOMETRY_CONTRACT_VERSION
        row.save()

    prior = (version.piece.versions
             .filter(status=PatternPieceVersion.Status.CONFIRMED)
             .exclude(pk=version.pk))
    version.status = PatternPieceVersion.Status.CONFIRMED
    version.confirmed_by = user
    version.confirmed_at = timezone.now()
    version.save(update_fields=['status', 'confirmed_by', 'confirmed_at',
                                'updated_at'])
    for old in prior.select_for_update():
        old.status = PatternPieceVersion.Status.SUPERSEDED
        old.superseded_by = version
        old.save(update_fields=['status', 'superseded_by', 'updated_at'])
    return version


@transaction.atomic
def reject_version(*, user, version, reason):
    _gate(user)
    reason = (reason or '').strip()
    if not reason:
        raise ValidationError('rejection needs a reason (F2).')
    version = PatternPieceVersion.objects.select_for_update().get(
        pk=version.pk)
    if version.status != PatternPieceVersion.Status.DRAFT:
        raise ValidationError(f'version is {version.status} — only drafts '
                              'reject.')
    version.status = PatternPieceVersion.Status.REJECTED
    version.status_reason = reason
    version.save(update_fields=['status', 'status_reason', 'updated_at'])
    return version


# ---- DXF (ADR-C §7 guaranteed exchange) ------------------------------------

@transaction.atomic
def import_dxf(*, user, piece, size, dxf_path):
    """DXF-AAMA import -> draft geometry row (trust: uncalibrated until a
    tape-accepted confirm upgrades it)."""
    _gate(user)
    if size.product_id != piece.product_id:
        raise ValidationError('size belongs to a different product.')
    open_draft = piece.versions.filter(
        status=PatternPieceVersion.Status.DRAFT).first()
    if open_draft and open_draft.size_geometries.filter(size=size).exists():
        # fail BEFORE the compute run — refusing after would waste the
        # subprocess and hide the real reason behind file lifetimes
        raise ValidationError(
            f'draft v{open_draft.version_no} already has geometry for '
            f'{size.code} — edit or re-capture instead of double-importing.')
    result = compute_bridge.run_tool('dxf', {'op': 'import',
                                             'dxf_path': str(dxf_path)})
    if not result.get('ok'):
        raise ValidationError(f"DXF import failed: {result.get('error')}")
    pieces = result['pieces']
    if len(pieces) != 1:
        raise ValidationError(
            f'DXF contains {len(pieces)} boundary pieces — import one piece '
            'per file (split the file).')
    geometry = pieces[0]
    problems = validate_canonical_geometry(geometry)
    if problems:
        raise ValidationError(f'imported geometry invalid: {problems}')
    draft = get_or_create_draft(user=user, piece=piece)
    row = draft.size_geometries.filter(size=size).first()
    if row is not None:
        # M8.1: the pre-check refused real double-imports, so this row can
        # only be the copy-forward carry — importing IS the re-capture
        row.geometry = geometry
        row.chord_tolerance_um = geometry['chord_tolerance_um']
        row.trust_grade = PieceSizeGeometry.TrustGrade.UNCALIBRATED
        row.source_extraction = None
        row.copied_from = None
        row.tape_acceptance = {}
        row.geometry_contract_version = GEOMETRY_CONTRACT_VERSION
        row.save()
        return row
    return PieceSizeGeometry.objects.create(
        version=draft, size=size, geometry=geometry,
        chord_tolerance_um=geometry['chord_tolerance_um'],
        trust_grade=PieceSizeGeometry.TrustGrade.UNCALIBRATED,
        created_by=user,
        geometry_contract_version=GEOMETRY_CONTRACT_VERSION)


def export_dxf_bytes(geometry_row):
    """Canonical -> DXF-AAMA bytes via the isolated runtime (read-only)."""
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory(prefix='pai_dxf_') as td:
        out = Path(td) / 'piece.dxf'
        result = compute_bridge.run_tool('dxf', {
            'op': 'export', 'geometry': geometry_row.geometry,
            'out_path': str(out)})
        if not result.get('ok'):
            raise ValidationError(f"DXF export failed: {result.get('error')}")
        return out.read_bytes()
