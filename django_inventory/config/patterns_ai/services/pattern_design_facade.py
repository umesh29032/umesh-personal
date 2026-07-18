"""pattern_design_facade — THE read-only supplier of Pattern Design
knowledge (PDM W1; owner-locked direction 2026-07-07, plan §0b).

The Product Pattern Workspace (consumer #1) and the future Cutting
Table (the INTENDED consumer) read the same Design Rows from here.
The current Generate page is a TEMPORARY consumer — nothing in this
module may shape itself around it.

A **Design Row is a complete business object**: one Pattern Design
(= one Pattern Piece for one Product Size) carrying everything needed
to understand it or compose with it. Consumers think in Design Rows,
never scattered fields.

READ-ONLY: exposes NO writers, performs NO writes (test-walled).

Design-row CONTRACT (stable keys — the Cutting Table lifecycle
Available → Selected → Placed will consume rows as-is; renaming keys
is a reviewed change, not a refactor):
    design_key        f'{piece_id}:{size_id}' — stable identity
    piece_id · piece_name · badges {optional, pair, fold}
    size_id · size_code · size_label
    status            'confirmed' | 'draft' | 'missing'
    version_no        confirmed version number (None unless confirmed)
    version_id        confirmed PatternPieceVersion id (None unless …)
    draft_in_progress bool · draft_version_no (None when False)
    geometry_row_id   confirmed PieceSizeGeometry id (None unless …)
    outline_mm        [[x, y], …] mm — confirmed geometry outline
                      (None unless confirmed; palette preview + future
                      composition read THIS, never live rows elsewhere)
    dims              {'w_mm', 'h_mm', 'measured' bool, 'label'} —
                      tape-accepted numbers when MEASURED, else the
                      geometry bbox with its honest trust label
    reference_asset_id  piece-level reference image (shown per row)
    area_cm2          outline area (shoelace), confirmed only
    updated_at        the confirmed geometry row's last update
    checks            can-I-cut mini-checklist {geometry, reference,
                      confirmed, dxf} — booleans, honest per row
    next_step         'Add geometry' | 'Confirm the draft' | 'Ready ✓'

Per-section verdicts (W2R): ready (ALL required designs confirmed for
that size — the owner's 'Ready for Cutting?'), required_missing names,
rows ordered ISSUES-FIRST (required-missing, draft, optional-missing,
confirmed). Summary gains any_size_ready (the Cutting-Table gate).
"""
from patterns_ai.models import (PatternPiece, PatternPieceVersion,
                                ProductFabricProfile)


