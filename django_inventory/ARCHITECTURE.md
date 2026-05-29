# ARCHITECTURE — Kapil Enterprises Inventory System

> A factory-floor ERP for a kids-garment manufacturer.
> Tracks raw cloth → batches (Adda) → layering → cutting-pattern → cutting → barcodes → public storefront.
> Built with **Django 5.2 + PostgreSQL** with a strict service-layer architecture.

This document is the technical contract. If something here disagrees with the code, the **code wins** — open a PR to update this doc.

> **Last refreshed:** 2026-05-28 (post cutting_pattern stage + ProductPattern library + Layering/Pattern reopen + curated role editor).
> For per-subsystem deep dives see `docs/production/OVERVIEW.md`.

---

## 1. 10,000-foot view

```
┌──────────────────────────────────────────────────────────────────────────┐
│  PUBLIC STOREFRONT   /                                                   │
│  (Hero, categories, featured products — DB-driven from storefront app)   │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │  "Login / Get Started"
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  AUTH  /app/                                                             │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐                     │
│  │ OTP login    │  │ Password    │  │ Google OAuth │                     │
│  │ (default)    │  │ (fallback)  │  │ (allauth)    │                     │
│  └──────────────┘  └─────────────┘  └──────────────┘                     │
│  OTP → SHA-256 hash in session + 5-min expiry + 3-try lockout            │
│  Rate-limit per IP+email on every auth endpoint (cache-backed)           │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │  on success
                             ▼
                ┌────────────────────────────┐
                │  Sidebar built per user    │
                │  permission_service.SIDEBAR│
                │  (DB SidebarItemRule layer │
                │   overrides hardcoded preds)│
                └──────────────┬─────────────┘
                               │
        ┌──────────────────────┼────────────────────────────────────┐
        ▼                      ▼                                    ▼
┌──────────────────┐  ┌──────────────────────┐  ┌──────────────────────────┐
│ raw_materials    │  │ production           │  │ tracking                 │
│  /raw-materials/ │  │  /production/        │  │  /tracking/              │
│  Cloth + master  │  │  Adda + stages       │  │  Barcodes + history      │
└──────────────────┘  └──────────────────────┘  └──────────────────────────┘

         ┌──────────────────┐                ┌──────────────────┐
         │ inventory        │                │ storefront       │
         │  /inventory/     │                │  /storefront/    │
         │  RBAC + dashboard│                │  public homepage │
         │  + Stages library│                │  admin CMS       │
         └──────────────────┘                └──────────────────┘
```

---

## 2. Django apps

| App | Purpose | Tables |
|-----|---------|--------|
| `accounts` | Custom User model, OTP/password/Google auth, skills, user CRUD UI | `User`, `Skill` |
| `inventory` | RBAC source of truth, sidebar registry, unified Dashboard | `Role`, `SidebarItemRule` |
| `production` | Factory production lifecycle | `Product`, `ProductPattern`, `ProductPatternAssignment`, `Stage`, `WorkflowStage`, `Adda`, `AddaStageRecord`, `LayeringRecord`, `LayeringRollEntry`, `RemainingClothOfClothRoll`, `CuttingPatternRecord`, `CuttingPatternPhoto`, `CuttingRecord` |
| `raw_materials` | Cloth inventory + master data | `ClothType`, `ClothColor`, `StorageLocation`, `ClothRoll` |
| `tracking` | Barcodes + per-domain audit history | `BatchBarcode`, `ClothRollHistory`, `AddaHistory`, `ProductHistory` |
| `storefront` | Public marketing homepage (admin-editable) | `HomePageConfig`, `Category`, `FeaturedProduct`, `HeroShowcaseCard`, `WhyUsCard`, `FooterLink`, `NavLink` |

**Cross-app FK rule** (enforced architecturally — do not break):

```
storefront ── (none)
inventory  ── (none, only consumed by views/templates)
accounts   ── (consumed by every downstream)
raw_materials  ──▶ production.Adda  (string FK, no cycle)
production     ──▶ raw_materials, accounts
tracking       ──▶ production, raw_materials, accounts
```

`raw_materials` never imports `production`/`tracking`. `production` never imports `tracking`.

---

## 3. Repo layout

