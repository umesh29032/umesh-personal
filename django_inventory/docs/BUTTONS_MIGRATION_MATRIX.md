# BUTTONS MIGRATION MATRIX

> **Status:** Per-family migration matrix — **DESIGN ONLY. NO CODE. NO CSS. NO token
> consumption. NO Stage 0b. NO commits.** The file-level execution map for Foundation 2.
> Evidence: [BUTTONS_AUDIT_REPORT.md](BUTTONS_AUDIT_REPORT.md) · Contract: [BUTTONS_FOUNDATION_SPEC.md](BUTTONS_FOUNDATION_SPEC.md).
> Owner approved **Option 1** (money geometry → `.btn .btn-X .btn-lg`, visually identical).
> **Owner:** Umesh · **Created:** 2026-06-16. File lists MEASURED 2026-06-16.

## 0. Count corrections (honesty)
- Inline-mini files = **7** (not 8 as first stated).
- Inline-styled `.btn` = **15 files / 31 occurrences** (31 = occurrences; 15 = files).
- Bare geometry-B buttons = **24 across 11 files** — and they are NOT only "money": forms
  (user_form, user_create, stage_form, product_flow, sidebar_access_list) also use geometry B.
  Family renamed **"Geometry-B / comfortable"** (not "money").

## 1. The touch reconciliation (important — read before the matrix)
Base `.btn` is **38px** today; `--touch-min` is **44px**. Tokenizing radius/font is
value-identical (inert), but **growing 38→44 is a VISUAL change** (taller buttons). So:
- **B-1 (tokenize) does NOT change min-height** — stays 38 → Visual NO.
- The **38→44 touch growth is a deliberate, owner-signed-off visual step (B-6)**, batched
  with `.action-link`/`.action-icon` touch enforcement. Not smuggled into the inert pass.

## 2. Stage legend
**B-1** tokenize base `.btn` (inert) · **B-2** define `.btn-sm`+`.btn-lg` (additive) ·
**B-3** repoint 24 bare→`.btn …btn-lg`, kill `:not(.btn)` (zero-visual, prove identical) ·
**B-4** kill inline geometry (7 mini + 15 inline + 2 `.btn-mini`)→`.btn-sm`/`.btn-lg` ·
**B-5** adopt `.btn` on escaped raw buttons · **B-6** intended touch growth (≥44) + focus ring.

---

## 3. MATRIX

### Family 1 — Standard `.btn` + modifier  (86 templates, dominant path)
Variants: `.btn-primary` (45f/81) · `.btn-ghost` (63f/122) · `.btn-copper` w/ base · `.btn-danger` (7f/15) · `.btn-filter` (1f/2) · `.btn-clear` (8f/12).
| Field | Value |
|---|---|
| File | all 86 `.btn` templates (no per-file edit — inherit base) |
| Current class | `class="btn btn-primary"` etc. |
| Target class | **unchanged** (`btn btn-primary`) |
| Current geom | A: r6 / fs12 / fw700 / UPPERCASE / mh38 |
| Target geom | A, **tokenized** (`--radius-sm`/`--fs-sm`/`--fw-bold`); mh38 unchanged |
| Visual? | **NO** (value-identical) · focus-visible ring = keyboard-focus-only a11y add |
| Touch impact | none in B-1 (38px); **+6px → 44 deferred to B-6 (visual, owner sign-off)** |
| Risk | LOW |
| Stage | **B-1** (+ B-6 for touch) |
| Rollback | `git revert` base.html (single block) |

### Family 2 — Geometry-B "comfortable" (bare modifiers) — 24 buttons / 11 files
| File | bare buttons |
|---|---|
| expense/adda_settlement_detail.html | 7 |
| production/stage_form.html · production/adda_report_review.html | 2 · 2 |
| expense/worker_profile_form.html · expense/settlement_form.html · expense/advance_form.html | 2 · 2 · 2 |
| accounts/user_form.html · accounts/user_create.html | 2 · 2 |
| expense/adda_settlement_list.html · production/product_flow.html · templates/inventory/sidebar_access_list.html | 1 · 1 · 1 |

