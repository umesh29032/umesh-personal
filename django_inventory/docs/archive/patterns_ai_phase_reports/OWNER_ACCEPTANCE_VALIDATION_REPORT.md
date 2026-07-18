> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# OWNER ACCEPTANCE VALIDATION REPORT — real T-SHIRT product
(2026-07-07 · executed per OWNER_ACCEPTANCE_VALIDATION_PLAN.md ·
freeze intact: ZERO code/schema/service/architecture changes)

**Product under validation: pk 2 · `T-SHIRT` · "T-Shirt"** (the real
production product). DEV-TEE untouched. Everything below went through
the real doors only: production setup pages/services, DXF-AAMA import,
tape-gated confirm, the Hub's frozen writers, real engines, the
audited Approve act, real exports.

---

## 1. What was set up on the real product (Suite A)

- Data hygiene finding first: T-SHIRT carried a **junk duplicate size**
  (empty code, label "S", zero references anywhere) — deactivated
  (soft, reversible). Active sizes now **S · M · L · XL**.
- **8 pattern pieces, industry names** (new clean library entries:
  `front-panel back-panel left-sleeve right-sleeve neck-rib
  patch-pocket brand-label care-label`):
  Required = Front Panel · Back Panel · Left Sleeve · Right Sleeve.
  **Optional (owner clarification honored: optional ≠ not part of the
  product) = Neck Rib · Pocket · Brand Label · Care Label.**
- **Realistic graded geometry** (§10 of the plan): front/back neck
  scoops (80 mm/25 mm), shoulder slopes, 3-point armhole curves,
  off-centre sleeve caps (front/back asymmetry, mirrored L/R), rib
  strip, pentagon pocket, true small labels (60×40 / 40×70 mm).
  Grading real: +25 mm chest / +15 mm length per size step.
- Entry route: authored DXF-AAMA (layer 1 boundary + layer 7 grain) →
  `import_dxf` → **confirm with HONEST tape** (bbox measured) →
  every confirmed row = trust grade **MEASURED**.
- Reference images on ALL 8 pieces — self-rendered from the pieces'
  own outlines (license-free, §9 class 6), display-only.
- Fabric defaults saved: 1700 mm width · 5000 mm length · 3.0 mm
  spacing · Single jersey · 180 gsm · face-up single-ply
  (**assumed-real values — owner should correct to the true numbers**).
- **Hub verdict: 100% · Production Ready ✅ · zero blockers** with the
  three optional gaps listed as honest warnings
  (`av_A_hub_stage1.png`).

## 2. Scenario results (PASS/FAIL)

