# Kapil Enterprises Inventory

Django 5.2 + PostgreSQL ERP for a garment manufacturing factory.
Tracks cloth rolls, production stages (layering → cutting pattern → cutting →
barcode generation), bundles, barcodes, **per-stage costing**, **worker
earnings/advances/settlement (payroll)**, role/skill access control, and the
storefront listings.

> Personal project. Owner: Umesh. Solo maintainer.

> **New here? → [docs/START_HERE.md](docs/START_HERE.md).** One front door that
> routes a new developer, the owner, or an AI agent to exactly what to read.

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

Current: **292 tests** (production + tracking + accounts + storefront + expense + inventory).
Run from anywhere; discovery needs the `config/` dir on path (`cd config && ../env/bin/python manage.py test`).
Mirror tests for invariants, RBAC (role + skill + URL enforcement), barcodes, payroll/settlement math, form validation.

---

## Doc Map

Lazy-load only what you need:

| File | When to read |
|------|-------------|
| [docs/START_HERE.md](docs/START_HERE.md) | **First, always.** Routes you (new dev / owner / AI agent) to exactly what to read. |
| [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) | **Current full system design** — most up-to-date big picture. |
| [CLAUDE.md](CLAUDE.md) | Working rules for AI agents + shortcuts. Always-on. |
| [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) | Canonical current-state design (models/services/ER/security/perf). First read: [docs/PROJECT_KNOWLEDGE_MAP.md](docs/PROJECT_KNOWLEDGE_MAP.md). |
| [config/expense/README.md](config/expense/README.md) · [docs/ARCHITECTURE_V2.md](docs/ARCHITECTURE_V2.md) §11 · [docs/LEARNING_2_0/CHOKEPOINTS/adda_settlement_service.md](docs/LEARNING_2_0/CHOKEPOINTS/adda_settlement_service.md) | **`expense` app (live canonicals):** earnings ledger, advances, settlement + stage costing ([ADR-0009](docs/adr/0009-cost-truth.md)). *(Pre-V2 design archived under [docs/archive/production/](docs/archive/production/) — history only.)* |
| [docs/production/RBAC.md](docs/production/RBAC.md) | Roles/skills, Access Control hub, sidebar + URL enforcement. |
| [CHANGELOG.md](CHANGELOG.md) · [docs/PAGES/](docs/PAGES/) · [docs/LEARNING_2_0/DATA_FLOWS/](docs/LEARNING_2_0/DATA_FLOWS/) | Changelog, per-page contracts, flows (write-path + REQUEST_JOURNEYS call-chains). |
| [docs/adr/](docs/adr/) · [docs/archive/](docs/archive/) | Locked architecture decisions (ADRs); superseded/dated docs (audits, build logs). |
| [ABOUT_THIS_PROJECT.md](ABOUT_THIS_PROJECT.md) | Why + how + learning map for a junior Django dev. |
| [UI_COMPONENTS.md](UI_COMPONENTS.md) | Component vocabulary + design tokens. Read before writing CSS. |
| [docs/production/OVERVIEW.md](docs/production/OVERVIEW.md) | Production tracking subsystem (rolls + Adda + stages). |
| [docs/production/CUTTING_PATTERN.md](docs/production/CUTTING_PATTERN.md) | Cutting-pattern stage: video, photos, verifications. |
| [docs/archive/production/CUTTING_DESIGN.md](docs/archive/production/CUTTING_DESIGN.md) | *(archived)* Cutting design spec — shipped; see OVERVIEW / CUTTING_PATTERN. |
| [docs/archive/production/BARCODE_STAGE_PLAN.md](docs/archive/production/BARCODE_STAGE_PLAN.md) | *(archived)* barcode_generation plan — shipped; see BARCODE_GENERATION.md. |
| [docs/production/BARCODE_GENERATION.md](docs/production/BARCODE_GENERATION.md) | Barcode Generation stage spec — flow, validation, reopen rules. |
| [docs/tracking/EXPORTS.md](docs/tracking/EXPORTS.md) | Barcode export flow (CSV / XLSX / PDF) + future label tracking. |
| [docs/archive/AUDIT_2026_05_29.md](docs/archive/AUDIT_2026_05_29.md) | *(archived)* 2026-05-29 audit findings — folded into the remediation plan. |

