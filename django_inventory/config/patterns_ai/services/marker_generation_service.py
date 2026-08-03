"""marker_generation_service — SINGLE WRITER for MarkerGenerationRun +
GeneratedMarkerCandidate, and the promotion path candidate -> Marker
(P3; ADR-A engines, ADR-D promotion, I-1 discipline).

Truth rules:
  * Consumes ONLY confirmed PieceSizeGeometry (latest confirmed version per
    piece); confirmed geometry is never touched.
  * Runs + candidates are append-only FACTS (params, placements, engine
    length, independent verification verdict).
  * Utilization / waste / per-garment numbers are DERIVED AT READ (F6) —
    no metric column exists.
  * Promotion = the HUMAN truth boundary: creates a real Marker (origin
    GENERATED) through marker_service (the marker single-writer), carrying
    benchmark EVIDENCE. When a manual baseline exists and the candidate's
    theoretical consumption is not strictly better, promotion REFUSES
    (owner principle: generated must beat the manual baseline, with
    evidence — theory must beat reality, labeled as such).
"""
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from accounts.services import MANAGEMENT_ROLES, user_has_role

from patterns_ai.models import (GeneratedMarkerCandidate, Marker,
                                MarkerGenerationRun, PatternPiece,
                                PatternPieceVersion, PieceSizeGeometry)
from . import compute_bridge
from . import marker_query_service
from . import marker_service
from .units import q2

PLACEMENTS_SCHEMA_VERSION = 1
PARAMS_SCHEMA_VERSION = 1
MIN_WIDTH_MM, MAX_WIDTH_MM = 300, 3000


def _gate(user):
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied('management role required')


# ---------- geometry resolution (read-only over frozen P2 truth) -----------

def resolve_generation_geometry(product, ratio):
    """🔒 M3 frozen API (renamed from collect_confirmed_geometry — it does
    more than collect). Resolves EVERYTHING a generation run consumes:
    required-piece validation (missing ⇒ raises naming exactly what
    blocks), optional-piece skipping per (piece, size) with honest
    warnings (rule 6 — never silent), and the engine payload.
    ratio: {ProductSize: count}. Returns (pieces_payload, sources,
    warnings)."""
    if not ratio or all(int(c) <= 0 for c in ratio.values()):
        raise ValidationError('ratio is empty — say how many garments of '
                              'which size the marker cuts.')
    pieces = list(PatternPiece.objects.filter(product=product)
                  .select_related('pattern'))
    if not pieces:
        raise ValidationError(f'{product.code} has no registered pattern '
                              'pieces — the geometry era comes first.')
    payload, sources, missing, on_fold, warnings = [], [], [], [], []
    for piece in pieces:
        if piece.on_fold:
            # fold ≠ missing design: blocks even for optional pieces
            # (fold-edge semantics are annotation-era scope, unchanged).
            on_fold.append(piece.pattern.name)
            continue
        version = (piece.versions
                   .filter(status=PatternPieceVersion.Status.CONFIRMED)
                   .order_by('-version_no').first())
        if version is None:
            if piece.is_optional:
                warnings.append(f'{piece.pattern.name} — skipped '
                                '(optional, no confirmed design)')
                continue
            missing.append(f'{piece.pattern.name} (no confirmed version)')
            continue
        rows = {r.size_id: r for r in
                version.size_geometries.select_related('size')}
        for size, count in ratio.items():
            if int(count) <= 0:
                continue
            row = rows.get(size.pk)
            if row is None:
                if piece.is_optional:
                    warnings.append(f'{piece.pattern.name} / {size.label} '
                                    '— skipped (optional, no design for '
                                    'this size)')
                    continue
                missing.append(f'{piece.pattern.name} / {size.label} '
                               f'(v{version.version_no} has no geometry '
                               'for this size)')
                continue
            qty = int(count) * (2 if piece.is_pair else 1)
            payload.append({
                'key': f'{piece.pattern.name}·{size.code}',
                'polygon_mm': [[x / 1000.0, y / 1000.0]
                               for x, y in row.geometry['outer']],
                'qty': qty,
                'allow_180': True,
                'allow_mirror': bool(piece.is_pair),
            })
            sources.append({'piece_id': piece.pk, 'size_id': size.pk,
                            'version_id': version.pk,
                            'geometry_row_id': row.pk,
                            'trust_grade': row.trust_grade,
                            'qty': qty})
    if on_fold:
        # M4.5: fold placement lives in the Digital Cutting Table; this
        # legacy generator stays honest — it cannot fold (retired from
        # navigation, §18-d).
        raise ValidationError(
            'on-fold pieces: compose their marker on the Digital '
            'Cutting Table (fold placement) — this legacy generator '
            'cannot fold: ' + ', '.join(on_fold))
    if missing:
        raise ValidationError('confirmed geometry missing — '
                              + '; '.join(missing))
    if not payload:
        raise ValidationError('nothing to nest for that ratio.')
    return payload, sources, warnings


