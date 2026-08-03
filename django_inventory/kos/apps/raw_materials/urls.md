---
id: app-raw-materials-urls
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "Any /raw-materials/ URL — rolls, damage, assignment, and the three masters, each individually."
related: [app-raw-materials]
---

# raw_materials — URL Learning Pages (all 23, individually)

> 📂 [raw_materials app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)
> Source: `config/raw_materials/urls.py`. Management-lane + sidebar-gated;
> intake is SA-only (master-data lockdown, MGT-A certified).

> 💡 **Samjho aise** — URLs = **address book**
>
> Yeh file batati hai kaunsa web address (jaise `/production/addas/`) kis view pe jaata hai. Jab aapko pata na ho ki koi page kis code se banta hai — **hamesha yahin se shuru karo**.
>
> *(`raw_materials` app ka kaam: **kapda** — roll, cloth type, colour, storage.)*

**Reading Strategy** — *Beginner:* §§1–3 → §8 (the reservation!).
*Intermediate:* §§4–7. *Senior:* §8's guards + §7's honesty semantics +
the archive-vs-delete pattern on any ONE master (§§9–13).

## Dashboards

### 1. `/raw-materials/` — `dashboard`
GET → `RawMaterialDashboardView`. Stock at a glance — all numbers DERIVED
(`stock_status_counts`, `stock_by_location`). **Why simple:** dashboards
borrow truth; the statuses do the work.

### 2. `cloth/` — `cloth-dashboard`
GET → `ClothDashboardView`. The cloth-centric board (financial columns
visible per FINANCIAL_ROLES walls). Same derived-only law.

## The roll story

### 3. `rolls/` — `roll-list`
GET → `RollListView`. The registry: status, type/color, location, Adda
binding. Pickers elsewhere read `active`; audits read all.

### 4. `rolls/bulk-add/` — `roll-bulk-create` 🔐
**Purpose:** intake — cloth arrives in batches, so creation is bulk-first.
POST → `RollBulkCreateView` (SA-only — MGT-A) → `roll_service.bulk_create_rolls`
[@atomic: N rolls + auto `roll_id`s via `_next_roll_id`].
**Reservation note:** intake does NOT assign — the coat is shelved, not
handed out. **Failure modes:** validation per row; id generation serialized.

### 5. `rolls/<pk>/` — `roll-detail`
GET → `RollDetailView`. One roll's life: identity, weights, financials
(role-gated), binding, history link (tracking's timeline).

### 6. `rolls/<pk>/edit/` — `roll-edit`
GET+POST → `RollUpdateView` → `update_roll_details`. **The wall in action:**
financial fields are form-STRIPPED for non-financial roles AND re-gated in
the service (certified OFF-C) — edit ≠ full edit for everyone.

### 7. `rolls/<pk>/damage/` — `roll-damage` ⭐ (the honesty verb)
POST → `RollDamageView`. Marks DAMAGED with an audited reason —
**available stock shrinks honestly.** The models.py comment is the spec:
every picker, guard, and count respects the status; partial damage stays
an audited weight correction. **Lesson:** negative inventory events get
first-class states, or counts rot.

### 8. `rolls/<pk>/assign/` — `roll-assign` ⭐⭐ THE RESERVATION
POST → `RollAssignView` → `roll_service.assign_roll_to_adda(user, roll,
adda, weight_kg, width_inch)`.
**Guards (memorize — this is the app's lesson):** roll must be `NOT_USED`
(one roll → one Adda, state-based idempotency: a second assign REFUSES) ·
Adda must be IN ITS LAYERING STAGE (the reservation window is a process
window, not a calendar) · weight verified at THIS moment (the number that
matters is the number at hand-out).
```
Journey: POST → view (mgmt gate) → assign_roll_to_adda
[@atomic: status guard → stage-window guard → bind roll.adda → verified
weight/width recorded → history event] → back to layering workspace
```
**Failure modes (each teaches):** already-used ("re-assign nahi") ·
wrong stage ("Rolls can only be assigned during the Layering stage") .
**Engineering Decision.** *Problem:* stock must never double-book.
*Options:* (A) a `reserved_by` nullable FK anyone can write; (B) an M2M
"bookings" table; (C) a status FSM + single service verb + process-window
guard. *Chosen:* C — the invariant lives in ONE transition. *Trade-off:*
advance BOOKING needs a new state (see README REQ #1) — accepted until the
business asks. *Still today?* Yes — zero double-assignments on record.

## Masters — three families, one pattern (each route individual)

*Shared teaching (once): archive-first CRUD — `is_active` flips, `active`
manager pickers, PROTECT on referenced rows; delete exists only for
never-used rows. [orm-and-managers](../../concepts/django/orm-and-managers.md).*

### 9. `cloth-types/` — `cloth-type-list`
GET → `ClothTypeListView`. The fabric-kind master.
### 10. `cloth-types/add/` — `cloth-type-create`
GET+POST → `ClothTypeCreateView` → `master_service`.
### 11. `cloth-types/<pk>/edit/` — `cloth-type-update`
GET+POST → rename ripples (referenced, not copied).
### 12. `cloth-types/<pk>/archive/` — `cloth-type-archive`
POST → soft-retire; pickers lose it, history keeps it.
### 13. `cloth-types/<pk>/delete/` — `cloth-type-delete`
POST → only if unreferenced (PROTECT refuses otherwise — learn from the refusal).

### 14. `cloth-colors/` — `cloth-color-list`
GET → color master list.
### 15. `cloth-colors/add/` — `cloth-color-create`
GET+POST → new color → available to rolls AND downstream breakups.
### 16. `cloth-colors/<pk>/edit/` — `cloth-color-update`
GET+POST → rename-with-care: colors key production breakups.
### 17. `cloth-colors/<pk>/archive/` — `cloth-color-archive`
POST → soft-retire.
### 18. `cloth-colors/<pk>/delete/` — `cloth-color-delete`
POST → PROTECT-guarded.

### 19. `storage-locations/` — `storage-list`
GET → where rolls physically live.
### 20. `storage-locations/add/` — `storage-create`
GET+POST → new rack/room.
### 21. `storage-locations/<pk>/edit/` — `storage-update`
GET+POST → relabel.
### 22. `storage-locations/<pk>/archive/` — `storage-archive`
POST → soft-retire (rolls keep their history location).
### 23. `storage-locations/<pk>/delete/` — `storage-delete`
POST → PROTECT-guarded.

## Learning Graph (this page)

**Before:** README Mental Model. **After:** [services.md](services.md)
(the reservation brain) → [production Part 3](../production/urls-layering-pattern.md)
(attach-roll consumes §8's work).
