---
id: r10-execution-plan
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# R10 — Machines (minimal) · Execution Plan (REVISED v2)

> **⚠️ SUPERSEDED IN PART (2026-07-05): the owner redefined machines as the
> foundation of machine-based production stages. The governing design is now
> [R10_MACHINE_STAGES_ARCHITECTURE_2026_07_05.md](R10_MACHINE_STAGES_ARCHITECTURE_2026_07_05.md)
> — this v2 plan survives as its R10-A asset layer (plus MachineType +
> Stage.machine_type). Owner approved; shipped 2026-07-05.**

> **STATUS: ✅ IMPLEMENTED as R10-A 2026-07-05 (gate 842/848; receipt in R10_MACHINE_STAGES_ARCHITECTURE).**
> PDD §25 (frozen scope): `Machine(code, name, status[active|inactive|
> maintenance], notes)` + `MachineAssignment(machine, worker, adda?, from/to)`
> + admin dashboard counts. **No maintenance scheduling, no utilization math
> (YAGNI).** First phase built ON the LOCKED operational foundation
> (2026-07-05) — additive only, zero changes to frozen modules' behavior.
>
> **v2 (owner-ordered scalability review, 2026-07-05):** §0 below answers the
> six long-term questions. ONE schema change vs v1: `from/to` become
> **DateTimeFields** (a Date can't express two workers sharing one machine in
> a day, and the window IS the future utilization primitive). Everything else
> confirmed; extension points now documented explicitly.

## 0) Long-term scalability review (owner's six questions)

### 0.1 MachineAssignment vs WorkerStageTask — same IDIOM, different CONCEPT
They must NOT share a table/base class: WST models a **work lifecycle**
(assigned→in_progress→completed→verified, carries contributions and the
expected-earning freeze); MachineAssignment models **possession over a time
window** (who holds a resource, from when to when). Forcing possession into a
status machine (or work into windows) would fake one of them. What they DO
share — deliberately, the house assignment idiom:

| Architectural idea | WST | MachineAssignment |
|---|---|---|
| single writer service | `worker_task_service` | `machine_service` |
| ≤1 active per subject | partial unique (sr,worker) active | partial unique (machine) where `to IS NULL` |
| never delete history | CANCELLED status | end-dated row (`to` set) |
| PROTECT FKs, append-only | ✓ | ✓ |
| actionable refusals | names blocker | names current holder |
| audit trail | status+timestamps (+AddaHistory events) | window rows ARE the trail; optional AddaHistory `MACHINE_ASSIGNED` event type later = additive |

### 0.2 Future machine costing — NO in R10, extension points documented
Machines stay OUTSIDE ADR-0009 costing in v1 (zero ₹ fields, zero
expense/settlement imports — grep-pinned). When costing/utilization comes:
- **Utilization = pure reads over existing data**: Σ(`to`−`from`) per machine
  / per Adda / per worker — the DateTime window (v2 change) is the complete
  primitive; NO schema change needed, ever, for utilization math.
- **Machine rates** = a separate additive table (`MachineRate`, the
  WorkflowStageRoleRate pattern) + its own ADR — NEVER ₹ columns on Machine.
- **Machine running cost** = factory-level expense first (the ADR-0011
  pattern: never silently per-Adda); any per-Adda allocation = its own
  owner-gated phase with a written allocation rule.
- Status enum is extensible (TextChoices) — e.g. `retired` later = additive.

### 0.3 Adda relationship — all four scenarios, no redesign
| Scenario | How the v2 schema handles it |
|---|---|
| Worker moves between Addas | release (end-date) → assign new window with the new `adda` (or NULL). Append-only windows = the movement history for free |
| Machine shared during a day | **DateTime windows** (the v2 change): sequential same-day windows; the one-OPEN-per-machine constraint still guarantees a single holder at a time. If true CONCURRENT sharing is ever wanted, the relaxation is dropping one partial-unique index — additive migration, no redesign |
| Machine permanently with a worker | `to=NULL, adda=NULL` — natural |
| Machine assigned to an Adda without a worker | PDD §25 pins `worker` required, so v1 keeps it required. The relaxation is ONE additive migration (`worker` nullable + CheckConstraint "worker OR adda NOT NULL") — documented here so it's a decision, never a redesign. Owner may also choose to include it in v1 (supersets PDD §25) |

