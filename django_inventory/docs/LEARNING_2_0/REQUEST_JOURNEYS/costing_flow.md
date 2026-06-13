# Journey: Costing dashboard (read-only)

## TL;DR (1 min)
Per-Adda manufacturing cost (Σ frozen processing_cost) shown ALONGSIDE worker
earnings — never summed (ADR-0009). Honest-NULL banners for unpriced stages/rolls.

**URL** `production:costing`. **View** `production/views/costing_views.py:ProductionCostingView`
(reads only). **Service** `cost_service.adda_cost_summary` + payroll reads.
**Models read** AddaStageRecord.processing_cost, StageWorkAssignment (earnings),
ClothRoll (unpriced count). **Models written** NONE. **Tx** none. **RBAC**
management. **ADRs** 0009 (duality, honest-NULL). **Tables** read-only across the above.

### How would I debug this in production?
- **First file:** `production/views/costing_views.py` + `cost_service.adda_cost_summary`.
- **First query:** `SELECT adda_id,SUM(processing_cost) FROM production_addastagerecord WHERE processing_cost IS NOT NULL GROUP BY adda_id;`
- **First log:** n/a (read-only).
- **Failure modes:** total "too high" = someone added processing_cost + settled labor (ADR-0009 violation); NULL costs = unpriced (honest-NULL, surfaced as banner — not a bug).
- **Expected DB state:** processing_cost frozen-or-NULL; earnings live in ledger/SWA separately.
- **Recovery:** n/a (read-only). Fix underlying data via the owning service (cost reopen / pricing).

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (costing_views.py reads; cost_service.adda_cost_summary; C-1 unpriced-rolls map added this session). **Architectural interpretation** on full summary shape.
