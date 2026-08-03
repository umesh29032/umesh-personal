> **ARCHIVED 2026-07-13** — design-system working doc (era build). Live vocabulary: [UI_COMPONENTS.md](../../../UI_COMPONENTS.md); frozen reference: DESIGN_SYSTEM_SPEC + UI_COMPONENTS_CATALOG (KEEP, active). Kept for history (Phase-7 DOCCLEAN-D, D-OR-4).

# TOKEN MIGRATION SPEC — Foundation Zero

> **Status:** Migration specification — **DESIGN ONLY. NO CSS. NO `:root` CREATION. NO
> IMPLEMENTATION. NO COMMITS. NO TOKEN VALUES ADDED TO CODE.** This is the LAST
> architecture gate before Foundation 1 (Design Tokens) implementation.
> Companions: [ARCHITECTURE](FRONTEND_DESIGN_SYSTEM_ARCHITECTURE.md) · [ROADMAP](DESIGN_SYSTEM_IMPLEMENTATION_ROADMAP.md) ·
> [SPEC](DESIGN_SYSTEM_SPEC.md) · [CATALOG](UI_COMPONENTS_CATALOG.md).
> **Owner:** Umesh · **Created:** 2026-06-16. All literal values + counts MEASURED from
> `config/accounts/templates/accounts/base.html` (the `:root`/style sink) + `config/**/*.html`.

---

## 0. The inertness model (READ FIRST — this is what makes Foundation Zero safe)

Foundation Zero runs in **two sub-stages, each browser-verified, STOP after each:**

- **Stage 0a — DEFINE (additive, 100% inert, trivially provable):** add the new token
  variables to base.html `:root` (+ dark override). **Zero consumers repointed.** Nothing
  references them yet ⇒ rendered output is byte-identical. The "prove inert" baseline.
- **Stage 0b — REPOINT (value-identical swaps):** replace literals with `var(--token)`
  **only where the literal EXACTLY equals the token value.** Value-identical ⇒ pixel-identical.

### ⚠ The exact-match rule (the honest core of this spec)
Measured reality: the codebase is **not on a clean grid.** Font-weight IS clean
(400/500/600/700). But font-size, radius, and spacing carry many **off-grid literals**
(e.g. 15/17/26px sizes; 7/9px radii; 6/9/11/14/22px spacing). **Snapping an off-grid
literal to a scale step = a visual change** → violates "zero visual change."

Therefore Foundation Zero **migrates only literals that already equal a token value.**
**Off-grid/odd literals are NOT touched** — they are logged as candidates for a SEPARATE,
explicitly-approved "scale rationalization" step (which IS a visual change, out of
Foundation-Zero scope). This keeps Foundation Zero provably inert. Coverage is partial by
design; the deferred set is enumerated, never silently snapped.

**Colors / status / surface / shadow-card are ALREADY tokenized** (base.html `:root`).
Foundation Zero **ADDS the missing scales** (type · weight · radius · spacing · extra
shadows · z-index · touch · breakpoints) and documents the existing color layer. Repointing
hardcoded *hex* in templates happens in LATER foundations, not here.

---

## 1. Token enumeration (by group)

Columns: **Token · Current literal(s) · Existing locations/count · Proposed value
(= a current literal, inert) · Consumer foundations · Migration priority.**
Priority: **P0** (Foundation Zero exact-match) · **DEFER** (off-grid → future scale
rationalization, visual) · **LATER** (consumed by a later foundation, not F0).

### 1.1 Colors  — ✅ ALREADY TOKENS (document only; no new token)
| Token | Current value | Locations | Proposed | Consumers | Priority |
|---|---|---|---|---|---|
| `--ink` | `#0e0b09` | base `:root` | unchanged | all (text) | LATER (repoint hex in templates) |
| `--copper` `--copper-l` `--copper-d` | `#b87333` `#d4924a` `#8a5520` | base `:root` | unchanged | Buttons, links, accents | LATER |
| `--cream` `--cream-2/3` | `#f5ede0` … | base `:root` | unchanged | inputs, borders | LATER |
| `--stone` `--smoke` `--white` | `#7a6a58` `#c4b39e` `#faf7f2` | base `:root` | unchanged | muted text, hints | LATER |
| `--page-bg` `--card-bg` `--topbar-bg` | `#f7f3ee` `#fff` `#fff` | base `:root` | unchanged | layout | LATER |

