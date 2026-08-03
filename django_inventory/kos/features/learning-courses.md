---
id: feature-learning-courses
type: feature
verified: 2026-07-31
knowledge_confidence: production_verified
answers: "Where do I actually READ the courses, and how does the /learn/ section work without storing any content?"
related: [concept-local-testing-environment, concept-testing-strategy, feature-rbac-access]
---

# Learning Courses — the `/learn/` reader

> 📂 [Features](README.md) · [KOS home](../README.md)

## Who can see the courses (owner ruling 2026-08-02)

**One idea first:** the courses are for **you and people in your domain** — not for
factory workers. A cutting master has no use for a PostgreSQL chapter.

**💡 Samjho aise:** factory ka gate aur classroom ka gate **alag** hone chahiye. Worker
ko factory chahiye, classroom nahi. Aapke bhai ko classroom chahiye, factory **bilkul
nahi**. Isliye ek naya **`student`** role banaya — sirf padh sakta hai, factory ka kuch
nahi dekh sakta.

| Role | Sees "Learn"? |
|---|---|
| `super_admin` (you) | ✅ always — you can never lock yourself out |
| **`student`** (new) | ✅ courses only, **zero** business access |
| `manager` · `worker` · `accountant` · `listing_team` | ❌ |

**You control it from the UI, no code:**
Access Control → **Sidebar Access** → the **Learn** row → tick/untick roles → Save.

**To give someone the courses:** create their user, set role = **Student**. They can log
in, read every chapter, keep their own progress — and see nothing of the factory.

> ⚠️ **Why a menu rule alone was not enough.** Hiding the menu item blocks `/learn/`, but
> `can_access_url_name()` allows any URL with **no** rule — and only `learning:index` has
> one. So a blocked user could still type `/learn/sql/14-indexes/`. Every learning view
> now checks that same one switch (`_LearningAccessMixin`), so the whole section moves
> together. Pinned by a test that types the URL directly.

**The `student` role is a system role** — it cannot be deleted, because deleting it would
silently strip access from every student pointing at it.

Future paid courses fit this shape unchanged: a paying customer is a `student`.

## Business Purpose

The engineering knowledge of this project lived only in markdown files — perfect
for an editor, useless for *reading like a course*. `/learn/` turns those same
files into a browsable site: an index of courses, a chapter list, a reading page
with an on-page table of contents, prev/next buttons, and one generated page
holding every interview question.

The owner's reason is concrete: **hand this to someone who knows nothing** — a
younger brother, a new developer — and have them learn how a real factory system
was built, from "what is a database" to "how do I deploy this and not lose money".

## 💡 Samjho Aise

Pehle saara gyaan `docs/` ke andar `.md` files mein tha — likhne ke liye theek,
padhne ke liye bekaar. Ab wahi files **website ban gayi hain**: `/learn/` pe jao,
course chuno, chapter kholo.

Sabse important baat: **content ki doosri copy nahi banayi.** Website wahi `.md`
file **padh ke** dikhati hai. Matlab `.md` badla → website apne aap badal gayi.
Do copy hoti to ek din dono alag ho jaati (aur is project ne wo galti ek baar
pehle bhugat li hai). **Ek hi sach, do jagah dikhta hai.**

## Mental Model

> **This app is a WINDOW, never a store.**
>
> ```
>    docs/sql_course/*.md          ─┐
>    docs/deployment_course/*.md   ─┼──▶  learning app  ──▶  /learn/ pages
>                                   │      (reads + renders)
>    THE SINGLE SOURCE OF TRUTH ────┘      no content models, ever
> ```
>
> It owns **no content tables** — only per-user progress (`LessonProgress`,
> `Bookmark`). If any other model appears in `config/learning/`, the law has been
> broken, and two tests fail: `test_app_has_no_CONTENT_models` and
> `test_no_model_stores_chapter_text`.

## The pages

| URL | What it shows |
|---|---|
| `/learn/` | all courses, continue-learning card, stats, search box |
| `/learn/<course>/` | that course's chapters, in teaching order |
| `/learn/<course>/<chapter>/` | one chapter: prose, TOC, prev/next |
| `/learn/interview/` | **every** interview question, Junior → Staff |
| `/learn/revise/mistakes/` · `/learn/revise/cheatsheet/` | generated revision pages |
| `/learn/search/?q=` | search every chapter |

