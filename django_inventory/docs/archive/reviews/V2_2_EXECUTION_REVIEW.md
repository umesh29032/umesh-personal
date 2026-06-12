> **📦 ARCHIVED 2026-06-12.** Historical record — do not update.
> Superseded by / live truth: [docs/ARCHITECTURE_V2.md §11](../../ARCHITECTURE_V2.md) + [ADR-0007](../../adr/0007-allocation-era-ledger-cutover.md).

# V2-2 Execution Review — AddaSettlement (settlement-time financial truth)

**Date:** 2026-06-11 · **Status: REVIEW ONLY — no code. Verdict in Part 12.**
Inputs: ARCHITECTURE_V2 §11 (🔒 locked, field-level), ADR-0007 (🔒 Option A),
ADR-0008 (🔒), R0 C5 (reverse_settlement folds in here), R1 I-invariants,
post-V2-1d truth model, live service APIs (ledger/settlement/allocation), and
the dev DB's REAL cross-era fixture (3-PATTI-001: worker2 holds a ₹135
allocation-era credit + ₹150 expected — the ADR-0007 guard's living test case).

---

## Part 1 — Current state (money, post-V2-1d)

- **Production truth (done):** WorkerStageTask + WSC sole truth; completed
  contributions carry frozen `expected_rate/expected_earning` (visibility, no
  ledger — ADR 0005).
- **Live money path (pre-V2, still on):** `allocation_service.allocate_stage_work`
  → SWA row + immediate `STAGE_EARNING` credit (ledger_service.log_credit:110).
- **PayrollSettlement (pre-V2):** one atomic settle+pay+recover —
  `create_settlement(user, worker, amount_paid, recoveries)` posts
  SETTLEMENT_PAYMENT + ADVANCE_RECOVERY debits, writes PayrollSettlementItem
  recovery lines, pays cash. No reversal for recovery lines (the known gap).
- **Ledger:** `WorkerLedgerEntry` (entry_type credit/debit, category ∈
  STAGE_EARNING/ADVANCE(legacy)/SETTLEMENT_PAYMENT/ADVANCE_RECOVERY/…),
  amounts always positive, balance = live SUM, single writer `ledger_service`
  (`log_credit/log_debit/reverse_entry/worker_balance`).
- **Gate to settlement-readiness already built by F3/F8:** when a stage
  completes, every task is completed or cancelled — so "all payable stages'
  active tasks completed" (the §11.5 draft gate) holds BY CONSTRUCTION for
  completed Addas. The lifecycle fix was quietly V2-2 prep.

## Part 2 — Exact model design (expense app; all per locked §11.3/11.4)

**`AddaSettlement`** — `reference` CharField unique (ADST-####, counter under
the shared advisory lock 5374, mirroring SETL) · `adda` FK PROTECT ·
`status` ∈ draft/finalized/reversed/superseded (draft default) ·
`variance_policy` (frozen at finalize; launch value `factory_absorbs`) ·
frozen audit totals: `expected_total, packed_total, missing_total,
rejected_total, alter_total, variance_total` · `settled_at/settled_by` ·
`supersedes` self-FK null + `reversed_at/reversed_by` · TimeStampedModel.
CheckConstraints: totals ≥ 0; status-vs-timestamps coherence (finalized ⇒
settled_at NOT NULL). Index `(adda, -settled_at)`; **NO unique(adda)** —
partial settlements legal.

**`AddaSettlementItem`** (append-only, never recomputed) — `adda_settlement`
FK CASCADE-protect? → PROTECT (financial snapshot) · `worker` FK PROTECT ·
optional `stage_record` FK PROTECT · frozen: `expected_earning,
advance_outstanding_before, advance_recovered, final_payable, variance_amount,
packed_quantity, missing_quantity, rejected_quantity, alter_quantity,
settled_at, settled_by` · `earning_assignment` FK → the settlement-written SWA
(closes the audit loop item↔SWA↔credit). Checks: all amounts/qtys ≥ 0;
`advance_recovered ≤ advance_outstanding_before`.

**`PayrollSettlementItem.adda_settlement`** — nullable FK (new recovery lines
parent here; legacy lines keep `settlement`). Check: exactly one parent set
(XOR constraint) — prevents orphan/double-parent lines.

