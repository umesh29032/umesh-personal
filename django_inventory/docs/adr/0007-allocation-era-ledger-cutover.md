---
id: docs-adr-0007-allocation-era-ledger-cutover
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR 0007 — Allocation-Era Ledger Cutover for Adda-Centric Settlement (V2-2)

**Status: ✅ ACCEPTED 2026-06-10 — owner selected Option A (Coexist).**
Owner's terms (verbatim intent): historical allocation-era credits remain untouched; no rewrite/void/rebook/fabrication of historical financial events; AddaSettlement credits only not-yet-credited earnings; explicit double-credit protection rule; rollback lever (`LEDGER_CREDIT_AT_ALLOCATION` flag) during transition; no synthetic settlements; no retroactive ledger rewrites; no worker balance churn.
Depends on: ADR 0005 (Option B), ARCHITECTURE_V2 §11 (locked), V2_1_REVIEW.
Blocks: any V2-2 (AddaSettlement) implementation.

## Context

Two earning surfaces coexist today:

1. **Live money (pre-V2 model):** `WorkerLedgerEntry` STAGE_EARNING credits written at **allocation time** by `expense/services/allocation_service.py:110` (cutting workspace), backed by `StageWorkAssignment` rows. This is real, append-only financial truth under the shipped M2.7 model. `PayrollSettlement` then settles+pays+recovers in one atomic event.
2. **Visibility (V2 model, built V2-1c):** `WorkerStageContribution.expected_rate`/`expected_earning`, frozen at worker completion, booking **no** ledger entry (Option B).

The locked V2-2 target moves the money-write to `AddaSettlement.finalize` (STAGE_EARNING credit + ADVANCE_RECOVERY debit; cash later via the narrowed PayrollSettlement). Undefined until now: **what happens to ledger credits that were already written at allocation time** when V2-2 goes live, and how the §11.9 double-credit invariant treats them.

**Data reality (2026-06-10):** dev-only deployment; dev DB has minimal/no allocation-era rows (V2-1a backfill found 0 stage-record rows). The policy cost is therefore near-zero *today* — but user testing or live use before V2-2 can create rows at any time, so the policy must be locked before V2-2 code, not after.

## Decision drivers
- Owner data rule: **backfill only known facts; never fabricate events/states** (V2_1_REVIEW Q1).
- Owner history rule: financial history is **append-only**; corrections via compensation/supersession, never edit/delete.
- §11.9 invariants must hold across eras: a unit of work credits the ledger **at most once**.
- Ledger stays single-writer (`ledger_service`, ADR 0002) and every credit must trace to one SWA row (`WorkerLedgerEntry.assignment` PROTECT, §11.4).
- Migration safety: reversible until an explicit point of no return; clone rehearsal (P0.5).

## Options

### Option A — COEXIST with a cutover boundary (RECOMMENDED)
Historical allocation-era credits remain untouched, valid financial truth. New money flows only through AddaSettlement after cutover.