Three courses today: **SQL & PostgreSQL From Zero** (26 pages), **Deployment From Zero**
(46) and **Git & GitHub From Zero** (41, added 2026-08-03) — **113 pages** in total.

### What the git course is for (added 2026-08-03)

40 teaching chapters in five parts: **Foundations** (01–08) → **Branching** (09–17) →
**Collaboration** (18–24) → **Discipline** (25–33) → **Recovery & depth** (34–40).

Two things make it different from every git tutorial:

1. **It is taught from THIS repo's own workflow and its real incidents** — `CONTRIBUTING.md`,
   the three `git-hooks/`, `ci.yml`, `CODEOWNERS`; PR #15's 289 commits; the merge commit
   `83a144ba` with its two parents; `.git` at 97 MB; the **two committed `pg_dump` files** and
   why history was deliberately *not* rewritten; the **dead `/deploy/` CODEOWNERS rule**; the
   stale-local-`main` **296-vs-1** trap; `bod` sitting outside the test gate.
2. **It is honest about money.** Branch protection, required reviews, required status checks,
   CODEOWNERS auto-assignment and secret scanning are **paid on private repos**. Most guides
   just say "enable branch protection". This one names the paid line, shows the free path, and
   states each layer's weakness — including the two failures **nothing** catches.

> 💡 **Samjho aise:** iska sabse kaam ka sabaq: **jo muft wala taala hai, wo paid se bhi
> mazboot hai.** Collaborator ko **Read** do aur **fork** se kaam karwao — uske paas push ki
> chaabi **hi nahi** hoti. Paid branch protection kehta hai "chaabi hai, par us darwaze pe
> nahi". Chaabi na dena behtar hai.

## Three pages that write themselves

One engine — `harvest_section(heading)` — collects a named section from **every
chapter of every course**. Three pages ride on it:

| Page | Built from | Today |
|---|---|---|
| `/learn/interview/` | `# Interview Questions` | **499 questions**, Junior→Staff |
| `/learn/revise/mistakes/` | `# Beginner Mistakes` | **109** chapters |
| `/learn/revise/cheatsheet/` | `# Cheat Sheet` | **109** chapters |

> 💡 **Samjho aise:** Yeh teen page **likhe nahi gaye** — chapters se **nikaale**
> gaye hain. Chapter mein sudhaar karo, page apne aap sudhar jaata hai. Ek hi
> jagah likho, teen jagah dikhe — yahi poore system ka usool hai.

## Plus: search, progress and shortcuts

- **Search** (`/learn/search/`) — literal match across all 72 chapters, ranked by
  hit count, snippet cleaned of markdown and the term highlighted. Not fuzzy on
  purpose: a result is never a mystery.
- **Progress** — opening a chapter *is* the signal, so the continue-learning card,
  completion bars, ✓ ticks and day-streak work without pressing anything. `Mark
  complete` and `Bookmark` are POST-only endpoints, kept apart from the GET-only
  content pages. Per-user and isolated (a test pins that).
- **Keyboard shortcuts** — `/` search · `j`/`k` next/previous chapter · `g i`
  interview prep · `g l` home. Never fires while you are typing.

## The clever bit: the interview page writes itself

Every chapter has an `# Interview Questions` section whose bullets are labelled
`**Junior:** … — answer`. The app **harvests those** into one page grouped by
level: currently **499 questions** (Junior 136 · Mid 133 · Senior 123 · Staff 107),
each with its answer and a link back to the chapter that teaches it.

Nothing is written twice. Fix a question in the chapter and the prep page fixes
itself. *(Yeh page banaya nahi gaya — chapters se **nikala** gaya hai.)*

## Technical Deep Dive

- **Renderer:** `markdown-it-py` (CommonMark + tables) with **Pygments** for code
  highlighting. Both were already installed — this feature added **no dependency**.
- **Safety:** the parser runs with `html=False`, so raw HTML inside a `.md` is
  escaped rather than executed. An unknown code-fence language falls back to plain
  `<pre>`, so an ASCII diagram can never break a page.
- **Link rewriting:** the courses cross-reference each other as `.md` files (so
  they stay readable in an editor and on GitHub). At render time those become
  `/learn/...` URLs — which is why **Ctrl+click opens a chapter in a new tab**,
  exactly how the owner wanted to read.
- **Read-only by construction:** `http_method_names = ['get','head','options']`
  → a POST to a course page is a 405, pinned by a test.