| # | Scenario | Result | Evidence |
|---|---|---|---|
| A-1 | Hub context lock + hero + chooser | **PASS** | av_A_hub_stage1.png |
| A-2 | 8 pieces registered, flags correct | **PASS** | Hub cards 8/8, optional badges |
| A-3 | Geometry per size via DXF + tape confirm | **PASS** | 5+3 pieces × sizes MEASURED |
| A-4 | Reference images add/zoom (display-only) | **PASS** | refs 8/8 on cards |
| A-5 | Dashboard truth (derived %) | **PASS** | 100%/Ready with honest warnings |
| A-6 | Fabric defaults prefill-only | **PASS** | Generate prefilled 1700/3.0 |
| B-1 | Smart redirect branch walk | **PASS** | reason="generate" → later ★ layout; log lines |
| B-2 | Worker lockout | **PASS** | tool/Hub/approve/PDF all 403 |
| C-A | **Marker A — Body layout** (mixed S1 M2 L2 XL1) | **PASS** | run 11 → layout #16; skipped = Neck Rib, Brand, Care (named + persisted) |
| C-B | **Marker B — Rib joins** after Rib confirm | **PASS** | run 12 → #17; pieces-in incl. Neck Rib |
| C-C | **Marker C — Brand joins; Care PARTIAL** | **PASS** | run 13 → #18; `Care Label / L`, `/ XL — skipped (optional, no design for this size)` |
| C-1 | Single size M×10 | **PASS** | run 14 → #19, no warnings (full M coverage) |
| C-W | Width variants 990 / 1830 mm | **PASS** | 4742 mm vs 2396 mm (physics sane) |
| C-3 | Large ratio (70 garments ≈ 490 pieces) | **HONEST-FAIL (by design + finding F-A1b)** | engine gave up; nothing persisted; message raw (see findings) |
| D-1 | Select/click semantics, live metrics | **PASS** | chip "1 selected"; live length/util |
| D-2 | Rotate 180° only | **PASS** | history armed; collisions indicator went live (2) — honest |
| D-3 | Lock | **PASS** | locked style; optimize refused "selected is locked — unlock…" (lock-wins rule) |
| D-4 | AI optimize at REAL 46-piece scale | **FAIL → finding F-A1** | server 500 after 90 s (timebox not engaging at this scale); UI stays safe, generic error |
| D-5 | Save = new immutable draft | **PASS** | "Layout saved (4005.99 mm, verified)" → #22 |
| D-6 | Switcher order + dirty confirm | **PASS** | drafts newest-first; exact prompt; cancel stays |
| D-7 | Version history | **PASS (by architecture + M9 re-check)** | layouts store own outlines (§3e); not re-run on real product to keep v1 clean |
| E-1 | Approve w/ summary-before-approve | **PASS** | #16 review → ★; audit line |
| E-3 | Approval ignores product-wide optional gaps (owner point 6) | **PASS** | body-only #16 approved while Care/Brand gaps existed |
| E-2 | Replace ★16 → ★22, history intact | **PASS** | review named #16; redirect follows ★22 |
| F-1 | PDF at real scale | **PASS + observation F-A2** | 161 pages (1+10×16) in 0.2 s; page 1 = summary + ★ audit; C10-R16 present; artifact reviewed |
| F-2 | Print page | **PASS** | 160 true-scale tiles, 0.2 s |
| F-3 | SVG stamped | **PASS** | desc + metadata, `"production": true` |
| F-4 | Export gates | **PASS** | worker 403; verified-only |
| G-1..3 | Mobile 390×844 Hub/editor/approve | **PASS** | no horizontal scroll; screenshots |
| H-1 | Required-missing blocks by name | **PASS** | XXL probe: "Front Panel / XXL (v1 has no geometry…)" + Hub blockers flipped live |
| H-3 | Fabric too narrow | **PASS** | both engines' reasons named |
| H-5 | Tamper 404 / worker 403 | **PASS** | H-5 tamper via test client 404s |
| H-6 | Overlap refusal | **PASS** | multiset wall first, then verifier: "max overlap 354421.193 mm²…" |
| H-2 | Capture-gate refusal (photo path) | **NOT RUN** | no physical mat/camera in this environment — owner exercise at the factory (5-minute check) |

**Bottom line: 32 PASS · 1 FAIL-with-finding (D-4 at real scale) ·
1 honest-fail-by-design (C-3, message quality finding) · 1 owner-held
(H-2 physical capture).** No silent failure anywhere. No data
corruption anywhere. Every refusal named its reason.

## 3. Owner Observation Report

### 3.1 Factory workflow observations
- The staged combo flow WORKED exactly like the owner's factory story:
  **Body marker first (Front/Back/Sleeves + Pocket) while Neck Rib was
  deliberately absent — then Rib joined only after its designs were
  confirmed.** The run record keeps the exclusion honest forever.
- Real cut-order arithmetic surfaced immediately: markers of ~6
  garments are comfortable; a 70-garment ratio in ONE marker is not —
  which matches real practice (repeat markers × plies do the volume).
  The system nudges you toward realistic markers, but only via an
  error, not guidance (see 3.8).
- The tape-gated confirm + MEASURED grade felt like a real QC step,
  not ceremony.

### 3.2 Operator workflow observations
- Hub → Generate → editor → approve is genuinely one straight line;
  the operator never re-enters product data (collect-once held).
