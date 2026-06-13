> **ARCHIVED 2026-06-13** -- PKALS review-cycle artifact (process/history), not living knowledge. Kept for the record; do NOT treat as current. Living docs: docs/LEARNING_2_0/ (START_HERE).

# PKALS — FINAL ARCHITECTURE & KNOWLEDGE-SYSTEM REVIEW (Phase 2)

> Independent final review. Assumes PKALS is feature-complete, H1–H4 are the new
> baseline, the original architect is gone, and real production development runs
> on top of this for **3–5 years** maintained by a **solo junior**. Companion:
> [PKALS_FINAL_SCORECARD.md](PKALS_FINAL_SCORECARD.md). Scope is bounded:
> recommendations are **prune / consolidate / extend-the-one-existing-guard /
> convention** only — no new systems, no redesign. Verified against commit
> `f067daf0`, 2026-06-13.

---

## Verdict

**PKALS is content-strong and, after H1–H4, well-organised — but its LONGEVITY is
unprotected.** Every durability mechanism it claims (PKALS-LIVE "drift = a bug",
commit-stamps, the change-impact/ownership matrices, the canonical-lookup table)
is a **rule with essentially no machine backstop**: the CI guard touches **2 of 98
files**, and `scripts/check.sh` has **no doc gate at all**. With a solo junior
maintainer and future phases (TM-1, MissingPiece, Alter, G1–G7) on the way, the
default 3–5-year outcome is **silent drift into "confidently wrong"** — which is
worse than no docs, because a future human/AI will *trust* a verified-stamped page
that no longer matches the code.

It survives the 3–5 years **only if** four things happen (all in-scope, none a new
system): (1) the one existing CI guard is extended to assert a few load-bearing
facts + resolve PKALS links; (2) brittle hard-coded counts are de-numbered and
single-sourced; (3) the known future phases are pre-wired into the binding
matrices; (4) a small "must-stay-true core" is designated so the maintainer can
triage instead of abandoning all 98 files. Without these, expect misleading docs
within ~1 year of active development.

## Method & confidence
A survey agent mapped the full tree (file-grounded). The 8 parallel reviewer lenses
and the adversarial-verify pass were **curtailed by an API session limit**, so the
reviewer of record (a) used the completed survey and (b) **directly verified every
Critical/High finding** below against the live tree (grep/read shown in evidence).
Findings rest on reproduced evidence, not the unrun agents. Confidence: High on
C/High items (re-verified), Medium on the two scalability/sustainability judgements
(analytical, not a single grep).

---

## Findings (Critical → Low)

### 🔴 CRITICAL

**C-1 — PKALS-LIVE is a rule, not a mechanism: 96 of 98 files have zero machine backstop.**
*Category: structural-weakness / drift-resistance.*
**Evidence:** `config/core/tests.py` `DocAccuracyTests.SOURCE_DOCS = ('SYSTEM_DESIGN.md','docs/PROJECT_KNOWLEDGE_MAP.md')` — 2 files. It asserts only Django-version string, 3 banned phrases, karigar-is-historical, expense/core installed, permission_service location. **No count invariant, no link integrity, no PKALS subtree.** `scripts/check.sh` gates import-purity, tests, coverage-floor, and three single-writer greps — **no doc/PKALS/link gate.** Commit-stamps, CHANGE_IMPACT_MATRIX, OWNERSHIP_MATRIX, COVERAGE_REPORT denominators are **entirely hand-maintained.** DRIFT_PREVENTION.md / MAINTAINING_PKALS.md describe a "link-integrity sweep (run periodically)" that is **manual and not in check.sh**.
**Long-term risk:** the entire premise ("documentation drift = an architecture bug", CLAUDE rule 12) is unenforced. A solo junior under feature pressure will not run manual sweeps. Drift is not a risk, it is the *default*. Every other finding below is a *symptom* of this one.
**Recommendation (in-scope — extend the guard that already exists, do not build a new one):** add a handful of asserts to the existing `DocAccuracyTests`: (a) the load-bearing counts resolve against code — number of single-writer services, number of `docs/adr/00*.md`, `len(INSTALLED_APPS domain apps)`; (b) a cheap link-resolver that walks markdown links under `docs/LEARNING_2_0/` and fails on a dead relative path. This converts the #1 rule into the cheapest possible gate. **Not a new system:** it is more methods on the one test class already wired into `check.sh`.

### 🟠 HIGH

