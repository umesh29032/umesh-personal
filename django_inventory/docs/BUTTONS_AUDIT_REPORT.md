---
id: docs-buttons-audit-report
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# BUTTONS AUDIT REPORT

> **Status:** Evidence/inventory — **DESIGN ONLY. NO CODE. NO CSS. NO token consumption. NO commits.**
> Full button inventory for the Buttons Foundation. Counts MEASURED 2026-06-16 (`config/**/*.html`)
> + base.html CSS read directly. Heights: browser-verified where noted, else computed-from-CSS box.
> Companion: [BUTTONS_FOUNDATION_SPEC.md](BUTTONS_FOUNDATION_SPEC.md) · context: [SPEC](DESIGN_SYSTEM_SPEC.md) §2 · [CATALOG](UI_COMPONENTS_CATALOG.md) #1.
> **Owner:** Umesh · **Created:** 2026-06-16.

## 0. Headline
The project has **8 distinct button systems** (2 canonical geometries in base.html + 6
divergent/ad-hoc owners). One `.btn` class is NOT the single source today — geometry,
ownership, and touch-size all fragment. **No `<input type=submit>` anywhere (0)** — every
submit is a `<button>`/`<a>`, so consolidation is class-only.

---

## 1. Full inventory of every button variant

### 1a. Canonical — base.html `.btn` + modifiers (GEOMETRY A)
Base `.btn` (base.html ~1185): `display:inline-flex; gap:7px; padding:9px 18px;
border-radius:6px; font-size:12px; font-weight:700; letter-spacing:0.1em; text-transform:
uppercase; min-height:38px; border:none; :active scale(0.98); svg 14px.`

| Variant | Style | Files | Occurrences |
|---|---|---|---|
| `.btn-primary` | copper bg / #fff | 45 | 81 |
| `.btn-copper` | copper bg / white | 13 | 27 |
| `.btn-ghost` | transparent / 1.5px cream-3 border / stone | 63 | 122 |
| `.btn-danger` | #fee2e2 / #991b1b | 7 | 15 |
| `.btn-filter` | copper / #fff · padding 9×16 · fs 11 | 1 | 2 |
| `.btn-clear` | transparent / border · padding 9×14 · fs 11 | 8 | 12 |

### 1b. Canonical — base.html bare modifier (GEOMETRY B = the divergence)
base.html ~1615 `.btn-copper:not(.btn), .btn-danger:not(.btn), .btn-ghost:not(.btn)`:
**different geometry** — `padding:10px 18px; border-radius:10px; font-size:13px;
min-height:40px; NOT uppercase.` Used by the "money family" markup with a BARE modifier
(no `.btn` base). danger=#b03434/#fff; ghost=transparent/border-card/ink/fw600.
- **24 bare usages:** `class="btn-copper"` ×12 · `class="btn-ghost"` ×11 · `class="btn-danger"` ×1.
→ **Same class names render two different shapes depending on whether `.btn` is present.**

### 1c. Page-scoped / ad-hoc systems (NOT base.html)
| System | Owner | Geometry | Reach |
|---|---|---|---|
| `.btn-mini` | page CSS in `product_sizes_edit.html` + `product_patterns_edit.html` (duplicated) | padding 6×10 · r8 · fs12 · **min-height:44px @≤sm** | 2 files / 11 uses |
| `.lybtn` / `.lybtn-primary` / `.lybtn-ghost` | page-scoped (layering) | own naming, own geometry | 6 raw `<button>` |
| inline `padding:4px 10px` mini-button | **inline `style=` per template** | ad-hoc row-action shrink | **8 files** (export_list, roll_list, master_list, product_list, role_list, _stage_panel_cutting, _stage_panel_cutting_pattern) |

---

## 2. All `.btn` usages and non-`.btn` usages
- **`.btn`-bearing templates:** 86.
- **`.btn` + modifier (Geometry A):** the dominant path (primary/ghost/copper/danger/filter/clear above).
- **Non-`.btn` (bare modifier, Geometry B):** **24** (`btn-copper` 12 · `btn-ghost` 11 · `btn-danger` 1) — money family, the `:not(.btn)` shape.
- **Non-`.btn` raw `<button>` (no btn class at all):** **18** — see §6.

## 3. Inline button styles
- **31** elements = `class="…btn…"` **with their own `style=`** overriding padding/font-size/
  border-radius (geometry forked inline).
