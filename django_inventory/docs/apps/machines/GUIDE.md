---
id: apps-machines-guide
type: app-guide
status: active
owner: handwritten
scope: machines
anchors: config/machines/
verified: 2026-07-13
---

# machines app — file-by-file GUIDE

> Business view: [config/machines/README.md](../../../config/machines/README.md) ·
> governing design: [R10_MACHINE_STAGES_ARCHITECTURE_2026_07_05.md](../../R10_MACHINE_STAGES_ARCHITECTURE_2026_07_05.md) 🔒

| File | What |
|---|---|
| `models.py` | Machine (asset; status enum = single truth) + MachineAssignment (possession windows; one OPEN per machine partial-unique; DateTime grain) |
| `services/machine_service.py` | ★ sole writer (+create_machine_type downward config write); actionable refusals name the current holder; `update_machine` code guard compares the DB row (MGT-F-1 fix — bound ModelForm mutates the instance before the guard) |
| `views.py` | mgmt-only register/list/create/edit/assign/release — parse→gate→delegate |
| `urls.py` | /machines/ + actions |
| `templatetags/machines_tags.py` | ops-dashboard tile (no module-level production→machines imports; 3 sanctioned lazy reads codified in .importlinter) |
| `templates/machines/` | machine_list (counts chips + summary cards, mobile-first) · machine_form (form-shell) · _ops_tile |
| `tests/test_r10a.py` | R10-A pins incl. category-fence + money-isolation greps |

**Worker-surface certification (V1.1 Phase F, 2026-07-12):** all 5 URLs
management-gated at dispatch (`_ManagementOnly`); worker 403 everywhere,
POSTs inert, ops tile double-gated; **0 bugs, 0 code changes** — evidence in
[WORKER_ROLE_CERTIFICATION.md](../../WORKER_ROLE_CERTIFICATION.md) Phase F.

**Management certification (MGT-F, 2026-07-12):** manager register/CRUD/assign/
release all functional; **1 bug FIXED (MGT-F-1)** — edit form could rename a
machine code WITH assignment history (F1-guard bypass via ModelForm instance
mutation); 2 pins added (17 total). Carry-over "assign accepts any user pk"
judged **INFO → DEPLOYMENT_BACKLOG #8** (picker filters UI to active
production-role users; server accepts any existing pk — no money/permission
consequence; non-int worker pk in a hand-crafted POST = 500). Evidence in
[MANAGEMENT_ROLE_CERTIFICATION.md](../../MANAGEMENT_ROLE_CERTIFICATION.md) MGT-F.
