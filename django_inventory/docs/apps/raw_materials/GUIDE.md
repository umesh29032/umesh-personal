# raw_materials app — file-by-file GUIDE (cloth stock)

> Business view: [config/raw_materials/README.md](../../../config/raw_materials/README.md).

| File | What |
|---|---|
| `models.py` | ClothType/Color · StorageLocation · ★ ClothRoll (CR-seq global, cost_per_kg=PURCHASE fact ADR-0009, adda one-way bind) |
| `services/roll_service.py` | ★ bulk intake · update (history-logged) · assign_roll_to_adda (layering-only) · consume_leftover (C-1 sole writer) |
| `services/master_service.py` | masters CRUD (soft-deactivate) |
| `views/` | dashboards · roll_views (list/bulk/detail) · master_views · assign_views · mixins |
| `forms/roll_forms.py` | intake (price fields role-popped — defence in form layer) |
| `urls.py` | header route map |

Dots: intake → rolls; layering (production) binds+weighs; leftovers mandatory;
G1 baad me inhi facts ko value karega.

## Topics yahan use hote hain — kahan padhein
Har concept ka official link + "is project me kahan" mapping:
[../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
App ka business-view: README (code ke saath). Deep lessons: [docs/LEARNING/](../../LEARNING/README.md).
