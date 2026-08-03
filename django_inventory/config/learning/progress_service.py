"""learning.progress_service — the ONLY writer of LessonProgress + Bookmark.

Single-writer discipline (CLAUDE.md rule 5): views call these functions, never
`Model.objects.create` directly. Keeps the "one place to be right" property that
the money services already have.

Everything here is per-user. Reads never leak across users: every query is
filtered by `user` first, and there is no code path that takes a user id from
the request body.
"""
from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from learning import services
from learning.models import Bookmark, LessonProgress


# ── writes ──────────────────────────────────────────────────────────────────
@transaction.atomic
def mark_opened(user, course_slug: str, chapter_slug: str) -> LessonProgress:
    """Record that the learner opened a chapter. Idempotent-ish: it bumps a
    counter, so it is safe to call on every page view."""
    row, created = LessonProgress.objects.get_or_create(
        user=user, course_slug=course_slug, chapter_slug=chapter_slug,
        defaults={'open_count': 1})
    if not created:
        # F() would avoid a read, but we already have the row and need it back.
        row.open_count += 1
        row.save(update_fields=['open_count', 'last_opened_at', 'updated_at'])
    return row


@transaction.atomic
def set_complete(user, course_slug: str, chapter_slug: str, *, done: bool) -> bool:
    """Mark a chapter finished / unfinished. Returns the new state.

    Un-completing is allowed on purpose: this is a learning aid, not an audit
    ledger. (Contrast with money — see docs/sql_course ch 12: THERE, nothing is
    ever edited. Knowing which rules apply where is the point.)
    """
    row, _ = LessonProgress.objects.get_or_create(
        user=user, course_slug=course_slug, chapter_slug=chapter_slug)
    row.completed_at = timezone.now() if done else None
    row.save(update_fields=['completed_at', 'last_opened_at', 'updated_at'])
    return row.is_complete


@transaction.atomic
def toggle_bookmark(user, course_slug: str, chapter_slug: str) -> bool:
    """Star / un-star a chapter. Returns True if it is now bookmarked."""
    existing = Bookmark.objects.filter(
        user=user, course_slug=course_slug, chapter_slug=chapter_slug).first()
    if existing:
        existing.delete()
        return False
    Bookmark.objects.create(user=user, course_slug=course_slug,
                            chapter_slug=chapter_slug)
    return True


# ── reads ───────────────────────────────────────────────────────────────────
def chapter_state(user, course_slug: str, chapter_slug: str) -> dict:
    if not user.is_authenticated:
        return {'complete': False, 'bookmarked': False}
    row = LessonProgress.objects.filter(
        user=user, course_slug=course_slug, chapter_slug=chapter_slug).first()
    return {
        'complete': bool(row and row.is_complete),
        'bookmarked': Bookmark.objects.filter(
            user=user, course_slug=course_slug,
            chapter_slug=chapter_slug).exists(),
    }


def course_progress(user, course_slug: str) -> dict:
    """Completion for one course: {done, total, percent, done_slugs}."""
    chapters = services.chapters_for(course_slug)
    total = len(chapters)
    if not user.is_authenticated or not total:
        return {'done': 0, 'total': total, 'percent': 0, 'done_slugs': set()}
    valid = {c.slug for c in chapters}
    done_slugs = set(
        LessonProgress.objects
        .filter(user=user, course_slug=course_slug, completed_at__isnull=False)
        .values_list('chapter_slug', flat=True)
    ) & valid          # unknown slugs (renamed chapters) simply don't count
    done = len(done_slugs)
    return {'done': done, 'total': total,
            'percent': round(done * 100 / total), 'done_slugs': done_slugs}


def chapter_states(user, course_slug: str) -> dict:
    """{chapter_slug: 'done'|'reading'|'new'} — the three states the nav shows.

    Returning a dict (not a set) is what lets the course page distinguish
    "started but unfinished" from "never opened", which a boolean cannot.
    """
    if not user.is_authenticated:
        return {}
    return {r.chapter_slug: r.state for r in LessonProgress.objects.filter(
        user=user, course_slug=course_slug)}


def resume_point(user) -> dict | None:
    """The 'Continue learning' card: the most recently opened chapter that is
    still a real chapter. Returns None for a learner who has not started."""
    if not user.is_authenticated:
        return None
    for row in (LessonProgress.objects.filter(user=user)
                .order_by('-last_opened_at')[:20]):
        ref = services.find_chapter(row.course_slug, row.chapter_slug)
        if ref is None:
            continue           # chapter was renamed/removed — skip, don't crash
        from learning.registry import COURSES_BY_SLUG
        course = COURSES_BY_SLUG.get(row.course_slug)
        if course is None:
            continue
        return {'course': course, 'chapter': ref,
                'complete': row.is_complete,
                'progress': course_progress(user, row.course_slug)}
    return None


@transaction.atomic
def add_time(user, course_slug: str, chapter_slug: str, *,
             seconds: int, scroll: int | None = None) -> None:
    """Accumulate reading time from the page heartbeat.

    Clamped hard: a single beat may add at most 120s, so a tab left open
    overnight (or a forged request) cannot invent hours of "study time". This is
    a motivation metric, not an audit trail — it should be roughly right and
    impossible to abuse into nonsense.
    """
    seconds = max(0, min(int(seconds or 0), 120))
    row = LessonProgress.objects.filter(
        user=user, course_slug=course_slug, chapter_slug=chapter_slug).first()
    if row is None:
        return                          # never seen the chapter — nothing to add
    fields = []
    if seconds:
        row.seconds_spent = row.seconds_spent + seconds
        fields.append('seconds_spent')
    if scroll is not None:
        pct = max(0, min(int(scroll), 100))
        if pct > row.scroll_percent:    # furthest point reached, never backwards
            row.scroll_percent = pct
            fields.append('scroll_percent')
    if fields:
        row.save(update_fields=fields + ['last_opened_at', 'updated_at'])


