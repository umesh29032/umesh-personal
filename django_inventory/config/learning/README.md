---
id: app-learning-readme
type: app-readme
status: active
owner: handwritten
scope: learning
anchors: config/learning/
verified: 2026-08-01
---

# `learning` — the course reader

**What it is:** the in-app front end for the engineering courses. It renders the
markdown in `docs/*_course/` as browsable, linkable web pages at `/learn/`.

**What it is NOT:** a content store. It holds **only per-user progress** models —
never a line of chapter text.

🔒 **Read [docs/LEARNING_PLATFORM_VISION.md](../../docs/LEARNING_PLATFORM_VISION.md)
first.** It is the owner-locked vision: this is a product (engineering academy +
interview platform + future SaaS), not a Learn page.

---

## The one architectural rule

> **The markdown files in `docs/` are the single source of truth.**
> This app reads them and renders HTML. There is never a second copy.

Edit a `.md` → the site changes. Nothing to sync, so the courses and the
engineering docs **cannot drift apart** — the failure this project has already
paid for once (see `docs/FRESH_DB_REQUIREMENTS.md` §6). A model appearing in this
app that is **not per-user progress** would mean that rule was broken;
`test_app_has_no_CONTENT_models` + `test_no_model_stores_chapter_text` are the alarms.

## Files

| File | Role |
|---|---|
| `models.py` | **USER STATE ONLY**: `LessonProgress` (one row per user×chapter: `completed_at` honest-NULL, `last_opened_at`, `open_count`, `seconds_spent`, `scroll_percent`, `.state` → done/reading/new) and `Bookmark` (`kind` = bookmark\|favourite, so one table serves both). Content is referenced by **string slugs, not FKs** — there is no content table to point at, and string keys keep rows portable (VISION §11). Migration `0001` is purely additive (2 new tables, touches nothing existing). |
| `progress_service.py` | **The ONLY writer** of those two models (rule 5). Reads: `course_progress` (% + done_slugs), `resume_point`, `learning_stats` (streak), `bookmarks_for`, `chapter_state`. Every query filters by `user` first; the user always comes from the session, never the request body. |
| `registry.py` | Which folders are courses (`COURSES` tuple) + chapter discovery. **Adding a course = one entry here + a folder of `.md`.** `_EXTRA_PAGES` keeps un-numbered pages (e.g. `ARCHITECTURE.md`) from being silently dropped. |
| `services.py` | Pure functions: markdown → HTML (markdown-it-py + Pygments), frontmatter strip, TOC extraction, prev/next, `.md`-link → URL rewriting, interview-question harvest, `lru_cache` + `reload_courses()`. |
| `views.py` | 4 read-only `TemplateView`s (GET/HEAD/OPTIONS only → POST 405) + 2 POST-only progress endpoints, all `LoginRequiredMixin`. |
| `urls.py` | `/learn/` · `/learn/interview/` · `/learn/<course>/` · `/learn/<course>/<chapter>/` · `…/complete/` + `…/bookmark/` (POST) |
| `templates/learning/_learn_base.html` | All page-scoped CSS under `.learn-page` (UI rule 10) + inlined Pygments theme. |
| `templates/learning/{index,course,chapter,interview}.html` | The four pages. |

## URLs — designed for multi-tab reading

Every page is a plain, shareable URL, so Ctrl+click / long-press opens chapters in
their own tabs (an explicit owner requirement). Cross-references inside the
courses are written as `.md` links (so the files stay readable in an editor and on
GitHub) and are **rewritten to `/learn/...` URLs at render time**.

## Generated pages — one engine, three outputs

`services.harvest_section(heading)` collects one named `# heading` from **every
chapter of every course**. Three pages ride on it, and adding a fourth is one row
in `REVISION_PAGES`:

| Page | Harvests | Today |
|---|---|---|
| `/learn/interview/` | `# Interview Questions` (by level) | **502** questions |
| `/learn/revise/mistakes/` | `# Beginner Mistakes` | **109** chapters |
| `/learn/revise/cheatsheet/` | `# Cheat Sheet` | **109** chapters |

A test pins that a harvest **stops at the next H1** — otherwise every revision
page would quietly become the whole chapter.

## Search

`/learn/search/?q=…` — literal substring match over all **113** pages, ranked by hit
count, with a cleaned-up snippet (markdown punctuation stripped, term `<mark>`ed,
HTML escaped **before** the mark is inserted). Deliberately not fuzzy: a result is
never a mystery. The corpus is cached and excludes each chapter's H1 + nav
blockquote, so navigation text never ranks.

## Keyboard shortcuts

`/` focus search · `j` next chapter · `k` previous · `g` then `i` interview prep ·
`g` then `l` learn home. Never fires while typing in a field and never uses
ctrl/meta/alt, so no browser shortcut is stolen. Lives in `_learn_base.html`;
`chapter.html` calls `{{ block.super }}` so its own script does not override them.

## The interview page is generated, not written

`services.interview_questions()` harvests every `- **Junior|Mid|Senior|Staff:**
question — answer` bullet from inside each chapter's `# Interview Questions`
section. Currently **502 questions** (Junior 136 · Mid 133 · Senior 123 · Staff 110)
— SQL 157 + Deployment 185 + **Git 160**. Every chapter also carries a `### Why interviewers ask
these` table (VISION §6 item 15: why the interviewer asks + the common wrong answer +
a killer follow-up) — **107/107 as of 2026-08-03** (69/69 when the contract was first
completed, before the git course), pinned by
`test_every_chapter_has_the_why_interviewers_ask_block`.

