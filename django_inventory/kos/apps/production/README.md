---
id: app-production
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "I'm about to work in the production app — what does it own, where do its 80 URLs enter, and which files matter?"
related: [feature-stage-tracking, feature-allocation, feature-cutting, flow-cloth-to-garment]
---

# production — the complete app map

> 📂 [Apps](../README.md) · [LOS home](../../README.md) — *andar koodo:
> [URLs](urls.md) · [Views](views.md) · [Models](models.md) · [Services](services.md)*

## Mental Model — read this before anything

> **A factory pipeline.** Material enters. Stations transform it, in
> order. Every station RECORDS its work. Nothing skips a station; nothing
> travels backwards without authorization (and a reason). The pipeline's
> stations are DATA (configured per product), not code — so the factory
> can grow new stations without rebuilding the machines. *(Pipeline hai:
> har station kaam note karta hai, ulta chalna = ijaazat + wajah.)*

## Common Misconceptions

- **"Production pays workers."** Never. This app records WORK (claims +
  verifications); money is born only in the expense app's gate. `expected_*`
  here = visibility, not money.
- **"Stages are code."** Stages are ROWS (Stage library + WorkflowStage
  config); only the four built-in workspaces have handler packages, and
  new config-only stages ride the generic endpoints (R10-B) — zero new code paths.
- **"The pool is inventory of money owed."** The pool counts CAPACITY
  (pieces), owner-locked away from every money concern.
- **"reported_quantity gets fixed when wrong."** Never touched — the
  worker's claim is immutable; corrections live in `verified_quantity`
  (both hands visible forever).
- **"Reopen = undo."** Reopen is a GUARDED unlock — refused whenever money
  or downstream consumption exists, and the refusal names the blocker.

## Real Engineering Questions

**PM: "Add a new 'Ironing' stage for T-shirts."**
Think: config-only? → Stage library row + flow-editor attach (rate, grain,
pay-eligibility) → R10-B: ZERO new endpoints, generic set serves it →
pool implications? (grain monotonicity) → tests: generic-stage suite
covers config stages → done without touching code. *If your plan involved
new views, re-read R10-B.*

**PM: "Manager says a worker's cutting count is wrong, Adda already settled."**
Chain: `set_verified_quantity` → refuses, names the ADST → reverse the
settlement first ([two-truths interlocks](../../concepts/architecture/two-truths.md))
→ correct → re-settle. The refusal IS the procedure.

**PM: "Why can't I reopen layering?"**
→ read the error: it names the furthest downstream blocker (allocations /
completed reports / settlement) → reverse-first peel → [allocation](../../features/allocation.md) reopen armor.

## Reading Strategy

- **Beginner:** Mental Model → [cloth-to-garment](../../flows/cloth-to-garment.md)
  → [urls.md](urls.md) index intro → the dashboard + adda-detail sections.
- **Intermediate:** Start Here table → [urls-adda.md](urls-adda.md)
  (create → panel → generic actions → worker/review) → [views.md](views.md) module map.
- **Senior:** [services.md](services.md) chokepoints → generic-reopen +
  allocate sections → [models.md](models.md) cross-model laws → Engineering
  Checklist → the S4 receipts via [reading-the-docs](../../project/reading-the-docs.md).

## Start Here — common tasks

| Need to… | Go to |
|---|---|
| Add a new endpoint | [urls.md](urls.md) — pick the lane; **config-only stages NEVER add endpoints** (R10-B generic set, frozen rule) |
| Modify stage/flow/production logic | [services.md](services.md) — the owning service; stage-specific = `stages/<stage>/service.py` |
| Change database schema | [models.md](models.md) (who writes it) + [migrations](../../concepts/django/migrations.md) — this app's migrations carry the famous 0035/0039 patterns |
| Fix permissions / stage visibility | [views.md](views.md) §mixins + access ∩ assignment ([rbac-access](../../features/rbac-access.md)) |
| Understand a request | Request Journeys in [urls.md](urls.md) · worker tap: [request-through-stack](../../flows/request-through-stack.md) |
| Debug wrong counts | [counts-mismatch](../../debugging/counts-mismatch.md) — name the number first |
| Add tests | 69 test files here; S3/S4 suites = the patterns to copy |

## Why a SEPARATE app (the senior question)

