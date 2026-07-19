---
id: feature-cutting
type: feature
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Where do 'pieces' come from — the moment cloth becomes countable, payable units?"
related: [feature-allocation, feature-stage-tracking, flow-cloth-to-garment]
---

# Cutting — where quantities are born

> 📂 [Features](README.md) · [LOS home](../README.md) — *pehle yeh page, phir code.*

## Business Purpose

Before cutting, the factory has *cloth* (rolls, kilograms, layers). After
cutting, it has *pieces* — countable units with a size and color that every
later number depends on: allocations, barcodes, worker pay, dispatch. Cutting
is the stage where **quantity truth is born**, which is why its output gets
the heaviest verification of any stage.

## Mental Model

> Cutting is the system's **mint**. Upstream is bulk metal; downstream is
> coined currency. Everything after cutting COUNTS pieces; nothing before
> cutting can. That's why the piece pool starts here, why barcodes derive
> from here, and why the verified breakdown — not anyone's report — is the
> single source downstream consumes.

## 💡 Samjho Aise

Darzi ki kainchi hi asli shuruaat hai. Kapda bichhaya (layering), naap ke
nishaan checklist se verify kiye (pattern design) — par jab tak kainchi
nahi chali, "kitne piece?" ka koi jawab nahi. Kainchi chali → ginti aayi
→ ab usi ginti par poora karkhana chalega: bundle, barcode, batwara, paisa.

## Technical Deep Dive

**The chain of records** (vocabulary is everything here — full table in
[GLOSSARY](../../GLOSSARY.md)):

```
LayeringRecord (rolls attached, leftovers MANDATORY at complete)
  → CuttingPatternRecord ("Pattern Design": checklist + photo/video proof,
                          FIXED-per-Adda pay — code keeps name cutting_pattern)
  → CuttingRecord + CuttingPieceBreakup   per-(size, color, pattern) counts
  → CuttingBundle / CuttingBundleItem     size-grouped physical containers
  → AddaProductSizeColorPieceBreakdown    THE final verified per-(size,color)
        (APSCPB)                          snapshot — everything downstream
                                          consumes THIS, nothing else
```

**CuttingStream — one lay→pattern→cut cycle** (identity
`(adda, fabric_group, sequence)`): seq 1 derives from the product Blueprint;
seq >1 is a *declared management act* with a mandatory reason (split lay /
recut / additional production — reasons are DATA, not notes). The JOIN rule:
bundles/barcodes/downstream ops unlock only when every blocking lane's
cutting completes; post-join lanes append, never regress. 🔒 Owner-ratified:
**sequence IS the production cycle — no third abstraction.**

**Why APSCPB is sacred:** it is the *verified* piece count — the input to
barcode generation (`preview_barcode_batches`), the cutting stage's pool
good ([allocation](allocation.md) — read directly, never copied into a
snapshot), and the denominator every "paid vs produced" reconciliation
trusts. `_materialize_breakdown` writes it from the cutting record;
`layout_reconciliation` + `get_suggested_breakup` compare it against the
pattern layout so a typo'd count surfaces BEFORE it becomes downstream truth.

**Access:** cutting is **skill-gated** (`_ensure_cutting_skill`), not
role-gated — a worker with the cutting skill operates it; completing is
management-checked separately ([people-and-roles](../project/people-and-roles.md)).

**Where the money isn't:** cutting workers report through the SAME
stage-tracking door as everyone (WSC lines, color/size/qty) — cutting has
no special pay path. The stage's `processing_cost` freeze is cost-truth
(ADR-0009), separate from worker earnings. Three ledgers of truth — piece
counts (APSCPB), work claims (WSC), stage cost (frozen snapshot) — meeting
only at settlement.

## Debugging Guide

| Symptom | Start |
|---|---|
| Downstream counts look wrong | APSCPB first — it's the single source; then `layout_reconciliation` for cut-vs-layout drift |
| Barcode ranges don't match pieces | `preview_barcode_batches` reads APSCPB — regenerate preview, compare |
| "Second stream appeared" | By design — check its mandatory reason (split/recut/additional); seq >1 is a declared act |
| Bundle totals ≠ breakup | Bundles are physical grouping of the SAME pieces — itemization drift = data-entry, reconcile against breakup |

