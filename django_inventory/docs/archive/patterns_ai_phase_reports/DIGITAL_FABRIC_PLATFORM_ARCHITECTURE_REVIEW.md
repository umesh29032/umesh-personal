> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# DIGITAL FABRIC PLANNING PLATFORM — business-architecture challenge review
(2026-07-08 · REVIEW ONLY · manufacturing CAD/CAM lens, NOT a Django review ·
challenges every assumption as requested, before permanent freeze)

Relation to earlier docs: this reviews the PLATFORM philosophy the owner
declared 2026-07-08. Where it agrees with BUSINESS_ARCHITECTURE_FREEZE_REVIEW.md
that is stated once and not repeated; this document is the industry challenge.

---

## 0. The strongest validation first

Your four-responsibility split is not an invention — it is, almost line
for line, **the segmentation the garment-CAD industry converged on after
40 years** (Gerber AccuMark, Lectra, Optitex all ship it this way):

| Your platform application | Industry name | Verdict |
|---|---|---|
| PRODUCT | Style master / PDM | ✅ standard |
| PRODUCT SIZE MANAGEMENT | Size run / size chart | ✅ standard |
| PRODUCT PATTERN BLUEPRINT | Piece list (pattern BOM) | ✅ standard |
| PATTERN DESIGN MANAGER | Pattern making + grading + digitization | ✅ standard |
| DIGITAL CUTTING TABLE | **Marker making** (Diamino / AccuNest) | ✅ standard |
| APPROVED LAYOUT | **The Marker** | ✅ standard |
| ADDA STAGE → LAYERING → CUTTING | Cut order execution: spread & cut | ✅ standard |

That an owner using his own factory reinvented the industry-standard
architecture independently is the strongest possible signal the direction
is right. **The skeleton is correct. Freeze-worthy.** Everything below is
where the flesh is missing or where your text contradicts itself.

---

## 1. Is it internally consistent? — YES, minus TWO contradictions in your own text

**CONTRADICTION 1 — Reference image silently became a readiness
requirement.** Your "WHEN DOES A SIZE BECOME READY" list includes
*Reference*. Your own locked verdict law (and your acceptance-validated
behavior) says: reference = illustration, display-only, NEVER required —
a tape-measured confirmed geometry without a photo is fully cuttable.
Both cannot be law. **Decide at freeze:** keep reference
recommended-not-required (my recommendation — the geometry is the
manufacturing truth; a photo proves nothing the tape didn't), or
consciously upgrade it to required and accept that legacy/DXF-imported
designs go un-Ready until someone photographs paper patterns.

**CONTRADICTION 2 — "THE manufacturing reference" (singular) vs how
factories actually cut.** Your text: "they approve a layout. That layout
becomes THE manufacturing reference." A real production run needs
**several concurrent markers per product**: one per fabric (body marker ≠
rib marker ≠ lining marker), per ratio, per fabric width, plus remnant
markers. Law 8 is right that approved layouts are the only manufacturing
truth — but the truth is a **LIBRARY of approved markers, plural**, each
with identity (name, fabric, width, ratio, length, utilization), and the
Adda stage CHOOSES one. Singular-★ thinking must die at this freeze, not
at the Adda refactor — because Law 9 (Adda consumes layouts) is
unimplementable without marker selection.

Everything else in the flow is consistent, including: Universal default,
blueprint auto-inheritance to new sizes, optional-never-blocks,
per-size preparation workspaces, ≥1-Ready gate (your "Ready Product
Sizes unlock" phrasing is now correctly ≥1, not all — the earlier
ambiguity is gone).

One explicitness gap, not a contradiction: the CT loads "Available Sizes
☑S ☑M ☑L ☑XL" — state that **only READY sizes are importable** (L =
Needs Attention → L greyed out on the table). Otherwise Law 5 leaks.

---

## 2. Are responsibilities clean? — YES, with three boundary rulings needed

The four-way split is clean. Three seams need an explicit owner or they
will be violated by accident:

