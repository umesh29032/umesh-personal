---
id: pre-production-architecture-final-review
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# PRE-PRODUCTION ARCHITECTURE — FINAL REVIEW (the freeze gate)
(2026-07-11 · the last architecture document before implementation ·
NO code, NO implementation plan · supersedes nothing — refines
PRE_PRODUCTION_REDESIGN_PROPOSAL.md on two points ·
verification method: main-thread code evidence, plus a 3-skeptic
adversarial panel on the load-bearing decisions. Panel outcome,
honestly: skeptic #1 (stream identity) COMPLETED — verdict HOLDS, with
two refinements folded into §1 and four code facts strengthening the
reopen-rejection; skeptics #2 and #3 FAILED on session rate limits, so
decisions 2 (per-size evolution) and 3 (derived status) were verified
MAIN-THREAD against the models read first-hand during campaign module
5 (CuttingBundle/CuttingBundleItem/PieceBreakup grains) and the reopen
skeleton read during module 6. Every claim stands on cited code, none
on panel silence)

# VERDICT: **B — approve the redesign WITH TWO MODIFICATIONS**

1. A CuttingStream is **one lay→pattern→cut CYCLE**, not "the fabric
   group itself" — the fabric group is the PARENT that derives it.
   Concretely: identity becomes `(adda, fabric_group, sequence)`,
   sequence defaulting to 1.
