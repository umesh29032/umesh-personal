# Cutting Pattern Validation + Cutting Stage — Design Doc

**Status:** Design only. No code yet. Drafted 2026-05-28.
**Author intent:** Umesh (junior dev) + Claude pair-design session.
**Companion docs:** [OVERVIEW.md](OVERVIEW.md), [CUTTING_PATTERN.md](CUTTING_PATTERN.md), [LAYERING_STAGE.md](LAYERING_STAGE.md), [TRACKING.md](TRACKING.md).

This doc captures the agreed-upon design for upgrading the **Cutting Pattern** stage validation rules and building the **Cutting** stage from skeleton to full production-ready. It supersedes the bare bullet plan in [PRODUCTION_APP.md](PRODUCTION_APP.md) for these two stages.

---

## 1. Business goals

### 1.1 Cutting Pattern stage — purpose
Verify that the physical pattern placement on layered cloth matches the product's predefined pattern structure (Front × 1 + Back × 1 + Sleeve × 2 …). Pattern designer also picks which **sizes** are in this batch and what **proportion** each size carries.

### 1.2 Cutting stage — purpose
Convert layered cloth + verified patterns into actual production pieces. Track per-(size, color, pattern) breakup. Generate metadata-rich barcodes that downstream manufacturing scans.

### 1.3 Manufacturing flow (target)

```
Cloth Rolls
   └─▶ Layering Stage            (rolls + layers + leftovers)
        └─▶ Cutting Pattern      (pattern verification + sizes + proportions)
             └─▶ Cutting Stage   (per-size / per-color / per-pattern piece breakup)
                  └─▶ Barcodes   (size + color + pattern + roll metadata)
                       └─▶ future: machine / worker / movement tracking
```

---

## 2. Current state — gap analysis

### 2.1 Cutting Pattern (partially built)
Source: [cutting_pattern_service.py](../../config/production/services/cutting_pattern_service.py), [pattern_stage_views.py](../../config/production/views/pattern_stage_views.py), [_stage_panel_cutting_pattern.html](../../config/production/templates/production/_stage_panel_cutting_pattern.html).

| Capability | Current | Required by spec |
|---|---|---|
| Workers assignment | ✔ `start_pattern_stage` | ✔ keep |
| Video upload | ✔ optional | ✔ keep |
| Photo upload (multiple) | ✔ Pillow-compressed | ✔ keep |
| Photo per-pattern linkage | ✘ photos are generic | ✔ each verification can attach photo |
| Per-pattern verification (✓/✗ + audit) | ✘ | ✔ **new model required** |
| Pattern count match validation at completion | ✘ only "video OR ≥1 photo" | ✔ all `ProductPatternAssignment` rows verified |
| Sizes-in-batch picker (subset of ProductSize) | ✘ no ProductSize model exists | ✔ **new model + M2M required** |
| Per-size proportion entry | ✘ | ✔ **new through-model required** |
| Reopen | ✔ admin unlock | ✔ keep |

### 2.2 Cutting (skeleton only)
Source: [cutting_service.py](../../config/production/services/cutting_service.py) (53 lines, one function), [_stage_panel_cutting.html](../../config/production/templates/production/_stage_panel_cutting.html), [stage_views.py:827](../../config/production/views/stage_views.py).

| Capability | Current | Required by spec |
|---|---|---|
| `complete_cutting()` | ✔ single shot: pieces_cut int + bulk barcode | ✘ replace with multi-step lifecycle |
| `start_cutting()` draft | ✘ | ✔ **add** |
| Per-(size,color,pattern) breakup | ✘ single int only | ✔ **new model required** |
| Suggested-count formula | ✘ | ✔ **`lay_count × Σpattern_assignments.pieces_count × proportion_pct`** |
| Save Draft | ✘ | ✔ **add** |
| Reopen | ✘ | ✔ optional v2 |
| Barcode metadata (size/color/pattern/roll FK) | ✘ value-only | ✔ **add FKs on BatchBarcode** |
| Tests | ✘ | ✔ add |

### 2.3 BatchBarcode (one-shot generator)
Source: [barcode_service.py](../../config/tracking/services/barcode_service.py), [tracking/models.py:33](../../config/tracking/models.py).

