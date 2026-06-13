> **ARCHIVED 2026-06-13** -- PKALS review-cycle artifact (process/history), not living knowledge. Kept for the record; do NOT treat as current. Living docs: docs/LEARNING_2_0/ (START_HERE).

# PKALS — SCORECARD (hostile v1 → post-H1–H4)

> Original scores were deliberately harsh (v1, pre-fix). The **Post-fix** column
> reflects the four structural fixes recorded in [PKALS_REVIEW_FIXES.md](PKALS_REVIEW_FIXES.md).
> Evidence = grep counts on the live tree at commit `f067daf0`, 2026-06-12.

| Dimension | v1 | Post-fix | Why it moved (or didn't) |
|---|---|---|---|
| **Navigation** | 5 | **8** | One front door (START_HERE) with persona "read this, then stop"; ATLAS demoted from entry-claiming switchboard to a labelled index (H3/H4). Residual circular links remain → not a 9/10. |
| **Discoverability** | 5 | **8** | Repo README now links PKALS (3 links, was 0); two overviews collapsed to one + an index — step-0 discovery from the repo root now works (H3/H4). |
| **Architecture Learning** | 7 | **7** | Unchanged — the EXPLAINED/VALIDATION 7-topic duplication was **intentionally not merged** (out of "do not expand" scope). |
| **Debugging Support** | 7 | **8** | Cited entry points no longer rot: 138 line-numbers → function/class names + a commit stamp (H1); DEBUGGING_INDEX symptom→place intact. |
| **AI-Agent Support** | 6 | **7** | 138 rot-prone citations gone; commit-stamp gives a re-verify signal; one deterministic front door → AI_AGENT_GUIDE (H1/H3). Token budget still unmeasured; indexes still prose. |
| **Maintenance Sustainability** | 4 | **6** | Biggest invariant duplication 17→1 canonical (H2) = invariant edits drop from many files to two; one overview to maintain not two (H4). PKALS-LIVE still a rule, not an automated mechanism (out of scope). |
| **Documentation Drift Resistance** | 3 | **6** | Two largest drift surfaces removed: line-cites 138→0, invariant copies 17→1 + commit stamps (H1/H2). Capped at 6: change-impact matrix still hand-maintained, CI doc guard still covers only 2 files — automated gate deliberately **not** added. |

**Composite (unweighted avg): 5.3 → 7.1 / 10.**
**Weighted for owner's goals** (drift + maintenance heaviest): **~5 → ~6.5 / 10.**
The captured knowledge was always solid; the fixes made the SYSTEM around it
single-source and discoverable. The ceiling now is automation (a drift *gate*),
which was intentionally left out of this pruning pass.

---

## Before vs After — measured metrics (commit f067daf0)

| Metric | Before (v1) | After (H1–H4) | How measured |
|---|---|---|---|
| Line-number citations in PKALS | **138** | **0** | `grep -rEo '\bL[0-9]+(-[0-9]+)?\b' docs/LEARNING_2_0` |
| Verification commit-stamps in footers | 0 | **35** | `grep -rl "verified against commit f067daf0"` |
| Files spelling out the full settlement lock chain | **17** | **1 canonical + 1 binding spec** | `grep -rln "advisory 5374 → ADST …"` (excl. archive) |
| Self-declared "overview" documents | **2** (KNOWLEDGE_MAP + ATLAS) | **1** (ATLAS → index) | manual + header grep |
| Repo-root README → PKALS links | **0** | **3** | `grep -c` on README.md |
| Single onboarding front door | **none** (≈10 competing doors) | **1** (START_HERE, README-linked) | START_HERE.md created + linked |
| Canonical-topic verification | n/a | full lock chain confirmed in exactly the 1 canonical (+ §11.5 spec); 0 stray line-cites | re-grep sweep |

## The 5 fixes that would move the needle most (v1 recommendation — status now appended)
1. **Kill line-number citations** (H1) → cite function names; add a last-verified
 commit stamp. **DONE** (138→0, 35 stamps).
2. **One invariant, one home** (H2) → settlement lock-order in ONE doc; rest LINK.
 **DONE** (17→1 canonical + binding spec).
3. **One router, demote the rest** (H3/H4) → single "you are A/B/C → read this"
 page; README links to it; meta docs off the reader surface. **DONE** (START_HERE).
4. **Merge the twins** (duplication) → EXPLAINED+VALIDATION into one "why" doc;
 COVERAGE+FINAL_REVIEW into one. **NOT DONE** — deferred (would expand scope).
5. **Automate one drift check** (H5) → a test that every citation/CHANGE_IMPACT row
 resolves; turn the rule into a gate. **NOT DONE** — deferred (new system).

### Verification Sources
v1 grep counts (entry points≈10, settlement-dup=17, line-cites=138, README PKALS
links=0, atlas outbound=55, EXPLAINED/VALIDATION overlap=7) and post-fix counts
(see Before/After table) on docs/ at commit f067daf0, 2026-06-12.
Confidence: High (measured).
