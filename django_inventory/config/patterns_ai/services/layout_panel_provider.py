"""Phase 8B — the READ-ONLY layout panel provider.

Registered into production's `cutting_pattern.LAYOUT_PROVIDER` from
apps.ready() (dependency inversion — the ARCHIVE_VALIDATORS pattern):
production consumes the plain dict this returns, never our modules.
SELECT-only; writes stay in layout_usage_service.
"""
from django.urls import reverse


def build_layout_panel(adda):
    """→ {'has_usage', 'choose_url', 'groups': [...]} for the pattern
    stage's Manufacturing Layout section. Derive-at-read; staleness
    re-checked LIVE on every render (LAW 11 — a contract that went
    stale after recording is shown loudly, not hidden)."""
    from patterns_ai.models import ApprovedLayoutUsage
    from patterns_ai.services.layout_library_service import layout_is_stale
    usages = (ApprovedLayoutUsage.objects
              .filter(adda=adda, voided_at__isnull=True)
              .select_related('layout__candidate__run', 'recorded_by')
              .order_by('fabric_group'))
    from patterns_ai.services.layout_usage_service import layer_multiplier
    groups = []
    for u in usages:
        lay = u.layout
        params = lay.candidate.run.params or {}
        groups.append({
            'group': u.fabric_group,
            'uid': lay.layout_uid,
            'version': lay.version_no,
            'name': lay.name,
            'width_mm': lay.candidate.run.usable_width_mm,
            'length_mm': float(lay.candidate.marker_length_mm),
            'svg_url': reverse('patterns_ai:candidate-svg',
                               args=[lay.candidate_id]),
            'stale': layout_is_stale(lay),   # derived, never stored
            'usage_id': u.pk,
            # M4: frozen Marker-Plan facts of this asset (data only —
            # multiplier = plies per LAID layer; plies stay production's)
            'layering_type': params.get('layering_type', 'single'),
            'layer_multiplier': layer_multiplier(lay),
            'recipe': params.get('recipe', ''),
        })
    # 8C — MARKER CONTENT (count hierarchy #1): per-(pattern, size)
    # piece counts derived from the stored placements of every ACTIVE
    # usage. CONTENT ONLY — lay_count (#2) is production's truth; the
    # provider never touches plies. Derived at read, stored nowhere.
    from patterns_ai.models import PatternPiece
    content = {}
    piece_ids = set()
    per_piece_size = {}
    for u in usages:
        # M4 G3: content is PER LAID LAYER — each usage's own multiplier
        # M4.5: fold placements open across the crease ⇒ multiplier÷2
        mult = layer_multiplier(u.layout)
        for p in (u.layout.candidate.placements or {}).get(
                'placements', []):
            try:
                piece_id, size_id = (int(x) for x in
                                     str(p['key']).split(':'))
            except (KeyError, ValueError):
                continue
            piece_ids.add(piece_id)
            k = (piece_id, size_id)
            ppp = mult // 2 if p.get('on_fold') else mult
            per_piece_size[k] = per_piece_size.get(k, 0) + max(1, ppp)
    pattern_by_piece = dict(
        PatternPiece.objects.filter(pk__in=piece_ids)
        .values_list('pk', 'pattern_id'))
    for (piece_id, size_id), n in per_piece_size.items():
        pattern_id = pattern_by_piece.get(piece_id)
        if pattern_id is None:
            continue
        k = (pattern_id, size_id)
        content[k] = content.get(k, 0) + n
    return {
        'has_usage': bool(groups),
        'choose_url': reverse('patterns_ai:choose-layout', args=[adda.pk]),
        'groups': groups,
        'content_by_pattern_size': [
            {'pattern_id': pid, 'size_id': sid, 'count': n}
            for (pid, sid), n in sorted(content.items())],
        'layout_uids': [g['uid'] for g in groups],
    }


def build_layering_recommendation(adda):
    """M6 — the layering edge (ADVISORY): recommended layer length per
    fabric group from the Adda's ACTIVE approved-layout contracts.
    Derive-at-read, plies-free; the operator's number always stands."""
    from patterns_ai.models import ApprovedLayoutUsage
    usages = (ApprovedLayoutUsage.objects
              .filter(adda=adda, voided_at__isnull=True)
              .select_related('layout__candidate__run')
              .order_by('fabric_group'))
    groups = []
    for u in usages:
        lay = u.layout
        params = lay.candidate.run.params or {}
        groups.append({
            'group': u.fabric_group,
            'uid': lay.layout_uid,
            'length_mm': float(lay.candidate.marker_length_mm),
            'layering_type': params.get('layering_type', 'single'),
        })
    return {'groups': groups} if groups else None