Current value: `{adda.code}-{piece_seq:04d}` (e.g. `T-SHIRT-001-0042`).
Required value: encode pattern + size + color so scans resolve metadata server-side **and** stickers carry human-readable hints.

---

## 3. Schema additions

All new models live in [production/models.py](../../config/production/models.py) (so existing `from production.models import ...` imports keep working). Barcode FKs added to [tracking/models.py](../../config/tracking/models.py).

### 3.1 `ProductSize` (new)

Per-Product size definitions. Each Product defines its own size chart — apparel (`S/M/L/XL`), numeric (`1/2/3/4`), or custom. Sizes are not global; same `code='M'` on T-Shirt and Kurta are different rows.

```python
class ProductSize(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sizes')
    code = models.SlugField(max_length=16)           # 'S', 'M', '1', '2'
    label = models.CharField(max_length=40)          # 'Small', 'Size 1'
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('product', 'code')]
        ordering = ['product', 'display_order', 'code']
```

**Why per-Product, not global?** User clarified: size sets vary per product type. T-Shirt uses S/M/L/XL, but a kids' garment may use 1/2/3/4. Global size library would force fake "Size 1" and "Small" coexistence and make admin UX brittle.

### 3.2 `CuttingPatternVerification` (new)

One row per `ProductPatternAssignment` that the cutting master has verified on this Adda.

```python
class CuttingPatternVerification(TimeStampedModel):
    record = models.ForeignKey(CuttingPatternRecord, on_delete=models.CASCADE, related_name='verifications')
    assignment = models.ForeignKey(ProductPatternAssignment, on_delete=models.PROTECT, related_name='+')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    verified_at = models.DateTimeField(auto_now_add=True)
    photo = models.ForeignKey(CuttingPatternPhoto, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = [('record', 'assignment')]
```

`photo` is optional pointer to a `CuttingPatternPhoto` already uploaded — proves *which* photo demonstrates *which* pattern. Photo upload itself stays generic; verification links it to the assignment.

### 3.3 `CuttingPatternSizeAllocation` (new)

Pattern designer enters proportion per size at Pattern stage. Sum across one record's rows must = 100. Cutting stage reads these to pre-fill the suggested breakup.

```python
class CuttingPatternSizeAllocation(TimeStampedModel):
    record = models.ForeignKey(CuttingPatternRecord, on_delete=models.CASCADE, related_name='size_allocations')
    size = models.ForeignKey(ProductSize, on_delete=models.PROTECT, related_name='+')
    proportion_pct = models.PositiveSmallIntegerField()    # 0..100, sum per record = 100

    class Meta:
        unique_together = [('record', 'size')]
```

Service validation enforces sum=100 at `complete_pattern_stage()`. Drafts may be unbalanced.

### 3.4 `CuttingPatternRecord` extension

```python
# add to existing CuttingPatternRecord
# sizes_in_batch is derived from CuttingPatternSizeAllocation rows — no separate M2M needed.
# (i.e. selecting a size = inserting an allocation row with proportion_pct > 0)
```

No M2M needed; allocation rows *are* the sizes-in-batch list. Render in UI as: "click a size to add an allocation row with 0%, then enter proportion."

### 3.5 `CuttingPieceBreakup` (new)

One row per unique (size, color, pattern) combination produced by the cutting master.

```python
class CuttingPieceBreakup(TimeStampedModel):
    cutting_record = models.ForeignKey(CuttingRecord, on_delete=models.CASCADE, related_name='breakup')
    size = models.ForeignKey(ProductSize, on_delete=models.PROTECT, related_name='+')
    color = models.ForeignKey('raw_materials.ClothColor', on_delete=models.PROTECT, related_name='+')
    pattern = models.ForeignKey(ProductPattern, on_delete=models.PROTECT, related_name='+')
    count = models.PositiveIntegerField()
    roll = models.ForeignKey('raw_materials.ClothRoll', on_delete=models.PROTECT, null=True, blank=True, related_name='+')

    class Meta:
        unique_together = [('cutting_record', 'size', 'color', 'pattern')]
        ordering = ['pattern__name', 'size__display_order', 'color__name']
```

