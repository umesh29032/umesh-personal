# B-4 — `.btn-sm` IMPLEMENTATION SPEC

> **🔒 FROZEN 2026-06-16 (owner).** B-4 SPEC frozen pending finalization of the compact-button
> design language. B-4/B-5/B-6 remain PENDING (not implemented). Foundation 2 paused after
> B-3 `138dafab` (B-1/B-2/B-3 done, inert). Resume only on explicit owner approval.
>
> **Status:** SPEC only — **NO CODE, NO commits.** B-4 = define `.btn-sm` + converge the
> compact/row-action buttons onto it. **Unlike B-1/B-2/B-3 (inert), B-4 is a RATIONALIZATION
> — it has INTENTIONAL visual deltas** (varied inline mini-paddings snap to one canonical).
> Owner must accept per-button before/after. Context: [BUTTONS_AUDIT_REPORT.md](BUTTONS_AUDIT_REPORT.md) · [BUTTONS_MIGRATION_MATRIX.md](BUTTONS_MIGRATION_MATRIX.md) Family 3-5.
> **Owner:** Umesh · **Created:** 2026-06-16. After B-3 `138dafab`.

## 1. Why B-4 is not inert (measured)
The inline/compact button surface is **varied**, not one geometry:
| Inline padding | count | class |
|---|---|---|
| `4px 10px` | 14 | dominant mini (the 7 inline-mini files) |
| `6px 14px` | 5 | other small |
| `5px 12px` · `4px 12px` · `3px 8px` · `2px 8px` | 1 each | other small |
| `8px 12px` | 2 | small-ish |
| `12px 32px` · `14px 20px` | 2 · 1 | **LARGE CTA — NOT mini → out of `.btn-sm` scope** |
Plus `.btn-mini` (page-scoped, 2 files): `6px 10px / r8 / fs12 / min-height:44 @≤sm`.
Plus `stage_rate_list:56` stray `btn btn-sm` (9 rendered, currently full-size — undefined).
→ Converging these to ONE `.btn-sm` necessarily changes some (snap to canonical) = visual.

## 2. Canonical `.btn-sm` geometry (DECISION — recommend)
**Recommended:** `.btn-sm { padding: var(--space-1) 10px; }` = **4px 10px**, everything else
inherited from `.btn` (r6 / fs12 / fw700 / uppercase / **height 38 via min-height**). Plus a
**mobile touch rule** `@media (max-width:600px){ .btn-sm{ min-height:44px } }`.
Rationale: 4/10 is the dominant (14×) inline-mini → **inert for the 7 inline-mini files on
desktop**; the mobile-44 preserves `.btn-mini`'s existing touch-safety + upgrades the rest.
- **Sub-decision A (mobile touch):** include `min-height:44 @≤sm` in `.btn-sm` now (recommended
  — keeps `.btn-mini` pages touch-safe, upgrades inline-mini) **OR** defer all touch to B-6
  (then `.btn-mini` pages temporarily lose their @sm 44). Recommend **include now**.
- **Sub-decision B (font-size):** keep fs12 (inherited, matches inline-mini) — NOT `--fs-xs`
  (11) as the original sketch said; 12 makes the 7 inline-mini files truly inert on desktop.

## 3. Per-target classification + visual impact
| Target | Files/count | Current → `.btn-sm` | Visual? |
|---|---|---|---|
| **Inline-mini `4px 10px`** | 7 files (product_list, master_list, role_list, export_list, _stage_panel_cutting, _stage_panel_cutting_pattern + 1) | `style="padding:4px 10px"` → `.btn-sm` | **NO (desktop)** · mobile +44 (intended) |
| **`.btn-mini` page-scoped** | 2 (product_sizes_edit, product_patterns_edit) | `.btn-mini` (6/10/r8/mh44@sm) → `.btn-sm` (4/10/r6/mh44@sm) | **small** (6→4 pad, r8→r6) — before/after |
| **stage_rate_list stray** | 1 (9 buttons) | `btn btn-sm` undefined (9/18) → defined (4/10) | **YES** (intended-fix; author wanted small) — before/after |
| **Other small inline** (6/14, 5/12, 3/8, 2/8, 8/12) | ~10 buttons across inline-styled 15-file set | snap to `.btn-sm` (4/10) OR keep if intentional | **small** — per-button judgment + before/after |
| **Large inline** (12/32, 14/20) | 3 buttons | **OUT OF `.btn-sm` SCOPE** — leave, or address as full-width/CTA separately | n/a |

## 4. Allowed / forbidden (consistent with [SPEC](DESIGN_SYSTEM_SPEC.md) §2)
- Allowed: `class="btn btn-ghost btn-sm"` etc. (`.btn` base + intent + `.btn-sm`).
- Remove inline `style="padding:…;font-size:…"` from migrated buttons.
- Forbidden: `.btn-sm` without `.btn` base; new page-scoped `.btn-mini`-style class; forcing
  large CTAs (12/32, 14/20) onto `.btn-sm`.

## 5. Tokens
`padding: var(--space-1) 10px` (4=token, 10 off-grid literal) · fs/r/fw inherited (already
tokenized via `.btn`, B-1) · `min-height:44px` = `var(--touch-min)` (mobile rule).

## 6. Migration order (B-4 sub-stages, each browser-verified + STOP)
1. **B-4a** define `.btn-sm` (additive). **NOTE: NOT inert** — `stage_rate_list:56` already
   uses `btn btn-sm` → defining it changes those 9 buttons immediately. So B-4a + the
   stage_rate_list verification happen together (before/after on stage-rates page).
2. **B-4b** migrate the 7 inline-mini files (desktop-inert; mobile +44). Per-file before/after.
3. **B-4c** fold `.btn-mini` (2 files) → `.btn-sm`; delete page `.btn-mini` CSS after. before/after.
4. **B-4d** the other small inline buttons (per-button: snap or keep). before/after each.
5. Large CTAs (12/32, 14/20) explicitly LEFT (logged, separate future decision).

## 7. Proof per sub-stage
- Computed-style of each migrated button (16 props) recorded before/after.
- Inert targets (7 inline-mini desktop): before==after (desktop) — assert identical.
- Rationalized targets (.btn-mini, stray, other-small): before/after screenshots 320–1280;
  owner accepts the delta. Document each change (e.g. r8→r6, 6→4 padding).
- scrollWidth===innerWidth · console clean · dark theme.

## 8. Rollback
Per-sub-stage single commit → `git revert`. `.btn-sm` definition removal restores
stage_rate_list to full-size (undefined no-op). Per-file `git checkout` restores inline styles
/ `.btn-mini`. 0 `.py`.

---

**No code. No commits.** B-4 is a separate approval gate. **Key difference from B-1/B-2/B-3:
B-4 carries intentional visual changes (compact rationalization)** — needs explicit owner
sign-off on the deltas, not just an inertness proof. Decisions in §2 (canonical geometry +
mobile touch + font-size) need owner approval before B-4a.
