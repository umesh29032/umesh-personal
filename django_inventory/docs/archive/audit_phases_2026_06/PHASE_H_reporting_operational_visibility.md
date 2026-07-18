> **ARCHIVED 2026-07-13** — 2026-06 production-readiness audit phase; findings closed, superseded by the current frozen architecture ([../../MANUFACTURING_V1_FREEZE.md](../../MANUFACTURING_V1_FREEZE.md)). Kept for history (Phase-7 DOCCLEAN-D). Its own outbound links reflect the 2026-06 tree.

# Phase H — Reporting & Operational Visibility

**Not a UI phase.** This audits what an owner/manager/accountant/supervisor/worker can SEE to run the factory — vs what they need. Built on A–G observations + the locked foundation (which *enables* several of these but doesn't itself build the reports). No implementation, no architecture, no new domains — only visibility/report/KPI/alert gaps, ranked by business value.

**One-line answer to "what can't the owner see at 8 AM?":** which Addas are **stalled**, where pieces are being **lost** (stage shrinkage), which stage is the **bottleneck by time**, and **today's production at a glance** — none are surfaced today.

---

## What reporting EXISTS today (verified)
- **Adda Dashboard** (`/production/`): KPI cards (In Progress / On Hold / Completed Today / All Completed) + **In-Progress by Stage** (counts) + Recent Addas + date filter.
- **Costing** (`/production/costing/`): per-Adda MFG cost (Σ frozen `processing_cost`), pieces, worker earnings, "margin gap" (standard-vs-actual labor per ADR-0009), unpriced-stage flags.
- **Payroll Overview** (`/expense/payroll/`): per-worker Pieces / Earned / Advance Out / Settled / **Pending Payable** + Settle action + Total Pending Payable.
- **Settlement queue** (`adda_settlement_service.settlement_queue`): classifies every Adda **ready** (all payable stages done, uncredited lines exist) vs **waiting** (names the blocking stage). Surfaced on the settlements list.
- **Adda History** (`/tracking/history/adda/<code>/`): full audit timeline (settle/supersede/complete/stage-advance/cost-freeze + actor + time).
- **My Earnings** (worker): Pending / Earned / Expected / Advance / Paid + stage-wise + by-Adda.
- **`worker_summary`** (per-worker, on worker detail): pieces, pending payable, last settlement.
- **Recent Activity feed** on the dashboard.

This is a **solid operational base** — better than most early ERPs. The gaps below are the next layer: *time/health/loss/productivity* signals.

---

## HIGH — business-critical visibility gaps

**H-1 — Stage-by-stage loss / shrinkage per Adda is not visible.** *production loss*
- Owner cannot see "Cutting 100 → Stitching 92 → Overlock 89 → Press 87 → Packing 85" for one Adda. Cutting qty IS visible (`pieces_cut`, e.g. 105) and packed qty is captured at settlement (`AddaSettlementItem.packed_quantity`), but **per-stage good/missing/alter does not exist today** (the locked foundation S3 adds it). No "where are pieces lost" view.
- Decision blocked: where to intervene to stop losses; which stage/worker leaks pieces. **The foundation's derived stage-loss read-model is the home for this** — it's a report to build *on* the foundation, not new architecture.

**H-2 — No stalled / inactive-Adda detection.** *adda health*
- Nothing surfaces "this Adda hasn't moved in N days" or "this stage has been open too long." Stage durations are auto-computed (`duration_minutes`) but never aggregated into an aging/stalled signal. The dashboard shows In-Progress **count**, not **health**.
- Decision blocked: the single most important morning question — "what's stuck?" — is unanswerable without clicking every Adda.

**H-3 — No bottleneck-by-TIME view.** *bottleneck detection*
- "In-Progress by Stage" shows **counts** (1 at Layering), not **time** (avg/median stage duration, WIP age per stage). Can't answer "which stage is my bottleneck."
- Decision blocked: where to add capacity / rebalance workers.

**H-4 — No owner operational landing / morning digest.** *decision support*
- Owner lands on the worker-style "My Dashboard" (C-1) showing "No active tasks." The operational Adda Dashboard isn't the default and lacks the morning signals (stalled, due-for-settlement, today's output, advance exposure). There is no single "state of the factory today" surface.
- Decision blocked: a 30-second morning situational read.

---

## MEDIUM — important operational improvements

**H-5 — No cross-worker productivity ranking.** Per-worker `worker_summary` exists, but no leaderboard ("who did the most this week"), and no missing/alter-frequency per worker (needs foundation data). Manager can't compare workers.

**H-6 — No "who hasn't reported" / pending-assignment surfacing.** (Ties Phase-F F-3.) Un-reported assignees are invisible until a stage closes (then auto-cancelled). Manager can't chase pending work.

**H-7 — No advance-exposure overview.** Per-worker advance shows on payroll, but no aggregate "total advances outstanding" or "top debtors" view. Accountant/owner can't see total cash exposure or who carries large balances.

**H-8 — No profitability (cost vs revenue).** Costing shows MFG cost + worker earnings + a labor "margin gap" (standard-vs-actual, ADR-0009) — but **no selling price / revenue linkage**, so **Adda profitability is not computable**. (Commerce↔manufacturing boundary is ADR-0008; not a new domain, a linkage gap.)

