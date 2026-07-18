---
id: adda-overview-audit-2026-07-05
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# Adda Overview Audit — calculations, business rules, architecture (2026-07-05)

> Owner-ordered pre-R7 pause: (1) prove why Manufacturing Cost < Worker
> Earnings, (2) inventory every Adda surface for a consolidation design,
> (3) re-validate ADR-0011. **Design-only — nothing implemented.**
> Method: main-thread code reads + live dev-DB decomposition (money analysis
> never delegated), plus a 3-agent read-only surface inventory verified
> against main-thread reads. Every claim cites code or a probe.

---

## 1) CALCULATION AUDIT — why cost < earnings (PROVEN, not assumed)

### 1a. What each number actually is

| Displayed number | Formula | Frozen when | Source |
|---|---|---|---|
| **"Mfg Cost" (costing page)** | Σ `AddaStageRecord.processing_cost` = `ws.cost_rate × handler OUTPUT qty` (`cost_quantity_snapshot`), priced+frozen rows only | stage ADVANCE | costing_views.py:40-44 ← cost_service |
| **"Worker Earnings" (same page)** | Σ non-voided `SWA.earning_amount_snapshot` = role-aware frozen rate × `settlement_quantity` (verified ?? good) per contribution line | settlement FINALIZE | costing_views.py:61-65 ← adda_settlement_service |
| **Expected earnings** | Σ frozen `WSC.expected_earning` = frozen `AddaStageRoleRate` × good qty | task COMPLETE | worker_task_service:288-296 |

These are the **ADR-0009 cost duality**: STANDARD labor cost vs ACTUAL labor
pay — "they diverge legitimately… they are NEVER additive." The costing page
displays both columns side-by-side (with an ADR-0009 comment in the template)
but labels the standard column "Mfg Cost", which invites the false invariant
`cost ≥ earnings`. **That invariant only holds for the ADR-0009 FULL-cost
formula** (material + ACTUAL settled labor + non-payable processing + overhead),
where actual labor is INSIDE cost by construction. The page does not compute
the full formula (it predates ADR-0009 and is marked transitional in-code,
costing_views.py:15-17).

### 1b. Live decomposition — every current cost<earnings case explained

Dev-DB sweep (all 12 Addas):

| Adda | Σ processing_cost | settled SWA | expected WSC | Mechanism |
|---|---|---|---|---|
| **3-PATTI-001** | 315.00 | **360.00** | 390.00 | **M1: quantity-basis divergence — the B-1 leak** |
| 3-PATTI-006 | None | — | 450.00 | M2: timing (stage still open — nothing frozen yet) |
| 3-PATTI-008 | None | — | 350.00 | M2: timing |
| DEV-R4M-001 | None | 200.00 | 325.00 | M3: test artifact (SR completed via shell, freeze skipped) |
| TEST-86f27f0a | None | — | 500.00 | M3: test artifact |

**M1 — the one real business case (3-PATTI-001, cutting):**
- Standard cost: ₹3 × **105 produced** (frozen `cost_quantity_snapshot`) = **₹315**.
- Settled: workers reported 130 good; verified corrections → 60+15+45 = **120
  paid** × ₹3 = **₹360**.
- **Paid 120 vs produced 105** — this is EXACTLY the pre-staging-audit
  headline leak (B-1), present in the seeded historical data. The recon
  machinery classifies it correctly TODAY (probe):
  `cutting | cost 315 | out 105 | paid 120 | flag over_allocated | WARN-class True`
  — with `ENFORCE_SETTLEMENT_RECONCILIATION=True` this finalize would have
  been **BLOCKED** (S5); with `ENFORCE_ALLOCATION_BOUND=True` the
  over-reporting would have been refused at complete-time (S4-P4). **Both
  flags are default-OFF by owner design (deploy → soak → enable runbook,
  docs/ENFORCEMENT_ROLLOUT_RUNBOOK_2026_06_14.md).**

**M2 — timing:** expected earnings freeze at task-complete; processing_cost
freezes at stage-advance. Every mid-flight stage shows earnings with NO cost
yet. Not a bug — two honest snapshots at different boundaries.

