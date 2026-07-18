---
id: bundle-assembly-architecture-review
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# BUNDLE ASSEMBLY — ARCHITECTURE REVIEW (is Cutting still the truth?)
(2026-07-11 · owner-ordered challenge · REVIEW ONLY — zero code, zero
migrations, zero model changes · method: live simulation NKS-001, a
REAL 3-fabric-group product walked cut → derive → bundle → barcode →
one stitching stage on the running system, plus the bundle service
code read line-by-line · companion evidence:
CUTTING_CYCLES_ARCHITECTURE_CHALLENGE.md, same day)

> **🔒 OWNER-RATIFIED 2026-07-11** (with the Cutting-Cycles and
> Production-Component challenges, same day): verdict accepted;
> production architecture FROZEN; GAP 5 + the pool-grain refinement =
> implementation debts on the ledger, not architecture problems.

# VERDICT: **A — Cutting stays the production truth. But it is the
truth of PIECES, and it is the ONLY written truth needed.**
"How many complete garments exist" is a **DERIVED truth** — a read
over cutting truth × the Blueprint (min over mandatory patterns per
size) — proven live to the exact numbers of your examples. Bundle
Assembly is the **physical staging EVENT** (what got tied, when, from
which pieces): an append-only record of an act, never a second count
truth. Making Bundle Assembly a WRITTEN production truth (option B)
would create the one thing this architecture exists to prevent — two
tables claiming the same fact, drifting.

**No implementation justified** — no BUNDLE_ASSEMBLY_IMPLEMENTATION_
READINESS.md is warranted. Your instinct, however, was pointing at
something real: the bundle SERVICE layer never moved to the post-join
role the streams freeze already assigned it (new GAP 5 below), the
ops pool must feed at garment-equivalent grain (refines GAP 1), and
the derived complete-garment number has NO surface today. All three
are make-code-match-frozen-docs fixes on existing tables.

---

## 1 · The live world (executed, not described)

Product **NKS** ("DEV Nickar Shortfall") — REAL Blueprint: Body →
`body`, Panel → `panel`, Rib → `rib` (all mandatory, 1 piece/garment);
the real provider derived **3 blocking lanes**. Flow: Layering
(per_layer ₹1) → Cutting (per_piece ₹0.50, color+size) → Side Seam
Close (per_piece ₹1). Three masters, three rolls (navy/grey/black —
deliberately one color per fabric), Adda **NKS-001**. Cut = your
Example-1 numbers, split M/L:

| pattern | M | L | Σ |
|---|---|---|---|
| Body (navy) | 25 | 25 | **50** |
| Panel (grey) | 22 | 23 | **45** |
| Rib (black) | 24 | 24 | **48** |

## 2 · Your nine questions — answered from the walk

**Q1 — TRUE output of Cutting: PIECES.** Structurally provable: the
body lane cut 50 pieces having never seen a panel; no lane can know
garments. Cutting truth = `CuttingPieceBreakup` (size × color ×
pattern, per lane) + APSCPB (size × color, verified). 143 pieces
existed; zero garments existed. Cutting is not diminished by this —
pieces are exactly what it should assert, and it is the LAST point
where anything is *counted into existence*. Everything after is
arithmetic.

**Q1b — where does "45" live? NOWHERE as a row — everywhere as a
read.** Executed live:
```
complete(size) = min over mandatory patterns( Σ cut(size,pattern) ÷ pieces_per_garment )
  M: min(25/1, 22/1, 24/1) = 22
  L: min(25/1, 23/1, 24/1) = 23     → TOTAL 45 ✓ (your Example 1)
```
Inputs: `CuttingPieceBreakup` (exists) × `ProductPatternAssignment.
pieces_count` (exists). No new table is "mathematically unavoidable" —
the math ran tonight on the current schema. Persisting 45 would
violate derive-at-read AND go stale the moment a recut lands (proven
in §4: the same read said 48 five minutes later with zero writes to
any "truth" table).

**Q2 — TRUE responsibility of Bundle Assembly: the staging EVENT, and
it is also the natural reconciliation SURFACE — but a surface that
derives, never writes counts.** A bundle row must record the physical
act (worker tied 22 M garment-sets from THESE breakup rows) because
that act is history (append-only law). It must NOT be promoted to the
count-truth, because then body=50/panel=45 has two answers the day a
bundle is mis-entered, and settlement/pool/reports must pick one. One
writer per fact: pieces → cutting; garment-possible → arithmetic;
garments-staged → bundle rows. Three different facts, no overlap.

**Q3 — the reconciliation panel you listed:** every line of it derives
from existing tables, live-proven: Expected per pattern (layout ×
plies — the cutting console already shows it) · Actual per pattern
(breakup Σ) · Complete garments (the min — computed) · Incomplete/
leftovers (`count − consumed_count` — printed live: body M3 L2, rib
M2 L1, your Example 3's shape) · bundle breakup (CuttingBundleItem
rows) · ready-for-ops (= complete − already-drawn). Build it as a
READ-ONLY panel on the bundle screen when the floor asks — zero new
writers.

