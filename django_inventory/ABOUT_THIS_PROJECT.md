# About this project — Kapil Enterprises Inventory

A narrative companion to [ARCHITECTURE.md](ARCHITECTURE.md).
ARCHITECTURE explains **what** the system is. This file explains **why** it
exists, **how** it grew, and **what I'm learning** as I build it.

---

## 1. The story

**Kapil Enterprises** is a family-run kids-garment manufacturer in India.
They make T-shirts, lowers, and "3-patti" suits — buying cloth in big rolls,
cutting them into pieces, stitching across many karigars (artisans) and
machines, packing, then dispatching to vendors who pay in tranches.

The factory ran on **paper and WhatsApp**. Lost batches, mis-counted rolls,
wages calculated from memory, no idea which dispatch was unpaid.

I'm building this app to:

1. Replace the paper register with a single source of truth.
2. Give the factory owner (Super Admin) a dashboard he can open on his
   phone after dinner.
3. Give each karigar a "My Work" view — what they did today, what's pending.
4. Track money in (vendor payments) vs money out (cloth purchase + wages).
5. Teach **me** Django + PostgreSQL by shipping something real.

---

## 2. Why Django + PostgreSQL (and not X)

| Decision | Reason |
|----------|--------|
| **Django over FastAPI** | I'm a beginner. Django gives me admin, auth, ORM, forms, and templates out of the box. FastAPI would force me to wire all of that. |
| **PostgreSQL over MySQL/SQLite** | CheckConstraints, partial indexes, `select_for_update()` work properly. The data model has multi-row invariants (input ≥ output + wastage) that I want enforced at the DB level, not just in app code. |
| **Server-rendered HTML over SPA** | Factory floor users are on cheap Android phones with patchy 4G. A 50 KB HTML page beats a 500 KB JS bundle. |
| **django-allauth** | Free Google OAuth + email signup. I can't reinvent that. |
| **whitenoise** | One-process static serving. No nginx config to learn yet. |
| **python-decouple** | `.env` first, no config gymnastics. |
| **No Celery (yet)** | No async jobs today. When I add SMS notifications I'll bring Celery + Redis. |

---

## 3. The journey — milestones in commit order

I'm keeping this loose so it survives refactors. Latest commit at the top.

1. **`feat: RBAC roles, BatchType workflow, Vendor/Payment CRUD, dynamic sidebar`**
   — admin can now add new product types at runtime without a migration.
2. **`Refactor code structure for improved readability and maintainability`**
   — split monolithic `views.py` / `services.py` / `forms.py` into packages.
3. **`feat: major refactor — service layer, secure OTP, DB indexes, new CRUD views`**
   — moved business logic out of views into `services/`. OTPs no longer
   stored in plaintext. Added composite indexes for dashboard queries.
4. Earlier: initial Django scaffold, cloth roll + batch CRUD, OTP login.

The big lesson from the last refactor: **signals are a footgun**. They
fired outside the transaction that triggered them, so a failed save would
leave half a ledger entry behind. I deleted every signal and made every
write go through a service. See [config/inventory/signals.py](config/inventory/signals.py)
— I left the file with a tombstone comment.

---

## 4. The mental model (read this once, you'll grok the codebase)

> **A `Batch` is a noun.** It's "the run of 500 t-shirts I started on
> April 24th." A batch has:
> - a **type** (T-Shirt, Lower, 3-Patti) — the recipe.
> - a list of **stages** (cut → stitch → pack) — the steps.
> - a stack of **cloth assignments** — which rolls feed it.
> - a roster of **worker assignments** — who's on it.
> - many **operation logs** — who did what for how long.
> - eventually, **products** — the finished t-shirts.
>
> Every time stock moves (in, out, consumed, wasted, produced), a
> **`StockLedger` entry** is written. The ledger is the truth; everything
> else is a view on top of it.

If you understand the paragraph above, you understand the app.

---

## 5. How it will work day-to-day

### Super Admin (the owner)
1. Opens dashboard → sees total cloth in stock, WIP batches, today's
   wastage, recent ledger movements.
2. Creates a new BatchType ("Hoodie") and chooses its stage template.
3. Adds new cloth rolls to inventory.
4. Reviews unpaid dispatches → records a payment.
5. Adds/removes team members, edits role permissions.

### Manager
1. Creates a new Batch ("Hoodie-2026-05-16, 300 pcs").
2. Reserves cloth rolls for the batch.
3. Assigns karigars to the batch.
4. Marks each stage In Progress → Completed as the day progresses.
5. Records dispatch when batch is done.

### Karigar
1. Opens **My Work** → sees today's assignments.
2. Logs the operation (start time, output qty, wastage qty, notes).
3. End of day — sees how many pieces they produced.

### Vendor (not in-app yet)
External — they pay; the manager records the payment.

---

## 6. What I'm learning (and where in the code)

This project is also my Django tutorial. Specific concepts and where they
show up:

| Concept | Where to look |
|---------|---------------|
| **Custom user model** | [config/accounts/models.py](config/accounts/models.py) — `AbstractUser` subclass, email as `USERNAME_FIELD`, custom manager |
| **Class-based views (CBVs)** | [config/inventory/views/](config/inventory/views/) — every CRUD is `ListView / CreateView / UpdateView / DeleteView` |
| **Mixins for permissions** | [config/inventory/views/mixins.py](config/inventory/views/mixins.py), `LoginRequiredMixin`, `UserPassesTestMixin` |
| **Model managers & querysets** | [config/inventory/services/](config/inventory/services/) — `select_for_update()`, `aggregate()`, `prefetch_related()` |
| **Generic relations (ContentType)** | `StockLedger.item` in [config/inventory/models.py](config/inventory/models.py) — one ledger that tracks any kind of item |
| **CheckConstraints** | `BatchStage.qty_reconciliation` — enforced at the **PostgreSQL** level, not just Python |
| **Composite indexes** | `Meta.indexes` on `Batch`, `BatchStage`, `StockLedger` |
| **Atomic transactions** | `@transaction.atomic` on every service write |
| **Form ModelForm + custom fields** | [config/inventory/forms/](config/inventory/forms/) and [config/accounts/forms.py](config/accounts/forms.py) |
| **Template context processors** | [config/inventory/context_processors.py](config/inventory/context_processors.py) — sidebar injected globally |
| **Settings split (env per environment)** | [config/config/settings/](config/config/settings/) |
| **Signing (HMAC-backed reversible token)** | `signing.dumps(password)` in signup flow — `accounts/views.py` |
| **OTP security** | [config/accounts/utils.py](config/accounts/utils.py) — `secrets.randbelow`, `hmac.compare_digest`, SHA-256 hashing |
| **Anti-enumeration** | `LoginView` and `ForgotPasswordView` always redirect the same way |
| **DB-backed sessions** | `SESSION_ENGINE='django.contrib.sessions.backends.db'` — revocable |
| **Signals (and why I dropped them)** | [config/inventory/signals.py](config/inventory/signals.py) — tombstone with reasoning |

---

## 7. Postgres-specific things I want to get right

I'm treating PostgreSQL as a first-class part of the stack, not "just the DB".

- **`CheckConstraint`** — assertions that the DB enforces. App bugs can't
  violate them. Look at `BatchStage` and `BatchStageMachineAssignment`.
- **`UniqueConstraint`** — multi-column uniqueness (e.g. one user can have
  exactly one role per batch).
- **Composite indexes** — `(status, -created_at)` answers "active batches
  newest-first" in a single B-tree scan.
- **`select_for_update()`** — row-level lock during cloth consumption.
  Prevents two managers from consuming the same roll concurrently.
- **`CONN_MAX_AGE`** — connection pooling. Cuts request latency.
- **`Generic relations`** with `ContentType` — built on Postgres FKs to
  the `django_content_type` table. Use sparingly; they bypass the schema's
  referential integrity.

I want to add later:
- **Materialized views** for the dashboard (it scans millions of ledger
  rows otherwise once the factory accumulates a year of data).
- **Partial indexes** (e.g. `WHERE is_active = TRUE`).
- **`EXPLAIN ANALYZE`** in CI for the dashboard query.

---

## 8. Decision log — things I *almost* did but didn't

- **DRF API** — I considered an API + React frontend. Dropped it: it
  would double my workload and the factory doesn't need a mobile app yet.
- **PostgreSQL `tstzrange`** for shift times — interesting but premature;
  start_time / end_time pair is fine.
- **Audit-log middleware** — covered by `StockLedger` for inventory; a
  full activity log will come if/when compliance is needed.
- **Multi-tenant SaaS** — Kapil is one tenant. If a second factory wants
  in, I'll add `tenant_id` everywhere; not now.

---

## 9. Open bugs / things to clean up

- **Stale shadow files**: `inventory/views.py`, `inventory/services.py`,
  `inventory/forms.py`, `config/config/settings.py`. The package
  versions of the same names are what actually load. Slated for deletion.
- **Tests are empty.** Every `tests.py` is a `pass`. Roadmap in
  ARCHITECTURE §13.
- **Storefront media** is local-FS only. Move to S3 before production.
- **Email** uses Gmail SMTP via app password. Move to SES/Postmark for prod.

---

## 10. How to learn from this codebase (suggested path)

If you're new to Django (or you're future-me coming back in 3 months):

1. Read [config/config/settings/base.py](config/config/settings/base.py) end-to-end.
2. Then [config/accounts/models.py](config/accounts/models.py) — the custom user.
3. Then [config/inventory/models.py](config/inventory/models.py) — the domain.
4. Then **one service** — start with [batch_service.py](config/inventory/services/batch_service.py).
   It shows transactions, validation, ledger writes, race protection.
5. Then **one view** — [batch_views.py](config/inventory/views/batch_views.py).
   See how thin views are once services exist.
6. Then [permission_service.py](config/inventory/services/permission_service.py)
   — the sidebar registry is the only place that knows about all the pages.

By that point you've seen 80% of the codebase's patterns.

---

## 11. Personal notes (Umesh)

- I am a junior dev. Please **explain the Django primitive** when you
  touch it, especially in code comments. Mention `select_related` vs
  `prefetch_related`, what `auto_now` vs `auto_now_add` does, what
  `on_delete=PROTECT` means.
- I prefer **junior-friendly explanations** with the "why" included.
- I want this repo to be **trainable** — i.e. when Claude reads it later,
  it should "get" the architecture from CLAUDE.md + ARCHITECTURE.md + this
  file without having to re-read every model.
- I want to do my **personal projects separately** from company work. This
  repo's `.claude/` is project-local: skills here don't leak into other
  projects.

Last updated: 2026-05-16.