```
django_inventory/
├── ARCHITECTURE.md            ← this file
├── CLAUDE.md                  ← repo-wide rules (service layer, RBAC, no signals)
├── ABOUT_THIS_PROJECT.md      ← motivation + learning map
├── UI_COMPONENTS.md           ← component vocabulary + tokens
├── docs/production/           ← subsystem deep-dive docs
│   ├── OVERVIEW.md            ← entry point for any new chat
│   ├── PRODUCTION_APP.md
│   ├── RAW_MATERIALS.md
│   ├── TRACKING.md
│   ├── LAYERING_STAGE.md
│   ├── CUTTING_PATTERN.md     ← NEW 2026-05-28
│   ├── RBAC.md, MIGRATIONS.md, TESTS_AND_RISKS.md
│   ├── DECISION_LOG.md, CHAT_LOG.md, UI_PATTERNS.md
├── env/                       ← Python virtualenv (gitignored)
├── media/                     ← user-uploaded files (gitignored)
└── config/                    ← Django project root
    ├── manage.py
    ├── config/                ← project package (settings + ROOT URLconf)
    │   ├── settings/
    │   │   ├── base.py        ← shared (apps, middleware, allauth, sessions, logging)
    │   │   ├── local.py       ← DEBUG=True, ALLOWED_HOSTS=*
    │   │   └── production.py  ← HSTS, secure cookies, prod hosts, X_FRAME_OPTIONS
    │   └── urls.py            ← root URLconf
    ├── templates/             ← project-level shared templates (inventory dashboard etc.)
    ├── logs/                  ← django.log, security.log
    ├── accounts/              ← Django app
    ├── inventory/             ← Django app
    ├── production/            ← Django app  (README.md inside)
    ├── raw_materials/         ← Django app
    ├── tracking/              ← Django app
    └── storefront/            ← Django app
```

### App internal structure (typical)

```
config/<app_name>/
├── __init__.py
├── apps.py                    ← AppConfig
├── admin.py                   ← Django admin registrations
├── constants.py               ← exported codes (e.g. STAGE_LAYERING)
├── models.py                  ← ORM rows
├── urls.py                    ← URL → view binding
├── migrations/                ← schema deltas + data seeds
├── forms/                     ← (or forms.py) Django ModelForm classes
├── services/                  ← business logic — multi-row writes
│   ├── __init__.py            ← re-exports public functions
│   └── *_service.py           ← per-domain modules
├── views/                     ← (or views.py) CBVs + FBVs
│   ├── mixins.py              ← role/perm gates
│   └── *_views.py
├── templates/<app>/           ← app-scoped templates
└── tests/                     ← pytest-style tests
```

---

## 4. Settings split

Modular settings — picked by `DJANGO_SETTINGS_MODULE`:

```
config/config/settings/
├── base.py        # shared: apps, middleware, DB, allauth, sessions, logging, STORAGES
├── local.py       # DEBUG=True, ALLOWED_HOSTS=*, allauth verification off
└── production.py  # HSTS, secure cookies, X_FRAME_OPTIONS='DENY', prod hosts
```

Secrets via `.env` + `python-decouple` — never hard-coded. `SECRET_KEY` missing → hard raise at startup unless running `test` / `makemigrations` / `migrate`.

`STORAGES['default']` = `FileSystemStorage` for media. Swap to S3/MinIO is settings-level only — no code change needed. Cutting-pattern uploads honor this abstraction.

---

## 5. Data model — domain breakdown

### 5.1 Users + RBAC

```
accounts.User                       ← AbstractUser-based, email PK
  ├── role (FK → inventory.Role)            RBAC source of truth
  ├── extra_roles (M2M → Role)              for users needing multiple roles
  ├── skills (M2M → Skill)                  per-stage skill gates
  └── legacy user_type (CharField)          back-compat fallback

inventory.Role
  ├── code (slug, stable)                   referenced by `permission_service`
  ├── permissions (M2M → auth.Permission)   Django built-in codenames
  └── is_system (bool)                      seeded rows cannot be deleted

accounts.Skill                              cutting_master / cutting_master_helper / …
```

5 seeded roles: `super_admin`, `manager`, `karigar`, `accountant`, `listing_team`.

Convenience sets in `permission_service`:
- `MANAGEMENT_ROLES = {super_admin, manager}`
- `PRODUCTION_ROLES = {super_admin, manager, karigar}`
- `FINANCIAL_ROLES = {super_admin, accountant}`
- `STOREFRONT_ROLES = {super_admin, listing_team}`

`user_has_perm` treats `ROLE_SUPER_ADMIN` as implicit bypass (super admin never needs every checkbox ticked).

### 5.2 Production catalog

