---
id: readme-flows
type: system
verified: 2026-07-19
---

# Flows — the system as stories

*(Part of the [KOS](../README.md).)*

## Why this folder exists — a teacher's note

Features explain PARTS; flows explain the MOVIE *(featurein kirdaar hain,
flow poori kahani)*. A flow follows one real thing — a worker's wage, a
roll of cloth, a settlement event, a single HTTP tap — end to end across
features, with every hand-off and every designed blocker visible. When
you can retell a flow from memory, you understand the SYSTEM; when you
can only list features, you understand files.

Flows are also your best DEBUGGING maps: production problems arrive as
broken stories ("worker ko paisa nahi dikha"), not as broken files — start
from the flow, find the failing hop, THEN open the feature page.

## The stories

| Flow | Follows | Read when |
|---|---|---|
| [worker-gets-paid.md](worker-gets-paid.md) | Meena's wage: report → verify → settle → cash | you want the money system in one sitting (start HERE) |
| [cloth-to-garment.md](cloth-to-garment.md) | one Adda: roll → layering → pattern → cutting → barcodes → done | you touch anything in production |
| [settlement-lifecycle.md](settlement-lifecycle.md) | the ADST event itself: draft → finalize → reverse/supersede | you touch settlement code or debug a correction |
| [request-through-stack.md](request-through-stack.md) | ONE phone tap through middleware→view→service→PG | you're new, or debugging ANY url ("universal debug recipe" inside) |

## How to use a flow

- Read it ONCE fully, then re-draw its diagram from memory *(yaad se
  banao — jo hop bhool gaye, wahi hop kal debug karna padega)*.
- Every hop names its feature page — depth is one click down, never
  duplicated here.
- Interview use: flows ARE your system-design answers — "walk me through
  your system" = retell worker-gets-paid + two-truths, 90 seconds.
