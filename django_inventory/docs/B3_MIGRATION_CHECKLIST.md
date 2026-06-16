# B-3 — MIGRATION CHECKLIST (24 Geometry-B buttons)

> **Status:** Pre-B-3 plan — **DESIGN + EVIDENCE only. NO CODE, NO markup change, NO commits.**
> B-3 = repoint 24 bare buttons `class="btn-X"` → `class="btn btn-X btn-lg"`, then delete the
> `:not(.btn)` hack — visually ZERO (`.btn-lg` already proven == Geometry-B byte-for-byte, B-2 `0317a65d`).
> Context: [B2_GEOMETRY_B_PROOF_PLAN.md](B2_GEOMETRY_B_PROOF_PLAN.md) · [BUTTONS_MIGRATION_MATRIX.md](BUTTONS_MIGRATION_MATRIX.md).
> **Owner:** Umesh · **Created:** 2026-06-16. HEAD `0317a65d` (B-1 `ff1d5702` + B-2).

## 0. Why this is safe before we start
`.btn-lg` was MEASURED to reproduce bare Geometry-B byte-for-byte (copper/ghost/danger,
16 props each — B-2 evidence). So swapping `class="btn-copper"` → `class="btn btn-copper btn-lg"`
yields the **same computed style** → same render. The migration is a class rename with a
CSS-guaranteed identical result. Screenshots + per-button computed checks CONFIRM it.

## 1. Per-button checklist (all 24)
Target: copper → `btn btn-copper btn-lg` · ghost → `btn btn-ghost btn-lg` · danger → `btn btn-danger btn-lg`.
Reachability: **✅** = reachable, before-baseline captured · **⚙** = state-gated (money/flow state) → computed-equality + opportunistic capture · **🔒** = golden-adjacent (settled adda) → harness-only, never open 3-PATTI-001.

| # | File:line | Variant | Target class | Page | Reach | Before shot |
|---|---|---|---|---|---|---|
| 1 | sidebar_access_list:217 | copper | `btn btn-copper btn-lg` | Access-control sidebar rules | ⚙ | pending |
| 2 | stage_form:226 | ghost | `btn btn-ghost btn-lg` | product flow → stage add/edit | ⚙ | pending |
| 3 | stage_form:227 | copper | `btn btn-copper btn-lg` | (same) | ⚙ | pending |
| 4 | product_flow:359 | copper | `btn btn-copper btn-lg` | /production/products/1/flow/ | ✅ | `geomB_flow_*` |
| 5 | adda_report_review:57 | ghost | `btn btn-ghost btn-lg` | adda report-review | ⚙ | pending |
| 6 | adda_report_review:58 | copper | `btn btn-copper btn-lg` | (same) | ⚙ | pending |
| 7 | user_form:260 | ghost | `btn btn-ghost btn-lg` | /app/users/&lt;id&gt;/edit/ | ⚙ | pending |
| 8 | user_form:261 | copper | `btn btn-copper btn-lg` | (same) | ⚙ | pending |
| 9 | user_create:218 | ghost | `btn btn-ghost btn-lg` | user create | ⚙ | pending |
| 10 | user_create:219 | copper | `btn btn-copper btn-lg` | (same) | ⚙ | pending |
| 11 | adda_settlement_list:62 | copper | `btn btn-copper btn-lg` | /expense/settlements/ (conditional) | ⚙ | pending |
| 12 | advance_form:45 | ghost | `btn btn-ghost btn-lg` | /expense/advances/add/ | ✅ | `geomB_advance_*` |
| 13 | advance_form:46 | copper | `btn btn-copper btn-lg` | (same) | ✅ | `geomB_advance_*` |
| 14 | settlement_form:97 | ghost | `btn btn-ghost btn-lg` | adda settlement form | ⚙ | pending (GET-only) |
| 15 | settlement_form:98 | copper | `btn btn-copper btn-lg` | (same) | ⚙ | pending (GET-only) |
| 16 | adda_settlement_detail:185 | ghost | `btn btn-ghost btn-lg` | settled adda detail | 🔒 | harness |
| 17 | adda_settlement_detail:186 | ghost | `btn btn-ghost btn-lg` | (same) | 🔒 | harness |
| 18 | adda_settlement_detail:189 | copper | `btn btn-copper btn-lg` | (same) | 🔒 | harness |
| 19 | adda_settlement_detail:270 | ghost | `btn btn-ghost btn-lg` | (same) | 🔒 | harness |
| 20 | adda_settlement_detail:271 | **danger** | `btn btn-danger btn-lg` | (same) | 🔒 | harness |
| 21 | adda_settlement_detail:273 | copper | `btn btn-copper btn-lg` | (same) | 🔒 | harness |
| 22 | adda_settlement_detail:279 | ghost | `btn btn-ghost btn-lg` | (same) | 🔒 | harness |
| 23 | worker_profile_form:44 | ghost | `btn btn-ghost btn-lg` | worker profile form | ⚙ | pending |
| 24 | worker_profile_form:45 | copper | `btn btn-copper btn-lg` | (same) | ⚙ | pending |