**No other schema.** No WorkerAdvance.adda (rejected, §11.3). No per-Adda paid
flag (§11.5c.3). SWA untouched (rows now also written at finalize, §11.4).
Settings: `LEDGER_CREDIT_AT_ALLOCATION` flag (decouple, default **True** at
ship — flipping it OFF is the owner's explicit cutover act, gated by the
amended-C2 rule that true soak precedes production usage).

**Single-writer rule extension:** new `adda_settlement_service` is the SOLE
writer of AddaSettlement/AddaSettlementItem (CLAUDE.md rule 5 + a check.sh
grep gate, same pattern as the WorkerStageTask gate).

## Part 3 — Settlement lifecycle

`draft → finalized → (reversed | superseded)`; corrections NEVER edit.
- **draft**: manager/accountant opens for a completed Adda (gate: every
  payable WorkflowStage's stage_record completed — which, post-F3/F8, implies
  task resolution). Draft = recomputable scratchpad: variance counts, policy,
  per-advance recovery choices. **Zero ledger rows; zero frozen rows.** Drafts
  deletable.
- **finalize** (`@transaction.atomic`, lock order EXACTLY: advisory lock 5374 →
  AddaSettlement row `select_for_update` (double-finalize reject) →
  AddaStageRecord row locks (freeze qty inputs) → per-worker WorkerProfile →
  WorkerAdvance):
  1. derive lines from **completed** WSCs of payable stages
     (`credits_workers=True` data); settled qty = `verified_quantity if set
     else reported_quantity` (§11.9.2);
  2. **ADR-0007 cross-era guard** (Part 10 I-2) filters lines already backed
     by a non-voided SWA earning line;
  3. per line: write SWA (qty, rate=frozen expected_rate, amount) →
     `log_credit(STAGE_EARNING, assignment=SWA)`;
  4. per worker: agreed recovery → `log_debit(ADVANCE_RECOVERY)` +
     PayrollSettlementItem(adda_settlement=this) — guard ≤ advance remaining;
  5. freeze AddaSettlementItem per worker (+ tie-out assert: final_payable ==
     Σcredits − recovery booked in THIS settlement);
  6. status=finalized, settled_at, totals frozen. **No cash. No
     SETTLEMENT_PAYMENT.**
- **Payment** stays the narrowed `create_settlement` → payment-only: guard
  `amount_paid ≤ worker_balance`, posts SETTLEMENT_PAYMENT debit. D1-D4
  worker-centric semantics preserved (anytime/partial/multi).

## Part 4 — Reversal lifecycle (closes R0 C5)

`reverse_adda_settlement(settlement, actor, *, supersede=False)`:
- same lock order; allowed only from `finalized`;
- for every ledger entry this settlement created (credits via its SWA lines,
  recovery debits via its PayrollSettlementItems): `ledger_service.reverse_entry`
  (compensating row, original entry_date copied — nets in-period);