> Color SCALE is complete. Debt = templates that hardcode these hexes inline → repoint in
> the foundation that touches each template (Buttons/Cards/Forms), NOT Foundation Zero.

### 1.2 Status colors — ✅ ALREADY TOKENS (document only)
| Token | Current value (light) | Locations | Proposed | Consumers | Priority |
|---|---|---|---|---|---|
| `--status-success-bg/text` | `#ecfdf5` / `#15803d` | base `:root` (+dark) | unchanged | Pills, Badges, Financial | LATER |
| `--status-warning-bg/text` | `#fffbeb` / `#b45309` | base `:root` | unchanged | Pills/Badges | LATER |
| `--status-danger-bg/text` | `#fef2f2` / `#b91c1c` | base `:root` | unchanged | Pills/Badges/Buttons | LATER |
| `--status-info-bg/text` | `#eff6ff` / `#1d4ed8` | base `:root` | unchanged | Pills/Badges | LATER |
| `--status-neutral-bg/text` | `#f4f4f5` / `#71717a` | base `:root` | unchanged | Pills/Badges | LATER |

### 1.3 Surface / background — ✅ ALREADY TOKENS (document only)
| Token | Current value | Locations | Proposed | Consumers | Priority |
|---|---|---|---|---|---|
| `--surface` | `var(--card-bg)` | base `:root` | unchanged | Cards, panels | LATER |
| `--surface-input` / `--surface-input-focus` | `var(--cream)` / `var(--white)` | base `:root` | unchanged | Inputs, Selects | LATER |
| `--border-card` `--border-default` `--border-subtle` | `#cfc0aa` / `var(--cream-3)` / `var(--cream-2)` | base `:root` | unchanged | Cards, tables, forms | LATER |
| `--text-primary/secondary/tertiary` | `var(--ink/stone/smoke)` | base `:root` | unchanged | all text | LATER |

### 1.4 Typography (family + line-height) — NEW
| Token | Current literal(s) | Locations | Proposed | Consumers | Priority |
|---|---|---|---|---|---|
| `--font-sans` | system stack (in `body`) | base.html body | = current stack (inert) | all | P0 (define) |
| `--font-mono` | mono stack (`<code>`) | base.html | = current `code` stack | code/IDs | P0 |
| `--lh-tight` | `1.2`-ish | headings | document current | headings | P0 (define) / DEFER (repoint) |
| `--lh-base` | `1.5`-ish | body | document current | body | P0 / DEFER |

### 1.5 Font sizes — NEW (clean cluster P0; outliers DEFER)
Measured distinct (base + inline-204): **10,11,12,13,14,15,16,17,18,20,22,24,26,28,30,36px.**
Core cluster (high-freq) → scale; outliers → DEFER (no snapping).
| Token | = literal | Count (base / inline) | Consumers | Priority |
|---|---|---|---|---|
| `--fs-2xs` | `10px` | 9 / 17 | micro-labels | P0 |
| `--fs-xs` | `11px` | 11 / 57 | labels, badges | P0 |
| `--fs-sm` | `12px` | 19 / 48 | secondary | P0 |
| `--fs-base` | `13px` | 24 / 40 | **body default** | P0 |
| `--fs-md` | `14px` | 11 / 22 | emphasis | P0 |
| `--fs-lg` | `18px` | 4 / 2 | sub-headings | P0 |
| `--fs-xl` | `22px` | 2 / 3 | headings | P0 |
| `--fs-2xl` | `28px` | 1 / 2 | page titles | P0 |
| `--fs-3xl` | `36px` | 1 / 0 | hero | P0 |
| **DEFER** | `15,16,17,20,24,26,30px` | low-freq | — | **DEFER (scale rationalization, visual)** |

### 1.6 Font weights — NEW (FULLY CLEAN → all P0, fully inert)
| Token | = literal | Count (base) | Consumers | Priority |
|---|---|---|---|---|
| `--fw-normal` | `400` | 3 | body | P0 |
| `--fw-medium` | `500` | 12 | labels | P0 |
| `--fw-semibold` | `600` | 16 | emphasis/titles | P0 |
| `--fw-bold` | `700` | 29 | values/headings | P0 |

