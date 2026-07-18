"""marker_query_service — READ-ONLY biography + query helpers (Block 2C).

Why this service exists: the marker biography is a read model composed from
append-only sources (transition events, usages, outcomes, lineage). It writes
NOTHING — test-enforced. Derived numbers reuse marker_feedback_service
(no math duplication; one METRICS_VERSION).
"""
from django.db.models import Q

from patterns_ai.models import Marker, MarkerOutcome, MarkerUsage
from . import marker_feedback_service as fb


def get_marker_usage_history(marker):
    """All usages (voided included, flagged) — newest last."""
    return list(
        MarkerUsage.objects.filter(marker=marker)
        .select_related('adda', 'confirmed_by').order_by('id'))


def get_marker_outcomes(marker):
    """Outcome facts + derived-at-read metrics per non-voided usage."""
    outcomes = (MarkerOutcome.objects
                .filter(usage__marker=marker)
                .select_related('usage', 'recorded_by').order_by('usage_id'))
    return [{'outcome': o,
             'metrics': fb.derive_metrics(o)} for o in outcomes]


def get_marker_lineage(marker):
    """Backward + forward lineage and benchmark relations."""
    back = []
    node = marker.supersedes
    while node is not None:
        back.append(node)
        node = node.supersedes
    forward = list(Marker.objects.filter(supersedes=marker).order_by('id'))
    return {
        'supersedes_chain': back,                       # oldest ancestor last
        'superseded_by': forward,
        'benchmarked_against': marker.benchmarked_against,
        'benchmark_children': list(marker.benchmark_children.order_by('id')),
    }


def get_marker_biography(marker):
    """The complete lifecycle timeline, oldest first.

    Entries: {'at', 'kind', 'detail', ...} composed from transition events
    (creation included), usages (+voids), and recorded outcomes. Pure read.
    """
    entries = []
    for ev in marker.transition_events.select_related('actor').order_by('id'):
        entries.append({
            'at': ev.created_at, 'kind': 'transition',
            'from': ev.from_status or None, 'to': ev.to_status,
            'actor': ev.actor, 'reason': ev.reason,
            'transition_version': ev.transition_version,
        })
    for u in get_marker_usage_history(marker):
        entries.append({'at': u.created_at, 'kind': 'usage',
                        'adda': u.adda, 'plies': u.plies, 'repeats': u.repeats,
                        'actor': u.confirmed_by, 'voided': u.voided_at is not None})
        if u.voided_at is not None:
            entries.append({'at': u.voided_at, 'kind': 'usage_void',
                            'reason': u.void_reason, 'adda': u.adda})
    for row in get_marker_outcomes(marker):
        o = row['outcome']
        entries.append({'at': o.created_at, 'kind': 'outcome',
                        'actor': o.recorded_by, 'metrics': row['metrics']})
    entries.sort(key=lambda e: e['at'])
    return entries


def get_marker_summary(marker):
    """One-glance card data: status, activity counts, honest averages.

    Averages reuse derive_metrics (no second math home); only VALID (non-void)
    outcomes with both facts present participate; n is always exposed.
    """
    usages = get_marker_usage_history(marker)
    active = [u for u in usages if u.voided_at is None]
    per100 = [row['metrics']['meters_per_100']
              for row in get_marker_outcomes(marker)
              if row['metrics']['valid'] and row['metrics']['meters_per_100'] is not None]
    avg = avg_per_garment = None
    if per100:
        from .units import q2
        avg = q2(sum(per100) / len(per100))
        avg_per_garment = q2(avg / 100)
    return {
        'reference': marker.reference,
        'status': marker.status,
        'origin': marker.origin,
        'usable_width_band': marker.usable_width_band,
        'usage_count': len(active),
        'voided_usage_count': len(usages) - len(active),
        'outcome_count': len(per100),
        'avg_meters_per_100': avg,          # None until n ≥ 1 — honest
        'avg_meters_per_garment': avg_per_garment,
        'n_for_average': len(per100),
        'last_used_at': active[-1].created_at if active else None,
    }


def get_product_yield_board(product, sort='avg'):
    """The Yield Board (Block 3E): one row per marker of `product`, every
    number DERIVED AT READ from usage/outcome facts via get_marker_summary —
    nothing stored, nothing cached (V3 F6). SELECT-only like everything here.

    sort: 'avg' (best m/100 first, honest-NULLs last) · 'usage' · 'recent' ·
    'reference'.
    """
    rows = []
    markers = (Marker.objects.filter(product=product)
               .select_related('photo').order_by('id'))
    for m in markers:
        s = get_marker_summary(m)
        rows.append({'marker': m, **s})

    if sort == 'usage':
        rows.sort(key=lambda r: (-r['usage_count'], r['reference']))
    elif sort == 'recent':
        import datetime
        from django.utils import timezone
        epoch = timezone.make_aware(datetime.datetime(1970, 1, 1))
        rows.sort(key=lambda r: (r['last_used_at'] or epoch, r['reference']),
                  reverse=True)
    elif sort == 'reference':
        rows.sort(key=lambda r: r['reference'])
    else:                                   # 'avg' — best consumption first
        rows.sort(key=lambda r: (r['avg_meters_per_100'] is None,
                                 r['avg_meters_per_100'] or 0,
                                 r['reference']))
    return rows
