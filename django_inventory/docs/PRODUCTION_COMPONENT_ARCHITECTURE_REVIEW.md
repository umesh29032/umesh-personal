---
id: production-component-architecture-review
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# PRODUCTION COMPONENT vs FABRIC GROUP — FINAL ARCHITECTURE CHALLENGE
(2026-07-11 · owner-ordered · REVIEW ONLY — zero code, zero migrations,
zero model changes · method: consumer census of `fabric_group` across
the codebase + a fresh live world SHT-001 — a REAL 7-component Shirt
with SHARED fabrics walked end-to-end through the running system,
full service path, zero bypasses · companions:
CUTTING_CYCLES_ARCHITECTURE_CHALLENGE.md ·
BUNDLE_ASSEMBLY_ARCHITECTURE_REVIEW.md, same day)

> **🔒 OWNER-RATIFIED 2026-07-11.** Verdict accepted; production
> architecture FROZEN — no new core concepts. Owner decisions: keep the
> table name `ProductPattern`; align documentation/glossary/UI labels to
> say **Production Component** (glossary updated same day); remaining
> work = the gap ledger (implementation debts, not architecture).

# VERDICT: **A — the Production Component already exists in the
architecture. It is `ProductPattern`.** `fabric_group` was never
claiming to be the component — it is the component's *lay-organizing
attribute*, and the live Shirt proves the two must NOT be merged:
components share fabric, and the factory cuts shared-fabric components
in ONE lay with one nested marker. A `ProductionComponent` table would
model the factory WRONG (§3) while adding zero information (§4).
Terminology note honestly conceded in §7 (a C-flavored garnish on the
A verdict): if the floor should see the WORD "component", that is a
display/docs rename of what `ProductPattern` already is — no schema.

---

## 1 · Your proposed hierarchy vs what exists — line by line

You proposed:
```
Product → Production Component → Blueprint Pieces → Fabric Group → Production Cycles → lay → pattern → cut
```
The system today, named exactly:
```
Product → ProductPattern      → PatternPiece(s)  → .fabric_group    → CuttingStream(group, seq) → lay → pattern → cut
           (= the component)     (its pieces)       (its attribute)     (= the cycles)
```
**Your diagram is the current schema.** Every property you listed for
a component maps to something that already exists and was exercised
live tonight:

| "A component has its own…" | Where it lives | Live proof (SHT-001 / NKS-001 / NKB-001) |
|---|---|---|
| Blueprint pieces | `PatternPiece.pattern` | 7 components → 7 pattern rows, pieces carrying groups |
| fabric group | `PatternPiece.fabric_group` — an ATTRIBUTE, exactly as you suspected | Front/Back/Sleeve/Pocket/Yoke share `body`; Collar/Cuff share `trim` |
| cut counts / shortages / bottlenecks | `CuttingPieceBreakup.pattern` + the derive | bottleneck named at COMPONENT grain: {Sleeve, Collar} — spanning BOTH lanes |
| per-garment multiple | `ProductPatternAssignment.pieces_count` | Sleeve ÷2, Cuff ÷2 in the min() live |
| bundle representation | `CuttingBundleItem.pattern` | bundle = 29 garments × 9 pieces, itemized per component; fabric_group ABSENT |
| costing / workers / cycles | per LANE (the lay's crew + frozen cost) + per-pattern derivable | per-cycle costs frozen; master A ₹686.00 exact across four products |
| its own lay/pattern/cut | **NO — and this is the finding** | see §3: shared-fabric components are cut in ONE lay |

## 2 · The consumer census (who actually reads `fabric_group`)

Grepped across production / tracking / expense / inventory:
`fabric_group` is consumed in exactly THREE places — the
`CuttingStream` model (identity + label), `adda_service` (derivation +
Max-sequence), `stage_views` (lane header display). **Nothing
downstream of the join has ever heard of it**: cutting truth is
pattern-grained, bundles are pattern-grained, barcodes are
dimension-grained, pools are dimension-grained, money is task-grained.
The architecture already treats the fabric group as scaffolding for
the PRE-PRODUCTION lay and the component (pattern) as the production
identity everywhere else. Your concern — "I don't want today's
terminology to block tomorrow's factory" — is structurally satisfied:
the string can change per piece at any time and only FUTURE lane
derivation notices (creation-time snapshot law).

## 3 · The live world that decides it: SHT-001 (Shirt, shared fabrics)

7 components: Front·Back·Sleeve(×2)·Pocket·Yoke on `body` fabric,
Collar·Cuff(×2) on `trim`. Real Blueprint, real provider →
**7 components derived exactly 2 lanes.** Then, full service path (no
bypass — one cloth color per world sidesteps GAP 2):

- **One lay cut FIVE components.** The body lane: 30 plies, one
  marker, breakup rows Front 30 · Back 30 · Sleeve 58 · Pocket 32 ·
  Yoke 30 = 180 pieces in ONE cutting record. This is real marker
  physics: components sharing a fabric are NESTED IN ONE MARKER to
  save cloth — that is what a cutting master's efficiency IS. A
  `ProductionComponent` that "owns its own layering, its own pattern,
  its own cutting" would force **five body lays for one shirt**:
  5× table occupancy, 5× lay labor, and the fabric waste the nested
  marker exists to prevent. The component is real; the component
  *owning the lay* is factually wrong about garment factories. The lay
  is owned by the FABRIC ON THE TABLE — which is precisely what a
  CuttingStream is.
- **Join → one identity range 1–271** (271 pieces ≠ 29 garments —
  piece truth, garment arithmetic, per the Bundle review).
- **The component derive** (min over 7 patterns with ÷multiples):
  Front 30 · Back 30 · Sleeve 58÷2=29 · Pocket 32 · Yoke 30 ·
  Collar 29 · Cuff 62÷2=31 → **complete = 29**, bottlenecks =
  **{Sleeve, Collar}** — named at COMPONENT grain and spanning BOTH
  lanes. A lane-level (fabric-level) view could never say "Sleeve is
  short"; the pattern grain does, today, with zero new schema.
- **Scenario 5 executed** — "body needs a second marker": declared
  body **cycle 2**, reason *"Split marker — sleeve panels on a second
  marker"*, cut +2 sleeves through the full service: no pointer
  regress, identities appended 272–273, derive moved Sleeve 29→30 and
  the bottleneck **collapsed to Collar alone**. Answer: one component,
  one more CYCLE (reason = data) — or even just more breakup rows in
  the same lay if both markers run on one spread. Both already exist;
  nothing missing.
- **Bundle challenge re-run:** the M bundle = 261 pieces = 29 garments
  × 9 pieces-per-garment, itemized **by component** (Back 29 ·
  Collar 29 · Cuff 58 · Front 29 · Pocket 29 · Sleeve 58 · Yoke 29),
  leftovers derived per component (+1 Front, +2 Sleeve, +4 Cuff …).
  **Bundles derive from components, not fabric groups — proven; the
  words "body"/"trim" appear nowhere downstream of the join.**
  (One GAP-5 detail caught for the eventual service move:
  `CuttingBundleItem` uniqueness is `(bundle, pattern, color)`, so
  cross-LANE takes of the same component must increment one row —
  the docstring's `source_breakup`-keyed description doesn't match
  the DB constraint.)
- Money: master A's expected = **₹686.00 exact** across four products
  and five cutting cycles tonight — component/lane structure never
  touched a money law.

## 4 · Your scenarios, each answered

1. **Nickar Body+Panel, cycle each** — modeled perfectly today
   (NKB/NKS walks; components = patterns, lanes = fabrics, cycles =
   sequence). Nothing missing.
2. **Body ×3 cycles + Panel ×1** — `sequence` solved it live in the
   Cutting-Cycles challenge (3 parallel masters, per-cycle costs +
   earnings + append). The missing abstraction did not appear.
3. **Shirt, some share fabric, some don't** — THE decisive case, run
   tonight: 7 components → 2 lanes; shared-fabric components nest in
   one marker; component-grain truth (bottlenecks, bundles, derive)
   flows from `pattern` regardless of sharing. `fabric_group` alone
   expresses it cleanly BECAUSE it never tries to be the component —
   tomorrow Collar moves to Rib's fabric = edit one string on one
   piece; Rib splits into two materials = two strings → next Adda
   derives three lanes. Configuration, forever.
4. **One component, multiple Blueprint patterns** (e.g. Collar =
   collar-top + collar-band) — today each pattern derives and
   bottlenecks independently, which is FINER truth, not less ("collar-
   band is short", not "collar-ish something"). What a multi-pattern
   component adds is only a display GROUPING. If a real garment ever
   demands it, that is one optional label column on `ProductPattern`
   (data, no abstraction, no new table) — explicitly YAGNI today: no
   real garment in this factory has named it.
5. **Two markers for Body** — executed live (§3). One component,
   one more cycle (or more rows in one lay). Nothing missing.

## 5 · Why a `ProductionComponent` table loses (the strongest case against myself)

I tried to construct the case FOR it; every property it would carry is
already owned:
- identity → `ProductPattern` (exists, with code/name)
- pieces → `PatternPiece.pattern` (exists)
- fabric → the piece attribute (exists; and per-PIECE is MORE flexible
  than per-component — a future component whose pieces straddle two
  fabrics, e.g. a lined yoke, is expressible today and would be
  IMPOSSIBLE with fabric-on-component)
- counts/bottlenecks/bundles/derive → pattern-grained (proven live)
- lays/cycles/crew/cost → the stream (correctly FABRIC-owned, §3)
What remains is a NAME. A table for a name costs: one more mandatory
config object per garment (genericity gets WORSE — today SHT needed
7 patterns + pieces + 3 stage rows and derived everything), one more
FK chain through Blueprint→cutting→bundle, one more single-writer, and
a data migration for every existing product — to store information the
pair (pattern, group-string) already carries. That is the exact
furniture-without-information trade the Cutting-Cycles challenge
rejected for Stream→Cycle, one level up.

## 6 · Genericity check (your constitutional test)

A brand-new 7-component garment was introduced tonight **entirely as
configuration**: patterns + assignments + pieces-with-groups + three
WorkflowStage rows. The engine derived 2 lanes, ran 3 cycles, named
271+2 identities, computed 29 complete garments, staged a 9-piece-per-
garment bundle, and paid ₹-exact — having interpreted ZERO of the
strings "Front", "Sleeve", "body", "trim". Introducing
ProductionComponent would not remove an engine assumption (there is
none to remove — the census in §2 is the proof); it would only add a
second product-modeling vocabulary that every future garment must fill
in.

## 7 · The honest concession (the C-garnish on the A verdict)

Two things your instinct is RIGHT about, both sub-architectural:
1. **Vocabulary.** The system's word for your "production component"
   is `ProductPattern` — a name chosen in the cutting era that
   under-sells what it now is. If the floor and the docs should say
   *component*, that is a GLOSSARY/UI-label alignment (and at most a
   someday `verbose_name`), not a schema act. Worth doing in a docs
   pass; changes nothing at runtime.
2. **The component deserves a SURFACE.** The bottleneck table in §3
   (the same "garment readiness" panel from the Bundle review, now
   proven to need PATTERN rows, not fabric rows) is where the
   component becomes visible to management. Read-only, existing
   tables, folds into the GAP-5/derive-panel work already on the
   ledger.

## 8 · Final statement

- **A — no change justified.** The Production Component exists
  (`ProductPattern`); the fabric group is its lay-routing attribute;
  the cycles are its lanes' sequences; the bundle and every downstream
  truth already speak component. Proven on a live 7-component,
  2-fabric, 3-cycle Shirt with zero engine code and zero bypasses.
- **B — rejected**: the table would mismodel the lay (shared-fabric
  nesting), reduce genericity, and carry no new information (§5).
- **C — accepted only as garnish**: terminology alignment
  (component ⇄ ProductPattern) in docs/labels + the component-grain
  readiness surface, both already implied by the existing gap ledger.

**No readiness document. No implementation. Gap ledger unchanged:
GAP 2 → GAP 1+grain → GAP 5 (+ derive/readiness panel, + the
bundle-item uniqueness detail from §3) → GAP 3 → GAP 4 + UI laws.**

**STOP — review only. SHT-001, NKS-001, NKB-001 and their cast remain
disposable DEV data.**
