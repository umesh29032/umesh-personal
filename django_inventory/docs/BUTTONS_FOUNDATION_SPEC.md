# BUTTONS FOUNDATION SPEC

> **Status:** Foundation contract — **DESIGN ONLY. NO CODE. NO CSS. NO token consumption.
> NO commits.** The single-source contract for every button in the project.
> Evidence: [BUTTONS_AUDIT_REPORT.md](BUTTONS_AUDIT_REPORT.md). Rules baseline: [DESIGN_SYSTEM_SPEC.md](DESIGN_SYSTEM_SPEC.md) §2.
> **Owner:** Umesh · **Created:** 2026-06-16. Foundation #2 in [ROADMAP](DESIGN_SYSTEM_IMPLEMENTATION_ROADMAP.md).

## 1. Purpose
One button system. One owner. One geometry per documented size. Change a button rule in
ONE place → whole project moves. Kill the 8-system fragmentation (audit §0): two base
geometries, 24 bare `:not(.btn)`, 31 inline-styled, 8 inline-mini files, `.btn-mini`×2,
`.lybtn`, sub-44 touch everywhere.

## 2. Shared owner
`accounts/base.html` — `.btn` + modifiers (CSS) + `.action-link` + `.action-icon`. **No
page-scoped button CSS. No inline button geometry. No second button class family.**

## 3. Variant taxonomy (the allowed set)
A button = `.btn` (base, REQUIRED) + at most one **intent** + at most one **size**.

### Intents
| Class | Use | Notes |
|---|---|---|
| `.btn-primary` | main action | copper (absorbs `.btn-copper` → alias, then retire) |
| `.btn-ghost` | secondary | transparent + border |
| `.btn-danger` | destructive | one danger style (resolve `#fee2e2/#991b1b` vs money `#b03434` → pick one, see §5) |
| `.btn-filter` / `.btn-clear` | filter toolbar pair | documented filter-group intents |

### Sizes
| Class | Geometry | Replaces |
|---|---|---|
| (default) | Geometry A — `--radius-sm`, `--fs-sm`, uppercase, `min-height:--touch-min` | today's `.btn` |
| `.btn-sm` | dense/table-row — small padding, `--fs-xs`, **`min-height:--touch-min` on ≤sm** | inline `4px 10px` (8 files) · `.btn-mini` (2) |
| `.btn-lg` | comfortable — Geometry B (`--radius-md`, `--fs-base`, not-uppercase) | the bare `:not(.btn)` money buttons |

### Affordances (not `.btn`, documented)
| Class | Use | Touch rule |
|---|---|---|
| `.action-link` | text row-action | bump to ≥44px tap area on ≤sm |
| `.action-icon` (or `.btn-icon`) | icon-only action | square ≥44px on ≤sm; `aria-label` required |

## 4. Allowed / Forbidden
**Allowed:** `class="btn btn-primary"`, `class="btn btn-ghost btn-sm"`,
`class="btn btn-lg btn-danger"`, `.action-link`, `.action-icon`.
**Forbidden (review-blockers):**
- Intent/size modifier **without `.btn` base** (`class="btn-copper"` alone) — the
  `:not(.btn)` divergence; banned once Foundation 2 lands.
- **Inline geometry** on a button (`style="padding…;font-size…;border-radius…"`).
- **New page-scoped button class** (`.lybtn`, future `.xbtn`) — fold into `.btn`.
- `<div>`/`<span>` as a button — use `<button>`/`<a>`.
- Color-only/icon-only button with no `aria-label`.

## 5. Geometry-divergence resolution (the one DECISION this spec needs)
Audit found two real geometries (A: r6/fs12/uppercase/mh38 · B: r10/fs13/no-uppercase/mh40,
24 money buttons). **Recommended (mostly-inert) path — Option 1:**
- **Legitimize B as `.btn .btn-lg`.** Money markup changes `class="btn-copper"` →
  `class="btn btn-copper btn-lg"`. The rendered look stays **identical** (same geometry,
  now via a named modifier on the base) — only the *mechanism* (`:not(.btn)` hack) dies.
  Net visual = zero. This removes the divergence WITHOUT a visual change.
- **Danger color:** two reds exist (`#fee2e2/#991b1b` soft vs `#b03434` solid). Picking one
  IS a visual change → **flagged decision**, owner picks; default = keep both as
  `.btn-danger` (soft) vs `.btn-danger.btn-lg` (solid) until a deliberate unification.
- **Option 2 (defer):** collapse A and B into ONE geometry → visual change to one set →
  separate, explicitly-approved "geometry rationalization." NOT in the inert migration.
- **uppercase / letter-spacing / padding (9/18 off-grid):** kept as-is (off-grid padding =
  DEFER per token spec; changing case/tracking = visual = defer).