| Field | Value |
|---|---|
| Current class | `class="btn-copper"` / `"btn-ghost"` / `"btn-danger"` (BARE, no `.btn`) |
| Target class | `class="btn btn-copper btn-lg"` / `"btn btn-ghost btn-lg"` / `"btn btn-danger btn-lg"` |
| Current geom | B: r10 / fs13 / fw700 / not-uppercase / mh40 (via `:not(.btn)`) |
| Target geom | B reproduced exactly by `.btn-lg` (r10/fs13/mh40, not-uppercase) |
| Visual? | **NO** — must PROVE pixel-identical (computed-style fingerprint) |
| Touch impact | none (40px both) |
| Risk | **MED (hotspot)** — adding `.btn` flips to A unless `.btn-lg` exactly equals B (define in B-2 first) |
| Stage | **B-2** (define `.btn-lg`) → **B-3** (repoint 11 files, then delete `:not(.btn)`) |
| Rollback | restore bare classes + `:not(.btn)` block (per-file `git checkout`) |

### Family 3 — Inline-mini (`padding:4px 10px`) — 7 files
product_list · _stage_panel_cutting · _stage_panel_cutting_pattern · master_list · roll_list · role_list · export_list
| Field | Value |
|---|---|
| Current class | `class="btn btn-ghost" style="padding:4px 10px;font-size:12px"` |
| Target class | `class="btn btn-ghost btn-sm"` (inline removed) |
| Current geom | ad-hoc ~24px tall, fs12 |
| Target geom | `.btn-sm` (dense; `--fs-xs`; **mh44 on ≤sm**) |
| Visual? | desktop ~identical · **mobile: touch grows to 44 (INTENDED)** |
| Touch impact | ↑ improves (sub-24 → 44 on mobile) |
| Risk | MED (row-action density; verify table layout not pushed) |
| Stage | **B-4** |
| Rollback | per-file `git checkout` (restores inline style) |

### Family 4 — Inline-styled `.btn` (geometry overrides) — 15 files / 31
user_confirm_delete · user_list · product_list · _stage_panel_barcode_gen · _stage_panel_cutting · _stage_panel_cutting_pattern · master_list · roll_list · storefront category_form/category_list/product_form/product_list · role_list · user_dashboard · export_list
| Field | Value |
|---|---|
| Current class | `class="btn …" style="padding…/font-size…/border-radius…"` |
| Target class | `class="btn …"` (+ `.btn-sm`/`.btn-lg` where the inline matched that size); inline removed |
| Current geom | per-file inline override |
| Target geom | nearest canonical size (default/sm/lg) |
| Visual? | **per-file verify** — most NO/minor; any that don't map to a size = flag (off-grid) |
| Touch impact | varies; net ↑ where it was dense |
| Risk | MED (wide; mechanical) — one file at a time, browser-checked |
| Stage | **B-4** |
| Rollback | per-file `git checkout` |

### Family 5 — `.btn-mini` page-scoped — 2 files
production/product_sizes_edit.html · production/product_patterns_edit.html
| Field | Value |
|---|---|
| Current class | `class="btn-mini"` / `.btn-mini.danger` (page CSS, duplicated) |
| Target class | `class="btn btn-sm"` / `btn btn-sm btn-danger` |
| Current geom | 6×10 / r8 / fs12 · **mh44 @≤sm (already touch-safe)** |
| Target geom | `.btn-sm` (preserve the mh44@sm behavior) |
| Visual? | minor (verify inline-edit table clip — these are clip-sensitive pages) |
| Touch impact | preserved (44@sm) |
| Risk | MED (PA-15 inline-edit clip history) |
| Stage | **B-4** (delete page `.btn-mini` CSS only AFTER repoint proven) |
| Rollback | per-file `git checkout` (restores `.btn-mini` markup + CSS) |

### Family 6 — Raw `<button>` (18, no `.btn`)
**6a. Escaped REAL buttons → adopt `.btn`:**
| File | Current class | Target class | Visual? | Touch | Risk | Stage | Rollback |
|---|---|---|---|---|---|---|---|
| production/_stage_panel_layering.html | `lybtn lybtn-primary` (3) / `lybtn lybtn-ghost` (3) | `btn btn-primary` / `btn btn-ghost` | small (verify) | ↑ | LOW | **B-5** | per-file checkout + keep `.lybtn` CSS until proven, then delete |
| production/adda_detail.html | `next-up-action` · `so-tile-jump` | `btn btn-primary`/`btn btn-ghost` (as fits) | small (verify) | ↑ | LOW | **B-5** | per-file checkout |

