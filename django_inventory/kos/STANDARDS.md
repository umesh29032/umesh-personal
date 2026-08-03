---
id: kos-standards
type: system
verified: 2026-07-19
---

# KOS STANDARDS — the constitution (1 page, frozen at Phase-1 approval)

> Har naya page yahan se paida hota hai. Yeh file badalti hai sirf owner ke
> kehne par. **docs/ = Claude ki engineering memory (HOW it was built).
> kos/ = insaan ki samajh (WHY it exists, HOW to think about it).**

## The 8 Laws

1. **Project-Anchor Law** — koi page tabhi banta hai jab project usse SACH MEIN
   use karta hai (file, model, URL, migration, bug). No Kubernetes page until
   this project runs Kubernetes. The project drives learning, never the reverse.
2. **One Canonical Page** — one feature = one page; one concept = one page.
   Nothing taught twice.
3. **Reference, Never Duplicate** — implementation truth docs/ aur code mein
   rehta hai; kos neeche link karta hai, kabhi copy nahi.
4. **Better, Not Bigger** — pehle existing page extend karo; naya page sirf
   genuinely naye feature/concept ke liye. `kos/README.md` is the ONLY index
   file, forever.
5. **Mentor Voice** — business → architecture → implementation → optimization
   → scalability, isi order mein. Simple bhasha, analogy, diagram. Kabhi
   assume mat karo ki reader topic jaanta hai. **Standardized voice pattern
   (frozen at Phase-1 approval):**
   `Business Purpose (professional English)` → `💡 Samjho Aise (Hinglish)` →
   `Technical Deep Dive (professional English)` → `🧠 Remember This (simple
   Hinglish summary)`. **Real SQL, real code, real bugs, real production
   stories — never generic examples.**
6. **Rewrite Freely** — docs/ append-only history hai; kos/ living
   understanding hai. Reality badle to page ré-likho, `verified:` date update karo.
7. **Real-Question Law** — every page must answer a real question the owner
   will ask while **building, debugging, learning, or interviewing**. Page
   proposal = pehle QUESTION likho. Question nahi bana? Page mat banao —
   existing page sudharo.
8. **Living-Mentor Law** — *The KOS is a living engineering mentor, not a
   historical record. Every page should increase understanding, improve
   engineering judgment, or accelerate future development. If a page cannot
   accomplish at least one of those goals, it should not exist. Historical
   implementation details belong in docs/; enduring knowledge belongs in kos/.*

## Frontmatter (every knowledge page)

```yaml
---
id: <stable-kebab-id>          # never changes, even if file moves
type: feature | concept | flow | project | debugging
verified: YYYY-MM-DD            # last checked against current code
knowledge_confidence: draft | verified_against_code | production_verified
answers: "<the real question this page answers>"   # Law 7, stated
related: [ids]
---
```

- **draft** — likha ja raha hai, claims unchecked.
- **verified_against_code** — har claim aaj ke codebase se check hua.
- **production_verified** — behavior production mein observe hua.

## Page anatomies

### CONCEPT page (the mentor unit)
1. **The project hook** — is project ki REAL problem jisne concept zaroori banaya
2. **💡 Samjho aise** (Beginner) — simple words + analogy
3. **Mental Model** — how an experienced engineer THINKS about this before
   reading any implementation (major pages)
4. **How it actually works** (Intermediate — Technical Deep Dive)
5. **Engineering Thinking** (Advanced/Senior) — why this design, which
   alternatives existed, why rejected, how a senior reasons
6. **How THIS project uses it** — files, tables, walkthrough; DB pages follow
   the Database Page Law below; include our actual past bugs
7. **What breaks without it** — concrete failure IN THIS PROJECT
8. **Common mistakes** — human ones
9. **AI Implementation Pitfalls** — ❌ list: what AI agents (any model) get
   wrong here; "always verify…"
10. **DSA & Complexity** — only where an algorithmic idea genuinely lives
    (Law 1 applies to DSA too — no textbook sections)
11. **Interview corner** — every important question in 5 parts:
    **Question → Short Answer → Senior Answer → Project Example → Follow-ups**
