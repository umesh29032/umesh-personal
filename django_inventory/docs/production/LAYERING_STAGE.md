# Stage 1 — Layering

Reference doc for the Layering stage. Covers data model, save paths, completion handler, and where every piece of data lives.

---

## Data model (where layering data is saved)

```
AddaStageRecord (parent — one per (adda, workflow_stage))
├── started_at                                  # set on Adda create (auto)
├── completed_at, completed_by                  # set on complete
├── workers M2M → User                          # skilled users, auto-tagged + manager-refined
├── draft_layer_length_meters                   # Phase 6 — header draft (Save Draft persists)
├── draft_duration_minutes                      # header draft
├── draft_notes                                 # header draft
│
├── LayeringRollEntry (per attached cloth roll) ─────────┐
│   ├── roll FK → ClothRoll                              │
│   ├── width_verified_inch                              │ filled at attach time
│   ├── weight_verified_kg                               │ on the floor
│   ├── layers_on_roll                                   │ filled in Section 04 breakup
│   ├── notes                                            │
│   ├── attached_by FK → User                            │
│   ├── attached_at                                      │
│   │                                                    │
│   └── remaining_pieces (reverse FK) → RemainingClothOfClothRoll
│       ├── remaining_length_meters                      │
│       ├── remaining_weight_kg                          │ filled in Section 04 breakup
│       ├── notes                                        │
│       ├── source_adda FK → Adda                        │
│       ├── is_consumed, consumed_in_adda, consumed_at   │ future: leftover reuse in next Adda
│       └── created_by, created_at                       │
│                                                       ─┘
│
└── LayeringRecord (created at complete only — OneToOne)
    ├── lay_count                               # = sum of all entry.layers_on_roll
    ├── total_colors                            # = COUNT(DISTINCT roll.cloth_color) over entries
    ├── duration_minutes
    ├── layer_length_meters                     # overall, single value
    ├── rolls_used M2M → ClothRoll              # snapshot at complete time
    └── notes
```

Also denormalized onto `ClothRoll` (after complete OR breakup save):
- `ClothRoll.layers_on_roll` — copied from `LayeringRollEntry.layers_on_roll`
- `ClothRoll.layer_length_meters` — copied from `LayeringRecord.layer_length_meters`
- `ClothRoll.remaining_length_meters` — copied from primary `RemainingClothOfClothRoll`
- `ClothRoll.remaining_weight_kg` — same

Inventory dashboards / list tables read these denorm fields directly (no join through stage history).

---

## Stage lifecycle (data flow)

### 1. Adda created
`production/services/adda_service.py::create_adda(user, product)`

1. Validates product is active.
2. Fetches **all** users with `cutting_master` or `cutting_master_helper` skill.
3. **Refuses** if pool is empty (`ValidationError`).
4. Allocates Adda code race-safe via `SELECT FOR UPDATE` on Product counter.
5. Creates `Adda(code, product, current_stage=first_stage, status=IN_PROGRESS)`.
6. **Auto-creates** `AddaStageRecord(adda, layering_stage, started_at=now)`.
7. **Auto-populates** `workers M2M` with all skilled user pks.
8. Logs `AddaHistory.CREATED`.

### 2. Manager refines workers (optional)
`layering_service.start_layering(adda, worker_ids, user)`

`get_or_create` → updates `workers M2M`. Re-assigning is idempotent. Validates ≥1 cutting_master remains.

### 3. Worker attaches a roll
`layering_service.attach_roll_to_layering(stage_record, roll, width_verified, weight_verified, ..., user)`

Inside one transaction:
1. Calls `raw_materials.assign_roll_to_adda` → `ClothRoll.status = USED`, `adda` FK set, `used_by/used_at` stamped, history logged.
2. Creates `LayeringRollEntry(stage_record, roll, width_verified, weight_verified, attached_by)`.

### 4. (Optional) Filter + Quick Add / Full Add new roll
Two button paths if the cloth doesn't exist in inventory yet:

| Button | View | Backend |
|---|---|---|
| **+ Quick Add Roll** (essentials only) | `LayeringQuickCreateAndAttachView` | `bulk_create_rolls(qty=1)` → `attach_roll_to_layering` |
| **+ Add Roll (Full Details)** | `LayeringFullCreateAndAttachView` | Same + `supplier` + `cost_per_kg` (financial gate) |

### 5. Worker fills per-row breakup + clicks Save Draft / Complete
Section 04 = **ONE form** with all inputs:
- Header: `layer_length_meters` + `duration_minutes` + `notes`
- Per-row inputs (one set per LayeringRollEntry):
  - `entry_<pk>_layers` → `layers_on_roll`
  - `entry_<pk>_leftover_len` → `RemainingClothOfClothRoll.remaining_length_meters`
  - `entry_<pk>_leftover_wt` → `RemainingClothOfClothRoll.remaining_weight_kg`