`roll` is optional in case a single (size, color, pattern) draws from multiple rolls — usually fills if the breakup row corresponds 1:1 with a roll.

### 3.6 `CuttingRecord` adjustment

Existing model keeps `pieces_cut` field (denormalized total — sum of all `breakup.count`). Service writes it in `complete_cutting()` so downstream `BatchBarcode.objects.filter(adda=...).count()` matches `cutting_record.pieces_cut` for audit.

### 3.7 `BatchBarcode` extension (in [tracking/models.py](../../config/tracking/models.py))

```python
# add nullable FKs to existing BatchBarcode model
size = models.ForeignKey('production.ProductSize', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
color = models.ForeignKey('raw_materials.ClothColor', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
pattern = models.ForeignKey('production.ProductPattern', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
roll = models.ForeignKey('raw_materials.ClothRoll', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
```

`null=True` keeps existing rows valid (legacy `T-SHIRT-001-0042` barcodes have no metadata). Migration backfills nothing — historical Addas remain sparse, future Addas populated.

### 3.8 New `BatchBarcode.value` scheme

```
{ADDA_CODE}-{PATTERN_CODE}-{SIZE_CODE}-{COLOR_CODE}-{SEQ:04d}
```

Example: `TSHIRT001-FRONT-M-RED-0042`

Per-Adda uniqueness ensured by `(adda, piece_seq)` unique_together (existing). `value` stays unique globally.

---

## 4. Service contracts

### 4.1 [`cutting_pattern_service.py`](../../config/production/services/cutting_pattern_service.py) — additions

```python
def verify_pattern(*, record, assignment, photo=None, note='', user) -> CuttingPatternVerification: ...
def unverify_pattern(*, record, assignment, user) -> None: ...
def set_size_allocation(*, record, allocations: list[dict], user) -> None:
    """allocations = [{'size_id': int, 'proportion_pct': int}, ...] — full replace."""

def complete_pattern_stage(...):
    # NEW validation block:
    #   - all product.pattern_assignments have a matching verification row
    #   - at least one CuttingPatternSizeAllocation row exists
    #   - sum(allocations.proportion_pct) == 100
    #   - at least one photo overall (existing rule retained)
```

### 4.2 [`cutting_service.py`](../../config/production/services/cutting_service.py) — full rewrite

```python
def get_cutting_snapshot(adda) -> dict:
    """state ('absent'|'not_started'|'in_progress'|'completed'), breakup rows,
    totals_by_size, totals_by_color, totals_by_pattern, suggested_total."""

def get_suggested_breakup(adda) -> list[dict]:
    """Compute per-(size, color, pattern) suggested counts:
        for each pattern_assignment in product.pattern_assignments:
            pattern_total = lay_count * pattern_assignment.pieces_count
            for each allocation in cutting_pattern_record.size_allocations:
                size_share = pattern_total * allocation.proportion_pct / 100
                # color allocation: distribute across rolls used in layering
                for each color in distinct(layering.rolls_used.color):
                    color_share = size_share * (color_roll_count / total_rolls)
                    suggested[(pattern, allocation.size, color)] = round(color_share)
    Cutting master overrides; this is informational only.
    """

def start_cutting(*, adda, worker_ids, user) -> AddaStageRecord:
    """Create AddaStageRecord, assign workers. Idempotent. No CuttingRecord yet."""

def upsert_breakup_row(*, cutting_record, size, color, pattern, count, roll=None, user) -> CuttingPieceBreakup: ...
def delete_breakup_row(*, breakup_row, user) -> None: ...

def save_cutting_draft(*, adda, breakup_rows: list[dict], notes: str, user) -> CuttingRecord:
    """Lax validation; sets cutting_record.notes; does NOT complete or generate barcodes."""

def complete_cutting(*, adda, user) -> CuttingRecord:
    """Strict validation:
        - at least one breakup row
        - sum(breakup.count) > 0
        - every breakup.size in cutting_pattern_record.size_allocations
        - every breakup.pattern in product.pattern_assignments
        - every breakup.color in layering.rolls_used.color (denorm check)
    Then: stamp completed_at + completed_by, denormalize pieces_cut,
    call tracking.generate_for_cutting(cr), advance_to_next_stage."""

def reopen_cutting(*, adda, user) -> None:
    """Admin unlock. Refuses if any barcode has been scanned. Preserves breakup rows."""
```

