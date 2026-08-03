# IMPLEMENTATION MASTER PLAN — CERTIFICATION (Phase 2 · 2026-07-06)

> Cross-check of [IMPLEMENTATION_MASTER_PLAN.md](IMPLEMENTATION_MASTER_PLAN.md)
> against: **MANUFACTURING_V1_FREEZE.md · 06_BLUEPRINT_V3_FINAL.md · ADR pack
> A–H · AI_PATTERN_INTELLIGENCE_KICKOFF.md.**

## 1. vs MANUFACTURING_V1_FREEZE (frozen contracts §7)

- Production files touched by the ENTIRE plan: settings/urls/importlinter
  registration (P1 wiring, same class as the machines app precedent) + the
  D2/D3 **owner mini-ADR additive nullable fields** — explicitly owner-gated,
  reversible, and named in the plan; **no other production file in any phase**
  (each phase's §4 says so). ✅
- No money paths anywhere; ₹ rendering is honest-NULL until D3 data exists. ✅
- Rollback strategy §2.2 proves the freeze guarantee: purity + untouched
  baseline suite gate every phase — a patterns_ai rollback cannot move
  manufacturing. ✅
- Enforcement flags, pools, verification, settlement: never referenced as
  write targets by any phase. ✅

## 2. vs Blueprint V3 (architecture CLOSED)

- Phase scopes = V3 roadmap §7 verbatim (memory → capture → generation →
  assistant → hardware → gated-ML); no phase adds an entity, changes a grain,
  or reorders the eras. ✅
- Constitution honored structurally: F3 (§2.4 migration gate), F4/F1 (P0
  adapters + P1 purity scaffold), F5 (rollback never deletes knowledge),
  F6 (P1 outcomes = facts; P4 computes at read), F2 (biography visible at P1
  exit). ✅
- The plan's only sequencing addition — ADR-C spec written in P1 while first
  geometry row waits for P2 — implements the "P1 gate" wording without
  weakening it (spec-before-row preserved). ✅

## 3. vs ADR pack A–H

| ADR | Plan compliance |
|---|---|
| A | P0 = the bake-off exactly as specified; winner + losers + BLF floor kept as adapters (P3) ✅ |
| B | worker built in P3 only; cap-1; orphan tests; runbook unit; governance note carried ✅ |
| C | spec doc = P1 output and P2 gate; goldens = round-trip tests (P2/P4) ✅ |
| D | statuses/promotion exercised in P3 exit criteria; single-writer tests every phase ✅ |
| E | POC mat commissioned even in P0; tiers re-validated on the factory table in P2 before UI ships; P5 requires re-proven tiers ✅ |
| F | compute runtime + vendored artifacts land P2; no-network test scaffold from P1; poc/ has its own pinned venv ✅ |
| G | media tree at P1; integrity sweep + budget at P2; knowledge-class never deleted on rollback ✅ |
| H | app wiring at P1 with importlinter (no ignores) + purity test + SidebarItemRule per URL; D8 already executed (ops-master §11 amended 2026-07-06) ✅ |

## 4. vs Kickoff Contract

Frozen contracts §5: all inherited (see 1–3). Owner Vision §10: every item has
a landing phase — manual markers/memory (P1), capture doors (P2), generation +
alternatives + previews (P3), confidence + recommendations + Product-360 (P4),
plotter/printing (P5), promotion (P3), offline reproducibility (P0/P2 via
ADR-F). Global rules: one-phase-per-block, STOP lines, completion reports, and
rule-11 STOP are written into the plan itself (§2.6, per-phase exit criteria,
§5). ✅

## 5. Structural checks

- **No contradiction** found against any governing document.
- **No cyclic dependency:** §1 graph is a DAG (verified by inspection: P0→P3
  is the only cross-edge; mini-ADRs and purchases are leaf inputs).
- **No missing dependency:** every phase's Inputs are produced by earlier
  phases or explicit owner actions (D2/D3/D7, hardware) — each named.
- **No impossible milestone:** every milestone = one phase's exit criterion;
  none requires data or tooling its phase doesn't produce; P5/P6 are
  explicitly gated on external reality.

## 6. CERTIFICATION

**The Implementation Master Plan is CERTIFIED consistent with the freeze, the
closed architecture, the ADR pack, and the kickoff contract — ready for owner
approval.**

*Phase 2 ends here. Phase 3 (IMPLEMENTATION_READINESS_REPORT) does not start
without explicit owner approval.*
