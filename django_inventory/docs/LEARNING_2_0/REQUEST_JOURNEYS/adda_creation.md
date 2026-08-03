---
id: l2-request-journeys-adda-creation
type: request-journey
status: active
owner: handwritten
scope: adda_creation (request-journey)
anchors: —
verified: 2026-07-13
---

# Journey: Adda Creation (one-click batch start)

> **TL;DR** — Owner picks a product; one POST → `adda_service.create_adda` opens
> the Adda (production batch) + one AddaStageRecord per WorkflowStage, race-safe
> auto code. No money, no work yet — just the batch shell. Operational call chain
> + debug + source files below.

**1. URL** — `/production/addas/start/` POST · name `production:adda-create`.
**2. View** — `production/views/adda_views.py` → `AddaCreateView` (management gate).
**3. Forms** — adda start form (`production/forms/adda_forms.py`): one field, product picker.
**4. Services** — `production/services/adda_service.py:create_adda(product, user)`.
**5. Models READ** — Product, WorkflowStage (the product's flow), last Adda code (for sequence).
**6. Models WRITTEN** — Adda (INSERT, `code` auto) · AddaStageRecord (INSERT one per WorkflowStage).
**7. Transaction boundaries** — `@transaction.atomic`; per-product code counter via
`select_for_update` (race-safe — do managers can't get the same code).
**8. RBAC** — management role; sidebar-gated.
**9. ADRs** — 0010 (global unique references forever).
**10. Tables** — production_adda, production_addastagerecord.
**11. Example payload** — `product=5 csrfmiddlewaretoken=…`
**12. Before → After**
```
BEFORE (Product 5 = "3 Patti", flow = Layering→Cutting-Pattern→Cutting→Barcode)
AFTER
 Adda(code=3-PATTI-003, product=5, status=in_progress, current_stage=Layering)
 AddaStageRecord × 4 (one per WorkflowStage, all not-started)
```
**13. Debugging** — "no stages created" → product has no WorkflowStage flow
(set it in the flow editor). Duplicate code → counter lock bypassed.
**14. Common mistakes** — creating an Adda for a product with no flow; expecting
to pick the code (it's auto + global-unique forever).
**15. Why** — one click + auto code = zero friction (the most-run management
action); race-safe counter so concurrent creates never collide.
**16. What breaks if bypassed** — hand-made Adda without stage records = a batch
that can't move through production.

Chokepoint context: adda_service uses the same select_for_update discipline as money code.
