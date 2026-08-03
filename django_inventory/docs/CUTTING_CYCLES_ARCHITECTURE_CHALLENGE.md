---
id: cutting-cycles-architecture-challenge
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# CUTTING CYCLES — ARCHITECTURE CHALLENGE (planned multi-lay production)
(2026-07-11 · owner-ordered challenge of the FROZEN Cutting Streams
architecture · REVIEW ONLY — zero code, zero migrations, zero model
changes were made · method: every stream document re-read
[PRE_PRODUCTION_ARCHITECTURE_REVIEW / REDESIGN_PROPOSAL / FINAL_REVIEW /
CUTTING_STREAM_LIFECYCLE / IMPLEMENTATION_READINESS / STREAMS_RECEIPT]
+ the live code [adda_service · pool_service · cutting/layering/pattern
services · handlers · views] + a REAL simulated factory world executed
against the running system — not theory)

> **🔒 OWNER-RATIFIED 2026-07-11** (with the Bundle-Assembly and
> Production-Component challenges, same day): verdict accepted;
> production architecture FROZEN; the four gaps = implementation debts
> on the ledger, not architecture problems.

# VERDICT: **A — the current Cutting Streams ARE sufficient.
The `sequence` column IS the Production Cycle.**
No second abstraction is missing. But the challenge caught the
implementation lying to the architecture in FOUR places — one of them
(the ops pool read) breaks the exact sentence the freeze promised.
Every finding is a make-code-match-the-frozen-docs fix; none needs a
new concept, a migration of meaning, or a redesign.

---

## 1 · The question, answered first

You asked: should there be `Adda → CuttingStream → ProductionCycle →
lay/pattern/cut`, where Stream answers *"what is being cut"* and Cycle
answers *"how many independent lays"*?

**That hierarchy already exists — it is just spelled differently:**

| Your proposed concept | Where it lives TODAY | Proof |
|---|---|---|
| Stream ("what is being cut") | `fabric_group` **string** on the lane row (data fact from the Blueprint) | provider derives `body` / `panel` from `PatternPiece.fabric_group` — proven live at NKB-001 creation |
| Production Cycle ("which independent lay") | `sequence` **integer** — `CuttingStream(adda, fabric_group, sequence)` | body seq 1 / seq 3 / seq 4 each walked their OWN lay→pattern→cut with own crew, rolls, costs, earnings |
| lay → pattern → cut under the cycle | stream-scoped `AddaStageRecord` trio, unique `(adda, workflow_stage, stream)` | 12 trio records across 4 live lanes on NKB-001 |

A `CuttingStream` row **is** one cycle. The "stream" as you mean it
(the fabric lane as a whole) is the *group of rows sharing a
fabric_group* — a GROUP BY, not a table. Making it a table would add a
second parent that carries **zero information** the pair
`(fabric_group, sequence)` doesn't already carry, plus a new FK to
migrate, new single-writer rules, and a new join in every lane query.
The frozen FINAL_REVIEW §1 already fought this exact battle:
*"A 'cycle below the stream' was considered and REJECTED: the stream
IS the cycle."* The live walk below confirms that decision was right —
everything the factory needs (parallel masters, per-cycle earnings,
per-cycle cost truth, append barcodes, join discipline) already
happens on the two-level model.

**And planned production was already in the frozen lifecycle**:
LIFECYCLE §3 lists **"Split lay — fabric arriving in parts / planned
multi-day lay"** as a standard reason. Reasons are DATA. "Recut",
"Additional production" and "Planned cycle 2" are the SAME ROW with a
different sentence stamped on it — proven live in §3-E below, where
one audit event lists both kinds side by side.

## 2 · The live world (created for this challenge, all via services)

Product **NKB** ("DEV Nickar Big") — REAL Blueprint pieces: Body +
Pocket → `fabric_group='body'`, Panel → `'panel'`; real provider
derived **2 blocking lanes** at Adda creation (no mock). Flow:
Layering (per_layer ₹1, non-payable) → Pattern Design (fixed ₹100,
payable) → Cutting (per_piece ₹0.50, payable, color+size grain) →
Side Seam Close (per_piece ₹1, payable, color+size). Cast: cutting
masters **A, B, C** + helper (all fresh DEV users), manager = you.
4 rolls (2× navy body, 1 grey panel, 1 navy reserve). Adda
**NKB-001**.

Cycles used: body **seq 1** (Cycle 1, 40 layers, master A) · body
**seq 3** (planned Cycle 2, 30 layers, master B — seq 2 was
double-declared by mistake and **cancelled empty**, exercising
lifecycle §9.4 live: reason stamped, excluded from the join, number
never reused) · **panel seq 1** (20 layers, master C) · body **seq 4**
(Scenario E, declared AFTER the join).

