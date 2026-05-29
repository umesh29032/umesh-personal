# Kapil Enterprises Inventory

Django 5.2 + PostgreSQL ERP for a garment manufacturing factory.
Tracks cloth rolls, production stages (layering → cutting pattern → cutting),
bundles, barcodes, and the storefront listings.

> Personal project. Owner: Umesh. Solo maintainer.

---

## Quick Start

```bash
# 1. Activate venv (lives in ./env)
source env/bin/activate

# 2. Apply migrations (Postgres expected; DATABASE_URL or config/settings.local.py)
env/bin/python config/manage.py migrate --settings=config.settings.local

# 3. Run dev server
env/bin/python config/manage.py runserver --settings=config.settings.local

# 4. Open
# http://localhost:8000/app/        ← login (pre-provisioned users only)
# http://localhost:8000/inventory/  ← Super Admin dashboard after login
```

Settings module: `config.settings.local`. Production uses `config.settings.production`.

---

## Run Tests

```bash
env/bin/python config/manage.py test production tracking accounts \
    --settings=config.settings.local
```

Current: **150+ tests** (production + tracking + accounts + storefront).
Mirror tests for invariants, RBAC, barcodes, form validation.

---

## Doc Map

Lazy-load only what you need:

| File | When to read |
|------|-------------|
| [CLAUDE.md](CLAUDE.md) | Working rules for AI agents + shortcuts. Always-on. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Models, services, ER, security, perf. Read before non-trivial changes. |
| [ABOUT_THIS_PROJECT.md](ABOUT_THIS_PROJECT.md) | Why + how + learning map for a junior Django dev. |
| [UI_COMPONENTS.md](UI_COMPONENTS.md) | Component vocabulary + design tokens. Read before writing CSS. |
| [docs/production/OVERVIEW.md](docs/production/OVERVIEW.md) | Production tracking subsystem (rolls + Adda + stages). |
| [docs/production/CUTTING_PATTERN.md](docs/production/CUTTING_PATTERN.md) | Cutting-pattern stage: video, photos, verifications. |
| [docs/production/CUTTING_DESIGN.md](docs/production/CUTTING_DESIGN.md) | Cutting design spec (ProductSize + breakup + bundles). |
| [AUDIT_2026_05_29.md](AUDIT_2026_05_29.md) | Latest application audit report (read-only findings). |

---

## Apps

| App | Responsibility |
|-----|----------------|
| `config/accounts` | User auth, OTP, password reset, signup adapter, Skill model. Argon2 + rate-limited. |
| `config/inventory` | RBAC core: Role model + `permission_service` + sidebar builder. |
| `config/raw_materials` | Cloth rolls master data: ClothType, ClothColor, StorageLocation, ClothRoll. |
| `config/production` | Product, Stage library, WorkflowStage, Adda, AddaStageRecord, layering + cutting + cutting-pattern records. |
| `config/tracking` | Barcodes (BarcodeBatch + lazy BatchBarcode) + scan endpoint + history audit trails. |
| `config/storefront` | Public-facing listings (categories, featured products, homepage CMS). |

Strict rule (CLAUDE.md #4): **service layer owns all multi-row writes.**
Views call `production.services` / `tracking.services` / `raw_materials.services` —
no ORM writes in views.

---

## Workflow at 10,000 Feet

```
ClothRoll (raw_materials)
    │
    ▼
Adda  ──── per Product, auto-coded T-SHIRT-001
    │
    ├── Stage 1: Layering          (start → attach rolls → complete)
    ├── Stage 2: Cutting Pattern   (video + photos + verify + size %)
    ├── Stage 3: Cutting           (breakup → bundles → barcodes)
    └── ...future stages           (stitching, packing, dispatch)
    │
    ▼
BatchBarcode (tracking)  ←  scan via QR  →  scan_detail page
```

Each stage transition logs to `tracking.AddaHistory`. Stage records own
their stage-specific child rows (LayeringRecord, CuttingRecord,
CuttingPatternRecord). Barcodes generated automatically at cutting completion.

---

## Roles (RBAC)

Defined in `config/inventory/services/permission_service.py`:

| Role | Capability |
|------|-----------|
| `super_admin` | All sections; can manage roles, users, sidebar visibility. Bypass for all gates. |
| `manager` | All production stages + raw materials + reports. |
| `karigar` | Factory floor — production stages they have skill access to. |
| `listing_team` | Storefront listings only. |
| `accountant` | Financial views (stocks, dispatch values). |

Per-stage access is **additive via skills + roles M2M** on each `Stage` row.
A user gets stage access if their `role` OR any skill matches the Stage's
`access_by_role` / `access_by_skill`.

---

## Conventions

- **Service layer** — `config/<app>/services/*.py`. Every multi-row write +
  `@transaction.atomic`. Views thin (parse POST → call service → redirect).
- **No signals.** All side-effects explicit (CLAUDE.md rule). `signals.py`
  files are tombstoned with explanation.
- **Hinglish "why" comments** on each new model/service file. One-line, names
  the Django/PG primitive being used.
- **Page-scoped CSS** — page-specific styles go in `{% block extra_head %}`
  scoped under a page class (`.user-create`, `.adda-detail`). Shared
  components in `templates/accounts/base.html`.
- **Component vocabulary** documented in [UI_COMPONENTS.md](UI_COMPONENTS.md).
  Reuse > extend > add new (only add new when same pattern repeats in 3+
  templates).

---

## Operational Notes

- Postgres expected. Local SQLite **not** supported — `Adda.code` generation
  uses `cloth_roll_seq` and `SELECT FOR UPDATE`.
- Media (uploaded videos + photos) stored via `STORAGES['default']`. Swap
  to S3/MinIO via `settings.py` only — code unchanged.
- Production deploy: HSTS 1yr + preload, SECURE_SSL_REDIRECT, all
  `SESSION_COOKIE_*` / `CSRF_COOKIE_*` secure flags on.

---

## Recent Major Changes

See [git log](https://github.com/) for full history. Headline items:

- **2026-05-29** — Audit (`AUDIT_2026_05_29.md`); composite indexes;
  invariant tests; service-boundary fixes; `ActiveManager` opt-in.
- **2026-05-28** — Cutting-pattern stage + ProductPattern + reopen +
  curated role editor.
- **2026-05-19** — Old BatchType/Batch deleted; replaced with per-product
  Adda flow.
- **2026-05-17** — Storefront app with `listing_team` role.
