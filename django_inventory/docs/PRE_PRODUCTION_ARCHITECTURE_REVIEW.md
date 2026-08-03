---
id: pre-production-architecture-review
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# PRE-PRODUCTION ARCHITECTURE REVIEW
(2026-07-11 · Factory Driven Development · REVIEW ONLY, no code ·
ordered by the owner after Module 6; campaign modules 7–13 paused ·
companion docs: PRE_PRODUCTION_REDESIGN_PROPOSAL.md ·
IMPLEMENTATION_READINESS_PRE_PRODUCTION.md · DOCUMENT_ARCHIVE_REVIEW.md)

## 1 · The factory reality being tested

A product's pieces can belong to DIFFERENT fabrics. Nickar: Body ×2 +
Pocket ×2 on the body fabric; Panel ×2 on a second fabric. Each fabric
needs its own rolls, its own lay, its own approved layout, its own
pattern check, its own cutting — on its own clock, possibly its own
crew. The garment exists only when EVERY fabric group's pieces are cut.
This is general (Shirt: body/collar-rib/lining · Polo: body/rib ·
Cargo: shell/pocketing/waistband), not a Nickar special.

## 2 · What the CURRENT architecture actually assumes (evidence)

**The two halves of the system already disagree about this.**

**Pattern Intelligence is per-fabric-group EVERYWHERE (built that way
since Phase 8):**
- `PatternPiece.fabric_group` (pieces.py:41) — the Blueprint already
  declares Body/Pocket = `body`, Panel = `other` for the real Nickar.
- `ApprovedLayout.fabric_group` (layouts.py:45) — layouts are made and
  approved PER GROUP; the DCT Marker Plan opens per group (LAW-12
  cross-group import refusal).
- `ApprovedLayoutUsage` partial-unique on `(adda, fabric_group)`
  (layouts.py:128) — the Adda↔layout CONTRACT is already one-per-group.
- The M6 layering advisory provider returns `groups: [...]` — plural by
  contract.

**Production/ERP is single-stream everywhere:**
- `AddaStageRecord` = ONE row per `(adda, workflow_stage)`
  (unique_together, adda.py) — there can only ever be ONE Layering, ONE
  Pattern Design, ONE Cutting record per Adda.
- `Adda.current_stage` = a single pointer walked linearly by
  `advance_to_next_stage` (adda_service.py:138) over
  `WorkflowStage.order` — no notion of two lanes being open at once.
- `LayeringRecord` / `CuttingPatternRecord` / `CuttingRecord` are all
  OneToOne on that single stage record.
- `StagePoolSnapshot` / pool derivation walk a single upstream lane
  (`_upstream_pool_source` = nearest non-NONE stage).
- `fabric_group` appears NOWHERE in production models — the ERP flow
  literally cannot say which fabric a lay belonged to.

**The bundle finding (important):** `CuttingBundle`'s own PR8 spec
(cutting.py:415) says a bundle is *"one bundle per size, holding ALL
pattern × color × count items needed for that size"* — i.e. the
COMPLETE cut product. Your bundle philosophy is not a new idea; it is
the model's ORIGINAL intent. What broke it is anchoring: the bundle
hangs off ONE CuttingRecord, so under multi-stream reality it can only
ever contain one fabric group's pieces. Module 5's browser walk proved
this live — Lot-S/Lot-M held Front+Back panels but a Panel-fabric piece
could never have joined them.