def product_design_library(product):
    """The canonical Product Design Library, size-first.

    Returns {'summary': {...}, 'sizes': [...], 'sections': [
        {'size': ProductSize, 'confirmed': int, 'total': int,
         'rows': [DesignRow, ...]}, ...]}
    Sections follow the size chart order; rows are piece-name ordered;
    ghost rows (status 'missing'/'draft') appear IN PLACE so the
    library always shows what SHOULD exist.
    """
    Status = PatternPieceVersion.Status
    sizes = list(product.sizes.filter(is_active=True)
                 .order_by('display_order'))
    pieces = list(PatternPiece.objects.filter(product=product)
                  .select_related('pattern', 'assignment')
                  .prefetch_related('versions__size_geometries')
                  .order_by('pattern__name'))
    profile = ProductFabricProfile.objects.filter(product=product).first()

    # one pass per piece: confirmed truth + open draft
    piece_cells = []
    for piece in pieces:
        confirmed = None
        draft = None
        for v in piece.versions.all():               # prefetched
            if v.status == Status.CONFIRMED and (
                    confirmed is None
                    or v.version_no > confirmed.version_no):
                confirmed = v
            elif v.status == Status.DRAFT:
                draft = v
        confirmed_rows = ({g.size_id: g
                           for g in confirmed.size_geometries.all()}
                          if confirmed else {})
        draft_rows = ({g.size_id: g for g in draft.size_geometries.all()}
                      if draft else {})
        piece_cells.append((piece, confirmed, draft,
                            confirmed_rows, draft_rows))

    ISSUE_ORDER = {'missing-required': 0, 'draft': 1,
                   'missing-optional': 2, 'confirmed': 3}
    sections = []
    total_confirmed = total_rows = 0
    any_size_ready = False
    for size in sizes:
        rows = []
        confirmed_count = 0
        required_missing = []
        for piece, confirmed, draft, c_rows, d_rows in piece_cells:
            row = _design_row(piece, size, confirmed, draft,
                              c_rows.get(size.pk), d_rows.get(size.pk))
            if row['status'] == 'confirmed':
                confirmed_count += 1
                # M4.5 readiness law: an on-fold piece is manufacture-
                # ready only WITH its fold edge — blocker names the fix
                if (row['capabilities']['fold_wished']
                        and not row['has_fold_edge']
                        and not row['badges']['optional']):
                    required_missing.append(
                        f"{row['piece_name']} (mark its fold edge in "
                        'the Studio)')
            elif not row['badges']['optional']:
                required_missing.append(row['piece_name'])
            rows.append(row)
        # issues float up (W2R): required gaps, drafts, optional gaps, done
        def _bucket(r):
            if r['status'] == 'confirmed':
                return ISSUE_ORDER['confirmed']
            if r['status'] == 'draft':
                return ISSUE_ORDER['draft']
            return (ISSUE_ORDER['missing-optional']
                    if r['badges']['optional']
                    else ISSUE_ORDER['missing-required'])
        rows.sort(key=lambda r: (_bucket(r), r['piece_name']))
        ready = bool(rows) and not required_missing
        if ready:
            any_size_ready = True
        # W2R2 traffic light: 🟢 ready · 🟡 1–2 required gaps ·
        # 🔴 3+ required gaps or nothing confirmed yet
        if ready:
            tier = 'ready'
        elif len(required_missing) <= 2 and confirmed_count:
            tier = 'attention'
        else:
            tier = 'missing'
        sections.append({'size': size, 'rows': rows,
                         'confirmed': confirmed_count,
                         'total': len(rows),
                         'ready': ready, 'tier': tier,
                         'required_missing': required_missing})
        total_confirmed += confirmed_count
        total_rows += len(rows)

    readiness = product_readiness(product)
    return {
        'summary': {
            'product': product,
            'pct': readiness['pct'], 'ready': readiness['ready'],
            'checklist': readiness['checklist'],
            'blockers': readiness['blockers'],
            'warnings': readiness['warnings'],
            'profile': profile,
            'sizes_count': len(sizes), 'pieces_count': len(pieces),
            'designs_confirmed': total_confirmed,
            'designs_total': total_rows,
            'any_size_ready': any_size_ready,
        },
        'sizes': sizes,
        'sections': sections,
    }