```
Product
  ├── code (slug, unique)                   Adda code prefix
  ├── adda_counter (PositiveInteger)        race-safe via SELECT FOR UPDATE
  ├── workflow_stages (reverse FK → WorkflowStage)
  └── patterns (M2M → ProductPattern through ProductPatternAssignment)

Stage  (admin-managed library at /production/stages/)
  ├── code (slug, LOCKED after create)      services hardcode constants
  ├── access_by_skill (M2M → accounts.Skill)
  └── access_by_role  (M2M → inventory.Role)

WorkflowStage  (per-product Stage in order)
  ├── product (FK Product)
  ├── stage   (FK Stage)
  ├── order   (PositiveInteger)
  └── unique_together = (product, order), (product, stage)

ProductPattern  (reusable shape: Sleeve / Front / Back …)
  ├── code (slug, LOCKED after create)
  ├── reference_image
  └── is_active

ProductPatternAssignment  (through-table)
  ├── product, pattern, pieces_count
  └── unique_together = (product, pattern)
```

### 5.3 Adda batch lifecycle

```
Adda
  ├── code = "{Product.code}-NNN"           editable=False, service-generated
  ├── product (FK PROTECT)
  ├── current_stage (FK WorkflowStage, nullable)  NULL when COMPLETED
  ├── status: in_progress | on_hold | completed | cancelled
  ├── started_at / completed_at
  └── rolls (reverse FK ← raw_materials.ClothRoll.adda)

AddaStageRecord  (polymorphic parent — one per Adda × Stage)
  ├── adda, workflow_stage
  ├── workers (M2M → User)                  per-stage assignment
  ├── started_at, completed_at, completed_by
  ├── draft_layer_length_meters / duration_minutes / notes  (Layering draft)
  └── unique_together = (adda, workflow_stage)
```

Typed child records hang via OneToOne:

```
AddaStageRecord
  ├── layering (OneToOne ← LayeringRecord)
  ├── cutting_pattern (OneToOne ← CuttingPatternRecord)
  └── cutting (OneToOne ← CuttingRecord)
```

### 5.4 Layering stage detail

```
LayeringRecord
  ├── stage_record (OneToOne AddaStageRecord)
  ├── lay_count, layer_length_meters, duration_minutes, total_colors, notes
  └── rolls_used (M2M → ClothRoll)

LayeringRollEntry  (per attached cloth roll)
  ├── stage_record, roll
  ├── width_verified_inch, weight_verified_kg, layers_on_roll
  ├── attached_by, attached_at, notes
  └── remaining_pieces (reverse FK ← RemainingClothOfClothRoll)

RemainingClothOfClothRoll  (leftover after layering)
  ├── layering_entry (FK)
  ├── source_adda (denormalized, search-friendly)
  ├── remaining_length_meters, remaining_weight_kg
  └── is_consumed (bool)
```

### 5.5 Cutting-Pattern stage detail (NEW 2026-05-28)

```
CuttingPatternRecord
  ├── stage_record (OneToOne AddaStageRecord)
  ├── video (FileField, optional)           upload_to=media/cutting_pattern/<adda>/video_*
  └── notes

CuttingPatternPhoto  (multiple per record)
  ├── record (FK)
  ├── image (ImageField, Pillow JPEG q=80, ≤2400px, EXIF-honored)
  ├── caption, uploaded_by
```

Complete-time gate: `has_video OR has_photo` (at least one).

### 5.6 Cutting stage detail

```
CuttingRecord
  ├── stage_record (OneToOne AddaStageRecord)
  ├── pieces_cut (PositiveInteger)          → denorm SUM(CuttingBundleItem.count)
  └── notes

CuttingPieceBreakup (suggested inventory; size × color × pattern × count + consumed_count)
CuttingBundle      (header per (cutting_record, size); total_pieces denorm)
CuttingBundleItem  (bundle line: pattern × color × count; source_breakup FK for consumed_count restore)

On completion → materialises:
AddaProductSizeColorPieceBreakdown    (cutting_record × size × color × verified_piece_count)
                                       ↑ manufacturing truth, frozen, source for downstream
```

### 5.6.1 Barcode Generation stage detail (NEW 2026-05-29 — optional per-product)

```
BarcodeGenerationRecord
  ├── stage_record (OneToOne AddaStageRecord)
  ├── total_barcodes (PositiveInteger)      → denorm SUM(BarcodeBatch.total_pieces)
  ├── generated_at (DateTime, nullable)     → set when one-shot generate succeeds
  └── notes

Reads:  AddaProductSizeColorPieceBreakdown    (frozen at cutting completion)
Writes: tracking.BarcodeBatch                  (one-shot per stage)
```