# ---------- the run ----------------------------------------------------------

@transaction.atomic
def start_run(*, user, product, usable_width_mm, ratio, spacing_mm=3.0,
              timebox_s=20, seed=42, engine='auto'):
    """Run the isolated nesting engines and persist run + every complete,
    verified candidate. Synchronous by design at factory volume (the ADR-B
    worker remains a later lever; nothing here forecloses it)."""
    _gate(user)
    usable_width_mm = int(usable_width_mm)
    if not (MIN_WIDTH_MM <= usable_width_mm <= MAX_WIDTH_MM):
        raise ValidationError(f'usable width {usable_width_mm} mm outside '
                              f'{MIN_WIDTH_MM}..{MAX_WIDTH_MM}.')
    if engine not in ('auto', 'svgnest', 'blf'):
        raise ValidationError(f'unknown engine {engine!r}.')
    pieces_payload, sources, optional_skipped = \
        resolve_generation_geometry(product, ratio)

    job = {'width_mm': float(usable_width_mm),
           'spacing_mm': float(spacing_mm),
           'timebox_s': float(timebox_s), 'seed': int(seed),
           'engine': engine, 'pieces': pieces_payload}
    result = compute_bridge.run_tool('nest', job,
                                     timeout_s=float(timebox_s) + 90)
    candidates = result.get('candidates') or []
    errors = result.get('errors') or {}
    if not candidates:
        raise ValidationError('no engine produced a complete layout: '
                              + '; '.join(f'{k}: {v}'
                                          for k, v in errors.items()))

    params = {'schema_version': PARAMS_SCHEMA_VERSION,
              'ratio': {str(s.pk): int(c) for s, c in ratio.items()},
              'spacing_mm': float(spacing_mm),
              'timebox_s': float(timebox_s), 'seed': int(seed),
              'engine': engine, 'pieces': sources}
    if optional_skipped:
        # additive key (M3, rule 6): the reproducibility spine records
        # exactly what was excluded — a skip is never silent, even
        # historically. Absent key = nothing was skipped.
        params['optional_skipped'] = optional_skipped
    run = MarkerGenerationRun.objects.create(
        product=product, usable_width_mm=usable_width_mm,
        params=params,
        pipeline_version=candidates[0]['pipeline_version'],
        errors=errors, created_by=user)
    rows = []
    for c in candidates:
        rows.append(GeneratedMarkerCandidate.objects.create(
            run=run, engine=c['engine'],
            placements={'schema_version': PLACEMENTS_SCHEMA_VERSION,
                        'placements': c['placements']},
            marker_length_mm=Decimal(str(c['length_mm'])),
            verification=c['verification'],
            seed=c.get('seed', seed), trials=c.get('trials')))
    return run, rows


# ---------- derived-at-read candidate metrics (F6 — never stored) -----------

def _polygon_area(ring):
    s = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def derive_candidate_metrics(candidate):
    """Pure-python derivation (no CV stack in Django — ADR-F): piece area
    from the SAME stored placement rings the cutter would use."""
    run = candidate.run
    ratio = run.params.get('ratio') or {}
    garments = sum(int(v) for v in ratio.values())
    length_mm = float(candidate.marker_length_mm)
    width_mm = float(run.usable_width_mm)
    pieces_area = sum(_polygon_area(p['polygon_mm'])
                      for p in candidate.placements['placements'])
    fabric_area = length_mm * width_mm
    util = (pieces_area / fabric_area) if fabric_area else None
    per_garment_mm = (length_mm / garments) if garments else None
    return {
        'garments': garments,
        'piece_count': len(candidate.placements['placements']),
        'length_mm': q2(length_mm),
        'utilization_pct': q2(util * 100) if util is not None else None,
        'waste_pct': q2((1 - util) * 100) if util is not None else None,
        'per_garment_m': q2(per_garment_mm / 1000) if per_garment_mm else None,
        'theoretical_m_per_100': (q2(per_garment_mm / 10)
                                  if per_garment_mm else None),
        'verified': bool(candidate.verification.get('ok')),
    }