**Q4 — pools: sourced from cutting, DELIVERED at garment grain.**
Example 3 answered: downstream must hear **90, not 100** (here: 45,
not 143 and not 50). But the source stays cut truth — the
garment-equivalent min IS a read over it. Feeding from
bundle-confirmed rows instead would make sewing wait on data entry
(bundle typing) rather than on physical reality, and a forgotten
bundle row would starve the line. The live probe showed today's pool
is doubly wrong anyway (GAP 1: picked the panel lane by id-luck —
`available` said grey 22/23, navy 0, black 0; the number LOOKED right
only because panel happens to be the min). The already-open GAP-1 fix
must therefore be specified as: **assembly-ops availability =
garment-equivalent min per SIZE across all lanes** — not merely
"Σ pieces" (Σ would say 143: three-and-a-half times the sewable
truth). A second real grain fact fell out of the walk: **a garment
spans three cloth colors** — (cloth_color × size) cannot express
garment availability at all; SIZE is the garment grain, cloth color
is a component attribute. The system already half-knows this: OW-A's
stitching report with size-only lines (no color) was ACCEPTED and
paid correctly.

**Q5 — barcodes: raw cutting. Your Example 4 is the proof piece-
sourcing is RIGHT, not merely frozen.** Live: after the panel recut
(+3 M, +2 L), append covered **144–148 only**; the five leftover
bodies and ribs that had been waiting were **already named** (23–47,
120–143…) and kept their names through the wait. Had generation
followed bundle-confirmed truth, those pieces would have been nameless
inventory for days and the recut would have triggered a confusing
second naming ceremony for OLD pieces. Identity follows the physical
object, and the physical object exists at cutting — the Identity Law's
"birth certificate = APSCPB" was the correct call and this challenge
strengthens it. (Honest corollary recorded: on multi-piece garments,
148 identities ≠ 48 garments — piece-status rollups like "packed"
count pieces, so garment-level dispatch reports must divide through
the derive, a read-side concern for the Reports module.)

**Q6 — inventory: pieces are the stock truth; garment-equivalents are
a derived VIEW.** "143 pieces on the floor, of which 45 complete sets
+ 8 leftovers" — both sentences from the same tables, one stored, one
computed. Counting bundle-confirmed only would make the 8 leftovers
vanish from stock — they are real cloth the factory owns (M9's
ownership: inventory = truth of material, and leftover pieces are
material).

**Q7 — "how many Nickars did we manufacture today?" — NEITHER
cutting NOR bundling.** Manufactured = garments that CLEARED the line
(final-ops completions / packed counts). Cutting answers "cut",
bundling answers "staged", ops contributions answer "sewn", checking/
packing answer "manufactured". The honest report reads the stage the
question is about; the garment-equivalent derive gives the cut-basis
ceiling. (Today OW-A's 45 side-seam garments are the furthest
downstream truth on NKS-001.)

**Q8 — variance: at BOTH, each owning its own comparison.** Cutting
console: expected (layout × plies) vs actual pieces — exists, per
lane. Bundle/A360 surface: complete-garment-possible vs cut-per-
pattern (the min table above — names WHICH pattern is the bottleneck:
"Panel short by 5 vs Body"). Settlement reconciliation (S1.1/S5)
stays the money-side variance. Three variances, three existing homes,
all reads.

**Q9 — the 7-piece Shirt: the derive IS the convergence point, and it
scales as data.** min() over 7 patterns instead of 3 — same one-line
formula, zero engine change (the walk's formula never mentions how
many patterns exist). Bundle Assembly as a physical stage naturally
grows in IMPORTANCE (more components = more staging discipline) but
still writes only "what was tied". Cutting stays sufficient as truth
because the truth was never "garments at cutting" — it was pieces,
which is true for 1 pattern or 20.

## 3 · Your examples, run