The deployment 185 were invisible until 2026-08-01:
they were written as `**Junior — "Q"** A` instead of `- **Junior:** Q — A`. A test
now counts what the chapters claim against what the page shows, so a question can
never again be written and silently not shown.
Fix a question in the chapter and this page fixes itself. It only reads inside
that section, so a bold label elsewhere cannot leak in.

## Rendering & safety

- `markdown-it-py` (CommonMark + tables + strikethrough) and `Pygments` were
  **already installed** — this app added no dependency.
- `html=False` on the parser: raw HTML in a `.md` is escaped, not executed.
  Our docs are trusted, but a renderer that executes whatever is in a text file
  is a footgun waiting for a paste.
- Unknown code-fence languages fall back to plain `<pre>`, so an ASCII diagram
  can never break a page.

## Mobile-first (UI rule 11 — functional, not polish)

Verified in a real browser at 360 / 768 / 1280 px:

| Width | Layout | Page overflow |
|---|---|---|
| 360 px | single column, collapsible TOC | **none** (code/diagrams scroll inside their own box) |
| 768 px | single column, roomier prose | none |
| 1280 px | prose + **sticky TOC rail** (`684px 250px`) | none |

Wide tables are wrapped in an `.lp-tablewrap` scroller by a small script, so the
page itself never scrolls sideways. Touch targets ≥44 px.

## Access

`LoginRequiredMixin` + an ungated `Learn` sidebar `MenuItem` (like *My Dashboard*
/ *My Earnings*: educational content, no business data). The owner intends to open
this publicly later — that is a change to the mixin here plus a sidebar rule, and
nothing in these views is user-specific, so nothing else has to move.

## Adding a course later

1. Put the `.md` files in `docs/<name>_course/`, named `NN_Title.md`.
2. Add one `Course(...)` entry to `registry.COURSES`.
3. That's it — index card, chapter list, prev/next, TOC and interview harvesting
   all come for free. `test_every_markdown_file_is_reachable` will hold you to
   serving every file.

**Proven, not theoretical.** `git_course` was added on 2026-08-03 exactly this way — one
`Course(slug='git', folder='git_course', …)` entry plus a folder of 41 files — and every
generated page picked it up with no other code change:

| | before | after |
|---|---|---|
| courses | 2 | **3** (SQL 26 · Deployment 46 · **Git 41**) |
| pages served | 72 | **113** |
| interview bank | 339 | **502** (Junior 136 · Mid 133 · Senior 123 · Staff 110) |
| mistakes / cheat-sheet pages | 69 chapters each | **109** each |
| teaching chapters on the 19-section contract | 67 | **107** |

That is the core law working: the markdown is the single source of truth, and the app is a
window. No model, no migration, no data entry — and no second copy to keep in sync.

## The dashboard is DERIVED, not stored

`progress_service.dashboard(user)` returns continue-learning, recommended-next,
active vs completed courses, remaining lessons, learning days, weekly activity,
recently opened and six stat tiles — **all computed from `LessonProgress` in one
pass**. Nothing is cached in a column.

That is deliberate: a stored `CourseProgress` row would be a second source of truth
for the same fact, and it would drift the first time a chapter is renamed. Only
what cannot be derived gets a column — **time spent**, **scroll depth**, and an
explicit **bookmark**. (If enrolment ever becomes a real business event — payment,
invite, cohort — *that* is a new fact and earns its own table.)

**Reading time** comes from a heartbeat that only counts while the tab is
*visible*, sends at most one beat per 30 s, is clamped to 120 s per beat
server-side, and fires a final `sendBeacon` on exit. So a tab left open overnight
cannot invent study time, and neither can a forged POST.

## Progress, and the line it must not cross

Progress is **user state**, so models are allowed (VISION §2, §9). Content models
are **forbidden**, and two tests are the alarm:
`test_app_has_no_CONTENT_models` (only `LessonProgress`/`Bookmark` may exist) and
`test_no_model_stores_chapter_text` (no `TextField` anywhere — chapter text cannot
sneak in as a column).

Opening a chapter *is* the progress signal (`mark_opened` on GET), so
continue-learning and the streak work without the learner pressing anything.
`Mark complete` and `Bookmark` are **POST-only endpoints** kept separate from the
content pages, so a course page itself can still never be POSTed to.
Un-completing is deliberately allowed — this is a learning aid, not an audit
ledger (contrast the money rules in sql_course ch 12).

## Tests — `tests/test_learning.py` (49)

Pins: every `.md` on disk is served (the `ARCHITECTURE.md` regression) · slugs
unique/URL-safe · teaching order · markdown→HTML (headings/tables/code/quotes) ·
`.md` links rewritten · title not duplicated · nav blockquote stripped but
teaching boxes kept · prev/next chain · login required · **every chapter of every
course returns 200** · POST → 405 · unknown → 404 · **no content models / no
TextField** · progress recorded on open · complete + un-complete · bookmark
toggle · resume point · **percentage ignores renamed/removed chapters** ·
**progress isolated between users** · progress endpoints need login and reject
GET · unknown chapter cannot create progress rows · **time clamped at 120 s/beat** ·
**scroll depth never goes backwards** · heartbeat on an unopened chapter creates
nothing · the three lesson states are distinguishable · dashboard totals and
weekly buckets · recommended-next picks the next unfinished chapter · **dashboard
isolated between users** · harvest stops at the next H1 · search ranking, escaping
and short-query guards · `reload_courses()` clears **every** cache.