**B-1 · Piece RULES belong to the Blueprint, not the Design Manager and
not the CT.** Grain line, pair/mirror allowance, fold rule, optional
flag — these are facts about WHAT the piece is (App 3), consumed by
App 4 (readiness) and App 6 (placement constraints). Your text puts
"Grain Direction / Rotation Rules / Pair Rules / Mirror Rules" under CT
FABRIC CONFIGURATION — **half wrong.** Fabric has a grain; but whether
*this piece* must lie on-grain, may rotate 180°, may mirror — that is a
piece property. If the CT session owns piece rules, two operators get
two different physics for the same piece. Ruling: **piece rules =
Blueprint; fabric facts = fabric spec; the CT only combines them.**

**B-2 · Readiness is a DERIVED verdict owned by nobody.** "Size M Ready"
is computed from Blueprint (required list) ∩ Design Manager
(confirmations). Neither app stores it; both must never cache it. Name
this in the freeze so nobody ever persists a `ready` flag that drifts.

**B-3 · Fabric is MASTER DATA, not a CT session setting.** Your fabric
configuration (width 48"/60"/72"/90", margins, spacing, shrinkage-ready)
describes a **fabric specification catalog** — a platform-level entity
the CT *selects from*, not free-typed numbers per session. Reason: the
approved marker is only valid FOR its fabric spec (§3, coupling K-1);
free-typed widths make two "60-inch" markers incomparable.

---

## 3. Hidden coupling problems? — YES, four. This is the meat of the review.

**K-1 · Approved Layout ↔ physical fabric (the invalidation nobody
modeled).** A marker made for 60" fabric is PHYSICALLY INVALID on 58"
fabric. So: every approved layout must permanently freeze its fabric
spec, and the Adda stage must MATCH the actual roll on the table against
the layout's spec before execution — a check, not a convention. Without
it, Law 9 hands the Cutting Master a beautiful lie.

**K-2 · Fabric GROUPS — your own acceptance evidence, absent from this
architecture.** Your T-SHIRT acceptance run's central observation (§3.8)
was: *body pieces and rib pieces were mixed in one marker — unnatural —
they are cut from different fabrics.* This platform text never mentions
fabric groups. The law that's missing: **one marker composes pieces of
ONE fabric group only; the Blueprint tags every piece with its fabric
group; the CT partitions by group.** A t-shirt is minimally TWO markers
(body + rib). Freezing without this re-freezes the exact flaw your own
validation caught.

**K-3 · Geometry version ↔ approved marker (the ECN problem).** Law 10
stops downstream edits — correct — but says nothing about UPSTREAM
change. Front-Panel geometry v3 gets confirmed AFTER a marker was
approved on v2. Industry answer (engineering change notice): the
approved marker is immutably bound to exact geometry versions, is never
mutated, and is flagged **STALE** ("newer confirmed geometry exists —
re-approve to use it"). The staleness signal is the ONLY legitimate
backward channel in the whole platform. Missing law — proposed as
Law 11 (§6).

**K-4 · The marker × plies arithmetic (where planning meets execution).**
Pieces produced = (pieces in marker) × (number of plies spread). Your
flow lists LAYERING but no application owns ply count, and nothing
states that the Adda's verified per-size production counts must
reconcile against `marker content × plies`. Declare the boundary: the
platform ends at approved-marker hand-off; the existing production
system owns plies/execution; the JOIN CONTRACT is "marker size-content ×
plies = expected cut quantities per size." Undeclared, this seam will be
invented ad-hoc during the Adda refactor.

---

## 4. Is the Digital Cutting Table correctly defined? — CONCEPT YES, four corrections

The definition — separate application, consumes prepared geometry,
operator composes, AI assists-never-owns, manual placements sacred — is
exactly a professional marker-making tool. Corrections:

**T-1 · Fabric width is a CONSTRAINT; fabric length is a RESULT.** "Infinite
canvas" is fine as UX, but the business object is a marker of fixed
width whose LENGTH is the outcome to minimize
(utilization = Σ piece area ÷ (width × length)). Listing "Fabric Length"
as a pre-configured input inverts the economics of marker making.
The real length limit is the **physical cutting table length** — a
different constraint, worth its own field in the fabric/table spec.

**T-2 · Composition without a TARGET is aimless — the missing CUT PLAN /
RATIO concept.** "Selecting a size imports ALL pattern designs of that
size" = one garment-set per size. Real markers are ratio markers:
1×S : 2×M : 2×L : 1×XL in ONE marker, driven by what the order needs.
Your platform currently has NO application answering "how many of each
size do we need?" (today the Adda's hand-entered proportion % answers it,
badly). The CT must accept a size-ratio target (import Size M **× 2**),
and the approved marker must record its ratio — because ratio is exactly
what the Adda stage needs to reconcile production. This is the single
biggest missing CONCEPT in the platform (industry: "cut planning").
It does not need to be a fifth application at v1 — a ratio input on the
CT session is enough — but the freeze must name it, or "import size"
hardwires 1:1:1:1 forever.

