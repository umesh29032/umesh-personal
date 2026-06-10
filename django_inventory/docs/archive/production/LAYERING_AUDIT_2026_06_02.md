# Layering Stage — Audit (2026-06-02, read-only)

Static audit of Stage 1 (Layering). No code changed. Covers ER + sequence
diagrams, full relationship trace, dashboard data flow, draft-saving logic, the
API→Service→Model→DB map, and refactor risks. Companion to `LAYERING_STAGE.md`
(behaviour spec) — this file is the structural/architecture view.

---

## 0. Audit summary

| Area | State |
|---|---|
| Models | 4 (`AddaStageRecord` shared parent + `LayeringRollEntry`, `RemainingClothOfClothRoll`, `LayeringRecord`). Clean FKs, correct on_delete (CASCADE for owned children, PROTECT for ClothRoll). |
| Service | `layering_service.py` (785 LOC), 12 funcs, all `@transaction.atomic`, all raise (no silent returns). Single-writer discipline holds. |
| Manufacturing cost | ✅ wired — `per_layer` × `lay_count`, frozen on advance. |
| **Worker earning** | ❌ **NOT wired for layering** — no `StageWorkAssignment` is created for the layering stage (only cutting allocates). A layering worker earns ₹0 on the dashboard. **This is the one functional gap.** |
| Dashboard | ✅ ready — earning rollups are stage-agnostic; will show layering automatically once allocations exist. |
| Draft saving | ✅ robust, lax-by-design (partial rows tolerated; bad rows silently skipped — see §6 risk). |
| Denormalization | `ClothRoll.{layers_on_roll, layer_length_meters, remaining_length/weight}` written from 4 service paths — sync risk on refactor (§8). |

---

## 1. ER diagram

```mermaid
erDiagram
    Adda ||--o{ AddaStageRecord : "has stage records"
    WorkflowStage ||--o{ AddaStageRecord : "typed per product"
    AddaStageRecord ||--o| LayeringRecord : "OneToOne (on complete)"
    AddaStageRecord ||--o{ LayeringRollEntry : "1 per attached roll"
    AddaStageRecord }o--o{ User : "workers M2M (roster)"
    LayeringRollEntry }o--|| ClothRoll : "FK PROTECT"
    LayeringRollEntry ||--o{ RemainingClothOfClothRoll : "leftover pieces"
    RemainingClothOfClothRoll }o--|| ClothRoll : "FK PROTECT"
    RemainingClothOfClothRoll }o--|| Adda : "source_adda PROTECT"
    LayeringRecord }o--o{ ClothRoll : "rolls_used M2M (snapshot)"
    User ||--o{ LayeringRollEntry : "attached_by"

    %% Earning side — generic, CURRENTLY only populated by Cutting
    AddaStageRecord ||--o{ StageWorkAssignment : "allocation (NOT created for layering yet)"
    User ||--o{ StageWorkAssignment : "worker"
    StageWorkAssignment ||--o| WorkerLedgerEntry : "EARNING credit"

    AddaStageRecord {
        datetime started_at
        datetime completed_at
        decimal draft_layer_length_meters "layering-specific draft"
        int draft_duration_minutes
        text draft_notes
        decimal processing_cost "frozen on advance"
    }
    LayeringRollEntry {
        int width_verified_inch
        decimal weight_verified_kg
        int layers_on_roll "filled at breakup/complete"
        FK roll "ClothRoll PROTECT"
        unique stage_record_roll "unique_together"
    }
    RemainingClothOfClothRoll {
        decimal remaining_length_meters
        decimal remaining_weight_kg
        bool is_consumed "future reuse stub"
    }
    LayeringRecord {
        int lay_count "Σ layers_on_roll"
        int total_colors "distinct cloth_color"
        decimal layer_length_meters
        int duration_minutes
    }
```

---

## 2. Model relationship trace (every edge + on_delete)

