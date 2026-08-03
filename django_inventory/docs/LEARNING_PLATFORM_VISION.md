---
id: learning-platform-vision
type: truth-lock
status: frozen-v1
owner: frozen
scope: learning — the in-app learning platform (courses, interview prep, progress)
anchors: config/learning/services.py, config/learning/registry.py, config/learning/progress_service.py
verified: 2026-08-01
title: Learning Platform — MASTER VISION (owner-locked)
lock: 🔒 LOCKED VISION (owner, 2026-07-31). Read before ANY learning-platform work.
supersedes: the "course reader" framing — this is a product, not a Learn page
canonical_for: what the learning platform is FOR, its laws, and its roadmap
implementation: config/learning/ (app) · docs/*_course/ (content) · kos/ (source of truth)
human_page: kos/features/learning-courses.md
---

# Learning Platform — Master Vision

> **Owner ruling, 2026-07-31.** *"Stop thinking of this as adding a Learn page.
> This is becoming an independent product inside our Django ecosystem."*

This document is the **why**. It is deliberately not a task list — the roadmap at
the end is, and it moves. Read this first, then check §10 for what is built.

---

## 1. What this is

Not documentation. Not a markdown viewer. An **Engineering Learning Operating
System** — the combination of:

interactive documentation · premium technical course · interview-prep platform ·
internal engineering academy · Knowledge Operating System · real-world
architecture reference · career-switch preparation system.

**Every architecture decision must assume it may one day serve thousands of users
and become a commercial product — without a rewrite.**

## 2. THE CORE LAW — one source of truth

> **Never duplicate technical knowledge.**
> **KOS + docs write the knowledge. The Learning app teaches it.**

```
   KOS / docs (markdown)          ← THE canonical knowledge. Only place it lives.
        │  renders
        ▼
   Learning Engine                ← organises · visualises · personalises
        ▼
   Course Experience              ← the premium reading surface
        ▼
   Student Progress               ← user-specific (models ALLOWED here)
        ▼
   Interview Preparation          ← generated FROM the chapters
        ▼
   Revision                       ← generated FROM the chapters
        ▼
   Certification  ─▶  Career Growth
```

Consequences that are **not negotiable**:
- The app **must never become a second documentation system.** No chapter text in
  a template, a fixture, or a database row.
- Content models are forbidden. Two tests are the alarm:
  `test_app_has_no_CONTENT_models` and `test_no_model_stores_chapter_text`.
- **Progress models are ALLOWED and expected** — progress is user state, not
  knowledge. It must never pollute the documentation.

## 3. Audience — six levels, one platform

| Level | Who |
|---|---|
| **0** | has never written code |
| **1** | beginner |
| **2** | junior developer |
| **3** | mid developer |
| **4** | senior developer |
| **5** | staff / principal |

Every chapter should help the reader **climb**. The experience must feel like
levelling up, not like reading documentation.

## 4. Teaching philosophy

**Not** textbook docs. **Not** generic AI tutorials. **Not** blog articles.

> Every lesson must read like a **senior engineer mentoring a junior**, sitting
> beside them.

Each lesson answers: What · Why · How · When · Where · **Why not** · common
mistakes · real production examples · tradeoffs · scaling · interview
expectations · architecture implications · business implications · future evolution.

## 5. Teach from OUR project — always

> **The project is the teaching laboratory.** Never teach a concept in isolation.

Teaching JOIN means: the real tables that interact, the ORM call that generates
it, where performance bites, which index matters, the mistake we actually made,
how we debugged it in production. **If a concept exists in our project, it is
taught with our project.**

That is the competitive advantage. We cannot out-video a ₹25,000 course. We can
out-**reality** it: a living ERP, real architecture, real mistakes, real
debugging, real deployment, real scaling, real business workflows.

## 6. Chapter contract — the 19 sections

The current courses use a 12-section format. The target is **19**; existing
chapters are upgraded additively, never rewritten from scratch.

1. **Learning Objectives** — what the student will achieve
2. **Why This Topic Exists** — business / real-world / production motivation
3. **Beginner Explanation** — assume nothing
4. **Concept Building** — complexity increases gradually
5. **Deep Technical Explanation** — how it actually works internally
6. **Visual Diagrams** — many: ASCII, flow, architecture, execution, lifecycle,
   DB, request lifecycle, sequence, relationship, decision trees
7. **Our Project Reference** — exact apps / models / services / URLs / workflow /
   business impact
8. **Production Walkthrough** — how it behaves live
9. **Common Mistakes** — and *why* developers fail
10. **Debugging Guide** — how to investigate
11. **Performance Notes** — scaling, caching, indexes, complexity
12. **Security Considerations** — auth, authz, validation, injection, secrets
13. **Architecture Decisions** — why this way, alternatives, tradeoffs
14. **Best Practices**
15. **Real Interview Questions** — Junior/Mid/Senior/Staff, **plus why the
    interviewer asks, the ideal answer, and the common wrong answer**
16. **Revision Notes**
17. **Cheat Sheet**
18. **Practice Tasks** — exercises, debugging, architecture thinking, code
    reading, design problems
19. **Further Reading** — only if it genuinely adds value

### 6b. How the 19 map onto the actual chapter headings (added 2026-08-01)

The courses do **not** use the 19 names above verbatim — they use 21 H1 headings that
cover the same ground. Recording the mapping so "19-section contract" stops being
ambiguous, and so the audit can be done by section *name* (the only reliable way):

| VISION §6 item | Actual H1 heading(s) in the chapters |
|---|---|
| 1 Learning Objectives | `Learning Objectives` |
| 2 Why This Topic Exists | `Purpose` + `The Problem` |
| 3+4+5 Beginner Explanation · Concept Building · Deep Technical | `Theory (from zero)` (one heading, three depths inside) |
| 6 Visual Diagrams | `Visual Diagram` |
| 7 Our Project Reference | `Real World Example (My ERP)` + `My ERP Section` |
| 8 Production Walkthrough | `Production Walkthrough` |
| 9 Common Mistakes | `Beginner Mistakes` |
| 10–14 | `Debugging Guide` · `Performance Notes` · `Security Considerations` · `Architecture Decisions` · `Best Practices` |
| 15 Real Interview Questions | `Interview Questions` — **see the gap below** |
| 16–19 | `Revision Notes` · `Cheat Sheet` · `Practice Tasks` (+ `Homework`) · `Further Reading` |
| — | `Practical` (hands-on: not a §6 item, kept because it is the most-used section) |

**✅ §6 item 15 COMPLETE 2026-08-01.** Item 15 asks for three things per question: the
levelled question + answer, **plus why the interviewer asks it, plus the common wrong
answer**. All three are now present in **all 69 teaching chapters** (was 3 of 69 —
deployment 01, 28, 39 were the pattern; the other 66 were written 2026-08-01).

Each block is a `### Why interviewers ask these` H3 holding a **3–4 row table**
(`Testing for | Weak answer | What lands`) plus **The killer follow-up** — the brutal
question that separates memorised answers from real experience.

- **Section presence:** ✅ 67/67 teaching chapters, test-pinned.
- **§6 item 15 interior structure:** ✅ **69/69**, test-pinned by
  `test_every_chapter_has_the_why_interviewers_ask_block` (checks presence, row count,
  the killer follow-up, and that no cell contains a stray pipe that would break the table).

**The weak answer must be plausible, never a straw man** — a mid-level dev's real
answer that sounds fine and is shallow. **What lands** must carry a concrete anchor: a
real number, file, flag, command or the exact term the interviewer is listening for.

## 7. Interview preparation is FIRST-CLASS

Not an afterthought. Every chapter contributes automatically to a **Junior / Mid /
Senior / Staff** question bank, spanning: conceptual · scenario-based · production
incidents · debugging · system design · performance · architecture · tradeoff
discussion · behavioural · leadership · code review.

**Target: the platform alone is sufficient to prepare for a technical interview.**

## 8. Revision system — all generated from the same markdown

Quick Notes · Flash Revision · One-page Summary · Common Mistakes · Cheat Sheet ·
Important Commands · Mental Models · Memory Tricks.

Generated wherever possible — **never written twice** (the §2 law).

## 9. Experience requirements

Must feel **premium** — not like GitHub, not like reading raw markdown.

Course dashboard · chapter progress · reading time · difficulty · prerequisites ·
learning path · recommended next · bookmarks · continue-learning · last-opened ·
recently completed · streak · time spent · completion % · achievements ·
milestones · roadmap · dark mode · **mobile-first, tablet-friendly,
desktop-optimised** · fast · excellent typography · comfortable reading · sticky
nav · search · keyboard shortcuts · notes · highlights · favourites.

**Progress entities** (user-specific, allowed): `LessonProgress` ·
`CourseEnrollment` · `Bookmark` · `Note` · `Highlight` · `LearningHistory` ·
`Achievement` · `LearningStreak` · `QuizAttempt` · `CertificationStatus`.
Each user's state is isolated; nothing leaks between learners.

## 9b. The two-layer law (owner follow-up, 2026-07-31)

> **Layer 1 — Knowledge Layer:** markdown / KOS. The single source of truth. It
> teaches *everyone*.
> **Layer 2 — Student Layer:** progress, history, bookmarks, notes, achievements,
> certifications. It remembers *each* student's journey.
> **Never mix them.** *"Documentation is shared. Progress is user-specific."*

### Derived vs stored — the rule that keeps Layer 2 honest

Layer 2 has its own version of the content-duplication trap: storing a number that
could be *computed* creates a second source of truth that drifts. So:

| Fact | How | Why |
|---|---|---|
| completion %, remaining lessons, active/completed courses, learning days, weekly activity, recently viewed, recommended next, streak | **DERIVED** from `LessonProgress` | one source of truth; can never disagree with the lesson rows |
| lesson opened / completed / first-seen / last-seen | **stored** (`LessonProgress`) | the atomic facts — nothing to derive them from |
| time spent, scroll depth | **stored** | genuinely unobservable after the fact |
| bookmark / favourite | **stored** (`Bookmark.kind`) | an explicit human act |

A `CourseProgress` table was **deliberately not created**: every field it would
hold is a function of the lesson rows. If enrolment ever becomes a real business
event (payment, invitation, a cohort), *that* is a new fact and earns its own table.

### Isolation

Every read filters by `user` first; the user always comes from the session, never
from a request body. Pinned by `test_dashboard_is_isolated_between_users` and
`test_progress_is_isolated_between_users`.

## 10. Status — what is built (update this section, keep it honest)

| Capability | State |
|---|---|
| Course reader (`/learn/`, index → course → chapter) | ✅ built 2026-07-31 |
| Markdown = single source of truth, zero content models | ✅ enforced by test |
| SQL course (26 ch) · Deployment course (46 ch) = 72 pages | ✅ served |
| On-page TOC · prev/next · `.md`→URL rewriting (multi-tab) | ✅ |
| Generated interview bank (**339 Q**: J96/M93/S83/Staff67 — SQL 154 + Deployment 185) | ✅ |
| Mobile-first verified 360 / 768 / 1280 px, zero overflow | ✅ |
| Adding a course = 1 registry entry + a folder | ✅ |
| **Progress · resume · completion % · streak · bookmarks** | ✅ built 2026-07-31 (migration `0001`, additive) |
| Generated revision pages — **Common Mistakes + Cheat Sheets** (69 chapters each) | ✅ built (same harvest engine as the interview bank) |
| **Search** across all 72 chapters (ranked, marked snippets) | ✅ built |
| **Keyboard shortcuts** (`/` search · `j`/`k` chapters · `g i` · `g l`) | ✅ built |
| **Personalised dashboard** — continue-learning · recommended next · active/completed courses · recently opened · weekly activity bars · 6 stat tiles | ✅ built 2026-07-31 |
| **Time spent + scroll depth** (visible-tab heartbeat, clamped, `sendBeacon` on exit) | ✅ built |
| **3-state lesson nav** (done ✓ / reading ◐ / not started ○) | ✅ built |
| Favourites | ✅ schema ready (`Bookmark.kind`), UI uses bookmark today |
| Notes · highlights | ⏳ (owner marked "future") |
| Quizzes · XP · badges · levels · leaderboards · certificates | 🔮 model must not block — it does not |
| Deployment course: **Hinglish Samjho boxes 46/46** | ✅ done 2026-07-31 |
| **SQL course: section presence — 25 of 25 chapters** | ✅ **COMPLETE 2026-07-31** (every chapter now carries Learning Objectives · Production Walkthrough · Debugging Guide · Performance Notes · Security Considerations · Architecture Decisions · Best Practices · Revision Notes · Practice Tasks, each citing something real from this repo) |
| **Deployment course: section presence — 44 of 44 chapters** | ✅ **COMPLETE 2026-08-01** (ch 01–42 + 00A hosting + 00B costs; every new section cites a real file/number from this repo) |
| **19-section contract pinned by test, not by hope** | ✅ `ChapterContractTests` fails if any chapter drops a section |
| **Every chapter feeds every generated page** | ✅ pinned — a written-but-invisible section now fails the suite |
| **§6 item 15 interior structure — "why the interviewer asks" + "common wrong answer"** | ✅ **69/69 COMPLETE 2026-08-01** — every teaching chapter has a `### Why interviewers ask these` table (3–4 rows: testing-for / weak answer / what lands) + a killer follow-up. Test-pinned incl. table-cell integrity. |
| Deployment course: more/richer diagrams | ⏳ avg ~5.7 per chapter today |
| 7-field frontmatter (DOC_STANDARDS §13) on all 72 course files | ✅ 2026-08-01 — `knowledge_sync` WARN 672 → 17 (the 17 left are pre-existing debt on other docs) |
| Test battery | ✅ **1992 green, all 14 installed apps, 0 failures** — `bod` (37) is now INSIDE the gate; it never was through the 1878/1896 baselines. The UTC-vs-IST date bug class it exposed is fixed (10 sites). See [UTC_LOCAL_DATE_BUG_CLASS_2026_08_01.md](UTC_LOCAL_DATE_BUG_CLASS_2026_08_01.md). |
| Public / no-login access for sharing | ⏳ **owner decision** |
| Quizzes · certificates · achievements | 🔮 later |
| Orgs · teams · payments · instructor mode · API | 🔮 architecture must not block |

### 10b. Three silent content-loss defects found while finishing the courses (2026-08-01)

All three had the same shape: **content was written, and the platform quietly did not
show it.** Nothing errored, nothing looked broken, so only counting caught them.

| # | Defect | Impact | Fix | Pinned by |
|---|---|---|---|---|
| 1 | `_section_body()` demanded an exact H1 (`^# Cheat Sheet$`), so a chapter enriching its heading (`# Beginner Mistakes (the greatest hits)`) contributed nothing | ch 42 vanished from mistakes + cheatsheet + interview | prefix-tolerant match | `test_enriched_headings_are_still_harvested` |
| 2 | `interview_questions()` kept a **private copy** of that regex — a second source of truth inside the app whose core law forbids exactly that | ch 42's four-level set invisible even after fix 1 | reuse the one extractor | `test_every_labelled_question_reaches_the_interview_bank` |
| 3 | `_LEVEL_RE` was `$`-anchored per line, but answers wrap over several lines (and sometimes start on the next line) | **185 deployment questions (all of them) missing from the bank; 6 more had no answer at all** | parse whole bullet blocks, collapse wrapped lines | `test_a_wrapped_answer_is_not_truncated` + `test_every_question_has_a_question_and_an_answer` |

Interview bank: **154 → 339 questions.** Also fixed: `## Further Reading` was H2 in the
deployment course, so the TOC (built from H1s) never listed the last section of any
chapter; and overview/reference pages that section with H2 had an **empty** TOC — the
builder now uses whichever heading level the page actually uses.

**The durable lesson: count what the chapters claim against what the page shows.**
A generated page that renders without error is not evidence that it is complete.

**Contract exemptions** (deliberate, encoded in `EXEMPT`): `00_COURSE_OVERVIEW.md` is a
course map and `deployment_course/ARCHITECTURE.md` is a reference diagram page. Both are
served and searchable; neither is a teaching chapter, so neither carries the 19 sections.

### How to do the 12 → 19 upgrade (the recipe, so it stays consistent)

`sql_course/07_JOINs.md` is the reference. Insert **additively** — never rewrite an
existing section:

| Insert before | New sections |
|---|---|
| `# Purpose` | **Learning Objectives** — 4-6 "by the end you can…" bullets, verbs not nouns |
| `# Beginner Mistakes` | **Production Walkthrough** · **Debugging Guide** (an ordered method) · **Performance Notes** · **Security Considerations** · **Architecture Decisions** (why this way + what it costs) · **Best Practices** |
| `# Cheat Sheet` | **Revision Notes** — 5 one-line recalls |
| `# Homework` | **Practice Tasks** — read-the-code · debug · design · architecture-argument |

Rules while upgrading: every new section must cite **something real from this
project** (a file, a table, a real bug, a real number) or it is filler. Keep the one
💡 Samjho aise box per chapter. Do not remove `Homework` — Practice Tasks sits
beside it (deeper, design-oriented).

## 11. Commercial readiness — do not build, do not block

Future: free + premium courses · subscriptions · company onboarding ·
organisation accounts · instructor mode · certificates · payments · teams ·
analytics · marketplace · invites · API access · white-label · licensing ·
offline export.

None is built now. **Nothing in the architecture may prevent them.** Practically
that means: content stays file-based and portable; progress is per-user rows
keyed by `(user, course_slug, chapter_slug)` strings rather than hard FKs to
content; access is one gate in one place, so "public", "enrolled" or "paid" is a
policy swap, not a refactor.

## 12. Course roadmap

Beyond SQL and Deployment: Python · Django · Django ORM · REST APIs · Auth ·
RBAC · System Design · Docker · Redis · Celery · PostgreSQL · Linux · Git ·
Testing · CI/CD · Cloud (Run/Storage) · Monitoring · Logging · Performance ·
Security · ERP Architecture · Manufacturing Domain · Inventory · Finance ·
Accounting · Business Workflows · Design Patterns · Clean Architecture ·
Microservices · AI/LLM Integration · Engineering Leadership · Code Reviews ·
Technical Writing · Debugging · Production Incidents · Software Careers ·
Interview Prep.

All fit the same platform with **zero new machinery**.

## 13. The final objective

Someone who finishes these courses achieves three things **at once**:

1. They deeply understand software engineering concepts.
2. They understand how those concepts work **inside a real production Django ERP**.
3. They are significantly stronger for interviews and real engineering work.

> This platform should become one of the strongest assets of the whole project —
> our internal engineering academy today, a commercial educational product later.

---

## Related

- App: [config/learning/README.md](../config/learning/README.md)
- Human page: [kos/features/learning-courses.md](../kos/features/learning-courses.md)
- Content: [sql_course](sql_course/00_COURSE_OVERVIEW.md) · [deployment_course](deployment_course/00_COURSE_OVERVIEW.md)
- The knowledge source: [kos/README.md](../kos/README.md)
