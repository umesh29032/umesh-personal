---
id: l2-apps-storefront-request-map
type: topic-canonical
status: active
owner: handwritten
scope: storefront
anchors: config/storefront/
verified: 2026-07-13
---

# storefront — REQUEST_MAP (`/`, `/storefront/`)

## TL;DR (1 min)
REQUEST_MAP: this app URL-to-View-to-Service-to-Model table.

| URL | View | Gate | Writes |
|---|---|---|---|
| / (public_home) | public_views | public | none (reads config rows) |
| /storefront/* | listing_views | listing_team | HomePageConfig/Featured/Category/cards |
Services: master_service (CRUD), image_service (croppable uploads).

---
*Depth: [config/storefront/README.md](../../../../config/storefront/README.md) (business) ·
[docs/apps/storefront/GUIDE.md](../../../apps/storefront/GUIDE.md) (file-by-file). This = navigation/flow only.*