# ---------- benchmark vs manual reality -------------------------------------

def manual_baseline(product, usable_width_mm):
    """Best (lowest) ACTUAL avg m/100 among non-generated markers of this
    product with recorded outcomes — the reality the candidate must beat.
    Width-band aware first, any-width fallback (labeled)."""
    rows = marker_query_service.get_product_yield_board(product, sort='avg')
    manual = [r for r in rows
              if r['marker'].origin != Marker.Origin.GENERATED
              and r['avg_meters_per_100'] is not None]
    if not manual:
        return None
    band = int(usable_width_mm) // 10
    same_band = [r for r in manual
                 if r['marker'].usable_width_band == band]
    pool = same_band or manual
    best = min(pool, key=lambda r: r['avg_meters_per_100'])
    return {'marker': best['marker'],
            'actual_m_per_100': best['avg_meters_per_100'],
            'n': best['n_for_average'],
            'same_width_band': bool(same_band)}


def benchmark_candidate(candidate):
    """Comparison payload shown to the human and frozen into promotion
    evidence. APPLES-TO-ORANGES BY NATURE and labeled so: candidate number
    is THEORY (perfect lay); baseline is RECORDED REALITY."""
    metrics = derive_candidate_metrics(candidate)
    base = manual_baseline(candidate.run.product,
                           candidate.run.usable_width_mm)
    verdict = 'no_baseline'
    if base is not None and metrics['theoretical_m_per_100'] is not None:
        verdict = ('beats' if metrics['theoretical_m_per_100']
                   < base['actual_m_per_100'] else 'does_not_beat')
    return {'metrics': metrics, 'baseline': base, 'verdict': verdict}


# ---------- promotion (D11 — the human truth boundary) ----------------------

@transaction.atomic
def promote_candidate(*, user, candidate, label='', notes=''):
    """Create the real GENERATED Marker from a verified candidate, through
    the marker single-writer. Refuses: unverified layouts, double
    promotion, and candidates that do not beat an existing manual baseline
    (evidence recorded either way)."""
    _gate(user)
    candidate = GeneratedMarkerCandidate.objects.select_for_update().get(
        pk=candidate.pk)
    if not candidate.verification.get('ok'):
        raise ValidationError('this candidate FAILED independent layout '
                              'verification — it can never be promoted.')
    if candidate.promoted_markers.exists():
        existing = candidate.promoted_markers.first()
        raise ValidationError(f'already promoted as {existing.reference} — '
                              'candidates promote once.')
    bench = benchmark_candidate(candidate)
    if bench['verdict'] == 'does_not_beat':
        base = bench['baseline']
        raise ValidationError(
            'promotion refused: theoretical '
            f"{bench['metrics']['theoretical_m_per_100']} m/100 does not "
            f"beat the manual baseline {base['marker'].reference} at "
            f"{base['actual_m_per_100']} m/100 (recorded reality, n="
            f"{base['n']}). Generated markers must beat the baseline "
            '(owner principle).')

    run = candidate.run
    ratio_counts = {str(k): int(v)
                    for k, v in (run.params.get('ratio') or {}).items()}
    marker = marker_service.create_marker(
        user=user, product=run.product,
        origin=Marker.Origin.GENERATED,
        usable_width_mm=run.usable_width_mm,
        ratio_counts=ratio_counts,
        label=label or f'Generated {candidate.engine} '
                       f'{candidate.marker_length_mm} mm',
        strategy=f'{candidate.engine}@{run.pipeline_version} '
                 f'seed={candidate.seed}',
        benchmarked_against=(bench['baseline']['marker']
                             if bench['baseline'] else None),
        notes=notes, candidate=candidate,
        benchmark_evidence={
            'schema_version': 1,
            'verdict': bench['verdict'],
            'theoretical_m_per_100':
                str(bench['metrics']['theoretical_m_per_100']),
            'baseline_actual_m_per_100':
                (str(bench['baseline']['actual_m_per_100'])
                 if bench['baseline'] else None),
            'baseline_n': (bench['baseline']['n']
                           if bench['baseline'] else None),
            'labels': 'candidate=THEORY(perfect lay) vs baseline='
                      'RECORDED REALITY — apples-to-oranges, stated',
        })
    return marker, bench