Per-product workflow: products without `barcode_generation` in their
`WorkflowStage` list still inline-generate barcodes at cutting completion
(legacy back-compat). New products opt in by admin via product flow editor.

Reopen guards: refused if any `BatchBarcode` scanned OR any
`BarcodeExportBatch` exists. Detailed spec: [docs/production/BARCODE_GENERATION.md](docs/production/BARCODE_GENERATION.md).

### 5.7 Cloth inventory

```
raw_materials.ClothType / ClothColor / StorageLocation
  ├── name, code, is_active                 master data, PROTECT FKs

ClothRoll
  ├── roll_id = "CR-NNNNNN"                 from Postgres sequence `cloth_roll_seq`
  ├── cloth_type, cloth_color, storage_location
  ├── purchased_date, width_inch, weight_kg
  ├── supplier, cost_per_kg                 FINANCIAL_ROLES only
  ├── adda (string FK → 'production.Adda')  set when assigned
  ├── layers_on_roll, layer_length_meters   stamped at Layering complete
  ├── remaining_length_meters / weight_kg   denormalized from primary leftover
  └── status: not_used | used
```

### 5.8 Tracking

```
BarcodeBatch  (range header — one row per (size, color) combo per Adda)
  ├── adda, product, color, size, bundle (PROTECT FKs)
  ├── start_seq..end_seq (contiguous range)
  └── total_pieces (denorm)

BatchBarcode  (per-piece scan state — lazy-created on first scan)
  ├── adda (FK)
  ├── batch (FK BarcodeBatch — backfilled on lazy create)
  ├── piece_seq (sequence within Adda)
  ├── value = "{ADDA_CODE}-{PIECE_SEQ:04d}"
  ├── status (pending/packed/dispatched/missing)
  ├── last_scanned_at / last_scanned_by
  └── QR served at /tracking/scan/<value>/

BarcodeExportBatch  (NEW 2026-05-29 — export manifest)
  ├── export_code = "EXP-YYYY-NNN" (unique)
  ├── adda, product, barcode_gen_record (PROTECT FKs)
  ├── export_method (csv/xlsx/pdf)
  ├── exported_by (User)
  └── total_labels (frozen at first export)
  Files regenerated on-demand from live BarcodeBatch — not stored on disk.

AddaHistory     (change_type: created | stage_advanced | stage_reopened | status_changed | roll_assigned | completed)
ClothRollHistory
ProductHistory
```

All history rows write-only via `tracking.services.history_service.log_*`. **No Django signals** (project rule — see `production/signals.py` tombstone).

Export details: [docs/tracking/EXPORTS.md](docs/tracking/EXPORTS.md).

### 5.9 Storefront

```
HomePageConfig         (singleton row — hero copy, theme, footer)
Category               (product groupings shown on homepage)
FeaturedProduct        (carousel cards)
HeroShowcaseCard       (banner tiles)
WhyUsCard              (value-prop cards)
FooterLink             (footer nav)
NavLink                (top-bar nav)
```

CRUD at `/storefront/` — gated to `STOREFRONT_ROLES`.

---

## 6. Service layer

