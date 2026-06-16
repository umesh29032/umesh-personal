# B-2 — GEOMETRY-B INVENTORY + PIXEL-IDENTICAL PROOF PLAN

> **Status:** DESIGN + EVIDENCE only — **NO CODE, NO CSS, NO commits.** Pre-B-2 gate.
> B-2 = define `.btn-sm` + `.btn-lg`; this doc proves `.btn-lg` will reproduce the current
> bare Geometry-B exactly before any code. Computed values MEASURED 2026-06-16 (live browser,
> getComputedStyle harness). Context: [BUTTONS_FOUNDATION_SPEC.md](BUTTONS_FOUNDATION_SPEC.md) · [BUTTONS_MIGRATION_MATRIX.md](BUTTONS_MIGRATION_MATRIX.md) (Family 2).
> **Owner:** Umesh · **Created:** 2026-06-16. B-1 committed `ff1d5702`.

---

## 1. Exact inventory — all 24 Geometry-B consumers (file : line : class)

| # | File | Line | Class | Variant | Screenshot |
|---|---|---|---|---|---|
| 1 | templates/inventory/sidebar_access_list.html | 217 | `btn-copper` | copper | harness¹ |
| 2 | production/stage_form.html | 226 | `btn-ghost` | ghost | harness¹ |
| 3 | production/stage_form.html | 227 | `btn-copper` | copper | harness¹ |
| 4 | production/product_flow.html | 359 | `btn-copper` | copper | `geomB_flow_*` ✅ |
| 5 | production/adda_report_review.html | 57 | `btn-ghost` | ghost | harness¹ |
| 6 | production/adda_report_review.html | 58 | `btn-copper` | copper | harness¹ |
| 7 | accounts/user_form.html | 260 | `btn-ghost` | ghost | harness¹ |
| 8 | accounts/user_form.html | 261 | `btn-copper` | copper | harness¹ |
| 9 | accounts/user_create.html | 218 | `btn-ghost` | ghost | harness¹ |
| 10 | accounts/user_create.html | 219 | `btn-copper` | copper | harness¹ |
| 11 | expense/adda_settlement_list.html | 62 | `btn-copper` | copper | harness¹ |
| 12 | expense/advance_form.html | 45 | `btn-ghost` | ghost | `geomB_advance_*` ✅ |
| 13 | expense/advance_form.html | 46 | `btn-copper` | copper | `geomB_advance_*` ✅ |
| 14 | expense/settlement_form.html | 97 | `btn-ghost` | ghost | harness¹ |
| 15 | expense/settlement_form.html | 98 | `btn-copper` | copper | harness¹ |
| 16 | expense/adda_settlement_detail.html | 185 | `btn-ghost` | ghost | harness¹ |
| 17 | expense/adda_settlement_detail.html | 186 | `btn-ghost` | ghost | harness¹ |
| 18 | expense/adda_settlement_detail.html | 189 | `btn-copper` | copper | harness¹ |
| 19 | expense/adda_settlement_detail.html | 270 | `btn-ghost` | ghost | harness¹ |
| 20 | expense/adda_settlement_detail.html | 271 | `btn-danger` | **danger** | harness¹ ² |
| 21 | expense/adda_settlement_detail.html | 273 | `btn-copper` | copper | harness¹ |
| 22 | expense/adda_settlement_detail.html | 279 | `btn-ghost` | ghost | harness¹ |
| 23 | expense/worker_profile_form.html | 44 | `btn-ghost` | ghost | harness¹ |
| 24 | expense/worker_profile_form.html | 45 | `btn-copper` | copper | harness¹ |

**Totals: 12 copper · 11 ghost · 1 danger.**
¹ All 24 render identically per variant (same `:not(.btn)` rules) → computed geometry captured
via injected harness (authoritative, all 3 variants). Live screenshots captured for 2 reachable
pages: `/tmp/geomB_advance_{320,375,390,414,1280}.png` (ghost+copper) · `/tmp/geomB_flow_*`(copper).
² **danger (line 271)** lives only on a *settled* adda's detail (void/reverse action). Measured
via harness, NOT a live page — to avoid touching the golden ₹225 chain (3-PATTI-001). Honest gap:
no live danger screenshot; harness computed geometry is the proof.

---

## 2. Current computed geometry (MEASURED) + target `.btn-lg`

Geometry-B (bare, current) — these ARE the `.btn-lg` targets:
| Property | copper | ghost | danger |
|---|---|---|---|
| border-radius | **10px** | 10px | 10px |
| font-size | **13px** | 13px | 13px |
| font-weight | **700** | **600** | 700 |
| padding | **10px 18px** | 10px 18px | 10px 18px |
| min-height | **40px** | 40px | 40px |
| text-transform | **none** | none | none |
| letter-spacing | **normal** | normal | normal |
| column-gap | **6px** | 6px | 6px |
| background | `#b87333` (copper) | transparent | `#b03434` |
| color | `#fff` | `#0e0b09` (ink) | `#fff` |
| border | none | **1px solid `#cfc0aa`** (border-card) | none |

### The delta `.btn-lg` must override (vs what `.btn .btn-X` gives = Geometry A)
`.btn .btn-X` WITHOUT `.btn-lg` computes (MEASURED): r6 · fs12 · fw700 · padding 9px 18px ·
mh38 · **UPPERCASE** · ls **1.2px** · gap7 · ghost=stone+1.5px cream-3 · danger=`#fee2e2`/`#991b1b`.
→ So `.btn-lg` MUST override: radius 6→10 · font-size 12→13 · padding-y 9→10 · min-height 38→40 ·
text-transform uppercase→none · letter-spacing 1.2px→normal · gap 7→6. **Per-variant:**
ghost weight 700→600 + color stone→ink + border 1.5px-cream-3→1px-border-card; danger
bg `#fee2e2`→`#b03434` + color `#991b1b`→`#fff`. Copper = no override (its `.btn-copper`
color rule already gives copper/white; only the `.btn-lg` layout applies).

