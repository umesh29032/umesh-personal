# Production Operations Certification — can a real factory run a full day on this ERP?

**Date:** 2026-07-20
**Lens:** operational, not feature. Owner / Manager / Supervisor / Worker / Finance / QA each try to finish a real day's responsibilities. Every important number is cross-checked across every surface. Brutal honesty on what breaks on day one.
**Method:** leveraged the 5 prior certifications (Manufacturing, UAT, Adversarial, Browser-Functional, Interactive-UI) + new operational verification: money reconciliation across models/surfaces, owner-dashboard trust, finance settlement/export/history, long-run list (26 Addas), empty-state/search/filter. Real browser + authenticated queries. **No Git commit; production data untouched.**

---

## EXECUTIVE SUMMARY

**The core daily loop is operationally sound and the money reconciles.** A garment factory CAN run a working day on this ERP: the owner sees production + cost + payable, the manager allocates + monitors + corrects, workers report on phones, QC corrects counts, finance settles + exports, and the numbers agree across screens. **Manufacturing cost == frozen expected earnings to the exact rupee** (₹633.75 == ₹633.75 on the settled 3-PATTI-016), and settlement correctly pays the verified quantity.

**But it is NOT a zero-problem deploy.** There is **one MUST-FIX before go-live** (BUST-B1, adda-creation can wedge — already fixed, needs commit), one **accountability decision** (workers can see their allocated target — F1), one **finance-clarity risk** (Expected ≠ Settled when QC corrects a count, with no visible correction trail on the earnings screen), one **config risk** (a cutting rate looks mis-seeded at ₹100/piece), and several **training/UX** items. There is also **no consolidated production/financial summary report and no revenue/profitability** — the owner reconstructs the picture across screens and sees labor cost, not profit.

**Deploy verdict: GO for the production floor after 3 pre-flight fixes (commit BUG-B1, verify stage rates, decide F1). The daily operation works; the gaps are reporting/clarity/training, not data corruption.**

---

## DATA RECONCILIATION (the operational-trust crux)

Cross-checked on a completed + settled Adda (**3-PATTI-016**):

| Surface | Number | Source |
|---|---|---|
| Manufacturing cost (Σ frozen stage processing_cost) | **₹633.75** | `AddaStageRecord.processing_cost` |
| Expected worker earnings (Σ frozen `expected_earning`, credited stages) | **₹633.75** | `WorkerStageContribution` |
| Settlement paid (Σ `final_payable`) | **₹633.00** | `AddaSettlementItem` |
| Settlement internal (expected == payable + advance) | ✅ balances | settlement |

- **Manufacturing cost == frozen expected earnings: EXACT** (₹633.75). Every rupee traces to good × configured stage rate. ✅
- **Settlement (₹633.00) is ₹0.75 LESS than frozen expected (₹633.75)** — isolated to one worker (checker dev.chk.a): reported good = 21 on Red/Size-1, **verified = 20** (a QC report-review correction). Settlement correctly pays the **verified** quantity (20 × ₹0.75); the "Expected Earnings" figure is the **frozen pre-correction** number (21 × ₹0.75). **This is BY DESIGN and mathematically correct** (settlement pays verified; expected is a frozen visibility snapshot).
- **Operational risk (MEDIUM, OPS-1):** a finance person reconciling "Expected vs Settled" sees a mismatch, and a worker told "expected ₹41.25" is paid ₹40.50 — **correct, but confusing without a visible correction trail** ("21 reported → 20 verified → paid 20") on the earnings/settlement screen. The data exists (`verified_quantity`); it is just not surfaced as an explanation.

**Verdict:** numbers reconcile; the only cross-surface delta is an intentional, correct QC correction. Surface the correction so finance/workers trust it.

---

## ROLE-BY-ROLE

### 1. Factory Owner — can finish the day? **YES, with two gaps**
- **Works:** Production Dashboard (KPI cards — Pending Reports 12, **Pending Payable ₹5857.75**, Advance ₹70; stage-distribution + **stalled Addas "no move 3+ days"** for bottlenecks); per-Adda A360 (12/12 stages, expected/settled/labor); Snapshot (per worker × bundle); Manufacturing Costing. All render clean, KPIs computed live.
- **Trust:** cost + expected reconcile to the rupee.
- **Gaps:** (a) **no single "final production summary / P&L" report** — the owner pieces together production + cost + earnings across 4 screens; (b) **no revenue/profitability** — the ERP tracks manufacturing **labor cost**, not profit (raw-material/fabric cost is out of production scope, and no sale price) — so "review profitability" is only partially answerable (labor cost only).
- **Confusion risk:** Expected (₹9,636.50) vs Settled vs Standard-Labor (₹17,136.50) on A360 are three different numbers on one card — needs a legend/training.

