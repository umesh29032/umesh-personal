"""learning.services — read a markdown chapter and turn it into a rendered page.

Zero models. Zero writes. This module is a pure function of the files on disk:
    markdown file  ──▶  {title, html, sections, prev, next}

Rendering stack (both ALREADY installed — no new dependency):
    markdown-it-py  CommonMark parser (+ table plugin)
    Pygments        syntax highlighting for fenced code blocks

Safety: `html=False` on the parser, so raw HTML inside a .md is escaped rather
than executed. Our own docs are trusted, but a renderer that executes whatever
is in a text file is a footgun waiting for the day someone pastes something.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from django.utils.safestring import mark_safe

from learning.registry import (
    COURSES, COURSES_BY_SLUG, Course, ChapterRef, chapter_files, slug_for,
)

# ── markdown → html ─────────────────────────────────────────────────────────
_H1_RE = re.compile(r'^#\s+(.+?)\s*$', re.M)
_FRONTMATTER_RE = re.compile(r'\A---\n(.*?)\n---\n', re.S)
# The 19 teaching sections are H1s in these files; we build the on-page TOC
# from them (and the interview-prep page harvests one of them by name).
# `(?!\d)` skips the file's own "# 14 — Indexes" title line.
_SECTION_RE = re.compile(r'^#\s+(?!\d)(.+?)\s*$', re.M)
# Fallback for the overview/reference pages, which section with H2.
_SUBSECTION_RE = re.compile(r'^##\s+(.+?)\s*$', re.M)


def _make_parser():
    from markdown_it import MarkdownIt

    def highlight(code: str, lang: str, _attrs) -> str:
        """Pygments-highlight a fenced block; fall back to plain <pre> on any
        unknown language so an ASCII diagram never breaks the page."""
        from pygments import highlight as pyg_highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import get_lexer_by_name
        from pygments.util import ClassNotFound
        try:
            lexer = get_lexer_by_name(lang)
        except ClassNotFound:
            return ''      # '' tells markdown-it to use its default escaping
        return pyg_highlight(code, lexer, HtmlFormatter(nowrap=False, cssclass='hl'))

    return (
        MarkdownIt('commonmark', {'html': False, 'linkify': True,
                                  'typographer': True, 'highlight': highlight})
        .enable('table')
        .enable('strikethrough')
    )


_MD = _make_parser()


def pygments_css() -> str:
    """The highlight stylesheet, inlined once per page (no extra HTTP request)."""
    from pygments.formatters import HtmlFormatter
    return HtmlFormatter(style='friendly').get_style_defs('.hl')


# ── chapter discovery ───────────────────────────────────────────────────────
def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def _strip_frontmatter(text: str) -> str:
    return _FRONTMATTER_RE.sub('', text, count=1)


def _first_h1(text: str, fallback: str) -> str:
    m = _H1_RE.search(text)
    return m.group(1).strip() if m else fallback


@lru_cache(maxsize=8)
def chapters_for(course_slug: str) -> tuple[ChapterRef, ...]:
    """Every chapter of a course, ordered, with titles read from the files.

    Cached because it stats+reads a few dozen small files; `reload_courses()`
    clears it so editing a .md shows up without restarting the server in dev.
    """
    course = COURSES_BY_SLUG[course_slug]
    refs = []
    for path in chapter_files(course):
        raw = _strip_frontmatter(_read(path))
        # Numbered chapters show their number in the badge; un-numbered
        # reference pages (ARCHITECTURE.md) show "REF" rather than a filename.
        head = path.name.split('_', 1)[0]
        num = head if head[:2].isdigit() else 'REF'
        refs.append(ChapterRef(
            number=num,
            slug=slug_for(path.name),
            filename=path.name,
            title=_first_h1(raw, path.stem.replace('_', ' ')),
            is_overview=num.startswith('00'),
        ))
    return tuple(refs)


def find_chapter(course_slug: str, chapter_slug: str) -> ChapterRef | None:
    for ref in chapters_for(course_slug):
        if ref.slug == chapter_slug:
            return ref
    return None


@dataclass
class RenderedChapter:
    course: Course
    ref: ChapterRef
    html: str
    sections: list[dict]      # [{title, anchor}] for the on-page TOC
    prev: ChapterRef | None
    next: ChapterRef | None
    reading_minutes: int


def _anchor(title: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')


def _rewrite_internal_links(html: str, course: Course) -> str:
    """Make the courses' own cross-links work as WEB links.

    The .md files link to each other by filename (`07_JOINs.md`) because they
    must stay readable in an editor and on GitHub. On the site those become
    real URLs, so every link is Ctrl+click-able into a new tab — which is
    exactly how the owner asked to read this.
    """
    def repl(m: re.Match) -> str:
        href = m.group(1)
        if href.endswith('.md'):
            fname = href.rsplit('/', 1)[-1]
            return f'href="/learn/{course.slug}/{slug_for(fname)}/"'
        return m.group(0)

    return re.sub(r'href="([^"]+\.md)"', repl, html)


def render_chapter(course_slug: str, chapter_slug: str) -> RenderedChapter | None:
    course = COURSES_BY_SLUG.get(course_slug)
    if course is None:
        return None
    ref = find_chapter(course_slug, chapter_slug)
    if ref is None:
        return None

    from learning.registry import DOCS_ROOT
    path = DOCS_ROOT / course.folder / ref.filename
    if not path.is_file():
        return None

    raw = _strip_frontmatter(_read(path))
    # Drop the leading H1 — the page renders its own hero title, so keeping it
    # would show the heading twice.
    body = _H1_RE.sub('', raw, count=1)
    # Drop the "> Part of … Prev: … Next: …" nav blockquote. It exists so the
    # .md stays navigable in an editor/on GitHub; on the site the hero
    # breadcrumb + prev/next buttons do that job better, and leaving it in
    # styles plain navigation as a 💡 teaching box.
    body = re.sub(r'\A\s*(?:^>.*\n)+', '', body, count=1, flags=re.M)
    html = _rewrite_internal_links(_MD.render(body), course)

    # Chapters section themselves with H1; the overview/reference pages use H2
    # as their top level. Use whichever level the page actually uses, so no
    # page is left with an empty table of contents.
    level, found = 1, _SECTION_RE.findall(body)
    if not found:
        level, found = 2, _SUBSECTION_RE.findall(body)
    sections = [{'title': t.strip(), 'anchor': _anchor(t)} for t in found]
    # Give each rendered heading an id so the TOC can jump to it.
    for s in sections:
        html = html.replace(f'<h{level}>{s["title"]}</h{level}>',
                            f'<h{level} id="{s["anchor"]}">{s["title"]}</h{level}>', 1)

    refs = chapters_for(course_slug)
    i = refs.index(ref)
    words = len(body.split())
    return RenderedChapter(
        course=course, ref=ref, html=mark_safe(html), sections=sections,
        prev=refs[i - 1] if i > 0 else None,
        next=refs[i + 1] if i + 1 < len(refs) else None,
        reading_minutes=max(1, round(words / 200)),
    )


def course_overview(course_slug: str) -> dict | None:
    course = COURSES_BY_SLUG.get(course_slug)
    if course is None:
        return None
    refs = chapters_for(course_slug)
    return {'course': course, 'chapters': refs, 'count': len(refs)}


def all_courses() -> list[dict]:
    out = []
    for c in COURSES:
        refs = chapters_for(c.slug)
        out.append({'course': c, 'count': len(refs),
                    'first': refs[0] if refs else None})
    return out


# ── interview prep: harvested from the chapters, never duplicated ───────────
# SPLIT, not match-per-line: an answer is usually wrapped over several lines
# (and sometimes starts on the line below the question). A `$`-anchored regex
# silently truncated those answers, and dropped 6 of them entirely.
_LEVEL_SPLIT_RE = re.compile(
    r'^-\s+\*\*(Junior|Mid|Senior|Staff):\*\*\s*', re.M)

LEVELS = ('Junior', 'Mid', 'Senior', 'Staff')


def _level_items(section: str) -> list[tuple[str, str]]:
    """[(level, 'question — answer'), …] from one Interview Questions section.

    Wrapped lines are collapsed to a single line so the em-dash split sees the
    whole answer, however the author laid it out in the .md.
    """
    parts = _LEVEL_SPLIT_RE.split(section)
    return [(parts[i], ' '.join(parts[i + 1].split()))
            for i in range(1, len(parts) - 1, 2)]


@lru_cache(maxsize=1)
def interview_questions() -> dict:
    """Every `**Level:** question — answer` bullet across every course.

    This is generated, not written twice: the chapters already label their
    interview questions by level, so the prep page is a VIEW over them. Fix a
    question in the chapter and this page fixes itself.
    """
    from learning.registry import DOCS_ROOT
    by_level = {lvl: [] for lvl in LEVELS}
    total = 0
    for c in COURSES:
        for ref in chapters_for(c.slug):
            raw = _strip_frontmatter(
                _read(DOCS_ROOT / c.folder / ref.filename))
            # Only harvest inside the Interview Questions section, so a stray
            # bold elsewhere cannot leak in. Reuses the ONE section extractor —
            # a private copy of this regex here silently lost ch 42, whose
            # heading carries a suffix.
            section = _section_body(raw, 'Interview Questions')
            if not section:
                continue
            for level, text in _level_items(section):
                q, _, a = text.partition('—')
                by_level[level].append({
                    'question': mark_safe(_MD.renderInline(q.strip())),
                    'answer': mark_safe(_MD.renderInline(a.strip())),
                    'course': c, 'chapter': ref,
                })
                total += 1
    # Shaped as an ordered list of groups so the template stays dumb — it needs
    # a per-level count, which a dict cannot give it without a custom filter.
    groups = [{'level': lvl, 'anchor': lvl.lower(),
               'questions': by_level[lvl], 'count': len(by_level[lvl])}
              for lvl in LEVELS]
    return {'groups': groups, 'total': total, 'levels': LEVELS}


# ── generic section harvest: the engine behind every generated page ─────────
def _section_body(raw: str, heading: str) -> str | None:
    """The text under `# <heading>...` up to the next H1, or None if absent.

    Prefix-tolerant on purpose: a chapter may enrich its heading
    (`# Beginner Mistakes (the greatest hits)`) and must still feed the
    generated pages. An exact-match regex silently dropped those chapters.
    """
    parts = re.split(rf'^#\s+{re.escape(heading)}\b.*$', raw, flags=re.M)
    if len(parts) < 2:
        return None
    return re.split(r'^#\s+', parts[1], flags=re.M)[0].strip() or None


@lru_cache(maxsize=8)
def harvest_section(heading: str) -> tuple[dict, ...]:
    """Collect one named section from EVERY chapter of EVERY course.

    This is the single mechanism behind the interview bank, the mistakes page and
    the cheat-sheet page (VISION §8: revision is *generated*, never written
    twice). Add a page by naming a heading — no new parsing code.
    """
    from learning.registry import DOCS_ROOT
    out = []
    for c in COURSES:
        for ref in chapters_for(c.slug):
            raw = _strip_frontmatter(_read(DOCS_ROOT / c.folder / ref.filename))
            body = _section_body(raw, heading)
            if body:
                out.append({'course': c, 'chapter': ref,
                            'html': mark_safe(_MD.render(body))})
    return tuple(out)


# The generated revision pages. Adding one is a row here — nothing else.
REVISION_PAGES = {
    'mistakes': {
        'slug': 'mistakes', 'heading': 'Beginner Mistakes',
        'title': 'Common Mistakes', 'icon': '⚠️', 'accent': '#9c4221',
        'blurb': 'Every mistake called out across every chapter — the fastest way '
                 'to avoid a bug you have not written yet.',
    },
    'cheatsheet': {
        'slug': 'cheatsheet', 'heading': 'Cheat Sheet',
        'title': 'Cheat Sheets', 'icon': '⚡', 'accent': '#2c5282',
        'blurb': 'Every chapter compressed to its essentials. Read the night '
                 'before an interview, or when memory needs a nudge.',
    },
}


def revision_page(slug: str) -> dict | None:
    spec = REVISION_PAGES.get(slug)
    if spec is None:
        return None
    items = harvest_section(spec['heading'])
    return {'spec': spec, 'items': items, 'count': len(items)}


# ── search: no index needed at this size, but cache the corpus ──────────────
@lru_cache(maxsize=1)
def _corpus() -> tuple[dict, ...]:
    """Every chapter's plain text, once. ~12k lines total — small enough that a
    linear scan is genuinely the right tool; an index would be premature."""
    from learning.registry import DOCS_ROOT
    docs = []
    for c in COURSES:
        for ref in chapters_for(c.slug):
            raw = _strip_frontmatter(
                _read(DOCS_ROOT / c.folder / ref.filename))
            # Drop the H1 + the "> Part of … Prev … Next" nav block: they are
            # navigation, not teaching, and would otherwise rank on every query.
            raw = _H1_RE.sub('', raw, count=1)
            raw = re.sub(r'\A\s*(?:^>.*\n)+', '', raw, count=1, flags=re.M)
            docs.append({'course': c, 'chapter': ref,
                         'text': raw, 'lower': raw.lower()})
    return tuple(docs)


def search(query: str, limit: int = 60) -> dict:
    """Plain substring search with a readable snippet per hit.

    Deliberately simple and honest: it matches what you typed, ranks by hit
    count, and shows you where. No stemming, no fuzzy matching — so a result is
    never a mystery.
    """
    q = (query or '').strip()
    if len(q) < 2:
        return {'query': q, 'results': [], 'total': 0, 'too_short': bool(q)}
    ql = q.lower()
    results = []
    for doc in _corpus():
        hits = doc['lower'].count(ql)
        if not hits:
            continue
        # First hit, widened to whole words, with the term marked.
        i = doc['lower'].find(ql)
        start, end = max(0, i - 90), min(len(doc['text']), i + len(q) + 130)
        snippet = doc['text'][start:end].replace('\n', ' ').strip()
        # Strip markdown punctuation so a snippet reads as prose, not source.
        # Order matters: fences and code spans first, then emphasis, then table
        # pipes and heading hashes.
        snippet = re.sub(r'```+\w*', ' ', snippet)
        snippet = snippet.replace('`', '')
        snippet = re.sub(r'\*\*|__|~~', '', snippet)
        # [label](target) -> label   ·   ![alt](img) -> alt
        snippet = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', snippet)
        snippet = re.sub(r'(?<!\w)[*_](?=\w)|(?<=\w)[*_](?!\w)', '', snippet)
        snippet = re.sub(r'^\s*#{1,6}\s*|\s#{1,6}\s', ' ', snippet)
        snippet = re.sub(r'[│┌┐└┘├┤┬┴┼─═║╔╗╚╝╠╣╦╩╬▶◀▲▼]+', ' ', snippet)
        snippet = re.sub(r'\s*\|\s*', ' | ', snippet)
        snippet = re.sub(r'\s+', ' ', snippet).strip(' |-')
        # Escape first, then insert our own <mark> — never trust the file's text
        # as HTML (same reason the renderer runs with html=False).
        from django.utils.html import escape
        safe = escape(snippet)
        safe = re.sub(f'({re.escape(escape(q))})', r'<mark>\1</mark>',
                      safe, flags=re.I)
        results.append({
            'course': doc['course'], 'chapter': doc['chapter'],
            'hits': hits,
            'snippet': mark_safe(('… ' if start else '') + safe + ' …'),
        })
    results.sort(key=lambda r: -r['hits'])
    return {'query': q, 'results': results[:limit],
            'total': len(results), 'too_short': False}


def reload_courses() -> None:
    """Clear the caches — call after editing a .md while the server runs."""
    chapters_for.cache_clear()
    interview_questions.cache_clear()
    harvest_section.cache_clear()
    _corpus.cache_clear()