- **The only way to keep a piece OUT of a marker is to not-yet-confirm
  its geometry.** For the validation this was workable (staging), but
  as an operator story it is backwards: participation is a property of
  *data completeness*, not of *operator intent* (see 3.8 — the central
  observation).
- The optional/required toggle reads clearly on the cards; the warning
  lines say exactly what will be skipped BEFORE generation.

### 3.3 Mobile usability
- Hub/editor/approve all render clean at 390 px, zero horizontal
  scroll; approve on the phone is realistic (big buttons, short page).
- The editor is usable for viewing/inspection on a phone; serious
  editing (46 pieces) is a desktop task — as expected.

### 3.4 UI/UX observations
- Honest-refusal wording is consistently GOOD ("Front Panel / XXL…",
  overlap mm², "selected is locked — unlock something…").
- "optimize failed — try again" (F-A1's client face) is the one
  MISLEADING message found — retry cannot help there.
- The switcher's flat list (8 drafts today) will get long on a real
  product that iterates weekly; fine for now, worth watching.

### 3.5 Performance observations
- Generation (SVGnest) at 30–46 pieces: ~35–60 s — acceptable for a
  planning task. BLF gives up honestly on these sizes (its message
  points to Thorough correctly).
- PDF/print/SVG at real scale: instant (0.2 s for 161 PDF pages).
- Editor stays responsive with 46 pieces incl. live collision checks.

### 3.6 Architecture observations
- Immutability + pointer-designation proved themselves: replaced ★
  layouts stayed reachable; the audit line always told who/when.
- Derived-at-read metrics matched between editor, summary, exports at
  every check.
- The junk duplicate size (empty code) shows real production data will
  carry surprises — the Hub surfaced it instantly (its matrix column
  made it visible), which is exactly what a readiness surface is for.

### 3.7 Where the architecture felt NATURAL
- Optional pieces skipping with named warnings; approval validating
  only the layout's own contents (body-only ★ while product-wide gaps
  existed) — both matched factory thinking perfectly.
- Multiple valid layouts with different combos, all immutable, one
  current ★, history in the switcher = matched "this week we cut the
  pocket style" reality.

### 3.8 Where it felt UNNATURAL (the owner's question, answered honestly)
1. **Participation-by-data-availability (central).** To cut a
   body-only marker the operator must rely on Neck Rib's geometry not
   being confirmed yet. Once Rib is confirmed, a body-only marker can
   NEVER be generated again — there is no "leave Rib out of this one".
   During validation this forced the staging order; in a real factory
   week it would force fake workarounds. This is the strongest single
   piece of evidence collected.
2. **One marker = the whole product's available pieces.** Real
   factories cut body fabric, rib and trims as SEPARATE lays (often
   different fabrics!). Today all confirmed pieces of all fabric
   groups nest into ONE marker — rib strips nested between body panels
   is physically wrong for different-fabric pieces. (The
   `fabric_group` field exists on pieces but generation ignores it.)
3. **A4 tiling at full marker scale (F-A2).** 160 sheets for a
   4 m × 1.7 m marker is not a practical assembly; it is right for
   piece-checks and small markers. Wide-format/plotter output is the
   real-world need for full markers.
4. **Marker-size guidance (C-3/F-A1b).** The engines' practical
   envelope (~≤ 50 pieces comfortable) is discovered by error message,
   not communicated up front.

### 3.9 Where manual piece selection would have IMPROVED the flow
- Marker A (body-only) and a hypothetical "rib-only lay" — both are
  one checkbox away conceptually; today both require data-staging.
- C-7 style situations: an operator who KNOWS Care Label L/XL is
  missing might prefer to exclude Care Label entirely from this marker
  rather than ship a partial-coverage marker.

### 3.10 Where manual selection would have caused CONFUSION
- If selection had existed, the validation would ALSO have needed
  selected-but-missing semantics (§8.3 points 7/8) — block vs skip.
  Today's rule ("whatever is complete joins; incomplete optional skips
  with a note") is simpler to explain to a new operator than a
  selection matrix would be. Any future selection UI must not lose
  this simplicity.