## Change Impact

Barcode generation (reads APSCPB) · pool source for cutting
(`pool_service.pool_good` handler) · stream JOIN logic · layering leftovers
· Pattern-Design checklist flow · reconciliation views · production test
suites (cutting/stream/R10-B generic).

## AI Implementation Pitfalls

- ❌ Writing a second "final count" table or copying APSCPB anywhere — single source, owner-locked.
- ❌ Creating streams implicitly — seq >1 REQUIRES a declared reason; reasons are data.
- ❌ Skipping leftover capture at layering complete — mandatory; leftovers are tracked cloth, not waste.
- ❌ Treating "Pattern Design" rename as a code rename — UI label changed (R8); internal code stays `cutting_pattern`.
- ✅ Always verify: breakdown ≡ barcode preview ≡ pool good on a test Adda after touching any of the three.

## Interview Notes

*Interview Signal: 🟡 Mid — pipeline data-modeling.*

**Q. "A manufacturing pipeline where downstream depends on upstream counts — how do you keep the counts trustworthy?"**
- *Short:* One verified snapshot table as the single source; everything downstream reads it; reconciliation surfaces drift before hand-off.
- *Senior:* Name the moment quantity is BORN and put your verification there — errors are cheapest at the source. Make exceptional flows (recut, split lay) first-class declared acts with reasons-as-data, not silent edits, so the audit trail explains every deviation.
- *Project example:* APSCPB as the mint's output; CuttingStream seq>1 with mandatory reasons; layout_reconciliation catching typos pre-downstream.
- *Follow-ups:* "Why not recount at every stage?" (the pool inherits verified counts — recounting reintroduces drift) · "Partial recut of 2 sizes?" (new stream, reason=recut, JOIN rule holds the rest).

## 🧠 Remember This

Kainchi = taksaal (mint). Ginti yahin janamti hai, aur uska EK hi
janam-patra hai: APSCPB. Doosri kainchi chalani ho to wajah likhni padegi
(stream seq>1). Neeche ka sab kuch isi ginti ka byaaj hai — barcode,
batwara, paisa.

## 30-Second Revision

- Chain: Layering → Pattern Design (checklist, fixed pay) → Cut (breakup) → Bundles → **APSCPB**
- APSCPB = single verified source: barcodes + cutting's pool + reconciliations
- CuttingStream (adda, fabric_group, seq); seq>1 = declared act + reason; JOIN gates downstream
- Skill-gated access; workers report via the ONE stage-tracking door
- Cost freeze (ADR-0009) ⊥ worker pay ⊥ piece counts — meet only at settlement

## DSA & Complexity

Two structures hide in the cloth. **Fork-join:** CuttingStreams are
parallel lanes forked from one Adda; the JOIN rule ("downstream unlocks
only when every blocking lane's cutting completes") is a **barrier
synchronization** — the same primitive as `Promise.all` / thread joins,
here made of fabric. Post-join lanes append-only = no rollback past a
barrier. **Partitioning:** the breakup is a partition of total pieces by
(size, color, pattern) — and APSCPB being the SINGLE materialized
partition is why downstream sums always reconcile: one partition, many
readers, zero recounts. Interview framing: "parallel workstreams with a
completion barrier + one canonical aggregate at the merge point."

## Implementation References

- Design: [docs/CUTTING_STREAM_LIFECYCLE.md](../../docs/CUTTING_STREAM_LIFECYCLE.md) (streams) · [docs/production/CUTTING_PATTERN.md](../../docs/production/CUTTING_PATTERN.md) · vocabulary: [GLOSSARY](../../GLOSSARY.md) · lifecycle: [PKM §5](../../docs/PROJECT_KNOWLEDGE_MAP.md)

## Code References
- `config/production/stages/cutting/service.py` (`_materialize_breakdown`, `layout_reconciliation`, `preview_barcode_batches`) · streams in production models

## Related Concepts

[allocation](allocation.md) · [stage-tracking](stage-tracking.md) ·
[flow: cloth-to-garment](../flows/cloth-to-garment.md)
