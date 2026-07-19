---
id: debug-counts-mismatch
type: debugging
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Piece counts don't match between screens/stages — breakdown vs bundles vs pool vs reported. Where is the truth?"
related: [feature-cutting, feature-allocation, feature-stage-tracking]
---

# Playbook: "Ginti alag-alag kyun hai?"

> 📂 [Debugging](README.md) · [KOS home](../README.md) — *pehle poochho: KAUN-SI ginti?*

## Symptoms this playbook covers

- Cutting says X pieces, downstream stage shows Y
- Bundle totals ≠ breakup totals
- Worker reported more than their allocation / pool shows negative-ish availability
- Barcode ranges don't match produced pieces
- "Reported 40 but screen shows 38"

## First Five Minutes

1. **Name the number you're staring at.** This system has FIVE piece
   numbers, each with a different meaning: `reported` (worker's claim) ·
   `verified` (manager's correction) · `good/alter/missing` (observation
   split) · pool good (`Coalesce(verified, good)` frozen at stage complete)
   · APSCPB (cutting's verified breakdown — the mint). Half of all
   "mismatches" are two DIFFERENT numbers correctly disagreeing.
2. **Find the birthplace.** All downstream counts descend from **APSCPB**
   (cutting). If APSCPB is right, walk forward; wrong — fix at the mint,
   never downstream.
3. **Check the resolver direction:** verified OVERRIDES reported everywhere
   that matters (pool + money). "Reported 40, shows 38" = a manager
   verified 38. That's the feature.
4. **Timing:** pool snapshots freeze at stage COMPLETE. A verification
   AFTER downstream materialization → reopen/refreeze path, not a bug.
5. Now open data, in birth order: APSCPB → SPS → WSA → WSC.

## Decision tree

```
Which two numbers disagree?
├─ reported vs shown        → verified_quantity set (Report Review) — by design
├─ breakup vs bundles       → same pieces, physical grouping drift = data entry;
│                             reconcile bundle items against CuttingPieceBreakup
├─ APSCPB vs layout         → layout_reconciliation(adda) — catches typo'd
│                             counts BEFORE they poison downstream
├─ pool available vs expect → available = frozen pool − Σ ACTIVE allocations;
│                             check voided WSAs + whether materialize ran
│                             (stage advanced through the funnel? NONE-grain = 0 by design)
├─ worker report vs alloc   → bound check (flag-gated): Σ(g+a+m) ≤ allocated;
│                             refusal at complete = working as designed
└─ barcodes vs pieces       → preview_barcode_batches reads APSCPB — regenerate
                              preview and diff; printed payloads are PERMANENT
                              (never "fix" a printed range — ADR-0010)
```

## Which checks, concretely

| Check | How |
|---|---|
| The mint | APSCPB rows for the Adda per (size,color) — the single source |
| Stream state | any lane seq>1? its mandatory REASON explains "extra" pieces (recut/split/additional) — JOIN gates downstream until blocking lanes complete |
| Pool math | pool_service: pool good vs Σ active WSA on that dim; H-2 = void refused while reports exceed remainder |
| Both hands | WSC: reported AND verified both visible — neither ever overwrites the other |

## Known real causes

- **Verified-else-good propagation (owner rule 2026-07-06):** one Report
  Review correction changes BOTH next-stage pool and money basis — from one
  truth. Two screens updating at different moments during that flow is
  read-timing, not corruption.
- **The 120-vs-105 class:** paid > produced = the exact leak the pool +
  bound exist to kill; if reconciliation flags it on old data, that's
  era-history, handled through S1/S5 evidence flow.
- **Second stream surprise:** seq>1 lanes are declared acts — read the
  reason before declaring counts wrong.

## Where to learn the concepts

[cutting](../features/cutting.md) (the mint) · [allocation](../features/allocation.md)
(pool/bound) · [stage-tracking](../features/stage-tracking.md) (both-hands +
resolver) · [cloth-to-garment](../flows/cloth-to-garment.md)

## Implementation References

- Pool law: [pool_service chokepoint](../../docs/LEARNING_2_0/CHOKEPOINTS/pool_service.md) · barcode identity: [ADR-0010](../../docs/adr/0010-growth-and-identity-policy.md)

## Code References

- `production/services/pool_service.py` (`pool_good`, `available`, H-2 guard) · `production/stages/cutting/service.py` (`layout_reconciliation`, `_materialize_breakdown`, `preview_barcode_batches`) · `worker_task_service.set_verified_quantity`
- Tests already covering: `test_s3_good_alter_missing.py` · S4 suites · cutting/stream tests