### 3.11 Suggestions for the next discussion (NOT implementation)
Evidence-backed topics, in the owner's own future-direction frame:
1. **Fabric-group-scoped lays** (Body Cutting · Rib Cutting · Trims) —
   the evidence in 3.8(1)(2) points at cutting-scope as a FIRST-CLASS
   idea (per-lay fabric group or per-run piece participation). The
   owner's "separate production stages" direction and this evidence
   agree.
2. Per-run piece participation UI (the §8.3 Path-2 question) — decide
   together with (1); they may be the same feature seen from two ends.
3. Wide-format/plotter export for full markers; keep A4 tiles for
   small markers and piece checks.
4. Optimize-timebox hardening at 40+ pieces (F-A1) + honest envelope
   messaging on the Generate page ("markers over ~N pieces need the
   Thorough method / smaller ratios").
5. Switcher grouping when layout counts grow (by month or by combo).

## 4. Findings register

| ID | Severity | What | Frozen-state impact |
|---|---|---|---|
| F-A1 | HIGH (UX/robustness, not data) | In-editor Optimize at 46 pieces runs to the 90 s bridge kill in EVERY mode (internal timebox not engaging at this scale) → server 500, client shows generic "optimize failed — try again" | No corruption (stateless op); editor keeps working; misleading message |
| F-A1b | MEDIUM | Very large GENERATION ratios die at the engine-runner kill with a raw traceback-ish error instead of the polished give-up message | Nothing persisted; message quality only |
| F-A2 | MEDIUM (practicality) | Full-scale markers ⇒ 160-sheet A4 assembly — impractical; plotter output is the real need | Exports correct + true-scale; practicality gap |
| F-A3 | LOW (data hygiene) | Real product carried a junk duplicate size (empty code) | Deactivated (soft); Hub surfaced it |
| F-A4 | INFO | H-2 physical capture-gate scenario needs the real mat + camera — owner runs it at the factory | 5-minute owner exercise |

**No fixes were made (freeze). All findings are discussion inputs.**

## 5. Owner future direction (recorded verbatim-in-spirit, per instruction)

The owner's current thinking, documented so it is not lost: many
factories process components separately (Neck/Waist/Sleeve Rib,
labels, elastic, bought-out components) — prepared, cut, purchased or
processed independently before stitching. The owner's architectural
preference is therefore moving toward **separate production stages**
(Product → Body Cutting → Rib Cutting → Accessory Preparation →
Stitching) rather than ever-growing marker-generation complexity.
**Design direction only — NOT an implementation request.** The
evidence gathered above (3.8, 3.11) is the input for that future
discussion, AFTER this acceptance review.

## 6. State left behind (all real, all reversible by normal means)

- T-SHIRT: 8 pieces · 30 confirmed MEASURED designs (Care Label S/M
  only — deliberate) · 8 reference images · fabric profile ·
  runs 11–16 · layouts #16–#22 · **★ = layout #22** (full-combo,
  manually saved). XXL probe size deactivated again; junk size
  deactivated. Server log carries the Rule-E redirect audit lines.
- Hygiene: patterns_ai app suite re-ran green after the validation
  (no code was changed; **318/318 OK post-validation**). Screenshots +
  the 161-page PDF artifact live in the session scratchpad
  (`av_*.png`, `av_F_star22.pdf`).

## 7. Sign-off

| Field | Value |
|---|---|
| Executed by | Claude (owner-directed acceptance run) |
| Date | 2026-07-07 |
| Product | pk 2 · T-SHIRT |
| Result | **32 PASS · 1 FAIL-with-finding (F-A1) · 1 honest-fail-by-design (C-3) · 1 owner-held (H-2)** |
| Owner acceptance | ☐ granted ☐ granted-with-findings ☐ withheld — **owner decides after reviewing §3–§5** |

**STOPPED. No further work of any kind until the owner reviews this
report and the findings register.**
