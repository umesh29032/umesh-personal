"""advisor_service — THE CUT ADVISOR BRAIN. **READ-ONLY** (P4 design §6).

Ranks and explains cut-planning options from the frozen fact streams.
Writes NOTHING (SELECT-only, test-proven). One math home: marker reality
comes from marker_query_service.get_marker_summary (P1's derive chain);
theory comes from P3's derive_candidate_metrics. Rankings are re-derived
from the growing fact base on every call — that IS the learning loop
(design §9); no scores are ever stored.
"""
from .units import q2

ADVISOR_VERSION = 'advisor:v1'
USABLE_STATUSES = ('candidate', 'validated')   # markers a cutter may lay


# ---------- eligibility + per-marker evidence -------------------------------

def _marker_rows(product):
    from patterns_ai.models import Marker
    from . import marker_query_service as q
    rows = []
    markers = (Marker.objects.filter(product=product,
                                     status__in=USABLE_STATUSES)
               .select_related('candidate__run'))
    for m in markers:
        s = q.get_marker_summary(m)
        theory = None
        if m.candidate_id:
            from . import marker_generation_service as gen
            theory = gen.derive_candidate_metrics(m.candidate)
        rows.append({
            'marker': m,
            'reference': m.reference,
            'origin': m.origin,
            'width_mm': m.usable_width_mm,
            'width_band': m.usable_width_band,
            'ratio_counts': (m.ratio or {}).get('counts') or {},
            'actual_m_per_100': s['avg_meters_per_100'],
            'n': s['n_for_average'],
            'usage_count': s['usage_count'],
            'last_used_at': s['last_used_at'],
            'theoretical_m_per_100': (theory['theoretical_m_per_100']
                                      if theory else None),
        })
    return rows


def _width_match(row, width_mm):
    if width_mm is None:
        return 'any'
    band = int(width_mm) // 10
    if row['width_band'] == band:
        return 'exact'
    if abs(row['width_band'] - band) <= 1:
        return 'near'
    return 'far'


# ---------- the recommendation (design §3 + ranking policy) ------------------

def recommend(product, width_mm=None):
    """The complete, explainable recommendation set for one product.
    Proven beats theory, ALWAYS (ranking policy §2/§3)."""
    rows = _marker_rows(product)
    for r in rows:
        r['width_match'] = _width_match(r, width_mm)
    scoped = [r for r in rows if r['width_match'] != 'far'] or rows
    width_fallback = bool(width_mm) and any(r['width_match'] == 'far'
                                            for r in rows) and not any(
        r['width_match'] in ('exact', 'near') for r in rows)

    proven = sorted(
        (r for r in scoped if r['actual_m_per_100'] is not None),
        key=lambda r: (r['actual_m_per_100'], -r['n'],
                       -(r['last_used_at'].timestamp()
                         if r['last_used_at'] else 0)))
    untested = sorted(
        (r for r in scoped if r['actual_m_per_100'] is None),
        key=lambda r: (r['theoretical_m_per_100'] is None,
                       r['theoretical_m_per_100'] or 0))

    best = proven[0] if proven else None
    baseline = _current_practice(scoped)
    saving = _saving(best, baseline)
    return {
        'advisor_version': ADVISOR_VERSION,
        'product_id': product.pk,
        'width_mm': int(width_mm) if width_mm else None,
        'width_fallback_used': width_fallback,
        'best': best,
        'proven': proven,
        'untested': untested,
        'current_practice': baseline,
        'saving': saving,
        'width_advice': _width_advice(rows),
        'ratio_evidence': _ratio_evidence(proven[:3]),
        'confidence': _confidence(best, width_mm) if best else None,
        'geometry_trust': _geometry_trust(product),
        'no_facts': best is None,
    }


def _current_practice(rows):
    """What the factory ACTUALLY reaches for: most non-voided usages;
    tie -> most recent use (design ranking policy §4)."""
    used = [r for r in rows if r['usage_count'] > 0]
    if not used:
        return None
    return max(used, key=lambda r: (r['usage_count'],
                                    r['last_used_at'].timestamp()
                                    if r['last_used_at'] else 0))


def _saving(best, baseline):
    if not best or not baseline or baseline['actual_m_per_100'] is None:
        return None
    if baseline['reference'] == best['reference']:
        return {'already_best': True}
    delta = baseline['actual_m_per_100'] - best['actual_m_per_100']
    if delta <= 0:
        return {'already_best': True}
    return {'already_best': False,
            'baseline_reference': baseline['reference'],
            'baseline_m_per_100': baseline['actual_m_per_100'],
            'delta_m_per_100': q2(delta),
            'pct': q2(delta / baseline['actual_m_per_100'] * 100)}


