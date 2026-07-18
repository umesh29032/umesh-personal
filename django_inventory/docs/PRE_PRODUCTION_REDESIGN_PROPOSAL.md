---
id: docs-pre-production-redesign-proposal
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# PRE-PRODUCTION REDESIGN PROPOSAL — Cutting Streams
(2026-07-11 · smallest generic change · REVIEW ONLY, no code ·
depends on: PRE_PRODUCTION_ARCHITECTURE_REVIEW.md)

## 1 · The one new concept: CuttingStream

> **A CuttingStream is one fabric group's independent pre-production
> lane inside one Adda: its rolls → its lay → its pattern check → its
> cut. The Adda leaves pre-production only when every stream is
> complete. Streams are DERIVED FROM DATA — never from product names.**

```
CuttingStream(adda, fabric_group, status)
  status: open → cut_complete
  derived at Adda creation:
    streams = DISTINCT fabric_group of the product's MANDATORY
              Blueprint pieces           ← pure data, zero engine names
```

A single-fabric product derives exactly ONE stream and behaves
byte-identically to today. That is the genericity proof and the
backward-compatibility proof in one sentence.

## 2 · The smallest schema change (3 moves, all additive)

1. **New table `CuttingStream`** — (adda FK, fabric_group, status,
   timestamps). Small, focused, single responsibility.
2. **`AddaStageRecord.stream`** — nullable FK. Pre-production stages
   (layering / cutting_pattern / cutting) get stream-scoped records;
   uniqueness becomes `(adda, workflow_stage, stream)`. Every OTHER
   stage keeps `stream = NULL` and its existing one-row-per-stage
   truth — ops call sites untouched.
3. **`CuttingBundle.adda`** — direct anchor (legacy `cutting_record` FK
   stays, nullable). A bundle is the Adda's complete-product container
   again (its own PR8 spec), free to hold items from every stream.

Nothing else changes shape. LayeringRecord/CuttingPatternRecord/
CuttingRecord stay OneToOne on their (now stream-scoped) stage record.
Rolls attach per stream's layering exactly as today. Costing freezes
per stage record as today (Adda cost = the same Σ it always was).
Worker tasks/contributions hang off stage records as today — the money
law never notices.

## 3 · Flow semantics

```
                       ┌─ Stream body:  Layering → Pattern → Cutting ─┐
Adda created ──────────┤                                              ├──▶ JOIN ▶ Bundling ▶ Barcode ▶ ops … ▶ Dispatch
 (streams derived)     └─ Stream other: Layering → Pattern → Cutting ─┘
                          (each lane independent: own rolls, own crew,
                           own layout contract, own clock, own reopen)
```

- **Within a stream**: exactly today's three-stage walk, per stream.
  Start/complete/reopen gates, helper-completion law, worker reports,
  verification, cost freeze — all unchanged, just scoped.
- **The JOIN**: one derived rule — `all streams cut_complete`. Until
  then the Adda is in the *Pre-production* phase; `current_stage`
  resumes its familiar linear walk from Bundling onward. One new guard
  in `advance`-land; no DAG engine, no workflow rewrite (deliberately —
  a general DAG is over-engineering for a two-phase reality).
- **Bundling** (restored to its original meaning): after the join,
  bundles are created per size, itemized per pattern×color across ALL
  streams. "Nickar Size L bundle = Body ×2 + Pocket ×2 + Panel ×2" —
  only now the product physically exists.
- **Barcode**: unchanged today. Batches stay per bundle×size×color
  with per-Adda sequence ranges — which keeps BOTH your future options
  open: Option A (one 1–800 sequence per Adda) is exactly the current
  numbering; Option B (size/color/bundle-aware codes) already has
  every needed fact on the batch row. Nothing here consumes or
  constrains those semantics.
- **First ops pool**: Σ of every stream's cutting output under the
  same verified-else-good law (a sum, not a new concept).

## 4 · Real examples (all pure configuration)

