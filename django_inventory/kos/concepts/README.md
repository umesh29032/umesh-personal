---
id: readme-concepts
type: system
verified: 2026-07-19
---

# Concepts — your backend engineering course, taught by your own project

*(Part of the [KOS](../README.md). Har concept-page ka backlink yahin aata hai.)*

## Why this folder exists — a teacher's note

You cannot become a strong backend engineer by reading definitions.
A definition tells you *what* a transaction is; it does not make you the
person who KNOWS where the boundary goes when six tables and real wages
are involved. That second thing only comes from seeing a concept **carry
weight in a real system** — and you own a real system.

So every page in this folder teaches one concept the same way a senior
sitting next to you would *(bilkul waise — "dekh, apne hi project mein
kya hota hai")*:

1. **The project hook** — the real problem in THIS repo that made the
   concept necessary. Not "imagine a bank" — YOUR settlement, YOUR ledger.
2. **The ladder** — beginner (simple words + analogy) → intermediate (how
   it works) → senior (Engineering Thinking: alternatives, rejections,
   trade-offs).
3. **The walkthrough** — real code, real SQL, real EXPLAIN plans, real
   bugs from this repo. Never invented examples.
4. **The interview corner** — the concept's *face-to-face form*: every
   question in 5 parts (Question → Short → Senior → **your project's
   story as the example** → follow-ups). This is how you answer like
   someone who has BUILT it, not read it.
5. **The closers** — 🧠 Remember This (Hinglish, one breath), 30-Second
   Revision (flash-card), What You Should Now Understand → next topic.

Read them in [Path 2 order](../README.md) — each page assumes the ones
before it.

## The sub-folders (and what each makes you)

| Folder | Pages | After reading, you can… |
|---|---|---|
| [django/](django/README.md) | transactions · orm-and-managers · migrations · settings | put boundaries where seniors put them; read the ORM like glass; change schemas without fear |
| [postgresql/](postgresql/README.md) | from-orm-to-sql · indexes · query-performance · locks · constraints | debug ANY slow/wrong query with evidence; design armor the app can't bypass |
| [architecture/](architecture/README.md) | service-layer · single-writer · two-truths | explain WHY this system is shaped this way — the three decisions everything else follows |
| [database-design/](database-design/README.md) | append-only-tables | design tables that can face an audit |
| [testing/](testing/README.md) | testing-strategy · local-testing-environment | test money like it's money — and get a clean factory to hand-test on |
| [security/](security/README.md) | auth-hardening | attack your own front door before someone else does |
| [patterns/](patterns/README.md) | 11 cross-app pattern cards | recognize + REUSE what the repo already solved (born from certification evidence) |

*(Naya concept tabhi aata hai jab project usse SACH mein use kare —
Project-Anchor Law. Kubernetes ka page tab banega jab Kubernetes aayega.)*

## How to study a page (the honest method)

- First pass: hook + Samjho Aise + Mental Model only. Close it. Explain
  the idea out loud in your own words. *(Bol ke samjhao — likha hua
  dhoka de sakta hai, bola hua nahi.)*
- Second pass: the walkthrough WITH the code open in your editor.
- Interview prep: read ONLY the corners + 30-Second Revisions, in Path-2
  order, and answer each question out loud using the project story.
- Something feels stale? Check the page's `verified:` date, then the code.
  Fix the page (Law 6) — that's also studying.
