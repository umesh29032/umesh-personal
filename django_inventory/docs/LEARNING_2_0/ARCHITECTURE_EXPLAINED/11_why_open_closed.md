---
id: l2-architecture-explained-11-why-open-closed
type: topic-canonical
status: active
owner: handwritten
scope: learning — architecture rationale
anchors: —
verified: 2026-07-13
---

# Why the stage engine is open-closed

**Problem:** Har naya production stage (Layering, Cutting, future Overlock/
Packing) agar worker-report UI + services me if/else daale, to code har stage
pe touch hota — bugs + duplication.

**Solution:** OPEN-CLOSED stage engine. `StageHandler` ek contract deta hai
(typed record, complete validations, `cost_quantity`, `contribution_schema`).
Har stage = apna package (handler + service), registry me register. Worker
report form schema se RENDER hota hai — koi stage-name if/else nahi.

**Kyun:** naya stage add karna = naya package likho, baaki kuch mat chhuo
(open for extension, closed for modification). Tracking Mode (TM) + future
barcode bhi isi seam se aate hain (C-TM: sab capture paths ek chokepoint me).

**Agar na ho:** har stage addition = core files me churn, regression risk, aur
"naya stage" har baar ek mini-rewrite ban jaaye.

R1 Stage Contract · [worker_reporting journey](../REQUEST_JOURNEYS/worker_reporting.md).