**How did the dev worlds pass?** Every flow validated so far (T-Shirt,
Lower, 3-Patti, DEV-NICKAR-A1's M6 chain) laid ONE fabric. DEV-NICKAR's
Panel group existed in the Blueprint and in the layout library, but the
ERP walk flattened everything into one Layering — the mismatch was
invisible until you looked at the real factory again. Modules 1–6
validated the single-stream flow correctly; they could not have caught
this because no test data exercised two fabrics.

## 3 · Verdict: redesign JUSTIFIED — narrowly

The architecture must evolve, and the change is **confined to
pre-production** (Layering · Pattern Design · Cutting · Bundling):

1. It is a REAL factory workflow, stated with a real product, and the
   platform's own PI half already models it — the ERP half is the
   laggard, not the concept.
2. No workaround exists inside the current model: you cannot run two
   Layerings on one Adda (unique constraint), cannot attach a second
   fabric's rolls to a second lay, cannot express "cutting done" per
   fabric, cannot bundle across cuts.
3. The alternative (one Adda per fabric group) is worse: it splits one
   production order into fake orders, doubles settlement/costing
   surfaces, and still can't bundle a complete garment anywhere.

**What must NOT change (and doesn't need to):** operations stages
5–13. Their pools are dimension-scoped `(color, size)` piece counts and
pattern-blind — they consume "what pre-production produced" and do not
care how many lanes fed it. Worker truth (WST/WSC), earnings,
settlement, costing freeze, tracking history, the PI wall, all four
registries, the contract versions — untouched. This keeps the redesign
small and the constitution intact.

## 4 · Challenges to your assumptions (as requested)

- **"One cutting group = one approved layout / one layering."** Mostly,
  but not always: a big order may need SEVERAL lays in the same fabric
  group over days, and re-lays happen after fabric shortfalls. The
  stream concept should therefore be "one fabric group's LANE" that
  today holds one layering/pattern/cutting cycle (v1 = exactly your
  model), but whose shape doesn't forbid a second cycle later. The
  proposal keeps stream = `(adda, fabric_group)`; "N lays per stream"
  stays a future factory ask, not built now (YAGNI).
- **"Bundles only after ALL cutting groups finish."** Right as the v1
  rule, with one honest trade-off named: a strict global barrier can
  idle the floor (Body cut Monday, Panel cut Wednesday ⇒ nothing
  bundles until Wednesday). The true requirement underneath is
  BLUEPRINT-completeness per size — every mandatory piece present for
  that size. All-streams-complete is the simplest correct
  approximation of it, and per-size early bundling can be layered on
  later WITHOUT schema change (the bundle already itemizes per
  pattern×color; the gate is just a rule). v1 = your rule.
- **"Pattern Design shows too much."** Agreed, and it is purely a UI
  concern — ratio/optimization/statistics belong to Pattern
  Intelligence screens; the production console needs select → preview →
  confirm. No model change required for this part.
- **Naming.** "Cutting group" as a MODEL name collides with the
  existing `CuttingBundle`/cutting-stage vocabulary and with
  `StageCategory` grouping. The proposal uses **CuttingStream** —
  factory-honest ("the Panel stream"), unambiguous in code, and it is
  the concept you and the advisor both converged on independently,
  which is itself evidence it's the right shape.

## 5 · Risks + migration impact (what the proposal must answer)

| Risk | Where it bites | Mitigation direction |
|---|---|---|
| `AddaStageRecord` uniqueness widening | every `get(adda=…, workflow_stage=…)` call site on pre-production stages | stream-scoped accessors; ops stages keep NULL stream so their call sites are untouched |
| `current_stage` semantics while lanes diverge | A360, dashboards, sidebar states, `advance_to_next_stage` | pre-production becomes a PHASE (lanes shown per stream); linear pointer resumes at the join; advance gains one rule: "leave pre-production only when every stream is complete" |
| Bundle re-anchoring | Bundle currently FK→CuttingRecord | additive `adda` anchor + nullable legacy FK; backfill from existing data |
| Pool upstream walk | ops stage 1 draws from "Cutting" — now plural | first ops pool = Σ across streams' cutting outputs (same verified-else-good law, summed) |
| Reopen/downstream guards | S4-P5 guard walks stages linearly | guard becomes stream-aware for pre-production, unchanged after the join |
| Cost freeze | per-SR freeze already works | per-stream SRs each freeze; Adda cost = Σ (no law change — ADR-0009 untouched) |
| Reconciliation advisory | per cutting SR | per stream — better, not harder |
| Existing data | every existing Adda has single-lane SRs | data migration: one DEFAULT stream per existing Adda, existing pre-production SRs assigned to it — behavior byte-identical for single-group products |
| Barcode future (Option A vs B) | seq ranges per adda + per-bundle batches | both survive: batches stay per bundle×size×color; sequences stay per adda; nothing in the redesign consumes the sequence semantics |
| Settlement/money | reads contributions via task→SR | SRs multiply but the money law doesn't change; settlement was already per-contribution. MUST be re-verified in campaign modules 10–11 after the redesign |

## 6 · Conclusion

Justified, urgent (blocks honest validation of modules 7–13 for real
multi-fabric products), and small if scoped exactly to: a stream
entity + stream-scoped pre-production stage records + a join gate +
bundle re-anchoring + the three console simplifications. Everything
else stands. The smallest concrete shape is in
PRE_PRODUCTION_REDESIGN_PROPOSAL.md.

**STOP — review only; no code written.**