| Product | Blueprint fabric groups (data) | Streams derived |
|---|---|---|
| **Nickar** | Body ×2, Pocket ×2 → `body` · Panel ×2 → `other` | 2 — body(Body+Pocket) · other(Panel) |
| Lower / T-Shirt (today) | all pieces → `body` | 1 — identical to current behavior |
| Shirt (future) | body+sleeve+pocket → `body` · collar+cuff → `collar_rib` · lining → `lining` | 3 |
| Polo (future) | body+sleeve → `body` · collar+rib → `rib` | 2 |
| Cargo (future) | shell pieces → `shell` · pocketing → `pocketing` · waistband → `waistband` | 3 |

New garment = Product + sizes + Blueprint (pieces with fabric groups) +
layouts + ERP stage config. **Zero engine code** — if any future
garment needs a new stream TYPE in code, that is the architectural
failure the constitution names.

Nickar walk-through, concretely: Adda NICKAR-001 derives streams
`body` and `other`. Monday: body stream — rolls attached, 40-layer
lay, Body layout confirmed (select → preview → confirm), cut, 160
Body + 160 Pocket pieces, stream `cut_complete`. Wednesday: other
stream — different rolls, its own lay, Panel layout, cut, 160 Panels,
stream `cut_complete` → JOIN unlocks → Size-L bundle holds Body ×2 +
Pocket ×2 + Panel ×2 per garment → barcodes → Panel Join starts with
the full piece pool.

## 5 · Console simplification (UI layer only, same change-set)

- **Pattern Design**: select approved layout → preview → confirm →
  submit. Ratio percentages, optimization statistics, layout
  percentages move OUT of the production console (they remain on the
  Pattern Intelligence screens where they belong). Checklist + photo
  evidence + worker report stay — they are floor laws, not statistics.
- **Layering**: already close; keep exactly the operator facts (rolls,
  color, weight, verified width, layer count, spread length, leftover,
  snapshot) — per stream. Remove nothing load-bearing; add nothing.
- **Cutting**: expected (from the stream's layout) vs actual vs
  pending · mandatory Blueprint pieces present? · size/color breakup.
  Suggestion panels shrink to those numbers.
- All three consoles render inside their STREAM's context (a lane
  header: "Layering — Panel fabric").

## 6 · What explicitly does NOT change

Single writers · derive-at-read · immutable approved layouts ·
settlement-only money · operator authority ("your numbers stand") ·
helper-completion + report-before-complete laws · genericity guard ·
the ADR-H wall and all four provider registries · adr-c contract
versions · pools/allocations for ops stages · WorkflowStage library and
per-product ordering (streams are INSTANCES of the same three stages,
not new stage types) · flags (all stay OFF).

## 7 · Migration (additive, reversible until cutover)

1. Schema: new table + two nullable FKs + widened unique constraint.
2. Data: every existing Adda gets ONE stream (`fabric_group` = the
   product's dominant/only group); its existing pre-production SRs and
   bundles are assigned to it. Single-group products — the entire
   current dataset — behave byte-identically after migration.
3. No destructive step anywhere; legacy `cutting_record` FK on bundles
   retained for history.

## 8 · Why this specific shape (and not the alternatives)

- **Not "Layering 1 / Layering 2" stages**: duplicating stage rows per
  fabric bakes a COUNT into configuration, breaks the stage library's
  meaning, and each new product would need flow surgery. Streams keep
  ONE Layering stage definition with N instances derived from data.
- **Not a general workflow DAG**: the factory reality is exactly two
  phases (parallel pre-production, then a linear line). A DAG engine
  is the over-engineering the developer philosophy forbids.
- **Not one Adda per fabric group**: splits one real order into fake
  orders; settlement, costing, tracking and bundling all fragment; the
  complete-product bundle becomes impossible anywhere.
- **Yes streams**: it is the concept BOTH the owner and the advisor
  arrived at independently, it matches the PI side's existing
  per-group grain (layout contracts are already `(adda, fabric_group)`
  — the stream is the ERP-side mirror of that same key), and its v1
  cost is one small table + one nullable FK + one join rule.

**STOP — proposal only; implementation waits for the readiness gate +
your approval.**
