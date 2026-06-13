# ARCHITECTURE VALIDATION — a review for future senior developers

> Not "what" (that's GUIDE/FILE_MAP) and not the junior "why" (that's
> ARCHITECTURE_EXPLAINED). This is the SENIOR review: each major decision, the
> alternatives REJECTED, and the trade-off. Companion to the ADRs (the binding
> records). Where a claim is reasoning rather than a code/ADR fact, it is
> marked *(Architectural Interpretation)*.

## 1. Why this architecture exists at all
A one-factory garment ERP where the make-or-break property is **trustworthy
worker pay**. The architecture optimizes for that: auditable money, separated
truths, single writers. Most ERPs get inventory right and pay wrong; this one
inverts the priority deliberately. *(Interpretation; consistent with ERP_MASTER_CONTEXT.)*

## 2. settlement-first vs allocation-time crediting → settlement-first
- **Rejected:** credit earnings at work allocation (era-A). It books money
 before the work is measured/verified → wrong numbers, no review point.
- **Chosen:** book at an explicit Adda settlement (era-B). Money exists only
 after management reviews quantities. Cutover kept era-A coexisting behind a
 lever (no history rewrite). ADR-0007.

## 3. Adda-centric vs worker-centric settlement → Adda-centric
- **Rejected:** settle each worker independently. Work happens in an Adda;
 a worker's stage output only makes sense in that batch's context.
- **Chosen:** AddaSettlement settles all workers of an Adda in one reviewed,
 reversible event; payment stays worker-centric (separate). ADR-0005 §11.

## 4. Production truth vs financial truth → separated (Option B)
- **Rejected:** write the ledger as work is reported (one truth).
- **Chosen:** WSC (production) ≠ ledger (financial); bridged only at settlement
 via verified-else-reported × frozen rate. Production mistakes never corrupt
 money; money is always post-review. ADR-0005.

## 5. Append-only vs mutable balances → append-only
- **Rejected:** a stored balance updated in place.
- **Chosen:** immutable ledger rows; balance = live SUM. Stored balances drift
 under concurrent writers and destroy the audit trail. ADR-0002/0004.

## 6. Reversal vs editing → reversal
- **Rejected:** edit/delete a wrong money row.
- **Chosen:** compensating reversal row (+ supersede chain at settlement level).
 Append-only forbids editing; reversal matches the accountant's real
 correction workflow and keeps history intact. ADR-0007.

## 7. WorkerStageTask vs WorkerStageContribution → separated
- **Rejected:** one row holding both "who worked" and "what they made."
- **Chosen:** WST = participation/lifecycle (cancel-not-delete), WSC =
 dimensional output lines. Different cardinality (one task → many lines),
 different lifecycle, different immutability rules. *(Interpretation; matches
 worker_task.py constraints.)*

## 8. Why allocation-era was retired (not deleted)
- **Rejected (now):** hard-delete era-A rows at cutover → financial history loss.
- **Chosen:** retire as default (lever off), keep readable+reversible; physical
 deletion soak-gated. Trust > tidiness. ADR-0007.

## 9. Stage engine: hard-coded vs open-closed → open-closed
- **Rejected:** per-stage if/else in views/services.
- **Chosen:** StageHandler contract + registry + per-stage packages; worker UI
 renders from `contribution_schema`. New stage = new package, zero core churn.
 R1 Stage Contract.

## 10. Single-writer + CI gates vs convention → enforced
- **Rejected:** "please only write money via the service" as a code-review hope.
- **Chosen:** grep-based CI gates (4/4b/4c) make a stray writer a failing build.
 Architecture as test, not folklore.

### Verification Sources
- ADRs read: the ADR set under docs/adr/. Models: expense/models.py,
 production/models/worker_task.py. Services: the chokepoint services (KNOWLEDGE_MAP §7).
- Confidence: **High** — verified against commit f067daf0 (2026-06-12); re-verify the cited file if it changed for ADR-backed sections; items marked *(Interpretation)*
 are reasoning consistent with code but not a single cited line.