- **Caching:** `lru_cache` over chapter discovery, every section harvest and the
  search corpus; `services.reload_courses()` clears **all** of them after editing a
  `.md` mid-session (a test pins that none survives, or a generated page would go
  quietly stale).
- **Progress storage:** content is referenced by **string slugs, not ForeignKeys** —
  there is no content table to point at, and string keys keep the rows portable if
  the courses are ever re-organised or served elsewhere.

## Mobile-first (verified, not claimed)

Checked in a real browser:

| Width | Layout | Page scrolls sideways? |
|---|---|---|
| 360 px | one column, TOC collapses | **no** — diagrams scroll inside their own box |
| 768 px | one column, roomier | no |
| 1280 px | prose + sticky TOC rail | no |

## Adding a course later

1. Drop `.md` files into `docs/<name>_course/`, named `NN_Title.md`.
2. Add one `Course(...)` entry in `config/learning/registry.py`.

Everything else — cards, chapter lists, prev/next, TOC, interview harvesting —
comes for free. A test (`test_every_markdown_file_is_reachable`) refuses to let a
file sit in a course folder unserved; that regression already happened once, with
the deployment course's `ARCHITECTURE.md`.

## What breaks without this

The knowledge stays in a folder only a developer opens. The owner cannot hand the
system's reasoning to anyone who isn't already reading the repo — which was the
whole point of writing it down.

## Interview prep: every chapter now tells you *why* they ask

**One idea first:** knowing the answer is not the same as knowing what the question is
*testing*. Every chapter of both courses now ends its interview section with a small
table that names the difference.

**💡 Samjho aise:** interview ek exam nahi, ek **audition** hai. Sawaal "index kya hai?"
ka matlab hai *"kya tumhe pata hai index ki keemat bhi hoti hai?"* Jo bolta hai "index
query fast karta hai" — theek, par adhoora. Jo bolta hai "reads fast, **writes slow,
disk zyada**" — usne sawaal ke peeche ka sawaal sun liya. Yahi farq table dikhati hai.

Each block has four parts:

| Part | What it gives you |
|---|---|
| **Testing for** | the real competence behind the question |
| **Weak answer** | a *plausible* mid-level answer that sounds fine and is shallow |
| **What lands** | the answer that gets the offer, with a concrete anchor bolded |
| **The killer follow-up** | the brutal second question that separates memorised from lived |

**The weak answer is never a straw man.** It is deliberately the answer a competent
developer would actually give — because recognising your own current answer in that
column is the whole point.

Where to read them: `/learn/<course>/<chapter>/`, at the end of **Interview Questions**.
All **69 teaching chapters** have one (2026-08-01), and a test fails the build if any
chapter loses it — including if a stray `|` breaks the table, which markdown does
silently.

## The bug that taught us the most: "written but never shown"

**One idea first:** a generated page can be *wrong by being incomplete*, and it
will never tell you. It renders. It looks finished. It is missing half the content.

**💡 Samjho aise:** *(ye kahani 2026-08-01 ki hai, jab bank mein 339 sawaal the — aaj 499 hain.)*
socho tumne 339 sawaal ek notebook mein likhe. Ab ek naukar ko
bola: "notebook se sawaal chipka do board pe." Wo sirf un pages se chipkata hai jinke
top pe **bilkul** `Interview Questions` likha ho. Tumne ek page pe likh diya
`Interview Questions (poora course, 4 levels)` — bas, wo page skip ho gaya. Board pe
board dikh raha hai, bhara hua lag raha hai, **koi error nahi** — par 185 sawaal
gayab. Yahi hua tha.

