# Staging Observation Framework & Tracking Dashboard Spec — 2026-06-14

Companion to [DEPLOYMENT_PACKAGE](DEPLOYMENT_PACKAGE_2026_06_14.md). The soak instrument for the §4 S1 go-gate. **Planning only — no code, no migrations.** Every metric below is derivable from **data the system already records** via read-only `manage.py shell` / SQL queries (the "dashboard" is a spec, not a build — implementing it is post-soak / foundation-adjacent).

**Data anchors (existing):** `WorkerStageTask` (created_at, status, started_at, completed_at, worker, stage_record) · `WorkerStageContribution` (reported_quantity, verified_quantity, expected_rate, settlement_line, created_at, updated_at, color, size) · `AddaStageRecord` (cost_quantity_snapshot = handler output qty, cost_rate_snapshot, completed_at) · `AddaSettlement` (settled_at, expected_total, status) + `AddaSettlementItem` (final_payable, packed/missing/rejected) · `WorkerLedgerEntry` (credit/debit) · `CuttingRecord.pieces_cut`.

---

## 1. Daily observation checklist (≤5 min)
- [ ] **No new 500s** in logs; error reporter quiet (or triaged).
- [ ] Key pages 200 (Operations dashboard, My Dashboard, a settlement detail, My Earnings) — quick canary.
- [ ] **Any settlement finalized today reconciles:** ledger net per worker == `final_payable` (spot-check 1).
- [ ] Operations digest tiles sane vs reality (stalled / pending / payable not absurd).
- [ ] **Stalled tile** — any new stalled Adda? Is it genuinely stuck (vs threshold noise)?
- [ ] **Pending Reports tile** — anyone stuck >1 day un-reported? Chase before stage close.
- [ ] Any worker/manager **friction report** logged (confusion, blocked, mobile pain) → capture verbatim.
- [ ] Note any Adda that **moved stage** today (for cycle-time tracking).

*Record:* one line/day in `SOAK_TRACKER` (date, incidents, settlements done, friction notes).

---

## 2. Weekly observation review template
Roll up the 7 daily entries + compute the three frameworks (§3–5):

```
WEEK OF ____  (staging day N..N+6)
Addas: started __  advanced-a-stage __  completed __  settled __
Settlements: finalized __  reversed/superseded __  reconciled? __/__ (must be all)
Incidents: P0 __  P1 __  (describe)
RC-5 (allocation viability):  pre-assign lead-time median ___h  · multi-worker-per-(color,size) stages __/__  · verdict: PRE-ASSIGN-FITS / AD-HOC / MIXED
RC-6 (verification discipline): contributions verified-before-settle ___%  · downward corrections __  · verdict
B-1 (report-vs-output variance): stages with Σreports>output __/__  · total over-report ₹___  · worst single ₹___
Threshold tuning: STALLED_ADDA_DAYS feels ___ (too low/right/high)
Worker feedback (verbatim): ...
Decision: CONTINUE SOAK / FLAG ISSUE / READY-FOR-S1-GATE
```

---

## 3. RC-5 framework — Strict-allocation viability
**Question:** does management pre-assign work per stage (Strict fits), or is the floor ad-hoc ("grab a bundle")?

**Metrics (existing data):**
- **Pre-assignment lead time** = `first contribution.created_at (or task.started_at) − task.created_at` per task. Large lead ⇒ assigned *ahead* (Strict-friendly); ≈0 ⇒ task created at report time (ad-hoc).
  - *Query:* per `WorkerStageTask`, `min(contributions.created_at) - task.created_at`. Report median + % with lead > 2h.
- **Color/size contention** = stages where the SAME `(color,size)` is reported by >1 worker. High ⇒ no clean per-worker split ⇒ Strict needs real allocation discipline (or hurts).
  - *Query:* group `WorkerStageContribution` by `(stage_record, color, size)`, count distinct workers > 1.
- **Roster churn** = workers added to a stage *after* others already reported (reactive add).
- **Qualitative:** ask the manager each week — "did you tell a specific worker which color/size/qty before they started?" (yes/no/sometimes).

**Verdict scale:** PRE-ASSIGN-FITS (lead high, low contention) → Strict mode ships as locked · AD-HOC (lead ≈0, high contention) → revisit Open mode (future ADR) before S5 · MIXED → Strict default + Open escape hatch.

---

## 4. RC-6 framework — verification-before-settlement discipline
**Question:** is management actually verifying quantities (`review-reports/`) before finalize — the premise that makes the over-report risk process-mitigable?

