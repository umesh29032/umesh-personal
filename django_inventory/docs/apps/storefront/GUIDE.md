---
id: apps-storefront-guide
type: app-guide
status: active
owner: handwritten
scope: storefront
anchors: config/storefront/
verified: 2026-07-13
---

# storefront app — file-by-file GUIDE (public site; commerce future home)

> Business view: [config/storefront/README.md](../../../config/storefront/README.md).

| File | What |
|---|---|
| `models.py` | display-config rows (HomePageConfig, FeaturedProduct FREE-TEXT — G6 SKU hi link banayega, Category, cards/links) |
| `services/image_service.py` | croppable image pipeline — the ONE side-effecting write (old ListingService pass-through removed; single-row CRUD = CBV-owned) |
| `views/public_views.py` | no-auth homepage composition (ADR-0008 face) |
| `views/listing_views.py` | listing_team editor — all 8 CBVs gated by `LoginRequiredMixin + ListingTeamMixin` (= `STOREFRONT_ROLES`: super_admin + listing_team; managers/workers blocked) |
| `processors.py` · `widgets.py` · `forms.py` | image widget machinery |
| `urls.py` | / public + /storefront/ editor |

LAW (ADR-0008/0010 §5): production se koi paisa/quantity yahan nahi; Order→Adda
FK kabhi nahi — G6→G5→G2 raasta locked.

Worker-role certification: **Phase G CERTIFIED 2026-07-12, 0 bugs, 0 changes**
(shell 3-role matrix + browser + CSRF-POST inertia) —
[docs/WORKER_ROLE_CERTIFICATION.md](../../WORKER_ROLE_CERTIFICATION.md).

## Topics yahan use hote hain — kahan padhein
Har concept ka official link + "is project me kahan" mapping:
[../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
App ka business-view: README (code ke saath). Deep lessons: [docs/LEARNING/](../../LEARNING/README.md).