2. The stream row carries **NO status column** — completion is DERIVED
   at read from its own cutting stage record. (Self-challenge result:
   the proposal's `status` field violated derive-at-read; removed.)

Everything else in PRE_PRODUCTION_REDESIGN_PROPOSAL.md is confirmed
unchanged: additive schema, join gate, bundle re-anchoring, ops stages
untouched, console simplification, barcode options both open.

---

## 1 · What exactly is a CuttingStream? (the challenge answered)

**Your instinct is correct: fabric_group is the parent, not the stream.**

The factory evolution that breaks "stream = fabric group":
- large orders spread across days/tables — the same fabric laid twice;
- roll availability — cut what arrived, lay again Thursday;
- shortfall/recut — Panel came up 12 pieces short after checking.

Under `unique (adda, fabric_group)` every one of those forces
REOPENING a completed cutting record to append work. The adversarial
panel confirmed with four verified code facts that reopen-recycling is
not merely ugly but UNUSABLE for routine second lays:
1. **Settlement armor** (_shared.py) — a settlement-credited stage
   refuses reopen; a recut discovered after payroll would force
   reversing a CORRECT settlement to record NEW work.
2. **Cost-truth destruction** — reopen clears the frozen cost and
   re-floats rates by design (it is a CORRECTION primitive); lay 2 is
   new work that must APPEND, not rewrite lay 1's ADR-0009 truth.
3. **Downstream-consumer guard** — reopen is transitively refused once
   any later stage has active allocations/contributions, so the most
   common real timing (shortfall discovered after stitching started)
   is unreachable via reopen at all.
4. **`LayeringRollEntry` is unique per (stage_record, roll)**
   (layering.py:96) — a leftover roll reused in lay 2 cannot even get
   a second entry with its own layer count; two physical lays cannot
   be truthfully recorded in one stage record.
Routine second lays are NOT corrections; modelling them as corrections
would poison cost/verification/settlement truth every time fabric
arrives late. That is the redesign-later trap you told me to avoid.

**The fix costs one integer.** `CuttingStream(adda, fabric_group,
sequence)`:
- Derivation still creates exactly ONE stream per group (sequence 1) —
  single-fabric products remain byte-identical to today.
- A second cycle for the same group = a NEW stream row (sequence 2),
  opened by an explicit manager act. The lane walks its own
  lay→pattern→cut; its pieces join the same Adda truth. **v1 does not
  even ship the "add lay" button** — the schema simply stops forbidding
  the known factory behavior. (Two different color-lots of the same
  fabric on different days = the same mechanism, free.)
- **No third concept.** A "cycle below the stream" was considered and
  REJECTED: if the stream IS the cycle, the hierarchy stays two-level
  (group = data fact, stream = execution instance) and the model stays
  small. Multiple ROLLS inside one lay are already modelled today by
  `LayeringRollEntry` rows — that is the only "below" that exists, and
  it already works.

YAGNI check, honestly: this is not an imaginary problem — you named it
yourself, twice ("kabhi kabhi ek hi fabric ki multiple layering",
"recutting", "fabric shortage"). One default-1 column now versus a
uniqueness-constraint migration plus a call-site sweep later. The
column wins.

**Two refinements from the adversarial panel, adopted into the freeze
(they close the "dormant affordance with undefined contract" trap):**
- **Late-cycle semantics, frozen now:** a stream opened AFTER the Adda
  has passed the join gate NEVER regresses the Adda — the join gate
  has no memory; it gates only the initial advance out of
  pre-production. The late stream walks its own lay→pattern→cut with
  its own cost freeze and earnings exactly like a sequence-1 lane, and
  its cut output simply APPENDS to the first-ops pool through the
  existing Σ-over-streams read (the same law by which stitching
  already tolerates pool growth). The first real recut will follow a
  frozen rule, not an ad-hoc decision under floor pressure.
- **Sequence assignment = `Max(sequence) + 1` under the adda_service
  lock** (never count+1), so an abandoned lane can never cause a
  uniqueness collision.
*(Panel skeptic #1: verdict HOLDS with these refinements; its four
code citations were independently re-verified before adoption.)*

## 2 · The JOIN rule (challenge confirmed — v1 rule stands)

You are right about the deeper rule. It is not "all streams complete";
it is:

> **A garment of size X may move only when every MANDATORY Blueprint
> piece for size X exists in cut truth.**

"All streams cut-complete" is the conservative SUPERSET of that rule —
correct, never wrong, occasionally slower (Body done Monday, Panel
Wednesday ⇒ nothing bundles till Wednesday). v1 ships the superset
because it is one predicate and zero UI complexity.

**Proof the per-size evolution needs no schema change:** the gate is a
RULE, not a column, and the data is already finer-grained than either
rule —
- cut truth: `PieceBreakup` / `CuttingBundleItem` per
  (pattern, color, size, count);
- required truth: Blueprint `pieces_count` per pattern ×
  `is_optional` × the Adda's size ratio.
A future per-size gate is a pure derive-at-read predicate over exactly
these tables ("Σ cut pieces of every mandatory pattern for size L ≥
required"), and bundles are ALREADY per-size containers, so per-size
unlock maps 1:1 onto bundle creation. The one denominator it needs —
garments required per size — is itself derivable (the Pattern Design
size proportions × the lay, or simply piece-count sets balanced across
mandatory patterns per their per-garment multiples). Nothing
persisted, nothing migrated, rule swapped when the floor asks.
*(Panel skeptic #2 rate-limited; verified main-thread against the
module-5 firsthand model walk — CuttingBundle per size ·
CuttingBundleItem per pattern×color×count · PieceBreakup grain.)*

## 3 · Blueprint → Stream ownership (the chain, unambiguous)

```
BLUEPRINT (patterns_ai — Pattern Intelligence owns, product-level, permanent)
│  PatternPiece: fabric_group (string) · is_optional
│  ProductPatternAssignment: pieces_count per garment
▼
FABRIC GROUPS = DISTINCT fabric_group over the product's pieces
│  (pure data; 'body', 'other', 'rib', … — strings the engine never interprets)
▼
CUTTING STREAMS (production — ERP owns; rows created ONCE at Adda creation
│  by adda_service = the single writer of stream rows; never updated after)
│  one row per group, sequence=1 · groups holding ≥1 MANDATORY piece are
│  JOIN-BLOCKING; optional-only groups derive a non-blocking lane
▼
per stream: LAYERING → PATTERN DESIGN → CUTTING
│  = stream-scoped AddaStageRecord rows, unique (adda, workflow_stage, stream)
│  each lane: own rolls · own crew · own clock · own cost freeze · own
│  reopen · own layout CONTRACT consumed from PI's ApprovedLayoutUsage
│  (already unique per (adda, fabric_group) — the stream is the ERP
│  mirror of that existing PI key; the stream stores the fabric_group
│  STRING, the same sanctioned denorm ApprovedLayoutUsage already uses)
▼
JOIN (derived predicate — nothing stored):
│  every join-blocking stream's cutting SR has completed_at
▼
BUNDLES (adda-level, per size, itemized per pattern×color ACROSS streams)
▼
BARCODE → OPS (single linear lane, exactly today, stream-blind)
```

Ambiguities killed explicitly:
- **Who derives streams?** `adda_service` at creation, from Blueprint
  pieces only. Layouts do NOT derive streams (a group with no approved
  layout still gets its lane; its Pattern Design uses the fallback
  exactly as today). Rolls/colors do NOT derive streams.
- **Who writes stream rows?** Created by adda_service; **never
  mutated** (no status — see §5). A future "add lay" act would INSERT
  sequence 2 via the same service. One writer, one direction,
  append-only. Deleting a stream never happens; a wrongly-derived
  stream means the Blueprint was wrong — fix the Blueprint, next Adda
  derives correctly (history never lies).
- **Blueprint edits after Adda creation?** Streams are a
  CREATION-TIME snapshot, like every other Adda fact (rates, flows).
  Existing Addas keep their derived lanes; new Addas see the new
  Blueprint. No live re-derivation — that would rewrite in-flight
  production.
- **Engine knowledge:** the engine sees group STRINGS and counts. A
  garment name appearing anywhere in stream logic = the constitutional
  failure; the existing genericity guard already polices patterns_ai +
  compute, and stream code lives in production where names never were.

## 4 · Operator experience (workflow only — no HTML)

Design law first: **a single-stream product renders EXACTLY as today —
zero lane chrome.** Lanes appear only when the Blueprint creates >1.
Workers NEVER see the word "stream": a worker sees their task.

**A360 (manager, mobile-first)** — pre-production phase becomes lane
cards; everything after the join is today's timeline:
```
┌ PRE-PRODUCTION ────────────────────────────┐
│ ● Body fabric                              │
│   Layering ✓ · Pattern ✓ · Cutting ⏳ 48/160│
│ ● Panel fabric                             │
│   Layering ⏳ · Pattern — · Cutting —       │
│ 🔒 Bundling unlocks when every lane is cut │
└────────────────────────────────────────────┘
```
One glance answers the only management questions: which lane is
behind, what unlocks next.

**Layering / Pattern / Cutting consoles** — bodies unchanged from the
module-4/5 verified flows; the ONLY addition is a lane header when >1
lane exists: `Layering · Panel fabric (lane 2 of 2)` with a switcher.
Rolls, verified width, layers, leftover — all per lane, which is
exactly how the floor already thinks ("Panel ka lay").

**Pattern Design (simplified, per your order)**:
```
Panel fabric · Pattern Design
[ Choose approved layout ▾ ]  → preview (piece silhouettes + counts)
[ Confirm & submit ]
```
Checklist ticks + photo evidence + worker report REMAIN (floor laws).
Ratios, optimization scores, utilization percentages LEAVE (they live
in Pattern Intelligence).

**Cutting**: `Expected 160 (layout × 40 plies) · Cut 148 · Pending 12`
+ the size×color grid + a mandatory-piece line (`Body ✓ · Pocket ⏳`).
Nothing else.

**Bundling (post-join, the one new screen)** — per size, the Blueprint
speaks:
```
Size L   Body 2/2 ✓  Pocket 2/2 ✓  Panel 2/2 ✓   [Create bundle]
Size XL  Body 2/2 ✓  Pocket 2/2 ✓  Panel 0/2 ✗   (missing: Panel lane)
```
The refusal names the missing piece and its lane — workers stop asking
"kyun locked hai".

**Worker phone report**: unchanged pixel-for-pixel; the task title
already carries the stage name, now suffixed by fabric when >1 lane
("Layering — Panel fabric"). J-2 prefill, gam fields, lock-on-submit —
all as verified in module 6.

Net: the UI gets SIMPLER than today (Pattern Design sheds its
statistics; Cutting sheds suggestion noise), and multi-stream
complexity appears only where it is true — on the manager's lane
cards and the bundling checklist.

## 5 · Constitutional audit (rule by rule)

| Rule | Verdict | Note |
|---|---|---|
| Genericity | ✅ | streams from data; strings never interpreted; guard stays green |
| Single writers | ✅ | stream rows: adda_service, insert-only · stage/cost/task writers unchanged |
| Derive-at-read | ✅ **strengthened** | self-challenge REMOVED the proposal's `status` column — stream completion = `cutting SR.completed_at IS NOT NULL`, join = a predicate, per-size completeness = a predicate, lane progress = read. The stream table stores identity only. Verified main-thread (panel skeptic rate-limited): reopen already clears `completed_at`, so a reopened lane HONESTLY regresses with zero state-machine code; the downstream-consumer guard confines that to pre-join; join queries touch a handful of rows per Adda — trivial |
| Operator authority | ✅ | untouched; reports/verification/completion laws as verified in modules 4–6 |
| Immutable assets | ✅ | ApprovedLayout/usage untouched; stream rows append-only; reopen keeps its existing heavy semantics — routine re-lays now DON'T need it (that PROTECTS immutability instead of eroding it) |
| Simple models | ✅ | one new 4-field table; two nullable FKs; no state machine (derived status means no illegal-transition code at all) |
| YAGNI | ⚠️→✅ | the `sequence` column is the single point of tension — defended in §1: known behavior, named by the owner, one integer now vs constraint surgery later. The "add lay" UI is NOT built. Nothing else speculative |
| Developer friendliness | ✅ | meaningful names (CuttingStream, fabric_group, sequence); no x/y/z; stream-scoped accessors keep ops call sites untouched |
| Factory-driven | ✅ | every element traces to a stated floor fact; the two deferred evolutions (per-size join, add-lay button) wait for the floor to ask |
| No duplicated responsibility | ✅ | fabric_group string on the stream = the same sanctioned denorm ApprovedLayoutUsage already carries (8A precedent); layout truth stays in PI; count truth stays in cut records |

Residual risks carried into implementation (unchanged from the first
review): stage-record uniqueness widening call-site sweep ·
`current_stage` phase semantics · first-ops pool = Σ streams ·
reopen guard stream-scoping · settlement re-verification in campaign
modules 10–11.

## 6 · Documentation archive — second pass

Re-checked DOCUMENT_ARCHIVE_REVIEW.md. The categorization stands, with
THREE corrections:
1. **CLAUDE.md links dated receipts directly** (S1_HOSTILE_REVIEW,
   S3/S4/S5 receipts, M1_M4_REVIEW, foundation chain, ADR links).
   Archiving those files MUST repoint the CLAUDE.md links to their
   `docs/archive/...` paths in the same commit — otherwise the
   project's own instruction file dangles. Added to the mechanics.
2. **Hold `IMPLEMENTATION_MASTER_PLAN_V2`** (already noted) and now
   also **hold the four pre-production review docs + this one** as
   LIVE until the redesign ships and its receipt lands; then the
   review pair (REVIEW + PROPOSAL) archives and THIS document +
   the readiness gate remain the spec-of-record.
3. One promotion to KEEP: **ENFORCEMENT_ROLLOUT_RUNBOOK** was already
   KEEP; additionally keep **S1_HOSTILE_REVIEW** out of the archive
   until the enforcement flags flip (its H-1/H-2 rationale is the
   flag-flip context named by SOAK_TRACKER). Everything else:
   unchanged. Nothing important was found mis-filed; nothing is
   deleted by this review.

---

# The freeze

With modifications 1 (sequence) and 2 (no status column) folded in,
the pre-production architecture is, in one sentence:

> **Streams are derived, not designed: the Blueprint's fabric groups
> spawn independent lay→pattern→cut lanes; the garment's existence —
> and everything after it — is a fact you READ from cut truth, never a
> state you set.**

On your approval this freezes; implementation follows
IMPLEMENTATION_READINESS_PRE_PRODUCTION.md (updated for the two
modifications at build time); and we do not touch this architecture
again unless a real factory problem forces it.

**STOP — no code, no implementation plan. Awaiting the freeze
decision.**