| From | Field | To | Kind | on_delete | Notes |
|---|---|---|---|---|---|
| `AddaStageRecord` | `adda` | `Adda` | FK | CASCADE | delete Adda → stage records gone |
| `AddaStageRecord` | `workflow_stage` | `WorkflowStage` | FK | PROTECT | can't delete a stage in use |
| `AddaStageRecord` | `workers` | `User` | M2M | — | roster only (NOT earnings) |
| `LayeringRecord` | `stage_record` | `AddaStageRecord` | OneToOne | CASCADE | 1 record per completed stage |
| `LayeringRecord` | `rolls_used` | `ClothRoll` | M2M | — | snapshot at complete |
| `LayeringRollEntry` | `stage_record` | `AddaStageRecord` | FK | CASCADE | entries die with stage |
| `LayeringRollEntry` | `roll` | `ClothRoll` | FK | PROTECT | roll can't vanish mid-stage; `unique_together(stage_record, roll)` |
| `LayeringRollEntry` | `attached_by` | `User` | FK | PROTECT | audit |
| `RemainingClothOfClothRoll` | `roll` | `ClothRoll` | FK | PROTECT | |
| `RemainingClothOfClothRoll` | `source_adda` | `Adda` | FK | PROTECT | |
| `RemainingClothOfClothRoll` | `layering_entry` | `LayeringRollEntry` | FK | SET_NULL | leftover survives entry delete |
| `StageWorkAssignment` (expense) | `stage_record` | `AddaStageRecord` | FK | PROTECT | earning allocation — **layering never creates one today** |

Reverse accessors used in code: `sr.layering` (OneToOne), `sr.layering_roll_entries`, `entry.remaining_pieces`, `sr.workers`, `roll.remaining_pieces`.

---

## 3. Sequence diagram — Complete Layering → advance

```mermaid
sequenceDiagram
    actor W as Worker (cutting_master_helper)
    participant V as LayeringCompleteView.post
    participant S as layering_service
    participant A as adda_service.advance_to_next_stage
    participant C as cost_service.freeze_stage_cost
    participant H as tracking.history_service
    participant DB as PostgreSQL

    W->>V: POST /addas/<code>/layering/complete/ (action=complete)
    V->>S: save_layering_draft(per_entry_data, header)   %% persist first, always
    S->>DB: update AddaStageRecord.draft_*; per row save_layering_breakup
    Note over S,DB: breakup → LayeringRollEntry.layers_on_roll + upsert RemainingCloth + denorm ClothRoll
    V->>V: re-fetch entries; verify EVERY entry has layers AND leftover
    alt any missing
        V-->>W: error toast (lists problem rolls); NO advance (drafts kept)
    else all present
        V->>S: complete_layering(duration, layer_length, per_entry_layers, notes)
        S->>S: _ensure_can_manage + _ensure_can_complete_layering (helper skill)
        S->>DB: per entry: layers_on_roll + denorm roll.layers/layer_length
        S->>DB: AddaStageRecord.completed_at/by; clear draft_*
        S->>DB: create LayeringRecord (lay_count, total_colors, ...); rolls_used.set
        S->>A: advance_to_next_stage(adda)
        A->>C: freeze_stage_cost(layering sr)  %% per_layer × lay_count
        A->>DB: adda.current_stage = cutting
        A->>H: log STAGE_ADVANCED (+ COST_FROZEN)
        V-->>W: redirect Adda Detail; layering ✓, cutting ▸
    end
```

## 3b. Sequence — Attach roll & autosave draft

```mermaid
sequenceDiagram
    actor W as Worker
    participant V as Layering action view
    participant S as layering_service
    participant R as raw_materials.assign_roll_to_adda
    participant DB as PostgreSQL

    W->>V: POST attach-roll (roll, width, weight)
    V->>S: attach_roll_to_layering(...)
    S->>R: assign_roll_to_adda → ClothRoll.status=USED, adda set, history
    S->>DB: create LayeringRollEntry
    V-->>W: redirect workspace

    W->>V: debounced POST complete/ (action=draft)  %% _autosave.html
    V->>S: save_layering_draft(...)
    S->>DB: draft_* + per-row breakup (lax; bad rows skipped)
    V-->>W: 204 No Content (silent autosave)
```

---

## 4. Dashboard data flow (earnings)