- **8 files** use the `padding:4px 10px` inline mini-button pattern on row actions (bypasses
  both `.btn-sm` (doesn't exist yet) and `.action-link`).
- These inline overrides are the single biggest "change-once breaks" — geometry lives in markup.

## 4. Mini buttons
Three competing "small button" idioms, none shared:
1. **inline `padding:4px 10px; font-size:12px`** on `.btn-ghost` (8 files, row actions).
2. **`.btn-mini`** page-scoped, duplicated in 2 edit pages (6×10/r8; **correctly bumps to
   min-height:44px on mobile** — the only touch-safe small button today).
3. **`.action-link`** (4×10/r4/fs12) — see §5.
→ No canonical small/dense button. `.btn-sm` (SPEC §2) does not exist yet.

## 5. Action links
`.action-link` (base.html ~1448): `inline-flex; gap:5px; padding:4px 10px; border-radius:4px;
font-size:12px; font-weight:600; color:stone; svg 13px` + `.action-link-danger` (red).
- **7 files / 26 uses** (`action-link`); `action-link-danger` 6 files / 7 uses.
- Text-style table-row actions. **Height ≈23px (browser-verified in prior audit) → far below 44px touch.**

## 6. Icon buttons
- **`.action-icon`** (base.html ~2193): `width:32px; height:32px; border-radius:6px; fs14`
  + `.action-icon-danger`. **1 file / 5 uses. 32px square → below 44px touch.**
- **Raw `<button>` icon/functional controls (18 total, no btn class):** `lybtn`×6,
  `remove-row`/`line-remove`×4 (dynamic-row delete), `cw-crop-cancel`×2 (crop modal),
  `theme-toggle`, `so-tile-jump`, `roll-x`, `next-up-action`, `nav-toggle`,
  `mobile-menu-close`, `logout-link`.
  - **Legit non-button controls** (keep as-is, documented): `theme-toggle`, `nav-toggle`,
    `mobile-menu-close`, `roll-x`/`remove-row`/`line-remove` (icon affordances),
    `cw-crop-cancel` (modal-private), `logout-link`.
  - **Real buttons that escaped the system** (candidates to adopt `.btn`): `lybtn*` (6),
    `next-up-action`, `so-tile-jump`.

## 7. Mobile touch sizes (target ≥44px = `--touch-min`)
| Control | Height | Source | ≥44? |
|---|---|---|---|
| `.btn` | **38px** | browser-verified (Stage 0a fingerprint) | ❌ (full-width @≤768 via `.page-header>.btn`/`.form-actions .btn`, but height still 38) |
| `.btn-*:not(.btn)` (money) | 40px (`min-height:40`) | CSS | ❌ |
| `.action-link` | **~23px** | browser-verified (prior audit) | ❌❌ |
| `.action-icon` | 32px | CSS | ❌ |
| inline mini (`4px 10px`) | ~24px | CSS box | ❌❌ |
| `.btn-mini` | 6×10 desktop → **44px @≤sm** | CSS | ✅ (only one) |
- **Touch debt is systemic:** every default button/action is sub-44px. Only the page-scoped
  `.btn-mini` mobile rule meets the target. (Enforcement = the Foundation, not Stage 0a.)

## 8. Ownership map
| Concern | Current owner(s) | State |
|---|---|---|
| Base button geometry A | base.html `.btn` | canonical |
| Money geometry B | base.html `:not(.btn)` hack | divergent (same names, 2nd shape) |
| Small/dense button | inline styles (8) + `.btn-mini` (2, dup) + `.action-link` | **fragmented, no owner** |
| Action link | base.html `.action-link` | canonical (but sub-44) |
| Icon button | base.html `.action-icon` + raw buttons | mixed |
| Layering buttons | page-scoped `.lybtn*` | separate system |
| Touch sizing | none (only `.btn-mini`@sm) | **no owner** |
→ **No single owner for "a button."** 8 systems; geometry leaks into markup (31 inline) and page CSS.

## 9. Shared-token dependency (post-Stage-0a tokens available, NOT yet consumed)
Buttons today hardcode every value. Target token mapping (values already match — inert repoint):
| Button property | Current literal | Token (Stage 0a, defined) |
|---|---|---|
| base radius | `6px` | `--radius-sm` (6px) |
| money geometry radius | `10px` | `--radius-md` (10px) |
| base font-size | `12px` | `--fs-sm` (12px) |
| filter/clear font-size | `11px` | `--fs-xs` (11px) |
| money font-size | `13px` | `--fs-base` (13px) |
| font-weight | `700` / `600` | `--fw-bold` / `--fw-semibold` |
| padding 9/18/16/14/10 | mix | `--space-*` (9,14,18 are off-grid → DEFER; 16=`--space-4`) |
| min-height target | `38/40/44` | `--touch-min` (44) / `--control-h` |
| focus ring | none consistent | `--shadow-focus` |
| colors | `--copper`/`#fee2e2`/`#991b1b`/`#b03434` | `--copper`/`--status-danger-*` (some raw hex → repoint) |
- **Off-grid note:** button padding (9px, 18px, 14px) is off the 4px grid → those literals are
  NOT repointed in the inert pass; they're rationalization candidates (visual, separate approval).

## 10. Migration impact (summary; full strategy in the SPEC)
- **Active edits:** unify the two geometries (resolve `:not(.btn)` → `.btn` + modifier) ·
  add `.btn-sm` · replace 8 inline mini-button files + 31 inline-styled btns · adopt `.btn`
  on the 9 escaped raw buttons (lybtn/next-up/so-tile) · fold `.btn-mini` (2) into `.btn-sm` ·
  enforce `--touch-min`.
- **Blast radius:** 86 `.btn` templates (most need no change) + 24 bare + 31 inline + 8 mini
  files + 2 btn-mini + 6 lybtn.
- **Risk hotspot:** the 24 bare `:not(.btn)` money buttons — changing their geometry IS a
  visual change (r10→r? , fs13→?) → must be a deliberate, browser-verified convergence, not
  a silent token swap.
- **Backend:** 0 `.py` (no submit inputs, all template/CSS).

---

**No code. No CSS. No token consumption. Evidence only.** Target contract + migration =
[BUTTONS_FOUNDATION_SPEC.md](BUTTONS_FOUNDATION_SPEC.md).