### 2. Production Manager — **YES, with friction**
- **Works:** start stage, skill-filtered worker assignment, whole/partial/void/reallocate bundle allocation, live board, reopen, complete, snapshot monitoring, delayed-work view. All exercised end-to-end in prior certs.
- **Friction (OPS-2):** pool stages are a **two-step** (roster the worker, THEN allocate bundles) — not obvious to a new manager. Pre-production has **multi-gate completion** (layering needs plies + leftover-weight per roll; pattern needs designs verified + photo + sizes-locked + worker checklist; cutting needs the worker's report) — each gate blocks with a clear message, but a new manager will hit several "why can't I complete?" moments. **Training + a one-page cheat-sheet needed.**

### 3. Floor Supervisor — **MOSTLY YES**
- **Works:** Snapshot shows who's working / done / pending / remaining per worker × bundle + progress %; dashboard stage-distribution shows where work is piled; stalled-Adda list flags no-movement.
- **Gap:** bottleneck detection is **per-Adda / manual** — no single "which stage across all Addas is the constraint today" view; supervisor scans the dashboard counts. Adequate, not great.

### 4. Worker — **YES**
- **Works:** think-free My Assigned Work (bundle cards, no colour/size selection), report Good/Alter/Missing/Damaged on a phone, blind report-entry form (no `max=`), task auto-completes, view earnings.
- **Risk (F1, HIGH — carried, OPEN):** the My Assigned Work dashboard **shows ALLOCATED + REMAINING** — the worker sees the target. Contradicts the owner's blind-accountability rule; a worker could report to the target. **Decide: hide it or accept it.**

### 5. Finance Executive — **MOSTLY YES**
- **Works:** settlement finalization, settlement **history page** (24 settlements, ADST refs, 200/clean), CSV/XLSX/PDF export (POST 200, recorded in export history), advance recovery, per-worker payable, audit fields (`verified_quantity`, `settled_by`, `settled_at`).
- **Reconciles:** settlement = Σ (verified × rate) − advance; internally balanced.
- **Gaps:** (a) **OPS-1** Expected-vs-Settled correction gap needs a visible trail; (b) no single consolidated financial report (per-Adda + per-worker + per-period roll-up in one export).

### 6. Quality Inspector — **YES**
- Checking stage + report-review verified-quantity correction works and flows to settlement (the ₹0.75 gap is literally a QC correction taking effect). Alter/Missing/Damaged captured. **Gap:** alter/missing/damaged are **dead-end observations** — no rework/recovery lifecycle (a "recovered" figure is a hard-coded zero); a real factory that re-works altered pieces has no flow for it yet.

---

## LONG-RUN / EMPTY / SEARCH / FILTER
- **Long-run:** Adda list renders 26 Addas cleanly with 2 filter selects; `?status=completed` → 12 rows; usable with accumulated history. ✅
- **Empty state:** filtering to a non-existent stage → graceful "no Adda" message, no crash. ✅
- **Filter:** status/stage server-side filters work (query-param based). ✅
- **Search:** the Adda list is **filter-select-based, not free-text search** — a manager looking for "3-PATTI-014" filters by status/stage or scans; no partial/fuzzy text search box on the production Adda list (minor OPS-3).
- **Reporting/exports:** barcode CSV/XLSX/PDF + settlement exports work + are recorded in history; repeated export OK.

---

## OPERATIONAL BLOCKERS / BUSINESS RISKS (brutal)

| ID | Severity | Issue | Impact | Fix status |
|---|---|---|---|---|
| **BUG-B1** | **MUST-FIX pre-deploy** | Adda-create 500s + wedges if the per-product counter desyncs from real codes (any out-of-band insert: migration, import, script) | Manager cannot create new Addas — production stops | **Fixed, NOT committed** — commit before deploy |
| **F1** | HIGH | Worker sees ALLOCATED/REMAINING on My Assigned Work | Accountability rule broken; worker can report to target | Open — owner decision |
| **OPS-1** | MEDIUM | Expected ≠ Settled after a QC correction, with no visible correction trail | Finance/worker confusion, support calls, trust dip | Open — surface the 21→20 trail |
| **Cutting rate** | MEDIUM | Cutting seeded at ₹100/piece (cost ₹15,000 vs worker earn ₹7,500 on the UAT Adda) | Wrong pay/cost if used in real production | Verify ALL stage rates before go-live |
| **OPS-2** | MEDIUM (training) | Two-step roster+allocate + multi-gate pre-production | New managers confused; support calls week 1 | Training + cheat-sheet |
| **No summary/P&L** | MEDIUM | No consolidated final production summary; no revenue/profitability | Owner reconstructs across screens; can't see profit | Build a report (data exists; ~70% in A360) |
| **Snapshot live-not-frozen** | LOW | Snapshot recomputes; a reopen/correction changes it | No permanent stage "certificate" | Additive (StageCompletionSnapshot) |
| **Rework/recovery** | LOW | Alter/missing/damaged go nowhere | Can't track recovered pieces | Additive module |
| **F2** | LOW | Login redirects when already authenticated | Shared floor-device friction | Open |
| **A11y/cross-browser** | UNKNOWN | Not tested (headless Chromium only) | Unknown on older Android/other browsers | Test before public release |

---

## WORKFLOW FRICTION / UX
- Two-step allocate; multi-gate pre-production (see OPS-2).
- Three money words on one A360 card (Expected / Settled / Standard-Labor) without a legend.
- No free-text Adda search (filter-only).
- Expected-vs-verified-vs-settled distinction is correct but unexplained on-screen (OPS-1).

## Recommendations (pre-deploy, ordered)
1. **Commit BUG-B1** (adda-create counter-skip). Non-negotiable.
2. **Audit every stage rate** in the flow editor (the ₹100/piece cutting rate is almost certainly wrong).
3. **Decide F1** — hide ALLOCATED on the worker card, or accept it as intended.
4. **Surface the QC-correction trail** on earnings/settlement (reported → verified → paid) to kill OPS-1 confusion.
5. **Supervisor cheat-sheet** for the two-step allocate + pre-production gates.
6. (Post-launch) build a consolidated production/financial summary; decide if profitability (needs sale price) is in scope.

---

## FINAL QUESTION — "If I deploy tomorrow, what operational problems will the factory experience?"

**Brutally honest, with evidence:**

1. **A wedged Adda-create the first time any data goes in out-of-band** (BUG-B1) — the manager gets a 500 and cannot start new production until the counter is fixed. **This will happen; commit the fix first.** (Evidence: reproduced live — `IntegrityError` on `3-PATTI-016` collision.)
2. **Wrong cutting pay/cost** if the ₹100/piece cutting rate ships as-is (Evidence: UAT Adda cutting cost ₹15,000 vs worker earn ₹7,500). **Verify rates.**
3. **Finance and workers will ask "why is my expected ₹41.25 but I was paid ₹40.50?"** — the answer (a QC verified-count correction) is correct but invisible on-screen (Evidence: 3-PATTI-016 checker, reported 21 → verified 20). **Support calls until the correction trail is shown.**
4. **Workers can see their target** (F1) — quietly erodes the blind-accountability the owner wanted (Evidence: pj1's card shows "ALLOCATED 75").
5. **Week-one manager confusion** on the two-step allocate + pre-production gates — not broken, but "why can't I complete this stage?" moments (Evidence: layering/pattern/cutting each blocked completion until a specific gate was satisfied, with clear messages).
6. **The owner cannot pull one production/financial summary or see profit** — only per-stage/per-screen labor numbers. Not a blocker, but not the "one dashboard tells me everything" an owner expects.

**What will NOT break:** data integrity, money math, allocation accountability (server-side bound), access control, worker reporting, settlement reconciliation, and every production page's functional health — all proven across the prior certifications and re-confirmed here. **No corruption, no double-pay, no leak, no dead workflow in the core loop.**

**Bottom line:** commit BUG-B1, verify rates, decide F1 — then a real garment factory can run its day on this ERP. The remaining items are reporting, clarity, and training, not a broken factory.

---

## STOP — awaiting manual audit
No Git commit. All production data intact. Awaiting your inspection.
