---
id: app-production-urls
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Any of production's 80 URLs — jump to ITS OWN learning section in one click."
related: [app-production]
---

# production — URL Learning Index (all 80, each individually documented)

> 📂 [production app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)
> Source: `config/production/urls.py` (mounted `/production/`, 80 routes).
> LOS law: every URL has its OWN section — this index routes you there in
> one click. Four parts, learning order = pipeline order.

**Reading Strategy** — *Beginner:* README Mental Model → Part 2's
`adda-create` + `worker-report` → Part 4's `workspace-complete` (the mint).
*Intermediate:* Part 1 (flow editor!) → Part 2 fully → Part 3.
*Senior:* Part 2's generic `reopen`/`allocate` (the guard architecture) →
Part 4's reopen pair (permanence) → `stage-rate-correct` (corrections-until-boundary).

**Mental Model:** the factory pipeline (README) — Part 1 configures the
machines, Part 2 runs batches through them, Parts 3–4 are the four
original stations up close.

## Part 1 — [Dashboards · Products · Flow Editor · Libraries](urls-core.md) (26)

| Route | Section |
|---|---|
| `/production/` · `stalled/` · `pending-reports/` · `costing/` | [Dashboards ×4](urls-core.md) |
| `products/` · `add/` · `<pk>/edit/` · `<pk>/archive/` | [Product CRUD ×4 (SA)](urls-core.md) |
| `products/<pk>/flow/` ⭐ | [THE Flow Editor](urls-core.md) |
| `products/<pk>/sizes/` · `<pk>/patterns/` · `…/blueprint/` | [sizes + patterns_ai redirects ×3](urls-core.md) |
| `patterns/` · `add/` · `<pk>/edit/` · `<pk>/delete/` | [Component library ×4](urls-core.md) |
| `stages/` · `add/` · `<pk>/edit/` · `<pk>/delete/` | [Stage library ×4 (SA)](urls-core.md) |
| `stage-categories/…` ×3 · `machine-types/…` ×3 | [R10-C masters ×6](urls-core.md) |

## Part 2 — [Adda Lifecycle · Generic Set · Worker/Review](urls-adda.md) (17)

| Route | Section |
|---|---|
| `addas/` · `addas/start/` ⭐ · `addas/<code>/` | [list · create · detail](urls-adda.md) |
| `addas/<code>/bundles/create-sets/` · `lanes/add/` · `lanes/cancel/` | [GAP-4/5 lanes + sets](urls-adda.md) |
| `addas/<code>/stage-rates/` · `…/correct/` 🔐 | [S1.1 rate correction](urls-adda.md) |
| `addas/<code>/stage/<type>/` · `stage-advanced/` | [panel + bounce](urls-adda.md) |
| `…/stage/<type>/start\|complete⭐\|reopen🔐\|allocate\|alloc-void/` | [the R10-B generic five](urls-adda.md) |
| `addas/<code>/report/<type>/` ⭐ · `review-reports/` ⭐ | [worker phone + red pen](urls-adda.md) |

## Part 3 — [Layering + Pattern Design workspaces](urls-layering-pattern.md) (18)

| Route | Section |
|---|---|
| `layering/` + start · attach-roll · use-leftover · quick-create-roll · entries/<pk>/remove · complete⭐ · reopen🔐 | [Layering ×8](urls-layering-pattern.md) |
| `pattern/` + start · save · photos-add · photo-remove · verify · unverify · sizes · complete⭐ · reopen🔐 | [Pattern Design ×10](urls-layering-pattern.md) |

## Part 4 — [Cutting + Barcode-Gen workspaces](urls-cutting-barcode.md) (19)

| Route | Section |
|---|---|
| `cutting/` (legacy) · `workspace/` · start · breakup save/delete · bundle create/add-pieces/item-delete/delete · item-allocate/allocation-delete · draft · **workspace/complete ⭐⭐** · reopen🔐 | [Cutting ×14](urls-cutting-barcode.md) |
| `barcode-gen/` + start · generate⭐ · complete · reopen🔐 | [Barcode-Gen ×5](urls-cutting-barcode.md) |

## Learning Graph (this index)

**Before:** [README](README.md) (Mental Model + Misconceptions).
**After:** pick your part → then [views.md](views.md) → [services.md](services.md).

## Direct paths

`config/production/urls.py` · `config/production/views/` ·
`config/production/stages/<stage>/service.py` · `config/production/services/` ·
`config/production/models/` · `templates/production/` · `config/production/tests/`
