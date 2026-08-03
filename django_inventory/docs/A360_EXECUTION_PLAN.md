---
id: a360-execution-plan
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# A360 EXECUTION PLAN v2 — Adda-360 management overview

> Phase A360 of [IMPLEMENTATION_ROADMAP_PDD_V1.md](IMPLEMENTATION_ROADMAP_PDD_V1.md).
> Design source (owner-accepted 2026-07-05):
> [ADDA_OVERVIEW_AUDIT_2026_07_05.md](ADDA_OVERVIEW_AUDIT_2026_07_05.md) §4 —
> "the Adda page becomes the PRIMARY operational page for management", built
> by REUSING existing services (no new tables, no new writes, no new money
> paths — the STOP rule applies; this phase is 100% read/UI).
> **v2 (owner-ordered architectural review, 2026-07-05): scope EXPANDED with
> Stage Progress header · Stage Timeline · Stage Health · worker board split
> into Progress + Contribution — see §R below. Page census: NOTHING merges
> away; A360 = the per-Adda READ hub, other pages stay as cross-Adda
> worklists / operation consoles / audited write chokepoints.**
> STATUS: **✅ ACCEPTED by owner 2026-07-05 + follow-ups accepted (uncommitted,
> checkpoint policy).** Built exactly per v2 (+ the two final refinements:
> worker contribution = full summary with HONEST metrics — per-stage share
> only, mixed-units rollup refused; genericness ENFORCED by a source-
> inspection test on views/a360.py). Gate PASS **808** (+8
> test_a360_overview), golden byte-identical, ZERO migrations/writes.
> LIVE E2E (real 3-PATTI): settled 3-PATTI-009 — 3✅+1🟡 health, Expected ₹0 /
> Settled ₹1500 / Standard ₹1500 / Variance ₹0, per-stage board rows with
> generic units (layers/job/pieces) + share% + settled counts, timeline,
> ADR-0009 cost rows; mid-flight 3-PATTI-010 — 🟡+⚪⚪⚪, "assigned 1 ·
> completed 1", DEV-Monthly badged with ₹ suppressed; WORKER LEAK = 0 bytes
> (browser-proven); 360/768 no-overflow; costing page relabeled + variance.
> ONE display-honesty fix found live: frozen expected on a now-non-payable
> stage (layering) was showing on the board — suppressed like monthly (the
> funnel never pays it; freeze-time semantics question flagged to owner).
> **POST-ACCEPTANCE FOLLOW-UPS (owner-ordered, 2026-07-05, gate PASS 811):**
> (1) ONE-RULE freeze fix — `effective_pay_rate` (the F2 chokepoint used at
> freeze/rerate/settlement/every dashboard) now returns 0 for
> `credits_workers=False` stages exactly like grouped members; +3 tests
> (freeze-0, payable-unchanged, rerate-cannot-resurrect); 4 old test
> fixtures updated to say `credits_workers=True` explicitly (they meant
> payable stages); 2 stale dev rows re-frozen to 0; live-proven: utest's
> My Work on 3-PATTI-009 shows ₹500+₹1000 only, phantom layering ₹300 gone.
> (2) MOBILE-DENSITY lock applied: cost/workers/timeline sections now
> COLLAPSED by default with answer-carrying summary lines ("std ₹1500 ·
> settled ₹1500", "1 on this Adda · 0 with open tasks", "4 events") —
> summaries-first scan layer (chips + strip) stays visible; 360px
> no-overflow re-verified; density principles saved to the standing
> mobile-first memory rule.
> Anchors verified against code 2026-07-05 (post-R8 + WP fixes, gate 800).

---

## §R — Architectural review (owner's 6 points, answered)

### R-1. Page census — what happens to every management page after A360

| Page | Verdict | Why |
|---|---|---|
| Adda detail | **BECOMES A360** | the host |
| Adda list | keep as-is | navigation index into A360 |
| Production dashboard (KPIs/digest/time-logs) | keep as-is | FACTORY-wide; A360 is per-Adda; they cross-link |
| Stalled Addas | keep as drill-down | cross-Adda filter; A360's Stage Health shows the per-Adda view of the SAME predicate |
| Pending Reports | keep as drill-down | cross-Adda worker queue; A360's Worker Progress shows the per-Adda slice |
| Costing page | keep as factory-wide list (relabel + variance per plan) | per-Adda cost detail lives in A360's cost panel |
| Stage Rates page | keep as drill-down | super-admin CORRECTION surface (write chokepoint); A360 links |
| Review-reports | keep as drill-down | verified-qty CORRECTION chokepoint; A360 worker rows link |
| Stage panels / pattern workspace | keep as-is | OPERATION surfaces (writes), embedded as tabs already |
| Settlement queue/list + detail | keep as-is | cross-Adda money worklist + THE money event page; A360 money strip links |
| Payroll overview / worker detail / My Earnings | keep as-is | worker-scoped by design (payment is per-worker) |
| Barcode dashboard/list/exports | keep as drill-down | piece-tracking domain; (future: a count tile on A360 — postponed) |
| Full Adda history | keep as drill-down | complete audit log; A360 timeline is the summarized view, already links to it |
| **Deprecations** | none now | candidates to revisit AFTER A360 proves itself: `stage_panel_standalone` (redundant with A360 tabs for management) — flagged, not acted on |

**The clean long-term shape:** A360 = per-Adda reading; queues (settlement/pending/stalled) = cross-Adda worklists; consoles = operations; chokepoint pages = audited writes. No page loses its write role to A360 — ever (point 4).

### R-2. The five requested sections — all belong, all pure reads

| Section | Verdict | Existing truth it aggregates |
|---|---|---|
| **Stage Progress** | YES — becomes the A360 header strip | product flow order + SR started/completed (the pipeline ctx already on the page) + % complete; "where is it stuck" = Stage Health |
| **Stage Timeline** | YES | `AddaHistory` ALREADY records started/advanced/completed events — the timeline is a change-type-filtered render of the existing feed (no new data, one filtered include) |
| **Worker Progress** | YES — status half of the worker board | `WorkerStageTask` statuses per stage (assigned/in_progress/completed/verified + cancelled excluded) — operational visibility FIRST, listed before money |
| **Worker Contribution** | YES — money half of the same board | reported Σgood / verified Σ / expected ₹ (monthly suppressed, R4) / settled lines — all frozen or derived rows |
| **Stage Health** | YES — derived at render time, never stored | ✅ = `completed_at` set · 🟡 = started & moving · 🔴 = the EXISTING `stalled_stage_records` predicate (H-2B: the ONE stalled calculation — digest, drill-down and A360 always reconcile) applied per-Adda · ⚪ = not started |

### R-3. Generic snapshot = the standard for every future stage — verified
The handler contract already carries all three roles: `snapshot(adda)` =
current-stage summary (tiles, REQUIRED) · `admin_snapshot(adda)` =
stage-specific reference consumed as the NEXT stage's previous-stage
reference (optional override, default None) · rendered by ONE shared partial.
A new stage implements its handler + typed record and gets tiles, panel
injection, report engine, and A360 aggregation with ZERO new UI components.
This section is now the documented standard (production GUIDE gets a
"new-stage checklist" row at docs-sync).

### R-4. READ-ONLY — reaffirmed as a hard property
Every A360 number is an existing frozen value or a SUM/COUNT/subtraction of
existing rows rendered at request time. No new money/settlement/ledger/payment
logic, no stored aggregates, no second calculation of anything that already
has a single home (stalled, recon, funnel, effective rate — all reused from
their sole owners). The money-write STOP rule is structurally satisfied:
the phase touches only views/templates.

### R-5. Future stages (Bundling, Sewing, Checking, Packing, Dispatch)
Each = one new handler package (register → tiles/panels/report/snapshots/A360
all pick it up), a typed record, its operation partial, and Flow-Editor config
for pay. A360's panels iterate `product.workflow_stages` generically — zero
stage names anywhere in A360 code. No redesign required; verified against the
R8 registry seams.

### R-6. Plan changes after this review
**ADDED:** Stage Progress header strip · Stage Timeline (filtered existing
feed) · Stage Health chips (reusing the single stalled predicate) · worker
board explicitly split Progress-then-Contribution (operational visibility
before money). **REMOVED:** nothing. **POSTPONED:** barcode count tile,
factory-month report (own phase), any deprecations (revisit after A360 lands).
Scope stays one working day + ~half for the additions; still zero migrations.

## What lands (v2: header + timeline + four panels + one relabel)

0. **Stage Progress header** — current stage, done/remaining, % complete,
   per-stage **Health chips** (✅🟡🔴⚪ per §R-2). 🔴 links to the pending
   workers / stalled context.
0b. **Stage Timeline** — vertical started→completed journey per stage
   (change-type-filtered AddaHistory render; "Full history" link stays).

All three panels render through the SAME component the generic stage
snapshots use — `_stage_admin_snapshot.html`'s `{'title','sections'}` shape —
exactly per your requirement that A360 reuse the snapshot architecture
instead of new UI. Management-gated in ctx (workers receive NOTHING —
leak-tested like R1/R8); collapsible; mobile-first single column.

### Panel 1 — Cost (per Adda)
Rows per stage: frozen `processing_cost` (honest-NULL shown as "unpriced") ·
method · settled labor (Σ non-voided SWA on that SR) · recon flag chip
(`reconcile_stage_pay(adda=)` — the same helper the settlement page uses).
Header lines, labeled per the P-COST finding so the ADR-0009 duality reads
correctly:
- **Standard labor cost** = Σ processing_cost (payable stages)
- **Actual settled labor** = Σ SWA
- **Variance (std − actual)** — the declared ADR-0009 home for this drift
- **Full cost (ADR-0009)** = material (honest "not priced — G1") + actual
  settled labor + non-payable priced processing. Never the sum of the two
  labor numbers.

### Panel 2 — Worker board (per Adda) — Progress THEN Contribution (v2)
Grouped by stage. **Progress half (first — operational visibility before
money):** per-stage counts + names by status (assigned / active / completed /
pending). **Contribution half:** per worker — reported Σ good · verified Σ ·
expected ₹ (SUPPRESSED + Monthly badge for monthly workers — R4 rules reused)
· settled-lines count · link → review-reports (corrections stay on their
audited page). Data = the page's existing `worker_tasks` + contributions
prefetches + one monthly-ids query + one WSC aggregate.

### Panel 3 — Money summary strip
Expected uncredited total (READ-ONLY reuse of the settlement funnel:
`_settleable_lines(_payable_stage_records(adda))` — no draft created) ·
settled total · settlement state chip (R1 button ctx reused) · quick links
(settlement detail/start · stage rates · review-reports · full history).

### Costing page (factory-wide list) — P-COST fix
Column relabel "Mfg Cost" → **"Standard labor cost"** + new **Variance**
column (std − actual per Adda) + a one-line ADR-0009 duality hint. Unpriced
flags unchanged.

## Files
| Area | Files |
|---|---|
| Panel data | `production/views/adda_views.py` (management-gated ctx builders; ~3 bounded aggregates) — reads only |
| Render | `adda_detail.html` (one "Adda 360" management section, three includes of the EXISTING snapshot partial via `{% with %}`) |
| Costing page | `costing_views.py` (variance column) + `costing.html` (relabel) |
| Tests | `test_a360_overview.py` (new) |

**No migrations. No services touched. No expense-app writes.**

## Tests
1. Gating: worker GET of Adda detail contains ZERO panel markers (leak test);
   management sees all three.
2. Math: expected-uncredited + settled are non-overlapping (settle → expected
   moves to settled); variance = std − actual; honest-NULL when unpriced.
3. Monthly worker row: qty shown, ₹ suppressed, badge (R4 pin reused).
4. Costing page relabel + variance column render.
5. Query bound: assertNumQueries guard on the Adda-detail management view
   (baseline documented in-file, PA-16 style).
6. Full gate + golden (no money code — must be byte-identical).

## Browser E2E (REAL 3-PATTI only, per standing rule)
On settled 3-PATTI-009: cost panel shows pattern ₹500 fixed + cutting ₹1000 =
std 1500, actual 1500, variance 0, recon all-ok; worker board shows utest's
rows settled; money strip expected ₹0 / settled ₹1500. Then a FRESH 3-PATTI
Adda mid-flight: expected>0/settled 0 state + monthly worker on the board
(badge, no ₹) + worker-login leak check + 360/768/1280.

## Risks
| Risk | Mitigation |
|---|---|
| Adda page weight | bounded aggregates, collapsible panels, assertNumQueries pin |
| Duality misread | explicit labels + variance column (the P-COST fix is the point) |
| Funnel reuse creates drafts | it doesn't — pure read of `_settleable_lines` (no AddaSettlement row) |

## Rollback
`git revert` — zero migrations, zero data.

## Acceptance criteria
- [ ] One page answers: cost, earnings, per-worker status, settlement state,
      links — browser-proven on real 3-PATTI at 3 viewports, both roles.
- [ ] Costing page relabeled with variance.
- [ ] Golden byte-identical; gate PASS; docs synced same session.

## Order (estimated)
Ctx builders + tests ~2h · template panels ~2h · costing page ~45m ·
E2E + docs ~1.5h ≈ one working day. Uncommitted (checkpoint policy).
