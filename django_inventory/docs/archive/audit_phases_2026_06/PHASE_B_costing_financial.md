> **ARCHIVED 2026-07-13** — 2026-06 production-readiness audit phase; findings closed, superseded by the current frozen architecture ([../../MANUFACTURING_V1_FREEZE.md](../../MANUFACTURING_V1_FREEZE.md)). Kept for history (Phase-7 DOCCLEAN-D). Its own outbound links reflect the 2026-06 tree.

# Phase B — Costing & Financial Audit (highest priority)

**Method:** code-traced (expense + production services, file:line) + reconciled against **live DB data**. Every number below is from the running system, not assumed. Adda 3-PATTI-001, cutting rate ₹3/piece.

---

## Part 0 — Business deep-dive on A-4 & A-5

### A-4 — Is OPTIONAL verification-before-settlement safe in a real factory?

**No — and the live data proves the leak.** Verification (`AddaReportReviewView` → `set_verified_quantity`) exists and works, but finalize reads `verified_quantity if not None else reported_quantity` ([adda_settlement_service.py:314](config/expense/services/adda_settlement_service.py#L314)). If management skips verification, the worker's **self-declared** number is paid in full.

**Proven on this Adda:** the cutting stage's actual recorded output is **105 pieces** (`CuttingRecord.pieces_cut`), but workers were paid for **120** (utest 60 *unverified* + utest 15 verified + worker2 45 verified). **₹45 was paid for 15 pieces that the stage never produced** — a 14% labor over-cost, traceable entirely to the one unverified line.

**Fraud / risk scenarios:**
1. **Phantom-piece over-reporting.** A worker reports 60, cut 45. If unverified → paid for 60. Repeatable every Adda; small per-Adda, large per-month.
2. **Collusion.** A worker + an unmonitored manager inflate reports; nothing cross-checks against the stage's own output count.
3. **Honest drift.** No fraud — workers estimate high, no one reconciles, the factory silently over-pays and under-prices product (standard cost looks fine; actual labor bleeds).
4. **Disputes.** A worker paid on "reported" later contests a manager's downward correction — no enforced checkpoint, so the record is ambiguous.

**Operational cost of MANDATORY verification:** management must touch every payable contribution before every settlement — real friction for a small team, and the reason it's currently optional.

**Recommendation (cheap, decisive):** don't force full manual verification — instead add a **finalize-time reconciliation gate**. The system *already knows* the true output (`pieces_cut`/handler quantity used for `processing_cost`). At finalize, compare Σ(billed contributions) vs the stage's recorded output; if they differ beyond a small tolerance, **block or hard-warn** ("workers report 120 pcs; cutting recorded 105 — verify before settling"). This catches the exact ₹45 leak with zero per-line manual effort. Effort: **M**.

### A-5 — Consequences of producing & settling when a stage rate is missing

**Current behavior:** an unpriced payable stage freezes `processing_cost = NULL` and pays workers **₹0** silently (succeed-and-flag, [cost_service.py:91](config/production/services/cost_service.py#L91); [flow_service.py:49](config/production/services/flow_service.py#L49)). Production and settlement both proceed.

**Real-world scenarios where an owner forgets a rate:**
1. Adds a new stage (e.g. "Stitching") mid-season, forgets to set the rate → workers stitch all week → settlement pays **₹0** → workers unpaid and angry, or owner reverses + re-settles after the fact.
2. Reactivates/renames a stage and the default rate doesn't carry → silent ₹0.
3. Product costing understates true cost (labor shows ₹0 for that stage) → mispriced quotes.

**Recommendation: block the MONEY event, not production.**
- **Keep** production progression unblocked (a pricing oversight shouldn't halt the floor).
- **Warn** louder than a badge at flow-save (already has the unpriced badge — good).
- **BLOCK finalize** when any `credits_workers=True` stage on the Adda has `cost_rate IS NULL`: "Cutting is unpriced — set a rate before settling." This converts a silent ₹0-payout into a caught, fixable error at the one moment money is booked. Effort: **S–M** (one guard in `create_draft`/`finalize`).

---

## Part 1 — Settlement calculations ✅ correct

Finalize ([adda_settlement_service.py:306-386](config/expense/services/adda_settlement_service.py#L306)): per worker, `worker_expected = Σ(qty × rate)`; `final_payable = worker_expected − recovered` (factory_absorbs), floored at 0; frozen onto `AddaSettlementItem`; `expected_total = Σ worker_expected`. An `assert final_payable == worker_expected − recovered` tie-out guards the snapshot.

**Worked (ADST-0003, utest):** lines 60×3=180 + 15×3=45 → worker_expected **₹225**; recovered 0 → final_payable **₹225**. Matches frozen `final_payable=225`. ✅

## Part 2 — Worker earnings calculations ✅ math correct (⚠️ basis is the issue)

`qty = verified ?? reported`, `rate = expected_rate` (frozen at task-complete, Option B) ([:314-316](config/expense/services/adda_settlement_service.py#L314)). One SWA per contribution line (D-S grain), `earning_amount_snapshot` frozen, `c.settlement_line` stamped for the era-B double-credit guard.

**Worked:** worker2 45×3=**135**; utest 60×3=**180** + 15×3=**45**=**225**. Arithmetic exact. The defect is not the multiply — it's **what `qty` is allowed to be** (see B-1).

## Part 3 — Adda costing calculations ✅ correct (standard cost) — and it exposes B-1

`processing_cost = ws.cost_rate × handler_quantity`, role-independent **standard cost** — explicitly a different measurement from worker pay ([cost_service.py:11-29](config/production/services/cost_service.py#L11), [:84-99](config/production/services/cost_service.py#L84)). Cutting = `per_piece` → `CuttingRecord.pieces_cut`.

**Live data:** `cost_quantity_snapshot=105`, `cost_rate=3` → `processing_cost=315`. Correct. The ₹315-vs-₹360 gap is the **standard-vs-actual labor variance** — legitimate accounting, BUT nothing flags that actual (120 pcs) **exceeds physical output** (105 pcs). That overage is B-1.

## Part 4 — Advance recovery calculations ✅ code-correct (not exercised in data)

Recoveries validated **up-front, under lock**, before any money moves: each `amt ≤ advance_remaining(adv)`, advance must belong to a settled worker ([:288-301](config/expense/services/adda_settlement_service.py#L288)). Then `log_debit(advance_recovery)` + `PayrollSettlementItem`. `final_payable = expected − recovered`.

**Worked (illustrative; no advances in current data):** expected ₹225, recover ₹100 of a ₹150 advance → final_payable **₹125**, advance remaining **₹50**. On reverse, the debit is compensated and the PSI stamped `reversed_at` → outstanding restores to ₹150. ✅ Current data: 0 advances, all `advance_recovered=0`.

## Part 5 — Ledger entries ✅ single-writer, reconciles

All writes go through `ledger_service` (single-writer discipline). Per finalize: one `credit/stage_earning` per line (linked to its SWA). **Net utest = 690 cr − 465 db = ₹225** = finalized `final_payable`. ✅
**Minor (already logged):** `WorkerLedgerEntry.settlement` FK is always NULL; settlement linkage is only transitive (entry→assignment→adda_settlement), and reversal entries link only via `reverses`. No direct "ledger for settlement X" query. Auditability nit. Effort **S**.

## Part 6 — Reverse / supersede flows ✅ verified correct

[adda_settlement_service.py:408-502](config/expense/services/adda_settlement_service.py#L408): (1) each earning credit → compensating debit, `entry_date` copied so it **nets in-period**; (2) each advance-recovery debit → compensating credit + PSI `reversed_at` (append-only, never edited); (3) SWAs soft-voided → re-arms the double-credit guard so a successor can re-credit; (4) frozen `AddaSettlementItem`s untouched (audit record); (5) supersede opens a fresh draft with `supersedes` FK. **No money created or lost; no double-credit possible.**

**Worked (the real chain):** ADST-0001 (₹240) → reversed (−240) → ADST-0002 (₹225) → reversed (−225) → ADST-0003 (₹225, finalized). Ledger nets to ₹225 across two full reversals. ✅

## Part 7 — Financial reconciliation — summary

| Check | Result |
|---|---|
| Settlement final_payable = Σ(qty×rate) − recovered | ✅ ₹225 |
| Ledger net = finalized final_payable | ✅ 690−465 = ₹225 |
| Reversal nets to zero per superseded version | ✅ |
| No duplicate credit (era-A/era-B guards) | ✅ structural + per-row |
| Advance recovery ≤ remaining | ✅ validated under lock |
| **Σ worker piece-reports = physical stage output** | ❌ **120 ≠ 105 (B-1)** |
| Variance policy honored | ❌ hardcoded absorb (B-3) |

---

## Findings

### HIGH

**B-1 — Workers can be paid for more pieces than the stage produced; no output-reconciliation.** *financial control* · confidence HIGH (live data)
- Evidence: `CuttingRecord.pieces_cut = 105`; Σ billed contributions = **120** (utest 60 unverified + utest 15 + worker2 45); paid **₹360** vs standard **₹315**; **₹45 / 15 pieces over physical output.**
- Root cause: finalize sums contributions with no comparison to the stage's own recorded output; verification is optional (A-4). [adda_settlement_service.py:313-337](config/expense/services/adda_settlement_service.py#L313).
- Fix: finalize-time reconciliation gate (Σ contributions vs handler output, tolerance-bounded). Effort: **M**.

### MEDIUM

**B-3 — `variance_policy` is never read; missing AND rejected pieces are always paid.** *financial control* · confidence HIGH
- `variance_policy` field with choices exists ([models.py:432-447](config/expense/models.py#L432)) but is read nowhere; finalize hardcodes `variance_amount=0`, `variance_total=0` ([adda_settlement_service.py:362,382](config/expense/services/adda_settlement_service.py#L362)). Rejected/defective and missing pieces are paid in full.
- Risk: defective output costs the same as good output; no lever to deduct rejects. Fix: either honor `variance_policy` (deduct rejected/missing under a "deduct" policy) or remove the dead field + document "factory always absorbs" as the deliberate rule. Effort: **M** (behavior) / **S** (document).

**B-4 — Ledger→settlement link is only transitive.** *auditability* — see Part 5. Effort **S**.

### INFO / WORKS-WELL

- **Settlement, earnings, advance-recovery, ledger, and reverse/supersede math are all correct and reconcile to the rupee** (Parts 1–7). Strong locking (advisory xact lock + ordered row locks), up-front recovery validation, append-only corrections, single-writer ledger.
- **`processing_cost` (standard) vs settled labor (actual) is a deliberate two-measurement design**, not a bug — but it is the lens that reveals B-1.

---

## Net Phase B

The money **engine** is trustworthy: every calculation reconciles, reversals are clean, no money is created or lost. The risk is at the **input boundary**: workers are paid on un-reconciled self-reports (B-1, proven ₹45 over on one Adda), variance policy is inert (B-3), and an unpriced stage settles to ₹0 (A-5). All three are "the numbers are computed correctly on possibly-wrong inputs." Highest-value fix: the **finalize reconciliation gate** (covers A-4 + B-1) + **block finalize on unpriced payable stage** (A-5).