def _design_row(piece, size, confirmed, draft, c_row, d_row):
    """Build ONE Design Row business object (contract in the module
    docstring)."""
    from .fold_service import get_fold_edge, unfold_outline
    status = ('confirmed' if c_row is not None
              else 'draft' if d_row is not None else 'missing')
    outline_mm = None
    dims = None
    area_cm2 = None
    updated_at = None
    has_fold_edge = False
    opened_outline_mm = None
    opened_dims = None
    if c_row is not None:
        outer = c_row.geometry['outer']
        outline_mm = [[x / 1000.0, y / 1000.0] for x, y in outer]
        # M4.5: fold capability facts + the DERIVED opened piece
        # (never stored — computed from the half at read)
        fe = get_fold_edge(c_row.geometry)
        has_fold_edge = fe is not None
        if has_fold_edge:
            opened = unfold_outline(c_row.geometry)
            opened_outline_mm = [[x / 1000.0, y / 1000.0]
                                 for x, y in opened]
            opened_dims = {
                'w_mm': round(max(p[0] for p in opened_outline_mm), 1),
                'h_mm': round(max(p[1] for p in opened_outline_mm), 1)}
        shoelace = 0.0
        for i in range(len(outline_mm)):
            x1, y1 = outline_mm[i]
            x2, y2 = outline_mm[(i + 1) % len(outline_mm)]
            shoelace += x1 * y2 - x2 * y1
        area_cm2 = round(abs(shoelace) / 2.0 / 100.0, 1)   # mm² → cm²
        updated_at = c_row.updated_at
        tape = c_row.tape_acceptance or {}
        if tape.get('width_mm'):
            dims = {'w_mm': float(tape['width_mm']),
                    'h_mm': float(tape['height_mm']),
                    'measured': True, 'label': 'tape-accepted'}
        else:
            xs = [p[0] for p in outer]; ys = [p[1] for p in outer]
            dims = {'w_mm': round(max(xs) / 1000.0, 1),
                    'h_mm': round(max(ys) / 1000.0, 1),
                    'measured': False,
                    'label': c_row.get_trust_grade_display()}
    next_step = ('Ready ✓' if status == 'confirmed'
                 else 'Confirm the draft' if status == 'draft'
                 else 'Add geometry')
    checks = {
        'geometry': status in ('draft', 'confirmed'),   # drawn at all
        'reference': bool(piece.reference_image_id),
        'confirmed': status == 'confirmed',
        'dxf': status == 'confirmed',                   # exportable
    }
    return {
        'design_key': f'{piece.pk}:{size.pk}',
        'piece_id': piece.pk,
        'piece_name': piece.pattern.name,
        'badges': {'optional': piece.is_optional,
                   'pair': piece.is_pair, 'fold': piece.on_fold},
        # Phase-2 additive (owner-approved): Blueprint rules the future
        # DCT consumes as placement constraints
        'grain_rule': piece.grain_rule,
        'fabric_group': piece.fabric_group,
        'size_id': size.pk, 'size_code': size.code,
        'size_label': size.label,
        'status': status,
        'version_no': confirmed.version_no if c_row is not None else None,
        'version_id': confirmed.pk if c_row is not None else None,
        'draft_in_progress': d_row is not None or (
            draft is not None and status == 'confirmed'),
        'draft_version_no': (draft.version_no
                             if draft is not None else None),
        'geometry_row_id': c_row.pk if c_row is not None else None,
        'outline_mm': outline_mm,
        'dims': dims,
        'reference_asset_id': piece.reference_image_id,
        'area_cm2': area_cm2,
        'updated_at': updated_at,
        'checks': checks,
        'next_step': next_step,
        # M4.5 R2-A: THE PATTERN CAPABILITIES CONTRACT — the one named
        # shape every consumer reads (DCT payload, queue, M6, M7…).
        # Derived from the existing pattern-owned fields; Blueprint/
        # Studio stay the only editors (three-concepts law, plan R3).
        'has_fold_edge': has_fold_edge,
        'opened_outline_mm': opened_outline_mm,
        'opened_dims': opened_dims,
        # piece-local fold-line x (mm) — the DCT pins this onto the
        # fabric's fold edge (None when no fold edge)
        'fold_x_mm': (round(fe['p1_um'][0] / 1000.0, 2)
                      if has_fold_edge else None),
        'capabilities': {
            'fold': bool(piece.on_fold and has_fold_edge),
            'fold_wished': piece.on_fold,      # Blueprint intent
            'mirror': piece.is_pair,
            'pair': piece.is_pair,
            'rotation': piece.grain_rule,
            'seam_mm': (float(piece.seam_allowance_mm)
                        if piece.seam_allowance_mm is not None else None),
            'expected_notches': piece.expected_notches,
            'count': (piece.assignment.pieces_count
                      if piece.assignment_id else 1),
            'optional': piece.is_optional,
        },
    }