**M4 — structural (no instance in data, possible by design):** role-rate
overrides (role ₹12 > base ₹10) make actual > standard at equal quantities;
super-admin rerate recalcs expected until settlement while processing_cost is
deliberately never re-frozen (Phase-10 documented by-design).

### 1c. Verdict

- **No calculation bug.** Every number matches its documented formula; the
  settlement chokepoint, freeze order, grouped→0 (F2), verified-else-reported
  resolver all compute as specified.
- **One real business finding:** the displayed comparison is the raw duality,
  and the single genuine `paid > produced` case is the KNOWN B-1 leak whose
  enforcement levers are built, tested, and waiting on the deploy+soak gate.
- **Presentation finding (P-COST):** the costing page's "Mfg Cost" column is
  standard labor ONLY (no material, no actual labor, no overhead). It should
  eventually show the ADR-0009 full-cost + a standard-vs-actual VARIANCE
  column (the declared home for this drift) — under that formula
  cost ≥ labor holds by construction. UI change → belongs to the Adda-360
  phase (§4), not a hotfix.

---

## 2) BUSINESS-RULE AUDIT

| Rule | Status | Evidence |
|---|---|---|
| Money books only at settlement (Option B) | HOLDS | census 2026-07-05 (review doc Part 2) |
| Duality never summed (ADR-0009) | HOLDS | no surface adds the two columns; costing template carries the warning |
| Paid ≤ produced | **NOT ENFORCED yet — by owner decision** | flags default-OFF; 3-PATTI-001 is the seeded example; recon flags it `over_allocated` today |
| ADR-0011 (monthly) | HOLDS everywhere | §3 below |
| Frozen snapshots never recomputed | HOLDS | rerate = audited exception, settlement-armored |

**The only action this audit recommends on Part 1:** treat the enforcement
flags' rollout (existing runbook) with priority once deployed — the leak class
is real, visible in data, and already catchable. No new code needed.

---

## 3) ADR-0011 VALIDATION (probes, 2026-07-05)

- Monthly worker (dev.monthly): **0 SWA rows, 0 ledger rows** after all R4/R5
  activity; production tracking fully intact (R4/R5 browser proofs: dashboard,
  report page, My Work, history).
- Per-Adda cost CANNOT see monthly salary structurally: `processing_cost` =
  rate × output qty (worker-independent — cost_service reads no worker/pay
  data), and **`FactoryExpense` has no Adda FK at all** (field list probed) —
  allocation is impossible even by accident.
- Factory-level reporting is buildable TODAY with zero allocation (probe):
  July expenses ₹10,500 (salary 9,000 + electricity 1,500) ·
  Addas completed 2 / in-progress 10 · Σ output qty 113 · Σ settled labor
  ₹560 — all independent queries. A future "factory month report" = pure
  read-only aggregation phase.
- Payroll/settlement surfaces: monthly exclusions verified R4/R5 (funnel,
  queue, cash path, era-A guard H-1, advances M-2).

**No ADR-0011 conflict found anywhere.**

---

## 4) ARCHITECTURE REVIEW — where Adda information lives today

Inventory: 20+ surfaces (3-agent sweep, file:line anchors in the workflow
output; key ones cross-verified main-thread). Consolidated matrix of the
owner's items:

| Data item | Lives today | Duplicated? | Verdict |
|---|---|---|---|
| Manufacturing cost | costing page ONLY (factory-wide list) | no | **ADD per-Adda cost panel to Adda page** (full-cost + variance); keep costing page as the factory-wide list |
| Worker earnings (settled) | costing page column · settlement detail (frozen items) · worker-scoped payroll pages | worker-vs-adda scoped, not true dupes | **ADD per-Adda per-worker rollup to Adda page** (reuse `worker_adda_earnings`-style query, Adda-scoped) |
| Expected earnings | My Work (self-only) · settlement queue/detail (per-Adda) | no | **surface the per-Adda expected rollup on Adda page for management** (reuse `settlement_queue`'s per-Adda expected computation / `preview_lines`) |
| Stage progress | Adda page (tiles + pipeline) · dashboards · adda list · stalled page | yes — Adda page already canonical | stays; dashboards keep summaries |
| Assigned/active/pending/completed workers | pending-reports page (queue) · stage panels (roster) · Adda page shows only OWN tasks | **gap** — no per-Adda all-worker board | **ADD worker board to Adda page**: per stage × worker: status, reported qty, verified, expected — data already prefetched (`worker_tasks`, contributions) |
| Worker contributions | review-reports page (correction UI) · settlement draft lines · My Work (self) | partial | worker board (above) shows read-only; review-reports stays the CORRECTION surface, linked |
| Settlement status | Adda page (R1 state-aware button) · settlement list/detail | no | stays; enrich button strip with expected-₹/settled-₹ chips |
| Payment status (cash) | worker detail / payroll overview (worker-scoped by design — payment is per-worker, not per-Adda) | no | keep worker-scoped; Adda page links to settlement detail which shows final payable per worker |
| Stage rates | stage-rates page (super-admin, per-Adda) + link on Adda page | no | stays (link already there, R1) |
| Reports/review | review-reports page + pending-reports queue | no | link from worker board rows |
| History/timeline | Adda page activity feed (mgmt) + full history page + dashboard accordions | yes (3 renderers, one source) | fine — one source (`AddaHistory`), summaries elsewhere |
| Rolls / barcodes / exports | Adda page (rolls) · tracking pages (barcodes/exports) | no | link tiles suffice |

**Assessment: your instinct is right and cheap to satisfy.** `AddaDetailView`
is ALREADY the de-facto hub (stage tiles, pipeline, My Work, settlement
button, stage-rates link, rolls, timeline). The missing pieces are exactly
three management panels — **cost, workers, money-summary** — and ALL their
data already exists behind services built in prior phases. No new tables, no
new services, no new writes:

1. **Cost panel** — `cost_map` per stage (frozen processing_cost, honest-NULL)
   + ADR-0009 full-cost line (material when priced + settled labor +
   non-payable processing) + variance vs standard + `reconcile_stage_pay(adda=)`
   flags (the over_allocated banner already exists on settlement detail —
   same helper, second consumer).
2. **Worker board** — per (stage, worker): task status · reported/verified qty
   · expected ₹ (suppressed for monthly workers, badge instead — R4 rules
   reused) · link to review-reports. Data = existing prefetches + one WSC query.
3. **Money summary strip** — expected total (funnel preview) · settled total
   (SWA sum) · settlement state chip · links (settlement detail, stage rates,
   review-reports). All existing reads.

Duplication policy: dashboards/lists keep COUNTS and summaries; the Adda page
becomes the single DRILL-DOWN. Nothing is removed; worker-scoped payroll pages
stay worker-scoped (payment is a worker-level concept).

**Explicit non-goals:** no FactoryExpense on the Adda page (ADR-0011 —
factory-level), no editing on the new panels (reads only; corrections keep
their audited chokepoint pages), no new money paths (STOP rule applies).

---

## 5) RECOMMENDATION — sequencing

**Make this a separate roadmap phase — "Adda-360 (management overview)" —
and run it BEFORE R7.** Reasons:
- It is pure READ/UI (zero money-write risk; the money-write STOP rule keeps
  it honest), while R7 is money-critical and independent.
- It fixes the owner-facing comprehension bug from Part 1 (the mislabeled
  duality) at its natural home — the cost panel ships the full-cost +
  variance presentation.
- Daily-ops value is immediate; F&F (R7) is a rare event (worker exit).
- No dependency in either direction; R7's design is unaffected.

Proposed shape: Adda-360 execution plan (panels 1-3 above + costing-page
column relabel "Standard labor cost" + variance column) → owner approval →
build → then R7.

### Verification sources
Main-thread: costing_views.py (full read), cost_service, adda_settlement_service,
worker_task_service, reconciliation_service, live dev-DB probes (per-Adda
sweep, 3-PATTI-001 stage decomposition, recon flags, ADR-0011 counts, factory
report feasibility). Inventory: 3 read-only agents (production / expense /
dashboards+tracking), file:line anchors, key surfaces cross-verified
main-thread. Confidence: High.