- **Current live ledger credits:** untouched. They were real credits under the then-valid model; rewriting history violates append-only.
- **Expected snapshots:** unchanged in meaning both eras — visibility only, never money. At V2-2 finalize, `AddaSettlementItem` freezes from completed contributions (or manual variance entry where contributions don't exist — §11.10 already covers M2M-era stage records that have no contribution lines).
- **Cutover boundary (grain = stage-record allocation):** a worker-stage line whose SWA already produced an allocation-era STAGE_EARNING credit is *credited history*. The **double-credit guard extends across eras**: `AddaSettlement.finalize` must exclude any (worker, stage_record) line already credited via an allocation-era SWA. Mixed Addas (some stages credited pre-cutover, some not) settle the uncredited remainder only; the settlement snapshot records both cohorts for audit (`AddaSettlementItem` carries the excluded-as-already-credited amounts in its frozen snapshot fields, so the per-worker picture stays complete without re-crediting).
- **Crediting switch:** when V2-2 finalize ships, allocation-time crediting turns OFF behind a settings flag (e.g. `LEDGER_CREDIT_AT_ALLOCATION`, default flips False at cutover; env-overridable like `WORKER_TASK_DUAL_WRITE`). The flag is the rollback lever.
- **Migration path:** purely additive — AddaSettlement/Item tables + nullable `PayrollSettlementItem.adda_settlement` FK (already in the locked design). **No ledger data migration. No backfill of synthetic settlements** (fabricating settlement events that never happened violates the known-facts rule).
- **Historical ledger entries:** remain queryable as the pre-V2 cohort. Reporting distinguishes cohorts by `entry.assignment` → SWA provenance (allocation-written SWA vs settlement-written SWA; settlement-written SWAs are reachable from their AddaSettlement). If provenance proves awkward in practice, an additive nullable `source` discriminator on new entries may be introduced later — not pre-built.
- **Rollback:** flip the flag back → allocation crediting resumes; AddaSettlements already finalized stay (append-only) and their credits stand; the cross-era double-credit guard then ALSO protects the reverse direction (allocation crediting must skip lines already settlement-credited) — the guard must be symmetric from day one.
- **Audit implications:** ledger never rewritten; single writer preserved; every credit traces to exactly one SWA; settlement snapshots write-once; the cutover itself is an auditable config event (log line + ADR). Worker-visible balances never jump.

### Option B — VOID AND REBOOK
Compensating debits for every allocation-era credit, then rebook everything through synthetic AddaSettlements.
- Rejected (recommendation): fabricates settlement events that never happened (violates known-facts rule); floods the ledger with compensation noise; worker-visible balances churn for zero business meaning; large blast radius for a problem Option A solves with an exclusion rule.

### Option C — RETRO-MAP (synthetic wrappers, no ledger change)
Create historical `AddaSettlement` rows that wrap existing credits so all reporting is uniform.
- Rejected (recommendation): still invents events ("this Adda was settled on date X" — it wasn't); the frozen-snapshot fields would be back-computed, contradicting the write-once/never-recompute lock; uniform reporting is achievable more honestly by treating the pre-V2 cohort explicitly.

## Consequences of Option A (if accepted)
1. V2-2 build gains two requirements: (a) **cross-era, symmetric double-credit guard** — explicit test: allocate-credit a line, attempt AddaSettlement → excluded; finalize-credit a line, flip flag back, attempt allocation → skipped; (b) `LEDGER_CREDIT_AT_ALLOCATION` flag wiring in `allocation_service`.
2. §11.9's invariant wording extends: "a (worker, stage_record) earning line maps to ≤1 non-voided credit **across both crediting eras**."
3. Reporting/V2-2 UI must label pre-V2 credited lines inside a mixed Adda's settlement screen ("already credited at allocation — excluded").
4. No action needed now beyond accepting this ADR; first code lands inside the V2-2 PR set.
5. Practical note: if cutover happens before any real factory data exists, the boundary logic still ships (tested via fixtures) but cohort A is empty — cheapest possible landing.

## Open question folded in (from R0 C5)
`reverse_settlement` for the PRE-V2 `PayrollSettlement` stays unbuilt; reversal/supersession is designed once, in V2-2's locked lifecycle (draft→finalized→reversed/superseded), covering both the new AddaSettlement and the narrowed payment event. Until then: manual ops caution on settlements (documented gap).

## Reporting implications & coexistence edge cases (owner-requested; V2-2 build requirements)

**Reporting:**
1. **Money views stay ledger-only.** Worker payroll screens (`my_earnings`, `worker_detail`, payroll overview) already aggregate `WorkerLedgerEntry` — both cohorts mix transparently and balances stay correct. Never mix `expected_*` into money totals.
2. **Mixed-Adda settlement screen** must show three line classes per worker: (a) to-credit now, (b) already credited at allocation — excluded by the guard (labelled, amount shown for completeness), (c) variance/manual entry (§11.10).
3. **Expected-vs-settled variance reports** are only meaningful for the post-cutover cohort: M2M-era stage records have NO contribution lines, hence no `expected_*` — reports must null-guard and label the pre-V2 cohort instead of showing 0-expected anomalies.
4. **PayrollSettlement history is bi-modal**: pre-V2 rows = settle+pay+recover events; post-V2 rows = payment-only. Distinguish via the nullable `adda_settlement` FK (and/or created-at vs cutover date). Settlement-history UI must not present old rows as payment-only.
5. **Adda profitability/costing unaffected**: costing reads frozen stage-record snapshots, not the ledger — no cohort handling needed.

**Edge cases (each needs a test in V2-2):**
1. **Mid-Adda cutover:** some workers of one stage credited at allocation, others not, flag flips mid-flight. Guard grain = (worker, stage_record) net non-voided credit — finalize credits only uncredited lines; per-line labels per Reporting-2.
2. **Reversed allocation-era credit:** if a legacy credit was compensated via `reverse_entry`, the line's NET non-voided credit is zero → eligible for AddaSettlement crediting. Guard counts net non-voided, not row existence.
3. **Symmetric rollback:** flag back ON after some AddaSettlements finalized → allocation crediting must skip settlement-credited lines (guard works both directions from day one).
4. **Advance recovery across eras:** pre-V2 PayrollSettlements already reduced advance outstanding; AddaSettlement recovery reads LIVE outstanding at finalize (per locked design) — no double recovery possible, but test it.
5. **Flag-flip auditability:** each `LEDGER_CREDIT_AT_ALLOCATION` change logged (config event) so the cohort boundary is reconstructable.

## Sign-off
- [x] Owner selected: **A** (2026-06-10)
- [x] Symmetric guard requirement + flag-based rollback lever confirmed
- [x] Status ACCEPTED; ARCHITECTURE_V2 §11 pointer added; agenda updated (see docs(R0) commit)

## Addendum — cutover EXECUTED (V2-3, 2026-06-11)

Owner D-V3.1/D-V3.2 locks. State as shipped:
- `LEDGER_CREDIT_AT_ALLOCATION` **default = False** (settings/base.py) —
  earnings book ONLY at Adda settlement. env `=True` is the ROLLBACK LEVER
  (restart-only; symmetric guard keeps mixed data coherent both directions).
- Settlement-money armor: reopen of a settlement-credited stage BLOCKED (names
  the ADST refs); `void_allocation` refuses era-B lines; PAY-3 reopen sweep =
  era-A only. Gate [4c/4] enforces the two-writer rule on SWA.
- Allocation UI hidden under the default (era-A history stays readable; void
  stays available on open stages). Lever path tested in CI: 8 legacy test
  classes pinned `override_settings(LEDGER_CREDIT_AT_ALLOCATION=True)`.
- **Physical deletion of the legacy path remains SOAK-GATED** (amended C2):
  separate PR after real workers run settlement-first in production.
