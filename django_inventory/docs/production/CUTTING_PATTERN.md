---
id: production-cutting-pattern
type: topic-canonical
status: active
owner: handwritten
scope: production subsystem
anchors: —
verified: 2026-07-13
---

# Pattern Design Stage (code: cutting_pattern; renamed from "Cutting Pattern" 2026-07-05, R8)

Pattern master verifies every Product Pattern Design on the layered cloth — phone CHECKLIST (R8) or the management console, both writing the same verification rows — and records evidence (video + photos). FIXED-per-Adda pay (stage-trio spec 2026-07-05). Sits between Layering and Cutting in product flows that require it. Optional per-product — admin inserts via the flow editor.

## Data model

```
production/models.py
────────────────────
ProductPattern
  ├── code (slug, unique, LOCKED on update)
  ├── name, description, reference_image, is_active

ProductPatternAssignment   (through table)
  ├── product (FK Product, CASCADE)
  ├── pattern (FK ProductPattern, PROTECT)
  ├── pieces_count (PositiveSmallIntegerField, default=1)
  ├── notes
  └── unique_together = (product, pattern)

Product.patterns = M2M ProductPattern through ProductPatternAssignment

CuttingPatternRecord       (OneToOne stage_record)
  ├── stage_record (OneToOne AddaStageRecord, CASCADE, related_name='cutting_pattern')
  ├── video (FileField, blank=True, null=True — optional)
  └── notes

CuttingPatternPhoto         (FK record, multiple per record)
  ├── record (FK CuttingPatternRecord, CASCADE, related_name='photos')
  ├── image (ImageField)
  ├── caption (CharField 200, blank)
  └── uploaded_by (FK User, PROTECT)
```

## Stage row (DB)

Seeded by `production/migrations/0013_seed_cutting_pattern_stage.py`:

```python
Stage(
    code='cutting_pattern',
    name='Pattern Design (code cutting_pattern)',
    description='Cutting master draws pattern on layered cloth + records via video/photos. Sits between layering and cutting.',
    is_active=True,
    access_by_skill=[cutting_master, cutting_master_helper],
)
```

Access for the stage panel UI is controlled by the Stage row's `access_by_skill` + `access_by_role` M2Ms — Super Admin + Manager always bypass via `MANAGEMENT_ROLES` in `access_service`.

## Service layer (`production/services/cutting_pattern_service.py`)

```
start_pattern_stage(adda, worker_ids, user)
  - Management gate
  - Pre: adda.current_stage_id == cutting_pattern wf
  - Creates AddaStageRecord (started_at=now) + assigns workers M2M

save_pattern_record(adda, video_file, notes, user)
  - Skill gate (cutting_master OR cutting_master_helper, management bypass)
  - Pre: stage_record exists + not completed
  - Lazily get_or_create CuttingPatternRecord
  - Updates video (if provided) and/or notes
  - Either can be None — both fields independently optional

attach_photo(stage_record, uploaded_image, caption, user)
  - Skill gate
  - Pre: stage_record exists + not completed
  - Lazily creates CuttingPatternRecord (no video required)
  - Pillow compresses to JPEG q=80, max 2400px long edge, EXIF-honored
  - Falls back to original bytes if Pillow fails (unusual format)
  - Creates CuttingPatternPhoto row

complete_pattern_stage(adda, user)
  - Helper-skill or super_admin gate
  - Pre: stage_record exists + not completed
  - Requires: has_video OR has_photo (at least one)
  - Stamps sr.completed_at + completed_by
  - Calls advance_to_next_stage

get_pattern_snapshot(adda)
  - Lightweight snapshot for dashboard/panel UIs
  - Returns dict with state in {absent, not_started, in_progress, completed}
```

## URL surface

