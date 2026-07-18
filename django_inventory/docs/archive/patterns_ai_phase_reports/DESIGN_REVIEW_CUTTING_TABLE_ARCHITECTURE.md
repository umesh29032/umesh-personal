> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# DESIGN REVIEW — "Digital Cutting Table" Architecture Direction
(2026-07-07 · architecture review ONLY — nothing implemented, freeze
intact. Scope: Product → Size → Pattern Design → Layout Tool.
Rib / accessories / production stages: NOT discussed.)

Owner direction under review: **Product Pattern Dashboard** (size-
grouped, previews, at `/production/products/<id>/patterns/`) →
**compose-first Layout Tool** (available designs ⇄ added-to-layout →
canvas → manual → AI optimizes only the selected → save).

---

## 0. Review verdict in one paragraph

The direction is coherent and — surprisingly — **mostly buildable on
the EXISTING frozen spine without new models**: composition can live
client-side over the existing stateless ops, the selection-scope
optimize law already implements "AI optimizes only what the operator
chose", and the per-design provenance the palette needs is already
persisted per run. The two hard points are (1) the **ADR-H boundary**
(the dashboard's home page is a production URL, and production python
can never read patterns_ai — three lawful mechanisms below), and
(2) a **policy ruling** the composition model forces: what happens when
an operator deliberately composes a marker WITHOUT a required piece.
Everything else is UI projection + one resolver-input generalization.

## 1. Architectural strengths of the proposal

1. **Dashboard-first entry matches how factories think.** Today the
   tool "starts" at Generate (a form); a cutting master starts at "what
   does this product have?". Moving the mental anchor to a pattern
   dashboard removes the most abstract page from the front of the flow.
2. **Size-grouping = production language.** Markers are composed in
   size terms; a size-sectioned view (S: its five designs…) reads like
   a cut order. The data grain (Design = Piece × Size) already IS this
   — the dashboard is a pure re-projection, zero schema.
3. **Compose-first = the real cutting table.** Physical masters lay
   cardboard onto fabric one piece at a time; "available ⇄ on-table" is
   exactly that. It also finally makes participation an act of
   OPERATOR INTENT instead of data-availability (the central unnatural
   point the acceptance run proved).
4. **"AI optimizes only selected designs" is ALREADY the law.** The
   Phase-5 selection-scope rule (optimize moves selected∩unlocked;
   everything else = obstacles) was built and validated — the proposal
   extends an existing principle rather than fighting one.
5. **"General" fallback group** keeps ONE hierarchy for every product —
   the right instinct (no special workflows).

## 2. The boundary reality (must be decided first)

`/production/products/<id>/patterns/` is a **production-app page**, and
the dashboard needs patterns_ai content (designs, previews, statuses).
**ADR-H: production python never imports/queries patterns_ai —
permanent, test-walled.** Three lawful mechanisms:

| Option | Mechanism | Cost / character |
|---|---|---|
| **A — Hub becomes the dashboard** (recommended default) | reshape the existing patterns_ai Hub into the size-grouped dashboard; the production page keeps assignments + the one button (as today) | zero boundary risk; "one click behind" instead of "at the production URL"; smallest change |
| **B — URL handover** | patterns_ai mounts a NEW dashboard view AT `/production/products/<id>/patterns/` (URL routing is config-level — patterns_ai importing production is the allowed direction); production's assignment editor moves to `…/patterns/assignments/` | satisfies the owner's sentence literally; costs URL-ownership migration (tests, muscle memory, sidebar rules) but NO law is broken |
| **C — production page embeds via template include of a patterns_ai-rendered fragment** | template-level composition | rejected: crosses the spirit of the wall (production view would orchestrate patterns_ai rendering); listed only for completeness |

**Decision D-1 for the owner: A or B.** Both keep the wall intact; B
makes the production URL the literal home.

## 3. The size-grouped dashboard — analysis

- **As a VIEW: cheap and right.** Size sections with per-design preview
  thumbnails are a re-projection of data that exists (geometry SVG
  renderer already inline on the version page; readiness derivation
  already computes the piece×size grid). V-3 (thumbnails first-class)
  and this proposal are the same move.
