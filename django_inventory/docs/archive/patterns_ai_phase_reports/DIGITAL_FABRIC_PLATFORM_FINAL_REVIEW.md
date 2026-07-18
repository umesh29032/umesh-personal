> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# DIGITAL FABRIC PLANNING PLATFORM — FINAL PRE-FREEZE REVIEW
(2026-07-08 · THE LAST architecture review before permanent freeze ·
REVIEW ONLY — no code, no plans · lens: lead architect of a garment
CAD/CAM platform, Gerber/Lectra/Optitex class)

Input: the owner's FINAL architecture v2 (13 Laws, 6 applications,
10 DCT modules). Prior round: DIGITAL_FABRIC_PLATFORM_ARCHITECTURE_REVIEW.md.

---

## 0. What v2 already fixed (verified, not repeated below)

The owner absorbed the previous round almost completely — each verified
against the v2 text:

| Prior challenge | v2 resolution | |
|---|---|---|
| Contradiction 1 (reference in readiness) | "Reference Image is OPTIONAL … only documentation. Manufacturing truth is the confirmed geometry." | ✅ |
| Contradiction 2 (singular marker) | "Approved Layout(s)", Layout Manager A/B/C/D, Adda "Choose Approved Layout" | ✅ |
| K-2 fabric groups | DCT module 1 + LAW 12 ("Body fabric and Rib fabric NEVER mix") | ✅ |
| T-2 cut plan / ratio | DCT module 3 (quantities or ratio = composition target) + LAW 13 | ✅ |
| T-1 width vs length | "Fabric Width is a CONSTRAINT. Layout Length is a RESULT." verbatim | ✅ |
| K-3 staleness / ECN | Module 9: immutable, stores geometry versions, "becomes STALE, never automatically modified" + LAW 11 | ✅ |
| B-3 fabric master (partial) | Module 1 "Select Fabric Specification" implies a catalog | 🟡 see F-1 |

**The skeleton is now industry-correct AND the prior couplings are
closed. What follows is the residue: attribute-level gaps, two internal
inconsistencies v2 itself introduced, and the honest Gerber-architect
critique. None of them break the structure.**

---

## 1. The 12 answers

### Q1 — Is the overall business architecture correct?
**YES.** Four responsibilities (define → prepare geometry → prepare
layout → execute), strictly one-directional flow, one manufacturing
truth (Approved Layouts), one backward channel (staleness). This is the
canonical CAD/CAM chain. No structural objection remains.

