> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# DESIGN REVIEW — Refined Direction: Pattern Design Management first,
# Cutting Table second, three-state composition
(2026-07-07 · architecture review ONLY — nothing implemented, freeze
intact. Supersedes nothing; refines DESIGN_REVIEW_CUTTING_TABLE_
ARCHITECTURE.md with the owner's three refinements.)

The owner's refinements under review:
1. **Sequence**: perfect Pattern Design Management (PDM) first —
   dashboard-centred, acceptance-validated — THEN build the Cutting
   Table.
2. **Separation**: the Cutting Table is conceptually a separate
   application; it composes layouts from existing designs and NEVER
   manages them.
3. **Composition model**: three states — Available → **Selected** →
   **Placed on Canvas**; AI optimizes ONLY Selected-not-yet-Placed.

---

## 0. Verdict

All three refinements are architecturally RIGHT, and each lands on
something the evidence already pointed at:
- the sequencing matches D-5's recommendation (read-only ancestors
  first) and de-risks the Phase-scale composer;
- the separation is the existing two-faces law (§3c: Hub = collect,
  editor = consume) hardened into a principle — the correct move is a
  **logical** bounded context, not a physical app split (analysis §3);
- the three-state model is **implementable as a client-side state
  machine over the EXISTING stateless ops with zero engine change**
  (analysis §4) — its "AI as assistant" semantics are an extension of
  the already-built selection-scope + lock laws, not a new paradigm.

One prior decision becomes MORE important (D-1: where the dashboard
lives), one gets deferred cleanly (D-2: required-omission — a Cutting
Table question, not a PDM question), and one new decision appears
(D-6: logical vs physical separation).

## 1. Sequencing — PDM first: correct, and here is the honest reason

The acceptance run showed the pattern-truth chain (Hub → versions) is
already the system's strongest part, and the composition experience is
the weakest. Intuition might say "fix the weakest first" — but the
composer can only ever be as good as the design surface it reads:
palette rows ARE dashboard rows; the six facts the owner wants per
design are the SAME six facts the palette needs later. **Every hour
spent on PDM is directly reused by the Cutting Table; none of it is
throwaway.** Sequencing verdict: right, with a bonus — PDM perfection
is freeze-compatible in spirit (read-only projections + navigation),
while the composer requires owner-gated amendments; doing PDM first
defers every unfreeze decision.

## 2. The Product Pattern Dashboard (PDM stage) — spec review

Per-size sections; every design row shows: geometry preview · reference
image · measured dimensions · confirmation status · version · edit.

- **All six facts + version are derivable READ-ONLY today** (inline
  geometry SVG exists on the version page; reference thumbs exist on
  Hub cards; tape W×H + MEASURED + v# live on version/piece pages).
  The dashboard is a re-projection — no schema, no writers.
- **Version display** should show: latest confirmed `v#` + a "v(n+1)
  draft in progress" marker when one exists — this closes V-5
  (newer-version visibility) in the same stroke.
- **The Edit button must resolve to the per-piece ladder.** The truth
  chain versions PIECES, not designs (ADR-D): "edit Front Panel · M"
  correctly means "open Front Panel's draft/version focused on M".
  A design-row Edit that deep-links there is natural; a size-level
  version model would be wrong. (Same caution as the previous review;
  the owner's row-level edit button is compatible — it is a LINK, not
  a new model.)
- **"General" size**: designs require a real `ProductSize` row (FK).
  Uniform hierarchy = a setup convention: a sizeless product gets one
  real size row (code `general`, label "General") when its first piece
  is registered. One checklist line + one honest question in the
  registration flow; no schema, no special workflow anywhere else.
- **Boundary (D-1) unchanged**: the dashboard needs patterns_ai data;
  production python cannot read it. Option A (the Hub grows into this
  dashboard) or Option B (URL handover). PDM-first makes this the
  FIRST decision needed, since the dashboard is now stage one.
- **What "perfect" should include** (so acceptance can measure it):
  size-sections + matrix both reachable (two lenses, one derivation) ·
  six facts per row · per-row Edit deep-links · readiness % + honest
  blockers/warnings retained · mobile summary-first · zero writes on
  view.

## 3. "Cutting Table = separate application" — the right kind of separate

Two interpretations, one recommendation:

- **Physical split** (a second Django app): the layout-side MODELS
  (runs, candidates, designations) live in patterns_ai today — moving
  models between apps means table renames/migration churn against
  frozen, populated tables. High cost, no behavioural gain. **Not
  recommended.**
- **Logical split (recommended, D-6)**: one bounded context inside the
  codebase with an enforced one-way interface:
  ```
  PDM context (design truth)          CUTTING TABLE context
  pieces · versions · geometry ·      runs · candidates · workspace ·
  references · Hub/dashboard          composer · approve · exports
            ▲                                   │
            └────── READ-ONLY design facade ◀───┘
                (resolver + list-designs-with-facts;
                 no design writes, ever — contract-tested)
  ```
  The composer imports the facade only; the facade never exposes
  writers. This is exactly the owner's sentence — "never becomes
  responsible for managing Pattern Designs" — made mechanical (an
  import-lint contract + the existing I-1 wall already covers writes).