### 4.3 [`tracking/services/barcode_service.py`](../../config/tracking/services/barcode_service.py) — rewrite

```python
@transaction.atomic
def generate_for_cutting(cutting_record) -> int:
    """Iterate CuttingPieceBreakup rows; for each row generate `count` barcodes
    with size/color/pattern/roll FKs and value format
    '{ADDA}-{PATTERN_CODE}-{SIZE_CODE}-{COLOR_CODE}-{SEQ:04d}'.
    piece_seq is global across the Adda (1..N), but value carries metadata."""
```

---

## 5. Views + URLs

### 5.1 Cutting Pattern (extend)

| URL name | View | Method | Purpose |
|---|---|---|---|
| `pattern-verify` | `PatternVerifyView` | POST | `verify_pattern()` from checklist row |
| `pattern-unverify` | `PatternUnverifyView` | POST | `unverify_pattern()` |
| `pattern-set-sizes` | `PatternSetSizesView` | POST | full replace of size allocations |

### 5.2 Cutting (replace skeleton)

| URL name | View | Method | Purpose |
|---|---|---|---|
| `cutting-workspace` | `CuttingWorkspaceView` | GET | full-page workspace (mirrors `pattern_workspace.html`) |
| `cutting-start` | `CuttingStartView` | POST | manager assigns workers |
| `cutting-breakup-save` | `CuttingBreakupSaveView` | POST | upsert one breakup row |
| `cutting-breakup-delete` | `CuttingBreakupDeleteView` | POST | delete row |
| `cutting-draft` | `CuttingDraftView` | POST | save notes + bulk row sync (no advance) |
| `cutting-complete` | `CuttingCompleteView` | POST | strict-validate + generate barcodes + advance |
| `cutting-reopen` | `CuttingReopenView` | POST | admin unlock |

All views inherit `ProductionRoleMixin` (PRODUCTION_ROLES gate). Per-action skill checks inside service layer (e.g. cutting requires `cutting_master` skill OR `MANAGEMENT_ROLES`).

---

## 6. Templates

### 6.1 Cutting Pattern panel — additions to [_stage_panel_cutting_pattern.html](../../config/production/templates/production/_stage_panel_cutting_pattern.html)

- **Section 02 — Pattern Verification**: per-`ProductPatternAssignment` row with ✓/✗ toggle, "linked photo" picker (existing photos as chips), "verified by + at" audit stamp.
- **Section 03 — Sizes in Batch + Proportions**: chip picker backed by `product.sizes.filter(is_active=True)`. Selected chip expands to inline percent input. Live total badge (red when ≠ 100%).

### 6.2 New `cutting_workspace.html` + `_stage_panel_cutting.html` rewrite

Layout mirrors `pattern_workspace.html` + `layering_workspace.html`:

- Hero strip (Adda code, product, stage label).
- Section 01 — Workers (start panel; same UX as Layering).
- Section 02 — Suggested vs Actual breakup table. Header columns: Pattern · Size · Color · Suggested · Actual. Inline-editable Actual cell.
- Section 03 — Notes textarea.
- Sticky bottom bar: `Save Draft` (ghost) + `Complete → Generate Barcodes` (primary, disabled until validation green).

### 6.3 Barcode list/print templates

Add size/color/pattern columns. QR payload unchanged (still `/tracking/scan/{value}/`), but landing page renders rich metadata from FKs.

---

## 7. Validation matrix

### 7.1 Cutting Pattern — `complete_pattern_stage()`

| Rule | Behavior |
|---|---|
| All `product.pattern_assignments` have verification rows | refuse with `"X of Y patterns verified — verify all before completing"` |
| ≥1 size allocation row | refuse with `"select at least one size for this batch"` |
| Sum of `proportion_pct` = 100 | refuse with `"size proportions sum to {n}%, must be 100%"` |
| ≥1 photo overall (existing) | retained |

### 7.2 Cutting — `complete_cutting()`