## 3 · Scenario evidence (executed, not described)

### A — three cycles in parallel, full walk
- **Three lays open simultaneously**, three different masters, three
  different rolls — the system held three open layering records at
  once and completed them 40/30/20 layers.
- Pattern ceremony ran **per cycle** (photo + size allocation +
  worker report + helper completion ×4 lanes total) — each cycle's
  marker check is real paid work: fixed ₹100 froze per lane.
- Cutting truth per cycle: C1 = 240 pieces (Body+Pocket S/M navy),
  C2 = 160, Panel = 200 (grey). `CuttingPieceBreakup` rows per lane;
  worker reports per (color, size).
- **JOIN discipline**: after C1 + Panel were cut, the Adda pointer
  HELD at Cutting and **zero barcodes existed**. Only when the last
  blocking cycle (C2) completed did the join fire → pointer moved to
  Side Seam Close → **one meaning-blind sequence 1–600** in four
  batches (S-grey 1–100 · S-navy 101–300 · M-grey 301–400 · M-navy
  401–600). Note S-navy = **200 = C1's 120 + C2's 80 merged**: pieces
  are fungible within (size, color) exactly as the Identity Law froze.
- **Frozen cost per cycle** (ADR-0009): layering ₹40 / ₹30 / ₹20 ·
  pattern ₹100 ×4 · cutting ₹120 / ₹80 — every cycle carries its own
  immutable cost row; Adda cost = the same Σ it always was.

### B — same master across cycles
Master A worked Pattern on ALL lanes + Cutting on C1 + the whole E
cycle: expected earnings = **₹570.00 exact** = 4×₹100 pattern +
₹60+₹60 (C1 cutting 240 pc) + ₹50 (E cutting 100 pc). Master B ₹80,
Master C ₹100, helper ₹0 (completion authority ≠ earning — the helper
law held). Every line lane-labelled in the payroll read layer. Money
needed ZERO special handling for cycles: a cycle's tasks are just
stage-record tasks.

### C — Cycle 2 starts before Cycle 1 finishes
Allowed and correct: cycles are independent lanes; C2's lay ran while
C1 was mid-flight; C2's pattern waited only for **its own lane's**
layering. One guard exists at the right place: `resolve_stream(adda,
None)` with >1 live lane **refuses** — *"NKB-001 has multiple cutting
lanes — specify which lane"* — nothing ever guesses a lane.

### D — Panel finishes first
Bundling/Barcode/Ops did NOT start: pointer held, 0 batches, A360
shows the lock. That is the frozen v1 join (the conservative
"all-blocking-lanes" superset of the per-size rule, FINAL_REVIEW §2 —
per-size early unlock stays a future predicate swap, no schema).
For a 5000-piece order the honest operating pattern is: **declare the
cycles you are actually laying; join fires when the declared blocking
set is cut; every LATER cycle appends post-join** (Scenario E) — so
sewing is fed continuously without ever bundling a garment whose
mandatory pieces don't exist.

### E — quantity increased after the join (the decisive one)
Declared body **seq 4**, reason *"Additional production — buyer
increased order by 100 garments"*, walked lay(25) → pattern → cut
(100 pc) **through the normal services**:
- Pointer **never regressed** (Side Seam before = Side Seam after) —
  the no-memory join law held for a PLANNED lane, not just recuts.
- Barcodes **auto-appended 601–650 S + 651–700 M**; 1–600 untouched.
- ONE audit event lists every lane with its reason — split-lay and
  additional-production side by side, same mechanism:
  `{'appended': 100, 'lanes': ['body', 'body (lane 3) (Split lay —
  planned cycle 2…)', 'body (lane 4) (Additional production — buyer
  increased order…)', 'panel']}`
**Answer: another Production Cycle and an Additional Production Lane
are the same row.** The distinction the factory cares about lives in
the mandatory reason — data, never code.

## 4 · What the challenge BROKE (all implementation vs. the freeze — none architectural)

**GAP 1 — the ops pool read is NOT "Σ-over-streams" (engine defect,
the promise-breaker).** LIFECYCLE §2 + FINAL_REVIEW §1 froze: a lane's
output *"APPENDS to the ops pool via the existing Σ-over-streams
read."* The code never got it: `pool_service._upstream_pool_source()`
returns **`.first()` — ONE stage record** — and the cutting handler's
`pool_good()` reads APSCPB **per cutting_record**. With multiple
cycles the first ops stage sees ONE arbitrary cycle's pieces:
- LOWER-002 (real data): source = body lane 1 → `available(S) = 0`
  while the 2 recut pieces (barcodes 81–82) exist cut+verified.
