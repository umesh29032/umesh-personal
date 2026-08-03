---
id: docs-apps-learning-guide
type: app-guide
status: active
owner: handwritten
scope: learning
anchors: config/learning/
verified: 2026-08-01
---

# learning — app guide (the in-app engineering academy, `/learn/`)

> **WINDOW over the markdown, plus per-user progress.** The vision is owner-locked:
> 🔒 [LEARNING_PLATFORM_VISION.md](../../LEARNING_PLATFORM_VISION.md). Deeper prose
> lives in [config/learning/README.md](../../../config/learning/README.md); the human
> page is [kos/features/learning-courses.md](../../../kos/features/learning-courses.md).

**The core law (VISION §2):** the markdown in `docs/*_course/` is the ONE source of
truth for course content. The app renders it and never stores it. **Content models are
forbidden; per-user progress models are allowed** — that is the two-layer law (§9b):
*documentation is shared, progress is personal.* Two tests stand guard
(`test_app_has_no_CONTENT_models`, `test_no_model_stores_chapter_text`).

| File | Role |
|---|---|
| `apps.py` | AppConfig |
| `registry.py` | The `COURSES` tuple + `chapter_files()` + `slug_for()`. **Adding a course = one entry here + a folder.** `_EXTRA_PAGES` keeps non-`NN_` pages reachable (`ARCHITECTURE.md` was silently dropped once by the filename regex — pinned by `test_every_markdown_file_is_reachable`) |
| `services.py` | Read-only rendering + every generated page. `render_chapter()` (markdown→HTML, TOC, `.md`→URL rewrite, prev/next, reading minutes) · `_section_body()` = **the ONE section extractor** · `harvest_section()` = the engine behind the revision pages · `interview_questions()` · `search()` · `reload_courses()` clears all four caches |
| `models.py` | `LessonProgress` (per user × chapter: `completed_at`, `last_opened_at`, `open_count`, `seconds_spent`, `scroll_percent`, derived `.state`) + `Bookmark` (with `Kind`, so favourites need no new table). String slugs, not FKs — chapters live on disk, so a DB FK is impossible by design |
| `progress_service.py` | **Single writer** for both models (rule 5). `dashboard()` · `add_time()` (clamped to 120 s per beat) · `recommended_next()` · `chapter_states()`. Every course percentage is **derived** from `LessonProgress` — deliberately no `CourseProgress` table, because a stored total is a second source of truth that drifts |
| `views.py` | 4 GET-only `TemplateView`s (index/course/chapter/interview + revision + search) and 3 POST-only progress endpoints. **Gated by `_LearningAccessMixin`** — login + the `learning:index` Access-Control row, so ONE checkbox governs the whole section. Without it a rule on `learning:index` would hide the menu link and still serve `/learn/sql/14-indexes/` by direct URL, because `can_access_url_name()` returns True for any url_name with no rule. Denial mirrors `SidebarAccessMiddleware`: message + 302 to the dashboard, or 403 for AJAX |
| `urls.py` | `/learn/` namespace (10 routes) |
| `templates/learning/` | `_learn_base.html` (shell, keyboard shortcuts) + index · course · chapter · interview · revision · search. Page CSS scoped under `.learn-page` (UI rule 10) |
| `tests/test_learning.py` | **57 tests.** Core-law alarms · reachability · render · progress isolation · search · and the **five anti-content-loss pins** added 2026-08-01 (contract presence · every chapter feeds every generated page · every question has an answer · wrapped answers not truncated · every chapter has its why-they-ask table) |

## The generated pages (nothing is written twice)

| URL | Harvested heading | Coverage |
|---|---|---|
| `/learn/interview/` | `# Interview Questions` | **339 Qs** — Junior 96 · Mid 93 · Senior 83 · Staff 67 (SQL 154 + Deployment 185) |
| `/learn/revise/mistakes/` | `# Beginner Mistakes` | 69 chapters |
| `/learn/revise/cheatsheet/` | `# Cheat Sheet` | 69 chapters |

Adding a revision page = one row in `REVISION_PAGES`. No new parsing code.

## The 19-section chapter contract

All **67 teaching chapters** (SQL 25 + deployment 42) carry the full contract; the
course-overview pages and `deployment_course/ARCHITECTURE.md` are deliberate
exemptions (`EXEMPT` in the tests). `ChapterContractTests` fails the suite if any
chapter loses a section, so the contract is pinned rather than hoped for.

**VISION §6 item 15 is complete too (2026-08-01):** every teaching chapter carries a
`### Why interviewers ask these` table — *testing for / weak answer / what lands* — plus
**The killer follow-up**. That was 3 of 69 when the contract was first called "complete";
the gap is now closed and pinned (presence, row count, killer line, and table-cell
integrity, since a stray pipe silently breaks a markdown table).

## Content-loss lessons (2026-08-01) — read before touching `services.py`

Three defects had the same shape: **content was written and the platform quietly did
not show it.** No errors, no visual breakage — only counting found them.

1. `_section_body()` required an exact H1, so an enriched heading
   (`# Beginner Mistakes (the greatest hits)`) contributed nothing. Now prefix-tolerant.
2. `interview_questions()` held a **private copy** of that regex — a second source of
   truth inside the app whose law forbids exactly that. Now reuses `_section_body()`.
3. The level regex was `$`-anchored per line, but answers wrap over several lines.
   **All 185 deployment questions were missing**, and 6 more had no answer. Now
   `_level_items()` parses whole bullet blocks.

Also: `## Further Reading` was H2 in the deployment course, so the H1-built TOC never
listed the last section of any chapter; and pages that section with H2 had an empty
TOC. `render_chapter()` now uses whichever heading level the page actually uses.

**Rule of thumb: count what the chapters claim against what the page shows.** A
generated page that renders without error is not evidence that it is complete.

## Related

- Vision: 🔒 [LEARNING_PLATFORM_VISION.md](../../LEARNING_PLATFORM_VISION.md)
- App prose: [config/learning/README.md](../../../config/learning/README.md)
- Human page: [kos/features/learning-courses.md](../../../kos/features/learning-courses.md)
- Courses: [sql_course/](../../sql_course/00_COURSE_OVERVIEW.md) · [deployment_course/](../../deployment_course/00_COURSE_OVERVIEW.md)