### 1.7 Radius scale — NEW (cluster P0; odd DEFER)
Measured distinct (base): **1,2,4,6,7,8,9,10,12,14,16,20,999px.** Inline: 4,6,8,10,12,14,16,20,999.
| Token | = literal | Count (base / inline) | Consumers | Priority |
|---|---|---|---|---|
| `--radius-xs` | `4px` | 4 / 7 | chips, small | P0 |
| `--radius-sm` | `6px` | 9 / 2 | inputs (sm) | P0 |
| `--radius` | `8px` | 11 / 25 | **default** (buttons/inputs) | P0 |
| `--radius-md` | `10px` | 7 / 15 | buttons (alt geometry) | P0 |
| `--radius-lg` | `12px` | 4 / 12 | cards | P0 |
| `--radius-xl` | `14px` | 6 / 4 | large cards | P0 |
| `--radius-2xl` | `16px` | 1 / 6 | hero panels | P0 |
| `--radius-3xl` | `20px` | 4 / 3 | big surfaces | P0 |
| `--radius-pill` | `999px` | 1 / 5 | pills/badges | P0 |
| **DEFER** | `1,2,7,9px` | one-offs | — | **DEFER** |

### 1.8 Spacing scale — NEW (⚠ MOSTLY DEFER — codebase off-grid)
Measured padding distinct: **2,3,4,6,9,10,11,12,14,16,18,20,22,24,28,32,64px;**
gap: **2,4,5,6,7,8,10,11,12,16,18px.** 4px-grid steps = P0; everything else = DEFER.
| Token | = literal | Note | Consumers | Priority |
|---|---|---|---|---|
| `--space-1` | `4px` | grid | all | P0 (exact-match only) |
| `--space-2` | `8px` | grid | all | P0 |
| `--space-3` | `12px` | grid | all | P0 |
| `--space-4` | `16px` | grid | all | P0 |
| `--space-5` | `20px` | grid | all | P0 |
| `--space-6` | `24px` | grid | all | P0 |
| `--space-8` | `32px` | grid | all | P0 |
| `--space-16` | `64px` | grid | layout | P0 |
| **DEFER** | `2,3,5,6,7,9,10,11,14,18,22,28px` | **off-grid (high volume)** | — | **DEFER (scale rationalization, visual)** |

> **Honest scope note:** spacing is the LEAST clean group. Many high-frequency off-grid
> values (6/9/10/11/14/18). Foundation Zero repoints ONLY exact 4/8/12/16/20/24/32/64.
> Off-grid spacing stays untouched until a separate, visible rationalization is approved.

### 1.9 Shadows — PARTIAL (2 exist; 3 new from inline)
| Token | Current value | Locations | Proposed | Consumers | Priority |
|---|---|---|---|---|---|
| `--shadow-card` | `0 2px 12px rgba(14,11,9,0.10)` | ✅ base `:root` | unchanged | Cards/KPI | exists |
| `--shadow-card-hover` | `0 6px 20px -2px rgba(14,11,9,0.14)` | ✅ base `:root` | unchanged | Cards hover | exists |
| `--shadow-focus` | `0 0 0 3px rgba(184,115,51,0.1)` | inline ×2 (base) | = that value | focus rings (a11y) | P0 |
| `--shadow-input-inset` | `inset 0 1.5px 4px rgba(14,11,9,0.07)` | inline (base) | = that value | inputs (readability) | P0 |
| `--shadow-sidebar` | `2px 0 24px rgba(10,3,30,0.55)` | ✅ `--sidebar-shadow` | alias/keep | sidebar | exists |

### 1.10 Breakpoints — NEW (documented CONSTANTS, not live vars)
CSS cannot `var()` inside `@media` → these are a documented convention enforced by review.
Measured layout media: `max-width:600` (primary), `560` (inconsistent), misc flex min-widths.
| Constant | Value | Current usage | Proposed | Priority |
|---|---|---|---|---|
| `bp-xs` | `414px` | — | mobile-large ceiling | P0 (document) |
| `bp-sm` | `600px` | primary mobile bp (most `@media`) | keep as `sm` | P0 |
| `bp-md` | `768px` | — | tablet | P0 (document) |
| `bp-lg` | `1024px` | — | desktop | P0 (document) |
| **DEFER** | align `560`→`600` | 1–2 media blocks | — | **DEFER (visual, tiny)** |