| Rule | Behavior |
|---|---|
| ≥1 breakup row | refuse with `"add at least one piece breakup row"` |
| Σ count > 0 | refuse with `"total piece count must be > 0"` |
| Every breakup.size ∈ pattern record's allocations | refuse with `"size {code} not in batch size set"` |
| Every breakup.pattern ∈ product.pattern_assignments | refuse with `"pattern {name} not assigned to this product"` |
| Every breakup.color ∈ layering rolls_used colors | refuse with `"color {name} not in layered rolls"` |

### 7.3 Reopen guards

- `reopen_pattern_stage` (existing): refuses if cutting stage started (already implemented).
- `reopen_cutting` (new): refuses if any `BatchBarcode.last_scanned_at is not None` for this Adda.

---

## 8. Migration plan

Single migration `production/migrations/0012_cutting_overhaul.py` + `tracking/migrations/0005_barcode_metadata.py`:

1. **production 0012**: create `ProductSize`, `CuttingPatternVerification`, `CuttingPatternSizeAllocation`, `CuttingPieceBreakup`.
2. **tracking 0005**: add 4 nullable FK columns to `BatchBarcode`.

Both no-data migrations. Existing T-SHIRT-001 records keep working (their barcodes have null FKs — list view shows "—" for missing metadata).

Run order matters: `production 0012` before `tracking 0005` (tracking FKs point at production).

---

## 9. Test matrix

New file `production/tests/test_cutting_pattern_validation.py`:
- ✘ refuse complete when one assignment unverified
- ✘ refuse complete when 0 size allocations
- ✘ refuse complete when allocation sum ≠ 100
- ✔ happy path — full pattern + all sizes balanced

New file `production/tests/test_cutting_workflow.py`:
- ✔ `get_suggested_breakup()` matches `lay_count × pieces × pct`
- ✘ refuse complete with empty breakup
- ✘ refuse complete with size outside allocations
- ✔ happy path → barcodes generated with correct FKs
- ✘ reopen blocked when barcode scanned

Update `tracking/tests/test_barcode_service.py`:
- ✔ barcode values follow new format
- ✔ size/color/pattern FKs populated when breakup rows have them
- ✔ legacy generator path still works for any Adda without breakup (regression safety — TBD whether to keep)

Target: existing 74/74 stays green; ~15 new tests on top.

---

## 10. RBAC

No new roles needed. Existing skills + roles wired through `Stage.access_by_skill` + `Stage.access_by_role`:

| Action | Allowed |
|---|---|
| Verify pattern | `cutting_master` skill OR MANAGEMENT_ROLES |
| Set size allocation | `cutting_master` skill (acting as designer) OR MANAGEMENT_ROLES |
| Start cutting | MANAGEMENT_ROLES |
| Save cutting draft | `cutting_master` skill OR MANAGEMENT_ROLES |
| Complete cutting | `cutting_master_helper` skill OR `ROLE_SUPER_ADMIN` (mirror current pattern-complete gate strictness) |
| Reopen cutting | MANAGEMENT_ROLES |

---

## 11. Phased PR plan

| PR | Scope | Files | Risk |
|---|---|---|---|
| **PR1 — Schema foundation** | All new models + BatchBarcode FKs + migrations. No service logic, no UI. Admin-registers new models for inspection. | production/models.py, tracking/models.py, 2 migrations, production/admin.py, tracking/admin.py | Low |
| **PR2 — Cutting Pattern validation** | `verify_pattern`/`unverify_pattern`/`set_size_allocation` services + views + template sections + tests. `complete_pattern_stage` new validation rules. | cutting_pattern_service.py, pattern_stage_views.py, _stage_panel_cutting_pattern.html, urls.py, forms/cutting_pattern.py (new), test file | Medium — touches existing happy path |
| **PR3 — Cutting workspace + draft** | Full cutting_service rewrite + workspace template + draft/complete flow. Skeleton complete-form path deprecated. | cutting_service.py, stage_views.py, _stage_panel_cutting.html, cutting_workspace.html (new), forms/cutting.py, urls.py, test file | High — replaces existing complete_cutting |
| **PR4 — Barcode metadata** | `generate_for_cutting` rewrite, value format change, list/print template metadata columns. | barcode_service.py, tracking/templates/, test_barcode_service.py updates | Medium |
| **PR5 — ProductSize admin UI** | Inline formset for ProductSize on product create/edit. Validation: ≥1 active size required before Adda creation if product has any patterns assigned. | product_forms.py, product templates, test_product_form.py | Low |