```
StageWorkAssignment (rate×qty frozen)            WorkerLedgerEntry (append-only)
        │  (created by allocate_stage_work)            │ (credit posted same call)
        ▼                                              ▼
expense.payroll_service:
  worker_summary(worker)         → total_earnings / advance_outstanding / pending_payable / total_settled
  worker_stage_earnings(worker)  → GROUP BY workflow_stage.stage.name   ← stage-agnostic
  worker_adda_earnings(worker)   → GROUP BY adda, then stage
        │
        ▼
Views:  MyEarningsView (/expense/my/, self)  ·  WorkerPayrollDetailView (/expense/workers/<pk>/, can_view_worker)
        inventory.user_dashboard (helper_data: layering-specific WIP cards for cutting_master_helper)
        │
        ▼
Templates: my_earnings.html · worker_detail.html · user_dashboard.html
```

**Key fact:** `worker_stage_earnings` / `worker_adda_earnings` key off
`stage_record__workflow_stage__stage__name` — they are **stage-agnostic**. The
moment a `StageWorkAssignment` exists with a *layering* `stage_record`, layering
earnings appear on the dashboard with **zero dashboard changes**. The only thing
missing is the **write path** that creates those allocations for layering.

`user_dashboard` separately builds `helper_data` (active layering list + personal
layering stats) for `cutting_master_helper` users — but that's *activity*, not
*earnings*; it reads `LayeringRecord` / stage records, not the ledger.

---

## 5. API → Service → Model → DB map

| URL (name) | View | Service | Models written | Denorm / side effects |
|---|---|---|---|---|
| `layering-workspace` (GET) | `LayeringWorkspaceView` | `get_layering_snapshot` (read) | — | reads entries + leftovers |
| `layering-start` | `LayeringStartView` | `start_layering` | `AddaStageRecord.workers` | `AddaHistory.WORKERS_ASSIGNED` |
| `layering-attach-roll` | `LayeringAttachRollView` | `attach_roll_to_layering` | `LayeringRollEntry` (create) | `ClothRoll.status=USED` + `assign_roll_to_adda` + roll history |
| `layering-quick/full-create-roll` | `Layering{Quick,Full}CreateAndAttachView` | `bulk_create_rolls`→`attach_roll_to_layering` | `ClothRoll` (create) + `LayeringRollEntry` | full path also sets supplier/cost (financial gate) |
| `layering-entry-update` | `LayeringEntryUpdateView` | `update_layering_roll_entry` | `LayeringRollEntry`, `ClothRoll` | width/weight sync to roll |
| `layering-entry-remove` | `LayeringEntryRemoveView` | `detach_roll_from_layering` | delete `LayeringRollEntry` | `ClothRoll.status=NOT_USED` + history |
| `layering-remove-remaining` | `LayeringRemoveRemainingClothView` | `remove_remaining_cloth` | delete `RemainingClothOfClothRoll` | re-denorm roll leftover |
| `layering-complete` (action=draft) | `LayeringCompleteView.post` | `save_layering_draft`→`save_layering_breakup` | `AddaStageRecord.draft_*`, `LayeringRollEntry.layers_on_roll`, `RemainingClothOfClothRoll` upsert | denorm roll leftover; returns 204 |
| `layering-complete` (action=complete) | `LayeringCompleteView.post` | `save_layering_draft` then `complete_layering` | `LayeringRecord` (create), `LayeringRollEntry`, `AddaStageRecord` (close + clear draft), `ClothRoll` (layers+length) | `advance_to_next_stage` → `freeze_stage_cost` + `AddaHistory` |
| `layering-reopen` | `LayeringReopenView` | `reopen_layering` | delete `LayeringRecord`; `AddaStageRecord` re-open | `clear_stage_cost`; `AddaHistory.STAGE_REOPENED` |

All views: `LoginRequiredMixin + ProductionRoleMixin + StageViewAccessMixin` (skill-gated render). Services re-check fine skill (`_ensure_*`).

---

## 6. Draft-saving logic

- **Entry point:** the Section-04 form posts to `layering-complete` with a hidden
  `action`. `action=draft` (debounced autosave via `_autosave.html`, ~900ms) OR
  `action=complete`.