# ---------- Phase 4: the interactive workspace save path --------------------

MAX_HEIGHT_MM = 100000          # 100 m fabric piece — sanity ceiling


def _piece_multiset(placements):
    """Identity of a layout's piece set: (key, mirrored) counted — moves/
    rotations/locks allowed, adds/removes/renames are not."""
    from collections import Counter
    return Counter((p['key'], bool(p.get('mirrored')))
                   for p in placements)


# M4 G3: plies each laid layer yields — doubled lays cut 2 pieces per
# placement. A LAYOUT fact (recorded at save), never plies (lay_count
# stays production's truth — count hierarchy).
# M4.5: 'double' split into open/folded (the factory distinguishes them
# with its hands); legacy 'double' reads as double_open — identical
# multiplier, zero fold edges (plan §Q3, byte-identical legacy math).
LAY_MULTIPLIER = {'single': 1, 'double': 2, 'double_open': 2,
                  'double_folded': 2, 'tubular': 2}
# M4.5 lay capability: fold edges this lay OFFERS (plan R3 concept 3)
LAY_FOLD_EDGES = {'single': 0, 'double': 0, 'double_open': 0,
                  'double_folded': 1, 'tubular': 2}


@transaction.atomic
def save_table_layout(*, user, product, width_mm, height_mm, spacing_mm,
                      fabric_group, placements, layering_type='single',
                      ratio=None, roll_ref=None, recipe_label='',
                      notes=''):
    """Phase 7 — persist a Digital-Cutting-Table SESSION as a NEW
    immutable run+candidate (engine='table'). EXTENSION of the manual
    save (same models, same ONE verifier), because a table session has
    no source candidate and its piece set is the operator's own.

    Owner rule 3: NOTHING is recomputed — the placements persist exactly
    as reviewed; the verifier only CHECKS them. Owner rule 4/6: every
    design_key is resolved server-side to the confirmed geometry row +
    version, making the layout self-contained and Law-11 stale-checkable
    forever. LAW 12 re-enforced server-side.

    M4 Manufacturing Planner: the MARKER PLAN persists WITH the layout —
    layering_type → layer_multiplier (G3) · ratio {size_id: garments}
    (fills the honest ratio gap) · roll_ref {'id','label'} · recipe_label
    (which Marker Recipe produced this asset — provenance, R1) · notes
    (R3). All data; defaults keep pre-M4 saves byte-identical."""
    # No local model imports here on purpose. PatternPiece, PieceSizeGeometry and
    # PatternPieceVersion are all imported unconditionally at module level, and
    # `patterns_ai.models.PatternPieceVersion is patterns_ai.models.pieces.PatternPieceVersion`
    # (verified), so a local re-import added nothing — while shadowing those names for
    # the WHOLE function, meaning any future use ABOVE this point would raise
    # UnboundLocalError. That is exactly the F823 bug this ruff pass found live in
    # devseed/layers/products.py, where it broke a DivergenceError path.
    _gate(user)
    try:
        width_mm = int(width_mm)
        height_mm = int(height_mm)
        spacing_mm = float(spacing_mm)
    except (TypeError, ValueError):
        raise ValidationError('width/height/spacing must be numbers.')
    layering_type = (layering_type or 'single').strip().lower()
    if layering_type not in LAY_MULTIPLIER:
        raise ValidationError(f'unknown layering type: {layering_type!r}')
    clean_ratio = {}
    for k, v in (ratio or {}).items():
        try:
            clean_ratio[str(int(k))] = max(1, int(v))
        except (TypeError, ValueError):
            raise ValidationError('ratio must map size ids to garment '
                                  'counts.')
    if not (MIN_WIDTH_MM <= width_mm <= MAX_WIDTH_MM):
        raise ValidationError(f'fabric width {width_mm} mm outside '
                              f'{MIN_WIDTH_MM}..{MAX_WIDTH_MM}.')
    if not (0 < height_mm <= MAX_HEIGHT_MM):
        raise ValidationError('fabric height must be a positive length '
                              f'up to {MAX_HEIGHT_MM} mm.')
    fabric_group = (fabric_group or '').strip().lower()
    if fabric_group not in PatternPiece.FabricGroup.values:
        raise ValidationError(f'unknown fabric group: {fabric_group!r}')
    _validate_layout_placements(placements)

    # resolve every design_key -> confirmed geometry (self-containment)
    pieces_spec = []
    qty = {}
    for p in placements:
        qty[str(p['key'])] = qty.get(str(p['key']), 0) + 1
    for key, count in sorted(qty.items()):
        try:
            piece_id, size_id = (int(x) for x in key.split(':'))
        except ValueError:
            raise ValidationError(f'bad design key {key!r}.')
        piece = PatternPiece.objects.filter(pk=piece_id,
                                            product=product).first()
        if piece is None:
            raise ValidationError(f'design {key}: piece not in this '
                                  'product.')
        if piece.fabric_group != fabric_group:
            raise ValidationError(
                f'LAW 12: "{piece.pattern.name}" is '
                f'{piece.fabric_group.upper()} — this layout is '
                f'{fabric_group.upper()}. One layout = one fabric group.')
        row = (PieceSizeGeometry.objects
               .filter(version__piece=piece, size_id=size_id,
                       version__status=PatternPieceVersion.Status.CONFIRMED)
               .select_related('version').first())
        if row is None:
            raise ValidationError(
                f'design {key}: no CONFIRMED geometry — the table only '
                'consumes confirmed Pattern Designs.')
        pieces_spec.append({'piece_id': piece_id, 'size_id': size_id,
                            'version_id': row.version_id,
                            'geometry_row_id': row.pk, 'qty': count,
                            'allow_mirror': bool(piece.is_pair)})

    # the ONE verifier — validation only, never a transform (rule 3)
    result = compute_bridge.run_tool('nest', {
        'op': 'verify', 'width_mm': float(width_mm),
        'spacing_mm': spacing_mm, 'placements': placements})
    if not result.get('ok'):
        raise ValidationError(
            f"verification failed: {result.get('error', 'unknown')}")
    verification, length = result['verification'], result['length_mm']
    if not verification['ok']:
        raise ValidationError(
            'layout refused by the verifier: max overlap '
            f"{verification['max_overlap_mm2']} mm², within width: "
            f"{verification['within_width']} — resolve the highlighted "
            'collisions in the workspace first.')
    if float(length) > height_mm:
        raise ValidationError(
            f'marker length {length} mm exceeds the fabric height '
            f'{height_mm} mm — shorten the layout or use longer fabric.')

    run = MarkerGenerationRun.objects.create(
        product=product, usable_width_mm=width_mm,
        params={'schema_version': PARAMS_SCHEMA_VERSION, 'manual': True,
                'table': True, 'fabric_group': fabric_group,
                'height_mm': height_mm, 'spacing_mm': spacing_mm,
                # M4: the Marker Plan is part of the asset (was the
                # honest `ratio: {}` gap — filled where it belongs)
                'ratio': clean_ratio,
                'layering_type': layering_type,
                'layer_multiplier': LAY_MULTIPLIER[layering_type],
                'fold_edges': LAY_FOLD_EDGES[layering_type],
                'roll': roll_ref or None,
                'recipe': (recipe_label or '')[:80],
                'notes': (notes or '')[:500],
                'pieces': pieces_spec},
        pipeline_version='table-v1', errors={}, created_by=user)
    candidate = GeneratedMarkerCandidate.objects.create(
        run=run, engine='table',
        placements={'schema_version': PLACEMENTS_SCHEMA_VERSION,
                    'placements': placements},
        marker_length_mm=Decimal(str(length)),
        verification=verification, seed=0, trials=None)
    return run, candidate


