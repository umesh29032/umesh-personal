> **ARCHIVED 2026-06-13** -- PKALS review-cycle artifact (process/history), not living knowledge. Kept for the record; do NOT treat as current. Living docs: docs/LEARNING_2_0/ (START_HERE).

# PKALS v1 — REVIEW FIXES (H1–H4, structural)

> Record of the four mandatory structural fixes applied after the hostile review
> ([PKALS_REVIEW_V1.md](PKALS_REVIEW_V1.md), scored in [PKALS_SCORECARD.md](PKALS_SCORECARD.md)).
> Scope was deliberately bounded: **simplify, de-duplicate, strengthen, reduce
> drift risk. No new systems, no new docs beyond the one router this required.**
> Verified against commit `f067daf0`, 2026-06-12.

---

## H1 — kill fragile line-number verification references

**Defect:** 138 `Lxxx`/`Lxxx–yyy` citations across PKALS, stamped "Verified High".
Any edit to a cited file silently invalidated the citation → confident-but-wrong.

**Fix applied:**
- Stripped **all 138** line-number citations from docs/LEARNING_2_0 (52 files). The
 references that remain are **file path + function/class name** — stable across edits.
- Added a verification **commit stamp** to the confidence footers:
 `(verified against commit f067daf0, 2026-06-12; re-verify the cited file if it
 changed)` — added to **35** footers. A reader/agent now has a concrete "as-of"
 anchor and an explicit re-verify trigger instead of a line number that rots.

**Result:** line citations remaining in PKALS = **0**.

---

## H2 — one invariant = one canonical source

**Defect:** the settlement finalize **lock order** (advisory 5374 → AddaSettlement
→ stage records → WorkerProfile → WorkerAdvance) was spelled out in full across
many docs. One reorder of the lock = a multi-file edit, and any miss = a doc that
teaches a deadlock.

**Canonical chosen:** [CHOKEPOINTS/adda_settlement_service.md](CHOKEPOINTS/adda_settlement_service.md)
(teaching canonical) — with [ARCHITECTURE_V2.md](../ARCHITECTURE_V2.md) §11.5 as the
**binding spec** (the authoritative source of record; intentionally retains the full
chain — it is the spec, not a restatement).

**Copies converted to links:** every other full restatement now points to the
canonical instead of repeating the order —
- [PROJECT_KNOWLEDGE_MAP.md](../PROJECT_KNOWLEDGE_MAP.md) §4
- [DATA_FLOWS/adda_settlement_flow.md](DATA_FLOWS/adda_settlement_flow.md)
- [REQUEST_JOURNEYS/settlement_finalize.md](REQUEST_JOURNEYS/settlement_finalize.md)
- [../LEARNING/02_DATABASE_RELATIONSHIPS.md](../LEARNING/02_DATABASE_RELATIONSHIPS.md) (write-flow STEP 3)
- [../LEARNING/03_TRANSACTIONS_AND_LOCKS.md](../LEARNING/03_TRANSACTIONS_AND_LOCKS.md) (general pattern, points to canonical for the order)
- [../LEARNING/09_SQL_BEGINNER_TO_ADVANCED.md](../LEARNING/09_SQL_BEGINNER_TO_ADVANCED.md) (SQL lesson)

**Result:** the spelled-out chain now lives in exactly **one teaching canonical +
one binding spec**. Everywhere else = a link. Reorder the lock → edit two files,
not the whole tree.

---

## H3 — onboarding discovery: a single entry router

**Defect:** ~10 competing "entry"/"start here"/"primary nav" docs, and the **repo
root README had 0 links into PKALS** — a brand-new developer could not discover the
knowledge system from the repository root.

**Fix applied:**
- Created **[../START_HERE.md](../START_HERE.md)** — one front door, persona-routed:
 **A** new developer · **B** owner/learner · **C** AI agent · plus a "just need one
 answer" row. Each row says *read exactly this, in order, then stop.*
