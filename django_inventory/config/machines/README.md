---
id: app-machines-readme
type: app-readme
status: active
owner: handwritten
scope: machines
anchors: config/machines/
verified: 2026-07-13
---

# machines app — physical assets + operator possession (R10-A)

**Frozen architecture:** [docs/R10_MACHINE_STAGES_ARCHITECTURE_2026_07_05.md](../../docs/R10_MACHINE_STAGES_ARCHITECTURE_2026_07_05.md)
(owner rules 1-12). Machines are ASSETS ONLY (rule 6): they never own
workflow, costing, reporting, verification or settlement. Stage-domain
metadata (MachineType, StageCategory, Stage.work_type/machine_type/category)
lives in PRODUCTION beside the Stage library — this app points DOWN at it
(string FKs). Import rule (as shipped): NO model/module-level imports from
production→machines; exactly three sanctioned function-level lazy reads exist
(worker_task_service machine_code stamp · generic handler/views_ctx machine
chip) — codified in config/.importlinter; the ops-dashboard tile stays a
template tag from here.

| Piece | What |
|---|---|
| `models.Machine` | physical instance (code F1-immutable once assigned, name, type→production.MachineType, status enum active/inactive/maintenance, notes). Status = the ONE truth (no second boolean) |
| `models.MachineAssignment` | possession window: machine+worker+adda?+start_at/end_at (DateTime — same-day sharing = sequential windows; utilization = future pure reads). ONE open holder per machine (partial unique), append-only (release = end-date) |
| `services/machine_service.py` | ★ SOLE writer of both tables (+ `create_machine_type` — the one explicit downward config-master write). create/update (code guard)/assign (names current holder on refusal; race backstop)/release/counts. **MGT-F-1 fix 2026-07-12:** `update_machine` code-immutability guard compares against the DB row, not `machine.code` — a bound `ModelForm(instance=machine)` mutates the in-memory instance during `is_valid()`, which made the old comparison new-vs-new and silently skipped the guard (edit form could rename a code with assignment history) |
| `views.py` | parse→gate→delegate; management-only register (counts strip + mobile summary cards + inline assign/release), create/edit form-shell w/ inline "new Machine Type" |
| `templatetags/machines_tags.py` | `{% machines_ops_tile user %}` — the Operations digest tile (mgmt-gated, graceful-degrade) |
| `tests/test_r10a.py` | 17 pins: seeds/defaults/pair-constraint/type-reuse/category-fence guard/service lifecycle/same-day windows/views/perms/money-isolation grep + 2 MGT-F-1 pins (edit-form code rename refused with history / allowed without) |

Worker picker on assign = active production-role users (machines are NOT
stages — deliberately not `eligible_stage_workers`). Zero ₹ anywhere
(grep-pinned); future MachineRate/maintenance/utilization = additive per the
frozen doc's extension points.
