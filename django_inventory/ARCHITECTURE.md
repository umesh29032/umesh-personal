# ARCHITECTURE — Kapil Enterprises Inventory System

> A factory-floor ERP for a kids-garment manufacturer.
> Tracks raw cloth → batches → cutting → stitching → packing → dispatch → payment.
> Written in **Django 5.2 + PostgreSQL** with a strict service-layer architecture.

This document is the technical contract. If something here disagrees with the
code, the **code wins** — please open a PR to update this doc.

> ## ⚠️ Major restructure 2026-05-19
>
> The original `inventory` app's BatchType/Batch/Stage/Machine/StockLedger/Vendor/Payment system was **removed** and replaced with three new apps:
> **`raw_materials`** (cloth + master data), **`production`** (Product/Adda/Workflow/Stage records), **`tracking`** (BatchBarcode QR + history). The `inventory` app now owns RBAC + dashboards only.
>
> **Canonical docs for the new flow live in [docs/production/OVERVIEW.md](docs/production/OVERVIEW.md).** Sections below this banner describe the old architecture and are kept for historical context only; they DO NOT reflect the current code.

---

## 1. 10,000-foot view

```
┌────────────────────────────────────────────────────────────────────┐
│                    PUBLIC STOREFRONT  /                            │
│              (Hero, categories, featured products — DB-driven)     │
└──────────────────┬─────────────────────────────────────────────────┘
                   │  "Login / Get Started"
                   ▼
┌────────────────────────────────────────────────────────────────────┐
│  AUTH  /app/                                                       │
│  ┌──────────────┐   ┌─────────────┐   ┌──────────────┐             │
│  │ OTP login    │   │ Password    │   │ Google OAuth │             │
│  │ (default)    │   │ (fallback)  │   │ (allauth)    │             │
│  └──────────────┘   └─────────────┘   └──────────────┘             │
│  OTP → SHA-256 hash in session + 5-min expiry + 3-try lockout      │
└──────────────────┬─────────────────────────────────────────────────┘
                   │  on success
                   ▼
┌────────────────────────────────────────────────────────────────────┐
│  INVENTORY APP  /inventory/                                        │
│                                                                    │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│   │ Cloth    │──▶│ Batch    │──▶│ Stages   │──▶│ Products │        │
│   │ Roll     │   │ (run)    │   │ (steps)  │   │ (finished│        │
│   └──────────┘   └────┬─────┘   └────┬─────┘   │  goods)  │        │
│                       │              │         └────┬─────┘        │
│                       ▼              ▼              │              │
│                  ┌─────────────────────────┐        │              │
│                  │   StockLedger           │◀───────┘              │
│                  │   (single source of     │                       │
│                  │    truth, append-only)  │                       │
│                  └─────────────────────────┘                       │
│                       │                                            │
│                       ▼                                            │
│   ┌───────────┐   ┌──────────────┐   ┌──────────┐                  │
│   │ Vendor    │──▶│ Dispatch     │──▶│ Payment  │                  │
│   └───────────┘   └──────────────┘   └──────────┘                  │
└────────────────────────────────────────────────────────────────────┘

                  ┌──────────────────────────┐
                  │ RBAC + Sidebar registry  │
                  │ permission_service.py    │
                  └──────────────────────────┘
```

---

## 2. Apps

| App | Purpose | Tables |
|-----|---------|--------|
| `accounts` | Custom user, OTP auth, signup, password reset, skills, user CRUD | `User`, `Skill` |
| `inventory` | Production ERP (cloth, batches, stages, dispatch, payments, RBAC) | `Stage`, `BatchType`, `BatchTypeStage`, `Machine`, `ClothRoll`, `Batch`, `BatchStage`, `BatchStageMachineAssignment`, `BatchClothAssignment`, `BatchUserAssignment`, `BatchOperation`, `Product`, `StockLedger`, `Vendor`, `VendorDispatch`, `Payment`, `Role` |
| `storefront` | Public marketing homepage (admin-editable) | `HomePageConfig`, `Category`, `FeaturedProduct`, `HeroShowcaseCard`, `WhyUsCard`, `FooterLink`, `NavLink` |

---

## 3. Settings split

Modular settings — picked by `DJANGO_SETTINGS_MODULE`:

```
config/config/settings/
├── base.py         # shared (apps, middleware, DB, allauth, sessions, logging)
├── local.py        # DEBUG=True, ALLOWED_HOSTS=*, allauth verification off
└── production.py   # hardening (HSTS, secure cookies, prod ALLOWED_HOSTS)
```

(The legacy `config/config/settings.py` shadow file was deleted on 2026-05-16
after verifying no imports referenced it. The settings package is now the only
source.)

Secrets come from `.env` via `python-decouple` — never hard-coded.

---

## 4. Data model — domain breakdown

### 4.1 Production catalog

```
Stage  (master list of physical/logical steps)
  │  stage_type:  STORAGE | PROCESSING
  │  category:    PRODUCTION | LOGISTICS | FINANCIAL
  │
  ├──◇ BatchTypeStage ◇── BatchType   (T-Shirt, Lower, 3-Patti…)
  │      └─ sequence_order (template order)
  │
  └──◇ Machine                          (sewing machine, cutter…)
```

