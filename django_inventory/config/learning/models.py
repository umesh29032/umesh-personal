"""learning.models — USER STATE only. Never content.

THE LINE THIS FILE MUST NOT CROSS (docs/LEARNING_PLATFORM_VISION.md §2):
    Knowledge lives in markdown. Progress lives here.
    If a chapter's TEXT ever appears in a column, the core law is broken.

Why the content is referenced by STRING slugs and not a ForeignKey:
    there is no content table to point at — and there must never be one. Keying
    on (course_slug, chapter_slug) also keeps these rows portable: content can be
    re-organised, exported, or served by a different deployment without a
    migration, which §11 (commercial readiness) requires us not to block.
    The cost is honest: a renamed chapter orphans its progress rows. That is the
    trade, and `learning/services.py` treats unknown slugs as "not started"
    rather than erroring.
"""
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class LessonProgress(TimeStampedModel):
    """One row per (user, chapter) — the atom of everything on the dashboard.

    Completion percentages, resume point, streak and "recently completed" are
    all READS over this table. Deliberately one table rather than four: a
    learner's relationship with a chapter is a single fact with a few fields.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='lesson_progress')
    # Content coordinates as strings — see the module docstring.
    course_slug = models.CharField(max_length=64)
    chapter_slug = models.CharField(max_length=160)

    # NULL = opened but not finished. Honest-NULL, not a fake boolean+timestamp
    # pair (the project's NULL policy — see docs/sql_course ch 04).
    completed_at = models.DateTimeField(null=True, blank=True)
    last_opened_at = models.DateTimeField(auto_now=True)
    open_count = models.PositiveIntegerField(default=0)
    # Time on the page, accumulated from the reader's heartbeat. Stored per
    # lesson (not per session) because "how long did this chapter take me" is
    # the useful question, and it sums cleanly to a course/global total.
    seconds_spent = models.PositiveIntegerField(default=0)
    # How far down the chapter the reader got, 0-100. Lets the UI say
    # "in progress · 60%" instead of a binary started/finished.
    scroll_percent = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'course_slug', 'chapter_slug'],
                name='learning_one_progress_row_per_user_chapter'),
        ]
        indexes = [
            # the dashboard's two hot reads: "my progress in this course" and
            # "what was I last reading?"
            models.Index(fields=['user', 'course_slug'],
                         name='learning_prog_user_course_idx'),
            models.Index(fields=['user', '-last_opened_at'],
                         name='learning_prog_user_recent_idx'),
        ]
        verbose_name_plural = 'lesson progress'

    def __str__(self) -> str:
        state = 'done' if self.completed_at else 'in progress'
        return f'{self.user_id}: {self.course_slug}/{self.chapter_slug} ({state})'

    @property
    def is_complete(self) -> bool:
        return self.completed_at is not None

    @property
    def state(self) -> str:
        """The three states the UI shows: done · reading · new."""
        if self.completed_at:
            return 'done'
        return 'reading' if self.open_count else 'new'


class Bookmark(TimeStampedModel):
    """A chapter the learner wants to come back to. Separate from progress
    because "I marked this" and "I read this" are different facts — merging them
    would make un-bookmarking ambiguous with un-completing.

    `kind` lets one table serve bookmarks AND favourites (and any future flag)
    without another migration — the owner's follow-up lists both.
    """

    class Kind(models.TextChoices):
        BOOKMARK = 'bookmark', 'Bookmark'
        FAVOURITE = 'favourite', 'Favourite'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='learning_bookmarks')
    course_slug = models.CharField(max_length=64)
    chapter_slug = models.CharField(max_length=160)
    kind = models.CharField(max_length=16, choices=Kind.choices,
                            default=Kind.BOOKMARK)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'course_slug', 'chapter_slug', 'kind'],
                name='learning_one_mark_per_user_chapter_kind'),
        ]
        indexes = [
            models.Index(fields=['user', '-created_at'],
                         name='learning_bm_user_recent_idx'),
        ]

    def __str__(self) -> str:
        return f'{self.user_id}: ★ {self.course_slug}/{self.chapter_slug}'