- Two submit buttons (`name="action"`):
  - `value="draft"` → `save_layering_draft` (lax, no advance)
  - `value="complete"` → `complete_layering` (strict, advance)

POST endpoint: `production:layering-complete` (`addas/<code>/layering/complete/`)
View: `LayeringCompleteView.post`

Pre-population on render:
- Per-row inputs ← `entry.layers_on_roll` + `entry.remaining_pieces.first()` (primary leftover)
- Header inputs ← `stage_record.draft_layer_length_meters` / `draft_duration_minutes` / `draft_notes`

---

## "Complete Layering → Advance to Cutting" — what happens

**Button:** `<button type="submit" name="action" value="complete">Complete Layering → Advance to Cutting</button>`

**URL:** `POST /production/addas/<code>/layering/complete/`
**View:** `LayeringCompleteView.post` ([production/views/stage_views.py](../../config/production/views/stage_views.py))
**Service:** `layering_service.complete_layering` ([production/services/layering_service.py](../../config/production/stages/layering/service.py))

### View phase

1. Parse `action` from POST. `complete` branch selected.
2. Bind `CompleteLayeringForm(request.POST)` (all fields `required=False` so form-level validation is lax).
3. Parse `entry_<pk>_layers` / `_leftover_len` / `_leftover_wt` from POST into `per_entry_data` dict.
4. **Always run `save_layering_draft` first** — persists everything the user typed so even if Complete fails validation, data survives.
5. Re-fetch entries from DB. Check **both** `layers_on_roll` AND `remaining_pieces` populated for every entry.
   - If missing: surface error message listing problem rolls. No advance.
6. Build `per_entry_layers = {pk: layers_on_roll}` dict from DB state.
7. Call `complete_layering(adda, duration_minutes, layer_length_meters, per_entry_layers, notes, user)`.
8. Redirect to Adda Detail.

### Service phase (`complete_layering`)

Inside `@transaction.atomic`:

1. **Auth gates:**
   - `_ensure_can_manage` → must be PRODUCTION_ROLES (super_admin / manager / karigar)
   - `_ensure_can_complete_layering` → must be `cutting_master_helper` skill OR `is_superuser` (strict)

2. **State gates:**
   - Adda must be at Layering stage + status IN_PROGRESS
   - `duration_minutes` ≥ 1
   - `layer_length_meters` > 0
   - `AddaStageRecord` for this stage exists + not yet completed

3. **Per-entry validation:**
   - Every entry has a positive `layers_on_roll` (raise if any missing)
   - Every entry has ≥1 `RemainingClothOfClothRoll` row (raise if any missing)

4. **Per-roll propagation (inside the transaction):**
   ```python
   for e in entries:
       e.layers_on_roll = per_entry_layers[e.pk]
       e.save(update_fields=['layers_on_roll', 'updated_at'])
       # Denormalize onto ClothRoll for inventory-level lookup
       e.roll.layers_on_roll = per_entry_layers[e.pk]
       e.roll.layer_length_meters = layer_length_meters
       e.roll.save(update_fields=['layers_on_roll', 'layer_length_meters'])
   ```

5. **Aggregate snapshot:**
   - `lay_count_total = sum(per_entry_layers.values())`
   - `total_colors = COUNT(DISTINCT roll__cloth_color_id)` over entries
   - `roll_ids = [e.roll_id for e in entries]`

6. **Stage record close:**
   ```python
   sr.completed_at = timezone.now()
   sr.completed_by = user
   sr.draft_layer_length_meters = None      # clear drafts
   sr.draft_duration_minutes = None
   sr.draft_notes = ''
   sr.save(...)
   ```

7. **LayeringRecord creation:**
   ```python
   lr = LayeringRecord.objects.create(
       stage_record=sr,
       lay_count=lay_count_total,
       total_colors=total_colors,
       duration_minutes=duration_minutes,
       layer_length_meters=layer_length_meters,
       notes=notes,
   )
   lr.rolls_used.set(roll_ids)   # M2M snapshot
   ```

8. **Stage advance:** `advance_to_next_stage(adda, user)` in `adda_service.py`:
   - Look up next `WorkflowStage` (`order > current.order`).
   - If found (cutting): `adda.current_stage = nxt`, save.
   - If `None` (last stage): `adda.status = COMPLETED`, `current_stage = NULL`, `completed_at = now`.
   - Log `AddaHistory.STAGE_ADVANCED` with `stage_from=layering`, `stage_to=cutting`.
   - If completed: also log `AddaHistory.COMPLETED`.

9. Returns `LayeringRecord` instance.

### Result visible to user

- Toast: "Layering complete for {code}. Advanced to Cutting."
- Redirect to `/production/addas/<code>/` (Adda Detail)
- Layering tab pill turns ✓ green; Cutting tab pill turns ▸ copper (current)
- Activity feed gains 1+ entries (`marked stage complete`, `advanced stage`)
- Per attached roll: `roll.layers_on_roll` + `roll.layer_length_meters` now visible on roll detail + cloth dashboard

