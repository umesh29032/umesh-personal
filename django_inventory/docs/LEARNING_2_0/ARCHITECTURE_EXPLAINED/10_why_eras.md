---
id: l2-architecture-explained-10-why-eras
type: topic-canonical
status: active
owner: handwritten
scope: learning — architecture rationale
anchors: —
verified: 2026-07-13
---

# Why era-A and era-B existed (and the lever)

> **Canonical** for the "when is the ledger credited" policy + the
> `LEDGER_CREDIT_AT_ALLOCATION` lever (binding source: ADR-0007). Other docs state
> the current default (settlement-first) and link here, not re-explain the lever.

**Problem:** Purana system allocation ke WAQT paisa credit karta tha (era-A).
Naya system settlement par (era-B). Cutover ke waqt purane credited rows ko
delete/rewrite karna = financial history todna (mana hai).

**Solution:** DONO ko coexist karo. SWA.adda_settlement = NULL → era-A (legacy);
set → era-B (settlement). Symmetric guard dono ko ek hi line dobara pay karne
se rokta hai. Ek env LEVER (`LEDGER_CREDIT_AT_ALLOCATION`): default False
(settlement-first); True = tested rollback.

**Kyun:** safe cutover. Purana paisa readable + reversible rehta hai forever;
naya paisa sahi rasta leta hai; rollback ek restart door hai, code change nahi.

**Aage:** era-A path ki physical DELETION soak-gated hai (real workers settle
karein, phir hi). Tab tak era-A = historical, frozen.

ADR-0007 · [allocation chokepoint](../CHOKEPOINTS/allocation_service.md).