### Q2 — Are the application boundaries clean?
**YES, with ONE under-specified application: the Pattern Blueprint.**
As written, the Blueprint is a bare NAME LIST ("Front Panel, Back
Panel…"). But three other applications need piece-level FACTS that can
only live here, or the boundaries leak:

- **fabric group** per piece (body / rib / lining) — without it, LAW 12
  is unenforceable: the DCT cannot partition pieces it cannot classify.
- **pair/mirror rule** (Left+Right vs cut-two-mirrored) — the DCT's
  "Mirror (if allowed)" needs a source of "allowed".
- **grain rule** (on-grain / may rotate 180° / free) — vanished from v2
  entirely (v1 had it, misplaced under fabric config). A marker nested
  ignoring grain is unmanufacturable on stretch or printed fabric.
- **required/optional flag** — v2 uses it ("Optional … never block
  readiness") but never says the Blueprint owns it.

**Ruling to add:** *the Blueprint owns ALL piece rules: name, count per
garment, required/optional, pair/mirror, fold, grain, fabric group.
Pattern Manager consumes them for readiness; DCT consumes them as
placement constraints. Neither may override.* This is one sentence in
the freeze and it completes application 3. Without it, piece rules will
end up scattered across three apps within a month of implementation.

### Q3 — Is the workflow chain correct?
**YES.** Product → Sizes → Blueprint → Pattern Manager → DCT →
Approved Layout(s) → Adda → Layering → Cutting → Manufacturing.
Two boundary declarations make it airtight:
- **Platform ends at Approved-Layout hand-off.** Layering/Cutting/
  Manufacturing belong to the existing production system. The JOIN
  CONTRACT: *expected cut quantities per size = layout content × plies*,
  and Adda verification reconciles against it.
- **Layouts are COLOR-BLIND by design.** Color/shade enters at
  spreading (the same marker is cut on black and white rolls). Correct
  and industry-standard — state it so nobody ever "improves" the DCT by
  adding color, which would multiply the marker library by the color
  count for nothing.

### Q4 — Does the Blueprint correctly separate definition from geometry?
**YES conceptually — the strongest idea in the architecture.**
Definition (size-blind, product-level) vs geometry (per-size) is the
exact split industry uses (piece list vs graded patterns). Inheritance
("new size automatically receives the Blueprint, only geometry
changes") is correct. Two refinements:
- The uniform-across-sizes law is right as LAW; the known exception
  ("pocket only on XL") is handled by the optional flag in v1 —
  register per-size requiredness as a FUTURE Blueprint concern so
  nobody hacks it into the Pattern Manager.
- See Q2 — the Blueprint must own piece RULES, not just names.

### Q5 — Is the Product Pattern Manager correctly defined?
**YES, with ONE internal inconsistency v2 introduced.** The preparation
workflow reads: *"For every Pattern Piece the operator uploads a
reference image"* → AI pipeline → confirm. But v2 also (correctly)
rules reference images OPTIONAL. Both cannot stand. And the same
paragraph freezes the PHOTO pipeline as the only entry path — while the
owner's own flagship product was digitized via **DXF import**, and
manual drawing exists.

**Resolution:** the photo→AI→confirm pipeline = the CANONICAL path, not
the ONLY path. Readiness is **entry-path-agnostic**: a Pattern Design is
ready when geometry + dimensions + area + DXF are confirmed — however
the geometry entered (photo, DXF import, manual draw). One sentence;
without it the freeze outlaws the platform's own best data.

Everything else — per-size preparation workspaces, "Preparing Size M",
one confirmed Design per piece per size, readiness checklist, optional
never blocks — correct and final.

### Q6 — Is the Digital Cutting Table correctly defined?
**YES.** Separate application, consumes-never-edits, gated on ≥1 Ready
size, one fabric group per table, width constraint / length result,
manual placement sacred, AI assistant-not-owner, plural layout
candidates, immutable approval with staleness. This is a professional
marker-making tool, correctly scoped.

### Q7 — Does the DCT contain every required module?
**Almost. Two modules lost pieces between v1 and v2, one property
missing:**
- **M-1 · Spacing/buffer rules dropped.** v1 had Margins, Spacing,
  Cutting Gap; v2 module 2 keeps only width. Blade clearance is
  physical reality — pieces cannot touch; edges need margins. Restore
  as part of the fabric/table settings (a property of the fabric spec
  or cutting method, not per-session free-typing).
- **M-2 · Physical TABLE LENGTH constraint absent.** A marker longer
  than the factory's cutting table cannot be spread. Distinct from
  fabric width; one field in settings, one constraint for the AI.
- **M-3 · AI Optimizer must be declared ASYNC.** Realistic nests run
  seconds-to-minutes (the platform's own validation measured 60–90s
  kills). "AI Optimize" = a job with progress + cancel, never a
  blocking click. This is a business-architecture property because it
  shapes the operator's workflow contract.
Module list otherwise complete — and module 9's stored-fields list
(geometry versions · fabric spec · cut ratio · width · utilization ·
area · approval info) is exactly a marker record. Add ONE stored field:
**layout NAME/identity** (operators will discuss "Marker B60-1221" by
name; searchable identity is how a marker library scales).

### Q8 — Hidden coupling problems remaining?
**Two, both small and both closable with one line each:**
- **C-1 · Adda roll-match check.** The layout stores its fabric spec +
  width (LAW 13 ✓), but the Adda workflow (Choose Layout → Visual
  Reference → Verification…) never states the CHECK: *the physical
  fabric on the table must match the layout's frozen spec/width, else
  refuse.* Without the check, LAW 13 is a label, not a guard.
- **C-2 · Cut-plan authority.** Module 3 puts the cut plan inside the
  DCT session. Fine for composition — but the REAL demand lives with
  the production order (the Adda's need). Declare: *DCT cut plan = a
  composition TARGET; layouts are reusable candidates; the Adda chooses
  the approved layout whose ratio serves its actual demand.* Otherwise
  two places will claim to own "how many of each size" — the exact
  duplication disease the old proportion-% field had.

### Q9 — Manufacturing concepts still missing?
**One critical, three minor:**
- **THE CUT-LINE DECLARATION (critical, flagged twice now, still
  absent).** Is confirmed geometry the SEW line or the CUT line — seam
  allowance included or not? Every pattern platform on earth must
  declare this once. Recommended freeze sentence: *platform geometry =
  CUT-ready contour, seam allowance already included; the Pattern
  Manager confirms cut lines.* Skipping this poisons every marker
  silently and is unfixable retroactively.
- Approval AUTHORITY: which role may approve; approval audited. (Module
  9 stores "Approval Information" — say who is allowed to create it.)
- Quantities→markers arithmetic: module 3 accepts raw quantities
  (S×5, M×10, L×8, XL×3). 5:10:8:3 is not a clean single-marker ratio —
  real answer = multiple markers × plies (+ remnant marker). v1 rule:
  **operator enters the RATIO; deriving an optimal marker-set from raw
  quantities = registered FUTURE cut-planning feature.** Freezing this
  prevents the DCT from silently growing an optimizer nobody planned.
- Units: platform-wide mm truth (already de-facto; one line).

### Q10 — Scales to thousands of products and factories?
**Structurally yes** — everything partitions per product; no
cross-product coupling in any law; fabric master + marker library are
the only shared surfaces and both are read-mostly. The honest scale
constraints:
- **Piece-name governance** (previous review S-1, still open): blueprints
  drawing from a curated piece-type vocabulary, or thousand-product
  search/analytics rot.
- **Nest farm economics**: async queue (M-3) becomes a scheduling system
  at factory scale. Architecture permits it; nothing to change now.
- **The grading question — see Q11.** At thousands of products,
  per-size manual digitization is the bottleneck; the architecture must
  not preclude grading automation (it doesn't — see below).

### Q11 — What would Gerber/Lectra/Optitex architects criticize?
The honest list, with verdicts:
1. **"You digitize every size separately?? We GRADE."** Industry
   digitizes a BASE size and auto-generates the size run via grading
   rules. This platform prepares each size independently (photo/DXF per
   size). **Deliberate and defensible** for a factory whose paper
   patterns already exist per size — grading rules would be reverse
   engineering. Crucially the architecture does NOT preclude grading: a
   future grading engine lives INSIDE the Pattern Manager and emits
   per-size Designs — every downstream contract unchanged. Register as
   the platform's biggest known divergence + its future answer.
2. **No automatic cut-plan optimization** (demand → optimal marker set ×
   plies). Manual v1, registered future (Q9). Acceptable.
3. **No pattern-matching for stripes/plaids/nap** (one-way layouts,
   repeat matching). Real Gerber feature; conscious v1 out-of-scope —
   grain + rotation rules (Q2) cover the 80% case.
4. **No shrinkage handling** (pre-shrink allowances per fabric spec).
   Belongs in the fabric master later; note, don't build.
5. **Single-product markers only** (industry occasionally nests multiple
   products together to kill remnants). Conscious platform law;
   acceptable simplification, cleaner truth chain.
6. **No splice marks / spreading-defect handling.** Execution-layer,
   correctly outside the platform boundary.
None of the six is a freeze blocker; 1–2 deserve a line in the
future-decision register so they're divergences BY CHOICE, not by
ignorance.

### Q12 — Strong enough to freeze permanently?
**YES — freeze it, with the §2 amendment list written into the freeze
text.** The structure survived two adversarial rounds; every structural
challenge got absorbed or consciously rejected; what remains is
attribute-level and resolvable in sentences, not redesign. Freezing
WITHOUT the amendments would leave four seams (piece rules, cut line,
entry paths, roll-match) to be invented ad-hoc mid-implementation —
which is how clean architectures rot.

---

## 2. THE AMENDMENT LIST — write these into the freeze, then freeze

1. **Blueprint owns piece RULES** — name, count/garment,
   required/optional, pair/mirror, fold, grain, **fabric group**.
   Pattern Manager reads for readiness; DCT reads as constraints;
   nobody overrides. (Completes LAW 3; makes LAW 12 enforceable.)
2. **CUT-LINE LAW** — confirmed geometry = cut-ready contour, seam
   allowance included.
3. **Entry-path-agnostic readiness** — photo pipeline = canonical, not
   exclusive; DXF import + manual draw equal citizens; readiness =
   checklist truth regardless of path. (Fixes v2's internal
   inconsistency with its own "reference optional" rule.)
4. **Adda roll-match check** — physical fabric must match the layout's
   frozen spec/width or execution refuses.
5. **Cut-plan authority** — DCT plan = composition target; real demand
   = production order; Adda picks the matching approved layout.
6. **DCT settings restored** — spacing/buffer/cutting-gap + physical
   table length; from master data, not free-typed.
7. **AI = async job** (progress, cancel); never blocking.
8. **Layouts are color-blind**; color enters at spreading.
9. **Approved layouts carry NAME/identity**; approval restricted to an
   authorized role, audited.
10. **v1 ratio rule** — operator enters ratio; quantities→marker-set
    optimization = future register.
11. **Future-decision register**: grading automation (inside Pattern
    Manager, contracts unchanged) · cut-plan optimization ·
    stripe/plaid matching · shrinkage · per-size requiredness ·
    piece-type vocabulary governance.

Amendments 1–3 are the only ones with teeth; 4–10 are single-sentence
guards; 11 is bookkeeping. Nothing requires redrawing the diagram.

---

**FINAL VERDICT: the business architecture is correct, boundaries are
clean, and it is strong enough to freeze permanently — as v2 + the 11
amendments above. This review finds no structural objection remaining.
On your confirmation the freeze is permanent and implementation
planning may begin.**

**STOPPED — review only. No code. Awaiting: accept/adjust amendments
1–11 → permanent freeze declaration.**

---

## 3. Addendum — the 500-factories / 10-years question

*Owner asked: if this freeze is wrong, which decision becomes the most
expensive mistake?*

**Answer: the SEMANTIC CONTRACT of confirmed geometry — the precise list
of physical facts a "Confirmed Pattern Design" attests.** Everything
else in the architecture is expensive-but-migratable. This one is not.

Why it stands alone:

1. **It is the only non-migratable decision.** A wrong app boundary is a
   refactor. A wrong schema is a migration. A wrong UI is a rewrite.
   But if stored geometries are AMBIGUOUS about what they mean
   physically, no migration can fix them — the missing facts live in
   the physical world at capture time, and by then they're gone.
2. **The platform becomes the sole custodian.** The moment factories
   trust it, they discard or stop maintaining the paper patterns.
   Ten years in, the platform's geometry IS the factory's pattern
   asset. Ambiguity in the contract = slow, silent destruction of 500
   factories' pattern libraries.
3. **Every downstream consumer trusts it blindly** (DCT, nesting,
   exports, the physical blade). Failures are silent and deferred:
   nothing crashes — fabric gets ruined years later, in someone else's
   factory, with no way to audit which designs are affected.

The horror scenario that makes it concrete: year 4, the convention
quietly shifts from "geometry = sew line" to "geometry = cut line with
allowance". No field records which convention each of 2 million stored
designs used. A factory spreads 800m of fabric on a marker mixing both.
Every garment is 1cm wrong. Unauditable, unrecoverable, and the trust
death is permanent.

**What the contract must pin at freeze — one attestation list, versioned
from day one:**
- cut line vs sew line; seam allowance included or not (amendment 2)
- units and precision (µm integer truth)
- grain reference frame — is grain direction baked into the stored
  coordinates (Y-axis = grain?) or a separate attribute
- fabric state — measured on relaxed/pre-shrunk fabric or paper pattern
- scale trust — tape-verified vs photo-estimated (already exists as
  trust grades: keep it IN the contract, forever)
- pair convention — stored geometry is WHICH hand (left?); mirror
  derives the other
- and a `geometry_contract_version` stamped on every design, so if the
  contract ever evolves, every historical design still declares which
  contract it satisfies.

That last stamp is the cheap insurance: one small field today makes the
one unfixable mistake fixable.

**Runners-up (expensive, but survivable):**
- *Master-data tenancy* — if the piece-type vocabulary and fabric
  catalog freeze as global singletons, the 500-factory retrofit to
  per-tenant catalogs + shared standards is a painful but known SaaS
  migration.
- *Per-size digitization economics* — without a grading path, onboarding
  cost scales linearly with sizes × products × factories; but the
  grading engine slots inside the Pattern Manager with zero contract
  change (Q11.1), so it's money, not architecture.
- *Approved-layout self-containment* — a marker must be reproducible
  from its own stored record alone (geometry versions + spec + ratio +
  width + placements). If it ever references live data, historical
  production becomes unreproducible. LAW 11 + amendment 9 already
  guard this; keep them absolute.

By contrast, the things that FEEL biggest today — page structure, app
naming, module layout, even the DCT's UX — are the cheapest class of
mistake: replaceable without touching a single stored fact.

---

## 4. v3 FINAL BUSINESS DIRECTION — confirmation review (2026-07-08)

The owner's v3 statement ("Final business direction before
implementation") reviewed against all three rounds. **The mental model
now matches — v3 absorbed the remaining deep amendments:**

| Amendment / challenge | v3 evidence | |
|---|---|---|
| A2 + contract stamp (the 500-factory answer) | geometry asset list includes "**trust level · geometry contract**" | ✅ absorbed |
| A3 entry-path-agnostic | "image is only one possible capture method… DXF import, manual drawing, grading engine… downstream workflow must remain identical" | ✅ absorbed, verbatim in spirit |
| Q11.1 grading future | "grading engine" named as future geometry source | ✅ registered |
| Image ≠ asset | "uploaded phone image is never the manufacturing asset" | ✅ |
| Plural layouts + library | Layout A/B/C examples with fabric group, width (mm!), utilization, ratio | ✅ |
| LAW 12/13 in examples | "Body Fabric · 1800 mm · 92%" per layout; "Different size ratio" | ✅ |
| Marker×plies seed | Adda sees "expected pieces" | ✅ seeded |
| Photo-pipeline contradiction | Step 4 still photo-first, but the "Important Clarification" section explicitly generalizes it | ✅ internally consistent now |

**Challenge round 3 result: NOTHING STRUCTURAL LEFT.** Residue riding
into the freeze text (clarifies, does not change, the model):
- **A1 (the only one with teeth):** the Blueprint must be stated as
  owner of piece RULES — fabric group, grain, pair/mirror, fold,
  required/optional, count — not just names. v3's own Layout examples
  carry "Body Fabric"; the tag has to originate somewhere, and that
  somewhere is the Blueprint.
- One-line guards: A4 Adda roll-match check · A5 cut-plan authority ·
  A6 spacing/buffer + table length · A7 AI async · A8 color-blind
  layouts · A10 v1 = operator-entered ratio.

**DECLARATION: the architecture is internally consistent,
manufacturing-correct, and scalable. It is READY TO FREEZE PERMANENTLY
— as v3 + amendment A1 + the six one-line guards. Three adversarial
rounds produced no remaining structural objection; further review
rounds would now cost more than they protect.**

The shared mental model, in one paragraph (the proof the review was
understood): *the platform's atomic truth is the confirmed geometry
(cut-ready contour under a versioned contract); the Blueprint declares
what pieces must exist and their rules; the Pattern Manager makes every
(piece × size) true; readiness is derived, never stored; the Digital
Cutting Table plans by composing frozen truths into a library of
candidate markers; approval freezes geometry versions + fabric spec +
ratio into an immutable, staleness-guarded manufacturing reference; the
Adda executes what it can never edit. Prepare → plan → execute, one
direction, one truth per layer.*