**H-A — The AI entry doc's first instruction routes agents to the doc H4 just demoted (self-inflicted baseline regression).**
*Category: contradiction / ai-usability.*
**Evidence:** `AI_AGENT_GUIDE/README.md:6` → step 1 is `[../PROJECT_ATLAS.md] — the map` (a link to the demoted index). H4 demoted PROJECT_ATLAS to "the PKALS index (not an overview)" and made PROJECT_KNOWLEDGE_MAP the one overview. `FUTURE_AGENT_WORKFLOW` already points to KNOWLEDGE_MAP, so the three entry docs (START_HERE, AI_AGENT_GUIDE, FUTURE_AGENT_WORKFLOW) now **disagree on what to read first.**
**Long-term risk:** AI agents are a first-class audience; their very first step is now stale. They land on an index expecting an overview, waste reads, and may distrust the routing — defeating the token-saving purpose.
**Recommendation (in-scope, one line):** repoint AI_AGENT_GUIDE step-1 to PROJECT_KNOWLEDGE_MAP (overview) with ATLAS as the secondary index — align the three entry docs on one order.

**H-B — Hard-coded count invariants ("5 chokepoints", "8 apps", "10 ADRs", "4 stages", "~146 routes/55 models/26 services") duplicated 4–9× each, unguarded, and future-phase-fragile.**
*Category: contradiction / maintainability / future-phase.*
**Evidence:** "5 chokepoints / five chokepoint services" asserted in 7 files (AI_AGENT_GUIDE, ARCHITECTURE_VALIDATION, PROJECT_ATLAS, COVERAGE_REPORT, WORK_LOG, NEW_DEVELOPER_FIRST_7_DAYS, **PROJECT_KNOWLEDGE_MAP §7**) — but `find config -name '*_service.py'` returns **25** files; "5" is a curated documentation grouping with no link to code. "10 ADRs / 0001-0010" in 4 files; `docs/adr/00*.md` = exactly 10 today. "8 apps" in 3+. Stage list enumerated despite stages being user-configurable + TM-1 adding a per-stage field.
**Long-term risk:** the moment a count changes — and TM-1 (C-TM convergence), a MissingPiece/Alter case-service, ADR-0011, or a new app *will* change one — **N files become wrong simultaneously and silently.** A reader can't tell which number is canonical.
**Recommendation (in-scope, de-number + single-source):** prefer "the chokepoint services" / "the ADRs" / "the domain apps" over the brittle numeral; where a count is genuinely useful, state it in **one** canonical place (KNOWLEDGE_MAP) and have the others link (the H2 pattern, already proven). Optionally back the 2–3 load-bearing counts with the C-1 guard.

**H-C — Future phases (MissingPiece, Alter, G1–G7) are absent from the binding maintenance matrices; only unenforced prose anticipates them.**
*Category: future-phase-breakage.*
**Evidence:** CHANGE_IMPACT_MATRIX has **one** future-phase row (WorkflowStage→TM-1 field); grep confirms **no row** for MissingPiece, Alter, or G1–G7. OWNERSHIP_MATRIX likewise. The only doc that maps per-phase PKALS work is `FINAL_PKALS_REVIEW.md` lines 41–52 — **prose, wired into nothing.** Future-phase names are scattered as "when built" notes across ~13 files.
**Long-term risk:** when MissingPiece/Alter/G1–G7 land, the *mechanical* "which docs do I update?" answer does not exist; the maintainer must happen to re-read FINAL_PKALS_REVIEW. Given C-1 (no enforcement), the new feature ships and PKALS silently describes a system that no longer exists.
**Recommendation (in-scope, table extension):** add rows for the known phases to CHANGE_IMPACT_MATRIX + OWNERSHIP_MATRIX now, each pointing at FINAL_PKALS_REVIEW's per-phase entry. Converts unenforced prose into the same lookup the maintainer already uses. No new system.

**H-D — No "load-bearing core vs periphery" designation → 98 hand-maintained files is an abandonment trap for a solo junior.**
*Category: abandonment-risk / sustainability.*
**Evidence:** 98 md files; large periphery is pure restatement of code (APPS/×3-per-app = 24 files, URL_ATLAS, COVERAGE_REPORT denominators, DATABASE_GUIDE per-model) that rots on the first model/route/service change. Nothing tells the maintainer which ~10 files MUST stay true vs which may lag.
**Long-term risk:** faced with "update 98 files or none", a solo junior rationally updates none → the whole system is distrusted → abandoned. All-or-nothing maintenance is the classic death of doc systems.
**Recommendation (in-scope, convention in MAINTAINING_PKALS):** explicitly designate the small **must-stay-true core** (KNOWLEDGE_MAP, START_HERE, AI_AGENT_GUIDE, ARCHITECTURE_V2, the chokepoint canonicals, the two matrices) and mark the periphery "verify-on-touch, may lag — re-derive from code when in doubt". Lets the maintainer triage. A header convention, not a new system.

### 🟡 MEDIUM

