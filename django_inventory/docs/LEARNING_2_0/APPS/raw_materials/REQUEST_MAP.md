---
id: l2-apps-raw-materials-request-map
type: topic-canonical
status: active
owner: handwritten
scope: raw_materials
anchors: config/raw_materials/
verified: 2026-07-13
---

# raw_materials — REQUEST_MAP (`/raw-materials/`)

## TL;DR (1 min)
REQUEST_MAP: this app URL-to-View-to-Service-to-Model table.

| URL | View | Service | Writes |
|---|---|---|---|
| dashboard, cloth-dashboard | dashboards | roll_service (reads) | none |
| roll-list/bulk-create/detail/edit | Roll* | roll_service.bulk_create_rolls/update_roll_details | ClothRoll (+history) |
| roll-assign | RollAssignView | roll_service.assign_roll_to_adda | ClothRoll.adda, status |
| cloth-type/color/* | masters CRUD | master_service | ClothType/Color/Location |
Gate: management for writes; price fields popped for non-financial roles.

---
*Depth: [config/raw_materials/README.md](../../../../config/raw_materials/README.md) (business) ·
[docs/apps/raw_materials/GUIDE.md](../../../apps/raw_materials/GUIDE.md) (file-by-file). This = navigation/flow only.*
