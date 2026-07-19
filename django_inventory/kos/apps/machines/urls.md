---
id: app-machines-urls
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "All 5 machine URLs — registry, checkout, checkin — individually."
related: [app-machines]
---

# machines — URL Learning Pages (all 5, individually)

> 📂 [machines app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)
> Source: `config/machines/urls.py` (mounted at /machines/, all management-gated).

**Reading Strategy** — *Beginner:* §4 → §5 (the checkout/checkin pair IS
the app). *Senior:* §4's ED (why no scheduling yet).

### 1. `/machines/` — `list`
**Purpose:** the crib board — every unit, its type, status, CURRENT HOLDER.
**Method:** GET → `MachineListView` (`views.py:50`).
**Reads:** `machines_with_holder()` + `register_counts()` — holder DERIVED
from open windows (never a column). **Why simple:** the model did the work;
the board just looks.

### 2. `add/` — `add`
**Purpose:** register a unit (code-unique, type, status).
**Method:** GET+POST → `MachineCreateView` (:81) → `machine_service.create_machine`.
**Capability note:** you pick an EXISTING type — creating a KIND is
production's master lane (custody: types live beside requirements).
**Failure modes:** duplicate code (unique refuses).

### 3. `<pk>/edit/` — `edit`
**Purpose:** rename/retype/re-status a unit.
**Method:** GET+POST → `MachineUpdateView` (:110) → `update_machine`.
**Care:** retyping a unit that's the last free satisfier of a stage's
requirement = a visible constraint elsewhere (README REQ #1) — the edit is
easy; the CONSEQUENCE is capability math.

### 4. `<pk>/assign/` — `assign` ⭐ THE CHECKOUT
**Purpose:** hand THIS unit to a worker (optional Adda context), opening a
possession window.
**Method:** POST → `MachineAssignView` (:145) → `machine_service.assign(machine,
worker, adda=, start_at=)`.
```
Journey: POST → mgmt gate → assign [@atomic: unit ACTIVE? no OPEN window?
→ INSERT MachineAssignment(start, end=NULL)] → DB partial unique = the
race-proof one-holder law → back to the board
```
**Failure modes:** already held (the open window names the holder) ·
inactive unit. Concurrency: two simultaneous checkouts → the second hits
the partial unique — the DB referees ([feature §DSA](../../features/machines.md)).
**Engineering Decision.** *Problem:* track who holds shared tools.
*Options:* (A) `current_holder` FK (history dies per reassignment);
(B) full scheduling with future bookings (overlap guards, no-shows —
weight the floor didn't ask for); (C) open/closed windows, one-open-holder
by partial unique, availability derived. *Chosen:* C. *Trade-off:* no
advance booking — accepted until the business asks (the README REQ sketches
that project honestly). *Still today?* Yes — R10-A shipped exactly this and
the floor's question ("kiske paas hai?") is answered in one query.

### 5. `assignments/<pk>/release/` — `release` ⭐ THE CHECKIN
**Purpose:** close the window (end_at stamped).
**Method:** POST → `MachineReleaseView` (:165) → `machine_service.release`.
**Law:** release CLOSES, never deletes — the window becomes history
(who-held-it-last-Tuesday = interval stabbing on these rows).
**Failure modes:** already closed (idempotent-refusal with message).
**Why simple:** append-only citizenship makes checkin one honest UPDATE of
`end_at` on the open row — state machines don't need ceremonies when the
model is right.

## Learning Graph (this page)

**Before:** README Mental Model. **After:** [services.md](services.md) →
[production urls-core machine-types](../production/urls-core.md) (the
capability side).