- **`save_layering_draft`** (lax, no advance):
  - Auth: `_ensure_can_manage` (management or assigned skilled worker).
  - Header drafts → `AddaStageRecord.draft_layer_length_meters / draft_duration_minutes / draft_notes` (each `None` = skip that field; partial OK).
  - Per-row: only persists a row when **all three** of `layers`, `leftover_length`, `leftover_weight` are present; else the row is skipped. Each row goes through `save_layering_breakup`, and a `ValidationError` on one row is **swallowed** (`continue`) so a single bad row never fails the whole draft.
- **`save_layering_breakup`** (single row): sets `layers_on_roll`, upserts the
  *primary* `RemainingClothOfClothRoll` (most-recent non-consumed), denorms leftover
  onto `ClothRoll` via `_sync_roll_leftover`.
- **Persistence guarantee on Complete:** the view runs `save_layering_draft`
  **first**, always — so even if `complete_layering` then fails validation, the
  typed data the worker entered survives.
- **Clear on complete:** `complete_layering` nulls all `draft_*` fields.
- **Pre-population on render:** per-row inputs ← `entry.layers_on_roll` +
  `entry.remaining_pieces.first()`; header ← `draft_*`.

⚠️ **Silent-skip caveat:** a partially-filled row (e.g. layers set, leftover blank)
is silently *not* saved, and a row that fails `save_layering_breakup` validation is
silently dropped. Good for autosave UX, but a refactor that surfaces "what didn't
save" would reduce confusion.

---

## 7. Reopen semantics
`reopen_layering` (super_admin / manager): rolls back `adda.current_stage` to
layering, clears `completed_at/by`, **deletes the `LayeringRecord`** (typed
summary) but **preserves** entries + per-roll layers + leftovers, and calls
`clear_stage_cost` (so a reopened-not-recompleted stage carries no money).
Re-complete re-creates the record + re-freezes cost.

---

## 8. Refactor risks & dependencies

**Risks**
1. **Earning gap (the build):** no allocation for layering → wiring it must reuse
   `expense.allocate_stage_work` (+ `role_rate_for` for per-role pay). Decide the
   quantity basis (per-layer / per-roll / flat) before building — it sets the
   `allocated_quantity` semantics.
2. **Denormalization fan-out:** `ClothRoll.{layers_on_roll, layer_length_meters,
   remaining_length/weight}` is written from `save_layering_breakup`, `complete_layering`,
   `update_layering_roll_entry`, `detach`, `remove_remaining_cloth`. Any refactor
   must keep all write points in sync (single `_sync_roll_leftover` helps for leftover,
   but layers/length are copied inline in 2 places).
3. **Layering-specific columns on the shared `AddaStageRecord`** (`draft_layer_length_meters`
   etc.) — leaky abstraction; future stages either reuse these oddly-named columns
   or add their own. Consider a per-stage draft JSON if more stages need drafts.
4. **Hardcoded skill coupling:** `_ensure_can_complete_layering` pins
   `cutting_master_helper`. Adding stages/skills means touching `_shared.py`.
5. **Silent draft skips** (§6) — refactor toward explicit per-row save status.
6. **`total_colors` recomputed via `roll__cloth_color` query** at complete — depends
   on `ClothRoll.cloth_color` being set; null colors would undercount.
7. **View re-parses + re-fetches** (`save_draft` then re-query then `complete`) —
   double DB round-trips on complete; acceptable but a hotspot if rolls are many.

**Dependencies (blast radius of a layering refactor)**
- Upstream: `raw_materials` (`assign_roll_to_adda`, `bulk_create_rolls`, `ClothRoll`),
  `adda_service.advance_to_next_stage`, `cost_service` (freeze/clear), `accounts.skills`,
  `permission_service` / `access_service`, `tracking` (`log_adda`/`log_roll`/`AddaHistory`).
- Downstream consumers of layering output: Cutting (reads `LayeringRecord.total_fabric_used_meters`),
  inventory/cloth dashboards (read denorm `ClothRoll` fields), `get_layering_snapshot`
  (3 dashboard surfaces), `expense` (where earnings should attach).
- Tests that pin behaviour: `production/tests/test_layering_workflow.py`, `test_counter_invariants.py`,
  `test_golden_path.py`, `inventory/tests.py` (helper_data), `test_cost_snapshot.py`.