@transaction.atomic
def save_manual_layout(*, user, source_candidate, width_mm, height_mm,
                       placements):
    """Persist a HUMAN-adjusted layout as a NEW immutable run+candidate
    pair (engine='manual'). Verified by THE generation verifier before
    anything persists; overlapping or oversize layouts are REFUSED with
    the numbers (fix in the workspace, then save)."""
    _gate(user)
    width_mm = int(width_mm)
    if not (MIN_WIDTH_MM <= width_mm <= MAX_WIDTH_MM):
        raise ValidationError(f'fabric width {width_mm} mm outside '
                              f'{MIN_WIDTH_MM}..{MAX_WIDTH_MM}.')
    height_mm = int(height_mm)
    if not (0 < height_mm <= MAX_HEIGHT_MM):
        raise ValidationError('fabric height must be a positive length '
                              f'up to {MAX_HEIGHT_MM} mm.')
    if not isinstance(placements, list) or not placements:
        raise ValidationError('layout has no pieces.')
    for p in placements:
        if not {'key', 'instance', 'polygon_mm'} <= set(p):
            raise ValidationError('each piece needs key, instance and '
                                  'polygon_mm.')
        ring = p['polygon_mm']
        if (not isinstance(ring, list) or len(ring) < 3
                or not all(isinstance(pt, (list, tuple)) and len(pt) == 2
                           for pt in ring)):
            raise ValidationError(f"piece {p['key']}: bad polygon.")
    source = GeneratedMarkerCandidate.objects.select_related('run').get(
        pk=source_candidate.pk)
    if (_piece_multiset(placements)
            != _piece_multiset(source.placements['placements'])):
        raise ValidationError(
            'the layout must contain exactly the source candidate\'s '
            'pieces — moving/rotating/locking only (no adds or removes).')

    spacing = float(source.run.params.get('spacing_mm', 2.0))
    result = compute_bridge.run_tool('nest', {
        'op': 'verify', 'width_mm': float(width_mm),
        'spacing_mm': spacing, 'placements': placements})
    if not result.get('ok'):
        raise ValidationError(f"verification failed: {result.get('error')}")
    verification = result['verification']
    length = result['length_mm']
    if not verification['ok']:
        raise ValidationError(
            'layout refused by the verifier: '
            f"max overlap {verification['max_overlap_mm2']} mm², "
            f"within width: {verification['within_width']} — resolve the "
            'highlighted collisions in the workspace first.')
    if length > height_mm:
        raise ValidationError(
            f'marker length {length} mm exceeds the fabric height '
            f'{height_mm} mm — shorten the layout or use longer fabric.')

    run = MarkerGenerationRun.objects.create(
        product=source.run.product, usable_width_mm=width_mm,
        params={'schema_version': PARAMS_SCHEMA_VERSION,
                'manual': True,
                'source_candidate_id': source.pk,
                'height_mm': height_mm,
                'spacing_mm': spacing,
                'ratio': source.run.params.get('ratio') or {},
                'pieces': source.run.params.get('pieces') or []},
        pipeline_version=source.run.pipeline_version,
        errors={}, created_by=user)
    candidate = GeneratedMarkerCandidate.objects.create(
        run=run, engine='manual',
        placements={'schema_version': PLACEMENTS_SCHEMA_VERSION,
                    'placements': placements},
        marker_length_mm=Decimal(str(length)),
        verification=verification, seed=source.seed,
        trials=None)
    return run, candidate