- The separation also cleanly PARKS D-2 (required-omission policy) and
  D-3 (custom-set metrics) as Cutting-Table-stage decisions: PDM never
  needs them.

## 4. The three-state composition model — analysis

```
AVAILABLE ──select──▶ SELECTED ──place (manual drag │ AI fill)──▶ PLACED
    ▲                    │  ▲                                       │
    └────deselect────────┘  └──────────remove from canvas──────────┘
```

- **Sharper than two-state** — it separates *intent* (Selected) from
  *arrangement* (Placed), which is exactly the cutting-table mental
  model: pull the cardboard you plan to use to the table edge, then
  lay pieces one by one.
- **"AI optimizes only Selected-not-yet-Placed" maps DIRECTLY onto the
  built laws**: Placed pieces = fixed obstacles (the lock law);
  the free set = Selected \ Placed; the existing stateless optimize op
  already does exactly "place these free pieces around those fixed
  ones". **Zero engine change.** Manual placements should auto-lock by
  default (AI never moves the operator's hand-laid work — the owner's
  "AI as assistant" sentence, expressed in the existing lock
  vocabulary); the operator can unlock any placed piece to hand it
  back to the AI — one rule, no new machinery.
- **All three states live CLIENT-SIDE until a run-creating act** —
  identical in character to the validated Keep/undo/preview model
  (server remembers nothing; immutability intact; provenance recorded
  at save with the declared multiset). The prior review's §4 mechanics
  stand unchanged; the three-state model is a better UI state machine
  over the same spine.
- **Undo** must span the client transitions (select/deselect/place/
  remove/AI-fill) — the owner's earlier undo question answered by
  design this time: yes, undo naturally returns items along the same
  arrows (DN-1 satisfied because everything is client state until
  save).
- Rules the model needs stated (Cutting-Table-stage decisions):
  - Save persists the **Placed** set. Selected-but-never-placed at
    save ⇒ honest prompt ("2 selected designs are not on the canvas —
    save without them?").
  - AI-fill can FAIL for some free pieces (doesn't fit) ⇒ per-piece
    honest naming, pieces stay Selected (not silently dropped) —
    consistent with the complete-or-refuse law.
  - Live metrics during composition describe the PLACED set, labeled
    ("placed 12 of 18 selected") — no pretend numbers.
  - D-2 (omit a required design) and D-3 (garment metrics on custom
    sets) decided at this stage, not before.

## 5. Risks in the refined direction

- **R-8 · Dashboard/Hub duplication during PDM.** The Hub already
  half-does this (cards, matrix, readiness). Building the dashboard
  BESIDE the Hub would create two competing truths. The PDM stage
  should be framed as the Hub EVOLVING into the dashboard (or moving
  to the production URL — D-1), never a second parallel page.
- **R-9 · Client state-machine complexity** (three states × undo ×
  AI-fill × locks). Contained: it is the same discipline the Phase-5
  editor already proved (transforms-over-immutable-base), extended
  with two more transition types. Needs the same test rigor.
- **R-10 · Facade discipline decay.** A logical split only holds if
  contract-tested (import-linter contract + a "composer never writes
  design tables" wall). Cheap to add, must not be skipped.
- **R-11 · Sequencing temptation.** PDM stage will surface "while
  we're here" composer wishes. The stage gate must be an acceptance
  validation of PDM ALONE (scenarios below) before any composer work
  opens.

## 6. Acceptance additions for the PDM stage (when the owner orders it)

- Dashboard walk: every size section lists exactly its confirmed
  designs; the six facts match the version-page truth per row.
- Version marker: create a v2 draft on one piece → the affected rows
  show "v1 confirmed · v2 draft in progress".
- Edit deep-links: row Edit lands on the right piece/version focused
  view in ≤1 hop.
- General-size product: register a piece on a sizeless product → the
  General convention engages → identical hierarchy everywhere.
- Zero-writes on all dashboard GETs; worker 403; mobile summary-first.

## 7. Decisions table (updated)

| # | Decision | Stage |
|---|---|---|
| D-1 | Dashboard home: Hub-evolves (A) vs URL handover (B) | **PDM — needed first** |
| D-6 (new) | Separation: logical bounded context + read-only facade (recommended) vs physical app split | PDM (sets the frame) |
| D-2 | Required-design omission policy in composition | Cutting Table |
| D-3 | Metric honesty on custom compositions | Cutting Table |
| D-4 | Classic Generate page fold/soak | Cutting Table |
| D-5 | Sequencing | **Resolved by this refinement: PDM first** |

## 8. Spine (unchanged, all options shaped to preserve it)

Immutable saved layouts · run-level composition provenance · one
verifier · honest named skips/omissions/failures · approve = explicit
audited pointer move · derived-at-read metrics · collect-once (Hub/
dashboard = the only design-truth surface) · ADR-H wall · per-piece
version chain (ADR-D).

**STOPPED — review only. Nothing implemented. The refined direction is
sound; next concrete step (when the owner orders it) would be the PDM
stage design against §2/§6, starting with decision D-1.**
