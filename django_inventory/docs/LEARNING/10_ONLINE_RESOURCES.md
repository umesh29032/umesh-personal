---
id: learning-10-online-resources
type: lesson
status: active
owner: handwritten
scope: learning — generic concept
anchors: —
verified: 2026-07-13
---

# Online resources — har topic ka OFFICIAL link + "is project me kahan"

> Fresher ke liye: pehle column ka concept padho (link official docs ka hai —
> sabse bharosemand source), doosra column batata hai isi project me woh
> kahan LIVE use hua hai (real example > tutorial).

## Django basics
| Topic | Official link | Is project me kahan |
|---|---|---|
| Tutorial (start here) | docs.djangoproject.com/en/5.0/intro/tutorial01/ | poora project iska adult version hai |
| Models | docs.djangoproject.com/en/5.0/topics/db/models/ | `production/models/*.py`, `expense/models.py` |
| Field types + options | docs.djangoproject.com/en/5.0/ref/models/fields/ | DecimalField money (kabhi Float nahi!), JSONField metadata |
| ForeignKey + on_delete | docs.djangoproject.com/en/5.0/ref/models/fields/#django.db.models.ForeignKey | PROTECT money-anchors (KNOWLEDGE_MAP §6 policy) |
| Abstract base models | docs.djangoproject.com/en/5.0/topics/db/models/#abstract-base-classes | `core/models.py` TimeStampedModel |
| Custom managers | docs.djangoproject.com/en/5.0/topics/db/managers/ | `core` ActiveManager `.active` |
| Migrations | docs.djangoproject.com/en/5.0/topics/migrations/ | `*/migrations/`; data-migration = backfill known facts only |

## Queries & data
| Topic | Link | Yahan |
|---|---|---|
| QuerySet API | docs.djangoproject.com/en/5.0/ref/models/querysets/ | har service ka read code |
| Aggregation | docs.djangoproject.com/en/5.0/topics/db/aggregation/ | `payroll_service` SUM/Count rollups |
| F / Q objects | docs.djangoproject.com/en/5.0/topics/db/queries/#complex-lookups-with-q-objects | era filters (`Q(settlement_line__isnull=True) \| Q(...)`) |
| select_related / prefetch_related | docs.djangoproject.com/en/5.0/ref/models/querysets/#select-related | settlement preview joins; perf-baseline tests |
| Constraints (Check/Unique) | docs.djangoproject.com/en/5.0/ref/models/constraints/ | PSI XOR, finalized⇒settled_at, WST partial-unique |

## Transactions & locking (paisa-code ka backbone)
| Topic | Link | Yahan |
|---|---|---|
| Transactions / atomic | docs.djangoproject.com/en/5.0/topics/db/transactions/ | har service `@transaction.atomic` |
| select_for_update | docs.djangoproject.com/en/5.0/ref/models/querysets/#select-for-update | finalize/void/consume — lock-then-recheck |
| PostgreSQL explicit locking | postgresql.org/docs/current/explicit-locking.html | lock ORDER §11.5 samajhne ko |
| Advisory locks | postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADVISORY-LOCKS | `pg_advisory_xact_lock(5374)` |
| Isolation levels | postgresql.org/docs/current/transaction-iso.html | background theory |

## Views / URLs / forms / templates
| Topic | Link | Yahan |
|---|---|---|
| Class-based views | docs.djangoproject.com/en/5.0/topics/class-based-views/ | TemplateView/FormView/View pattern everywhere |
| URL dispatcher | docs.djangoproject.com/en/5.0/topics/http/urls/ | har `urls.py` (headers me route maps) |
| Forms | docs.djangoproject.com/en/5.0/topics/forms/ | `production/forms/`, expense forms |
| Templates | docs.djangoproject.com/en/5.0/topics/templates/ | `accounts/base.html` + partials |
| Messages framework | docs.djangoproject.com/en/5.0/ref/contrib/messages/ | har action ka redirect+message |
| Middleware | docs.djangoproject.com/en/5.0/topics/http/middleware/ | SidebarAccessMiddleware |

## Auth & security
| Topic | Link | Yahan |
|---|---|---|
| Custom User model | docs.djangoproject.com/en/5.0/topics/auth/customizing/ | `accounts/models.py` email login |
| Permissions/auth | docs.djangoproject.com/en/5.0/topics/auth/default/ | permission_service wraps it |
| Password hashing (Argon2) | docs.djangoproject.com/en/5.0/topics/auth/passwords/ | settings hashers |
| django-allauth | docs.allauth.org | Google OAuth (pre-provisioned only) |
| OWASP cheat sheets | cheatsheetseries.owasp.org | rate-limit/auth design background |

## SQL & PostgreSQL (saath me LEARNING/09 padho)
postgresql.org/docs/current/tutorial.html · use-the-index-luke.com (indexes
ki BEST free book) · postgresql.org/docs/current/sql-explain.html (EXPLAIN).

## Python (jahan atakो)
docs.python.org/3/tutorial/ · `decimal` module (paise INT/Decimal me, float
kabhi nahi): docs.python.org/3/library/decimal.html · `pathlib`, `re` refs.

## Frontend (server-rendered yahan)
MDN HTML/CSS/JS: developer.mozilla.org · CSS grid/flex: css-tricks.com/snippets/css/complete-guide-grid/ ·
DataTables: datatables.net/manual/ (list pages) · Paged print/media queries: MDN @media.

## Architecture patterns (yeh project kyu aisa hai)
| Concept | Link | Yahan |
|---|---|---|
| Service layer (a.k.a. application services) | martinfowler.com/eaaCatalog/serviceLayer.html | ADR-0001; `*/services/` |
| Ledger / append-only accounting | martinfowler.com/eaaDev/AccountingNarrative.html | WorkerLedgerEntry |
| Event sourcing-ish corrections | martinfowler.com/eaaDev/EventSourcing.html (background) | reverse/supersede chains |
| ADRs (decision records) | adr.github.io | `docs/adr/` |
| Open-closed principle | en.wikipedia.org/wiki/Open%E2%80%93closed_principle | StageHandler engine |
| Strangler-fig migrations | martinfowler.com/bliki/StranglerFigApplication.html | V2 dual-write → cutover |

## Seekhne ka tareeka (fresher steps)
1. Tutorial part 1–4 (Django) → 2. Is project ka KNOWLEDGE_MAP + LEARNING 01/03/04
→ 3. Ek chhota read-only view khud trace karo (My Earnings) → 4. LEARNING/09 SQL
levels 1–3 dbshell pe → 5. Phir paanch core service files. Link tab kholo jab
project ka code samajh na aaye — context ke saath padhna 10× tez hai.