---

## 3. CONFIRM — `.btn-lg` exactly reproduces Geometry-B (the B-2 rule set, design-only)

The rules B-2 will write (consume committed 0a tokens where exact; off-grid stays literal):
```
.btn-lg {
  padding: 10px 18px;            /* 10/18 off-grid → literal */
  border-radius: var(--radius-md);   /* 10px ✓ token */
  font-size: var(--fs-base);         /* 13px ✓ token */
  min-height: 40px;              /* no 40 token (--control-h 39 / --touch-min 44) → literal */
  text-transform: none;
  letter-spacing: normal;
  gap: 6px;                      /* off-grid → literal */
  /* font-weight inherits .btn 700 (correct for copper + danger) */
}
.btn-ghost.btn-lg {
  font-weight: var(--fw-semibold);   /* 600 ✓ token */
  color: var(--ink);
  border: 1px solid var(--border-card);
}
.btn-danger.btn-lg {
  background: #b03434;           /* raw hex, kept identical (no exact token) */
  color: #fff;
}
/* copper: NO .btn-copper.btn-lg rule needed — copper/white from existing .btn-copper */
```

Per-property confirmation (current-B → target-`.btn-lg`):
| Requirement | copper | ghost | danger | Reproduced? |
|---|---|---|---|---|
| **radius** | 10→`--radius-md`(10) | 10 | 10 | ✅ identical |
| **font-size** | 13→`--fs-base`(13) | 13 | 13 | ✅ identical |
| **padding** | 10px 18px | 10px 18px | 10px 18px | ✅ identical (literal) |
| **min-height** | 40px | 40px | 40px | ✅ identical (literal) |
| **casing** | none | none | none | ✅ (override uppercase) |
| **letter-spacing** | normal | normal | normal | ✅ (override 1.2px) |
| (gap) | 6px | 6px | 6px | ✅ |
| (weight) | 700 | 600 (`--fw-semibold`) | 700 | ✅ |
| (color/bg/border) | copper/#fff | ink/transp/1px border-card | #b03434/#fff | ✅ per-variant override |

**Design confirmation: YES** — with the rule set above, `.btn .btn-copper .btn-lg`,
`.btn .btn-ghost .btn-lg`, `.btn .btn-danger .btn-lg` reproduce the measured Geometry-B
values exactly. **Final confirmation = the B-2 measurement gate (§4): post-code harness must
byte-equal `/tmp/geomB.json` `B_*` values before any markup repoint (B-3).**

---

## 4. Pixel-identical migration proof plan

**B-2 (define `.btn-sm`/`.btn-lg`) — additive, no markup change yet:**
1. Write the §3 rules.
2. Restart server (template cache).
3. Re-run the §2 harness measuring `.btn .btn-copper .btn-lg` / `.btn-ghost .btn-lg` /
   `.btn-danger .btn-lg`. **GATE: each computed property === the current `B_*` baseline in
   `/tmp/geomB.json`.** Any mismatch → fix `.btn-lg` before proceeding. (B-2 changes nothing
   on screen — no element uses `.btn-lg` yet — so page screenshots stay byte-identical.)
4. Also confirm `.btn`/`.btn-primary`/etc. (B-1 state) UNCHANGED (no regression to Geometry A).

**B-3 (repoint 24 buttons → `.btn …btn-lg`, delete `:not(.btn)`) — the visual-zero migration:**
- Per the 11 files (§1), `class="btn-copper"` → `class="btn btn-copper btn-lg"` (+ ghost/danger).
- **Before/after screenshots** at **320 / 375 / 390 / 414 / 1280** on every reachable page:
  `/expense/advances/add/` (ghost+copper), `/production/products/1/flow/` (copper),
  user_create/user_form, settlement_form, worker_profile_form. (Baselines already captured:
  `/tmp/geomB_advance_*`, `/tmp/geomB_flow_*`.)
- **Computed-style comparison:** harness on each migrated button → must equal `B_*` baseline.
- **Pixel-diff:** before/after screenshot md5 — expect identical on static pages (DataTable/
  animated pages excepted, as established).
- `scrollWidth===innerWidth` unchanged · 0 new console · dark-theme renders.
- **danger (line 271):** verify via harness + (if a NON-golden settled adda exists) a live
  shot; else harness-only, documented. **Never open/reopen golden 3-PATTI-001.**
- Delete `:not(.btn)` block ONLY after all 24 proven pixel-identical.

**Gate to advance:** every viewport · every variant · computed-identical + pixel-identical
(static) → STOP → owner approve → 1 commit (B-2), then separately B-3.

---

## 5. Risks / honesty
- **Highest:** ghost (color/weight/border) + danger (color) differ between Geometry A and B →
  `.btn-lg` per-variant overrides are MANDATORY; the §4 measurement gate catches any miss.
- danger has no live screenshot (golden-avoidance) — harness-proven only.
- `#b03434` stays raw hex (no exact token) to remain identical; danger-color unification is a
  SEPARATE future visual decision, not B-2/B-3.
- B-2 is inert on screen (zero consumers of `.btn-lg` until B-3).

---

**No code. No CSS. No commits.** On approval, B-2 implements the §3 rules, runs the §4
measurement gate, STOPs. B-3 (markup repoint) remains a separate later approval.
