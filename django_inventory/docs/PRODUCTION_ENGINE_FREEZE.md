---
id: docs-production-engine-freeze
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# PRODUCTION ENGINE FREEZE — certification
(2026-07-11 · production-hardening phase CLOSED · full battery
**1479/1479 OK** · this document certifies the frozen state before
campaign Modules 11–13; it designs nothing)

## CERTIFICATION

The pre-production engine — **Cutting Streams (lanes = production
cycles) · Bundles · Barcodes · Tracking · Inventory** — is hereby
**FROZEN**. The architecture was independently challenged four times in
one day (Cutting Cycles · Bundle Assembly · Production Component ·
Final Implementation Audit — all owner-ratified verdict A) and the
implementation-debt ledger those challenges produced is now **CLOSED**:

| Gap | What was owed | Shipped as | Proof |
|---|---|---|---|
| **GAP 2** | lane-blind color/pattern-record validation blocked cross-fabric cutting completion | completion validations lane-scoped (`_pattern_record_for_adda(…, stream)` / layering-color per lane) | grey lane completed via the real console — "Lane cut recorded (9 pieces)" → join fired, 21 identities across 2 fabrics; `CrossFabricCompletionTests` |
| **GAP 1** | ops pool read ONE arbitrary lane; pieces ≠ sewable sets | `_upstream_pool_sources` = Σ over every lane + **garment-equivalent min per SIZE** cap (registry #6 `MANDATORY_PATTERNS_PROVIDER`; fail-open; single-component byte-identical) | LOWER-002 available(S) 0→2.00 (recut pieces allocatable); SHA-001 = 40 sets both colours over 5 lanes; `test_gap1_pool` 6/6 |
| **GAP 5** | bundle services never moved to their frozen post-join/Adda-level role | all six writers gated on `preproduction_joined` + anchored (adda, size); cross-lane consumption; (bundle, pattern, colour) increment + group invariant; **Garment Readiness panel** (derive-only) + one-tap `bundle_ready_sets`; initial join generation now logs its audit event | live tap: "Bundled 9 complete garment set(s) — bundle 16 now holds 18 pieces" + instant re-derive; NKS 48-set panel (Rib ▲); SHA 7-component 40-set panel; `test_gap5_bundles` 7/7 |
| **GAP 3** | bare multi-lane console URL / A360 embedded tab = 500 | render-path ambiguity → **lane picker** (44 px chips with reasons); POST ambiguity refusal stays law | picker live on the bare URL AND inside the embedded tab |
| **GAP 4** | worker cross-lane read exposure · cancelled lanes hidden · no Add-lane flow · phase-count · label | worker lane **isolation** (only own lanes; sibling by URL = 403; single own lane auto-selects, zero lane vocabulary) · cancelled lanes **greyed with reason** (§7) · **Add-lane + cancel-if-empty** exactly per lifecycle §1–§9 (sole writers `add_stream`/`cancel_stream`, `STREAM_ADDED`/`STREAM_CANCELLED` events, tracking 0018) · joined ⇒ pre-production reads complete · "Payments" label | XFB-002: form → "Lane added: body (lane 2)" → card cancel → greyed "(Declared twice while planning…)"; SHA-001 "Pre Production 3/3" + greyed cancelled trim lane; `test_gap4_lanes` 13/13 |

**Full battery after the final gap: 1479 tests, OK.** Genericity guard
green; the purity wall (production never imports patterns_ai) enforced
itself twice during the hardening and won both times.

## The frozen architecture, one page

```
Product
├─ ProductPattern            = the PRODUCTION COMPONENT (owner-ratified)
│    └─ PatternPiece(.fabric_group = LAY-ROUTING attribute · is_optional)
├─ CuttingStream(adda, fabric_group, sequence)   = ONE production CYCLE
│    seq 1 derived from the Blueprint (registry #5) · seq>1 DECLARED with a
│    mandatory reason (reasons are DATA) · blocking = group has mandatory
│    pieces · cancel-if-empty = the only mutation · NO status column
├─ per lane: Layering → Pattern Design → Cutting   (own rolls · own crew ·
│    own frozen cost · own earnings · per-cycle trio discipline)
├─ JOIN (derived predicate, no memory): every blocking lane's cutting
│    complete → pointer resumes; late lanes append, never regress
├─ CUT TRUTH = pieces (CuttingPieceBreakup per component ·
│    APSCPB verified per size×colour)   — the ONLY written count truth
├─ COMPLETE GARMENTS = ARITHMETIC (min over mandatory components ÷
│    pieces-per-garment, per size) — derive-at-read, never stored
├─ BUNDLE = the physical STAGING EVENT (post-join, Adda-level,
│    spans lanes; records the act, never a second truth)
├─ BARCODE = permanent meaning-blind PIECE identity ({ADDA}-{SEQ},
│    Max+1 append forever, lazy biography rows, terminal statuses)
├─ TRACKING = the read-side memory (append-only history reconstructs
│    every story: lanes+reasons, voids, corrections, settlements)
├─ INVENTORY = pieces + rolls/remnants stock truth; garment view derives
└─ OPS pools = garment-equivalent capacity per SIZE (Σ over lanes);
     money NEVER here — settlement is the only money boundary
```

Roles: **workers perform work** (their task, their lane, their pieces —
no streams/derives/architecture vocabulary anywhere in their UI) ·
**managers manage production** (lane cards, readiness, add-lane,
consoles) · **owners observe** (A360, history, money surfaces).

## Browser proofs on file (scratchpad screenshots + this session's logs)
DEV worlds NKB-001 · NKS-001 · SHT-001 · SHA-001 · XFB-001/002 —
multi-cycle, multi-fabric, optional-component, shortfall, recut,
additional-production, cancelled-lane, one-tap-bundle, lane-picker and
isolation walks, desktop + 390 px phone, all through the real consoles.

## Change control from this moment
Same rule as MANUFACTURING_V1_FREEZE: owner-approved ADR or recorded
owner decision only. A change request must first prove a REAL factory
workflow impossible within this design (live evidence, not theory).
No new core models, ownership boundaries, abstractions, or duplicate
truths. The five single-writer families (streams · stage records ·
breakups/bundles · identities · history) stay exactly as named in the
GUIDE.

## Remaining campaign (runs ON this frozen engine)
- **Module 11 — Settlement** (dress-rehearsed end-to-end in the final
  audit: rerate → finalize → armor → reverse → supersede, byte-exact)
- **Module 12 — Reports** (the derive surfaces — garment-equivalent,
  component bottlenecks, cut-vs-manufactured grains — belong here)
- **Module 13 — Costing**

## Known future work (recorded, deliberately NOT built)
Owner-decision findings: remnant re-issue workflow · roll damage
status · A360 worker-reachability class (with exports-list) ·
barcode-stage roster-after-start (resurfaces at Modules 10–11 per the
module-5 ruling — payroll validated it; settlement re-checks) ·
per-size early join (future predicate swap, schema ready) · S6
reported_quantity retirement (post-deploy, soak-gated) · enforcement
flags (`ENFORCE_ALLOCATION_BOUND`, `ENFORCE_SETTLEMENT_RECONCILIATION`,
layout gates) ship OFF per the rollout runbook · UI-label sweep
"Production Component" across older pattern screens (glossary + new
surfaces already speak it) · export-code concurrent mint (documented
floor-scale limitation).

## Constitutional statement
Single writers · append-only history · derive-at-read · operator
authority ("your numbers stand") · settlement-only money · generic
engine (strings and counts, never names) · YAGNI · honest data · no
duplicate truths. Every one of these was exercised — and several
enforced themselves against this very hardening work — during the four
challenges and five gap closures certified above. **The architecture is
the constitution. Reality is the architect. The production engine is
frozen.**
