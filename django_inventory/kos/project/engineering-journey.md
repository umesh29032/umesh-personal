---
id: project-engineering-journey
type: project
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "In what order should I learn EVERYTHING here — from zero to senior-level mastery of this system and the engineering inside it?"
related: [project-business-story, project-reading-the-docs]
---

# The Engineering Journey — zero to mastery, in order

> 📂 [Project — the WHY layer](README.md) · [LOS home](../README.md)
> *Productive-in-a-day version: [START-HERE](../START-HERE.md). This page
> is the longer road: expert.*

> 💡 **Samjho aise:** Yeh page ek **raasta** hai, syllabus nahi. Ek hi baithak
> mein poora padhne ki koshish mat karo — jo stop aaj kaam aa raha hai, wahi
> padho. Har stop pe ek hi shart hai: **bina dekhe, apne shabdon mein bolo.**
> Agar bol nahi paaye, to padha nahi — sirf dekha hai. Padhna aur samajhna alag
> cheezein hain, aur farq sirf bol ke pata chalta hai.

## How to walk it

One rule: **out loud or it doesn't count.** After every stop, close the
page and explain it to an empty chair *(khali kursi ko samjhao — jo atak
jaaye, wahi kal ka gap hai)*. Each week ends with a self-test. Pace is
suggested — mastery isn't a race; regressions mean re-read, not shame.

## Week 1 — The world and the money

| Day | Read | You now understand |
|---|---|---|
| 1 | [business-story](business-story.md) · [system-map](system-map.md) | the factory, the apps, the click-path |
| 2 | [money-story](money-story.md) · [worker-gets-paid](../flows/worker-gets-paid.md) | two truths, Expected→Earned→Paid |
| 3 | [reading-the-docs](reading-the-docs.md) + skim all 11 [ADRs](../../docs/adr/) | where knowledge lives; every locked WHY |
| 4 | [settlement](../features/settlement.md) (the depth benchmark) | the money gate, end to end |
| 5 | [transactions](../concepts/django/transactions.md) · [ledger](../features/ledger.md) | boundaries, locks-vs-atomicity, the book |

**Self-test:** explain to the chair: why does no money exist before
settlement, and what EXACTLY happens at finalize (locks → funnel →
validate → write → close)?

## Week 2 — Production truth + the database track

| Day | Read | You now understand |
|---|---|---|
| 1 | [cloth-to-garment](../flows/cloth-to-garment.md) · [cutting](../features/cutting.md) | the pipeline; where quantities are born |
| 2 | [stage-tracking](../features/stage-tracking.md) · [allocation](../features/allocation.md) | both-hands truth; the pool |
| 3 | [from-orm-to-sql](../concepts/postgresql/from-orm-to-sql.md) · [indexes](../concepts/postgresql/indexes.md) | reading SQL + plans like glass |
| 4 | [query-performance](../concepts/postgresql/query-performance.md) · [orm-and-managers](../concepts/django/orm-and-managers.md) | N+1, pins, managers |
| 5 | [locks](../concepts/postgresql/locks.md) · [constraints](../concepts/postgresql/constraints.md) | ordering, advisory keys, tiered armor |

**Self-test:** run the §4 captures from from-orm-to-sql YOURSELF in shell;
explain why PG ignored five indexes and was right.

## Week 3 — The architecture spine + operations

| Day | Read | You now understand |
|---|---|---|
| 1 | [service-layer](../concepts/architecture/service-layer.md) · [single-writer](../concepts/architecture/single-writer.md) | verbs, pens, enforcement |
| 2 | [two-truths](../concepts/architecture/two-truths.md) — the capstone; re-read slowly | boundary-drawing by change-physics |
| 3 | [append-only-tables](../concepts/database-design/append-only-tables.md) · [migrations](../concepts/django/migrations.md) | evidence-vs-state; fearless schema change |
| 4 | [settings](../concepts/django/settings.md) · [production-and-docker](../concepts/deployment/production-and-docker.md) | fail-fast; drilled recovery |
| 5 | [testing-strategy](../concepts/testing/testing-strategy.md) · [auth-hardening](../concepts/security/auth-hardening.md) · [rbac-access](../features/rbac-access.md) | pins; the walls; the front door |

**Self-test:** the 38→35 correction trace (two-truths §6) from memory,
both before AND after settlement.

## Week 4 — Mastery: debugging, DSA, interviews

| Day | Do | You now can |
|---|---|---|
| 1 | all 4 [debugging playbooks](../debugging/README.md) — walk each decision tree against the dev DB | investigate like a senior (First Five Minutes habit) |
| 2 | [DSA Path 4](../README.md) — all 15 stops, say each "interview framing" aloud | see structures inside business code |
| 3 | Interview [Route C](../README.md) (system design) + settlement + two-truths mock dialogues, OUT LOUD | survive the drill-down |
| 4 | Routes A + B (backend + database) | answer at 🟠 Senior signal level |
| 5 | remaining features (payroll · advances · machines) + [settlement-lifecycle](../flows/settlement-lifecycle.md) + the [🔴 Staff trio](../README.md) | defend trade-offs at staff altitude |

**Final self-test — the graduation question:** *"Design a system where
field workers report piece-work, managers verify, an owner settles batch-
wise with advance recovery, and every rupee stays provable for years —
under concurrency."* If your answer naturally produces two truths, one
gate, lock ordering, append-only corrections, and golden tests — you
didn't memorize this system. You UNDERSTAND it. *(Ab tum is project ke
engineer ho, sirf developer nahi.)*

## After the journey

Maintain mastery through USE: debug with the playbooks, revise with the
routes before interviews, and honor kos-sync — every change you ship
updates its page the same session. The KOS stays alive exactly as long as
it keeps being the first place you look.