| | Setup | System answer (live) | Where the rule lives |
|---|---|---|---|
| **Ex 1** | 50/45/48 | derive → **45** (M 22 + L 23) | arithmetic over breakup × Blueprint — computed, not stored |
| **Ex 2** | rib = 0 | pointer HELD at Cutting, **0 barcodes**, ops locked — probed twice mid-walk | the JOIN predicate (every blocking lane's cutting complete) — already the "zero complete garments = not finished" rule |
| **Ex 3** | 100/90/100 → 90 + leftovers | bundles staged 45 sets; leftovers derived from `count − consumed`: Body M3 L2 · Rib M2 L1 | bundle EVENT rows + existing consumed columns |
| **Ex 4** | recut completes the set | append **144–148 only**; old pieces kept names; derive 45 → **48** with zero truth-writes; pointer never regressed | piece-sourced identity + deficit append (M7) + the derive |

## 4 · What the challenge broke (implementation, not architecture)

**GAP 5 — the bundle write path never moved to its frozen post-join
role.** The streams PROPOSAL §2/3 + READINESS §4 froze: bundles become
adda-level, post-join, spanning streams (the schema shipped: `CuttingBundle.adda`
+ conditional uniqueness). The SERVICES did not move: `create_bundle`
and `add_pieces_to_bundle` still resolve ONE cutting lane
(`_get_or_create_cutting_stage_record` → multi-lane Addas get
*"specify which lane"* — live-hit on NKS-001) and both REFUSE once
that lane's cutting is complete (*"Stage already completed — bundles
locked"*) — i.e. **post-join bundling is impossible exactly where the
design says it begins**, and pre-join multi-lane bundling is refused
too. Single-lane products never noticed (legacy in-cutting bundling
still works — every world to date). The deferred "bundle-slip screen"
(receipt) hid this. In this walk the bundle event was simulated at
the ORM exactly per the shipped schema (adda-anchored, items with
`source_breakup`, consumed math mirrored) — it worked flawlessly,
which is the proof the SCHEMA is right and only the service/UI move
is owed.

**GAP 1 refined (pool formula).** The Cutting-Cycles challenge proved
the pool reads ONE arbitrary lane. THIS challenge proves fixing it to
"Σ pieces over lanes" would still mislead assembly ops (143 ≠ 45).
The correct frozen-law-compatible read for assembly-ops availability:
**per size, min over mandatory patterns of (Σ pieces across lanes ÷
pieces_per_garment), minus draws** — sourced from breakup rows +
`ProductPatternAssignment`, both existing. Single-pattern products
degrade to exactly today's per-piece math (min over one pattern =
Σ pieces — byte-identical, the compatibility proof). Grain: SIZE
(cloth color is a component attribute — proven by the accepted
color-less stitching report).

**Re-verified untouched:** money (expected earnings exact through the
whole walk: master B ₹105 across two Addas and a recut; OW-A ₹45 for
45 garments), costing freeze per lane, join law, no-regress, append
identity math, cancel-if-empty, history events. The bundle/pool gaps
sit entirely on the read/staging plane — not one rupee moved wrongly.

## 5 · Why option B (bundle = written production truth) loses

1. **Dual truth.** Cut counts exist; bundle counts would also claim
   production. First mis-typed bundle (or unbundled loose work — floors
   do sew loose pieces under deadline) ⇒ two answers, and pool/report/
   settlement must silently pick one. The drift class this project
   spent S1–S5 killing.
2. **Truth by data-entry.** Garments become "produced" when a clerk
   confirms a bundle, not when scissors cut cloth. Operator-authority
   law inverts: the floor's work waits on paperwork.
3. **Settlement re-plumbing for nothing.** Cutting masters are paid
   per cut piece (proven ₹-exact tonight); making bundles the truth
   either double-books (pieces AND bundles) or forces earnings to wait
   for bundling — both violate the frozen money boundary.
4. **It buys nothing the derive doesn't give.** Every number B wants
   (complete, leftovers, ready-for-ops) computed live tonight from
   existing rows, including through a recut. B's only unique offer is
   a *stored* copy of that arithmetic — i.e., a cache that can lie.
5. **Ex 2 already enforced.** "Zero complete garments = production not
   finished" is the join predicate; it fired twice tonight.

Hybrid C collapses into A: "bundle rows as event + derived counts as
truth" IS the current architecture once GAP 5's owed service move
lands.

## 6 · What the floor should eventually see (reads only, when asked)

```
A360 / Bundle screen — POST-JOIN (derive panel, no new writers)
┌ NKS-001 · Garment readiness ────────────────────────┐
│ SIZE M   Body 25 ✓ · Panel 22 ▲min · Rib 24 ✓ → 22  │
│ SIZE L   Body 25 ✓ · Panel 23 ▲min · Rib 24 ✓ → 23  │
│ COMPLETE-GARMENT SETS: 45 of 143 pieces             │
│ LEFTOVER: Body 5 · Rib 3 (waiting on Panel)         │
│ [Bundle M — 22 sets] [Bundle L — 23 sets]           │
└─────────────────────────────────────────────────────┘
Bottleneck named per size (the ▲min) — the manager's one question
("kis piece ki kami hai?") answered without a calculator.
```

## 7 · Final statement

- **A. Current architecture correct — YES**, with the sharpened
  sentence: *Cutting writes the piece truth; the garment truth is
  arithmetic; Bundle Assembly records the act of staging.*
- **B — rejected with evidence** (§5), while crediting what it saw:
  the missing derive surface, the wrong pool grain, and the stalled
  bundle service move are all real (GAP 5 + GAP 1 refinement) — and
  all are implementation debts against already-frozen design.
- **C — collapses into A.**

**No implementation justified. No readiness document produced.**
Owed fixes fold into the existing gap ledger, updated severity order:
**GAP 2** (cross-fabric cutting completion — blocks real multi-fabric
Addas at one line) → **GAP 1+grain** (assembly pool = garment-
equivalent min per size) → **GAP 5** (move bundle services post-join /
adda-level per the shipped schema + the derive panel) → **GAP 3**
(bare-URL 500) → **GAP 4 + UI laws** (lane scoping · greyed cancelled ·
Add-lane form).

**STOP — review only. NKS-001 and its data are DEV, disposable on
your word.**
