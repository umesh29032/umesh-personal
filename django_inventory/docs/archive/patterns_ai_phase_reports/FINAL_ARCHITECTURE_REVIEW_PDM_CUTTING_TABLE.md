> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# FINAL ARCHITECTURE REVIEW — Pattern Design Management + Digital Cutting Table
(2026-07-07 · the review-before-implementation · REVIEW ONLY — no code,
no tasks, no phases. Rib / accessories / stages / fabric-groups:
out of scope, not mentioned again.)

Direction under final review (owner-locked wording):
**Product → Product Sizes → Pattern Designs → Cutting Table → Saved
Layouts → Production Layout → Export.** PDM first via the **Product
Pattern Workspace** (Product Summary · Sizes · Pattern Designs · Open
Cutting Table · Approved Layouts). Composition = **Available → Selected
→ Placed → Saved Layout**. AI = assistant, never touches manual work.
Option A (Hub evolves; no URL handover). Goal: a DIGITAL CUTTING TABLE,
not an automatic nesting system.

---

## 0. Verdict up front

**The architecture is sound and stable enough to become the Cutting
Table foundation — CONFIRMED — with five pre-implementation decisions
(§10), one of which is a genuine catch the section name "Approved
Layouts" just exposed (§4.2: approval history is currently LOST on
every replace — decide before PDM, because every future re-approve
destroys another fact).** Nothing found requires changing the
hierarchy, the four-state model, the AI law, or Option A.

## 1. Option A (Hub evolves) — is it the correct long-term decision? YES.

- A URL is an address, not an architecture. The workspace is
  patterns_ai-domain truth; serving it from the patterns_ai app keeps
  the ADR-H wall untouched *by construction* rather than by care.