**6b. Legit non-`.btn` controls → KEEP (document, NO migration):**
| File | Class | Why keep | Touch action |
|---|---|---|---|
| accounts/base.html | `theme-toggle` · `logout-link` | chrome controls | verify ≥44 (B-6 if short) |
| public_home.html | `nav-toggle` · `mobile-menu-close` | nav chrome | verify ≥44 |
| production/_stage_panel_layering.html | `roll-x` | icon remove affordance | verify ≥44 |
| raw_materials/roll_bulk_form.html | `remove-row` | dynamic-row delete | verify ≥44 |
| production/_worker_report_body.html | `line-remove` | dynamic-line delete | verify ≥44 |
| storefront/widgets/croppable_image.html | `cw-crop-cancel` | modal-private (Family F) | no change |
| Visual? | **NO** (kept as-is) | | Stage = doc-only / B-6 touch check |

### Family 7 — `.action-link` (text row-action) — 7 files / 26 (+danger 6f/7)
| Field | Value |
|---|---|
| File | skill_list, user_list, usertype_list, etc. (7) |
| Current class | `class="action-link"` / `action-link-danger` |
| Target class | **unchanged** (`action-link`) |
| Current geom | 4×10 / r4 / fs12 · **~23px (browser-verified)** |
| Target geom | same chrome + **≥44px tap area on ≤sm** |
| Visual? | **mobile only — INTENDED touch growth** (desktop unchanged) |
| Touch impact | ↑ (23 → 44 on mobile) |
| Risk | LOW |
| Stage | **B-6** (owner sign-off) |
| Rollback | `git revert` base.html |

### Family 8 — `.action-icon` (icon action) — 1 file / 5
| Field | Value |
|---|---|
| Current class | `class="action-icon"` / `action-icon-danger` |
| Target class | **unchanged** (`action-icon`) + `aria-label` if missing |
| Current geom | 32×32 / r6 / fs14 |
| Target geom | same + **≥44px on ≤sm** |
| Visual? | **mobile only — INTENDED touch growth** |
| Touch impact | ↑ (32 → 44 on mobile) |
| Risk | LOW |
| Stage | **B-6** |
| Rollback | `git revert` base.html |

---

## 4. Stage rollup
| Stage | Families touched | Files | Visual | Gate |
|---|---|---|---|---|
| **B-1** | F1 base tokenize | base.html | NO (inert) | computed-style identical, 6 pages | ✅ DONE `ff1d5702` (incl. prereq 0a token defs) |
| **B-2** | F2 define `.btn-lg` ONLY | base.html | additive/inert | `.btn-lg` == geometry B exactly (verified byte-identical) |
| **B-3** | F2 repoint bare→`.btn …btn-lg`, kill `:not(.btn)` | 11 | **NO** (proven byte-identical) | ✅ DONE `138dafab` (24 migrated; +danger-hover; old==new all pages; 0 bare; 0 live :not(.btn)) |
| **B-4** | F3+F4+F5 kill inline + `.btn-mini` | 7+15+2 (≈22 distinct) | desktop ~NO, mobile touch↑ | per-file browser check, no clip/overflow |
| **B-5** | F6a adopt `.btn` on raw | 2 | small (verify) | layering + adda_detail shown |
| **B-6** | F1 38→44 · F7 · F8 · F6b touch | base.html + verify | **YES (intended a11y)** | owner sign-off; ≥44 confirmed |

**Order:** B-1 → B-2 → B-3 (hotspot, pixel-proof) → B-4 → B-5 → B-6 (intended-visual last).
Each: implement → browser-verify 320/375/390/414/1280 → STOP → owner review → ONE commit.
GET-only on money pages; never reopen golden ₹225. Backend untouched (0 `.py`, 0 submit inputs).

---

**No code. No CSS. No token consumption. No Stage 0b. No commits.** On approval, Foundation 2
begins at **B-1**, one stage at a time, browser-verified, STOP after each.
