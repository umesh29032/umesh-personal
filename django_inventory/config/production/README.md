# `production` app — Kapil Enterprises

> Junior-Django friendly walkthrough. Hinglish + English.

Yeh app **factory ka production lifecycle** handle karta hai — raw cloth se lekar finished pieces tak. Iss app ki responsibility hai:

- Products define karna (T-SHIRT, NIKKAR, 3-PATTI etc.)
- Reusable **patterns** maintain karna (Front panel, Sleeve etc.)
- **Stages** ka global library (Layering, Cutting Pattern, Cutting…)
- Per-product **workflow** banana (kis order mein stages chalenge)
- Live **Adda** (production batch) ka state track karna
- Har stage ka **typed record** save karna (Layering, Cutting Pattern, Cutting)

`raw_materials` upstream hai (cloth inventory) aur `tracking` downstream (barcode + history). Cross-app FK rule: **production app `raw_materials` se kuch import nahi karta**, sirf string FKs use karta hai.

---

## Big picture flow

```
Admin setup (one-time)
   │
   ▼
┌─────────────────────────────────────┐
│ Create Stage rows (admin)          │  /production/stages/
│ Create ProductPattern library      │  /production/patterns/
│ Create Products                    │  /production/products/
│ Configure Product flow (stages)    │  /production/products/<pk>/flow/
│ Assign patterns to product         │  /production/products/<pk>/patterns/
└─────────────────┬───────────────────┘
                  │
                  ▼
        Daily production
                  │
                  ▼
┌─────────────────────────────────────┐
│ Start Adda  (manager)               │  /production/addas/start/
│   → code = T-SHIRT-001              │
└─────────────────┬───────────────────┘
                  │
                  ▼
        ┌─────────────────┐
        │  Layering       │  /addas/<code>/layering/
        │  (assign        │
        │   workers,      │
        │   attach        │
        │   cloth rolls,  │
        │   record        │
        │   layers +      │
        │   leftover)     │
        └────────┬────────┘
                 │  complete (cutting_master_helper)
                 ▼
        ┌─────────────────┐
        │ Cutting Pattern │  /addas/<code>/pattern/     (optional)
        │  (cutting       │
        │   master draws  │
        │   pattern on    │
        │   layered       │
        │   cloth,        │
        │   uploads       │
        │   video/photos) │
        └────────┬────────┘
                 │  complete (helper / super_admin)
                 ▼
        ┌─────────────────┐
        │  Cutting        │  /addas/<code>/cutting/
        │  (pieces_cut,   │
        │   triggers      │
        │   barcode       │
        │   generation    │
        │   in tracking)  │
        └────────┬────────┘
                 │  complete
                 ▼
            Adda COMPLETED
```

---

## Models — ek dum simple explanation

### Product
Factory ka kaunsa item ban raha hai. Example: T-SHIRT.
- `code` (slug, unique) — Adda code is se banta hai (`T-SHIRT-001`).
- `adda_counter` — kitne Addas iss product ke ab tak ban chuke. Service `SELECT FOR UPDATE` se increment karta hai (race-safe).
- `patterns` (M2M via `ProductPatternAssignment`) — iss product ko kaunse patterns chahiye + kitne pieces.

### ProductPattern
Pattern library ka reusable shape. Example: "Sleeve", "Front Panel".
- `code` (slug) — locked after create kyunki services iss ko refer kar sakte hain.
- `reference_image` — admin sample design upload kar sakta hai.

### ProductPatternAssignment (through table)
Product ↔ ProductPattern jodne wala join row. **Pieces count** carry karta hai.
- Example: T-Shirt = 1 × Front + 1 × Back + 2 × Sleeve → 3 rows.

### Stage
Stages ka master library — admin manage karta hai (`/production/stages/`).
- `code` (slug) — services hardcode karte hain (`STAGE_LAYERING`, `STAGE_CUTTING_PATTERN`, `STAGE_CUTTING`) isliye edit nahi hota.
- `access_by_skill` + `access_by_role` — kaun stage pe kaam kar sakta hai.

### WorkflowStage
Product → Stage ka join with `order` field. Per-product workflow define karta hai.
- Example: T-Shirt → [Layering(1), CuttingPattern(2), Cutting(3)].

### Adda
Ek production batch. Code = `{Product.code}-NNN`.
- `current_stage` (FK WorkflowStage) — abhi kaunsa stage chal raha hai. `None` = completed.
- `status` — `in_progress | on_hold | completed | cancelled`.

### AddaStageRecord
Har Adda + stage combination ka **execution row**. Yahi row workers + started_at + completed_at carry karta hai. Typed records (LayeringRecord, CuttingPatternRecord, CuttingRecord) `OneToOne` se hang karte hain.