def _width_advice(rows):
    """Per width band: the best PROVEN consumption (design §3.2)."""
    bands = {}
    for r in rows:
        if r['actual_m_per_100'] is None:
            continue
        b = bands.setdefault(r['width_band'], [])
        b.append(r)
    out = []
    for band, rs in bands.items():
        best = min(rs, key=lambda r: r['actual_m_per_100'])
        out.append({'width_band': band,
                    'width_mm_example': best['width_mm'],
                    'best_reference': best['reference'],
                    'best_m_per_100': best['actual_m_per_100'],
                    'n': best['n']})
    out.sort(key=lambda w: w['best_m_per_100'])
    return out


def _ratio_evidence(top_proven):
    """Report the ratios the winners actually ran — evidence, not invention
    (design §3.3)."""
    out = []
    for r in top_proven:
        if r['ratio_counts']:
            out.append({'reference': r['reference'],
                        'ratio_counts': r['ratio_counts'],
                        'm_per_100': r['actual_m_per_100'], 'n': r['n']})
    return out


def _confidence(best, width_mm):
    """Component-visible, weakest-component composite (house law).
    Display only — never an acceptance authority."""
    from django.utils import timezone
    n = best['n']
    depth = min(1.0, n / 5.0)
    if best['last_used_at']:
        days = (timezone.now() - best['last_used_at']).days
        recency = max(0.0, 1.0 - days / 180.0)
    else:
        recency = 0.0
    spread = _consistency(best)
    wm = {'exact': 1.0, 'near': 0.7, 'any': 0.85, 'far': 0.3}[
        best['width_match']]
    comp = {'evidence_depth': round(depth, 2),
            'recency': round(recency, 2),
            'consistency': round(spread, 2),
            'width_match': round(wm, 2)}
    return {'components': comp,
            'composite': int(round(100 * min(comp.values()))),
            'note': 'weakest-component score; display only — the human decides'}


def _consistency(best):
    """Spread of the winner's per-outcome m/100 around its mean."""
    from . import marker_feedback_service as fb
    from . import marker_query_service as q
    vals = [row['metrics']['meters_per_100']
            for row in q.get_marker_outcomes(best['marker'])
            if row['metrics']['valid']
            and row['metrics']['meters_per_100'] is not None]
    if len(vals) <= 1:
        return 0.5 if vals else 0.0        # one point: middling by honesty
    mean = sum(vals) / len(vals)
    if mean == 0:
        return 0.0
    worst = max(abs(v - mean) for v in vals)
    return max(0.0, 1.0 - float(worst / mean))


def _geometry_trust(product):
    """Provenance context: how trustworthy is this product's geometry era
    (P2 trust grades on the latest confirmed versions)."""
    from patterns_ai.models import PatternPiece, PatternPieceVersion
    grades = {'measured': 0, 'photo_calibrated': 0, 'uncalibrated': 0}
    pieces = 0
    for piece in PatternPiece.objects.filter(product=product):
        version = (piece.versions
                   .filter(status=PatternPieceVersion.Status.CONFIRMED)
                   .order_by('-version_no').first())
        if version is None:
            continue
        pieces += 1
        for row in version.size_geometries.all():
            grades[row.trust_grade] = grades.get(row.trust_grade, 0) + 1
    return {'confirmed_pieces': pieces, 'grade_counts': grades}


# ---------- the frozen offer snapshot (what suggestion_service records) ------

def offer_payload(recommendation):
    """Serializable snapshot of what was SHOWN — evidence included, model
    instances stripped (SuggestionEvent payload, schema_version'd)."""
    def slim(r):
        if r is None:
            return None
        return {'reference': r['reference'], 'origin': str(r['origin']),
                'width_mm': r['width_mm'],
                'actual_m_per_100': _s(r['actual_m_per_100']),
                'theoretical_m_per_100': _s(r['theoretical_m_per_100']),
                'n': r['n'], 'usage_count': r['usage_count'],
                'width_match': r.get('width_match')}
    rec = recommendation
    return {
        'schema_version': 1,
        'advisor_version': rec['advisor_version'],
        'width_mm': rec['width_mm'],
        'best': slim(rec['best']),
        'proven': [slim(r) for r in rec['proven'][:5]],
        'untested': [slim(r) for r in rec['untested'][:5]],
        'current_practice': slim(rec['current_practice']),
        'saving': _jsonable(rec['saving']),
        'width_advice': _jsonable(rec['width_advice']),
        'ratio_evidence': _jsonable(rec['ratio_evidence']),
        'confidence': rec['confidence'],
        'geometry_trust': rec['geometry_trust'],
        'no_facts': rec['no_facts'],
    }


def _s(v):
    return str(v) if v is not None else None


def _jsonable(obj):
    from decimal import Decimal
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, Decimal):
        return str(obj)
    return obj