- NKB-001: source = body **lane 3** (id-order luck — a different lane
  than LOWER-002 picked!) → available 80+80 of a 600-piece truth
  (27%); **grey allocation impossible (0 available)**.
- After E's append: available still 80 vs navy-S truth 250 — late
  cycles are invisible to allocation forever.
Blast radius: OP-1 allocation panel + `check_allocation_bound`
(flag OFF) + the J-2 prefill economy. NOT money, NOT barcodes, NOT
settlement (all read adda-wide — re-verified in this walk). Fix shape
(when you approve one): sum `pool_good` across ALL pool-participant
records at the nearest upstream order — literally the frozen sentence.
FINAL_REVIEW §5 even carried *"first-ops pool = Σ streams"* as a
residual risk; the receipt never closed it.

**GAP 2 — lane-blind validations inside cutting completion (engine
defect, blocks real multi-FABRIC cycles).**
`complete_cutting_from_bundles` validates the lane's breakup colors
against `_get_layering_record_for_adda(adda)` — **no lane** — which
resolves to the lowest-stream-id layering record (= body lane 1,
navy). The PANEL lane (grey) therefore **cannot complete**: *"Color
id=18 not in layered rolls."* The receipt's DEV-NICKAR-001 browser
proof missed this because both its lanes' rolls happened to share a
color. `_pattern_record_for_adda(adda)` in the same function is
equally lane-blind (size-allocation check — masked here, both lanes
50/50). Same-fabric multi-CYCLE walks fine (colors match by
definition); cross-fabric is broken at exactly one line. In this
simulation the panel lane was finished via the two post-validation
steps the service itself performs (breakdown materialization +
`advance_lane`) — documented bypass, and its side effect (panel
cutting cost froze at qty 0 because only the blocked service sets
`pieces_cut`) shows the defect also poisons lane cost truth if
worked around naively.

**GAP 3 — bare multi-lane console URL = 500 (view defect).** An
assigned worker opening `/cutting/workspace/` WITHOUT `?stream=` on a
multi-lane Adda gets an unhandled `ValidationError` (the
resolve_stream refusal) — a server error, not a lane picker. Deep
links/bookmarks break the moment a second cycle is declared.