Teen alag-alag versions of the same mistake were found on 2026-08-01 — **aur ek chautha
2026-08-03 ko** (neeche #4):

1. The harvester wanted an **exact** heading, so `# Beginner Mistakes (the greatest
   hits)` matched nothing.
2. The interview page kept its **own private copy** of that matching rule — a second
   source of truth inside the app whose whole law is "one source of truth".
3. The rule read **one line only**, but answers wrap over several lines. So the
   deployment course's 185 questions were dropped, and 6 more lost their answers.
4. **(2026-08-03)** A `# ` at column 0 **inside a ``` code fence** ended the section
   early. And this is not a contrived shape: `# Conflicts:` is *git's own merge output*,
   quoted in the git course's conflicts chapter — so a Cheat Sheet showing that line
   would have silently lost everything after it. Fixed fence-aware, and pinned twice:
   one unit test proven to fail against the old code, and one corpus test asserting
   every harvested section shows its full length.

### How to check it yourself (any generated page)

Count what the chapters *claim*, then count what the page *shows*. If the two numbers
differ, content is being lost.

```bash
cd ~/umesh-personal/django_inventory

# 1. What do the chapters CLAIM? (count every level label written by hand)
grep -rhoE '^-\s+\*\*(Junior|Mid|Senior|Staff):\*\*' \
  docs/sql_course docs/deployment_course docs/git_course | wc -l
```
Expected output: `499`  *(339 before the git course was added)*

> **Match the parser's exact shape, not an approximation of it.** The parser wants a bullet:
> `- **Junior:** …`. Earlier versions of this check used a looser `\*\*(Junior|Mid|…)\b`,
> and it produced *false alarms twice*:
>
> - without `\b`, `**Middleware:**` counted as a "Mid" question → `340`;
> - **with** `\b` it still over-counted, because `\b` matches before a hyphen — so
>   `**Mid-flight:` and `**Mid-rebase:` in the git course's rebase chapters counted as
>   questions → `501` against a real `499`.
>
> That second one is the instructive failure: the check reported 2 missing questions when
> nothing was missing at all. **A counting check that is looser than the parser will cry wolf,
> and a check that cries wolf gets ignored — which is worse than no check.** Requiring the
> full `- **Level:**` bullet makes the count exactly what the harvester sees.

```bash
# 2. What does the PAGE actually show?
env/bin/python config/manage.py shell --settings=config.settings.local -c \
  "from learning import services as S; print(S.interview_questions()['total'])"
```
Expected output: `499`

**Same number = nothing lost.** Different numbers = go find the format that does not
match. The test `test_every_labelled_question_reaches_the_interview_bank` now does
this comparison automatically, so it can never silently return.

### The confusing bits, named

- **"It renders, so it works"** — no. Rendering proves the template ran, not that the
  content arrived. Only counting proves completeness.
- **Two places doing the same parsing** is the real bug; the wrong regex was just the
  symptom. Fixing one copy left the other broken, which is exactly why the law says
  *one* source of truth.
- **`$` in a regex means end of LINE**, not end of the item. That single character
  dropped 185 questions.

### The undo

Every one of these fixes is in `config/learning/services.py` and is pure reading
logic — no data, no migration. To undo, `git checkout config/learning/services.py`.
Nothing in the database changes, because the courses have no database.

## Common mistakes

- **Assuming a generated page is complete because it renders.** Count the source
  against the page (see the section above). This cost 185 interview questions.
- **A second copy of any parsing/matching rule.** If two functions decide "where does
  this section start", one of them will be wrong and nobody will notice.
- **Copy-pasting a chapter into a template.** That is the second copy; it will
  drift. Always render the `.md`.
- Adding a model for anything other than **per-user state**. Progress models are
  allowed (and built); a model holding chapter text, titles or ordering is the law
  being broken — that data belongs in the markdown.
- Forgetting `reload_courses()` after editing a `.md` while the server runs.
- Writing page CSS outside `.learn-page` — it would leak into the whole app
  (UI rule 10).

## 🧠 Remember This

`/learn/` ek **khidki** hai, godown nahi. Content `docs/*.md` mein hi rehta hai;
app use padh ke dikhata hai — isi liye course aur docs **kabhi alag nahi ho
sakte**. Naya course chahiye? `.md` folder + registry mein ek line — **git course
2026-08-03 ko bilkul isi tarah aaya**, 41 files + ek line, aur teeno generated page
khud bhar gaye. Aur interview page **khud ban jaata hai** chapters se — **499
sawaal**, level ke hisaab se, jawaab ke saath.

## Implementation References

- App: [config/learning/README.md](../../config/learning/README.md) (files, rules, tests)
- Courses: [docs/sql_course/](../../docs/sql_course/00_COURSE_OVERVIEW.md) · [docs/deployment_course/](../../docs/deployment_course/00_COURSE_OVERVIEW.md)
- Practice DB for the SQL course: [local-testing-environment](../concepts/testing/local-testing-environment.md)

## Code References
- `config/learning/registry.py` (course list) · `services.py` (render + harvest) · `views.py` (4 GET-only views) · `tests/test_learning.py` (19 pins)