12. **🧠 Remember This** — simple Hinglish summary of the whole page
13. **30-Second Revision** — bullet flash-card block for quick interview prep
14. **What You Should Now Understand** → **Recommended Next Topic**
15. **Evolution / Future design** — optional; anchored to real registered futures
16. **Implementation references** — typed links (ADR / receipt / code / test / migration)
17. **Further reading** — official docs first, then max 2–3 curated items
18. **Related** — feature/concept/flow ids

### FEATURE page
Business Purpose · **Mental Model** · Architecture · **Engineering Thinking** ·
Request Flow · Frontend · Backend · Models · Database · Services · Permissions ·
Related URLs · Related APIs · Debugging Guide · **Change Impact** (modify this →
review these first) · **AI Implementation Pitfalls** · Implementation References ·
Learning Notes · Interview Notes (5-part format) · **🧠 Remember This** ·
**30-Second Revision** · *(optional)* Evolution / Future Design · Related Concepts

**Depth benchmark:** [features/settlement.md](features/settlement.md) is the
MAXIMUM depth — future core features match it, secondary features stay lighter.

### FLOW page
One end-to-end business story: actors → numbered journey crossing features →
diagram → what-can-go-wrong → links into feature pages + code.

### PROJECT page
The WHY layer — business story, system map, money story, roles. Prose + diagrams.

### DEBUGGING page
Symptom → how a senior thinks → where to look → which kos/docs page explains it.

## Database Page Law

Har database-related page yeh poori chain dikhata hai, REAL project query ke saath:

```
Django ORM code → the actual generated SQL → why PostgreSQL executes it
that way → which index serves it → EXPLAIN read-through → how to optimize
```

## Reference block format (bottom of every page — THREE sections, owner-ordered 2026-07-19)

```markdown
## Implementation References        ← docs/ ONLY: the ADRs, receipts,
- ADR: docs/adr/0005-….md             specs, deep-dives that explain it
- Built in: docs/<receipt>.md, migration <app> <number>
- Deep dive: docs/LEARNING_2_0/…

## Code References                  ← code ONLY: files, classes, functions,
- config/<app>/services/….py (`function_name`)   models, services, URLs,
- Tests: config/<app>/tests/…                    migrations. Cite file +
                                                 FUNCTION, never line numbers.
## Further Reading                  ← optional deeper study material
- Official docs first, then max 2-3 curated items
```

The bridge every page completes: *Business → Architecture → Flow →
Implementation References (docs) → Code References (Python) → Further
Reading.* KOS = **the translation layer between the project's
implementation knowledge (code + docs) and human understanding** — frozen
philosophy.

## kos-sync rule

Feature/change DONE nahi hai jab tak uska kos feature page + touched concept
pages same session update na ho. (docs-sync rule 12 ka human-layer mirror.
CLAUDE.md ratification Phase 8 mein.)

## The source-of-truth philosophy (owner-stated 2026-07-19 — PERMANENT)

```
Project code + docs/ + the running system      ← source of truth, always
              ↓
      Engineering Knowledge
              ↓
             KOS                               ← built ON TOP, never disconnected
              ↓
      Human Understanding
```

KOS is NOT replacing docs/ — the problem was never missing knowledge, it
was a human not knowing where to start or how things connect. So:
**prefer understanding + organizing + linking + teaching what docs/ already
holds over recreating it.** Extract directly from code ONLY when the
knowledge (a) doesn't exist in docs/, (b) docs are outdated, or (c) the
implementation changed. Every KOS page ends at exact docs + exact code —
nobody ever randomly searches docs/ again. End state: any AI agent
understands the project via CLAUDE.md + docs/; any developer via KOS;
knowledge is added once and stays understandable forever. *(Gyaan do baar
kabhi nahi likha jaata — ek baar docs mein bana, KOS mein samjhaya gaya.)*

## The README layer (owner-ordered, 2026-07-19)

Har folder ka apna **teacher README**: why the section exists · read order
· what-you-can-do-after · page table (page ↔ real question ↔ app/URLs).
Voice: majorly English, thodi Hinglish comments. Har content page apne H1
ke neeche breadcrumb rakhti hai — `> 📂 section-README link · KOS-home link`.
kos/README.md = master front door (app/URL navigation table lives there);
section READMEs = section teachers; **koi aur index file kabhi nahi** (Law 4).