### LayeringRecord / LayeringRollEntry / RemainingClothOfClothRoll
Layering stage ke typed fields.
- `LayeringRollEntry` — har attached roll ka row (width verified, weight verified, layers_on_roll).
- `RemainingClothOfClothRoll` — har entry ka leftover (length + weight).
- `LayeringRecord` — summary (lay_count, layer_length, duration, notes).

### CuttingPatternRecord + CuttingPatternPhoto (NEW)
Cutting-pattern stage ke typed fields.
- `CuttingPatternRecord` — OneToOne stage record + optional video FileField.
- `CuttingPatternPhoto` — multiple photos per record (FK).
- Storage: `media/cutting_pattern/<ADDA_CODE>/video_*.{mp4,...}` + `photos/*.jpg`. Photos auto-compress via Pillow.

### CuttingRecord
Cutting stage ka typed record. `pieces_cut` = denormalized SUM of all `CuttingBundleItem.count` across all bundles (set at complete-time).

### CuttingPieceBreakup (Section 02 — Suggested Piece Breakup / Inventory)
Cutting master ka per-(pattern, size, color) inventory row. Acts as available cutting piece inventory:
- `count` = total pieces cut for this combo
- `consumed_count` = pieces moved into bundles (denormalized)
- `available_count` = `count − consumed_count` (computed property)

Pieces flow OUT of this table INTO bundles via `add_pieces_to_bundle`.

### CuttingBundle + CuttingBundleItem (Section 03 — Actual Manufacturing Bundles)
**Bundle = per-size manufacturing container.** Items inside = (pattern, color, count).

- `CuttingBundle(cutting_record, size, total_pieces, bundle_number)` — one per (cutting_record, size)
- `CuttingBundleItem(bundle, pattern, color, count, source_breakup)` — items consumed from `CuttingPieceBreakup`

`source_breakup` FK links each item back to the inventory row it came from. On `delete_bundle_item` / `delete_bundle`, the inventory's `consumed_count` is restored automatically.

Bundle drives barcode generation (`generate_for_cutting` iterates items, aggregates by size+color, creates `BarcodeBatch` ranges).

### BarcodeBatch + BatchBarcode (downstream — tracking app)
Storage: BarcodeBatch range row per (Adda, bundle, size, color). Lazy per-piece BatchBarcode on first scan. See [TRACKING.md](../../docs/production/TRACKING.md).

---

## Stage flow — kaise ek stage agla stage trigger karta hai

1. Worker stage workspace pe details bharta hai (form submit).
2. View ka POST handler **service function** call karta hai (`complete_layering`, `complete_pattern_stage`, `complete_cutting`).
3. Service:
   - Skill / role gate check
   - Typed record save (LayeringRecord / CuttingPatternRecord / CuttingRecord)
   - `advance_to_next_stage(adda, user)` call
4. `advance_to_next_stage` (in `adda_service.py`):
   - Next `WorkflowStage` by order find karta hai
   - `adda.current_stage` update
   - Last stage ho to `adda.status = COMPLETED`, `completed_at` stamp
   - History entry via `tracking.services.log_adda`

**Iframe-safe redirect**: jab user iframe ke andar Complete dabata hai, view check karta hai `request.POST['embedded']=='1'`. Agar haan to **new current stage ke embedded panel** pe redirect karta hai with `?advanced=1`. Embedded panel JS `?advanced=1` dekh ke parent ko postMessage bhejta hai: `{type:'stage-advanced'}`. Parent (`adda_detail.html` / `user_dashboard.html`) sun ke `window.location.reload()` chala deta hai.

---

## Roles & responsibilities

| Role | Kya kar sakta hai |
|---|---|
| `super_admin` | Sab kuch — implicit bypass har perm pe (`user_has_perm`) |
| `manager` | Adda start, workers assign, sab production CRUD |
| `karigar` | Stage workspace pe kaam (workers assigned hone par) |
| `accountant` | Supplier + Cost Per KG view/edit |
| `listing_team` | Storefront app CRUD |

Skill-level gating (cutting_master, cutting_master_helper) Stage row's `access_by_skill` M2M se aati hai.

---

## Folder structure