### 1.11 Touch sizes — NEW
| Token | = value | Source | Consumers | Priority |
|---|---|---|---|---|
| `--touch-min` | `44px` | WCAG target (audit) | Buttons/links/inputs/chips | P0 (define) / DEFER (enforce = visual, in F2/F3) |
| `--control-h` | `39px` | measured fancified `sf-input` (CC-05) | Inputs/Selects/Date triggers | P0 (define) |

> `--touch-min` is DEFINED in Foundation Zero but ENFORCING it (resizing 23px action-links
> to 44px) is a VISUAL change → happens in Buttons (F2)/Forms (F3), not Foundation Zero.

### 1.12 Z-index layers — NEW
Measured distinct (base): **1,5,10,100,199,200,1000,9999;** templates: 5, 10000.
| Token | = literal | Current usage | Consumers | Priority |
|---|---|---|---|---|
| `--z-base` | `1` | base stacking | all | P0 |
| `--z-raised` | `10` | raised elements | misc | P0 |
| `--z-dropdown` | `100` | fancify/menus | Selects/Date | P0 |
| `--z-sticky` | `200` | sticky bars (`199/200`) | form CTA/topbar | P0 (align 199→200 = invisible) |
| `--z-overlay` | `1000` | overlays | modal backdrop | P0 |
| `--z-modal` | `9999` | crop modal | Modals | P0 (template `10000` → align, invisible) |
| **DEFER** | `5` | local stacking one-off | — | DEFER |

---

## 2. Per-token completeness
Every token above carries: name · current literal(s) · existing locations/count · proposed
value (= a current literal ⇒ inert) · consumer foundations · migration priority. **No token's
proposed value differs from a value already in the UI.** New values are introduced ONLY as
DEFER candidates, never applied in Foundation Zero.

---

## 3. Proof of visual inertness

- **Stage 0a (define):** tokens added to `:root`, **zero consumers** → render byte-identical.
  Proof = before/after screenshots identical on all 6 pages (§4) + 0 layout shift.
- **Stage 0b (repoint):** every swap is `literal → var(--token)` where `token value ===
  literal`. CSS resolves the var to the identical computed value → **pixel-identical.**
- **Zero color change:** colors are pre-existing tokens; Foundation Zero adds none and
  repoints no hex.
- **Zero spacing change:** only exact 4/8/12/16/20/24/32/64 repointed; off-grid untouched.
- **Zero typography change:** only exact-cluster font-sizes + clean weights repointed;
  15/17/26 etc. untouched.
- **Audit-grade guarantee:** any value that cannot map to an equal token is LEFT AS-IS and
  listed in the DEFER set. Coverage is partial; inertness is total. No silent snapping.
- **Mechanical verification:** computed-style spot-check — for a sample of repointed
  elements, `getComputedStyle(el).<prop>` before === after.

---

## 4. Browser evidence plan

Representative pages (one per surface family), each at **320/375/390/414/1280:**
| Surface | Page |
|---|---|
| Dashboard | main dashboard (`.kpi` grid) |
| Form | a create/edit page (form-shell, `.sf-*`) |
| DataTable | product_list (TC-1 engine) |
| Financial | costing or payroll_overview (GET-only; never reopen golden ₹225) |
| Auth | login |
| Card | adda_detail (`.card` systems) |

For each page × viewport, capture and record:
- **Before** screenshot (pre-0a baseline) → `docs/screenshots/token_<page>_<vw>_before.png`.
- **After** screenshot (post-0a, and again post-0b) → `…_after.png`.
- **Pixel-diff expectation: ZERO diff** (identical). Any non-zero diff = STOP + investigate
  (a non-inert swap slipped in).
- **`scrollWidth === innerWidth`** (0 horizontal overflow) — unchanged from baseline.
- **Console: 0 errors / 0 warnings** (favicon 404 excluded) — unchanged from baseline.
- **Dark theme** toggle on 1 page → tokens theme correctly (no regression).