---

## Apps

| App | Responsibility |
|-----|----------------|
| `config/accounts` | User auth, OTP, password reset, signup adapter, Skill model, user_type. Argon2 + rate-limited. |
| `config/inventory` | RBAC core: Role model + `permission_service` + sidebar builder + `SidebarItemRule` + **Access Control hub** + **`SidebarAccessMiddleware`** (URL enforcement). |
| `config/raw_materials` | Cloth rolls master data: ClothType, ClothColor, StorageLocation, ClothRoll. |
| `config/production` | Product, Stage library, WorkflowStage, Adda, AddaStageRecord, layering/cutting/cutting-pattern/barcode-gen records, **stage costing** (`cost_service`). |
| `config/tracking` | Barcodes (BarcodeBatch + lazy BatchBarcode) + scan endpoint + history audit trails (`AddaHistory`). |
| `config/expense` | **Worker payroll**: allocation-driven earnings (`StageWorkAssignment`), immutable `WorkerLedgerEntry`, advances, on-demand `PayrollSettlement`. |
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
    ├── Stage 1: Layering            (start → attach rolls → complete)
    ├── Stage 2: Cutting Pattern     (video + photos + verify + size %)
    ├── Stage 3: Cutting             (breakup → bundles → freeze breakdown)
    ├── Stage 4: Barcode Generation  (generate batches → validate counts)  [optional]
    └── ...future stages             (stitching, packing, dispatch)
    │
    ▼
BarcodeBatch / BatchBarcode (tracking)  ←  scan via QR  →  scan_detail page
    │
    ▼
Export (CSV / XLSX / PDF summary)  →  Vendor or factory printer
```

Per-product workflow: some products skip Barcode Generation entirely
(legacy cutting still inline-generates barcodes). Each stage transition
logs to `tracking.AddaHistory`. Stage records own their stage-specific
child rows (`LayeringRecord`, `CuttingPatternRecord`, `CuttingRecord`,
`BarcodeGenerationRecord`). Cutting completion materializes
`AddaProductSizeColorPieceBreakdown` — the **manufacturing truth** that
downstream stages consume.

---

## Roles (RBAC)

Defined in `config/inventory/services/permission_service.py`:

| Role | Capability |
|------|-----------|
| `super_admin` | All sections; can manage roles, users, skills, sidebar visibility, stages. Bypass for all gates. |
| `manager` | All production stages + raw materials + payroll + reports. |
| `worker` | Factory floor — production stages they have **skill** access to. (Renamed from `karigar` 2026-06-02.) |
| `listing_team` | Storefront listings only. |
| `accountant` | Financial views (supplier + cost-per-kg on cloth rolls). |

**Three separate concepts** (never mixed): **User Type** (1:1, display only) ·
**Role** (M2M → page/module/sidebar access) · **Skill** (M2M → production-stage
work capability). Per-stage access is additive via `Stage.access_by_skill` /
`access_by_role` (OR semantics; management bypass). Menu items + their URLs are
gated together by `SidebarItemRule` + `SidebarAccessMiddleware`, with a read-only
**Access Control hub** at `/inventory/access/`.

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

See [git log](https://github.com/) for full history + [CHANGELOG.md](CHANGELOG.md). Headline items:

- **2026-06-02** — Stage costing + worker payroll/settlement (`expense` app);
  unified Access Control hub + `SidebarAccessMiddleware` (URL-level RBAC);
  stage views skill-gated; user-type spec set + role `karigar`→`worker`;
  dead-code cleanup. 292 tests.
- **2026-05-29** — Audit (`AUDIT_2026_05_29.md`); composite indexes;
  invariant tests; service-boundary fixes; `ActiveManager` opt-in.
- **2026-05-28** — Cutting-pattern stage + ProductPattern + reopen +
  curated role editor.
- **2026-05-19** — Old BatchType/Batch deleted; replaced with per-product
  Adda flow.
- **2026-05-17** — Storefront app with `listing_team` role.
