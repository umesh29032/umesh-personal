# storefront app — file-by-file GUIDE (public site; commerce future home)

> Business view: [config/storefront/README.md](../../../config/storefront/README.md).

| File | What |
|---|---|
| `models.py` | display-config rows (HomePageConfig, FeaturedProduct FREE-TEXT — G6 SKU hi link banayega, Category, cards/links) |
| `services/master_service.py` + `image_service.py` | listing CRUD + croppable image pipeline |
| `views/public_views.py` | no-auth homepage composition (ADR-0008 face) |
| `views/listing_views.py` | listing_team editor |
| `processors.py` · `widgets.py` · `forms.py` | image widget machinery |
| `urls.py` | / public + /storefront/ editor |

LAW (ADR-0008/0010 §5): production se koi paisa/quantity yahan nahi; Order→Adda
FK kabhi nahi — G6→G5→G2 raasta locked.

## Topics yahan use hote hain — kahan padhein
Har concept ka official link + "is project me kahan" mapping:
[../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
App ka business-view: README (code ke saath). Deep lessons: [docs/LEARNING/](../../LEARNING/README.md).