### 0.4 Dashboard integration — v1 minimum + the documented future map
Machines is NOT an isolated page: the list IS the register, and machine facts
surface where each audience already looks. v1 builds only the PDD minimum;
the rest is mapped (each = a small additive read, no redesign):

| Surface | v1 (build) | Future (documented, owner-gated) |
|---|---|---|
| Operations dashboard | ✅ counts tile (template tag; mgmt-gated) | stays THE factory-pulse entry |
| Machines list | ✅ counts strip + holder chips | — |
| A360 (per Adda) | — | "Machines on this Adda" collapsed `<details>` row from the `adda` FK (read-only, mgmt) |
| Worker dashboard | — | "My machine" chip from the worker's open window (minimum-info, no ₹) |
| My Dashboard/personal admin | — | nothing (machines = ops, not personal) |

### 0.5 Mobile usability — one business question per section
- **List (the register):** question *"which machines exist and who holds
  them?"* — summary cards, ONE line each: `MC-001 · Overlock #1 · 🟢 active ·
  👤 utest`; tap to expand → notes, current window, actions. No horizontal
  table on phones; counts strip = 4 chips (total/active/maintenance/assigned).
- **Assign/release panel:** question *"is it free, and to whom does it go?"*
  — current holder named first; worker chips + optional Adda + FancyDate;
  release = one tap + confirm.
- **Create/edit:** form-shell (hero + numbered panels + cream inputs + sticky
  CTA), 4 fields only.
- 390×844 no-overflow is an E2E acceptance step, not polish.

### 0.6 Architectural-debt verdict — ZERO redesign-class items
The review found exactly one would-have-been debt: **DateFields** (fixed in
v2 → DateTime). Remaining consciously-documented relaxation points, each a
single additive migration, never a redesign: worker-nullable (0.3), dropping
one index for concurrent sharing (0.3), MachineHistory/AddaHistory events
(0.1), MachineRate (0.2). Layering is enforced (machines top-layer;
production can never import it), money isolation is grep-pinned, and no
parallel flows exist — every write goes through one new service.

## 1) Architecture audit — what exists today

- **Live code: NOTHING.** No `Machine`/`MachineAssignment` model, service,
  view, URL, or template exists in the current tree (full grep census).
- **Dead ancestor:** the Batch-era `inventory.Machine` +
  `BatchStageMachineAssignment` (inventory migration 0009) were **dropped in
  migration 0012** with the whole Batch architecture. Nothing to reuse or
  migrate; no table-name clash (tables gone; new app uses `machines_*` names
  anyway). One lesson taken: the ancestor hung assignments off BatchStage +
  Skill — v2 deliberately hangs them off **worker + optional Adda** per PDD
  §25 (machines follow people and batches, not stages).
- **PDD placement:** §31 validation table pins "Machines … = **additive
  apps**; none forces redesign" — a NEW app, not a production module.

## 2) Reuse analysis — everything rides the frozen architecture

| Concern | Reused mechanism (no new parallel flow) |
|---|---|
| Base models | `core.TimeStampedModel`; status = explicit enum per PDD (no bool duplication — WP-B lesson); `.active` manager pattern for status=active |
| Writes | **service layer owns all writes** — `machines/services/machine_service.py` = the SOLE writer of both tables (create/update/retire machine; `assign`/`release` for assignments). Views parse→gate→delegate |
| History | assignments are END-DATED (`to_date` set), never deleted — the append-only work-history principle |
| Permissions | role lens ONLY: `user_has_role(MANAGEMENT_ROLES)` via the existing mixin pattern; NO new predicate. Sidebar item enters the SIDEBAR registry → owner can govern it via Sidebar Access hub like every other item (menu-hidden ⇒ URL-blocked middleware already applies) |
| Worker picker | active users with a production role (machines are not stages — `eligible_stage_workers` is deliberately NOT used; documented in-service why) shown with the existing `_WorkerCheckboxes` chip widget + FancySelect |
| Adda picker | in-progress Addas (optional FK, PDD `adda?`) |
| UI | form-shell pattern (hero + numbered panels + cream inputs + sticky CTA), UI_COMPONENTS vocabulary, DataTables-free simple list → **mobile-first cards** (summary-first: one line per machine = status chip + assignee; details on expand) |
| Dashboard counts | PDD "admin dashboard counts" = ①) count strip on the Machines list page (total / active / maintenance / assigned-now) + ②) ONE tile on Operations via a **`machines` template tag included in `adda_dashboard.html`** — template-level include keeps the python import direction clean (machines imports production for the Adda FK ⇒ machines sits ABOVE production; production must never import machines). Tag is management-gated + graceful-degrade (same posture as the R5 expense digest) |
| Docs | new `config/machines/README.md` + `docs/apps/machines/GUIDE.md` + GLOSSARY entry + roadmap/receipt — DOCS-SYNC same session |

**Fit check against the 6 permanent rules:** rosters untouched · visibility
via existing role/sidebar machinery · ZERO money surface (no rates, no cost,
no settlement contact — machines never enter ADR-0009 costing in v1) ·
snapshots untouched · mobile-first summary cards · additive app, no parallel
flow. Frozen modules edited: **one template include line** in
`adda_dashboard.html` + `INSTALLED_APPS`/root urls registration — no behavior
change to any foundation module.

## 3) Design (minimal, PDD-exact)

```python
# machines/models.py
class Machine(TimeStampedModel):
    code   = CharField(unique=True)          # e.g. MC-001; IMMUTABLE once assigned (F1-style guard in clean())
    name   = CharField()
    status = CharField(choices=ACTIVE|INACTIVE|MAINTENANCE, default=ACTIVE)
    notes  = TextField(blank=True)

