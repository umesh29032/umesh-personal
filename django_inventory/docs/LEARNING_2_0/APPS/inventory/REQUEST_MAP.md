---
id: l2-apps-inventory-request-map
type: topic-canonical
status: active
owner: handwritten
scope: inventory
anchors: config/inventory/
verified: 2026-07-13
---

# inventory — REQUEST_MAP (`/inventory/` + `/tracking/`)

## TL;DR (1 min)
REQUEST_MAP: this app URL-to-View-to-Service-to-Model table.

| URL group | View | Gate | Notes |
|---|---|---|---|
| dashboard | dashboard.py | all (role-aware) | home |
| access-control / role / sidebar-access | access_hub/role/sidebar views | super-admin | RBAC hub |
| /tracking/ barcode dashboard/export/history | tracking_*.py | role | P4.2: inventory owns these |
Writes: role/sidebar edits call accounts services. No own model writes.

---
*Depth: [config/inventory/README.md](../../../../config/inventory/README.md) (business) ·
[docs/apps/inventory/GUIDE.md](../../../apps/inventory/GUIDE.md) (file-by-file). This = navigation/flow only.*
