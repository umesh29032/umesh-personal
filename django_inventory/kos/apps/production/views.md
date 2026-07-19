---
id: app-production-views
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "96 view classes in 15 modules — which file do I open, and what may each group do?"
related: [app-production, app-production-urls]
---

# production — handler knowledge (`config/production/views/`, 15 modules)

> 📂 [production app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)
> Same house law: views parse + gate; stage/production logic lives in
> services and `stages/<stage>/service.py` handlers.

## Handler groups at a glance

- **READ:** dashboard.py (3) · costing_views.py (2) · a360.py (Adda-360 hub) · list views across modules
- **WRITE (production truth):** stage_views.py (26 — the four workspaces' actions) · generic_stage_views.py (6) · worker_report_views.py (2) · adda_views.py (6) · flow_views.py (2) · pattern_stage_views.py (12)
- **ADMIN (SA-enforced):** product CRUD (product_views.py 5) · stage library/masters (in stage_views) · rate_views.py (2 — S1.1 rerate) · reopen views (every workspace has one)
- **DELETE:** row-level workspace deletes only (breakup/bundle-item/photo) — always pre-money, always guarded; nothing money-bearing deletes
- **ASYNC:** none (server-rendered; embedded iframes via `?embedded=1`, not XHR APIs)

## The gate layer — `mixins.py` (4 classes, read FIRST)

Stage-facing mixins resolve the Adda by `<code>`, check **access ∩
assignment** via `access_service` (the ONE predicate), and management/SA
role sets via `permission_service`. Every stage view inherits from here —
if a gate misbehaves, fix the mixin, not 20 views.

## Module map (open the right file in seconds)

| Module | Classes | Owns |
|---|---|---|
| `dashboard.py` | 3 | floor home, stalled, pending-reports |
| `adda_views.py` | 6 | Adda list/create/detail + lanes + bundle-sets |
| `stage_views.py` | 26 | layering + cutting workspaces' actions (templates `production/layering_workspace.html`, `production/cutting_workspace.html`), stage panel (dynamic `get_template_names` — embedded vs standalone variants), stage library + categories + machine-types CRUD |
| `pattern_stage_views.py` | 12 | Pattern-Design workspace: start/save/photos/verify/sizes/complete/reopen |
| `barcode_gen_views.py` | 7 | barcode-gen workspace + bounce |
| `generic_stage_views.py` | 6 | R10-B parameterized set: start/complete/reopen/allocate/alloc-void + panel |
| `worker_report_views.py` | 2 | WorkerReportView (phone form) · AddaReportReviewView (red pen) |
| `flow_views.py` | 2 | the flow editor |
| `product_views.py` | 5 | product CRUD (SA) + sizes |
| `pattern_views.py` | 8 | ProductPattern library CRUD + patterns_ai redirects |
| `rate_views.py` | 2 | S1.1 stage-rate list + correct (SA; service re-gates) |
| `costing_views.py` | 2 | ADR-0009 cost surfaces (read-only) |
| `a360.py` | — | the per-Adda management hub (A360) |
| `access_views.py` | 15 | Access-Control hub surfaces (roles/skills admin UI) |
| `presentation.py` | — | display helpers (no gates, no writes) |

## The handlers that matter most

**`WorkerReportView`** (worker_report_views.py) — the phone form. Gates:
own task only (assignment), skill via mixin. Builds the report schema from
the stage's grain + the worker's allocations (labels only — blind
reporting). POST → `worker_task_service.report_contributions` /
`save_draft_contributions` / `complete_worker_task` (the freeze — five
guards, [stage-tracking](../../features/stage-tracking.md)).

**`AddaReportReviewView`** — management red pen. POST per line →
`set_verified_quantity` (raw string → service parses; settled line refuses
naming the ADST). One correction here propagates to pool AND money via the
shared resolver.

**`GenericStageCompleteView`** — the funnel every config stage passes:
C3 mid-work block (names workers; SA override = audited reason) → complete
→ `materialize_stage_pool`. Its reopen twin walks the downstream-consumer
guard (actionable error, furthest blocker).

**`GenericStageAllocateView` / `AllocationVoidView`** — OP-1 split-the-work:
POST → `pool_service.allocate/void_allocation` (over-draw refused always-on;
H-2 void guard).

**`StageRateCorrectView`** — S1.1: SA-only `rerate_stage_role` until
settlement, per (stage_record, role), auto-recalc + `RateCorrectionAudit`.

**Reopen family** (Layering/Pattern/Cutting/BarcodeGen/Generic) — admin-only
unlock; each refuses when money or downstream consumption exists
([settlement-lifecycle §armor](../../flows/settlement-lifecycle.md)).

## Handler rules of thumb (this app)

1. New config-only stage = ZERO new views — the generic set + a
   `stages/<stage>/` handler package (R10-B frozen rule).
2. Stage-gated view? Inherit the mixins; never hand-roll `user_can_access_stage`.
3. Worker-facing = mobile-first FUNCTIONAL requirement (owner rule 11) —
   verify phone layout before done.
4. Panel routes honor `?embedded=1` — new panels must too (iframe embedding).
5. Complete/reopen actions: the guard lives in the service — surface its
   message verbatim; the refusals are designed to be read.

## Required Knowledge (this page)

- [ ] CBV packages + shared mixins → [transactions §boundary](../../concepts/django/transactions.md)
- [ ] access ∩ assignment predicate → [rbac-access](../../features/rbac-access.md)
- [ ] Why views never own stage logic → [service-layer](../../concepts/architecture/service-layer.md)

## Learning Graph

**Before:** [urls.md](urls.md) parts 1–4 (each handler's URL story).
**After:** [services.md](services.md) → open `views/mixins.py` first, then
the module your URL named.