Production owns the highest-CHURN domain — new stages, new workflows, new
floor realities every month. Separating it from money means churn never
touches the audited zone: this app can gain a whole stage type (R10-B did)
with ZERO expense-app diffs. It isolates the **production-truth** half of
[two-truths](../../concepts/architecture/two-truths.md) and follows the
platform principle: stages are DATA + handler packages, so the app evolves
by configuration, not by endpoint growth. Future: barcode-scan capture
(TM-2) lands HERE via C-TM's one door — already designed for.

## Technology Stack

| Layer | Used here | Learn it |
|---|---|---|
| Views | CBV package (15 modules) + shared gate mixins + `?embedded=1` iframes | [views.md](views.md) |
| Business | domain services + **stage HANDLER packages** (dispatch, no name-conditionals) | [services.md](services.md) · [service-layer](../../concepts/architecture/service-layer.md) |
| Data | ORM: `Coalesce` resolver, grouped aggregates; frozen snapshot columns | [from-orm-to-sql](../../concepts/postgresql/from-orm-to-sql.md) |
| Database | PG: advisory (5375,objid) + row locks, `wsc_gam_nonneg_sum_positive`-class CHECKs, the 0035/0039 migration patterns | [locks](../../concepts/postgresql/locks.md) · [migrations](../../concepts/django/migrations.md) |
| Testing | S3/S4 suites, refusal pins, perf baseline (fixed-cost fixtures) | [testing-strategy](../../concepts/testing/testing-strategy.md) · [query-performance](../../concepts/postgresql/query-performance.md) |

## Security

- **Authz axis 1 — role:** management lanes via mixins; SA-only masters (products, stage library, rerate)
- **Authz axis 2 — skill ∩ assignment:** the ONE stage-visibility predicate (`access_service`) — [rbac-access](../../features/rbac-access.md)
- **Validation:** report lines parsed at the edge (PA-07-2); DB shape armor on WSC
- **Threats defended:** over-claiming (pool + bound) · stale-instance races (P0-5 lock-and-reread) · double fixed-pay reports · history forgery (append-only WST/streams)
- **Audit:** every override is audited (C3 super-admin reason, `RateCorrectionAudit`), every stage event → timeline

## Required Knowledge — before working here

- [ ] Django: CBV packages + mixins · atomic boundaries → [transactions](../../concepts/django/transactions.md)
- [ ] PG: lock-and-reread + `of=('self',)` → [locks](../../concepts/postgresql/locks.md)
- [ ] Architecture: two-truths (this is the OTHER half) → [two-truths](../../concepts/architecture/two-truths.md) · single-writer/C-TM → [single-writer](../../concepts/architecture/single-writer.md)
- [ ] Domain: the pipeline story → [cloth-to-garment](../../flows/cloth-to-garment.md) · both-hands truth → [stage-tracking](../../features/stage-tracking.md)
- [ ] DSA shapes here: FSM (tasks) · fork-join (streams) · bounded counters (pool) → [stage-tracking §DSA](../../features/stage-tracking.md) · [cutting §DSA](../../features/cutting.md) · [allocation §DSA](../../features/allocation.md)

## Learning Graph

