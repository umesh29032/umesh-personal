# Bugs Found — QA 2026-06-02

7 confirmed by adversarial code audit (12 candidate findings refuted). Severity
after verification. ✅ = fixed this session, 📝 = documented for owner decision.

| # | Sev | Area | Bug | Status |
|---|---|---|---|---|
| 1 | HIGH | money | Settlement over-pay race | ✅ fixed |
| 2 | HIGH | money | Settlement delete/reverse strands advance pool | 📝 + mitigated |
| 3 | HIGH | money | Delete bundle/item with allocation → 500 ProtectedError | ✅ fixed |
| 4 | MED | money | `total_settled` ignores reversed settlement payment | ✅ fixed (2nd pass) |
| 5 | MED | cost | Priced non-producing stage freezes cost=NULL | 📝 |
| 6 | LOW | money | `_next_reference` cross-worker race | ✅ fixed (2nd pass) |
| 7 | LOW | mobile | Costing "unpriced" note crowds row on phone | ✅ fixed |
| 8 | LOW | cutting | `add_bundle_item` clobbers sourced count → consumed_count drift | ✅ fixed (2nd pass) |
| 9 | MED | money | Settlement-item inline admin-editable → breaks invariant | ✅ fixed (2nd pass) |
| 10 | MED | rbac | `/production/products/` reachable by karigar (Worker) — spec says Worker ✖ | ✅ fixed (3rd pass) |
| 11 | MED | sec | `tracking:scan` (`scan_piece`) `@login_required` only — any authed user stamps audit fields | ✅ fixed (3rd pass) |
| 12 | MED | rbac | Stage workspace/panel VIEWS role-gated only — skill enforced on actions, not viewing. Direct-URL into any stage workspace shows data/UI regardless of skill (inconsistent with AddaDetailView; violates spec "skills control stage visibility") | ✅ fixed (4th pass) |

> **4th pass (full route-enforcement audit, 2026-06-02):** Django URL-resolver
> introspection over EVERY route confirmed all app CBVs are gated (LoginReq +
> role/perm mixin); login-only views (my-earnings, worker-detail) have correct
> internal scoping (`can_view_worker`); all FBVs gated (`barcode_export_csv` 403,
> dashboards `@login_required` by design, scan fixed). Only real gap = #12: stage
> *viewing* was role-only. Fixed via `StageViewAccessMixin` (reuses
> `user_can_access_stage`) on the 5 standalone workspace/panel views. Browser-
> verified: no-skill karigar → layering/barcode-gen 403, cutting 200 (role-granted,
> OR-semantics), super 200.

> **3rd pass (RBAC refactor review, 2026-06-02):** #10 ProductListView was
> `ProductionRoleMixin` (incl. karigar) + sidebar rule granted karigar →
> tightened to management (super_admin+manager) at view + sidebar predicate +
> `SidebarItemRule` (migration 0018). #11 `scan_piece` now gated to
> `PRODUCTION_ROLES`. Browser-verified 4-persona matrix. Architecture gaps
> (no `supplier`/`worker` user-type; legacy `user_type`→role + `is_superuser`
> fallbacks load-bearing) documented, NOT removed — see STAGE_A re-audit + below.

> **2nd pass (Stage A re-audit, 2026-06-02):** every reader-tagged critical/high
> finding was REFUTED under adversarial verify (export lateral-access, MEDIA leak,
> StagePanel bypass, opening_advance, consumed_count drift — all not real; MEDIA
> is `DEBUG`-gated and safe in prod). Net new real bugs were #8 + #9 above, and
> prior-deferred #4 + #6 got fixed. Full reasoning: `STAGE_A_REAUDIT_2026_06_02.md`.

## Details

### #1 — Settlement payable-overdraw race (HIGH) ✅
`create_settlement` (settlement_service.py) reads `payable_before =
worker_balance(worker)` (unlocked `SUM`) and guards `total_settled <=
payable_before`. The only lock taken is `WorkerAdvance.select_for_update()`,
which matches **no rows** for a cash-only settlement (the common case). Two
concurrent cash settlements both read the same payable and each pay it in full
→ worker over-paid, permanently in the append-only ledger.

### #2 — Settlement removal/reversal strands the advance pool (HIGH) 📝
`advance_outstanding` / `advance_remaining` derive **only** from
`PayrollSettlementItem.amount_recovered`. Reversing the `advance_recovery`
ledger debit (the documented "fix a mistake" path) writes a REVERSAL row but
never touches `PayrollSettlementItem` → payable restored but advance still shows
recovered. **Observed live**: SETL-0001 was deleted out from under this audit;
wa-audit was left with an `advance_recovery ₹30` ledger debit (settlement=None)
while `advance_outstanding` showed the full ₹100 — overstated by ₹30, and
"Settlement History: none" despite `total_settled ₹20`. Root cause: no
`reverse_settlement` service that compensates the items; and (now fixed)
PayrollSettlement was admin-deletable.

### #3 — Delete bundle/item with worker allocation crashes (HIGH) ✅
`StageWorkAssignment.bundle_item`/`.bundle` are `on_delete=PROTECT` and those
rows are immutable (void only flags them). `delete_bundle_item`/`delete_bundle`
called `item.delete()` raw → `ProtectedError` 500 whenever an allocation
existed. Reachable via UI: allocate work, then delete the item before completing.

### #4 — `total_settled` overstated after a reversal (MED) 📝
`worker_summary` (payroll_service.py:128) and `PayrollOverviewView` sum
`DEBIT/SETTLEMENT_PAYMENT` without subtracting REVERSAL rows that reverse them.
Only manifests after the manual reversal path (tied to #2).

### #5 — Priced non-producing stage → cost NULL (MED) 📝
`cost_service._quantity_for` resolves a quantity only for `layering`, `cutting`,
`barcode_generation`. A `cutting_pattern` (or future custom) stage priced
`per_piece`/`per_layer` returns None → `processing_cost` frozen NULL and shown
as "unpriced" despite a rate being set. Needs an owner decision on what such a
stage bills on (likely `fixed_cost` only) or a flow-editor method restriction.

### #6 — `_next_reference` cross-worker race (LOW) 📝
`SETL-NNNN` is `max(id)+1` with no lock; `reference` is unique. Two concurrent
settlements (any workers) collide → IntegrityError 500 instead of retry. The #1
per-worker lock does NOT cover cross-worker collisions.

### #7 — Mobile "unpriced" note crowds the cost cell (LOW) ✅
costing.html mobile `td` is `display:flex`; the nested `.unpriced` div sat on
the same line as the cost + data-label.
</content>