# ---------- Phase 5 M2: stateless optimize endpoint (compute-only) ----------

OPTIMIZE_EFFORTS = ('fast', 'balanced', 'best')
MIN_SPACING_MM, MAX_SPACING_MM = 0.5, 50.0
EFFORT_TIMEOUT_S = {'fast': 60, 'balanced': 90, 'best': 150}


def _validate_layout_placements(placements):
    if not isinstance(placements, list) or not placements:
        raise ValidationError('layout has no pieces.')
    for p in placements:
        if not isinstance(p, dict) or not (
                {'key', 'instance', 'polygon_mm'} <= set(p)):
            raise ValidationError('each piece needs key, instance and '
                                  'polygon_mm.')
        ring = p['polygon_mm']
        if (not isinstance(ring, list) or len(ring) < 3
                or not all(isinstance(pt, (list, tuple)) and len(pt) == 2
                           for pt in ring)):
            raise ValidationError(f"piece {p.get('key')}: bad polygon.")


def optimize_layout(*, user, width_mm, height_mm, spacing_mm,
                    placements, selected=None, options_wanted=3,
                    effort='balanced', seed=42):
    """STATELESS compute (clarification 1): everything needed arrives in
    this call; the server keeps NOTHING (clarification 2 — preview/keep/
    undo live in the browser; only the Phase-4 save path ever persists).
    Returns options with stable in-response ids (clarification 3) plus
    the submitted layout's own metrics so deltas are computed where the
    numbers are born. WRITES NOTHING — test-walled.
    """
    _gate(user)
    try:
        width_mm = int(width_mm)
        height_mm = int(height_mm)
        spacing_mm = float(spacing_mm)
        options_wanted = int(options_wanted)
        seed = int(seed)
    except (TypeError, ValueError):
        raise ValidationError('width/height/spacing/options/seed must be '
                              'numbers.')
    if not (MIN_WIDTH_MM <= width_mm <= MAX_WIDTH_MM):
        raise ValidationError(f'fabric width {width_mm} mm outside '
                              f'{MIN_WIDTH_MM}..{MAX_WIDTH_MM}.')
    if not (0 < height_mm <= MAX_HEIGHT_MM):
        raise ValidationError('fabric height must be a positive length '
                              f'up to {MAX_HEIGHT_MM} mm.')
    if not (MIN_SPACING_MM <= spacing_mm <= MAX_SPACING_MM):
        raise ValidationError(f'piece spacing must be between '
                              f'{MIN_SPACING_MM} and {MAX_SPACING_MM} mm.')
    if not (1 <= options_wanted <= 8):
        raise ValidationError('layout options must be between 1 and 8.')
    effort = str(effort).lower()
    if effort not in OPTIMIZE_EFFORTS:
        raise ValidationError('mode must be Fast, Balanced or Best.')
    _validate_layout_placements(placements)

    selected = selected or []
    sel = set()
    for item in selected:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValidationError('selection entries must be '
                                  '[key, instance] pairs.')
        sel.add((str(item[0]), int(item[1])))

    # scope law (rule 7): selected∩unlocked when a selection exists,
    # else all unlocked; everything else = fixed obstacle for this run.
    fixed, free = [], []
    for p in placements:
        in_sel = (str(p['key']), int(p['instance'])) in sel
        locked = bool(p.get('locked'))
        movable = (not locked) and (not sel or in_sel)
        (free if movable else fixed).append(p)
    if not free:
        if sel:
            raise ValidationError('everything selected is locked — unlock '
                                  'something or select other pieces.')
        raise ValidationError('every piece is locked — unlock something '
                              'to optimize.')

    # the submitted layout's own metrics (deltas are computed where the
    # numbers are born; an invalid current layout is reported, not hidden)
    cur = compute_bridge.run_tool('nest', {
        'op': 'verify', 'width_mm': float(width_mm),
        'spacing_mm': spacing_mm, 'placements': placements})
    current = {
        'length_mm': cur['length_mm'],
        'utilization_pct': None,
        'waste_pct': None,
        'verification': cur['verification'],
    }
    total_area = sum(_polygon_area(p['polygon_mm']) for p in placements)
    if cur['length_mm']:
        u = total_area / (width_mm * float(cur['length_mm'])) * 100
        current['utilization_pct'] = round(u, 2)
        current['waste_pct'] = round(100 - u, 2)

    result = compute_bridge.run_tool('nest', {
        'op': 'optimize', 'width_mm': float(width_mm),
        'height_mm': float(height_mm), 'spacing_mm': spacing_mm,
        'seed': seed, 'options_wanted': options_wanted, 'effort': effort,
        'fixed': fixed,
        'free': free,
    }, timeout_s=EFFORT_TIMEOUT_S[effort])
    if not result.get('ok'):
        raise ValidationError(result.get('error', 'optimization failed.'))

    options = []
    for i, o in enumerate(result['options'], start=1):
        util = round(o['utilization_pct'], 2)
        length = float(o['length_mm'])
        delta_len = (round(length - float(current['length_mm']), 2)
                     if current['length_mm'] else None)
        delta_util = (round(util - current['utilization_pct'], 2)
                      if current['utilization_pct'] is not None else None)
        options.append({
            'id': f'option-{i}',            # stable WITHIN this response only
            'placements': o['placements'],
            'length_mm': length,
            'utilization_pct': util,
            'waste_pct': round(100 - util, 2),
            'verification': o['verification'],
            'delta_length_mm': delta_len,
            'delta_utilization_pct': delta_util,
            'worse_than_current': (delta_len is not None
                                   and (delta_len > 0
                                        or (delta_util is not None
                                            and delta_util < 0))),
        })
    return {'ok': True, 'seed': seed, 'effort': effort,
            'orderings_tried': result.get('orderings_tried'),
            'dropped': result.get('dropped'),
            'current': current, 'options': options}