**Metrics (existing data):**
- **Verified-before-settle %** = of the contributions a settlement paid (via `settlement_line` → SWA → contribution), how many had `verified_quantity` set with `updated_at < settlement.settled_at`.
  - *Query:* for each finalized `AddaSettlement`, its settled contributions; `verified_quantity is not null AND updated_at <= settled_at` ÷ total.
- **Downward corrections** = count of settled contributions where `verified_quantity < reported_quantity` (over-reports actually caught). >0 proves the gate is *working*; =0 with high reported≠output (§5) proves it's being *skipped*.
- **Time-to-verify** = `verification updated_at − task.completed_at` (how long management takes).

**Verdict scale:** STRONG (≥~80% verified-before-settle, downward catches present) → over-report risk genuinely mitigated; foundation is hardening, not rescue · WEAK (<~50%) → real workers being paid on self-reports → **B-1 is live in production**, raises foundation urgency.

---

## 5. B-1 framework — report quantity vs actual production variance
**Question:** how often, and by how much, does Σ(worker piece-reports) exceed the stage's recorded output? (The leak: 120 paid vs 105 cut = +₹45 on the demo Adda.)

**Metrics (existing data):**
- **Per-stage variance** = `Σ(billed contribution qty) − AddaStageRecord.cost_quantity_snapshot` (the handler output: `pieces_cut` etc.), where billed qty = `verified_quantity ?? reported_quantity`.
  - *Query:* per payable `AddaStageRecord` (credits_workers, completed): `Σ contributions billed − cost_quantity_snapshot`. Positive = over-report.
- **Leak frequency** = % of payable stages with variance > tolerance (e.g. >0, or >2%).
- **₹ impact** = `variance × cost_rate_snapshot`, summed across the soak; + worst single.
- **Trend** = does it shrink as RC-6 discipline rises? (cross with §4.)

**Output:** a running tally — `stages_over / stages_total`, `total_₹_over`, `worst_₹`. This sizes the foundation's payoff: high frequency/₹ ⇒ S5 (allocation-bounded reporting) is high-ROI; near-zero (because RC-6 is strong) ⇒ foundation is preventive insurance.

---

## 6. Foundation readiness scorecard — objective S1 go/no-go
Fill during soak; **S1 starts only when every row is GO.**

| # | Criterion | Metric (existing data) | GO threshold | Current |
|---|-----------|------------------------|--------------|---------|
| 1 | End-to-end proven | Addas completed through settlement | **≥ 2–3**, money reconciled **100%** | ___ |
| 2 | Money integrity | settlements reconciled (ledger net == final_payable); reversals net 0 | **100%**, zero mis-book | ___ |
| 3 | RC-6 measured | verified-before-settle % over ≥ ~5 settlements | **measured + verdict recorded** (not a min %, but the decision made) | ___ |
| 4 | RC-5 answered | lead-time + contention + manager Q | **verdict recorded** (fits / ad-hoc / mixed) → Strict-vs-Open decision locked | ___ |
| 5 | B-1 quantified | over-report frequency + total ₹ | **measured** (frequency + ₹ known) | ___ |
| 6 | Stability | P0-class incidents (500 / money mis-book / access leak) | **0** during window | ___ |
| 7 | Thresholds tuned | STALLED_ADDA_DAYS + digest/queue calibration | **confirmed with the owner** | ___ |
| 8 | Window | calendar | **≥ 2 weeks**, ≤ ~4 weeks | ___ |

**Go/no-go rule:** all 8 GO → start S1. Any NO-GO → continue soak (or, for #4 AD-HOC, raise the Open-mode question before S5). The scorecard is *evidence-gated*, not calendar-gated (§4 of the deployment package): criteria 3–5 are the ones Option-B staging exists to answer.

**Critical interlock:** if #6 fails on a *money* incident, or #5 shows a large live B-1 leak with #3 WEAK, that strengthens (not delays) the case for S1 — the foundation is the fix. Record the reasoning; don't let a scary number both delay the fix AND keep the leak open.

---

## Dashboard spec (what to build later — NOT now)
A read-only "Soak Monitor" page (post-soak / foundation-adjacent) would surface §3–5 as live panels: RC-5 lead-time histogram, RC-6 verified-%-trend, B-1 variance-per-stage table + ₹ running total, plus the §6 scorecard auto-filled. Until built, run the documented queries weekly and record in `SOAK_TRACKER`. No code now.