`BatchType` is the **template**. Each new `Batch` clones its
`BatchTypeStage` rows into per-batch `BatchStage` rows so editing the
template doesn't retro-mutate live batches. New batch types may be added at
runtime by admins — no migration required.

### 4.2 Batch lifecycle

```
Batch  (the actual production run)
  status: DRAFT → PLANNED → WIP → COMPLETED | CANCELLED
  │
  ├── BatchStage[]                  cloned from template; execution layer
  │     status: PENDING → IN_PROGRESS → COMPLETED | SKIPPED
  │     input_qty, output_qty, wastage_qty  (CheckConstraint: in ≥ out + waste)
  │     │
  │     └── BatchStageMachineAssignment[]   stitching fan-out: many (machine, worker) per stage
  │
  ├── BatchClothAssignment[]        which rolls feed this batch
  │     status: RESERVED → CONSUMED
  │     reserved_length, consumed_length, wastage_length
  │
  ├── BatchUserAssignment[]         karigars on this batch (soft-delete via is_active)
  ├── BatchOperation[]              per-session worker log (start/end/output/wastage)
  └── Product[]                     finished goods produced
```

### 4.3 StockLedger (universal ledger)

The **only** source of truth for stock movement. `transaction_type` ∈
`INWARD | OUTWARD | CONSUMPTION | WASTAGE | TRANSFER | PRODUCTION | ADJUSTMENT`.

- Generic relation (`ContentType + object_id`) — points to *any* item type
  (ClothRoll, Product, future SKUs).
- Append-only — no row is ever updated; corrections create an `ADJUSTMENT`.
- All inserts go through `StockService.log(...)` inside a service-level
  `@transaction.atomic`. **Signals are deliberately not used** (see
  [config/inventory/signals.py](config/inventory/signals.py) for the rationale).
- Indexed: `(batch, transaction_type, -date)` for dashboard "recent movements"
  + per-item history queries.

### 4.4 Logistics & finance

```
Vendor ─< VendorDispatch >─ Batch
                │            BatchStage (optional execution context)
                ▼
            Payment   (mode: CASH | BANK_TRANSFER | UPI | CHEQUE | OTHER)
```

`on_delete=PROTECT` everywhere on finance FKs — you cannot delete a batch
with dispatches or a vendor with payments. This is intentional: audit trail
must survive.

### 4.5 RBAC

```
Role (Super Admin, Manager, Karigar)
  ├── code: stable slug used in code
  ├── permissions: M2M to auth.Permission  (Django's built-in codenames)
  └── is_system: cannot be deleted

User
  ├── role: FK → Role            (RBAC source of truth, post-refactor)
  └── user_type: legacy CharField (kept for backward compatibility with old views/mixins)
```

Decision precedence in `user_role_code(user)`:
1. Superuser → `super_admin`
2. `user.role.code` if set
3. Legacy `user.user_type` mapped to a role code
4. Otherwise → `None` (treat as unauthorized)

---

## 5. Request lifecycle (CRUD page example)

A typical "edit batch" hit:

```
GET /inventory/batches/edit/42/
   │
   ▼
config/config/urls.py  ── routes 'inventory/' to inventory.urls
   │
   ▼
inventory/urls.py    ── path 'batches/edit/<int:pk>/' → BatchUpdateView
   │
   ▼
LoginRequiredMixin   ── redirects to /app/ if anonymous
ManagerOrSuperuserMixin  ── 403 if not management
   │
   ▼
BatchUpdateView (CBV in inventory/views/batch_views.py)
   │
   ▼
TEMPLATE  inventory/batch_form.html
   ├─ {% extends 'inventory/base.html' %}
   ├─ context processor `inventory.context_processors.sidebar`
   │   injects `sidebar_menu` filtered by build_menu_for(user)
   └─ form rendered with crispy-style markup (manual, no crispy lib)
```

For mutating endpoints the view delegates to a service:

```
POST /inventory/batches/42/transition/
   ▼
BatchTransitionView.post()
   ▼
BatchService.transition_status(batch, new_status)   ← @transaction.atomic
   │   ├─ check VALID_TRANSITIONS map
   │   └─ batch.status = new_status; batch.save()
   ▼
messages.success / messages.error
   ▼
redirect inventory:batch_detail
```

---

## 6. Service layer responsibilities

One module per aggregate. **All writes go through these.**

| Service | Owns |
|---------|------|
| `BatchService` | Batch lifecycle, stage template cloning, ad-hoc stages, status transitions, cloth assign, cutting, worker assign, operation logging |
| `ClothService` | Cloth roll inwards, location transfers |
| `StockService` | Single entry point for `StockLedger.objects.create` |
| `ProductService` | Finished-goods creation + ledger PRODUCTION entry |
| `BatchTypeService` | Stage template CRUD |
| `VendorService` / `DispatchService` | Vendor + dispatch lifecycle |
| `PaymentService` | Payment record + status reconciliation |
| `WorkerService` | Karigar dashboard data |
| `permission_service` | `user_has_perm`, `user_has_role`, sidebar menu builder |

