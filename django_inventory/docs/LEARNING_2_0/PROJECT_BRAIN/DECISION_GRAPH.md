# DECISION GRAPH — ADRs and how they depend on each other

## TL;DR
The ADRs aren't independent — they build on each other. Read top-down.

```
0001 services own writes (no signals)
 └─ 0002 single writer per ledger/history table ← CI gates 4/4b/4c
 └─ 0005 production truth ≠ financial truth (Option B; expected_*=visibility)
 ├─ 0007 era coexistence + lever (cutover EXECUTED in V2-3)
 │ └─ (depends on 0005's "money only at settlement")
 └─ 0009 cost truth (duality never-add; labor-source; purchase price)
 └─ (builds on 0005 truth split + 0002 single writer)
0003 RBAC (type/role/skill; stage = skill-gated) [independent axis]
0004 tracking = append-only history primitive [feeds 0002 discipline]
0006 architect-for-scale, don't implement early [meta-rule over all]
0008 commerce boundary (Order↔Adda only via G5 stock; revenue in commerce)
 └─ 0010 growth/identity (global refs forever; one-DB multi-factory;
 barcode payload permanence; rework case-scoped; no price in production)
 └─ (enforces 0008's boundary in schema terms)
```

**Reading order for a new architect:** 0001 → 0002 → 0005 → 0007 → 0009
(the money spine), then 0003/0004 (RBAC + history), then 0008 → 0010 (commerce
future), 0006 as the standing meta-rule. Full text: [../../adr/](../../adr/).
Senior rationale + rejected alternatives: [../ARCHITECTURE_VALIDATION/README.md](../ARCHITECTURE_VALIDATION/README.md).

### Verification Sources
ADR files under docs/adr/ (read this session). Dependencies are
*Architectural Interpretation* of their cross-references. Confidence: High (ADRs) / Med (edges).