- recovery reversal **restores advance outstanding** (the pre-V2 impossibility,
  now structural: outstanding = Σgiven − Σrecovered, and the recovery line's
  reversal is itself a ledger event while the PayrollSettlementItem is matched
  by a compensating negative line — exact mechanism: write an offsetting
  PayrollSettlementItem with negative amount_recovered? NO — append a reversal
  PayrollSettlementItem row (amount_recovered negative is barred by checks) →
  **design decision D-R: reversal writes a mirrored `PayrollSettlementItem`
  with `is_reversal=True` flag OR we relax to signed amounts.** Recommendation:
  add `reversed_at` to PayrollSettlementItem + exclude reversed lines from the
  outstanding SUM — append-only, no signed rows, no schema ambiguity;
- void this settlement's SWA lines (`voided_at`) — re-arms the double-credit
  guard so a successor settlement can re-credit those contributions;
- frozen AddaSettlementItems untouched (audit); status=reversed + stamps;
- `supersede=True` additionally opens a fresh draft with `supersedes` set.
Pre-V2 `PayrollSettlement` reversal stays out of scope (legacy rows keep their
known limitation; only NEW-world settlements get the lifecycle) — flag to owner.

## Part 5 — Advance recovery flow

Issue (unchanged): WorkerAdvance row, no ledger entry. Outstanding (unchanged
formula): Σgiven − Σ recovered lines. **Re-homing:** recovery is decided + booked
at AddaSettlement finalize (debit + item line parented to ADST); payment never
re-runs recovery. Owner controls per-advance amounts in the draft; over-recovery
guarded under the WorkerAdvance lock. Legacy lines (parented to SETL rows)
remain valid forever — the SUM is parent-agnostic.

## Part 6 — Ledger interactions (complete map after V2-2)

| Event | Writer path | Ledger rows |
|---|---|---|
| Worker completes report | — | none (Option B) |
| Allocation (flag ON, legacy) | allocation_service | +STAGE_EARNING credit |
| Allocation (flag OFF, post-cutover) | — | none |
| **AddaSettlement finalize** | adda_settlement_service → ledger_service | +STAGE_EARNING per line (assignment=settlement-SWA) · −ADVANCE_RECOVERY per agreed recovery |
| **Reverse settlement** | same | compensating rows for the above |
| Payment | settlement_service (narrowed) | −SETTLEMENT_PAYMENT |
| Advance issue | — | none (loan pool) |
`ledger_service` remains the only `objects.create` site — unchanged invariant.

## Part 7 — Adda-level cost visibility delivered

Per Adda after V2-2: frozen stage `processing_cost` (existing) + **settled
labor** (finalized ADST totals + per-worker items) + advance-recovery applied +
variance counts (frozen) + reversal/supersede history. Plus a **settlement-
pending queue** (completed Addas with no finalized ADST) on the management
side — small, ships with the UI PR (also softens F6). NOT delivered: material
cost (G1), ₹-valued variance (G3), all-in cost & Adda-360 (G4) — per the locked
gap registry.

## Part 8 — Migration strategy

Purely **additive**: expense migrations (2 new tables + 1 nullable FK +
constraints/indexes). No data migration, no backfill (no synthetic settlements —
ADR-0007), no destructive op, no production-app migration. `makemigrations
--check` clean after model+migration land together. Clone rehearsal (P0.5):
up → down → up on a dev-DB clone — reverse = plain DropTable/RemoveField of
EMPTY-or-new structures; rehearsal asserts legacy tables untouched byte-for-byte
(row counts + checksums on WorkerLedgerEntry/SWA/PayrollSettlement*).

## Part 9 — Rollback strategy

- **Pre-execution pg_dump** (same ritual as V2-1d).
- **Schema:** `migrate expense <prev>` — additive tables drop cleanly; legacy
  data untouched by construction.
- **Behavior:** `LEDGER_CREDIT_AT_ALLOCATION` stays True until the owner's
  explicit flip → until then, zero behavioral change to live money. Flip-back
  is the ADR-0007 rollback lever (symmetric guard keeps it safe).
- **Money written by a finalized settlement:** never rolled back by migration —
  reversed through the lifecycle (that's what it's for).
- **Code:** git revert per PR; PRs sequenced so each is independently green.

## Part 10 — INVARIANTS (each becomes an explicit test)

1. **Single ledger writer** unchanged; **single ADST writer** =
   adda_settlement_service (new grep gate).
2. **Cross-era double-credit guard, symmetric** (ADR-0007): a (worker,
   stage_record, color/size) contribution line maps to **≤1 non-voided SWA
   earning line across BOTH eras**; allocation (flag ON) skips
   settlement-credited lines; finalize skips allocation-credited lines;
   NET non-voided counting (reversed legacy credit ⇒ line re-creditable).
   Live fixture test: 3-PATTI-001 finalize must credit utest ₹240 and
   **exclude worker2's already-credited 45 pieces** (₹135 era-A) while
   crediting only his uncredited remainder per policy.
3. **No cash at finalize** — finalize never writes SETTLEMENT_PAYMENT;
   payment never writes earnings/recovery.
4. **Drafts carry no money** — zero ledger rows, zero frozen rows until finalize.
5. **Quantity-freeze** — later verified_quantity edits don't move booked money
   (reverse/supersede required).
6. **Frozen snapshot write-once** — AddaSettlementItem rows never UPDATEd post-
   finalize (and never read as live truth; tie-out only at finalize).
7. **Recovery bounds** — Σ recovered per advance ≤ given, enforced under lock;
   recovery decided ONLY at settlement (payment never re-runs it).
8. **Lock order** fixed as §11.5 (5374 → ADST → stage records → profile →
   advances) — deadlock-free by global ordering with create_settlement.
9. **Expected_* untouched** — settlement reads, never writes, contribution rows.
10. **Payability is data** — only `credits_workers=True` stages produce earning
    lines (3-PATTI's layering must produce none).

## Part 11 — Risks, edge cases, G1-G7 compatibility

**Edge cases (each → test):** double-finalize race (row lock) · partial
settlement then second settlement (guard skips settled lines) · settle an Adda
with zero completed contributions (empty finalize → reject with message) ·
worker with 0-rate lines (unpriced stage: lines exist, ₹0 credits — include,
they're truth) · reverse after partial payment (worker balance may go negative —
legal, money fungible, surfaced on payroll screens) · supersede chain length >1 ·
ADST reference race (advisory lock) · mixed-era Adda labelling (UI shows
already-credited lines distinctly, ADR-0007 reporting note) · reversed-era-A
credit then settle (NET counting) · flag flip mid-life both directions ·
Adda reopened after finalize (production reopen + settlement reverse are
independent acts; document the operating procedure: reverse first).

**Risks:** (R1) UI is the largest surface — mitigated: management-only, form-
shell pattern, no worker exposure; (R2) finalize correctness density — mitigated
by invariant tests + the live dev fixture; (R3) legacy PayrollSettlement rows'
bi-modal meaning in reports — handled per ADR-0007 reporting note (label by
parent FK); (R4) pre-V2 settlements remain irreversible — explicitly out of
scope, owner-flagged.

**G-compatibility:** G1 material cost = separate read-model, untouched · G2/G5
revenue/inventory — settlement is Adda-side cost truth only, zero commerce
coupling (ADR-0008 honored: no order references anywhere) · G3 valuation —
variance stored as COUNTS, ₹-valuation stays a future derived policy · G4 —
ADST + items are precisely the rows the Adda-360 screen will read · G6/G7
unaffected. Missing/Alter (P6) plug into §11.10's source-agnostic counts with
zero schema change — verified: the form fields and future module summaries
write the same snapshot columns.

## Part 12 — Readiness verdict

**READY. No formal blockers.** Everything V2-2 needs is locked (§11 to field
level, ADR-0007, ADR-0008), its prerequisites are built (V2-1d sole truth;
F3/F8 made the draft gate hold by construction), and the dev DB already
contains the perfect cross-era test fixture. One standing owner rule restated:
**building V2-2 is approved territory; flipping `LEDGER_CREDIT_AT_ALLOCATION`
off for real production usage waits for the true soak** (amended C2).

**Open micro-decisions to confirm at PR-B (flagged, not blockers):**
D-R (Part 4): recovery-reversal mechanics — recommend `reversed_at` on
PayrollSettlementItem + SUM excludes reversed (append-only, unsigned).
D-S: settled-line grain for SWA = per (worker, stage_record, color/size)
contribution line (recommended; matches §11.4) vs per worker-stage aggregate.

**PR breakdown (each independently green, suite + gates):**
- **PR-A** models + migrations + read-only admin + clone rehearsal.
- **PR-B** `adda_settlement_service.finalize` + cross-era guard + invariants
  1-10 as tests (incl. the 3-PATTI-001 fixture test) + new check.sh gate.
- **PR-C** reversal lifecycle + PayrollSettlement narrowing to payment-only +
  D-R mechanics.
- **PR-D** management UI (draft form: variance counts, per-advance recovery,
  mixed-era labels; finalize/reverse actions; settlement-pending queue) +
  `LEDGER_CREDIT_AT_ALLOCATION` wiring in allocation_service (default True).

---

## Part 13 — Future-state review (owner-requested, pre-PR-A; brutally critical)

Reviewed against the mandatory Adda-360 vision + locked G1-G7/ADR-0008.

### Q1 — Lock-in for G1-G7? NONE found.
G1: settlement never touches material; Costing-2 composes as a derived read.
G2/G5: zero commerce/order references anywhere in the design; stock valuation
is derived later and is ordering-independent. G3: variance stored as COUNTS —
valuation stays a future policy. G4: ADST+items are exactly the Adda-360 read
rows. G6: no product duplication. G7: no planning coupling.

### Q2 — What becomes harder later if PR-A..D ship EXACTLY as proposed? Three things:
1. **(THE finding) Credit↔contribution provenance is implicit.** The §11.9.1
   double-credit guard matches on the key tuple (worker, stage_record,
   color/size) — but a worker can legally have TWO completed contribution rows
   with the same key (reported 20 + 30 of Red/Free). Key-matching then (a)
   makes the guard ambiguous at the margins, and (b) leaves future dispute/
   reporting ("which worker reports back this ₹150 credit?") to heuristic
   re-derivation. Retrofitting provenance after real settlements exist =
   backfill-by-guess, the exact class of debt this project refuses.
   **CHANGE NOW: add nullable `WorkerStageContribution.settlement_line` FK
   (PROTECT → StageWorkAssignment), stamped at finalize.** Guard becomes EXACT
   (skip WSC rows with a non-voided settlement_line — per-row, not per-key);
   reversal voids the SWA and the linkage self-documents history; era-A
   (allocation credits) stays key-based per ADR-0007 — coarse there is fine,
   exact from era-B forward. One nullable FK in PR-A; near-free now.
2. **D-S upgrades from micro-decision to LOCKED: SWA settlement lines MUST be
   per (worker, stage_record, color/size).** A worker-stage aggregate would
   destroy the dimension grain that G5 inventory costing needs (labor cost per
   color/size feeds per-piece stock valuation; material already has dimension
   via rolls→color). Aggregate = cheaper rows today, a costing migration later.
3. **Settlement events belong on the Adda timeline.** Add AddaHistory change
   types SETTLEMENT_FINALIZED / SETTLEMENT_REVERSED / SETTLEMENT_SUPERSEDED
   (logged via history_service in PR-B/C). The Adda-360 view is a TIMELINE;
   without these the financial closing event is invisible on it and gets
   bolted on later.

### Q3 — Grain correctness for future costing/inventory/order/profitability: YES, with #2 locked.
Labor per Adda ✓ (totals) · per stage ✓ (items.stage_record) · per dimension ✓
(SWA lines, given #2) · per worker ✓ (items). Variance per worker (counts) is
the right FINANCIAL grain; per-dimension variance is an inventory concern that
G5 reconciles from scan truth vs the frozen breakdown — settlement doesn't need
it (the AddaSettlementItemLine child stays the additive escape hatch, §11.9.3).
Order costing: per-piece cost = Adda cost / pieces, dimension-aware via #2 +
rolls-per-color material — derivable end-to-end through the barcode bridge.

### Q4 — Data discarded that future costing/reporting needs? One conscious loss + nothing else.
The only discard: pre-Missing-module, per-DIMENSION variance facts ("50 RED
missing") are flattened to per-worker counts on the snapshot — accepted by the
owner's Q4/§11.10 manual-entry decision and remedied automatically when the
Missing module becomes the source. Everything else checked and retained:
material facts (rolls/weights/₹-kg/leftovers), output dimension truth (frozen
breakdown), task timestamps, frozen rates, piece identities, cohort provenance
(era-A vs era-B derivable: SWA referenced by an ADST item = settlement-era).
Drafts are deletable scratchpads by design — not data.

### Q5 — Would I build V2-2 this way from day one? Yes, with two day-one differences — both adopted above.
The event+frozen-snapshot+live-ledger triad is the right pattern at this scale
(double-entry-lite without account-tree machinery the factory doesn't need).
From scratch I would have had (a) explicit credit↔contribution linkage and
(b) settlement events on the unified timeline from the start — which is
exactly #1 and #3. I would NOT add: multi-currency (single-₹ is a documented
conscious assumption, painful-but-YAGNI), tax/GST (belongs to future commerce
invoicing), payee/contractor indirection (thekedar-model payments — flagged as
a domain QUESTION for the owner someday; additive payee FK if ever real).

### Q6 — Changes adopted NOW (amending the PR plan):
- **PR-A** += `WorkerStageContribution.settlement_line` nullable FK (PROTECT).
- **PR-B** guard implementation = exact per-row (era-B) + key-based (era-A);
  invariant 2 restated accordingly. += SETTLEMENT_FINALIZED history event.
- **PR-C** += SETTLEMENT_REVERSED / SUPERSEDED history events.
- **D-S locked**: per-dimension SWA lines (no aggregate option).
- Documented assumptions (no build): single currency; direct-worker payees;
  per-dimension variance arrives with the Missing module.

Verdict unchanged: READY — now with provenance exact from birth.