Every method that mutates ≥1 row uses `@transaction.atomic`. Reads stay outside
transactions to keep them short.

`select_for_update()` is used on cloth rolls during consumption to prevent
race conditions when two batches consume the same roll concurrently.

---

## 7. Frontend (server-rendered)

- Templates live in `config/templates/inventory/` (project-level) and
  `config/<app>/templates/<app>/` (app-level).
- Base layout: sidebar + content panel; sidebar items injected by the
  `sidebar` context processor.
- No SPA, no JS framework — vanilla JS + small bits of Alpine-style markup.
- Static assets served via **whitenoise** (`CompressedManifestStaticFilesStorage`).
- Public homepage (`storefront/templates/.../public_home.html`) is fully
  DB-driven from the `HomePageConfig` singleton + the showcase/category models.

---

## 8. Security posture

| Concern | Mitigation |
|---------|------------|
| Account enumeration | LoginView always redirects to OTP page, regardless of email existence |
| OTP brute force | 3 wrong tries → session cleared, must restart |
| Plaintext OTPs | Stored as SHA-256 hash; compared with `hmac.compare_digest` |
| Plaintext signup passwords in session | Signed with `django.core.signing` (SECRET_KEY-backed) before persistence |
| CSRF logout | `LogoutView` is POST-only with `never_cache` |
| Session hijack | DB-backed sessions (revocable), HttpOnly cookie, SameSite=Lax, 8h idle expiry |
| Static-file MIME confusion | whitenoise's `CompressedManifestStaticFilesStorage` |
| XSS | Django auto-escape on; no `\|safe` outside vetted SVG fields |
| Race on cloth consumption | `select_for_update()` inside `BatchService.process_cutting` |
| Production secrets | `.env` + `python-decouple` — never hard-coded |
| `SECRET_KEY` missing | Hard raise at startup unless running `test` / `makemigrations` / `migrate` |

---

## 9. Dead code sweep — 2026-05-16

The following shadow files were deleted after grep-verification that no live
code referenced them. The package form of the same name had already taken
precedence at import time:

- ~~`config/inventory/views.py`~~ — superseded by `inventory/views/`
- ~~`config/inventory/services.py`~~ — superseded by `inventory/services/`
- ~~`config/inventory/forms.py`~~ — superseded by `inventory/forms/`
- ~~`config/config/settings.py`~~ — superseded by `config/settings/`
- ~~`config/verify_inventory.py`~~ — standalone test script using the
  pre-refactor `InventoryService` API (which itself was removed in the
  service-layer split).

`config/inventory/signals.py` is intentionally kept as a tombstone comment
file — it documents *why* this project does not use Django signals (they
fired outside the triggering transaction and left half-written ledger
rows). Do not "fix" the empty file by deleting it.

---

## 10. Performance notes

- `Batch` indexes: `(status, -created_at)`, `(batch_type, status)`.
- `BatchStage` indexes: `(batch, status)`, `(stage, status)` + uniqueness on
  `(batch, sequence_order)` and `(batch, stage)`.
- `StockLedger` index: `(batch, transaction_type, -date)`.
- `CONN_MAX_AGE=600` — DB connections reused 10 min.
- `prefetch_related('skills')` on `UserListView`.
- `select_related('from_stage', 'to_stage', 'batch', 'created_by', 'content_type')`
  on the dashboard ledger query.
- Dashboard KPIs use `aggregate(Sum(...))` — one query each, no N+1.

---

## 11. Where to add things

| You want to add… | Touch these |
|-------------------|-------------|
| New stage in a workflow | Admin → BatchType → "Manage stages" (no code) |
| New product category | Admin → BatchType create (no migration) |
| New permission for a role | `inventory/services/permission_service.py` + role admin |
| New CRUD page | `inventory/urls.py`, `inventory/views/<area>_views.py`, `inventory/forms/<area>_forms.py`, templates in `config/templates/inventory/`, then add a `MenuItem` in `permission_service.SIDEBAR` |
| New ledger trigger | Call `StockService.log(...)` from inside the service that mutates state |
| Public-page section | Edit `HomePageConfig` (admin) or add a new storefront model + Wagtail-style admin form |

---

## 12. Deployment

- WSGI: `config.wsgi.application` (gunicorn-friendly).
- Static collect: `python manage.py collectstatic --noinput`.
- DB: PostgreSQL with the connection params in `.env`
  (`DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT`).
- Media in `MEDIA_ROOT` (production should use S3/MinIO instead of local FS).

---

## 13. Test plan (currently sparse — TODO)

`tests.py` files exist but are empty. Suggested first wave:

1. `BatchService.transition_status` — every transition & every illegal hop.
2. `StockService.log` — content-type resolution for `ClothRoll` and `Product`.
3. `BatchService.process_cutting` — over-consumption rejection.
4. `permission_service.build_menu_for` — superuser, manager, karigar matrices.
5. Auth `LoginView` — anti-enumeration redirects.

See [ABOUT_THIS_PROJECT.md](ABOUT_THIS_PROJECT.md) for the learning roadmap.