**M-A — COVERAGE_REPORT contradicts itself and claims "100%" while parts are 0%.**
*Category: contradiction / misleading.*
**Evidence (same file):** GAP REPORT says "all 12 journeys, all 7 data flows, all 5 chokepoints v2"; the "thin areas" section 8 lines up says "10 of 12 request journeys; 6 of 7 data flows … Chokepoint v2 traces — 1 of 5 (4 pending)". Header "Overall = 100% of PKALS (v1)" while Django pages are 0/14 and per-model pages "not started".
**Long-term risk:** a coverage report that lies about coverage is worse than none — a future maintainer reads "100% / all done" and skips real gaps. It also models "stamp it done" behaviour that infects the rest.
**Recommendation (in-scope):** reconcile the numbers or convert COVERAGE_REPORT to an explicit "snapshot, may lag — counts are approximate" note and drop the "100%" claim. It is already off the reader front-door surface (good); finish neutering it.

**M-B — "no ledger until settlement" asserted in 7 files but reversible by the `LEDGER_CREDIT_AT_ALLOCATION` env lever, unguarded.**
*Category: contradiction.*
**Evidence:** the Option-B / settlement-first assertion appears in ~7 files (APPS/expense/APP_FLOW, ARCHITECTURE_EXPLAINED 02/06/10, ARCHITECTURE_VALIDATION, PROJECT_BRAIN CHANGE_HISTORY_MAP + DECISION_GRAPH). CLAUDE.md documents `LEDGER_CREDIT_AT_ALLOCATION=True` as a rollback lever that flips this behaviour.
**Long-term risk:** if the lever is ever flipped for rollback, 7 prose assertions become false at once with no guard. Lower probability (default is settlement-first; flipping is deliberate) but a 7-file blast radius.
**Recommendation (in-scope):** single-source the claim (one canonical statement that names the lever as the switch; others link), so a flip is a one-file edit.

**M-C — PKALS's per-entity fan-out (app×3 + per-model + per-flow) scales super-linearly; G1–G7 will outgrow it.**
*Category: scalability.*
**Evidence:** today 8 apps × 3 files (APP_FLOW/REQUEST_MAP/FILE_MAP) + 10–11 per-model DB pages + per-flow pages, plus 3 PROJECT_BRAIN indexes that must list every feature. Adding app #9 / model #56 / stage #5 means touching the new triplet **and** every count **and** every index.
**Long-term risk:** the structure manageable at today's surface becomes unmaintainable at the 2–3× surface G1–G7 implies; the indexes (FEATURE/SEARCH/DEBUGGING) are the first to fall behind, and once an index is stale it's actively misleading.
**Recommendation (in-scope, convention):** cap the fan-out — new apps/models get **one** file until they are load-bearing (not the full triplet), documented as a rule in MAINTAINING_PKALS. Keeps growth linear. No redesign of existing pages.

### 🟢 LOW

**L-A — PROJECT_ATLAS section numbering has a 2/3/4 gap (residue of the H4 collapse).**
*Category: cosmetic-structural.*
**Evidence:** `grep '^## '` PROJECT_ATLAS → sections 0, 1, 5, 6, 7, 8, 8b, 8c, 9, 9b, 9c, 9d, 10 — **2, 3, 4 missing** because H4 collapsed the old §1–§4 overview into a single §1 pointer.
**Long-term risk:** minor; signals "half-edited" to a careful reader and invites "is something missing here?".
**Recommendation (in-scope, trivial):** renumber sequentially next time ATLAS is touched. Cosmetic — do not prioritise over C/High.

---

## What I did NOT flag (kept out of scope, deliberately)
- Merging ARCHITECTURE_EXPLAINED + ARCHITECTURE_VALIDATION (the H6 twin residue): real duplication, but merging them is a content reorganisation bordering on redesign — out of "do not redesign". Left as known debt in the scorecard, not a Phase-2 action.
- Building an automated doc-generation pipeline, a docs site, or a CI doc-coverage system: all would materially help, all are **new systems** → explicitly out of scope. C-1's recommendation is deliberately the *minimum* guard extension, not a pipeline.
- Cosmetic/style/wording nits across the 98 files: ignored per instruction.

## Bottom line for the owner
The knowledge is good and the navigation is now clean. The thing that decides
whether PKALS is an asset or a liability in 3–5 years is **enforcement + triage**,
not more content. Do C-1 (one test extension) and H-A (one-line repoint) first —
they are cheap and high-leverage — then H-B/H-C/H-D as consolidation passes. Stop
adding pages.

### Verification Sources
config/core/tests.py (read), scripts/check.sh (read), `find config -name '*_service.py'`,
`ls docs/adr/00*.md`, grep sweeps for "5 chokepoint"/"10 ADRs"/"8 apps"/future-phase
names across docs/, COVERAGE_REPORT.md (read), AI_AGENT_GUIDE/README.md:6 (read),
PROJECT_ATLAS.md headings (read). Commit f067daf0, 2026-06-13. Confidence: High on
Critical/High (re-verified), Medium on M-C/H-D (analytical).
