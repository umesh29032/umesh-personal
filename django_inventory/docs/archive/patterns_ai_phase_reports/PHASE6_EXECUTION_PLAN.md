> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PHASE 6 EXECUTION PLAN (2026-07-07) — engineering plan, no design

**Scope = the frozen design, nothing else: integration items 1–9
(INTEGRATION_DESIGN §5) + PDF export + full-marker tiled print + final
validation. Every milestone ends with STOP; nothing proceeds without
approval. No Phase 7 exists.**

## 1. Implementation order (smallest safe milestones)

### M1 — Engine hardening: BLF internal timebox (item 9, finding F1)
- **Objective:** the grid-BLF placement pass respects a timebox and
  gives up HONESTLY ("layout too large for the Quick method — the
  Thorough method handles large mixes") instead of hanging until the
  bridge kills it. Applies to generation BLF, the optimize op, and the
  verify-free paths that reuse the scan.
- **Files:** `compute/patterns_ai/nest.py` only.
- **Browser behavior:** none (engine-level); CLI smoke recorded.
- **Tests:** big-set BLF returns within box with the honest error ·
  small sets unchanged (byte-determinism suite still green) · optimize
  op under locks inherits the same give-up · existing 13 M1-engine
  tests untouched.
- **Regression impact:** none expected (additive time check); full
  engine suite re-run.

### M2 — Schema (the ONE migration)
- **Objective:** all Phase-6 storage in a single additive migration:
  `ProductFabricProfile` (OneToOne→production Product; default width /
  layer length / spacing; **optional production metadata: fabric type ·
  GSM · lay mode** (owner refinement 4 — natural profile fields, display
  + export-summary only, no logic hangs on them); **`production_layout`
  FK→saved layout + `approved_by`/`approved_at`** — the
  exactly-one-per-product designation BY STRUCTURE) · `PatternPiece.is_optional`
  (default False) · `PatternPiece.reference_image` (nullable FK→
  CaptureAsset) · `CaptureAsset.Kind.REFERENCE_IMAGE` choice.
- **Files:** `models/generation.py` or new `models/profile.py`,
  `models/pieces.py`, `models/capture.py`, `models/__init__.py`,
  migration `patterns_ai/0007`, `tests/test_purity.py` (pin 15→16,
  conscious).
- **Browser behavior:** none yet.
- **Tests:** pin move · field defaults · FK protections ·
  `makemigrations --check` clean after.
- **Regression impact:** pin test consciously updated; everything else
  untouched.

### M3 — Services (single writers + semantics)
> **As-built amendment (owner-approved behavior review, 2026-07-07):**
> the frozen contract lives in INTEGRATION_DESIGN §3i — F-1 approve takes
> (user, product, layout) · F-2 `set_piece_optional` added to the
> PatternPiece writer · F-3 same-layout re-approve = strict no-op ·
> F-4 optional skip per (piece, size), persisted warnings · F-5 two new
> writer modules (fabric_profile_service, production_layout_service) ·
> F-6 `set_reference_image` lives in pattern_geometry_service · Rules
> A/B · `collect_confirmed_geometry` → `resolve_generation_geometry`.
- **Objective:** `set_fabric_profile(...)` (defaults) ·
  **`approve_production_layout(user, layout)`** — the explicit act
  (§3g): audited who/when, refuses unverified layouts, never bundled
  with save; `clear` = approving another layout (the FK moves) ·
  **optional-skip semantics**: `collect_confirmed_geometry` skips
  optional pieces lacking designs for the requested sizes and records
  the honest note (required pieces keep blocking with names) ·
  `set_reference_image(piece, asset)` (kind-checked, display-only).
- **Files:** `services/marker_generation_service.py` (or a small
  `services/profile_service.py`), `services/pattern_geometry_service.py`,
  `services/capture_service.py` (kind whitelist), I-1 test extension.
- **Browser behavior:** none yet (service-level).
- **Tests (the heavy milestone):** approve happy/audited · approve
  refuses unverified + non-product layouts · designation moves, old
  layout intact · optional piece skipped WITH note when designs missing ·
  optional included when designs exist · required still blocks by name ·
  profile bounds validation · reference image kind/product checks ·
  zero-writes walls still hold for read services.
- **Regression impact:** `collect_confirmed_geometry` change touches
  generation — full P3/P5 engine+service suites re-run; DEV-TEE mix
  re-validated.

### M4 — Smart redirect + entry button (items 1–2)
- **Objective:** `/patterns/tool/<product>/` view implementing the
  locked priority (approved → latest saved → generate → library →
  register) + the single `is_management`-gated button on the production
  Product Pattern Design page (template-level URL only).
- **Files:** `views.py`, `urls.py`, ONE production template (the pattern
  page), boundary test.
- **Browser behavior:** button appears for management; click lands per
  state; workers see nothing, URL 403s them.
- **Tests:** all 5 priority branches (fixtures per state) · worker
  403/anon 302 · tamper 404 · production-imports wall re-asserted.
- **Regression impact:** one production template line-set (precedent:
  Adda links); purity scan proves direction unchanged.

### M5 — Layout switcher + prefills (item 3 + item 8 consumption)
> **As-built amendment (owner rules F/G/H/I, 2026-07-07 — §2c):** the
> "prefill the editor width/height/spacing" line below is SUPERSEDED by
> Rule G — saved layouts always display their own stored values; profile
> prefills the Generate form only. Switcher = version-history menu
> (★ → drafts newest-first → ＋ Generate New) with the document-editor
> unsaved-changes confirm; pure links (Rule I).
- **Objective:** editor toolbar "Layout ▾" (★ production → saved drafts
  → "＋ Generate New Layout") + profile defaults prefill Generate form
  and editor width/height/spacing (editable as always).
- **Files:** `workspace.html`, `views.py` (switcher context; prefill
  context), `generate_form.html`.
- **Browser behavior:** switcher jumps between saved layouts without
  losing the page; ★ marks production; prefills appear, remain editable.
- **Tests:** switcher ordering (role, not recency) · ★ only when
  approved · prefill values render · absent profile ⇒ current defaults ·
  Phase-4/5 editor suites still green.
- **Regression impact:** editor template touched — full phase4/5 UI
  suites + a browser editing pass.

### M6 — Pattern Design Hub (item 5, consuming 6+7+8)
- **Objective:** the library page becomes the collect-once Hub —
  **framed as an extension of Product setup, not a second product**
  (product-first heading/breadcrumb; the owner's workflow owns it):
  Types × Sizes **validation checklist** with visible per-cell
  completeness **plus a product-level readiness percentage/status**
  (owner refinement 2; generation stays the final honest backstop),
  required/optional badges + toggle, reference-image slot per piece,
  fabric-profile edit panel (incl. the optional metadata),
  "Pattern Designs complete" banner.
- **DEV-TEE becomes the permanent validation dataset** (owner
  refinement 3): completed here + at M9 with pattern photos (synthetic
  goldens — the metrology rule), reference images (license-safe
  self-rendered piece illustrations unless the owner supplies specific
  images), archived DXF exports, confirmed measurements — so the full
  lifecycle demos end-to-end forever.
- **Files:** `piece_list.html` (+ small partials), `views.py`,
  `piece_form.html` (optional flag at registration).
- **Browser behavior:** incomplete product shows exact ✗ cells and the
  banner withholds; completing a design flips the cell; reference image
  visible; profile editable.
- **Tests:** checklist math per state (required-missing blocker ·
  optional-missing warning · unconfirmed · complete) · banner logic ·
  optional toggle via service · uploads for reference images gated.
- **Regression impact:** library page markup — piece/library view tests
  re-run.

### M7 — Approve UI + Production Layout Summary (item 4 + §3f)
- **Objective:** "Approve for production" button on the saved-layout
  page (explicit, separate from Save) + the **Production Layout
  Summary** block (width · required layer length · utilization · waste ·
  pattern count · size ratio — facts + derived-at-read) on the approved
  layout; switcher ★ goes live end-to-end.
- **Files:** `candidate_detail.html` (product-language labels),
  `views.py`.
- **Browser behavior (owner refinement 5):** the Production Layout
  Summary renders on the saved layout BEFORE approval — the user reviews
  exactly what is about to become the production layout, with the
  explicit audited Approve button beneath it → after approve the layout
  is marked ★ and redirect priority 1 lands here → editing + saving
  creates a DRAFT (designation untouched) until a new explicit approve.
- **Tests:** approve via UI · save-never-moves-designation (the §3g
  law, asserted) · summary values match derive functions · re-approve
  moves ★ · old layout intact.
- **Regression impact:** candidate page tests re-run.

### M8 — Exports (PDF + full-marker tiled print + summary stamping)
- **Objective:** `pdf` op in the compute runtime — **pure-python PDF
  writer (zero new dependencies)**, treated as a PRODUCTION DOCUMENT
  (owner refinement 6): **page 1 = the Production Layout Summary;
  remaining pages = the tiled true-scale marker** (numbered tiles,
  overlap marks);
  PDF download view · full-marker **tiled true-scale print page** (HTML,
  tile grid + scale bar + summary, like the Gate-1 print) · SVG export
  gains the summary block as metadata text.
- **Files:** `compute/patterns_ai/pdf_io.py` (new), `nest.py` untouched,
  `compute_bridge.py` (tool entry), `views.py`, `urls.py`, one print
  template.
- **Browser behavior:** Download PDF (opens true-scale, summary on
  p.1, tiles numbered) · print page renders tiles + 10 cm bar.
- **Tests:** PDF parses (header/xref sanity + page count math for known
  lengths) · true-scale points math pinned · tiling covers length with
  overlap marks · summary values present · SVG metadata block ·
  exports of the approved DEV-TEE layout.
- **Regression impact:** compute runtime gains a tool — ADR-F walls
  re-run; no engine changes.

### M9 — Final validation + PROJECT CLOSE
- **Objective:** everything fresh: full serial suite, app suite,
  migrations, contracts, sweep, health, complete E2E (Product button →
  redirect → Hub completeness → generate w/ prefills → edit → optimize →
  save draft → approve → summary → switcher ★ → PDF/print/SVG exports),
  mobile pass, hostile engineering review, PHASE6_COMPLETION_REPORT,
  freeze, **project COMPLETE statement**.
- **Files:** docs only (+ fixes for anything the review finds,
  correctness-class only).
- **Regression impact:** the whole point.

## 2. Dependency order

```
M1 (BLF timebox)          — independent, safest first
M2 (migration 0007)       — everything below needs the fields
  └─ M3 (services)        — approve/optional/profile/reference writers
       ├─ M4 (redirect+button)     — priority #1 reads the designation
       │    └─ M5 (switcher+prefills) — ★ reads designation; prefills read profile
       │         └─ M6 (Hub)            — shows optional/reference/profile/checklist
       │              └─ M7 (Approve UI + Summary) — the owner-stated chain end
       └─ M8 (exports)    — needs only M2/M3 (summary facts) — can follow M7
M9 (final validation)     — last, after all
```
(Owner's stated chain honored: Smart Redirect → Switcher → Approve.)

## 3. Database changes — ONE migration

| Migration | Contents | Why | Production impact | Rollback |
|---|---|---|---|---|
| `patterns_ai/0007` (M2) | new `ProductFabricProfile` (OneToOne product · width/length/spacing defaults · `production_layout` FK · approved_by/at) · `PatternPiece.is_optional` bool default False · `PatternPiece.reference_image` nullable FK · `CaptureAsset` kind choice (no DB change) | items 4, 6, 7, 8 | ZERO: purely additive — new table + nullable/default columns; no data migration; no production-app tables touched; existing rows unaffected | fully reversible (drop table/columns); no data loss possible on forward; designation is a nullable FK — rollback simply forgets approvals |

Model pin 15→16 (conscious, documented in the pin test). No other
migrations anywhere in Phase 6.

## 4. Test plan (summary; details per milestone above)

- **Unit:** ~10 (M1 engine) · ~6 (M2 schema/pin) · ~16 (M3 services —
  the largest: approve laws, optional semantics, profile, reference) ·
  ~8 (M4 branches+walls) · ~6 (M5) · ~8 (M6 checklist math) · ~6 (M7
  §3g law) · ~10 (M8 PDF/tiling math) ≈ 70 new.
- **Browser:** per milestone as listed; M9 = the full E2E chain +
  mobile @390.
- **Regression:** full serial manufacturing suite + patterns_ai suite +
  migrations + import contracts EVERY milestone; sweep + health at M9.
- **Honest failure cases baked in:** BLF give-up message · approve
  refuses unverified · required-missing still blocks with names ·
  optional-missing warns and skips with note · save-never-approves ·
  redirect on empty product lands at register · PDF for a 15 m marker
  produces the right page count · tamper 404s everywhere.

## 5. Implementation risks & validation

| Risk | Validation |
|---|---|
| **Import wall** (production button/template) | template-level URL only; purity scan + M4 boundary test re-assert direction; NO context processors |
| **Migration ordering** | single migration, additive-only; `--check` gate in every milestone battery; FK targets all pre-existing |
| **Editor state** (switcher navigating away from unsaved edits) | switcher = plain links (full page load); unsaved-work loss is the browser-native rule already true for Reload — M5 adds a confirm prompt ONLY if testing shows accidental loss is easy (decided by browser test, not speculation) |
| **Export consistency** (PDF vs SVG vs canvas) | one geometry source (stored outlines); PDF/tiling math pinned against known-length fixtures; DEV-TEE visual diff by eye in M8 browser pass |
| **Production approval** (silent change) | §3g law tested: save-never-moves-designation assertion + approve-is-explicit UI test |
| **Switcher state** (★ correctness) | ordering unit tests + browser re-approve flow in M7 |
| **BLF timeout** (F1) | M1 first; big-mix DEV-TEE case becomes a permanent test fixture |
| **PDF correctness w/o a library** | minimal PDF spec (paths+text only), deterministic output, parse-sanity tests; if hand-rolled PDF proves unworkable in practice, STOP and report per the impossible-clause — no silent library adoption |
| **Optional semantics breaking existing generation** | full P3/P5 suites + DEV-TEE regeneration in M3 battery |

## 6. Stop points

**After every milestone M1–M9: STOP. Report (summary · files · tests ·
browser proof where applicable · regression). Wait for approval. Never
continue automatically.** M9 ends with the freeze and the project-
complete statement — and nothing after it.