- Option B's only gain is cosmetic (the literal production URL); its
  costs are real (sidebar-rule migration, tests, bookmarks, muscle
  memory) and its risk is subtle (a patterns_ai view living at a
  production address invites future "just read one production thing
  here" erosion).
- B remains available FOREVER at pure routing cost if the owner ever
  wants the address — deciding A now closes no doors.
- One follow-through A requires: the production page's single button
  becomes "Open Pattern Workspace" (product language), and the smart
  redirect's incomplete-setup branches should land on the workspace —
  already their shape today.

**Confirmed: A.**

## 2. "Product Pattern Workspace" — name and shape

- The name is right and it also FIXES a latent clash this review would
  otherwise have flagged: the code already calls the layout editor
  "workspace" (`/patterns/workspace/<pk>/`, workspace.html). Two
  workspaces = operator confusion. **Vocabulary ruling needed (cheap
  now, expensive later):** product language = "Pattern Workspace" (the
  owner's page) and "Cutting Table" (the composer+canvas); the editor
  stops being called workspace anywhere a user can see. Internal
  file/url names can stay (rename = churn), but the visible vocabulary
  table must be written down (§9).
- The five sections map cleanly onto existing truth: Product Summary
  (product + profile + readiness %) · Sizes (the size chart) · Pattern
  Designs (the size-grouped rows — six facts + version + edit) · Open
  Cutting Table (the one action) · Approved Layouts (see §4.2).
- "Everything visible from the dashboard" needs one honest boundary
  stated now, or it balloons: the workspace is one-stop for
  UNDERSTANDING (all six facts + preview per design, no hops) and
  one-HOP for ACTION (edit/capture/confirm stay on their focused
  pages, deep-linked). Recreating the version page inside every row
  would wreck mobile and density — the split above is the right
  "perfect".

## 3. The four-state model — formalized (and one clarification it needs)

Owner's addition of **Saved Layout** as the fourth state is correct —
"Placed is still temporary" is exactly the immutability spine speaking.
Formalization the build will need: these are TWO nested state machines,
and naming them prevents a whole class of future bugs:

```
Per DESIGN-INSTANCE (client-side, undoable, lost unless saved):
  AVAILABLE ─select→ SELECTED ─place(manual│AI)→ PLACED
      ▲                 │▲                          │
      └───deselect──────┘└───remove from canvas────┘

Per LAYOUT (server-side, immutable chain — already built):
  [browser composition] ─Save→ SAVED LAYOUT ─★Approve→ PRODUCTION ─→ EXPORT
```

- Save is the bridge: it collapses the instance-machine into one
  immutable layout with declared-multiset provenance. Reopening a
  saved layout re-enters the instance machine with every piece PLACED
  (arrange-only unless composition ops occur, which are run-creating —
  per the prior reviews).
- AI law consequence worth stating: once AI places a piece it is
  PLACED and therefore untouchable by the next AI run too. Re-running
  AI over its own previous fill requires the operator to hand pieces
  back (remove→Selected, or an explicit "return AI-placed pieces"
  gesture — worth designing as ONE control, else operators will drag
  pieces off one by one).
- Deselect of a PLACED design must be guarded (remove from canvas
  first) — one rule, prevents state divergence.

## 4. Hierarchy challenges (assumption hunting)

### 4.1 Levels — sound
Product→Sizes→Designs→CuttingTable→Saved→Production→Export holds.
Version stays an attribute of design truth (per-piece chain, ADR-D);
the Edit action deep-links to the piece ladder — compatible.

### 4.2 ⚠️ THE CATCH: "Approved Layouts" (plural) vs what is stored
The law is exactly-one CURRENT ★ (OneToOne pointer + audit fields).
**When the pointer moves, the PREVIOUS approval fact (who approved
that layout, when) is overwritten — approval HISTORY is not persisted
anywhere.** The acceptance run demonstrated it: #16 was approved, then
replaced by #22 — #16's approval record no longer exists. The
workspace section "Approved Layouts" can today show: the current ★ +
all immutable saved layouts — but NOT "previously approved, by whom,
when".
- If the owner means the section as "★ + saved layouts" — no gap.
- If the owner means real approval history (the plural suggests it,
  and factory audit instinct agrees) — this needs an append-only
  approval log, which is a SMALL, additive, data/history-principles-
  conformant schema decision that should be taken at the PDM stage —
  **because it cannot be backfilled: every re-approve between now and
  then permanently loses a fact.** → Decision **D-7**, the one
  schema-touching item in this whole direction.

### 4.3 "Available = designs for the selected sizes"
Implies a size/quantity step BEFORE the palette — good (bounds the
palette, keeps garment metrics alive). State it as step zero of the
Cutting Table. And Available must mean **confirmed designs only**
(drafts never compose — consistent with generation law today).

## 5. Scalability review

- Workspace page weight: sizes × designs × (geometry preview + ref
  thumb). 8×6 = 48 rows ≈ fine; 20 pieces × 8 sizes = 160 rows needs
  per-size collapse + lazy preview loading from day one (design
  constraint, not architecture). Geometry previews as simplified
  outlines (fewer vertices) keep DOM cheap.
- Saved/Approved section growth: grouping (by month or by composition)
  should be in the FIRST workspace design, not retrofitted — the flat
  switcher list is already at 8 after one validation day.
- Client composition state: bounded naturally by the engine envelope
  (~50 comfortable pieces); Phase-5 discipline (transforms over
  immutable base) already proved this scale.
- Derivations (readiness, six facts) are per-product single queries
  today; no N+1 risk if the facade (§6) is the single supplier.

## 6. The facade should be born WITH PDM (not with the Cutting Table)

D-6's read-only design facade (list-designs-with-facts + resolver) is
usually framed as the composer's interface — but the WORKSPACE rows
need exactly the same facts. Building the workspace directly on ad-hoc
queries and then introducing the facade for the composer would leave
two supply paths for one truth. **Recommendation: the facade is a PDM
deliverable; the workspace becomes its first consumer; the Cutting
Table inherits it for free.** (This is the one sequencing nuance this
final review adds.)

## 7. Mobile usability — one honest posture decision needed (D-8)

- The WORKSPACE must be mobile-first and can be: summary-first
  accordion per size, card-stacked rows, tap-to-zoom previews (the
  lightbox exists), 44 px edit targets. No architectural risk.
- The CUTTING TABLE is a different animal: palette + three-state tray
  + canvas on a 390 px phone is not how a cutting master will work —
  the factory reality is desktop/tablet at the table. The standing
  mobile-first rule (functional requirement) therefore needs an
  explicit, owner-acknowledged scoping for the composer: **phone =
  inspect/review/approve; compose = tablet and up.** Pretending the
  full composer will be phone-first would produce a worse product and
  a dishonest review. → Decision **D-8**.

## 8. What becomes HARD after the Cutting Table is built (act-before list)

1. **Approval history (D-7)** — hard forever if not decided now (facts
   are being destroyed by each replace).
2. **Vocabulary (§9)** — trivial now; renaming user-visible concepts
   after operators learn them is not.
3. **Facade-first (§6)** — retrofitting the facade under a live
   workspace + composer means re-plumbing two consumers.
4. **Composition provenance format** — the run params payload gains a
   declared-multiset shape at CT time; versioning that payload
   (schema_version bump) should be specified in the CT design, not
   invented mid-build.
5. **Saved-layout grouping** — retrofit cost grows with every saved
   layout.
None of these blocks the direction; all are cheapest exactly now.

## 9. Vocabulary table (to lock with the PDM design)

| Concept | Product language | NOT to be called |
|---|---|---|
| The owner's page | **Product Pattern Workspace** | dashboard, hub, library |
| The composer+canvas | **Cutting Table** | generator, workspace, editor |
| Design readiness | Confirmed (design) | approved |
| Layout designation | **Approved / ★ Production layout** | confirmed |
| Instance states | Available · Selected · Placed | staged, queued, pending |
| Persisted result | Saved Layout (immutable) | draft (a saved layout is not a draft; unapproved ≠ draft) |

("Confirmed" vs "Approved" carrying two meanings today is exactly the
kind of overload operators trip on — the table kills it.)

## 10. Pre-implementation decisions (complete list — nothing else open)

| # | Decision | When | Review's recommendation |
|---|---|---|---|
| D-1 | Workspace home | **RESOLVED: Option A** (owner + this review concur) | — |
| D-5 | Sequencing | **RESOLVED: PDM first** | — |
| D-6 | Separation | logical bounded context + facade | facade born at PDM (§6) |
| **D-7** | Approval history: append-only approval log vs "★+saved is enough" | **PDM (cannot backfill)** | add the small append-only log |
| **D-8** | Cutting Table mobile posture | PDM sign-off (sets expectations) | phone = inspect/approve; compose = tablet+ |
| D-2 | Required-design omission policy | Cutting Table design | loud-banner-allow |
| D-3 | Metric honesty on custom sets | Cutting Table design | "garments: —" honesty |
| D-4 | Classic Generate fold/soak | Cutting Table design | fold into CT after soak |

## 11. The spine (final restatement — everything above preserves it)

Immutable saved layouts · declared composition provenance per run ·
one verifier · honest named refusals/skips/failures · approve =
explicit audited pointer move (+ history if D-7 = log) ·
derived-at-read metrics · collect-once (the Workspace = the only
design-truth surface) · ADR-H wall · per-piece version chain ·
client-side transience until Save.

## 12. Final statement

**Challenged: hierarchy, naming, state model, AI law, Option A,
scalability, mobile, operator flow, and the post-build pain list. One
real catch surfaced (D-7 approval history — decide at PDM). With D-7
and D-8 decided, this architecture is STABLE and is hereby confirmed
as the foundation for the Pattern Design Management stage and the
Cutting Table stage that follows. No changes to the owner's direction
are recommended beyond the decisions table above.**

**STOPPED — final review delivered. No code, no tasks, no phases.
Awaiting the owner's D-7 and D-8 rulings and the order to design the
PDM stage.**