12 copper · 11 ghost · 1 danger. (`adda_settlement_detail` = 7 buttons, all on the settled-adda
detail; danger at :271 is the void/reverse action that only renders on a settled adda.)

## 2. Before screenshots
- **Captured baselines (pre-B-3):** `/tmp/geomB_flow_{320,375,390,414,1280}.png` (copper),
  `/tmp/geomB_advance_{320,375,390,414,1280}.png` (ghost+copper).
- **State-gated (⚙):** capture at B-3 start once the page is reachable in the right state
  (find user edit/create URL; reach a settleable adda for settlement_form; report-review state).
- **Golden-adjacent (🔒) `adda_settlement_detail`:** before-state captured via the variant
  HARNESS (`/tmp/geomB.json` B_copper/B_ghost/B_danger) — NOT by opening the golden chain.
  If a NON-golden settled adda exists, capture there; else harness-only (documented).

## 3. After screenshots
Re-capture each reachable page (✅/⚙) at 320/375/390/414/1280 after the class swap →
`/tmp/b3_after_<page>_<vp>.png`. Compare to the before-baseline.

## 4. Computed-style equality (the primary gate)
Per migrated button, harness `getComputedStyle` of the live element → must equal the
`B_*` baseline (16 props: radius/font-size/weight/padding×4/min-height/text-transform/
letter-spacing/gap/bg/color/border×3). Because `.btn-lg` is already proven == B, this
verifies the class was applied correctly (typo-free) on each page. **Gate: every migrated
button computed-equal to its variant's `B_*`; any mismatch → fix markup before continuing.**

## 5. Pixel-diff proof
Before/after screenshot md5 on reachable static pages → **expect IDENTICAL.** Pages with
DataTables / animation are non-deterministic (established) → fall back to the computed-style
gate (§4) there. Tiny byte deltas on dynamic pages are noise, not the migration.

## 6. `:not(.btn)` removal
Delete the `:not(.btn)` block (base.html ~line 1620, 6 occurrences) **ONLY after all 24
buttons are migrated AND computed-equal**. Until then it stays (harmless — migrated buttons
carry `.btn` so they no longer match `:not(.btn)`; any unmigrated bare button still works).
After deletion: re-verify no bare `.btn-copper/.btn-ghost/.btn-danger` remain
(`grep` → 0) so nothing falls back to undefined geometry.

## 7. Rollback plan
- **Single B-3 commit** → `git revert <hash>` restores all bare classes + (if removed) the
  `:not(.btn)` block in one shot.
- **Pre-commit / per-file:** `git checkout -- <template>` restores that file's bare classes.
- **Ordering safety:** do all 24 markup swaps + verify FIRST; delete `:not(.btn)` LAST in the
  same commit. If any button fails the computed gate, revert that file and keep `:not(.btn)`.
- No `.py`, 0 migrations — template + base.html CSS only. Backend untouched.
- **Golden safety:** GET-only on all money pages; never open/reopen/settle 3-PATTI-001.

## 8. Execution order (when approved)
1. Capture before-baselines for any ⚙ pages now reachable (+ already-have ✅).
2. Swap classes file-by-file (11 files), browser-verify each: computed-equal + screenshot.
3. After all 24 pass → delete `:not(.btn)` → re-verify grep=0 bare + spot-check pages.
4. Full sweep: 5 viewports, scrollWidth===innerWidth, console clean, dark theme.
5. STOP → owner review → ONE commit "Foundation 2 - B3 ...".

---

**No code. No markup change. No commits.** B-3 remains a separate approval gate. On approval,
execute §8, prove §4/§5 per button, STOP before commit.