**Order matters**: PR1 → PR2 → PR3 → PR4 → PR5. Each merges to main, runs `manage.py test`, gates the next.

---

## 12. Out of scope

Spec §17 future scope, restated here:

- Machine tracking (which sewing machine produced piece X)
- Worker scanning (per-piece worker assignment on cut)
- Manufacturing analytics / real-time dashboards
- Movement tracking (piece transitions between stages post-cutting)
- Advanced scan history beyond `last_scanned_at`

These remain in the [TRACKING.md](TRACKING.md) future-work section. Foundation for them lives in the new BatchBarcode FKs — once piece has size+color+pattern+roll, machine/worker tracking is "just another FK" later.

---

## 13. Open questions (to resolve before code starts)

1. **Color picker in cutting breakup** — pull from `layering.rolls_used.color.distinct()` or open all `ClothColor` rows? **Recommended:** restrict to layering rolls' colors (matches validation rule).
2. **Roll FK on breakup row** — optional or required? **Recommended:** optional. Required would force cutting master to pick a roll for each (size,color,pattern) row, which is operationally noisy when a row spans rolls.
3. **Suggested-breakup pre-fill UX** — pre-populate Actual column with suggested values, or leave blank + show suggestion in a "hint" cell? **Recommended:** pre-populate; cutting master deletes/adjusts. Less data entry on the happy path.
4. **`CuttingPieceBreakup.count` upper bound** — sanity-check vs suggested total (warn if actual > suggested × 1.5)? **Recommended:** soft warn in UI, no hard refuse. Cutting masters know better than the formula.
5. **Legacy Adda barcode display** — show "—" for missing FKs, or backfill from CuttingRecord context (since old Addas have no breakup rows)? **Recommended:** show "—". Backfill is data-archeology busywork.

These will get resolved in PR review or quick Slack check before each PR opens.

---

## 14. Architectural rules retained

- Service layer owns all multi-row writes (CLAUDE.md rule 4). Views call services. No signals.
- `@transaction.atomic` on every write service.
- Audit via `tracking.history_service.log_*` where applicable.
- No raw `is_superuser` checks — go through `permission_service`.
- Hinglish beginner comments on new files, naming Django/PG primitives on first touch.
- Templates: BEM-lite classes, page-scoped CSS in `{% block extra_head %}`, reuse `.panel` / `.field` / `.sf-*` from [UI_COMPONENTS.md](../../UI_COMPONENTS.md).
- Mobile-responsive: stage workspace tables get `data-label` on cells for stacked mobile view.

---

**Next step:** review this doc → approve schema (§3) → cut PR1 branch.

---

# Appendix A — PR6 to PR13 (Schema + Flow Evolution)

After the initial 5-PR plan landed, the cutting flow went through 7 more iterations driven by user feedback. This appendix captures the final state.

## A.1 Schema additions beyond the original plan

```
CuttingBundle (new — PR7+PR8)
    cutting_record FK            (one bundle per (cutting_record, size))
    size FK
    total_pieces                  (denormalized from items)
    bundle_number                 (optional label, e.g. "Lot-A")
    unique_together (cutting_record, size)

CuttingBundleItem (new — PR8+PR10)
    bundle FK
    pattern FK
    color FK
    count
    source_breakup FK → CuttingPieceBreakup   (PR10 — for restore-on-delete)
    unique_together (bundle, pattern, color)

CuttingPieceBreakup (extended — PR10)
    + consumed_count              (denormalized)
    + available_count property    (count - consumed_count)

BarcodeBatch (new — PR6, extended PR11)
    adda FK, product FK
    bundle FK → CuttingBundle     (PR11 — null for legacy NIKKAR)
    size FK, color FK             (null for legacy)
    start_seq, end_seq, total_pieces
    unique_together (adda, color, size)

BatchBarcode (existing, extended PR6)
    batch FK → BarcodeBatch       (lazy population on scan)
    Per-piece scan state created on first scan only.
```