- **Root [README.md](../../README.md) now points to it** (top banner + first row of
 the Doc Map) — discovery works from the repository root.
- Demoted the competing doors in [../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md):
 START_HERE is the single front door; WORK_LOG / DOC_AUDIT / FINAL_PKALS_REVIEW /
 PKALS_REVIEW_* are explicitly labelled **meta/operational, not reader doors** and
 moved out of the "Entry points" table.

**Result:** README → PKALS links = **3** (was 0). One unambiguous front door; the
rest are destinations it routes to.

---

## H4 — eliminate overlapping overview documents

**Defect:** two overview documents — PROJECT_KNOWLEDGE_MAP (business→arch→DB→code)
and PROJECT_ATLAS (which re-explained the same overview in its §1–§4) — split the
front door and duplicated prose.

**Decision:** **[PROJECT_KNOWLEDGE_MAP.md](../PROJECT_KNOWLEDGE_MAP.md) survives as
THE single overview** (it is CLAUDE.md's FIRST-READ and is covered by the
doc-accuracy CI guard). **PROJECT_ATLAS becomes a pointer/index.**

**Fix applied to [PROJECT_ATLAS.md](PROJECT_ATLAS.md):**
- Retitled "the INDEX of the PKALS learning system" (was "start here, navigate
 everywhere") and the header now explicitly says it is **not** an overview and
 points to KNOWLEDGE_MAP + START_HERE.
- Collapsed the duplicated overview prose (§1 project, §2 architecture, §3 business,
 §4 domain) into a **single pointer** to KNOWLEDGE_MAP's matching sections.
- Kept ATLAS's genuine, non-duplicated job: the **section-index into the
 LEARNING_2_0 subdirs** (PROJECT_BRAIN, DATA_FLOWS, REQUEST_JOURNEYS, CHOKEPOINTS,
 ARCHITECTURE_EXPLAINED/VALIDATION, AI_AGENT_GUIDE, LIVING_DOC_SYSTEM) — which
 KNOWLEDGE_MAP does not provide.

**Result:** one overview (KNOWLEDGE_MAP). ATLAS no longer self-declares as an entry
point and carries no duplicated overview prose.

---

## Reassessment of the four watched dimensions

- **Navigation** — one front door + persona "stop here" signals; ATLAS demoted from
 a 55-link switchboard-claiming-to-be-entry to a labelled index. **Improved.**
- **Drift resistance** — the two largest drift surfaces removed (138 line-cites → 0;
 invariant duplication → 1 canonical + commit stamps). **Improved**, but capped:
 the change-impact matrix is still hand-maintained and the CI doc guard still covers
 only 2 files — an automated drift *gate* was **deliberately not added** (would be a
 new system; out of this scope).
- **AI-agent usability** — fewer rot-prone citations, a commit-stamp re-verify
 signal, and one deterministic front door (START_HERE → AI_AGENT_GUIDE).
 **Improved**; token-budget measurement and machine-readable manifests remain open.
- **Maintenance sustainability** — invariant edits drop from many files to two;
 one overview to keep current instead of two. **Improved**; PKALS-LIVE remains a
 rule rather than an automated mechanism (out of scope).

## Explicitly NOT done (out of the "do not expand" boundary)
- No automated drift gate / new CI test (the scorecard's fix #5 / H5).
- No merge of ARCHITECTURE_EXPLAINED + ARCHITECTURE_VALIDATION twins (scorecard #4 /
 H6 residue) — flagged as remaining duplication, not fixed here.
- No new content, models, or systems added.

### Verification Sources
grep counts on docs/ at commit f067daf0, 2026-06-12 (line-cites=0, full lock chain
files=1 canonical + 1 binding spec, README→PKALS=3, ATLAS self-entry claims=0,
commit-stamps=35). See [BEFORE_AFTER metrics in the scorecard](PKALS_SCORECARD.md).
Confidence: High (measured on the live tree).