**GAP 4 — cross-lane read exposure (owner UI-law deviation).** Master
B (assigned ONLY body cycle 2's cutting) can read the PANEL lane's
workspace by URL (`?stream=16` rendered panel's crew, rows, totals).
No switcher chip is shown to workers (leak = URL-probing only, the
familiar menu-hides-URL class), and write paths stay task/roster
gated — but your law is *"he should only see Body Cycle 1"*: the
stage-access mixin passes on ANY-lane assignment and then renders ANY
requested lane. Lane-scoping for non-management is a small view
change (finding, not built).

**Small deviations (presentation-class, recorded):**
- Cancelled lanes are filtered OUT of A360 — LIFECYCLE §7 says render
  greyed with reason (the cancelled seq-2 lane is invisible today).
- The coarse pointer walks forward on ANY lane's stage completion
  (NKB-001 read "Cutting" while no lane had started Pattern) — harmless
  by design (per-lane truth = lane cards; gates are per-lane), but the
  Adda LIST's stage column mildly lies mid-pre-production.
- The "Add lane" button (LIFECYCLE §10, deferred) is now **required**
  for real operations: planned cycles are declared today only via
  shell/admin. §1–§9 rules are frozen; it's one management form.
- Fixture note for honesty: NKB's pattern-assignment rows were created
  mid-walk, so rule-7 (all patterns verified) was exercised only on
  the E lane; the R8 worlds cover it elsewhere.

## 5 · Product configuration — challenged

**Fabric groups ONLY. No Cutting Group. No Stream Types.** The number
of cycles is an OPERATIONAL fact (order size ÷ what one table/lay can
hold, roll arrival dates, recuts) — it varies per Adda, per week, per
fabric market mood. Baking it into Product config would be recording
tomorrow's weather in the constitution: wrong the first time reality
differs, and it would force flow surgery per product — the exact
failure PROPOSAL §8 rejected ("Layering 1 / Layering 2" stages).
Blueprint pieces already carry `fabric_group` strings; the provider
derives lanes; managers declare extra cycles with a reason when the
floor actually lays again. **Every new garment stays configuration:**
NKB needed pieces + groups + stage rows — zero engine code, proven at
creation when the real provider derived body+panel.

## 6 · UI (owner requirements vs. what exists — walked on phone, 390px)

```
MANAGER (complete picture — A360, exists today, screenshot on file)
┌ NKB-001 · Adda 360 ────────────────────────────┐
│ ✅ Pre Production 3/3   🟡 Stitching 0/1        │
│ EXPECTED ₹750 · SETTLED ₹0     ← 570+80+100 ✓  │
│ PRE-PRODUCTION — CUTTING LANES                 │
│ ● Body          Lay ✓ · Pattern ✓ · Cut ✓      │
│ ● Body (Lane 3) Lay ✓ · Pattern ✓ · Cut ✓      │
│     (Split lay — planned cycle 2…)             │
│ ● Body (Lane 4) Lay ✓ · Pattern ✓ · Cut ✓      │
│     (Additional production — buyer increased…) │
│ ● Panel         Lay ✓ · Pattern ✓ · Cut ✓      │
│ [🔒 bundling unlocks when every lane is cut]    │
└────────────────────────────────────────────────┘
Navigation: Addas list → Adda 360 → lane card → stage tab (?stream=pk)
Missing per lifecycle: cancelled lane greyed · "＋ Add lane" button (§10)

WORKER (phone, one-question law — target state)
┌ My Dashboard ──────────────────────┐
│ TASK: Cutting — Body (lane 3)      │   worker sees A TASK,
│ NKB-001 · 30 layers laid           │   never the word "stream";
│ [Report my pieces]                 │   ONLY the assigned lane
└────────────────────────────────────┘   (GAP 4 = today he can
Report form: J-2 prefilled dims · gam    URL-guess siblings)
fields · lock-on-submit — unchanged.

DECLARE CYCLE (the §10 form when built — one question + confirm)
┌ Add cutting lane — NKB-001 ────────┐
│ Fabric: [body ▾]  (groups from the │
│  Adda's derived lanes only, §6)    │
│ Reason (required): [Split lay ▾ /  │
│  free text]                        │
│ Context: body already has lane 1   │
│  (Cut ✓ 240 pc) · lane 3 (Cut ✓…)  │
│ [Confirm — this appends, never     │
│  rewrites]                         │
└────────────────────────────────────┘
```
Nothing above needs new architecture: the manager view EXISTS (walked
live), the worker view exists minus lane-scoping (GAP 4), the declare
form is lifecycle §1–§9 verbatim.

## 7 · Constitutional spot-check of the verdict

Single writers ✓ (cycle rows: adda_service insert-only; this challenge
wrote via ORM only to simulate the missing §10 form) · derive-at-read
✓ (join, lane completion, labels — all read; the pool GAP is a read
that derives from too little) · append-only history ✓ (cancel = the
one soft mutation, exercised; E appended) · settlement-only money ✓
(expected ≠ money throughout; nothing booked) · operator authority ✓
(reports immutable; verified-else-good untouched) · genericity ✓ (the
engine saw only strings + integers; NKB is data) · YAGNI ✓ (verdict A
adds NOTHING; verdict B would add a table carrying no information).

## 8 · The verdict, restated with its proof

- **A. Current Cutting Streams are sufficient — YES.** `(fabric_group,
  sequence)` already IS (Stream, Cycle). Proven by: 3 masters cutting
  in parallel · per-cycle costs frozen · per-cycle earnings exact to
  the rupee · join held/fired correctly · one identity sequence with
  post-join append · planned-vs-additional = reason data.
- **B. One more abstraction — NO.** A ProductionCycle table under a
  Stream table is the same pair with more furniture. Rejected twice
  now (FINAL_REVIEW §1, and this live walk found nothing it would fix:
  every gap found is a lane-blind READ, which a new parent table would
  not repair).
- **C. Something simpler — NO.** The simpler-looking options (reopen
  the cutting record and append work · one Adda per lay) were the
  redesign-trap the FINAL_REVIEW demolished with code citations
  (settlement armor, cost-truth destruction, roll-entry uniqueness).

**What SHOULD happen next (owner decision, no code done):** schedule
the four gaps as campaign fixes in severity order — GAP 2 (blocks real
multi-fabric cycles at one validation line) · GAP 1 (the frozen Σ pool
read; unblock ops allocation with cycles) · GAP 3 (bare-URL 500) ·
GAP 4 + greyed-cancelled + Add-lane form (the owner UI laws). All
are code-matches-frozen-architecture; none reopens the freeze.

**STOP — review only. No implementation, no migrations, no model
changes. NKB-001 and its cast are DEV data, disposable on your word.**
