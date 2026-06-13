> **ARCHIVED 2026-06-13** -- PKALS review-cycle artifact (process/history), not living knowledge. Kept for the record; do NOT treat as current. Living docs: docs/LEARNING_2_0/ (START_HERE).

# PKALS — FINAL SCORECARD (Phase 2, 3–5-year survival)

> Scores the 7 review objectives for **long-term survival**, not present-day
> polish. Companion: [PKALS_FINAL_REVIEW.md](PKALS_FINAL_REVIEW.md). Baseline =
> H1–H4 applied. Evidence reproduced on the live tree, commit `f067daf0`,
> 2026-06-13. "Post-H1–H4 organisational score" (from PKALS_SCORECARD) measured
> *current* quality; this scores *durability* — so it is intentionally harsher.

> **UPDATE 2026-06-13:** findings C-1, H-A, H-B, H-C, H-D have been APPLIED (see
> [PKALS_LONGEVITY_HARDENING.md](PKALS_LONGEVITY_HARDENING.md)). The table now
> carries a **Pre / Post** column pair. M-A, M-B, L-A, and the EXPLAINED/VALIDATION
> merge remain deferred (out of the hardening scope).

| # | Objective | Pre | Post | What moved it (or capped it) |
|---|---|---|---|---|
| 1 | **Architecture preservation** | 6 | **7** | Brittle counts removed/single-sourced (H-B); canonical chokepoint-service refs now CI-guarded against rename (C-1). Capped: env-lever "no ledger" duplication (M-B) still deferred. |
| 2 | **Long-term maintainability** | 5 | **7** | Counts de-duplicated to one self-counting source; the link guard means a rename can't silently orphan docs; core/periphery triage + fan-out cap give a real maintenance model (H-B/C-1/H-D). Capped: EXPLAINED/VALIDATION twin still unmerged (excluded). |
| 3 | **Knowledge-system sustainability** | 5 | **7** | Core-vs-periphery triage + fan-out cap directly defuse the all-or-nothing abandonment trap (H-D). Capped: still ~100 files for one person. |
| 4 | **AI-agent usability after 1 year** | 6 | **8** | Entry instruction fixed + 3 entry docs aligned (H-A); canonical-lookup services + front-door chain now CI-guarded so the lookup stays honest (C-1). Capped: token-budget still unmeasured. |
| 5 | **New-developer onboarding after 1 year** | 6 | **7** | Front-door chain CI-guarded (can't re-fragment); de-numbered docs won't mislead (C-1/H-B). Capped: "read N files" routes still hand-maintained (now link-guarded). |
| 6 | **Documentation drift resistance** | 4 | **7** | The decisive move: rule → mechanism for references/counts/navigation. 100 files link-guarded + ADR contiguity + service refs + front-door chain, all FAIL CI; manual sweep automated (C-1). Capped: prose accuracy + COVERAGE counts still human. |
| 7 | **Future-phase integration (TM-1, MissingPiece, Alter, G1–G7)** | 5 | **7** | All four phases now in BOTH binding matrices with pointers to the per-phase table; the mechanical "which docs" answer now exists (H-C). Capped: phases still need human execution. |

**Composite: 5.3 → 7.1 / 10.**
**Weighted for survival** (drift-resistance + sustainability + future-integration
heaviest, all now 7): **~5.0 → ~7.0 / 10.** The artifact was always ~8; hardening
lifted the **preservation mechanism** from ~4 to ~7 — PKALS now has a machine
backstop for its highest-value invariants and a sustainable maintenance model.

---

## Severity ledger (from the review)

| Severity | Count | Findings |
|---|---|---|
| 🔴 Critical | 1 | C-1 drift-mechanism absent (96/98 unguarded) |
| 🟠 High | 4 | H-A stale AI entry instruction · H-B hard-coded counts duplicated · H-C future phases not in matrices · H-D no core/periphery triage |
| 🟡 Medium | 3 | M-A COVERAGE_REPORT self-contradiction + false 100% · M-B "no ledger until settlement" reversible/duplicated · M-C per-entity fan-out scales super-linearly |
| 🟢 Low | 1 | L-A PROJECT_ATLAS §2/3/4 numbering gap |

## Top recommendations — STATUS (all five applied 2026-06-13)

| # | Action | Fixes | Status |
|---|---|---|---|
| 1 | Extend the existing `DocAccuracyTests` → `PkalsNavigationGuardTests` (link integrity + ADR contiguity + chokepoint service refs + front-door chain) | C-1 | ✅ DONE (4 methods, full core 17/17 green) |
| 2 | Repoint AI_AGENT_GUIDE step-1 to KNOWLEDGE_MAP; align the 3 entry docs | H-A | ✅ DONE |
| 3 | De-number + single-source brittle counts (canonical list in KM §7; others link) | H-B | ✅ DONE (0 brittle counts in live nav surface) |
| 4 | Add MissingPiece/Alter/G1–G7 rows to CHANGE_IMPACT_MATRIX + OWNERSHIP_MATRIX | H-C | ✅ DONE (+4 / +4 rows) |
| 5 | Core-vs-periphery triage + fan-out cap in MAINTAINING_PKALS | H-D, M-C | ✅ DONE |
| — | reconcile COVERAGE_REPORT (M-A) · single-source "no ledger" (M-B) · renumber ATLAS (L-A) · EXPLAINED/VALIDATION merge | M-A/M-B/L-A | ⏸ DEFERRED (out of hardening scope) |

## Survival statement (post-hardening)
PKALS now has a **machine backstop** for its highest-value invariants (references,
counts, navigation) and a **sustainable maintenance model** (core-vs-periphery +
fan-out cap), with future phases **pre-wired** into the binding matrices. For the
guarded surface it is safe to carry 3–5 years: a rename/move/new-phase that would
silently break the load-bearing docs now **fails CI** instead. Residual risk is
inherently-human prose accuracy plus the deferred M-A/M-B/L-A/twin-merge — none
load-bearing. **No new systems were added; the existing guard was extended and the
docs were pruned + triaged.**

### Verification Sources
Same as PKALS_FINAL_REVIEW Verification Sources (direct grep/read on the live tree,
commit f067daf0, 2026-06-13). The 8-lens parallel + adversarial-verify workflow was
curtailed by an API session limit; Critical/High findings were re-verified directly
by the reviewer of record. Confidence: High (C/High), Medium (M-C/H-D analytical).
