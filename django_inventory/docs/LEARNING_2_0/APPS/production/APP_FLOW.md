---
id: l2-apps-production-app-flow
type: topic-canonical
status: active
owner: handwritten
scope: production
anchors: config/production/
verified: 2026-07-13
---

# production — business flows (APP_FLOW)

## TL;DR (1 min)
APP_FLOW: the business flows of this app (what happens, in order).

> Junior: yeh app factory ka "kaam" sambhalta hai. Ek Adda (ek product ka ek
> batch) stages se guzarta hai; workers report karte hain; cost freeze hota hai.

## Flow 1 — Adda banao aur chalao
```
Owner: product chuno → Adda banta hai (code auto: 3-PATTI-003)
 → har WorkflowStage ka ek AddaStageRecord ban jaata hai (us product ke flow se)
 → Adda.status = in_progress, current_stage = pehla stage
```
Stages (per-product flow editor me set hote hain): Layering → Cutting-Pattern →
Cutting → Barcode-Gen.

## Flow 2 — Ek stage chalana (har stage ka pattern same)
```
manager workers assign karta hai (set_stage_workers — roster)
 → worker apne phone pe report karta hai (color/size/qty)
 → submit → expected_rate/earning FREEZE (sirf dikhane ko, paisa NAHI)
 → master/manager "Mark Complete" → stage band, Adda agle stage pe
```
Stage complete pe jo workers ne report nahi kiya unke task auto-cancel (F3) —
"Mark Complete" pehle unke naam dikha ke warning deta hai (P2).

## Flow 3 — Cost freeze
Stage advance pe `cost_service` us stage ka `processing_cost` freeze karta hai
(standard cost; unpriced = NULL, kabhi 0 nahi). Yeh worker EARNING se ALAG
cheez hai (ADR-0009 — kabhi add mat karna).

## Flow 4 — Reopen (galti sudhaar)
Stage reopen ho sakta hai JAB TAK paisa na bana ho. Settle ho chuka stage
reopen REFUSE karta hai (ADST ka naam le ke) — pehle settlement reverse karo.

## What this app does NOT do
Paisa (expense app), barcode identity (tracking), cloth stock (raw_materials).
Yeh sirf "kaam ka sach" banata hai.

---
*Canonical depth (don't duplicate — read these):* business view →
[config/production/README.md](../../../../config/production/README.md) · file-by-file dev
view → [docs/apps/production/GUIDE.md](../../../apps/production/GUIDE.md) · this folder =
the NAVIGATION + FLOW layer only.*