```
config/production/
├── README.md                          ← yeh file
├── apps.py                            ← Django AppConfig
├── admin.py                           ← Django admin registrations
├── constants.py                       ← STAGE_LAYERING, STAGE_CUTTING_PATTERN, STAGE_CUTTING
├── models.py                          ← saare models (Product, Stage, Adda, *Record, *Photo)
│
├── forms/                             ← Django form classes
│   ├── adda_forms.py
│   ├── product_forms.py
│   └── layering_forms.py
│
├── services/                          ← business logic — multi-row writes yahan
│   ├── _shared.py                    ← skill/role gate helpers (DRY)
│   ├── adda_service.py               ← Adda lifecycle, advance_to_next_stage
│   ├── product_service.py            ← Product CRUD
│   ├── layering_service.py           ← Layering stage state machine + reopen
│   ├── cutting_pattern_service.py    ← Cutting-pattern stage NEW
│   ├── cutting_service.py            ← Cutting stage
│   ├── flow_service.py               ← per-product Stage list editor
│   ├── access_service.py             ← per-stage skill/role gating
│   └── activity_service.py           ← cross-Adda activity timeline
│
├── views/                             ← Django CBVs + FBVs
│   ├── mixins.py                      ← ProductionRoleMixin, SuperAdminOnlyMixin
│   ├── dashboard.py
│   ├── adda_views.py                  ← Adda list / detail / create
│   ├── product_views.py
│   ├── flow_views.py                  ← per-product flow editor
│   ├── access_views.py                ← Stage library CRUD (perm-gated)
│   ├── pattern_views.py               ← ProductPattern CRUD + per-product assign NEW
│   ├── pattern_stage_views.py         ← cutting_pattern workspace + actions NEW
│   └── stage_views.py                 ← Layering workspace + stage panel dispatcher
│
├── templates/production/              ← page-scoped HTML
│   ├── adda_detail.html               ← Adda detail (tabbed pipeline)
│   ├── adda_list.html, adda_form.html
│   ├── product_list.html, product_form.html, product_flow.html
│   ├── product_patterns_edit.html     ← NEW
│   ├── pattern_list.html, pattern_form.html, pattern_confirm_delete.html  ← NEW
│   ├── stage_list.html, stage_form.html, stage_confirm_delete.html
│   ├── layering_workspace.html, _stage_panel_layering.html
│   ├── pattern_workspace.html, _stage_panel_cutting_pattern.html  ← NEW
│   ├── cutting_form.html, _stage_panel_cutting.html
│   ├── stage_panel_embedded.html      ← iframe-friendly wrapper
│   └── _form_styles.html, _activity_feed.html, ...
│
├── urls.py                            ← route table
├── migrations/                        ← schema changes (0001 → 0014)
└── tests/                             ← pytest-style tests
```

---

## Important Django concepts in this app