def _fmt_duration(seconds: int) -> str:
    if seconds < 60:
        return f'{seconds}s'
    if seconds < 3600:
        return f'{seconds // 60}m'
    return f'{seconds // 3600}h {(seconds % 3600) // 60}m'


def dashboard(user) -> dict:
    """Everything the personalised dashboard needs, in ONE pass over the rows.

    Deliberately DERIVED, not stored: active/completed courses, remaining
    lessons, learning days and weekly activity are all functions of
    LessonProgress. Storing them too would create a second source of truth that
    can drift — the same mistake the content layer forbids. Only facts that
    cannot be derived (time spent, an explicit mark) get their own column.
    """
    from learning.registry import COURSES
    if not user.is_authenticated:
        return {'active': [], 'completed': [], 'stats': {}, 'week': [],
                'recent': [], 'recommended': None}

    rows = list(LessonProgress.objects.filter(user=user))
    by_course: dict[str, list] = {}
    for r in rows:
        by_course.setdefault(r.course_slug, []).append(r)

    active, completed = [], []
    for course in COURSES:
        prog = course_progress(user, course.slug)
        if not prog['done'] and course.slug not in by_course:
            continue                                  # never started
        item = {'course': course, 'progress': prog,
                'remaining': prog['total'] - prog['done'],
                'seconds': sum(r.seconds_spent for r in by_course.get(course.slug, [])),
                'time': _fmt_duration(sum(r.seconds_spent
                                          for r in by_course.get(course.slug, [])))}
        (completed if prog['percent'] >= 100 else active).append(item)

    # Weekly activity: one bucket per day for the last 7 days.
    today = timezone.localdate()
    opened = {}
    for r in rows:
        d = timezone.localtime(r.last_opened_at).date()
        opened[d] = opened.get(d, 0) + 1
    week = [{'date': today - timedelta(days=i),
             'count': opened.get(today - timedelta(days=i), 0),
             'label': (today - timedelta(days=i)).strftime('%a')}
            for i in range(6, -1, -1)]

    recent = []
    for r in sorted(rows, key=lambda x: x.last_opened_at, reverse=True)[:6]:
        ref = services.find_chapter(r.course_slug, r.chapter_slug)
        from learning.registry import COURSES_BY_SLUG
        c = COURSES_BY_SLUG.get(r.course_slug)
        if ref and c:
            recent.append({'course': c, 'chapter': ref, 'state': r.state,
                           'at': r.last_opened_at})

    total_seconds = sum(r.seconds_spent for r in rows)
    return {
        'active': active, 'completed': completed, 'week': week, 'recent': recent,
        'recommended': recommended_next(user),
        'stats': {
            **learning_stats(user),
            'learning_days': len({timezone.localtime(r.last_opened_at).date()
                                  for r in rows}),
            'time_spent': _fmt_duration(total_seconds),
            'seconds_spent': total_seconds,
            'courses_started': len(active) + len(completed),
        },
    }


def recommended_next(user) -> dict | None:
    """The next unfinished chapter of the course you are furthest into.

    Simple and explainable on purpose — a recommendation the learner cannot
    predict is a recommendation they will not trust.
    """
    from learning.registry import COURSES
    best = None
    for course in COURSES:
        prog = course_progress(user, course.slug)
        if prog['total'] and prog['done'] and prog['percent'] < 100:
            if best is None or prog['percent'] > best[1]['percent']:
                best = (course, prog)
    if best is None:
        return None
    course, prog = best
    for ref in services.chapters_for(course.slug):
        if ref.slug not in prog['done_slugs']:
            return {'course': course, 'chapter': ref, 'progress': prog}
    return None


def learning_stats(user) -> dict:
    """Dashboard numbers: chapters finished, bookmarks, and the current streak."""
    if not user.is_authenticated:
        return {'completed': 0, 'bookmarks': 0, 'streak': 0}
    qs = LessonProgress.objects.filter(user=user, completed_at__isnull=False)
    # Streak = consecutive days (counting back from today) on which the learner
    # opened at least one chapter. Cheap enough at this scale; if the table ever
    # grows large this becomes a single GROUP BY date query.
    days = set(
        LessonProgress.objects.filter(user=user)
        .values_list('last_opened_at', flat=True))
    seen = {timezone.localdate(d) for d in days if d}
    streak, day = 0, timezone.localdate()
    while day in seen:
        streak += 1
        day -= timedelta(days=1)
    return {
        'completed': qs.count(),
        'bookmarks': Bookmark.objects.filter(user=user).count(),
        'streak': streak,
    }


def bookmarks_for(user) -> list[dict]:
    if not user.is_authenticated:
        return []
    from learning.registry import COURSES_BY_SLUG
    out = []
    for bm in Bookmark.objects.filter(user=user).order_by('-created_at')[:50]:
        ref = services.find_chapter(bm.course_slug, bm.chapter_slug)
        course = COURSES_BY_SLUG.get(bm.course_slug)
        if ref and course:
            out.append({'course': course, 'chapter': ref, 'at': bm.created_at})
    return out
