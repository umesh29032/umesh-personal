"""learning.registry — WHICH markdown folders are courses, and in what order.

THE ONE ARCHITECTURAL RULE OF THIS APP:
    The markdown files in docs/ are the SINGLE SOURCE OF TRUTH.
    This app READS them and renders HTML. It never stores a second copy.
    Edit the .md → the website changes. There is nothing to keep in sync,
    so the courses can never drift from the docs (the failure this project
    has already paid for once — see docs/FRESH_DB_REQUIREMENTS.md §6).

Adding a future course is ONE entry here plus a folder of .md files.
No models, no migrations, no data entry.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

# docs/ sits beside config/ at the repo root: BASE_DIR is .../django_inventory/config
DOCS_ROOT = Path(settings.BASE_DIR).parent / 'docs'

# Chapter files are named NN_Title.md (00_ = the course overview / index).
# 00A_/00B_ variants exist in the deployment course, hence the optional letter.
_CHAPTER_RE = re.compile(r'^(\d{2}[A-Z]?)_(.+)\.md$')

# Un-numbered reference pages that belong to a course but sit outside the
# chapter sequence (e.g. the deployment course's ARCHITECTURE.md). They are
# listed after the chapters rather than dropped — losing a page silently is
# worse than showing it out of order.
_EXTRA_PAGES = {'ARCHITECTURE.md'}


@dataclass(frozen=True)
class Course:
    slug: str            # URL segment: /learn/<slug>/
    folder: str          # directory under docs/
    title: str
    tagline: str
    icon: str            # emoji — cheap, zero-asset, renders everywhere
    level: str           # who it is for
    accent: str          # CSS accent colour token for the course card


# Ordered: the order they appear on /learn/.
COURSES: tuple[Course, ...] = (
    Course(
        slug='sql',
        folder='sql_course',
        title='SQL & PostgreSQL From Zero',
        tagline='What a database really is, taught from this factory’s own tables — '
                'every example is a real query with its real output.',
        icon='🗄️',
        level='Absolute beginner → interview-ready',
        accent='#2d6a4f',
    ),
    Course(
        slug='deployment',
        folder='deployment_course',
        title='Deployment From Zero',
        tagline='Laptop to live server: the internet, Linux, Docker, Caddy, '
                'Gunicorn, Postgres, backups — using this project’s real deploy files.',
        icon='🚀',
        level='Absolute beginner → production-capable',
        accent='#8b5a2b',
    ),
)

COURSES_BY_SLUG = {c.slug: c for c in COURSES}


@dataclass(frozen=True)
class ChapterRef:
    number: str          # "07"  (string: preserves leading zero and 00A/00B variants)
    slug: str            # "07-joins" — URL-safe, derived from the filename
    filename: str
    title: str           # from the file's own H1, falling back to the filename
    is_overview: bool    # the 00_* file


def _title_from_filename(stem: str) -> str:
    return stem.replace('_', ' ').strip()


def chapter_files(course: Course) -> list[Path]:
    """Every page of a course: numbered chapters in teaching order, then any
    un-numbered reference pages. Nothing in the folder is silently dropped."""
    folder = DOCS_ROOT / course.folder
    if not folder.is_dir():
        return []
    numbered, extra = [], []
    for p in sorted(folder.glob('*.md')):
        if _CHAPTER_RE.match(p.name):
            numbered.append(p)
        elif p.name in _EXTRA_PAGES:
            extra.append(p)
    return numbered + extra


def slug_for(filename: str) -> str:
    """`07_JOINs.md` -> `07-joins`. Stable, readable, URL-safe."""
    m = _CHAPTER_RE.match(filename)
    if not m:
        return filename.removesuffix('.md').lower()
    num, rest = m.groups()
    body = re.sub(r'[^a-z0-9]+', '-', rest.lower()).strip('-')
    return f'{num.lower()}-{body}'