class MachineAssignment(TimeStampedModel):
    machine    = FK(Machine, PROTECT, related_name='assignments')
    worker     = FK(AUTH_USER_MODEL, PROTECT, related_name='machine_assignments')
    adda       = FK(production.Adda, PROTECT, null=True, blank=True)
    # v2: DateTime, not Date — same-day sharing = sequential windows, and the
    # window is the future utilization primitive (§0.2/§0.3). UI shows dates.
    start_at   = DateTimeField(default=now)
    end_at     = DateTimeField(null=True, blank=True)   # NULL = currently assigned
```

DB constraints (all in the initial migration):
- `unique` Machine.code
- **one OPEN assignment per machine**: partial unique on `machine` where
  `end_at IS NULL` (mirrors the ≤1-active-task pattern)
- `CheckConstraint`: `end_at IS NULL OR end_at >= start_at`
- status ∈ enum (choices + CheckConstraint, DB-integrity-PR1 style)

Service API (sole writer): `create_machine` · `update_machine` (code
immutable once assigned) · `set_status` · `assign(machine, worker, adda=None,
start_at=now)` (refuses if an open assignment exists → actionable error
naming the current holder; release-first) · `release(assignment, end_at=now)`.
Every write logs to logger (no history table in v1 — end-dated rows ARE the
history; a `MachineHistory` table would be YAGNI against §25).

Pages (management-only, `/machines/`):
- **List** — count strip (total/active/maintenance/assigned-now) + card/table
  rows: code · name · status chip · current worker (+Adda) · quick actions.
  Mobile: stacked cards, one machine = one summary line, expand for detail.
- **Create / Edit** — form-shell; status via FancySelect.
- **Assign / Release** — small panel on the machine row/detail: worker picker
  (chips), optional Adda, from-date (data-fancy-date); release = one tap +
  confirm. No separate "assignment admin" page (minimal).

## 4) Migrations

ONE new-app initial migration (`machines/0001_initial.py`) — two tables +
constraints above. No changes to any existing table. Reversible trivially
(drop app tables). No data migration (nothing to backfill).

## 5) Tests (target ≈ +18)

- Service: create/duplicate-code refusal/code-immutable-after-assign/
  set_status/assign/second-open-assign refused (names holder)/release/
  re-assign after release/adda-optional/window constraint (end≥start)/
  same-day sequential windows (DateTime — the §0.3 sharing scenario).
- Views: management 200s; worker 403 on every `/machines/` URL (mixin);
  sidebar item visible to management, absent for worker (registry fallback
  predicate); list counts correct.
- Ops tile: renders for management, absent for workers, graceful when app
  data empty.
- Single-writer discipline: greps stay clean (no model writes outside
  machine_service) — add machines to the gate-4-style census ONLY as a
  comment (no new CI gate in v1; service is trivially auditable).
- Golden + full gate: must stay byte-identical / green (zero money contact).

## 6) Browser E2E (REAL flow, dev server)

1. umesh (super admin): sidebar shows "Machines" → create MC-001 "Overlock #1"
   (form-shell, FancySelect status).
2. Assign utest to MC-001 against 3-PATTI-011 → list shows assignee chip;
   assigned-now count = 1; second-assign attempt refused with actionable
   message.
3. Operations dashboard: machines tile shows counts + links to list.
4. Release → counts update; assignment history row end-dated (visible on
   machine detail).
5. dev.manager: full machines access (management) ✓.
6. utest (worker): `/machines/` → 403; no sidebar item; dashboard unchanged.
7. Mobile 390×844: list = summary cards, no horizontal overflow; create form
   usable (sticky CTA).
8. Set MC-001 status=maintenance → status chip + counts update.

## 7) Risks

| Risk | Mitigation |
|---|---|
| New-app wiring (INSTALLED_APPS, urls, sidebar) breaks smoke | page-smoke test extended to machines URLs; sidebar registry fallback predicate = management until owner seeds a rule |
| Layering violation (production importing machines) | forbidden by design — ops tile via machines template tag only; import-linter layers updated 2026-07-06 (freeze package): `machines` in root_packages + top layer, with the 3 sanctioned lazy reads codified as ignore_imports |
| Open-assignment race (two managers assign same machine) | partial-unique index = DB backstop; service catches IntegrityError → friendly error |
| Scope creep (maintenance schedules, utilization, QR codes) | plan pins §25 YAGNI line; anything more = new owner-gated phase |
| Frozen-module drift | only additive touches: 1 template include + registrations; no foundation file logic edited |

## 8) Acceptance criteria

- PDD §25 delivered exactly: both models + statuses + optional Adda + admin
  counts; nothing more. §0 review honored: DateTime windows, extension
  points documented in-code (model docstrings cite §0.2/§0.3), no ₹ fields.
- Full gate PASS (≈845 expected) · golden byte-identical · foundation-purity
  + layering contracts green with `machines` added to the layer map.
- All 8 E2E steps proven in a real browser incl. 390px mobile.
- Zero money-pipeline contact (no expense/settlement/rate imports anywhere in
  the app — grep-pinned in a test).
- Docs same session: README + GUIDE + GLOSSARY + roadmap row → receipt +
  DOCUMENTATION_INDEX; PDD body untouched (no amendment needed — §25 built
  as written).
- Tree stays uncommitted (checkpoint policy).

## 9) Implementation order + estimate

| Step | Work | Est |
|---|---|---|
| M1 | app skeleton + models + constraints + migration + INSTALLED_APPS/urls | ~45m |
| M2 | machine_service + service tests | ~45m |
| M3 | views/urls/templates (list+form+assign/release) — mobile-first | ~1.5h |
| M4 | sidebar entry + ops-dashboard template tag + tile | ~30m |
| M5 | view/perm/smoke tests + full gate | ~45m |
| M6 | browser E2E (8 steps) + docs sync + receipt | ~45m |

Total ≈ 5h. Non-goals (explicit): maintenance scheduling · utilization math ·
worker-facing machine surfaces · A360 machine panel · barcode/QR on machines ·
machine costing (ADR-0009 untouched) · CI single-writer gate for machines.
Each returns only as its own owner-gated phase.

### Verification sources
PDD §25/§31 (2026-07-04) · roadmap R10 section · full-tree Machine grep census
2026-07-05 (live: none; ancestor dropped in inventory 0012) ·
operations_digest.py:53 (tile seam) · frozen-foundation rules memory.