**T-3 · Per-fabric-group tables** (K-2): opening the CT for T-Shirt means
composing per group — Body table, Rib table — not one mixed table.

**T-4 · AI optimization must be assumed ASYNC.** Your own acceptance run
killed nesting at 60–90s on realistic piece counts. Business-architecture
consequence: "AI Optimize" is a JOB the operator awaits (with progress /
cancel), never a blocking click. State it now; retrofitting async onto a
synchronous UX contract is expensive.

Everything else on the CT list (drag/rotate/flip/lock/snap/measure/
undo/groups/zoom) is correct professional-CAD table stakes; the 4-state
model (Available→Selected→Placed→Saved) already locked earlier remains
compatible with this text.

---

## 5. Does it scale to thousands of products? — STRUCTURALLY YES, three governance gaps

Scaling is clean because everything partitions per product: blueprint,
designs, markers — no cross-product coupling anywhere in the laws. The
gaps at scale are governance, not structure:

- **S-1 · Piece-name governance.** Thousands of products each defining
  "Front Panel" free-form → library chaos (Front/FRONT/Front Panel/Front
  Pannel). The blueprint should draw piece TYPES from a curated shared
  vocabulary with product-level overrides — otherwise search, analytics
  and AI training data all rot.
- **S-2 · Marker-library identity.** Hundreds of approved markers per
  product family (fabric × width × ratio) require first-class identity +
  search (name, fabric spec, ratio, utilization, status
  active/stale/retired). Follows directly from Contradiction 2.
- **S-3 · Nesting compute.** Thousands of products ⇒ nesting farm/queue
  economics (T-4). A per-click synchronous optimizer dies at exactly the
  moment the platform succeeds.

---

## 6. Fundamentally missing before permanent freeze? — YES: two concepts, one declaration, three laws

**Missing concept 1 — CUT PLAN / SIZE RATIO** (T-2). Biggest one.
**Missing concept 2 — FABRIC as master data + FABRIC GROUPS on the
blueprint** (B-3, K-1, K-2). Second biggest — and your own acceptance
evidence demands it.

**Missing declaration — the CUT LINE.** Nowhere does the platform say
whether confirmed geometry is the SEW line or the CUT line (seam
allowance included or not). Every pattern system on earth must declare
this; ambiguity here poisons every marker silently. Recommend declaring:
**platform geometry = CUT-ready contour, seam allowance already
included; the Design Manager confirms cut lines.** One sentence, saves a
factory of ruined fabric.

**Missing minor decisions** (each one line at freeze):
- Approval AUTHORITY: who may approve a marker (role), approval is
  immutable + audited.
- Readiness is entry-path-agnostic: the linear pipeline you listed
  (photo→processing→…→confirm) is the canonical PHOTO path, not the only
  path — DXF-import and manual draw reach the same checklist. Your own
  T-SHIRT was DXF-imported; don't freeze a law your best product already
  violates.
