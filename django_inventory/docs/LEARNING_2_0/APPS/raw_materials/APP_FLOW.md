---
id: l2-apps-raw-materials-app-flow
type: topic-canonical
status: active
owner: handwritten
scope: raw_materials
anchors: config/raw_materials/
verified: 2026-07-13
---

# raw_materials — business flows (APP_FLOW)

## TL;DR (1 min)
APP_FLOW: the business flows of this app (what happens, in order).

> Cloth stock — factory ka input side.
## Flow 1 — Intake: BulkRollForm → ClothRoll rows (CR-seq global, status=not_used,
cost_per_kg optional [PURCHASE fact, honest-NULL]). Price fields = financial roles only.
## Flow 2 — Assign: roll → Adda at the LAYERING stage (weight required); status=used.
One roll → one Adda forever.
## Flow 3 — Leftover: at layering complete, per-roll leftover weigh-in MANDATORY →
RemainingCloth row. Reuse in another Adda = consume_leftover (sole writer, C-1).
## Flow 4 — Masters: cloth types/colors/locations — soft-deactivate, never delete.

---
*Depth: [config/raw_materials/README.md](../../../../config/raw_materials/README.md) (business) ·
[docs/apps/raw_materials/GUIDE.md](../../../apps/raw_materials/GUIDE.md) (file-by-file). This = navigation/flow only.*
