> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PHASE 6 COMPLETION REPORT — Export & Production Ready
(2026-07-07 · M9 final validation)

**Status: ✅ PHASE 6 COMPLETE (M1–M9). CODEBASE FROZEN.**
**⚠️ The project is NOT declared finally complete (owner instruction):
final Owner Acceptance Validation — on the owner's real T-Shirt product,
with the owner's dedicated specification — happens next and is
owner-held. No new work of any kind until that specification arrives.**

## Phase-6 milestone chain (each owner-approved, each STOPPED)
| M | Delivered | Receipt |
|---|---|---|
| M1 | BLF internal timebox (F1) — honest give-up both engine paths | PHASE6_M1_REPORT |
| M2 | THE one migration (0007): two-model split (ProductFabricProfile defaults-only · ProductionLayout designation-only) + is_optional + reference kind; reversibility proven live; pin 15→17 | PHASE6_M2_REPORT |
| M3 | 🔒 FROZEN single-writer contract (F-1..F-6 + Rules A/B + `resolve_generation_geometry` rename): approve/profile/piece-flag/reference writers; optional per-(piece,size) honest skip persisted | PHASE6_M3_REPORT |
| M4 | Smart redirect `/patterns/tool/<pk>/` (locked 5-branch priority) + the ONE production entry button (ADR-H-safe) + Rules C/D/E (§2b; Rule-E audit = the app log) | PHASE6_M4_REPORT |
| M5 | Layout ▾ switcher (★ → drafts newest-first → ＋ Generate New; document-editor dirty confirm) + Rule-G prefills (Generate form only) + Rules F/G/H/I (§2c) | PHASE6_M5_REPORT |
| M6 | Pattern Design Hub (Rules J–N §2d): derived-only completion dashboard, blockers/warnings, readiness matrix (also on Generate), piece-first next-steps, reference-image UI w/ zoom, optional toggle; DEV-TEE golden 100% + DEV-HUB incomplete demo | PHASE6_M6_REPORT |
| M7 | Approve UI: summary-BEFORE-approve review step → explicit audited act; Production Layout Summary (§3f) on every layout page; §3g law runtime-verified | PHASE6_M7_REPORT |
| M8 | Production exports: pure-python PDF (page 1 = summary; TRUE-SCALE numbered tiles, byte-pinned 283.46 pt/100 mm), tiled print page, SVG summary stamping; verified-only | PHASE6_M8_REPORT |
| M9 | This validation + freeze | this file |

## M9 hostile engineering review
Full pass over every Phase-6 surface (views, services, templates,
compute tool, JS). **One correctness-class finding, fixed:** the SVG
renderers inserted piece names and the summary `<desc>` unescaped —
a management-entered `&`/`<` could corrupt a production artifact; both
`marker_svg` and `marker_tile_svg` now XML-escape (regression-tested).
**Known limits (accepted, documented):** extreme markers near the 100 m
sanity ceiling produce thousands of print/PDF tiles (bounded by the
existing `MAX_HEIGHT_MM` cap); the switcher lists all saved layouts
(fine at factory volume). Phase-5's reviewed `innerHTML` sinks build
from numeric metrics only — unchanged, frozen.

## M9 complete E2E (browser, live server, real engines)
One unbroken production loop on DEV-TEE:
1. Production page → **🧵 Open Layout Tool** → smart redirect →
   `workspace/12` (★ production, context strip correct).
2. Hub: **100% · Production Ready ✅** (golden demo intact).
3. Generate: profile prefills (1500/5.0) shown, edited to 990/L×1 →
   **real engine run #9** → 2 verified options (#13, #14).
4. Editor on #13 → height edited → **real Optimize** → 4-card strip,
   Option 1 honestly "SAVES 14.0 mm" → Keep → **Save** → new immutable
   draft **#15** ("Layout saved (1291.0 mm, verified)").
5. Approve #15: review step names the replaced #12 + history promise →
   explicit POST → **★ THE production layout**.
6. Redirect now lands `workspace/15`; exports on the new ★: print page
   **30 tiles**, **PDF 200/83 KB `%PDF-1.4`**, SVG stamped
   (`"production": true`).
   (One E2E stumble, honestly: a form-submit helper hit the sidebar
   Sign-Out form — the documented first-form trap — logged me out;
   re-ran scoped via `field.form`. No app defect.)

## Mobile pass (390×844)
Hub / editor / approve screenshots (`m9_mobile_*.png`): dashboard
stacks, chips wrap, buttons ≥44 px, **no horizontal scroll**.

## Final regression (all fresh, serial)
patterns_ai **318/318 OK** · full manufacturing suite **1203/1203 OK** (serial, fresh) ·
`makemigrations --check`: **No changes detected** · import contracts: **unchanged — 1 kept, 1 broken (pre-existing target)** ·
`manage.py check`: **no issues (0 silenced)** · compute-bridge smoke: **OK — runtime available, BLF candidate produced + verified** ·
model pin 17 · ONE Phase-6 migration (0007, reversibility proven) ·
I-1/ADR-F/purity walls green inside the suites.

## What Phase 6 delivered (INTEGRATION_DESIGN §5 — all nine items)
smart redirect + entry button ✅ · switcher ✅ · exports (PDF/print/SVG
stamp) ✅ · Approve act + Production Layout Summary ✅ · Pattern Design
Hub ✅ · is_optional + honest skip ✅ · reference images ✅ ·
ProductFabricProfile + prefills ✅ · BLF timebox + engine envelope ✅.
Locked rule set: A–N (§2b/§2c/§2d/§3i) — all implemented, all tested.

## 🔒 FREEZE
Phase-6 code, the frozen M3 service contract, the locked rules A–N and
the golden demo data (DEV-TEE ★ #15 · DEV-HUB incomplete) are FROZEN.
Per §6 finality: no Phase 7, no roadmap, no proposals, no AI expansion.
**Next and only next: the Owner Acceptance Validation** — owner-held,
real T-Shirt product only, dedicated owner specification to come.
Everything remains uncommitted per the owner checkpoint-commit policy.
