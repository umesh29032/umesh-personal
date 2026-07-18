---
id: apps-raw-materials-guide
type: app-guide
status: active
owner: handwritten
scope: raw_materials
anchors: config/raw_materials/
verified: 2026-07-13
---

# raw_materials app — file-by-file GUIDE (cloth stock)

> Business view: [config/raw_materials/README.md](../../../config/raw_materials/README.md).

| File | What |
|---|---|
| `models.py` | ClothType/Color · StorageLocation · ★ ClothRoll (CR-seq global, cost_per_kg=PURCHASE fact ADR-0009, adda one-way bind) |
| `services/roll_service.py` | ★ bulk intake · update (history-logged) · assign_roll_to_adda (layering-only) · consume_leftover (C-1 sole writer) · **G-1/G-2 (BOD-C 2026-07-18, owner-gated): `stock_status_counts` + `stock_by_location` — the cloth-dashboard reads extracted VERBATIM (one calculation, two consumers: the page + the BOD materials tiles); INERT proven in `tests/test_stock_reads.py`** · **RMX-C (Phase 17, 2026-07-18): `material_purchases_in_period` — purchases-in-period at PURCHASE price (ONE aggregate; honest-NULL counted never ₹0; damaged included+counted per owner ruling)** |
| `services/master_service.py` | masters CRUD (soft-deactivate) — writes MANAGEMENT-only (Phase-E cert 2026-07-12; was production-roles name-trap) |
| `views/` | dashboards · roll_views (list/bulk/detail) · master_views (lists=ProductionRole, writes=ManagementRole since Phase-E; `_MasterDeleteView.get_context_data` fix MGT-E 2026-07-12 = backlog #5 delete-confirm 500) · assign_views · mixins |
| `forms/roll_forms.py` | intake (price fields role-popped — defence in form layer) |
| `urls.py` | header route map |

Dots: intake → rolls; layering (production) binds+weighs; leftovers mandatory;
G1 baad me inhi facts ko value karega.

## Topics yahan use hote hain — kahan padhein
Har concept ka official link + "is project me kahan" mapping:
[../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
App ka business-view: README (code ke saath). Deep lessons: [docs/LEARNING/](../../LEARNING/README.md).