- Blueprint uniformity across sizes is LAW (good, keep) — with the noted
  v1 simplification that "pocket only on XL"-type cases are handled by
  the optional flag, and per-size requiredness is a registered FUTURE
  blueprint concern, never a Design-Manager hack.
- Resolve Contradictions 1 (reference) and 2 (marker plurality).

**Proposed additional laws** (completing your ten):

> **LAW 11 — An approved layout is immutably bound to exact geometry
> versions and one fabric specification. Upstream changes never mutate
> it; they mark it STALE, and stale markers cannot be handed to
> production without re-approval.**
>
> **LAW 12 — One layout composes pieces of ONE fabric group. Products
> with multiple fabric groups produce multiple markers.**
>
> **LAW 13 — Every layout is composed against an explicit size-ratio
> target and a fabric specification chosen from master data, and both
> are frozen into the approved layout.**

---

## 7. Answers, one line each

1. **Consistent?** Yes — after resolving the reference-in-readiness and
   singular-marker contradictions in your own text.
2. **Responsibilities clean?** Yes — with piece-rules→Blueprint,
   readiness→derived-never-stored, fabric→master-data rulings.
3. **Hidden coupling?** Four real ones: marker↔fabric-spec validity,
   fabric groups, geometry-version staleness (ECN), marker×plies
   reconciliation.
4. **CT correctly defined?** Conceptually exactly right (it is marker
   making); fix width-vs-length economics, add ratio target, partition
   by fabric group, declare AI async.
5. **Scales to thousands?** Structurally yes; needs piece-name
   governance, marker identity/search, async nesting economics.
6. **Missing before freeze?** Cut plan/ratio · fabric master + groups ·
   cut-line declaration · Laws 11–13 · approval authority ·
   entry-path-agnostic readiness · the two contradictions resolved.

**Freeze the skeleton — it is industry-correct. Do not freeze the text
as written until the §6 list is ruled, because two of the gaps (fabric
groups, ratio) are things your OWN acceptance run already proved the
factory needs.**

---

## 8. Owner ruling 2026-07-08 — vocabulary + DCT module map

**RULING: "Open Cutting Table" → "Open DIGITAL Cutting Table"
everywhere.** Rationale accepted: "Cutting Table" reads as one screen;
the thing is an APPLICATION. Rename scope verified: two UI strings
(`piece_list.html` gate button, enabled + disabled variants) + two code
comments; no test asserts the label text — a trivial edit, executes with
the next approved implementation milestone (freeze holds until then).

**The owner's DCT module breakdown** — reviewed, and it CONVERGES with
this document's challenges rather than fighting them:

| DCT module (owner) | Maps to | Note |
|---|---|---|
| Fabric Settings | fabric SPEC selection | must draw from fabric master data (B-3/K-1), not free-typed |
| Available Pattern Library | the read-only facade, `palette` mode | Design-Row atom already reserves this mode |
| Imported Pattern Pieces | Selected state (4-state model) | + ratio multiplier per T-2 (import Size M × 2) |
| Digital Fabric Canvas | Placed state, the CAD surface | new build — the real work of the DCT stage |
| AI Optimizer | nest engine | ASYNC job (T-4); Selected-not-Placed only (locked) |
| Layout Manager | saved-layout library | plural markers — resolves Contradiction 2 in the owner's own diagram |
| Layout History | version/approval history | **owner just implicitly resolved deferred D-7: history IS a DCT module** |
| Export DXF / PDF | M8 export machinery | exists — reuse, verified-layouts-only rule stands |
| Approve Layout | M7 approve flow (summary-before-approve) | exists — reuse; add Law-11 staleness + Law-13 freezing |

Reading: the DCT application = ONE genuinely new surface (the canvas +
its panels) wrapped around FOUR existing, tested subsystems (facade,
approve, export, saved layouts). The module list is architecturally
sound and consistent with Laws 1–13 as amended.

---
**STOPPED — challenge review delivered. No code, no plans, no redesign.
Awaiting your rulings on: Contradictions 1–2 · Laws 11–13 · the §6
missing-concept list. Rename ruling recorded, executes at unfreeze.**