| Concept | Where to see |
|---|---|
| **Service layer** owns multi-row writes (CLAUDE.md rule #4) | `services/*.py` |
| **`@transaction.atomic`** wraps every mutating service | e.g. `complete_layering`, `reopen_layering` |
| **`select_for_update`** for race-safe counters | `adda_service.create_adda` |
| **Permissions** via `permission_service` — no raw `is_superuser` | view mixins + `user_has_perm` |
| **Iframe + postMessage** for inline stage panels | `stage_panel_embedded.html` + `adda_detail.html` |
| **Pillow image compression** on save | `cutting_pattern_service._compress_image` |
| **`STORAGES['default']`** abstraction for media (S3-swappable) | `config/config/settings/base.py` |
| **Generic FileField/ImageField `upload_to=callable`** | `_cutting_pattern_video_path` etc. |

---

## Request lifecycle (example: "Complete Layering" click)

```
1. Browser: POST /production/addas/T-SHIRT-001/layering/complete/
            (form submit from iframe, embedded=1, csrf_token included)

2. urls.py routes → LayeringCompleteView (production/views/stage_views.py)

3. LoginRequiredMixin → user logged in?
   ProductionRoleMixin → user in PRODUCTION_ROLES?

4. View.post():
   - request.POST parse → action ('draft' | 'complete'), header values,
     per-entry breakup data
   - save_layering_draft(...) — lax write of header + per-entry
   - if action=='complete':
       complete_layering(...) — strict service call
         ├── @transaction.atomic
         ├── _ensure_can_manage(user)
         ├── _ensure_can_complete_layering(user)
         ├── validate: duration > 0, layer_length > 0, all entries have
                      layers + leftover
         ├── per-roll layers_on_roll stamp onto ClothRoll
         ├── LayeringRecord.objects.create(...)
         └── advance_to_next_stage(adda, user)
                ├── find next WorkflowStage by order
                ├── update adda.current_stage (or COMPLETED if last)
                └── log_adda(AddaHistory.STAGE_ADVANCED)

5. View returns 302 redirect:
   - if embedded=1: → /production/addas/<code>/stage/<next>/?embedded=1&advanced=1
   - else: → /production/addas/<code>/

6. Browser follows redirect inside iframe → new stage panel loads.
   JS reads ?advanced=1 → postMessage parent {type:'stage-advanced'}.
   Parent listens → window.location.reload() → fresh state shown.
```

---

## Database relations diagram

```
                ┌─────────────┐
                │   Product   │
                └──────┬──────┘
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
┌─────────────┐ ┌──────────────┐ ┌────────────────────────┐
│WorkflowStage│ │ProductPattern│ │ProductPatternAssignment│
│  (order)    │ │ Assignment   │ │  (pieces_count)        │
└──────┬──────┘ │ (M2M thru)   │ └───────┬────────────────┘
       │ stage  └──────┬───────┘         │
       ▼               ▼                 │
   ┌───────┐    ┌──────────────┐         │
   │ Stage │    │ProductPattern│ ◀───────┘
   │(libr.)│    │  (library)   │
   └───────┘    └──────────────┘
       ▲
       │
       │
       │              ┌─────────────────┐
       └──────────────┤      Adda       │
                      │  current_stage  │
                      └────────┬────────┘
                               │
                               ▼
                   ┌──────────────────────┐
                   │  AddaStageRecord     │
                   │  (workers M2M)       │
                   │  ┌────────────────┐  │
                   │  │ LayeringRecord │  │
                   │  │ CuttingPattern │  │
                   │  │   Record       │  │
                   │  │ CuttingRecord  │  │
                   │  └────────────────┘  │
                   └──────────────────────┘
                          │ rolls assigned
                          ▼
              ┌────────────────────────┐
              │ raw_materials.ClothRoll│  (upstream app)
              └────────────────────────┘
                          │ piece barcodes
                          ▼
              ┌────────────────────────┐
              │ tracking.BatchBarcode  │  (downstream app)
              └────────────────────────┘
```

---

## Step-by-step: T-SHIRT-001 ka complete journey

| Step | Who | Action | Where |
|---|---|---|---|
| 1 | Manager | Start Adda for T-SHIRT product | `/production/addas/start/` |
| 2 | (system) | Adda code = `T-SHIRT-001`, current_stage = Layering wf | `create_adda` service |
| 3 | Manager | Assign workers (cutting_master + helper) | `/addas/T-SHIRT-001/layering/` Section 02 |
| 4 | Master | Attach cloth rolls + verify width/weight | Section 02 attach form |
| 5 | Master | Fill per-roll layers + leftover breakup | Section 04 form |
| 6 | Helper | Click "Complete Layering → Advance" | Section 04 button |
| 7 | (system) | LayeringRecord created → advance → current = Cutting Pattern | `complete_layering` service |
| 8 | Master | Open `/addas/T-SHIRT-001/pattern/` — see pattern checklist | Section 01 |
| 9 | Master | Pick video file (auto-submits) | Section 03 |
| 10 | Master | Pick photos (auto-submits each batch) | Section 04 |
| 11 | Helper | Click "Complete Pattern" → confirm | Section 05 |
| 12 | (system) | Advance → current = Cutting | `complete_pattern_stage` |
| 13 | Manager | Open Cutting workspace `/addas/<code>/cutting/workspace/` — Section 02 inventory + Section 03 bundles | `cutting-workspace` |
| 14 | Master | Fill Section 02 cutting pieces (Pattern × Size × Color × Count) | upsert_breakup_row |
| 15 | Master | Section 03 "+ Create New Bundle" — pick size + multi-select Pattern × Color × Take from inventory | `create_bundle_with_pieces` (atomic header + items) |
| 16 | (system) | `CuttingBundleItem` rows created; `consumed_count` incremented on source breakup rows | service |
| 17 | Helper | Section 05 — review barcode preview (Bundle × Color × Start..End ranges) → Complete Cutting | `complete_cutting` |
| 18 | (system) | `BarcodeBatch` ranges created (one per bundle × color); `BatchBarcode` lazy on scan | `tracking.services.generate_for_cutting` |
| 19 | (system) | Adda status = COMPLETED (if last stage), current_stage = None | `advance_to_next_stage` |

---

## Admin tools (out-of-band corrections)

- **Layering Reopen** (admin only): `POST /addas/<code>/layering/reopen/` — completed Layering ko unlock karta hai correction ke liye. Header values (length/duration/notes) `sr.draft_*` mein wapas copy hote hain. Refuses if downstream stage already started.
- **Stage library editor**: `/production/stages/` — perm-gated (`production.change_stage`). Super Admin bypass.
- **Per-product flow editor**: `/production/products/<pk>/flow/` — drag stages in/out of product workflow.

---

## Tests + verify

```bash
cd /home/tech/umesh-personal/django_inventory
env/bin/python config/manage.py check                                                       # clean
env/bin/python config/manage.py test raw_materials production tracking inventory accounts   # 74/74
env/bin/python config/manage.py runserver
```

---

## Where to read next

- `../docs/production/OVERVIEW.md` — subsystem index
- `../docs/production/CUTTING_PATTERN.md` — cutting_pattern stage deep dive
- `../docs/production/LAYERING_STAGE.md` — layering stage deep dive
- `../docs/production/CHAT_LOG.md` — chronological design decisions
- `../CLAUDE.md` — repo-wide rules (service layer, RBAC, no signals)
