> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# Phase 6 · M2 REPORT — the ONE migration (two-model architecture)
(2026-07-07)

**Status: ✅ M2 COMPLETE — STOPPED. M3 will not start without approval.**

## Migration report — `patterns_ai/0007` (single, additive, reversible)

| Change | Why | Production impact | Rollback |
|---|---|---|---|
| new `ProductFabricProfile` | long-lived product defaults ONLY (width/length/spacing prefills + fabric_type/gsm/lay_mode metadata) | none — new table | drop table |
| new `ProductionLayout` | the designation ONLY: OneToOne(product) + `approved_layout` PROTECT FK + approved_by/at | none — new table | drop table (forgets designations; layouts untouched) |
| `PatternPiece.is_optional` | pattern-set semantics; **default False = everything stays required unless explicitly flagged** | nullable-free default column | drop column |
| `PatternPiece.reference_image` | display-only documentation FK | nullable column | drop column |
| `CaptureAsset.Kind.REFERENCE_IMAGE` | choices-only (no DB change) | none | choices revert |

**Reversibility PROVEN live:** `migrate patterns_ai 0006` → unapplied OK →
`migrate` → re-applied OK. No data migration anywhere; zero production-app
tables touched.

## Final schema diagram (owner-locked §3h)

```
production.Product
│
├── patterns_ai.ProductFabricProfile   (OneToOne — DEFAULTS ONLY)
│      default_width_mm · default_length_mm · default_spacing_mm
│      fabric_type · gsm · lay_mode
│      [NEVER references any layout]
│
├── patterns_ai.ProductionLayout       (OneToOne — DESIGNATION ONLY)
│      approved_layout ──PROTECT──▶ immutable saved layout
│      approved_by · approved_at
│      [NEVER contains fabric defaults; pointer moves, layouts never change]
│
└── Saved Layouts (GeneratedMarkerCandidate — immutable, append-only)
       Layout A · Layout B · Layout C · …
       [approval history = these rows + the audit fields]
```

## Engineering review
- The pre-migration 8-rule review's finding (designation merged into the
  defaults profile) was corrected BEFORE the migration existed — the two
  models now have single responsibilities and independent lifecycles.
- Exactly-one-approved-per-product is structural (OneToOne), not
  conventional; approve-duplicates-nothing is structural (FK to an
  immutable, PROTECTed row).
- `is_optional=False` default means the migration cannot silently weaken
  any existing required-pattern validation (all current pieces stay
  required).
- Reference images are excluded from geometry STRUCTURALLY — extraction
  already refuses any capture kind ≠ `pattern_capture` (source-pinned in
  the tests); M3 adds the service whitelist on top.
- Model pin consciously 15 → **17** (documented in the pin test).
- No writers exist yet for the new models (M3) — the I-1 wall already
  covers both names.

## Test results
- **M2 suite 5/5**: profile holds defaults only (layout-ish field names
  asserted ABSENT) · designation is pointer-only (defaults field names
  asserted ABSENT) + exactly-one enforced by the DB (IntegrityError on a
  second row) + PROTECT on the layout · **pointer move leaves the layout
  byte-untouched** · `is_optional` defaults False · reference-image kind
  exists + extraction's kind gate source-pinned.
- Purity/pin suite green at 17 models.
- Full battery: counts below.

## Browser validation
N/A per plan (schema milestone — no UI yet).

## Regression
patterns_ai **235/235 OK** (230 + 5 M2) · full manufacturing suite **1120/1120 OK** (serial, fresh) ·
`makemigrations --check`: **No changes detected** · import contracts
unchanged · vendored code + Django venv untouched.

**STOPPED — awaiting approval for M3 (single-writer services:
approve / optional-skip / profile / reference images).**
