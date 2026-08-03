---
id: docs-future-feature-vision-2026-07-18
type: topic-canonical
status: active
owner: handwritten
scope: planning
anchors: —
verified: 2026-07-18
---

# Phase 18 Vision Package — Future Features, Roadmaps, and Evolution (FFD-0)

> **PLANNING DOCUMENT (owner-ordered, 2026-07-18). NOT build authority.** Every roadmap,
> version, and category below is a PROPOSAL until the owner rules it (the
> Factory-Driven-Development law: no invented milestones). The campaign roadmap 16–22
> stays FROZEN and is unaffected. Candidate for the FFD-D3 ruling: THIS document becomes
> the planning-doc-of-record for post-freeze feature reality (the contract's recorded
> ambiguity). Evidence log: [FEATURE_DOC_SYNC_LOG.md](FEATURE_DOC_SYNC_LOG.md).

## 1. Phase 18 Executive Vision

The ERP's build story for V1 is over: production truth, settlement money, recurring
expenses, material cost, and the operating dashboard are built and certified. What
remains before deployment is DISCIPLINE, not features: make the documentation converge
to reality (Phase 18's own sweeps), certify the whole product in the browser (18A),
document and execute the deployment (19–21), and take the first checkpoint (22). This
package preserves everything deliberately NOT built — every deferral, every reserved
ADR future, every vision — so the post-deployment roadmap starts from a complete,
owner-ruled register instead of memory.

## 2. Future Feature Register (every deferral, by owning phase — with term categories)

| # | Feature | Origin (ruling) | Term |
|---|---|---|---|
| FF-1 | Phase-18 documentation reality-sync (558 stale outputs · 136 frontmatter · 220 unowned — the standing sync queue) | P14/P18 contract | **Short** (this phase's own waves) |
| FF-2 | Release Certification Program execution (RC-0..RC-F) | 18A (owner directive) | **Short** (pre-deploy) |
| FF-3 | Enforcement flags ON (`ENFORCE_ALLOCATION_BOUND` · `ENFORCE_SETTLEMENT_RECONCILIATION`) — "R11" | S5 runbook; U10 | **Short** (post-deploy soak, owner-gated) |
| FF-4 | S6 `reported_quantity` retirement (irreversible migration) | S3/S6, soak-gated | **Short-Medium** (post-deploy soak) |
| FF-5 | MEE: non-monthly frequencies (daily…yearly, custom) — each via PDD change-control | P16 D1 | **Medium** |
| FF-6 | MEE: one-time + variable amounts | P16 D1 | **Medium** |
| FF-7 | MEE: report pages (upcoming/missed/overdue, quarterly/yearly summaries) + FY/quarter definitions | P16 D1/D9 | **Medium** |
| FF-8 | MEE: persisted skip-ledger; effective-dated template amounts | P16 (options recorded) | **Long** |
| FF-9 | BOD ladder wave 2: MEE tiles (recurring total · pending generation) + RMX tiles (material spend · unpriced count · full-cost rollup) | MEE-E/RMX-F handoffs | **Medium** |
| FF-10 | BOD: W2 completed-work · pieces-today aggregate · G-3 pivot tile · MC2 holder lists | P15 census rulings | **Medium** |
| FF-11 | BOD: F4 salary obligations — REQUIRES the Payroll-Obligation entity first (permanent never-derive law) | P15 F4 | **Long** |
| FF-12 | BOD: manager/accountant tiers · delay/threshold rules · analytics/trends · the dedicated Expense Financial Dashboard | P15 charter deferrals | **Long** |
| FF-13 | RMX: holdings/inventory/stock valuation (the third basis) | P17 D9 | **Medium** |
| FF-14 | RMX: variance reporting (standard-vs-actual home) | ADR-0009 D2 | **Medium** |
| FF-15 | Overhead in full cost (era-stamped) | ADR-0009 reserved | **Long** (ADR) |
| FF-16 | Factory-expense allocation model | ADR-0011 reserved | **Long** (ADR) |
| FF-17 | **Raw Materials V2 — the generic materials foundation** (units · purchasing · warehouses · consumption; owner adds materials without code) | [RAW_MATERIALS_V2_PRODUCT_VISION.md](RAW_MATERIALS_V2_PRODUCT_VISION.md) | **Long** (post-22 program) |
| FF-18 | Supplier/procurement workflows | P17/RM-V2 boundary | **Long** |
| FF-19 | Revenue entity → P&L/margin surfaces | P15 ruling (no entity exists) | **Long** |
| FF-20 | KOS Consolidation Program | owner-approved, deferred post-22 | **Long** (post-22, sequenced at the roadmap review) |
| FF-21 | Pattern tool Phase 6 (PDF/print/export) | ROADMAP_V2, owner-gated | **Medium** |
| FF-22 | Remnant re-issue UI (leftovers issuable as stock) + un-consume leftover event | Module-9 record; roll_service docstring | **Medium** |
| FF-23 | Streams deferred UI (Add-lane button · pattern-console injector · adda-level bundle-slip) | streams redesign record | **Medium** |
| FF-24 | Monthly-worker advances rule revisit (M-2 temporary block → salary-deduction recovery path) | R5 M-2 | **Medium** |
| FF-25 | Accountant reachability resolution (PHASE_03 D1 contradiction) | recorded, unresolved | **Short-Medium** (owner ruling; cheap) |
| FF-26 | Accounts permission-layer request-cache (≈5 role/extra-roles queries on EVERY page) | BOD-E finding | **Short-Medium** (small, high-leverage) |
| FF-27 | Performance dataset volumes (DATA-D6 targets) + performance scenario | spec §7 deferred | **Medium** |
| FF-28 | Material-Spend sidebar MenuItem (+2 pin cost) · Access-Control rows for new pages | RMX-D decision | **Short** (owner UI call) |

## 3. Product Roadmap (PROPOSAL — owner approval required)

1. **Now (frozen campaign):** 18 (doc sweeps) → 18A (RCP) → 19 → 20 (deploy) → 21 → 22
   (first checkpoint).
2. **Stabilization (immediately post-22):** owner roadmap review (already promised) ·
   FF-3 flags-ON soak · FF-4 S6 · FF-25/26 quick rulings/fixes · snapshot refresh.
3. **Operate & polish (V1.x):** FF-9/10 BOD wave 2 · FF-7 MEE reports · FF-13 holdings ·
   FF-21 pattern export · FF-22/23 floor-UX items.
4. **Programs (V2 era):** FF-17 RM-V2 (vision → PDD change-control → design → hostile
   review → phases) · FF-20 KOS · the ADR-class money futures (FF-15/16/19/11) — each
   its own owner-chartered program with an RCP pass before its deployment.

## 4. Architecture Evolution Plan

- **The pattern is set — keep it:** owner charter (PDD change-control) → contract →
  design review → gated waves → money certification → closure certificate. Every future
  feature follows it (the P15–P17 discipline is now the house methodology).
- **Extension seams already built:** the Metric Resolution Ladder + Widget Registry
  (BOD) · the frequency enum + period_key coverage (MEE) · the material service seams +
  ONE Decision-2 assembly (RMX) · generic_stage config-only archetype (production) ·
  the dataset registry + amendment mechanism (A1–A4 precedents).
- **Evolution rules:** no parallel systems; new domains (RM-V2) get their own truth
  tables behind service seams, never columns bolted onto frozen tables; money futures
  enter ONLY via their reserved ADR processes; every new writer = a Money-Write census
  addendum; every schema = U14.
- **Known structural debt to schedule (not silently fix):** the paused arch-remediation
  stream (RBAC relocation · cycle-break worklist · god-file splits) and the paused
  frontend HTML audit — candidates for the post-22 review.

## 5. Technical Debt Review

| Debt | Severity | Disposition |
|---|---|---|
| 558 stale generated outputs + 136 frontmatter + 220 unowned docs | Medium (honest, accepted) | Phase 18's own sweeps (FF-1) |
| Accounts permission layer: ~5 role/extra-roles queries per request, every page | Medium | FF-26 — small request-cache, owner-gated (touches the certified permission layer) |
| Page-pin growth trend (a360 74→80 · costing 11→16 — all conscious/documented) | Low | acceptable; FF-26 recovers ~2-4; watch at RCP RC-11 |
| Paused streams: arch remediation (phases 4+), HTML audit, layering light-refactor | Medium | post-22 review items; NOT pre-deploy |
| INFO residue #6–#14 (fix-when-touched) · 2 git stashes · snapshot refresh due | Low | standing registers; snapshot = owner action |
| M-2 temporary business rule (monthly advances blocked) | Low (business) | FF-24 |
| PHASE_03 accountant contradiction | Low (nobody harmed; accountant unreachable) | FF-25 owner ruling |
| Uncommitted working tree until P22 | **High (operational)** | the reason 18→22 must stay short; mitigations: backups + the locked order |

## 6. Future ADR Register (candidates — each needs its own owner process)

ADR-C1 overhead-in-full-cost (0009 reserved; era-stamp law) · ADR-C2 factory-expense
allocation model (0011 reserved) · ADR-C3 Payroll-Obligation entity (unblocks BOD F4) ·
ADR-C4 revenue entity + margin formula ownership (extends 0008/0009) · ADR-C5 RM-V2
material-type architecture (the config-driven domain) · ADR-C6 leftover un-consume
lifecycle event · ADR-C7 MEE effective-dated amounts (versioned template evolution) ·
ADR-C8 accountant reachability + FINANCIAL_ROLES surface policy consolidation (formalize
the D2 permanent rule alongside it).

## 7. Future BOD Opportunities (ALL via the PHASE_15 Ladder + Registry, owner-gated)

L1-ready today: MEE recurring total · MEE pending-generation count · RMX material spend
(consumption/purchases) · RMX unpriced-roll count (data quality) · full-cost rollup.
Needs new truth first: F4 obligations (ADR-C3) · pieces-today aggregate · W2
completed-work definition · revenue tiles (ADR-C4). Structural: tiers (manager/
accountant boards) · thresholds/rules engine · the Expense Financial Dashboard the BOD
would then consume.

## 8. Future Dataset Plan

Performance world (DATA-D6 — owner supplies volume targets; dated amendment) · MEE
frequency worlds (arrive WITH each enabled frequency) · RM-V2 material worlds (new
truth tables era) · holdings-valuation fixtures (with FF-13) · revenue/P&L worlds (with
ADR-C4). Mechanism unchanged: registry + CONTENT + dated spec amendments (A1–A4
precedents) + verify_feature per world.

## 9. Future Testing Strategy

- **Near-term:** 18A RCP = the integrated-product browser certification (the missing
  layer above the 1871-test battery); P13 adoption of the recorded candidates (3 RMX
  predicates + 3 MEE notes) per the registry's own law.
- **Standing:** battery-per-wave stays the law; money features always get the
  MEE/RMX-style certification wave (rupee-once/do-no-harm instruments now templated).
- **New layers to add over time:** a query-budget regression suite generalizing the
  page pins (watch the growth trend centrally) · post-deploy `verify_production` cadence
  (P19 runbook) · RCP re-runs as release gates for every future program (the 18A
  permanence rule).

## 10. Updated Risk Register

| Risk | Change |
|---|---|
| Uncommitted-tree exposure until P22 | UNCHANGED-HIGH — mitigations hold; argues for no scope before 22 |
| Deferred-feature memory loss | **CLOSED by this register** (FF-1..28 + the owning registers) |
| Doc drift | LOW — knowledge_sync live (6 guard catches auto-caught this stream); Phase 18 sweeps clear the accepted queue |
| Money regression in future features | LOW — census + ADR walls + certification-wave methodology now standard |
| RM-V2 scope gravity (pulling early) | Managed — vision doc + boundaries recorded in three phases' registers |
| Permission-layer perf on floor devices | NEW-LOW — FF-26 |
| Accountant role limbo | UNCHANGED-LOW — FF-25 |

## 11. Version Roadmap (PROPOSAL)

**V1.0** = what deploys at P20 (everything through Phase 17, certified by 18A) ·
**V1.1** = stabilization (flags ON · S6 · FF-25/26/28) · **V1.2** = operate-and-polish
(BOD wave 2 · MEE reports · holdings · pattern export · floor UX) · **V2.0** = the
programs era (RM-V2 · KOS · the money-future ADRs). Numbers are labels for planning —
the owner names real versions at the post-22 review.

## 12. Release Roadmap (PROPOSAL)

R0 (now→22): sweeps → RCP → deploy docs → DEPLOY → certificate → checkpoint · R1
(+~2-4 weeks): soak outcomes (flags, S6) + quick rulings · R2+: one owner-chartered
feature train per cycle, each ending with its RCP pass — release cadence = owner's
call at the roadmap review.

## Owner decisions required before ANY implementation

1. FFD-D1..D9 ratification (the frozen Phase-18 contract's decision pack) — including
   **D3: is THIS package the planning-doc-of-record?** (recommended yes).
2. Approve/amend the FF-register categorization (§2) and the roadmap/version/release
   proposals (§3/§11/§12) — all currently PROPOSALS.
3. The Phase-18 sweep scope confirmation (FF-1: regenerate the 558 + clear the queues —
   the contract's first-run reality-sync).
4. P13 candidate adoption (the 6 recorded predicates) — at P13's registry law.
5. Quick calls whenever convenient: FF-25 (accountant), FF-26 (permission cache),
   FF-28 (Material-Spend MenuItem).