## A.2 Final service contracts (cutting_service.py)

| Service | Path |
|---|---|
| `start_cutting` | Manager assigns workers |
| `upsert_breakup_row` | Section 02 inventory edit |
| `delete_breakup_row` | Section 02 row remove (locked if consumed) |
| `create_bundle` | Bundle header only |
| `create_bundle_with_pieces` (**PR12**) | Atomic header + initial items |
| `add_pieces_to_bundle` (**PR10**) | Multi-select consume from inventory |
| `add_item_to_bundle` (PR9) | Single freeform item |
| `add_bundle_item` (PR8) | Auto-bundle + item shortcut |
| `delete_bundle_item` | Restore consumed_count |
| `delete_bundle` | Restore all consumed_counts |
| `save_cutting_draft` | Notes only |
| `complete_cutting` | Workspace (bundle-driven) or legacy (pieces_cut int) |
| `reopen_cutting` | Admin unlock (refused if scanned) |
| `get_cutting_snapshot` | UI context (state, breakup, bundles, totals, color_summary) |
| `get_suggested_breakup` | Formula-based pre-fill |
| `preview_barcode_batches` (**PR13**) | Pre-completion barcode batch preview |

## A.3 Final UI section layout (Cutting workspace)

```
Section 01 — Assigned Workers
    Manager assigns; chip display

Section 02 — Suggested Piece Breakup (Inventory)
    Pattern · Size · Color · Count · Consumed · Available · Action
    Edit form: multi-row Pattern × Size × Color × Count editor

Section 03 — Actual Cutting Bundles
    [+ Create New Bundle]
        Size + Bundle Number + Multi-select Pattern×Color×Take picker
        → atomic header + items in one tx (PR12)

    Per bundle card:
        Header: [Size L] · Lot-A · 45 pieces · [Delete Bundle]
        Pattern chips: [Front (20)] [Back (15)] [Sleeve (10)]
        Items table: Pattern × Color × Count + Remove
        Color totals pills: [Black × 25] [Red × 20]
        Add more pieces form: multi-select from remaining inventory

Section 04 — Notes (Save Draft)

Section 05 — Mark Cutting Complete & Generate Barcodes
    Barcode Generation Preview (PR13):
        Bundle · Color · Pieces · Start · End
        Shows exactly which ranges will be created
    Confirm → generate_for_cutting → advance stage
```

## A.4 Validation chain at complete_cutting

1. AddaStageRecord exists for cutting stage
2. CuttingRecord exists
3. ≥1 CuttingBundleItem across all bundles
4. Σ items.count > 0
5. Every item.bundle.size ∈ pattern stage size allocations (if pattern stage exists)
6. Every item.pattern ∈ product.pattern_assignments
7. Every item.color ∈ layering.rolls_used.colors

All fail-loud with specific user-facing messages.

## A.5 Resolved open questions (§13 above)

| Q | Resolution |
|---|---|
| Color picker scope | Restricted to layered roll colors |
| Roll FK required | Optional |
| Suggested-breakup pre-fill | Editable rows pre-populated |
| Count upper bound | No hard limit; user verifies |
| Legacy barcode display | Show "—" for null FKs (no backfill) |

## A.6 Bundle-driven barcode flow

```
CuttingPieceBreakup (Section 02 inventory)
    consumed_count tracks pieces moved into bundles

         ↓ (multi-select via add_pieces_to_bundle)

CuttingBundle → CuttingBundleItem rows
    bundle.total_pieces = SUM(items.count)

         ↓ (complete_cutting → generate_for_cutting)

BarcodeBatch ranges (one per bundle × color)
    aggregated by (size, color) across all items in that bundle
    start_seq..end_seq inside Adda's global sequence

         ↓ (lazy on scan)

BatchBarcode per-piece scan state
    populated with size, color, pattern, roll FKs from batch lookup
```

## A.7 Final test count

127 passing tests covering:
- Pattern verification (16 in PR2)
- Cutting workspace lifecycle (18 in PR3, extended in PR7-PR12)
- Bundle creation + consumption (5+5+5+1+4 across PR9-PR12)
- Barcode range allocation (4 across PR6-PR11)
- Legacy back-compat path (golden path + barcode service tests)