**Before:** [business-story](../../project/business-story.md) →
[cloth-to-garment](../../flows/cloth-to-garment.md) →
[stage-tracking](../../features/stage-tracking.md).
**After:** [allocation](../../features/allocation.md) →
[cutting](../../features/cutting.md) →
[counts-mismatch playbook](../../debugging/counts-mismatch.md) → then
[apps/expense](../expense/README.md) (where this app's truth becomes money).

## What this app owns

**Production truth, end to end:** products + their per-product flows (the
flow editor), Addas + stage records, the four built-in stage workspaces
(layering · pattern · cutting · barcode-gen) + config-only generic stages
(R10-B), worker tasks/contributions (the ONE capture door), piece pools +
allocations, stage costing snapshots (ADR-0009), Adda-frozen role rates,
streams/lanes.

## What it does NOT own

Money (→ `expense`; this app's `expected_*`/rates are visibility+snapshots,
never ledger) · barcode SCAN state + history timelines (→ `tracking`) ·
machines as assets (→ `machines`; stages point at MachineTypes) · cloth
roll masters (→ `raw_materials`; layering ATTACHES rolls).

## Where requests enter — 80 URLs, 7 lanes

| Lane | Routes | Who |
|---|---|---|
| Dashboards | `/production/` · `stalled/` · `pending-reports/` · `costing/` | management |
| Product masters + flow editor | `products/…` (CRUD SA-only, flow, sizes) · `patterns/…` | SA / mgmt |
| Adda lifecycle | `addas/` · `start/` · `<code>/` · lanes add/cancel · bundle-sets | management |
| Stage panels + generic actions | `<code>/stage/<type>/` + start/complete/reopen/**allocate/alloc-void** | skill+assignment gated |
| Built-in stage workspaces | `<code>/layering/…` (8) · `/pattern/…` (10) · `/cutting/…` (13) · `/barcode-gen/…` (5) | stage-skill gated |
| Worker + review | `<code>/report/<type>/` (worker phone) · `<code>/review-reports/` (P1 red pen) · `stage-rates/…` (S1.1 SA rerate) | worker / mgmt / SA |
| Stage library + masters | `stages/…` · `stage-categories/…` · `machine-types/…` (R10-C rows-not-code) | SA |

## The census

- **URLs:** 80 (`config/production/urls.py`, 181 lines — beautifully commented, read its header).
- **Views:** 15 modules in `config/production/views/` (~96 classes) — [views.md](views.md).
- **Models:** 35 across 7 modules in `config/production/models/` — [models.md](models.md).
- **Services:** 14 in `config/production/services/` + 6 stage-handler packages in `config/production/stages/` — [services.md](services.md).
- **Tests:** 69 files in `config/production/tests/`.

## The laws to carry in

1. **C-TM:** every work-capture path converges into WSC via
   `worker_task_service` — no second door, ever.
2. **Production ⊥ money:** four concerns orthogonal (allocation / cost /
   earning / settlement) — pool and allocation NEVER read or write money.
3. **R10-B:** new config-only stages ride the generic endpoint set —
   never new URLs.
4. Reopen armor: settlement-credited or downstream-consumed stages refuse,
   naming the blocker — reverse-first peel.

## Engineering Checklist — pre-flight before ANY change here

- [ ] **Concern check:** is this capacity / production-truth / config? If it's MONEY → wrong app, stop
- [ ] **C-TM:** does this capture work? It MUST flow through `worker_task_service` — no second door
- [ ] **R10-B:** new config-only stage? ZERO new endpoints — generic set + `stages/<stage>/` handler package
- [ ] Frozen snapshots stay frozen: `processing_cost`, `AddaStageRoleRate`, `expected_*` — config edits never re-price history
- [ ] Pool implications: does complete/reopen touch materialization? grain monotonicity held? locks stay in (5375, objid), never 5374
- [ ] Reopen/complete guards: surface the service's refusal verbatim — they name the fix
- [ ] Gates via `views/mixins.py` (access ∩ assignment) — never hand-rolled
- [ ] Worker-facing UI = mobile-FIRST (functional requirement, rule 11)
- [ ] New URL? sidebar rule (edited at [inventory §6 — the pair editor](../inventory/urls.md)) + [urls.md](urls.md) + [views.md](views.md) group
- [ ] Tests: S3/S4-suite patterns + refusal pins; battery runs SEQUENTIAL fresh-DB
- [ ] kos-sync + docs-sync (rule 12) same session

## Change Impact — touching this app affects

- **Settlement funnel** (reads WSC/verified/rates) + goldens ₹344.25/₹801/₹633
- **Pools downstream** (materialize at complete; grain monotonicity)
- **Barcode generation** (APSCPB is its input; printed payloads PERMANENT — ADR-0010)
- **Worker phones** (report schema scopes to allocations; mobile-first rule)
- **Sidebar rules** per new URL · **69 local tests + cross-app guards + CI gate 4/4 (WST)**
- Flow-editor changes ripple into every future Adda of that product (existing ASRs keep snapshots)

## Learn it / debug it

WHY: [stage-tracking](../../features/stage-tracking.md) · [allocation](../../features/allocation.md) ·
[cutting](../../features/cutting.md) · flows [cloth-to-garment](../../flows/cloth-to-garment.md)
· broken: [counts-mismatch](../../debugging/counts-mismatch.md) ·
docs: [docs/production/HUMAN_GUIDE.md](../../../docs/production/HUMAN_GUIDE.md) ·
[pool chokepoint](../../../docs/LEARNING_2_0/CHOKEPOINTS/pool_service.md) · PKM §3/§5