## The app-navigation layer (owner-ordered 2026-07-19, discoverability pass)

`kos/apps/<app>/` = daily-development navigation, one consistent shape per
app: **README** (map: owns/doesn't-own/census/laws) · **urls.md** (every
route: business → handler → what-changes → where-it-ends → related
kos/docs/source) · **views.md** (handlers: purpose/gates/calls/side-effects)
· **models.md** (why/writers/readers/armor) · **services.md**
(responsibilities/callers/failure-modes). Rules: NAVIGATION only — point at
feature/concept pages, docs, and direct source paths; never re-teach;
everything verified against code; `type: app` frontmatter. Built app-by-app
with an owner gate after each. **Template additions (owner, post-expense
review):** README opens with a **Start Here** task table (endpoint/logic/
schema/permissions/flow/debug/tests → page) and ends with a **Change
Impact** summary (downstream systems + tests + gates); important WRITE URLs
carry a compact **Request Journey** block (Browser → URL → View → Permission
→ Service [@atomic·locks] → Models → external APIs → Response); views.md
opens with **handler groups** (READ / WRITE / ADMIN / DELETE / ASYNC —
absent groups stated as none). App order = owner's development frequency
(unclear → ASK). Every README also carries an **Engineering Checklist**
(pre-flight boxes before any change: app-specific laws, gates, test plan,
kos-sync). **An app is COMPLETE only when four scenarios pass:** (1) add a
feature without searching the repo (2) debug a production issue from the
symptom (3) add an endpoint knowing where each responsibility belongs
(4) a new engineer understands ownership + architecture from the app pages
alone. Metric: engineering NAVIGATION TIME — business requirement → correct
source file, fastest path.

**LOS learning elements (owner-ratified, post-expense-LOS review) — part of
the app template:** (1) **Mental Model** — a real-world analogy opens every
app README and every important feature/URL section (intuition BEFORE
implementation: expense=bank ledger, production=factory pipeline,
inventory=library catalog); (2) **Common Misconceptions** — the wrong
beliefs new developers bring, corrected explicitly; (3) **Real Engineering
Questions** — actual PM/production requests with the senior thinking-chain
(which invariants → services → transactions → tests → playbook); (4)
**Reading Strategy** — top of complex pages: what to read at
Beginner / Intermediate / Senior level. Philosophy line (owner-quoted):
*"every unknown term is a door, not a wall."* URL law stands: every URL
individually, no grouped summaries; simple → WHY simple, complex → WHY
complex. Path stays `kos/`; identity = LOS.

**FINAL two sections (owner, post-production review) — value-gated, never
mechanical:** **Engineering Decision** (problem · alternatives considered ·
why this one · trade-offs accepted · *would we still choose it today?*) and
**Evolution Timeline** (originally → problem discovered → refactor →
current → future direction) — added ONLY where a future reader will ask
"why on earth did we do it this way?". Include learn-from-absence (why a
route/feature does NOT exist) wherever true.

**🔒 TEMPLATE FROZEN (owner order).** The LOS template = everything above.
No new headings, ever, unless a **Validation Sprint task** exposes a
genuine gap. Validation Sprint protocol: 15–20 realistic engineering tasks;
per task ask *"could an engineer complete this using ONLY the LOS?"*;
every NO = backlog item, not failure. A stable template outranks a perfect one.

**Learning-OS refinement (owner, 2026-07-19): the project IS the textbook.**
Every app README also carries, as LINK-LAYERS into the concept canon (never
re-taught in place): **Business Purpose** answering WHY-a-separate-app (risks
isolated, principle followed, future evolution) · **Technology Stack** table
(each tech → its concept page) · **Security** section (authn/authz/
validation/threats/audit → linked canon) · **Required Knowledge** checklist
("to understand this app you should know: …", each item linked — reader
self-diagnoses, reads, returns) · **Learning Graph** ("Before this app read
… → After this app continue …"). App acceptance criterion (final): *a
beginner spending enough time in this app's KOS pages can confidently
understand, modify, and extend the real code without feeling lost.*

## Growth protocol

Project adopts X → X gets concept page + touched feature pages updated +
README paths updated. Directory tree kabhi restructure nahi hota — sirf
bharta hai. Rejected pages (Law 7 fail) get one line in the phase report,
never a file.