- **As an EDIT grouping: careful.** "[Edit S Pattern Designs]" implies
  editing a size-slice as a unit — but the truth chain is **per-piece
  versions** (draft → confirm covers that piece's sizes; ADR-D). An
  "Edit S" button can only be a FILTERED VIEW of per-piece actions; it
  must not become a size-level version model. Recommendation: size
  sections for seeing + navigating; the edit ladder stays
  piece-anchored underneath (exactly today's Rule-K ladder, reached
  from a size lens).
- **"General" group:** designs REQUIRE a real ProductSize row
  (`PieceSizeGeometry.size` FK). The uniform-hierarchy goal is
  achievable as a **product-setup convention** — a sizeless product
  gets one real size row (code `general`) at setup time — not as a
  display hack and not as a schema change. Needs one line in the
  product-setup checklist; nothing else.
- Keep BOTH lenses reachable: the matrix (piece × size) answers
  readiness; the size sections answer composition. Same derivation
  feeds both.

## 4. Compose-first Layout Tool — the key finding

**The cutting-table flow can be built as a CLIENT-COMPOSED front end
over the existing immutable spine — no new models, no mutable
draft-layout state, no new writer.**

```
Palette (client)                      Existing spine (unchanged)
available designs, grouped by size
  operator adds/removes  ──────────▶  explicit composition multiset
  (garment-set quick-add + piece-     │
   level tweaks; undo = client)       ▼
                              start_run(composition)  → run + verified
                              candidates (immutable, provenance keeps
                              per-design ids exactly as today)
                                      ▼
                              canvas arrange → selection-scope optimize
                              (ALREADY only-selected by law) → save =
                              new immutable candidate
```

Why this works with the frozen laws:
- **Immutability intact**: nothing mutable ever persists; composition
  lives in the browser until the run-creating act, exactly like
  Keep/undo already do (Phase-5 clarifications: server remembers
  nothing until save).
- **Provenance intact**: `run.params.sources` already records
  piece/size/version/geometry-row per design — an explicit composition
  is BETTER provenance than a ratio, not worse.
- **One-verifier intact**: composed sets go through the same
  generate/verify door.
- **The resolver generalizes, not breaks**: today
  `resolve_generation_geometry(product, ratio)` derives the multiset
  from ratio+availability. Compose-first needs the same function fed an
  EXPLICIT per-design multiset (ratio becomes one convenient way to
  BUILD that multiset — "add one M garment set" = the ratio semantics
  as a palette shortcut). One frozen-API amendment, owner-gated.
- **Mid-editing composition** (add a Pocket·M after arranging): the
  multiset law ("save = exactly the source's pieces") is a
  per-save-vs-SOURCE rule. The lawful extension is: a composition
  change is a RUN-CREATING act — the save declares its own multiset
  with full provenance, seeded by the current arrangement (kept pieces
  = obstacles; new pieces placed by the existing stateless optimize).
  That amends the law's wording, not its purpose (no silent
  composition drift; every layout still explains itself).

## 5. Weaknesses & risks (R register)

- **R-1 · Required-piece policy under free composition (needs a
  ruling).** Owner-locked law: missing REQUIRED designs block. In a
  compose-first world the operator can deliberately omit Back Panel M.
  Options: (a) hard-block (kills cutting-table freedom), (b) allow
  with a loud honest banner + recorded note (mirrors optional-skip
  honesty), (c) allow only via an explicit "partial marker" toggle.
  **Decision D-2.** Recommendation: (b) — honesty over restriction,
  consistent with the system's character.
- **R-2 · Garment metrics semantics.** `derive_candidate_metrics`
  computes garments / per-garment length FROM the ratio. Free
  composition can make "garments" undefined (7 fronts, 5 backs).
  Mitigation: palette's garment-set quick-add keeps a ratio when the
  operator composes in sets; piece-level tweaks mark the run
  "custom composition" and per-garment metrics honestly display "—".
  **Decision D-3** (accept metric degradation on custom sets?).
- **R-3 · Two collection surfaces risk.** The Hub (collect-once) and
  the composer must not blur: Hub = product truth (designs, geometry,
  references); composer = per-marker intent. Keep the composer
  READ-ONLY over designs — it never edits geometry/flags. (Guards the
  collect-once law.)
- **R-4 · Smart-redirect priorities shift.** If compose-first becomes
  primary, priority 3 ("confirmed geometry → Generate form") should
  land on the composer instead. Small, but the locked redirect table
  needs a consciously-amended row (owner-gated).
- **R-5 · Palette scale.** 8 pieces × 6 sizes = 48 preview SVGs on one
  page — fine; 20 pieces × 8 sizes needs lazy rendering. Known,
  solvable, not architectural.