```
GET  /production/addas/<code>/pattern/                      Workspace (standalone)
GET  /production/addas/<code>/stage/cutting_pattern/?embedded=1   Embedded iframe panel

POST /production/addas/<code>/pattern/start/                Manager assigns workers
POST /production/addas/<code>/pattern/save/                 Upload/replace video + notes
POST /production/addas/<code>/pattern/photos/add/           Multipart, multiple files
POST /production/addas/<code>/pattern/photos/<pk>/remove/   Detach photo
POST /production/addas/<code>/pattern/complete/             Finalize + advance
```

## Templates

- `production/_stage_panel_cutting_pattern.html` — reusable partial (workspace + iframe + dashboard accordion all include this)
- `production/pattern_workspace.html` — standalone full-page wrapper
- Five sections in the panel:
  1. Pattern Checklist (from `Product.pattern_assignments`)
  2. Assigned Workers (Manager assigns; chip display)
  3. Video upload (auto-submits on file pick)
  4. Photo upload (auto-submits on file pick, multiple allowed)
  5. Complete + advance (helper-skill gate; native confirm dialog)

Auto-submit JS exists because earlier users were picking a file but never clicking the submit button. Now `<input change>` → `form.submit()` immediately, with status line showing "Uploading…" + size in MB.

## Storage

- Django `STORAGES['default']` abstraction — currently `FileSystemStorage` writing to `media/cutting_pattern/<adda_code>/`
- Swapping to S3/MinIO is a settings-level change in `config/config/settings/base.py:203` — zero code change
- Video: stored as uploaded (no recompress). Future ffmpeg-driven pipeline deferred
- Photos: compressed by Pillow on save inside `_compress_image()` helper

Disk layout:
```
media/cutting_pattern/<ADDA_CODE>/
  video_<original_name>.<ext>
  photos/
    <original_basename>.jpg
    ...
```

## Permissions

| Action | Gate |
|---|---|
| Start stage | MANAGEMENT_ROLES (super_admin / manager) |
| Upload video / save notes / attach photo / remove photo | cutting_master OR cutting_master_helper skill, OR management |
| Complete + advance | cutting_master_helper skill, OR super_admin |

`_StagePermissionRequired` is NOT used on the workspace/action views (they live behind `ProductionRoleMixin` instead). Stage CRUD (Stage library editing) uses perm-based mixin separately.

## Iframe-safe Complete flow

On Complete from embedded panel:
1. Service `complete_pattern_stage` → `advance_to_next_stage` → `adda.current_stage` moves to next wf
2. View checks `POST['embedded']=='1'` → redirect to NEW current stage's embedded URL with `?embedded=1&advanced=1`
3. Embedded panel JS reads `?advanced=1` → `postMessage` to parent with `{type:'stage-advanced'}`
4. Parent (`adda_detail.html` or `user_dashboard.html`) listens → `window.location.reload()`

Same pattern as Layering Complete + Layering Reopen. Avoids "refused to connect" browser error from `X-Frame-Options: DENY` defaulting.

## Testing notes (no automated tests yet — follow-up)

Manual test checklist for fresh chat:
1. Configure product flow: `/production/products/<pk>/flow/` → insert cutting_pattern stage
2. Configure patterns: `/production/products/<pk>/patterns/` → assign at least one pattern with count
3. Start Adda → complete Layering → advances to cutting_pattern
4. Open workspace `/production/addas/<code>/pattern/`
5. Manager assigns cutting masters
6. Cutting master uploads either photo or video (auto-submit fires)
7. Photo appears in grid; video plays inline
8. Helper-skill user clicks Complete → confirm dialog → advances to Cutting

## Open follow-ups

- **HIGH**: write tests for cutting_pattern (start, attach_photo bootstrap, complete gates, complete-without-video, complete-without-photos)
- **MEDIUM**: ffmpeg-driven video recompression
- **MEDIUM**: pattern stage history events (currently only generic STAGE_ADVANCED transition)
- **MEDIUM**: pattern reopen (mirror of layering reopen)
- **LOW**: per-pattern photo grouping in UI (right now all photos pool together)