**H-9 — Missing-piece / alter COST impact not quantified.** Once good/alter/missing exist (foundation), the *rupee cost* of losses (missing × rate, rejects) should roll up per Adda/stage/worker. Today the loss isn't measured, so its cost can't be.

---

## LOW — nice-to-have reporting

**H-10 — Throughput / cycle-time trend.** Addas completed per week, avg days-to-complete, trend over time. (Dashboard shows point-in-time counts only.)
**H-11 — Cloth utilization / yield.** Layering captures yield data (`LayeringRecord`), not surfaced as consumed-vs-output yield report.
**H-12 — Daily production digest.** A "yesterday/today" summary (completed stages, pieces, settlements) — push/email or a dated card.

---

## OK / WORKS-WELL — existing reporting strengths
- **Adda Dashboard** is a real operational snapshot (KPIs + in-progress-by-stage + recent + filter).
- **Settlement queue (ready/waiting)** already answers "which Addas are waiting for settlement" and **names the blocking stage** — genuinely good.
- **Payroll Overview** answers "which workers are unpaid / pending payable" + total.
- **Costing** transparently separates standard cost vs actual labor (cites ADR-0009) + flags unpriced stages — financially honest.
- **Adda History** gives a complete per-Adda audit trail (also a supervisor tool).
- **My Earnings** gives workers real self-visibility (Expected→Earned→Paid).

---

## Per-role visibility summary

| Role | Has today | Biggest missing |
|------|-----------|-----------------|
| **Owner** | KPIs, costing, payroll totals, settlement queue | Stalled-Adda + bottleneck + morning digest (H-2/3/4); profitability (H-8) |
| **Production Manager** | In-progress-by-stage counts, Adda list/history | Bottleneck-by-time (H-3), who-hasn't-reported (H-6), stage loss (H-1) |
| **Accountant** | (no settlement access — Phase-G G-AUTH-2) cloth-cost only | Advance exposure (H-7), cost variance report, profitability (H-8) |
| **Team Supervisor** | Per-stage roster, Adda history | Worker productivity ranking (H-5), pending reports (H-6) |
| **Worker** | My Earnings, My Queue (badges) | (well served; loss/alter self-view comes with foundation) |

---

## Owner 8 AM — top 10 things to know, and visibility today

| # | What the owner should know at 8 AM | Visible today? |
|---|-----------------------------------|----------------|
| 1 | What's **stalled / not moving** | ❌ (H-2) |
| 2 | **Yesterday's output** (stages completed, pieces) | ❌ (H-12) |
| 3 | Which Addas are **due for settlement** | ✅ (settlement queue) |
| 4 | **Total money owed** to workers (pending payable) | ✅ (Payroll total) |
| 5 | Which **stage is the bottleneck** right now | ❌ (H-3, counts only) |
| 6 | Where pieces are being **lost** (shrinkage) | ❌ (H-1) |
| 7 | **Advance exposure** / who owes a lot | ⚠️ partial (per-worker, no aggregate — H-7) |
| 8 | Which Addas are **in progress + their stage** | ✅ (dashboard / Adda list) |
| 9 | **Profit** on completed Addas | ❌ (H-8) |
| 10 | **Who's working / who's behind** today | ❌ (H-5/H-6) |

**Score: ~3.5 of 10 visible.** The strong ones are money-side (settlement queue, pending payable, in-progress list); the missing ones are **time/health/loss/productivity** — exactly the operational pulse.

---

## Top 10 reports the owner will eventually need (ranked by ROI)

1. **Stalled-Adda alert** (Adda/stage idle > threshold) — *highest ROI; catches stuck money/production daily.* (H-2)
2. **Stage-loss / shrinkage per Adda** (Cutting→…→Packing, missing/alter per stage) — *directly protects margin.* (H-1, needs foundation data)
3. **Owner morning digest** (stalled + due-to-settle + yesterday's output + pending payable on one screen) — *the 30-second factory pulse.* (H-4)
4. **Bottleneck-by-time** (avg/median stage duration, WIP age) — *where to add capacity.* (H-3)
5. **Advance-exposure report** (total outstanding + top debtors) — *cash-flow control.* (H-7)
6. **Worker productivity** (pieces/period ranking + missing/alter frequency) — *performance + quality management.* (H-5, needs foundation data)
7. **Pending-reports queue** (assigned-but-not-reported per active stage) — *chase work before stages close.* (H-6)
8. **Adda profitability** (cost vs sale revenue) — *which products/Addas make money.* (H-8, needs commerce linkage)
9. **Loss-cost rollup** (₹ of missing + rejects per Adda/worker) — *quantify the leak.* (H-9, needs foundation data)
10. **Throughput / cycle-time trend** (Addas/week, avg days-to-complete) — *capacity planning.* (H-10)

> Dependency note: #2, #6, #9 unlock once the locked foundation's good/alter/missing data exists (S3+) — they are **reports over the foundation**, not new architecture. #1, #3, #4, #5, #7, #10 are buildable on **today's** data (timestamps, durations, advances, settlement queue).

---

## Net Phase H
The **money-side** visibility is good (settlement queue, pending payable, costing honesty). The **operational pulse** is missing: stalled/health (H-2), bottleneck-by-time (H-3), stage loss (H-1), morning digest (H-4). Six of the top-10 reports are buildable on today's data; three more arrive free with the foundation's good/alter/missing. **Highest ROI before staging: a stalled-Adda alert + an owner morning digest** — both from data that already exists.
