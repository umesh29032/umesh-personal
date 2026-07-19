---
id: kos-front-door
type: system
verified: 2026-07-19
---

# LOS — the Learning Operating System of the Django Inventory project

*(formerly "KOS"; the path stays `kos/` — stable links. The codebase is the laboratory; this system is the teacher.)*

> **KOS v1.0 — declared 2026-07-19.** 55 pages · 9 docs/ human guides ·
> frozen architecture (STANDARDS) · improvements now come from USE, not
> planning (v1.1 = the 30-day reality check). **Brand new here? →
> [START-HERE.md](START-HERE.md)** (productive by tomorrow) · going deep? →
> [engineering-journey](project/engineering-journey.md) (four weeks to mastery).

> **Kya hai yeh:** is project ki human understanding layer. `docs/` batata hai
> HOW it was built (Claude ki engineering memory — plans, ADRs, receipts,
> audits). **kos/ batata hai WHY it exists aur HOW to think about it** —
> business flows, features, concepts, learning, interviews. Rules:
> [STANDARDS.md](STANDARDS.md) (the 8 laws).

**The 4 purposes:** understand the project · understand AI-generated code ·
grow as a backend engineer · prepare for interviews — sab kuch ISI project
ke through.

## Map

```
kos/
├── README.md        ← you are here (the ONLY index — Law 4)
├── STANDARDS.md     ← the constitution
├── project/         ← WHY this project exists            ✅ Phase 2
│   └── business-story · system-map · money-story · people-and-roles · tech-stack
├── features/        ← one canonical page per feature     ✅ money (P3) + production (P4)
│   ├── settlement · ledger · payroll · advances
│   └── stage-tracking · allocation · cutting · machines · rbac-access
├── flows/           ← end-to-end business stories        ✅ P4
│   └── worker-gets-paid · cloth-to-garment · settlement-lifecycle · request-through-stack
├── concepts/        ← the mentor layer, project-anchored
│   ├── django/          transactions · orm-and-managers · migrations · settings
│   ├── architecture/    service-layer · single-writer · two-truths
│   ├── database-design/ append-only-tables
│   ├── postgresql/      locks · constraints · from-orm-to-sql · indexes · query-performance
│   ├── testing/         testing-strategy      security/  auth-hardening
│   ├── patterns/        11 cross-app reuse cards              ✅ hardening
│   └── deployment/      production-and-docker             ✅ P8
└── debugging/       ← symptom-first incident playbooks    ✅ P8
    └── money-looks-wrong · counts-mismatch · access-denied · page-slow
```

## Reading paths

**Path 1 — New to the project** ✅
1. [project/business-story.md](project/business-story.md)
→ 2. [project/system-map.md](project/system-map.md)
→ 3. [project/money-story.md](project/money-story.md)
→ 4. [project/people-and-roles.md](project/people-and-roles.md)
→ 5. [project/tech-stack.md](project/tech-stack.md)
→ 6. [flows/worker-gets-paid.md](flows/worker-gets-paid.md)
→ 7. [features/settlement.md](features/settlement.md)

**Path 2 — Learning backend engineering** *(grows every phase)*
1. [django/transactions](concepts/django/transactions.md)
→ 2. [architecture/service-layer](concepts/architecture/service-layer.md)
→ 3. [architecture/single-writer](concepts/architecture/single-writer.md)
→ 4. [database-design/append-only-tables](concepts/database-design/append-only-tables.md)
→ 5. [postgresql/locks](concepts/postgresql/locks.md)
→ 6. [postgresql/constraints](concepts/postgresql/constraints.md)
→ 7. [postgresql/from-orm-to-sql](concepts/postgresql/from-orm-to-sql.md)
→ 8. [postgresql/indexes](concepts/postgresql/indexes.md)
→ 9. [postgresql/query-performance](concepts/postgresql/query-performance.md)
→ 10. [django/orm-and-managers](concepts/django/orm-and-managers.md)
→ 11. [django/migrations](concepts/django/migrations.md)
→ 12. [django/settings](concepts/django/settings.md)
→ 13. [testing/testing-strategy](concepts/testing/testing-strategy.md)
→ 14. [security/auth-hardening](concepts/security/auth-hardening.md)
→ 15. [architecture/two-truths](concepts/architecture/two-truths.md) — the capstone

**Path 3 — Interview revision system** ✅ *(answer every question OUT
LOUD, using this project's story — that's the whole method)*