### Failure modes

| Scenario | What happens |
|---|---|
| Some row missing layers/leftover | Error toast lists problem rolls. Drafts saved. No advance. |
| User lacks helper skill | `PermissionDenied`. Error toast: "only cutting_master_helper can complete Layering stage" |
| Adda not at Layering | `ValidationError`. Defensive — shouldn't happen via UI. |
| Adda not in-progress | `ValidationError`. Shouldn't happen via UI. |
| Race: stage_record already completed | `ValidationError`. Idempotent guard. |

---

## Per-stage save services (table)

| Service | Surface | Mandatory inputs | Side effects |
|---|---|---|---|
| `start_layering` | Workers chip widget | worker_ids (≥1 cutting_master) | `AddaStageRecord.workers` M2M replaced |
| `attach_roll_to_layering` | "Add Cloth Roll" form | roll, width, weight | `ClothRoll.status=USED`, new `LayeringRollEntry` |
| `update_layering_roll_entry` | Inline edit (Correct/remove) | entry, optional fields | Entry + linked roll field updates |
| `detach_roll_from_layering` | Detach button | entry | Entry deleted, `ClothRoll.status=NOT_USED` |
| `save_layering_breakup` | (Internal) — called by `save_layering_draft` | entry, layers, leftover_len, leftover_wt | Entry + upsert primary `RemainingClothOfClothRoll` + denorm to ClothRoll |
| `save_layering_draft` | Section 04 "💾 Save Draft" | adda, per_entry_data, header_fields | Stage record `draft_*` fields + per-row via `save_layering_breakup` |
| `record_remaining_cloth` | (Internal) extra leftover piece | entry, weight, length | New `RemainingClothOfClothRoll` row |
| `remove_remaining_cloth` | × button on leftover badge | leftover | Delete (blocked if `is_consumed`) |
| `complete_layering` | Section 04 "Complete" button | adda, duration, layer_length, per_entry_layers | LayeringRecord + roll denorm + advance |
| `sync_layering_workers_for_skill` | accounts signal `m2m_changed` | user | Adds user to all active Layering `workers` M2M |

All services are `@transaction.atomic`. All raise `ValidationError` / `PermissionDenied` — never silent returns.

---

## Forms (per-stage)

`production/forms/layering.py`:
| Form | Used by |
|---|---|
| `StartLayeringForm` | Section 01 worker assignment |
| `AttachRollForm` | Section 02 attach form (width + weight) |
| `EditRollEntryForm` | Inline row edit |
| `RemainingClothForm` | (Reserved for future multi-leftover UI) |
| `CompleteLayeringForm` | Section 04 header (layer_length + duration + notes) |

All inherit from `production.forms._shared` for widgets (worker checkboxes, roll labels).

---

## Templates (per-stage)

| Template | Used by |
|---|---|
| `_stage_panel_layering.html` | Layering full panel (Sections 01-04). Reusable. |
| `_stage_card_layering.html` | Tab summary card on Adda Detail (read-only) |
| `_activity_feed.html` | Activity timeline (shared with user dashboard) |
| `stage_panel_embedded.html` | Chromeless wrapper for iframe |
| `stage_panel_standalone.html` | Full-page wrapper for standalone view |

---

## Permission matrix

| User type | See Adda | Open Layering panel | Attach roll | Save Draft | Complete |
|---|---|---|---|---|---|
| super_admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| manager | ✅ | ✅ | ✅ (bypass) | ✅ | ❌ (needs helper skill) |
| karigar + cutting_master + assigned | ✅ | ✅ | ✅ | ✅ | ❌ |
| karigar + cutting_master_helper + assigned | ✅ | ✅ | ✅ | ✅ | ✅ |
| karigar (no skill) | ✅ read-only | View only | ❌ | ❌ | ❌ |
| listing_team | ✅ read-only | View only | ❌ | ❌ | ❌ |

Template gates (`can_assign`, `can_attach`, `can_draft`, `can_complete`) mirror service-side checks. Defence in depth.

---

## Future stages — drop-in pattern

To add Stage 3 (e.g., Sewing):
1. Add `WorkflowStage.StageType.SEWING = 'sewing'` enum value + seed migration on each Product
2. Create `production/forms/sewing.py` with stage-specific forms
3. Create `production/services/sewing_service.py` with `start_sewing`, `save_sewing_breakup`, `save_sewing_draft`, `complete_sewing`
4. Create `production/templates/production/_stage_panel_sewing.html` (copy layering panel as starting point)
5. Create `production/templates/production/_stage_card_sewing.html` (tab summary)
6. Add views in `stage_views.py` (or new `sewing_views.py`)
7. Register URLs in `urls.py`
8. Dispatch in `StagePanelView.get_context_data` (`stage_type == 'sewing'` branch)

Adda Detail tab UI auto-renders new stage tab. Activity feed auto-includes new stage events.