Cadence: verify after 0a (define), STOP; verify after 0b (repoint), STOP. Never batch.

---

## 5. Rollback plan

- **Single commit** for Foundation Zero (or two: 0a, 0b — owner choice). Rollback =
  `git revert <hash>` (post-commit) / `git checkout -- <files>` (pre-commit).
- **Removing the `:root` tokens restores current behavior** for Stage 0a (nothing consumes
  them). For Stage 0b, revert restores the literals (the diff is literal↔var, mechanical).
- **No template rollback choreography required** — 0a touches only base.html `:root`; 0b
  is value-identical so even a partial revert is safe (a reverted `var()` → literal renders
  the same).
- Files in scope: `base.html` (0a) + the repointed CSS/templates (0b). **No `.py`.**

---

## 6. Backend boundary — STRICT

Foundation Zero is presentation-only. **PROHIBITED:** Python changes · views · services ·
models · URLs · **migrations** · forms (field/logic) · business logic · context vars.
Touch set = `base.html` `:root`/CSS (0a) + literal→token CSS swaps (0b). **0 `.py`, 0
migrations, 0 backend.** Verification gate: `git diff --stat` shows only `.html`/CSS-in-html;
zero `*.py`, zero `migrations/`.

---

## 7. Future compatibility (why this maps cleanly forward)

- **CSS Variables (today):** tokens ARE CSS custom properties on `:root` — already the
  native, framework-free mechanism. Zero build step.
- **Dark mode:** already implemented as a `[data-theme="dark"]` override of the SAME token
  names. New scales (type/radius/space/z) are theme-invariant; color tokens already flip.
  One override block = whole-app theme.
- **React Theme Provider:** the `:root` token set maps 1:1 to a theme object
  (`{ color: { copper: '#b87333' }, space: {1:'4px'…}, radius: {…}, fontSize: {…} }`) fed to
  a ThemeProvider; `var(--copper)` → `theme.color.copper`. Names already namespaced.
- **Tailwind config:** token groups map directly to `theme.extend`
  (`colors`/`spacing`/`borderRadius`/`fontSize`/`fontWeight`/`boxShadow`/`zIndex`/`screens`).
  `screens` ← the §1.10 breakpoint constants. A generator can emit the config from `:root`.
- **Design-system components:** primitives (`.btn`/`.card`/`.stat-card`/MoneyCell/StatusPill)
  consume tokens, so porting a component = swap the styling layer, keep the token contract.
  Strict ownership (one source per concern) = each component has exactly one place to port.

**Portability precondition:** style must live in tokens/classes, NOT inline. That is exactly
what Foundation Zero (define) + later foundations (repoint, de-inline) accomplish.

---

## 8. Coverage ledger (honest summary)

| Group | Foundation-Zero coverage | Deferred (future visible step) |
|---|---|---|
| Colors / Status / Surface | already tokens (define done); repoint hex = LATER foundations | — |
| Font weight | 100% (clean) | — |
| Font size | core cluster (10–14,18,22,28,36) | 15,16,17,20,24,26,30 |
| Radius | cluster (4,6,8,10,12,14,16,20,999) | 1,2,7,9 |
| Spacing | 4/8/12/16/20/24/32/64 only | 2,3,5,6,7,9,10,11,14,18,22,28 (high volume) |
| Shadows | +focus/+input-inset (card ones exist) | — |
| Z-index | full layer set (align 199→200, 10000→9999 invisible) | local `5` one-off |
| Touch | DEFINE `--touch-min`/`--control-h`; ENFORCE = F2/F3 | resizing sub-44 controls (visual) |
| Breakpoints | define xs/sm/md/lg constants | align `560`→`600` |

**Foundation Zero = define-all + repoint-exact-match-only. Inertness total, coverage partial,
deferred set fully enumerated. No silent snapping.**

---

**This is the last architecture gate. No CSS, no `:root` creation, no implementation, no
commits, no token values in code.** On approval, Foundation 1 begins: **Stage 0a (define) →
browser-verify → STOP → Stage 0b (repoint exact) → browser-verify → STOP.** One stage at a time.
