"""intelligence_service — Management Insights. **READ-ONLY** (P5 §2).

Composes EXISTING derive paths only — advisor_service (saving/practice),
marker_query_service (yield truth), P3 candidate metrics, SuggestionEvent
counts. No new math homes, no stored aggregates, no jobs: every number on
the dashboard re-derives from immutable facts at read (SELECT-only,
test-walled) and is explainable back to fact rows.
"""
from collections import OrderedDict

from django.utils import timezone

from . import advisor_service as adv
from . import marker_query_service as q
from .units import q2


def product_rows():
    """One insight row per product that owns markers: best-proven vs
    current practice, POTENTIAL saving (labeled), untested count."""
    from production.models import Product
    rows = []
    products = (Product.objects
                .filter(is_active=True, markers__isnull=False)
                .distinct().order_by('code'))
    for product in products:
        rec = adv.recommend(product)
        best = rec['best']
        rows.append({
            'product': product,
            'best_reference': best['reference'] if best else None,
            'best_m_per_100': best['actual_m_per_100'] if best else None,
            'best_n': best['n'] if best else 0,
            'practice_reference': (rec['current_practice']['reference']
                                   if rec['current_practice'] else None),
            'saving': rec['saving'],
            'proven_count': len(rec['proven']),
            'untested_count': len(rec['untested']),
            'confidence': (rec['confidence']['composite']
                           if rec['confidence'] else None),
        })
    return rows


def origin_comparison():
    """Manual vs generated — PROVEN reality only, by origin (the honest
    comparison; theory never enters)."""
    from patterns_ai.models import Marker
    buckets = {}
    for m in (Marker.objects.filter(status__in=adv.USABLE_STATUSES)
              .select_related('product')):
        s = q.get_marker_summary(m)
        b = buckets.setdefault(str(m.origin), {
            'markers': 0, 'with_reality': 0, 'values': []})
        b['markers'] += 1
        if s['avg_meters_per_100'] is not None:
            b['with_reality'] += 1
            b['values'].append(s['avg_meters_per_100'])
    out = []
    for origin, b in sorted(buckets.items()):
        avg = (q2(sum(b['values']) / len(b['values']))
               if b['values'] else None)
        out.append({'origin': origin, 'markers': b['markers'],
                    'with_reality': b['with_reality'],
                    'avg_m_per_100': avg})
    return out


def suggestion_stats():
    """The decision spine: all-time counts via ONE aggregate query
    (append-only tables grow forever — no full-python scans in a
    dashboard), plus the honest follow-up for the 10 most recent ACCEPTED
    suggestions: what did the shown-best marker's reality do SINCE?"""
    from django.db.models import Count
    from patterns_ai.models import Marker, SuggestionEvent
    counts = {'offered': 0, 'accepted': 0, 'modified': 0, 'rejected': 0}
    for row in (SuggestionEvent.objects.values('outcome')
                .annotate(c=Count('id'))):
        counts[row['outcome']] = row['c']
    accepted_followups = []
    recent_accepted = (SuggestionEvent.objects
                       .filter(outcome=SuggestionEvent.Outcome.ACCEPTED)
                       .select_related('product', 'decided_by')
                       .order_by('-id')[:10])
    for ev in recent_accepted:
        best = (ev.payload or {}).get('best') or {}
        ref = best.get('reference')
        follow = None
        if ref and ev.decided_at:
            marker = Marker.objects.filter(reference=ref).first()
            if marker:
                vals = [row['metrics']['meters_per_100']
                        for row in q.get_marker_outcomes(marker)
                        if row['metrics']['valid']
                        and row['metrics']['meters_per_100'] is not None
                        and row['outcome'].created_at >= ev.decided_at]
                if vals:
                    follow = {'n': len(vals),
                              'avg_m_per_100': q2(sum(vals) / len(vals))}
        accepted_followups.append({
            'event': ev, 'shown_reference': ref,
            'shown_m_per_100': best.get('actual_m_per_100'),
            'since': follow})
    decided = counts['accepted'] + counts['modified'] + counts['rejected']
    rate = q2(counts['accepted'] / decided * 100) if decided else None
    return {'counts': counts, 'decided': decided,
            'acceptance_rate_pct': rate,
            'accepted_followups': accepted_followups}


def factory_kpis():
    """Census chips — plain counts over immutable rows."""
    from patterns_ai.models import (CalibrationMat, CaptureAsset,
                                    GeneratedMarkerCandidate, Marker,
                                    MarkerGenerationRun, MarkerOutcome,
                                    MarkerUsage, PieceSizeGeometry)
    grades = {'measured': 0, 'photo_calibrated': 0, 'uncalibrated': 0}
    for row in PieceSizeGeometry.objects.all():
        grades[row.trust_grade] = grades.get(row.trust_grade, 0) + 1
    return {
        'markers_total': Marker.objects.count(),
        'markers_generated': Marker.objects.filter(
            origin=Marker.Origin.GENERATED).count(),
        'usages': MarkerUsage.objects.filter(voided_at__isnull=True).count(),
        'outcomes': MarkerOutcome.objects.count(),
        'captures': CaptureAsset.objects.count(),
        'geometry_rows': PieceSizeGeometry.objects.count(),
        'trust_grades': grades,
        'mats_active': CalibrationMat.objects.filter(status='active').count(),
        'generation_runs': MarkerGenerationRun.objects.count(),
        'candidates': GeneratedMarkerCandidate.objects.count(),
    }


def outcome_trend(months=6):
    """Outcomes recorded per month (simple honest buckets, newest last)."""
    from patterns_ai.models import MarkerOutcome
    now = timezone.localtime()
    buckets = OrderedDict()
    for i in range(months - 1, -1, -1):
        y = now.year
        m = now.month - i
        while m <= 0:
            m += 12
            y -= 1
        buckets[f'{y}-{m:02d}'] = 0
    # append-only table: bound the scan to the window (no full scans in
    # a dashboard as years accumulate)
    from datetime import timedelta
    since = now - timedelta(days=31 * months + 5)
    for o in MarkerOutcome.objects.filter(created_at__gte=since):
        # Bucket keys above are built from LOCAL time, so the fill must be local
        # too — `created_at.month` is the UTC month and disagrees with the key for
        # 5.5h every day (docs/UTC_LOCAL_DATE_BUG_CLASS_2026_08_01.md).
        created_local = timezone.localtime(o.created_at)
        key = f'{created_local.year}-{created_local.month:02d}'
        if key in buckets:
            buckets[key] += 1
    peak = max(buckets.values()) if buckets else 0
    return [{'month': k, 'count': v,
             'bar_pct': int(v / peak * 100) if peak else 0}
            for k, v in buckets.items()]


def executive_dashboard():
    return {'kpis': factory_kpis(),
            'products': product_rows(),
            'origins': origin_comparison(),
            'suggestions': suggestion_stats(),
            'trend': outcome_trend()}