*Route A — Backend/Django round (~45 min):*
[transactions](concepts/django/transactions.md) → [orm-and-managers](concepts/django/orm-and-managers.md)
→ [migrations](concepts/django/migrations.md) → [settings](concepts/django/settings.md)
→ [service-layer](concepts/architecture/service-layer.md) → [request-through-stack](flows/request-through-stack.md)
— corners only. **Mock dialogue:** [transactions](concepts/django/transactions.md#mock-interview-walkthrough).

*Route B — Database round (~45 min):*
[from-orm-to-sql](concepts/postgresql/from-orm-to-sql.md) → [indexes](concepts/postgresql/indexes.md)
→ [query-performance](concepts/postgresql/query-performance.md) → [locks](concepts/postgresql/locks.md)
→ [constraints](concepts/postgresql/constraints.md) → [append-only-tables](concepts/database-design/append-only-tables.md).

*Route C — System-design round (~40 min):*
[money-story](project/money-story.md) → [worker-gets-paid](flows/worker-gets-paid.md)
→ [settlement](features/settlement.md) → [two-truths](concepts/architecture/two-truths.md)
→ [single-writer](concepts/architecture/single-writer.md) → [tech-stack](project/tech-stack.md)
→ [system-map](project/system-map.md). **Mock dialogues:**
[settlement](features/settlement.md#mock-interview-walkthrough) ·
[two-truths](concepts/architecture/two-truths.md#mock-interview-walkthrough).

*Route D — DSA round:* Path 4 below, framings only (~20 min).

*Rapid pass (night before, ~15 min):* read ONLY the **30-Second Revision**
blocks, Route C order first, then B, then A. *(Raat se pehle bas yeh —
naya kuch mat kholo.)*

*Study by target level* — every corner carries an **Interview Signal**
(the level where the concept typically appears, not difficulty). Prepare
your target level + one above *(apna level + ek upar)*:
- **🟢 Junior:** request-through-stack
- **🟡 Mid:** orm-and-managers · from-orm-to-sql · indexes · query-performance · settings · stage-tracking (FSM) · machines · auth-hardening · advances · cutting · rbac-access
- **🟠 Senior:** transactions · locks · constraints · append-only · single-writer · service-layer · testing-strategy · settlement · ledger · payroll · allocation · worker-gets-paid · cloth-to-garment · system-map
- **🔴 Staff:** two-truths · money-story · tech-stack

**Path 4 — DSA through the project** ✅ *(woven — sections live INSIDE
pages where each algorithm genuinely appears; no textbook tree, Law 1)*
1. Hash & sort aggregates → [from-orm-to-sql §10](concepts/postgresql/from-orm-to-sql.md)
2. Btree lookups + the cost model → [indexes §10](concepts/postgresql/indexes.md) · race-proof uniqueness → [constraints §10](concepts/postgresql/constraints.md)
3. Log + fold (events → state) → [append-only §10](concepts/database-design/append-only-tables.md)
4. N+1 & join placement → [query-performance §10](concepts/postgresql/query-performance.md)
5. Lazy builders (querysets as ASTs) → [orm-and-managers §10](concepts/django/orm-and-managers.md)
6. Finite state machines → [stage-tracking §DSA](features/stage-tracking.md)
7. Bounded counters + lock sharding (semaphore-in-SQL) → [allocation §DSA](features/allocation.md)
8. Fork-join barriers + partitions → [cutting §DSA](features/cutting.md)
9. Interval sets & stabbing → [machines §DSA](features/machines.md)
10. Set algebra + bulk evaluation → [rbac-access §DSA](features/rbac-access.md)
11. Star graphs (audit = O(1) per table) → [single-writer §10](concepts/architecture/single-writer.md)
12. Waits-for cycles + total ordering → [locks §10](concepts/postgresql/locks.md) · [transactions §9](concepts/django/transactions.md)
13. DAG topological sort → [migrations §10](concepts/django/migrations.md)
14. Complement testing (sampling the reject-region) → [testing-strategy §10](concepts/testing/testing-strategy.md)
15. Rate-limiter ladder → [auth-hardening §10](concepts/security/auth-hardening.md)

## Find it by app (jahan URL hai, wahin se dhoondo)

Every folder has its own **teacher README** (why the section exists, read
order, what you'll be able to do): [project/](project/README.md) ·
[features/](features/README.md) · [flows/](flows/README.md) ·
[concepts/](concepts/README.md) (+ one per sub-topic). Every page links
back to its section README.

**Working IN an app right now?** → [apps/](apps/README.md) — app-first
navigation: every URL → handler → service → model → file, in seconds.
(✅ all 9 apps mapped — [expense](apps/expense/README.md) ·
[production](apps/production/README.md) · accounts · inventory ·
raw_materials · tracking · machines · storefront · core.)

| You're touching… | Start at |
|---|---|
| `expense` app — `/expense/…` URLs (settlement, payroll, my-earnings, advances) | **[apps/expense/](apps/expense/README.md)** (URL/handler/model/service maps) · WHY: [features §Money](features/README.md); flow: [worker-gets-paid](flows/worker-gets-paid.md) |
| `production` app — dashboards (incl. `stalled/`), Adda/stage/cutting screens, flow editor + Stage library, worker reports | **[apps/production/](apps/production/README.md)** ([urls.md](apps/production/urls.md) = all 80 routes, each with its own section) · WHY: [features/README §Production](features/README.md) → stage-tracking · allocation · cutting; flow: [cloth-to-garment](flows/cloth-to-garment.md) |
| `accounts` / `inventory` — login, roles, sidebar, permissions | [rbac-access](features/rbac-access.md) · [people-and-roles](project/people-and-roles.md) · [auth-hardening](concepts/security/auth-hardening.md) |
| `machines` app | [machines](features/machines.md) |
| `raw_materials` — rolls, suppliers | [business-story](project/business-story.md) + [cloth-to-garment](flows/cloth-to-garment.md) step 0 (feature page comes with a future phase) |
| ANY unfamiliar URL | [request-through-stack](flows/request-through-stack.md) — the universal debug recipe |
| **Setting up a fresh machine** | [project/dev-setup.md](project/dev-setup.md) — clone → env → PG → seed → first safe commit |
| **Lost inside docs/ itself** | [project/reading-the-docs](project/reading-the-docs.md) — the human's map of Claude's engineering memory (7 piles, the shortlist, the routing rule) |
| **Something is BROKEN right now** | [debugging/README](debugging/README.md) — symptom-first playbooks with First-Five-Minutes thinking |
| `deploy/` — VPS, compose, backups | [production-and-docker](concepts/deployment/production-and-docker.md) + [docs/release/](../docs/release/) handbook |

## How to use this brain

- **Forgot something?** Search kos/ first; follow Implementation References
  down only if you need the history or the code.
- **AI wrote code you don't understand?** Find the feature page → Backend +
  Engineering Thinking sections explain the WHY; Common AI Mistakes lists
  what agents get wrong here.
- **About to modify a feature?** Read its **Change Impact** section FIRST.
- **Learned something new?** Improve the page (Law 6) and bump `verified:`.

## Page registry

| Page | Type | Confidence | Answers |
|---|---|---|---|
| [features/settlement.md](features/settlement.md) | feature | verified_against_code | "How does the factory decide and record what a worker has earned?" |
| [concepts/django/transactions.md](concepts/django/transactions.md) | concept | verified_against_code | "Why does settlement wrap everything in transaction.atomic, and what breaks without it?" |
| [flows/worker-gets-paid.md](flows/worker-gets-paid.md) | flow | verified_against_code | "What is the full journey from a worker stitching a piece to cash in their hand?" |
| [project/business-story.md](project/business-story.md) | project | verified_against_code | "What business does this software actually run?" |
| [project/system-map.md](project/system-map.md) | project | verified_against_code | "How is the codebase organized, and what path does every click take?" |
| [project/money-story.md](project/money-story.md) | project | verified_against_code | "How does money work here — from reported work to provable rupees?" |
| [project/people-and-roles.md](project/people-and-roles.md) | project | verified_against_code | "Who can see and do what — and how is it enforced?" |
| [project/tech-stack.md](project/tech-stack.md) | project | verified_against_code | "What runs this system, and why each boring choice?" |
| [features/ledger.md](features/ledger.md) | feature | verified_against_code | "Where does every rupee actually live, and how do I read the money book?" |
| [features/payroll.md](features/payroll.md) | feature | verified_against_code | "How does cash leave the factory, and how does anyone know what's still owed?" |
| [features/advances.md](features/advances.md) | feature | verified_against_code | "How do worker loans work without corrupting the earnings math?" |
| [concepts/architecture/service-layer.md](concepts/architecture/service-layer.md) | concept | verified_against_code | "Why does every write go through a service function?" |
| [concepts/architecture/single-writer.md](concepts/architecture/single-writer.md) | concept | verified_against_code | "Why does exactly ONE service own each money table, and how is that enforced?" |
| [concepts/database-design/append-only-tables.md](concepts/database-design/append-only-tables.md) | concept | verified_against_code | "Why are money/history tables never UPDATEd — and how do corrections work?" |
| [concepts/postgresql/locks.md](concepts/postgresql/locks.md) | concept | verified_against_code | "Row locks vs advisory locks — and why lock ORDER is the whole game?" |
| [concepts/postgresql/constraints.md](concepts/postgresql/constraints.md) | concept | verified_against_code | "Why 80+ CHECK constraints when services already validate?" |
| [features/stage-tracking.md](features/stage-tracking.md) | feature | verified_against_code | "How is who-did-what recorded — and correctable until money books?" |
| [features/allocation.md](features/allocation.md) | feature | verified_against_code | "How does the system stop paying for more pieces than were produced?" |
| [features/cutting.md](features/cutting.md) | feature | verified_against_code | "Where do 'pieces' come from — the moment cloth becomes countable?" |
| [features/machines.md](features/machines.md) | feature | verified_against_code | "Who holds which machine now — and who held it last Tuesday?" |
| [features/rbac-access.md](features/rbac-access.md) | feature | verified_against_code | "What machinery decides exactly what each user sees and reaches?" |
| [concepts/architecture/two-truths.md](concepts/architecture/two-truths.md) | concept | verified_against_code | "Why can't 'work happened' and 'money owed' be the same fact?" |
| [flows/cloth-to-garment.md](flows/cloth-to-garment.md) | flow | verified_against_code | "Roll of cloth → barcoded garments: every step and every blocker" |
| [flows/settlement-lifecycle.md](flows/settlement-lifecycle.md) | flow | verified_against_code | "Every state a settlement passes through — including corrections" |
| [flows/request-through-stack.md](flows/request-through-stack.md) | flow | verified_against_code | "One tap on a phone: what code runs, in order, and what can stop it?" |
| [concepts/postgresql/from-orm-to-sql.md](concepts/postgresql/from-orm-to-sql.md) | concept | verified_against_code | "What SQL does my queryset really run, and how do I SEE it?" |
| [concepts/postgresql/indexes.md](concepts/postgresql/indexes.md) | concept | verified_against_code | "Why does PG sometimes ignore my index?" |
| [concepts/postgresql/query-performance.md](concepts/postgresql/query-performance.md) | concept | verified_against_code | "Where does query time go, and how are regressions made impossible?" |
| [concepts/django/orm-and-managers.md](concepts/django/orm-and-managers.md) | concept | verified_against_code | "What is a Manager really — why Model.active, never a filtered default?" |
| [concepts/django/migrations.md](concepts/django/migrations.md) | concept | verified_against_code | "How does a money-bearing schema change without losing data?" |
| [concepts/django/settings.md](concepts/django/settings.md) | concept | verified_against_code | "How can production never boot half-configured?" |
| [concepts/testing/testing-strategy.md](concepts/testing/testing-strategy.md) | concept | verified_against_code | "What do 1,878 tests actually PIN in a money system?" |
| [concepts/security/auth-hardening.md](concepts/security/auth-hardening.md) | concept | verified_against_code | "What protects the front door — which real attacks were found and closed?" |
| [project/reading-the-docs.md](project/reading-the-docs.md) | project | verified_against_code | "1,100 docs files — where does a HUMAN start, and when do I go in there?" |
| [debugging/money-looks-wrong.md](debugging/money-looks-wrong.md) | debugging | verified_against_code | "A money number looks wrong — what do I check, in what order?" |
| [debugging/counts-mismatch.md](debugging/counts-mismatch.md) | debugging | verified_against_code | "Piece counts disagree between screens/stages — where is the truth?" |
| [debugging/access-denied-or-invisible.md](debugging/access-denied-or-invisible.md) | debugging | verified_against_code | "Can't see it / shouldn't see it — which of the four walls fired?" |
| [debugging/page-slow-or-erroring.md](debugging/page-slow-or-erroring.md) | debugging | verified_against_code | "Slow, 500ing, or deadlocking — where does a senior look first?" |
| [concepts/deployment/production-and-docker.md](concepts/deployment/production-and-docker.md) | concept | verified_against_code | "How does one person run this in production — and rebuild it by evening?" |