## 6. Token contract (consume Stage-0a tokens; values already match = inert where on-grid)
`--radius-sm`(6) base · `--radius-md`(10) lg · `--fs-sm`(12)/`--fs-xs`(11)/`--fs-base`(13) ·
`--fw-bold`/`--fw-semibold` · `--touch-min`(44) min-height · `--shadow-focus` focus ring ·
`--copper`/`--copper-d` + `--status-danger-*` colors. **Off-grid padding (9/18/14px) NOT
repointed** in the inert pass (token spec DEFER). Raw hex (`#fee2e2/#991b1b/#b03434`) →
repoint to status tokens only as a deliberate (possibly visual) step.

## 7. Touch + accessibility
- Every interactive button ≥ `--touch-min` (44px) tap target. `.btn-sm`/`.action-link`/
  `.action-icon` reach 44 via mobile min-height/padding (mirror the existing `.btn-mini@sm`
  pattern — the one control that already does this right).
- Real `<button>`/`<a>`; `:focus-visible` ring from `--shadow-focus`; icon-only ⇒ `aria-label`;
  `:active` scale preserved; `-webkit-tap-highlight-color:transparent` kept.

## 8. Naming
`.btn` base · `.btn-<intent>` · `.btn-<size>`. Affordances `.action-link(-danger)` /
`.action-icon(-danger)`. No `ly`/page prefixes. Filter pair stays `.btn-filter`/`.btn-clear`.

## 9. Migration strategy (staged; each browser-verified, STOP, owner-approved, then commit)
| Stage | Work | Visual? | Risk |
|---|---|---|---|
| **B-1** | Tokenize `.btn` + modifiers in base.html (on-grid values → tokens) | inert (value-identical) — ✅ DONE `ff1d5702` | low |
| **B-2** | Add `.btn-lg` ONLY (lg = current geometry-B, exact values). **`.btn-sm` deferred to B-4** — it has a pre-existing consumer (`stage_rate_list.html:56`), so defining it here is NOT inert. `:focus-visible` ring also deferred (visual). | additive, inert (verified byte-identical) | low |
| **B-3** | Legitimize money buttons: 24 bare `class="btn-copper"` → `class="btn btn-copper btn-lg"` (+11 ghost, +1 danger); delete `:not(.btn)` hack | **zero visual** (same geometry) — verify pixel-identical | MED (the hotspot) |
| **B-4** | Replace 8 inline-mini files + 31 inline-styled btns → `.btn .btn-sm`; fold `.btn-mini`(2) → `.btn-sm` | near-inert (≤sm touch grows to 44 = intended) | MED |
| **B-5** | Adopt `.btn` on escaped raw buttons (`lybtn`×6, `next-up-action`, `so-tile-jump`); delete `.lybtn` CSS | small visual on those few → verify | low |
| **B-6** | Enforce `--touch-min` on `.action-link`/`.action-icon` (mobile) | **intended visual** (sub-44 → 44) → owner sign-off | low |
- B-1/B-2 first (inert, unblock). B-3 is the divergence kill (must prove pixel-identical).
- B-6 is a deliberate a11y improvement (the only intended visual) — separate approval.

## 10. Rollback
Per-stage single commit → `git revert`. B-1/B-2 inert (revert = no-op visually). B-3 revert
restores bare classes + the `:not(.btn)` block. No `.py` (0 submit inputs). Working-tree
`git checkout -- <files>` pre-commit.

## 11. Browser verification (every stage, 320/375/390/414/1280)
- Representative pages with each variant: a list (ghost/sm row-actions), a form (primary +
  ghost in `.form-actions`), a **money page** (B-3: bare→btn-lg, must be pixel-identical via
  computed-style fingerprint), a filter toolbar (filter/clear), the layering page (B-5).
- Assert: computed-style before==after for inert stages · `scrollWidth===innerWidth` ·
  0 new console · `:focus-visible` ring present · touch heights ≥44 where enforced (B-6) ·
  dark theme. GET-only on money pages; never reopen golden ₹225.

## 12. Risks
- **B-3 money geometry (highest):** 24 buttons; the bare classes currently rely on
  `:not(.btn)`. Adding `.btn` flips them to Geometry A unless `.btn-lg` exactly reproduces B
  — `.btn-lg` MUST be defined to equal B's values first (B-2) and proven pixel-identical.
- **Inline-style sprawl (B-4):** 31 + 8 files; mechanical but wide → per-file, browser-checked.
- **Escaped raw buttons (B-5):** small visual shifts acceptable but must be shown.
- **Touch enforcement (B-6):** intentional visual growth on row-actions — owner must accept.

---

**No code. No CSS. No token consumption. No commits.** This is the contract. Implementation =
the §9 stages, one at a time, browser-verified, STOP + approve + commit each. **STOP after
these two button documents.**