**All multi-row writes go through services** (CLAUDE.md rule #4). One module per aggregate.

| App | Service | Owns |
|---|---|---|
| `inventory` | `permission_service` | role/perm helpers, sidebar builder, ROLE_EDITOR_SECTIONS |
| `production` | `adda_service` | Adda lifecycle, `create_adda` (SELECT FOR UPDATE counter), `advance_to_next_stage` |
| `production` | `product_service` | Product CRUD |
| `production` | `flow_service` | per-product Stage list editor (add/remove/move) |
| `production` | `access_service` | DB-driven per-stage skill+role gate, `stage_access_map` |
| `production` | `layering_service` | start / attach roll / draft / complete / **reopen_layering** |
| `production` | `cutting_pattern_service` | start / attach photo / save record / complete / **reopen_pattern_stage** |
| `production` | `cutting_service` | complete cutting → triggers `tracking.generate_for_cutting` |
| `production` | `activity_service` | cross-Adda activity timeline |
| `raw_materials` | `roll_service` | bulk_create_rolls (sequence-based), transfer, assign |
| `raw_materials` | `master_service` | ClothType/Color/StorageLocation CRUD |
| `tracking` | `barcode_service` | `generate_for_cutting` (Adda complete → barcode rows) |
| `tracking` | `history_service` | `log_adda` / `log_roll` / `log_product` write-only helpers |

Every mutating method uses `@transaction.atomic`. Reads stay outside transactions.

`select_for_update()` used on `Product.adda_counter` increment + `reopen_*` services.

---

## 7. Request lifecycle (example: "Complete Layering" inside iframe)

```
1. POST /production/addas/T-SHIRT-001/layering/complete/  (embedded=1)
        ↓
2. urls.py routes → LayeringCompleteView (production/views/stage_views.py)
        ↓
3. LoginRequiredMixin → user authenticated?
   ProductionRoleMixin → user in PRODUCTION_ROLES?
        ↓
4. View.post():
   • parse action ('draft' | 'complete'), header values, per-entry breakup
   • save_layering_draft(...)  (lax write)
   • if complete:
       complete_layering(adda, duration, layer_length, per_entry_layers, notes, user)
         ├── @transaction.atomic
         ├── _ensure_can_manage(user) + _ensure_can_complete_layering(user)
         ├── validate (duration > 0, layer_length > 0, missing layers/leftover)
         ├── stamp ClothRoll.layers_on_roll + layer_length_meters per entry
         ├── LayeringRecord.objects.create(...)
         └── advance_to_next_stage(adda, user)
              ├── find next WorkflowStage by order
              ├── adda.current_stage = next  (or status=COMPLETED if last)
              └── log_adda(AddaHistory.STAGE_ADVANCED)
        ↓
5. Iframe-safe redirect:
   embedded=1 → /production/addas/<code>/stage/<next>/?embedded=1&advanced=1
   else        → /production/addas/<code>/
        ↓
6. Iframe loads embedded panel. JS reads ?advanced=1 → postMessage parent.
   Parent (adda_detail.html / user_dashboard.html) listens → window.location.reload().
```

Same pattern for `complete_pattern_stage`, `complete_cutting`, `reopen_layering`, `reopen_pattern_stage`.

---

## 8. RBAC + sidebar

Three layers:

1. **Hardcoded `SIDEBAR` tuple** in `inventory.services.permission_service` — declarative MenuSection/MenuItem with `predicate=callable(user)`
2. **DB `SidebarItemRule` rows** — admin override hardcoded predicates from `/inventory/sidebar-access/`
3. **Per-stage Stage.access_by_skill + access_by_role** — used by `access_service` for stage workspace + adda detail tab visibility

`build_menu_for(user, path)` resolves all three layers, returns the visible menu for the request.

Role editor at `/inventory/roles/<pk>/edit/` is **curated section-by-section** (`ROLE_EDITOR_SECTIONS` in `permission_service.py`):
- Production Flow · Raw Materials · Tracking · Storefront · Administration
- Internal join tables hidden (AddaStageRecord, LayeringRollEntry, *Record, *History, *Assignment)

Stage CRUD (`/production/stages/`) + ProductPattern CRUD (`/production/patterns/`) are perm-driven (`production.{view,add,change,delete}_{stage,productpattern}`) — Super Admin bypass via `user_has_perm`.

---

## 9. Frontend (server-rendered)

- Templates: `config/templates/<app>/` (project-level) + `config/<app>/templates/<app>/` (app-level)
- Base layout: sidebar + content panel. Sidebar injected by `inventory.context_processors.sidebar`
- No SPA, no JS framework — vanilla JS + small Alpine-style markup
- Static assets via **whitenoise** (`CompressedManifestStaticFilesStorage`)
- Public homepage is fully DB-driven from `HomePageConfig` + storefront models

**Iframe + postMessage pattern** (Adda detail page):
- Each stage tab embeds `stage_panel_embedded.html?embedded=1` via iframe
- `StagePanelView` + `AddaDetailView` carry `@xframe_options_sameorigin` (default `DENY` would break iframe)
- Iframe auto-resize via `postMessage({type:'stage-panel-resize', height, code})`
- Stage advance → embedded URL with `?advanced=1` → `postMessage({type:'stage-advanced'})` → parent reload

**Mobile rules** (codified in `docs/production/UI_PATTERNS.md`):
- `data-label` on every `<td>` for stacked-on-narrow tables
- Filter chips on a single scrollable row
- Form-shell mandatory (hero + numbered panels + cream inputs + sticky CTA)
- Page-scoped CSS under root class (`.adda-detail`, `.layering-workspace`) — never leak

---

## 10. Security posture

| Concern | Mitigation |
|---|---|
| Account enumeration | OTP login always redirects to OTP page regardless of email existence |
| OTP brute force | 3 wrong tries → session cleared. Rate-limit per IP+email (cache) on every auth endpoint |
| Plaintext OTPs | SHA-256 hash in session, compared via `hmac.compare_digest` |
| Signup password in session | `django.core.signing` (SECRET_KEY-backed) before persist |
| Self-lockout (admins) | Lockout flow protects super-admin user explicitly |
| CSRF logout | `LogoutView` POST-only + `never_cache` |
| Session hijack | DB sessions (revocable), HttpOnly, SameSite=Lax, 8h idle expiry |
| MIME confusion | whitenoise `CompressedManifestStaticFilesStorage` |
| XSS | Django auto-escape on, no `\|safe` outside vetted SVG fields |
| Iframe clickjacking | `X_FRAME_OPTIONS='DENY'` in production. Stage panels + AddaDetail downgrade to SAMEORIGIN explicitly |
| Race on roll consumption / Adda counter | `select_for_update()` |
| Argon2 password hasher | Configured in `PASSWORD_HASHERS` |
| Production secrets | `.env` + `python-decouple` |
| `SECRET_KEY` missing | Hard raise at startup unless test/makemigrations/migrate |

Security log: `logs/security.log` — every auth event (success / failure / throttle) lands here.

---

## 11. Performance notes

- `Adda` indexes: `(status)`, `(product, status)`, `(current_stage)`
- `BatchBarcode` indexed on `(adda, piece_seq)`
- `CONN_MAX_AGE=600` — DB connections reused 10 min
- `select_related` / `prefetch_related` on every list query (no N+1)
- Pillow compression on photo upload caps disk + future S3 egress
- Iframe lazy-load (`loading="lazy"`) on stage panels — non-default tab iframes don't fetch until activated

---

## 12. Where to add things

| You want to add… | Touch these |
|---|---|
| New Stage in the global library | `/production/stages/` (admin UI, no migration) — set `access_by_skill`/`access_by_role` |
| New stage in a Product's flow | `/production/products/<pk>/flow/` (admin UI) |
| New Product | `/production/products/add/` (Super Admin) |
| New Pattern | `/production/patterns/` then assign at `/production/products/<pk>/patterns/` |
| New permission for a role | `/inventory/roles/<pk>/edit/` (curated section editor) |
| New typed stage record (e.g. Stitching) | new model in `production/models.py` (OneToOne AddaStageRecord) + new service `<stage>_service.py` + new templates `_stage_panel_<stage>.html` + add dispatch in `stage_panel_embedded.html` + add constant in `production/constants.py` + data migration to seed Stage row |
| New CRUD page | `<app>/urls.py` + `<app>/views/<area>_views.py` + `<app>/forms/...` + templates + `MenuItem` in `permission_service.SIDEBAR` |
| New audit event | extend `tracking.AddaHistory.ChangeType` enum, then call `log_adda(...)` from inside the service that mutates |
| New storefront section | new model in `storefront/` + Wagtail-style admin form OR extend `HomePageConfig` |

---

## 13. Deployment

- WSGI: `config.wsgi.application` (gunicorn-friendly)
- Static collect: `python manage.py collectstatic --noinput`
- DB: PostgreSQL, params via `.env` (`DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT`) or `DATABASE_URL`
- Media in `MEDIA_ROOT` — production should serve via S3/MinIO (swap `STORAGES['default']` backend)
- whitenoise serves static; for media use a real object store

---

## 14. Test plan + verify

```bash
cd /home/tech/umesh-personal/django_inventory
env/bin/python config/manage.py check                                                       # clean
env/bin/python config/manage.py test raw_materials production tracking inventory accounts   # 74/74 OK
env/bin/python config/manage.py runserver
```

Current coverage breakdown (high level):
1. `BatchService` / `AddaService` — Adda lifecycle + counter race
2. `permission_service.build_menu_for` — every role matrix
3. `LayeringService` — start, attach, complete, reopen
4. `accounts` auth — OTP + password + Google + throttle + lockout
5. `tracking` — barcode generation + history append

See `docs/production/TESTS_AND_RISKS.md` for the long version.

---

## 15. Decision log + chat history

For chronological design decisions (every "why we did X instead of Y") see:
- `docs/production/DECISION_LOG.md`
- `docs/production/CHAT_LOG.md`
- `docs/production/CUTTING_PATTERN.md` (latest stage)

For repo-wide rules (service layer, no signals, RBAC discipline, mobile rules, form shell) see `CLAUDE.md`.
