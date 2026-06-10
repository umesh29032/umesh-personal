# Worker Ledger + Settlement Architecture

> ⚠️ **STATUS CORRECTION + SUPERSESSION (2026-06-09):** the models below (`PayrollSettlement`,
> `PayrollSettlementItem`, ledger) are **BUILT and LIVE** (this header's "PROPOSED" is stale). This doc
> describes the **worker-centric** settlement (1 worker : 1 payout, anytime). The **Adda-centric**
> settlement direction is now LOCKED in [../ARCHITECTURE_V2.md](../ARCHITECTURE_V2.md) **§11** —
> **Option B** (earnings booked only at settlement), **Model A** (settlement ≠ payment: settlement books
> earning credit + advance-recovery debit; cash payout is the separate worker-centric flow here), and a
> new `AddaSettlement` event that **WRAPS** this worker-centric `PayrollSettlement` (which becomes the
> payment record). Where this doc and ARCHITECTURE_V2 §11 differ, **§11 is the locked target.**

**Status:** BUILT/LIVE (worker-centric); Adda-centric direction LOCKED in ARCHITECTURE_V2 §11.
**Supersedes:** the payment half of `PAYROLL_ARCHITECTURE.md` (`WorkerPayment` → `PayrollSettlement`).
**Superseded-for-direction-by:** `ARCHITECTURE_V2.md` §11 (Adda-centric, Option B, Model A).
**Date:** 2026-06-02 (banner updated 2026-06-09)

This is **NOT** a monthly payroll system. Workers earn from production work; the
owner settles **whenever they decide** (today / +10 days / month-end). The system
is a **Worker Ledger + on-demand Settlement** flow.

---

## 0. What already exists (reuse as-is)

The `expense` app (built last session) already gives us most of this:

| Built | Role in the new design |
|---|---|
| `StageWorkAssignment` | Earnings source. `Worker → Bundle → Size → Color → Pattern → bundle_item → qty × rate`. Already supports the future multi-worker / piece-wise grain **without redesign**. |
| `WorkerLedgerEntry` | The append-only ledger. `balance = Σcredit − Σdebit`, never stored. Reversal-based corrections, one-reversal-per-entry DB constraint. |
| `WorkerAdvance` | Immutable advance record (+ attachment). |
| `ledger_service` | Sole writer. `log_credit / log_debit / reverse_entry / worker_balance`. |
| `payroll_service` | Read-only derived aggregations + `can_view_worker` scoping. |

So this is **mostly an additive change**, not a rewrite. Two things change; two
models get added.

---

## 1. Architecture diagram

```
PRODUCTION                         EXPENSE (payroll)
──────────                         ─────────────────
Adda → WorkflowStage                StageWorkAssignment ──credit──┐
  → AddaStageRecord  ──allocate──▶  (qty × rate, frozen)          │
                                                                  ▼
WorkerAdvance  (separate loan account, NOT on payable ledger)   WorkerLedgerEntry
      │                                                          (PAYABLE account)
      │ recovered at settlement (owner's choice)                  ▲   ▲   ▲
      ▼                                                           │   │   │
  PayrollSettlement ──┬─ advance_recovery debit ──────────────────┘   │   │
  (the payout event)  ├─ settlement_payment  debit ───────────────────┘   │
                      └─ PayrollSettlementItem (per-advance recovery line)─┘
```

Two **derived** numbers, never stored:
- **Pending Payable** = `Σ credits − Σ debits` on the ledger (earnings the factory still owes).
- **Advance Outstanding** = `Σ WorkerAdvance.amount − Σ advance_recovered` (separate loan pool).

---

## 2. Model design

### 2a. CHANGED — advance no longer auto-debits payable
`advance_service.record_advance` **stops** booking the `ADVANCE` debit on the
payable ledger. An advance is a separate loan, recovered at settlement by the
owner's choice — not an automatic reduction of what the worker earned.
`WorkerAdvance` row stays exactly as is.

### 2b. NEW — `PayrollSettlement` (the payout event, immutable)
```python
class PayrollSettlement(TimeStampedModel):
    reference        = CharField(unique=True)        # SETL-0001, auto
    worker           = FK(User, PROTECT)
    settlement_date  = DateField()
    # Snapshots frozen at settlement time (audit; never recomputed):
    payable_before   = DecimalField()                # pending payable at the moment
    advance_outstanding_before = DecimalField()
    advance_deducted = DecimalField()                # owner's choice, 0..min(adv,payable)
    amount_paid      = DecimalField()                # cash actually handed over
    method           = CharField(cash/bank/upi/other)
    notes            = TextField(blank=True)
    created_by       = FK(User, PROTECT)
    # Invariant: amount_paid + advance_deducted == payable_before  (full settle)
    #            (partial settle allowed → remaining stays on ledger)
```

### 2c. NEW — `PayrollSettlementItem` (advance-recovery lines, OWNER-controlled)
```python
class PayrollSettlementItem(models.Model):
    settlement      = FK(PayrollSettlement, PROTECT, related_name='items')
    advance         = FK(WorkerAdvance, PROTECT, related_name='recoveries')
    amount_recovered= DecimalField()
    # One line per advance the owner chose to recover from. The settlement
    # screen shows a TABLE of every outstanding advance (date, amount, already
    # recovered, remaining) and the owner types how much to recover from EACH —
    # decides per-advance what to clear vs leave outstanding (D3). NOT auto-FIFO.
    # advance_deducted (header) == Σ amount_recovered across these lines.
    # Guard: amount_recovered ≤ that advance's remaining.
```

### 2d. `WorkerLedgerEntry` — add link + categories
- Add `settlement = FK(PayrollSettlement, PROTECT, null=True, related_name='+')`.
- New categories: `SETTLEMENT_PAYMENT` (debit), `ADVANCE_RECOVERY` (debit).
- `ADVANCE` category is retired from the payable ledger (advances live only in `WorkerAdvance`).

### 2e. `WorkerPayment` — DEPRECATED → removed
Replaced by `PayrollSettlement` (a settlement *is* the payout). Only seeded test
rows exist, so safe to drop. "Record Payment" sidebar item → "Start Settlement".

### 2f. NEW — `WorkerProfile` (one-to-one with User) — BUILD NOW (D4)
Per-worker payroll metadata, kept lean (NO stored totals — those stay derived):
```python
class WorkerProfile(TimeStampedModel):
    user                = OneToOneField(User, PROTECT, related_name='worker_profile')
    phone               = CharField(blank=True)
    bank_account_name   = CharField(blank=True)
    bank_account_number = CharField(blank=True)
    bank_ifsc           = CharField(blank=True)
    upi_id              = CharField(blank=True)
    joining_date        = DateField(null=True, blank=True)
    opening_advance     = DecimalField(default=0)   # advances given pre-system
    is_active           = BooleanField(default=True)
    notes               = TextField(blank=True)
```
`opening_advance` seeds Advance Outstanding for workers who had loans before the
system. Management-editable from the worker detail page. Auto-created on demand
(`get_or_create`) so existing workers don't need a backfill.

---

## 3. Ledger design (the PAYABLE account)

| Direction | Category | When |
|---|---|---|
| CREDIT | `stage_earning` / `production_earning` | worker allocated work (existing) |
| CREDIT | `adjustment` (+) | manual correction up |
| DEBIT  | `settlement_payment` | cash paid at a settlement |
| DEBIT  | `advance_recovery` | earnings used to repay advance at a settlement |
| DEBIT  | `deduction` | penalty / correction down |
| —      | `reversal` | opposite-direction undo (existing) |

**Pending Payable** = `Σcredit − Σdebit` (unchanged formula; `worker_balance`).
**Total Earned** = `Σ credit(stage_earning, production_earning)` net of reversals.
**Total Settled (cash, lifetime)** = `Σ debit(settlement_payment)`.
**Advance Outstanding** = `Σ WorkerAdvance.amount − Σ PayrollSettlementItem.amount_recovered`.

All derived. Nothing stored. No balance is ever UPDATE'd.

---

## 4. Settlement design (the "Start Settlement" flow)

Owner-driven, any time. Per-worker (batch view lists all workers, drill into one).

```
1. Owner opens Payroll → sees every worker:
   Name | Total Earned | Advance Outstanding | Already Settled | Pending Payable
2. Owner clicks a worker → "Start Settlement":
   shows Adda-wise + stage-wise earnings, advance history, prior settlements,
   current Pending Payable + Advance Outstanding.
3. Owner sets `advance_deducted` (0 ≤ x ≤ min(advance_outstanding, payable)).
   System computes amount_paid = payable − x  (live preview).
4. Owner confirms (one atomic transaction):
     • PayrollSettlement row (snapshots payable_before, advance_outstanding_before).
     • DEBIT settlement_payment = amount_paid       (ledger, settlement FK)
     • DEBIT advance_recovery   = x                 (ledger, settlement FK)  [if x>0]
     • PayrollSettlementItem rows = the owner's explicit per-advance recovery amounts (D3 — NOT auto-FIFO; each ≤ that advance's remaining).
5. Result: Pending Payable → 0 (fresh overview). Advance Outstanding −= x.
   Worker dashboard instantly shows the new settlement in history.
```

Worked example (the brief's numbers): earned ₹7000, advance outstanding ₹5000.
- Owner deducts ₹5000 → `amount_paid = 2000`, advance outstanding → ₹0, payable → ₹0.
- Owner deducts ₹3000 → `amount_paid = 4000`, advance outstanding → ₹2000, payable → ₹0.
- Owner deducts ₹0 → `amount_paid = 7000`, advance outstanding stays ₹5000, payable → ₹0.

**Partial settlement** (optional): allow `amount_paid < payable − x`; remaining
just stays on the ledger as still-payable. Recommend supporting it (owner may pay
part now). Defaults to full.

**Immutability:** a settlement is never edited. A mistake = a `reversal` of its
ledger debits + a fresh settlement (same discipline as the rest of the ledger).

---

## 5. Advance design

- `WorkerAdvance` unchanged (immutable, attachment, audit).
- Recording an advance **no longer** posts to the payable ledger (§2a).
- Advances are recovered **only** at settlement, by the owner's explicit amount.
- Per-advance remaining = `advance.amount − Σ its PayrollSettlementItem.amount_recovered`
  (plus `WorkerProfile.opening_advance` in the worker's total outstanding).
- **Owner-controlled recovery (D3):** settlement screen lists every outstanding
  advance; owner types how much to recover from each (≤ its remaining) and what to
  leave. No auto-FIFO — full control on settlement day.

---

## 6. Security design

- Worker self-view (`/expense/my/`): self-scoped (`request.user`), **login-only,
  no role gate** — payroll is critical, never gate a worker out of their own money.
- Sidebar: "My Earnings" under **Main** for everyone; the Payroll section
  (overview + advances + settlements) is **MANAGEMENT_ROLES only**. (Done.)
- `can_view_worker`: own = yes; management/`view_all_payroll` = all; else 403.
- Settlement create / advance create = `MANAGEMENT_ROLES` (service-layer `_ensure_management`).
- **Manager-team scoping** (manager sees only assigned workers) = future seam:
  add `supervised_workers` M2M, branch `can_view_worker`. Not built now; manager = all.

---

## 7. Mobile UX (worker dashboard, mobile-first, no big tables)

Cards (existing `my_earnings.html` already has 5 — re-point semantics):
1. **Pending Payable** (hero)
2. **Total Earned**
3. **Advance Outstanding**
4. **Last Settlement** (date + amount + reference)
5. **Recent Addas** (count)

Below: **Adda breakdown** list (Adda · stage · pieces · ₹ · status) — already built
(`worker_adda_earnings`). Plus **Settlement history** list (date · paid · advance
deducted · reference). Stage-wise rollup already built.

Admin: all-workers table → drill-in → Start Settlement screen.

---

## 8. Migration plan (additive, dev DB)

1. `expense/0004` — add `PayrollSettlement`, `PayrollSettlementItem`,
   `WorkerLedgerEntry.settlement` FK, new categories. Drop `WorkerPayment`.
2. `expense/0005` (data) — reverse existing `ADVANCE`-category ledger debits
   (append a reversal each) so old advances stop reducing payable under the new
   semantics; the `WorkerAdvance` rows remain as outstanding. (Seeded test data is
   disposable — alternatively just clear `wa-audit`/`wb-audit` ledger + re-seed.)
3. No production data exists yet → low risk. Run `migrate` after (lesson learned).

---

## 9. Rollback plan

All uncommitted on `new_flask_app`. To revert:
- `migrate expense 0003` (drops settlement models + settlement FK; restores `WorkerPayment`).
- `git restore` the changed services/views/templates + `permission_service.py`.
- Delete new migration files.
- Per-piece rollback possible — the settlement layer is additive over the existing ledger.

---

## 10. Scalability review

- Ledger reads are per-worker, indexed (`worker, -created_at` / `entry_type` / `category`). O(rows-per-worker).
- Settlement batch view (all workers) = one grouped aggregate, not N queries.
- Future allocation grain (multi-worker, bundle/size/color/piece) **already
  modelled** in `StageWorkAssignment` — no schema change to scale the earning side.
- Multi-factory / attendance / machine tracking = additive FKs later; the
  ledger + settlement core is factory-agnostic.

---

## Decisions — RESOLVED (owner, 2026-06-02)

- **D1 Manufacturing-cost link:** ✅ keep per-Adda cost = `Σ(stage rate × qty)`
  frozen + immutable; show wages actually paid as a separate factory-level figure.
- **D2 Partial settlement:** ✅ allowed; form defaults to full payable.
- **D3 Advance recovery:** ✅ **owner-controlled per-advance** — settlement screen
  shows a table of all outstanding advances; owner decides how much of each to
  recover vs leave. NOT auto-FIFO.
- **D4 `WorkerProfile`:** ✅ build now (§2f) — bank/UPI/joining/opening-advance.
```