- **R-6 · URL handover (if Option B)**: sidebar gating, tests,
  bookmarks, and the production assignment editor's new address — a
  mechanical but real migration.
- **R-7 · Scope creep guard.** Compose-first + palette + dashboard is
  a Phase-scale build, not a milestone. The frozen-state review S-1/S-2
  (read-only composition panel + generate preview) remains the cheap
  first step and is FULLY REUSED by this direction (the palette's
  "added" list = S-1's Included list made interactive). Nothing is
  wasted by doing S-1/S-2 first.

## 6. UI improvements (within this direction)

- Palette row = the owner's six facts exactly: geometry preview
  (true-shape mini SVG) · reference thumb (piece-level, V-6 stands) ·
  piece name · size · tape W×H (MEASURED badge) · confirmation status
  — all already derivable read-only.
- **Garment-set quick-add per size section** ("＋ add 1 × M set") —
  bridges ratio-thinking and piece-thinking; keeps R-2 metrics alive.
- Composition tray with the three states the owner named: Available ·
  Added (with counts) · Not-yet-added; skipped/omitted notes inline.
- Canvas keeps everything already validated (drag/rotate/lock/undo/
  optimize strip/save); UX-3/4/5 niceties (size legend, persistent
  labels, selected-piece info card) fold naturally into the palette
  work.
- One sentence of UI copy on the composer: "Composing changes what the
  marker cuts; the canvas arranges it" (UX-6 resolved by design).

## 7. Workflow improvements

- Entry chain becomes: **Product page → Pattern Dashboard (size-grouped
  truth) → [Compose marker] → palette+canvas → optimize → save →
  approve** — one straight line, each step in factory language.
- The classic Generate form (ratio + width) survives as the quick path
  INSIDE the composer (a ratio quick-fill = "compose by sets"), not as
  a separate page. **Decision D-4:** retire the standalone Generate
  page after the composer proves itself, or keep both during soak.
- The Hub remains the setup surface (readiness, geometry ladder,
  references, fabric defaults) — linked from the dashboard, never
  merged into the composer (R-3).

## 8. A better hierarchy? (owner asked)

The proposed hierarchy is right. One refinement — make the marker act
explicit as its own level, because that is where intent lives:

```
Product
  → Product Pattern Dashboard (sizes → designs, previews, readiness)
      → MARKER COMPOSITION (operator intent: which designs, how many)
          → Canvas (arrange · lock · AI-optimize the selection)
              → Saved Layout (immutable) → Approve ★ → Exports
```

And one naming suggestion in the same spirit: call the palette page
**"Cutting Table"** — operators already own that phrase; "Generate" is
engine language (the vocabulary rule that renamed engine→Method in
Phase 5 applies again here).

## 9. What simplifies the operator experience WITHOUT new architecture

Ranked; every item is display/derivation only:
1. S-1/S-2 from the composition review (Included/Skipped/Available
   panel + pre-run preview) — the palette's read-only ancestor.
2. Size-grouped dashboard view with mini geometry previews (this
   direction's face, buildable on today's derivations).
3. Size legend + persistent labels + selected-piece info card in the
   editor (UX-3/4/5).
4. The Cutting-Table copy/vocabulary pass.
The only pieces that genuinely need an (owner-gated) architecture
amendment are: explicit-multiset resolver input, the required-omission
policy (D-2), and mid-edit composition-as-new-run (§4) — all three are
contained, none touches storage.

## 10. Owner decisions needed before any build order exists

| # | Decision |
|---|---|
| D-1 | Dashboard home: Option A (Hub becomes it) or B (URL handover to patterns_ai) |
| D-2 | Required-piece omission policy in compose-first: block / loud-banner-allow / explicit-partial-marker toggle |
| D-3 | Custom compositions: accept "garments: —" metric honesty when sets are broken |
| D-4 | Classic Generate page: fold into composer or keep during soak |
| D-5 | Sequencing: S-1/S-2 first as the read-only ancestor (recommended), or straight to the composer |

## 11. The spine that must survive any of this (unchanged from §9 of the composition review)

Immutable saved layouts · run-level composition provenance · one
verifier · honest named skips/omissions · approve = explicit audited
pointer move · derived-at-read metrics · Hub collect-once · ADR-H wall.
Every option in this review was shaped to keep all eight.

**STOPPED — architecture review only. Nothing implemented. Awaiting
D-1…D-5 and the owner's direction.**