def product_readiness(product):
    """LEGACY-SHAPE readiness (verbatim move of views._hub_readiness —
    byte-parity guarded by tests). The Workspace summary + the
    temporary Generate-page matrix read this shape; it derives from the
    same truth chain as the Design Rows above."""
    from patterns_ai.models import PatternPiece as _PP
    Status = PatternPieceVersion.Status
    sizes = list(product.sizes.filter(is_active=True)
                 .order_by('display_order'))
    pieces = list(_PP.objects.filter(product=product)
                  .select_related('pattern', 'reference_image')
                  .prefetch_related('versions__size_geometries')
                  .order_by('pattern__name'))
    profile = ProductFabricProfile.objects.filter(product=product).first()

    rows, blockers, warnings = [], [], []
    req_cells = req_done = draft_cells = 0
    pieces_with_ref = 0
    for piece in pieces:
        name = piece.pattern.name
        confirmed = None
        draft_covered = set()
        for v in piece.versions.all():                 # prefetched
            if v.status == Status.CONFIRMED and (
                    confirmed is None
                    or v.version_no > confirmed.version_no):
                confirmed = v
            elif v.status == Status.DRAFT:
                draft_covered |= {g.size_id
                                  for g in v.size_geometries.all()}
        covered = ({g.size_id for g in confirmed.size_geometries.all()}
                   if confirmed else set())
        cells, missing, pending = [], [], []
        for s in sizes:
            if s.pk in covered:
                cells.append((s, 'ok'))
            elif s.pk in draft_covered:
                cells.append((s, 'draft'))
                pending.append(s.label)
                draft_cells += 1
            else:
                cells.append((s, 'missing'))
                missing.append(s.label)
            if not piece.is_optional:
                req_cells += 1
                if s.pk in covered:
                    req_done += 1
        if piece.on_fold:
            # M4.5 conscious law change: fold pieces are manufacturable
            # WITH a marked fold edge; the blocker now names the fix.
            no_edge = [s.label for s in sizes
                       if s.pk in covered and not (
                           (({g.size_id: g for g in
                              confirmed.size_geometries.all()}
                             [s.pk].geometry.get('features') or {})
                            .get('fold_edge')))]
            if no_edge:
                blockers.append(f'{name} — mark the fold edge in the '
                                f"Studio ({', '.join(no_edge)})")
        if missing:
            if piece.is_optional:
                warnings.append(f'{name} — missing {", ".join(missing)} '
                                '(optional: skipped honestly, never '
                                'blocks)')
            else:
                blockers.append(f'{name} — missing '
                                f'{", ".join(missing)} geometry')
        if pending:
            warnings.append(f'{name} — {", ".join(pending)} drawn but '
                            'not confirmed')
        if piece.reference_image_id:
            pieces_with_ref += 1
        else:
            warnings.append(f'{name} — missing reference image (warning)')
        if not sizes:
            nxt = 'Add product sizes first (production → Sizes)'
        elif confirmed is None and not draft_covered:
            nxt = 'Capture or import geometry'
        elif missing:
            nxt = f'Add {missing[0]} geometry'
        elif pending:
            nxt = 'Confirm the drawn sizes'
        elif not piece.reference_image_id:
            nxt = 'Add a reference image'
        else:
            nxt = 'Ready ✓'
        rows.append({'piece': piece, 'name': name, 'cells': cells,
                     'next_step': nxt, 'ready': nxt == 'Ready ✓'})

    checklist = [
        ('Product Sizes', bool(sizes),
         f'{len(sizes)} size(s)' if sizes else 'none — add on the '
         'production Sizes page', True),
        ('Pattern Types', bool(pieces),
         f'{len(pieces)} piece(s)' if pieces else 'register the pieces',
         True),
        ('Required Pieces', req_cells == 0 or req_done == req_cells,
         f'{req_done}/{req_cells} size designs confirmed', True),
        ('Confirmed Geometry', draft_cells == 0,
         'all confirmed' if draft_cells == 0
         else f'{draft_cells} drawn size(s) awaiting confirm', False),
        ('Grain', True, 'enforced at confirm — cannot be missing', False),
        ('Fold Rules',
         not any('mark the fold edge' in b for b in blockers),
         'fold edges marked' if any(p.on_fold for p in pieces)
         and not any('mark the fold edge' in b for b in blockers)
         else 'no on-fold pieces' if not any(p.on_fold for p in pieces)
         else 'on-fold pieces need their fold edge marked', True),
        ('Reference Images', pieces and pieces_with_ref == len(pieces),
         f'{pieces_with_ref}/{len(pieces)} pieces illustrated', False),
        ('Optional Pieces', True,
         f'{sum(1 for p in pieces if p.is_optional)} optional '
         '(skip honestly when incomplete)', False),
        ('Fabric Profile', profile is not None,
         'defaults set' if profile else 'no defaults yet (optional)',
         False),
    ]
    total = req_cells + len(pieces) + 1          # + fabric profile
    done = req_done + pieces_with_ref + (1 if profile else 0)
    pct = int(round(100 * done / total)) if total else 0
    ready = bool(sizes and pieces and not blockers)
    return {'sizes': sizes, 'rows': rows, 'checklist': checklist,
            'pct': pct, 'ready': ready,
            'blockers': blockers, 'warnings': warnings,
            'profile': profile}
