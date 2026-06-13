# raw_materials — FILE_MAP

## TL;DR (1 min)
FILE_MAP: every important file in this app and how they connect.

## models.py — **ClothType**, **ClothColor** (hex swatch), **StorageLocation**,
**ClothRoll** ★ (roll_id CR-seq global, type/color/location FKs, purchased_date,
`cost_per_kg` PURCHASE fact [nullable, honest-NULL], `adda` 1→1 bind, status).
(Leftover model **RemainingClothOfClothRoll** lives in production/models/layering.py.)
## services/ — `roll_service.py` ★ (bulk_create_rolls, update_roll_details
[history-logged], assign_roll_to_adda [layering-only guard], **consume_leftover**
[C-1 sole writer, row-locked]) · `master_service.py` (masters CRUD).
## views/ — dashboards, roll_views (list/bulk/detail/edit), master_views,
assign_views, mixins (RBAC). ## forms/ — roll_forms (price role-gated), master_forms.
## urls.py — route map header. admin.py — 4 admins.
## DB behaviour (junior): a roll row is SAVED at intake (INSERT, price maybe NULL);
UPDATED at assign (adda_id + status=used) and at layering completion
(denormalized leftover weight/length). cost_per_kg edits are history-logged so
past prices are reconstructable.

---
*Depth: [config/raw_materials/README.md](../../../../config/raw_materials/README.md) (business) ·
[docs/apps/raw_materials/GUIDE.md](../../../apps/raw_materials/GUIDE.md) (file-by-file). This = navigation/flow only.*
