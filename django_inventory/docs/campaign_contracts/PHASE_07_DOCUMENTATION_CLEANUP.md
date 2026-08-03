---
id: docs-campaign-contracts-phase-07-documentation-cleanup
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 7 Execution Contract — Documentation Cleanup

> Authored 2026-07-12 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md), **every definition of the parent contract
> [PHASE_05_DOCUMENTATION_FOUNDATION.md](PHASE_05_DOCUMENTATION_FOUNDATION.md)** (tiers,
> typology, ownership classes, lifecycle §6.1.12 incl. the archive/banner rules, metadata core,
> naming/linking laws, KOS:GEN rules, validation dimensions — none restated here), **and the
> execution outputs of Phase 6** ([PHASE_06_DOCUMENTATION_DISCOVERY.md](PHASE_06_DOCUMENTATION_DISCOVERY.md)
> → `docs/DOCUMENT_DISCOVERY_REPORT.md`, whose risk-flagged work queue is this phase's SOLE
> work-source). Process shape = the campaign's permanent implementation protocol
> ([PHASE_04_CONFIRMED_FINDINGS.md](PHASE_04_CONFIRMED_FINDINGS.md) §6.6), adapted for
> documentation: work-queue rows in, single-item-at-a-time, smallest change, per-item evidence,
> terminal states out. **This contract is deltas only.** "The Standard" = `docs/DOC_STANDARDS.md`
> (frozen-v1). Evidence doc (created at DOCCLEAN-0): `docs/DOCUMENT_CLEANUP_LOG.md`.

## 1. Phase objective

Execute the Phase-6 work queue: repair, retrofit, re-route, and archive the documentation
corpus into Standard compliance — **with zero knowledge loss, zero new discovery, and zero
content invention**. At close, every work-queue row is in a terminal state, the corpus passes
the Phase-6 validation instruments re-run clean, the CI-guarded manifest is refreshed and
battery-proven, and Phase 8 receives a clean substrate for graph construction.

## 2. Scope

### 2.1 Work-source discipline

The Phase-6 work queue is the ONLY work-source. A defect noticed mid-cleanup that has no queue
row is NOT worked: it is recorded as a dated Phase-6 amendment candidate in the cleanup log and
reported at session close (PHASE_06 evidence-note rule: "Phase 7 … returns to discovery ONLY
via a dated Phase-6 amendment"). Exception-free.

### 2.2 Change-class taxonomy (every queue row lands in exactly one lane)

| Lane | Definition | Battery | Gate |
|---|---|---|---|
| **Docs-only** | md content/banner/index/metadata/link edits with no test surface | never runs | none |
| **Battery-bearing** | anything `core.tests.PkalsNavigationGuardTests` (or any other test found by the DOCCLEAN-0 census) can see: editing `canonical_manifest.json`, AND **moving/renaming any file the manifest (or another test) references by path** | full sequential battery per U5 | isolated to DOCCLEAN-E |
| **Owner-gated** | REMOVE-LATER deletions (default: NONE this campaign — deletion stays soak-gated post-deploy per DOCUMENT_ARCHIVE_REVIEW), KEEP-family disposition changes, anything truth-lock-adjacent, DOCUMENT_ARCHIVE_REVIEW contradictions | per item | verbatim owner approval in the Design Record before touching |
| **Frozen** | T1 truth-lock CONTENT, closed receipts/evidence CONTENT, `docs/DOC_STANDARDS.md` (owner change-control), `.git` | — | untouchable; only their inbound references are repairable |

### 2.3 Finding-class → handling map (§6 details each)

Stale repairs (incl. **backlog #6 RBAC.md role table** — this phase is its named venue — and
the pre-logged patterns_ai README drift) + wrong-canonical + duplicate resolution → DOCCLEAN-A
· metadata retrofits + ownership corrections → DOCCLEAN-B · broken links + orphans + navigation
(PKALS/PROJECT_BRAIN/AI_AGENT_GUIDE/index) corrections → DOCCLEAN-C · archive moves + banners +
archive index + DOCUMENT_ARCHIVE_REVIEW reconciliation → DOCCLEAN-D · manifest refresh +
manifest-referenced moves → DOCCLEAN-E · generation-boundary preparation → carried as
DOCDISC-F register annotations only (**no KOS:GEN fences are written in Phase 7** — fences
without generators mislead; Phase 9 writes them when generation lands) · **Missing-doc
creation is NOT cleanup** (authoring ≠ repairing): Missing-class rows route per DC-D1.

## 3. Success criteria

Phase 7 is DONE when ALL hold:
1. Every work-queue row terminal: DONE (with per-item evidence) · DEFERRED (venue named:
   Phase 8/9, DC-D1 route, post-soak) · OWNER-DECLINED (verbatim). None silently dropped —
   arithmetic: queue rows in = terminal rows out.
2. **Zero knowledge loss, proven:** file-count ledger across the phase — creations + moves
   balance, deletions = 0 (unless an owner-gated row says otherwise, expected NONE);
   every archived file retains full content + gains banner + archive-index row (both, always —
   parent §6.1.12).
3. **Zero dead inbound links after every move/rename:** each move ships with its same-session
   inbound-reference rewrite (§6.4); the DOCCLEAN-F link audit re-run reports 0 broken links
   corpus-wide.
4. canonical_manifest.json refreshed (stale topics fixed, missing topics added per the queue,
   all paths valid) and **battery green** with arithmetic recorded (manifest work adds no pins
   unless a fix does — expected count = entry baseline).
5. DOCCLEAN-F re-runs the Phase-6 mechanical instruments over the cleaned corpus: links 0
   broken · orphans 0 (or each remaining orphan owner-accepted) · metadata complete for the
   R2-ratified retrofit scope · indexes complete · naming conformant.
6. Backlog #6 struck (row retained per history convention) with pointer to the fix; the
   patterns_ai README drift carry-over cleared from the status file.
7. DOCCLEAN-G certification written: Standard-compliance statement + Phase-8 handoff (graph
   substrate confirmed: mapping-law censuses from DOCDISC-F still valid or re-counted).
8. Status file + memory synced every sub-phase; the cleanup log complete.

## 4. Rules of engagement (deltas beyond U1–U14 + parent + PHASE_04 protocol)

- **Single-item-at-a-time within a session** (PHASE_04 §4 adapted): item N repaired → verified
  → logged before item N+1. Batching exception: mechanical same-shape edits (metadata
  frontmatter blocks; identical banner stamps) MAY be batch-applied per register, but every
  file's diff is individually reviewed before session close and individually logged.
- **Smallest change:** repair = the minimum edit that makes the doc true/compliant. Stale
  repair rewrites the WRONG SENTENCES/TABLE, not the document; a rewrite-the-doc impulse =
  scope growth (stop §16.5). Content statements added during repair must carry a source
  (certification evidence, code file:line, Standard clause) — cleanup never introduces
  uncited claims.
- **Moves are plain `mv`, never `git mv`** — `git mv` stages the rename and violates U2
  (no `git add`). The working tree carries the move; phase 22's commit resolves renames.
- **Append-only receipts:** receipt/evidence/certification docs are moved/banner-stamped only;
  their CONTENT is never edited (U13 analog; parent append-only class).
- **Truth-locks:** content untouchable; only links TO them / stale references ABOUT them are
  repaired elsewhere.
- **Manifest quarantine:** outside DOCCLEAN-E, `canonical_manifest.json` and every file it
  references by path are move/rename-frozen (edit-in-place of a referenced file's CONTENT is
  fine — the guard checks paths). DOCCLEAN-0 produces the manifest-referenced path list +
  greps for any OTHER test reading docs/ paths; that list is taped to every session.
- Generated-document boundaries: none exist yet (first fences arrive in Phase 9); if DOCCLEAN-0
  unexpectedly finds fence markers, stop — that contradicts the record (§16.9).

## 5. Evidence standard

Per work item (PHASE_04 §5 adapted for docs):
1. the queue row (id + class + proposed action) quoted;
2. pre-state (the wrong content/link/location, quoted or path-cited);
3. the change (diff summary; for moves: old→new path + inbound-reference list rewritten);
4. post-state proof (corrected content quoted / link resolves / banner+index row present);
5. source citation for any content statement added (§4);
6. lane + (if battery-bearing) the battery number; (if owner-gated) the approval reference.
Batch items: one evidence block per register batch + the per-file table. Mechanical re-audits
(F): command + raw counts, Phase-6 §5 style. Sub-agent sweeps supplemental (U7); every content
repair and every verdict main-thread.

## 6. Methodology

### 6.1 Stale documents (incl. backlog #6, patterns_ai README)

Repair against the CITED truth: the queue row's evidence names what is true (certification
section, code file:line). Rewrite only the falsified spans; stamp nothing "verified" beyond
what the citation covers; add the doc's metadata block if the file is in the R2 retrofit scope
and gets touched anyway (touch-it-retrofit-it rule — derived from U6's same-session spirit).
RBAC.md #6: the "What each role can do" table is rebuilt from the certified gate matrix
(MGT-A/E/F + worker-cert evidence; PHASE_03 §6.2 for specialist rows once OFF-* closes — if
Phase 3 is not yet executed at repair time, the table states the code-derived matrix and cites
PHASE_03 §2.2 rather than waiting).

### 6.2 Duplicates + canonical corrections

Per queue row: the canonical survivor is the one the Standard's tier rules pick (already
proposed at DOCDISC-E). Non-survivors get the superseded banner naming the survivor and become
archive-candidates (physically moved in D, not A). Every router (index, manifest [E-lane],
guide, START_HERE) is re-pointed to the survivor. Wrong-canonical rows (e.g. the roadmap
pointer, DOCDISC re-verified) = re-point + note.

### 6.3 Metadata retrofits + ownership corrections

Frontmatter blocks added per the R2-ratified scope (ACTIVE tier), fields per the Standard;
mechanically derivable fields (id/type/status from the census row) batch-scripted if desired
(§4 batching rule — scripts run read-diff-review-write from scratchpad, never blind);
judgment fields (owner/scope/anchors/verified) hand-set from the census + OWNERSHIP_MATRIX.
Ownership corrections land in OWNERSHIP_MATRIX (rows added/fixed per the DOCDISC-C register) —
the matrix is a living PKALS doc, extended not replaced (parent §6.1.11).

### 6.4 Moves, banners, links, redirects (the no-knowledge-loss mechanics)

For EVERY move/rename (archive or restructure):
1. inbound census FIRST — grep the filename + known link forms across the census boundary;
2. move via `mv` (§4);
3. banner: `> **ARCHIVED <date>** — superseded by <successor / reason>. Kept for history.`
   stamped at the TOP of the moved file (repo convention, parent §6.1.12);
4. archive-index row added same session (file · what it was · superseded by);
5. every inbound reference rewritten same session — to the successor for content links, to the
   archive path only where the citation is deliberately historical;
6. **no stub/redirect files** — markdown has no redirects and the repo has no stub convention
   (inventing one is out); the banner + archive index + rewritten inbound links ARE the
   redirect strategy. A file that cannot satisfy step 5 in-session does not move that session.
Deletion is not a move: default NONE this campaign (REMOVE-LATER stays owner-gated + soak-gated
post-deploy, DC-D3).

### 6.5 Archive restructuring

Execute the archive-candidate register (already reconciled per-file against
DOCUMENT_ARCHIVE_REVIEW at DOCDISC-E): move SUPERSEDED/ARCHIVE-class actives into
`docs/archive/` subdirs per the existing layout; repair the archive's OWN integrity findings —
missing index rows (12/104 baseline), missing banners (42/104 baseline), the dead
ARCHITECTURE.md pointer; KEEP families untouched; divergences from the review that DOCDISC-E
flagged for the owner are worked only with their Design-Record approval.

### 6.6 canonical_manifest refresh (battery-bearing, DOCCLEAN-E only)

One coordinated session: (a) execute any deferred moves of manifest-referenced files;
(b) edit the manifest per the queue — fix stale canonicals, add missing topics
(machines/patterns_ai/PDD-class gaps from B.2), update paths for (a), bump the version string;
(c) keep `never_modify` / `hard_rules` / `entry` semantically intact unless a queue row cites
Standard authority to change them (money rules in the manifest mirror U8 — changing those
lines = owner-gated); (d) full sequential battery (U5) — expected = entry baseline (no pins);
red = revert the session's manifest+move diff, re-run to green, report (§16.7). The
`/find-canonical` skill + `scripts/pkals_canonical.py` are readers of this file — smoke-check
the script once post-edit (read-only run; it is repo tooling, not app code).

### 6.7 Validation + certification

DOCCLEAN-F re-runs the Phase-6 mechanical instruments (same scripts, preserved from the
discovery evidence) over the cleaned corpus and reconciles: every instrument's before→after
delta must be explained by logged work items (unexplained delta = §16.8). DOCCLEAN-G writes
the certification: queue arithmetic, no-knowledge-loss ledger, Standard-compliance statement,
Phase-8 handoff (graph-readiness re-confirmed), residual register (deferred rows + venues).

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); per-item evidence into the cleanup log;
documentation updates per §11 at close. Battery column is normative.

| # | Scope · Inputs · Outputs · Evidence · Rollback · Regression · Battery · Stop deltas |
|---|---|
| **DOCCLEAN-0** — Validate Phase-6 outputs + work queue | **Scope:** gate check (Phase 6 closed, report complete, verdict present; Phase 5 Standard frozen-v1 transitively); work-queue intake review (every row has class+action+risk flag; ambiguous rows → back to owner/Phase-6 amendment, not guessed); build the **manifest-quarantine list** (manifest-referenced paths + grep for other tests reading docs/ — the DOCCLEAN-E coordination set); create cleanup-log skeleton; owner answers DC-D1..DC-D3. **Inputs:** discovery report, Standard, this contract. **Outputs:** validated queue (accepted/ambiguous split), quarantine list, log skeleton, filled Design Record. **Evidence:** gate proofs + queue census arithmetic. **Rollback:** docs-only. **Regression:** none. **Battery:** never. **Stop:** gate fails; queue rows unclassifiable; DC answers missing. |
| **DOCCLEAN-A** — Canonical + stale-content corrections | **Scope:** stale repairs (incl. **#6 RBAC.md table** per §6.1, patterns_ai README, drifted app READMEs/blurbs per queue) · duplicate resolutions (survivor confirmed, losers banner-stamped as superseded — moves deferred to D) · wrong-canonical re-pointing in md routers (manifest rows deferred to E). **Inputs:** queue rows classed Stale/Duplicate/Wrong-canonical. **Outputs:** repaired docs + updated routers. **Evidence:** §5 per item, citations mandatory. **Rollback:** per-file revert. **Regression:** touched files' outbound links spot-checked. **Battery:** never (quarantine list respected). **Stop:** repair needs uncited content (missing truth source = back to owner/Phase-6); quarantined path implicated. |
| **DOCCLEAN-B** — Metadata + ownership corrections | **Scope:** frontmatter retrofit per R2 scope (batch rule §4) · OWNERSHIP_MATRIX corrections/additions · wrong-tier/wrong-ownership row fixes. **Inputs:** DOCDISC-C registers. **Outputs:** retrofitted files + corrected matrix. **Evidence:** batch table + per-file diff review note. **Rollback:** frontmatter blocks removable cleanly (top-of-file, no content interleave). **Regression:** sample-parse the YAML (mechanical validity check). **Battery:** never. **Stop:** a retrofit would alter content beyond the frontmatter block. |
| **DOCCLEAN-C** — Broken-link + navigation repair | **Scope:** broken-link rows (re-point to canonical/successor; a link whose target genuinely vanished pre-campaign = repair-to-archive or flag) · orphan integration (index/parent-index rows added) · navigation-consistency fixes: read-4-files terminology drift, AI_AGENT_GUIDE table rows, PROJECT_BRAIN indexes, START_HERE/DOCUMENTATION_INDEX gaps (all per queue). **Inputs:** DOCDISC-D registers. **Outputs:** clean nav layer. **Evidence:** per-link before/after resolution. **Rollback:** per-file. **Regression:** re-run link check over touched files. **Battery:** never (manifest rows live in E). **Stop:** quarantined path implicated. |
| **DOCCLEAN-D** — Archive restructuring + banners | **Scope:** §6.5 — physical moves per the archive-candidate register (EXCLUDING quarantined files), §6.4 six-step mechanics per file; archive-index completion; banner back-fill (42/104 baseline); dead archive-README pointer fixed. **Inputs:** DOCDISC-E register + quarantine list. **Outputs:** restructured archive, complete index, zero dead inbound links. **Evidence:** per-move table (old→new · inbound refs rewritten · banner · index row) + file-count ledger. **Rollback:** `mv` back + revert reference edits (log records both sides). **Regression:** link check over every file that referenced a moved doc. **Battery:** never — BY CONSTRUCTION (quarantined files excluded; violating this = §16.6). **Stop:** a move's step-5 inbound rewrite can't complete in-session (file stays put); owner-gated row without approval. |
| **DOCCLEAN-E** — canonical_manifest refresh (BATTERY-BEARING) | **Scope:** §6.6 — the one code-adjacent session: quarantined moves + manifest edit + version bump + full battery + pkals script smoke-check. **Inputs:** queue manifest rows + quarantine list + deferred moves from D. **Outputs:** current manifest, valid paths, battery green. **Evidence:** manifest diff + battery arithmetic (expected = entry baseline; command output quoted). **Rollback:** battery red → revert session diff wholesale → re-run to green → report (§16.7). **Regression:** PkalsNavigationGuardTests green = the regression instrument; `/find-canonical` smoke output. **Battery:** **REQUIRED — the phase's only battery sub-phase.** **Stop:** battery red after revert (baseline itself broken = report); never_modify/hard_rules semantic change without owner gate. |
| **DOCCLEAN-F** — Documentation validation | **Scope:** §6.7 re-audit — Phase-6 instruments re-run corpus-wide; before→after reconciliation per instrument; residual findings classified (owner-accepted orphans etc.). **Inputs:** cleaned corpus + preserved discovery scripts. **Outputs:** validation section of the log (the "after" census). **Evidence:** raw counts + delta explanations. **Rollback:** docs-only (report section). **Regression:** this IS the regression audit. **Battery:** not re-run (no code changed since E; if F finds a needed fix → the fix routes to the owning lane, F re-runs after). **Stop:** unexplained delta (§16.8). |
| **DOCCLEAN-G** — Cleanup certification + Phase-8 handoff | **Scope:** queue arithmetic · no-knowledge-loss ledger (creations/moves/deletions=0) · backlog #6 struck + carry-over cleared · Standard-compliance statement · deferred/declined residual register with venues · Phase-8 handoff (graph substrate + mapping-law censuses re-confirmed) · PHASE-7 VERDICT. **Inputs:** everything. **Outputs:** certification section; status Phase-7 → ✅. **Evidence:** the arithmetic. **Rollback:** n/a. **Battery:** not re-run (E's number stands). **Stop:** unaccounted queue row → back to its lane as dated amendment. |

## 8. Deliverables

- `docs/DOCUMENT_CLEANUP_LOG.md` (NEW at DOCCLEAN-0): validated queue · per-item evidence
  blocks · per-move tables · file-count ledger · validation "after" census · certification +
  handoff. Append-only once sections close.
- Filled Design Record (DC-D1..DC-D3) + any per-item owner-gate approvals.
- The cleaned corpus itself: repaired/retrofitted/re-routed docs, restructured archive,
  refreshed manifest (battery-proven).
- Updated DEPLOYMENT_BACKLOG (#6 struck), status file, memory per sub-phase.

## 9. Files expected to change

**This phase is the campaign's one LICENSED broad-docs-write phase — but strictly
queue-scoped:** any file inside the Phase-6 census boundary MAY change **iff a validated
work-queue row names it** (the queue is the allowlist; §10 lists the exceptions that override
even a queue row). Plus: `docs/DOCUMENT_CLEANUP_LOG.md` (new) ·
`docs/DEPLOYMENT_CAMPAIGN_STATUS.md` · `docs/DEPLOYMENT_BACKLOG.md` (#6 strike) ·
`docs/DOCUMENTATION_INDEX.md` (log row; re-pointing rows per queue) · OWNERSHIP_MATRIX ·
`canonical_manifest.json` (DOCCLEAN-E only) · docs/archive/** (moves/banners/index) · this
file (Design Record + dated amendments) · memory files. **Scratchpad:** batch/validation
scripts + outputs (read-diff-review-write discipline, §6.3).

## 10. Files that must never change (touching one = STOP + report — overrides any queue row)

- ANY application file: code, tests, migrations, templates, settings, media, `.env` — a queue
  row demanding a code change is misfiled (that is Phase-4/certification work; report it).
- T1 truth-lock CONTENT (PDD, ADRs, freeze packages, ARCHITECTURE_V2, PRE_S1_DESIGN_ADDENDUM,
  FACTORY_OPERATIONS_MASTER, REQUIREMENT_REVIEW_STAGE_TRACKING) and `docs/DOC_STANDARDS.md`
  — reference repairs point AT them; their content changes only via ADR/owner change-control.
- Closed receipt/evidence/certification CONTENT (banner/move only, §4).
- `canonical_manifest.json` + quarantine-listed paths outside DOCCLEAN-E.
- The manifest's never_modify/hard_rules semantics without an owner gate (§6.6c).
- `.claude/` tooling · non-DEV data · the 2 stashes · `.git` state (U2; no `git mv`, §4).
- NOTHING is deleted (DC-D3 default: zero deletions this campaign).

## 11. Documentation update rules

At every sub-phase close, same session: (a) cleanup-log sections appended (closed = append-only,
corrections dated); (b) status-file Phase-7 row + dashboard (battery row updates ONLY at
DOCCLEAN-E; docs-sync; memory-sync; carry-overs — patterns_ai drift + #6 cleared when done) +
"Next action"; (c) DOCUMENTATION_INDEX: log row at DOCCLEAN-0 + re-pointing per queue; (d) U6
app-doc lookups: N/A for pure doc repairs; **where a queue row corrects an app README/GUIDE,
that IS the U6 surface — the correction itself is logged, no second sync needed**; (e) backlog
#6 struck at its repair, row retained.

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-7
bullet: sub-phase closed, items done/deferred, battery number at E, log pointer) + MEMORY.md
index line at each sub-phase close. Agents without memory: skip — the cleanup log + status
file are the complete binding record.

## 13. Battery policy

**Exactly one battery-bearing sub-phase: DOCCLEAN-E** (manifest + quarantined moves). There,
full sequential fresh-DB canonical per U5 (9-app then patterns_ai; never `--parallel`/
`--keepdb`); expected count = entry baseline (status dashboard at DOCCLEAN-0 — 1526/1526 at
authoring, phases 2/3/4 may have raised it; no pins expected from doc work). Every other
sub-phase: battery never runs, guaranteed by the quarantine mechanism (§4) — a battery-relevant
surprise outside E is stop condition §16.6, not a battery run.

## 14. Regression policy

- Per sub-phase regression instruments as tabled (§7): touched-file link checks (A/C), YAML
  parse (B), moved-file inbound checks (D), PkalsNavigationGuardTests + skill smoke (E),
  full instrument re-run (F).
- Certified truths and closed certifications are never re-litigated: cleanup makes docs MATCH
  them (evidence-doc-wins rule); a repair that would contradict one = misfiled row (§16.9).
- No pins, no new tests (U4 — doc repairs pin nothing; the battery at E guards the manifest).
- The Phase-6 report itself is never edited by Phase 7 (it is the closed discovery record);
  divergences discovered here become dated Phase-6 amendments (§2.1).

## 15. Rollback policy

- Every item independently revertable (single-item discipline): content edits = per-file
  revert; moves = `mv` back + reference-edit revert (both sides logged); batches = the batch
  register reverses file-by-file.
- DOCCLEAN-E red battery: revert the session's whole diff (manifest + moves), battery to
  green, report — never leave the tree red between sessions.
- The cleanup log + Design Record are append-only (dated amendments, never edits).
- Session crash mid-item: next session re-runs the F-lite check on the item's touched files
  FIRST, reconciles the log's last state, completes or reverts the half-done item before new
  work (PHASE_04 §15 crash rule adapted).

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. DOCCLEAN-0 gate fails (Phase 6 not closed / report incomplete / Standard not frozen-v1) or
   DC-D1..D3 unanswered.
3. A needed repair has no queue row (§2.1 — record as Phase-6 amendment candidate, stop the
   impulse or the session).
4. Owner-gated row without its recorded approval; or a REMOVE-LATER deletion urge (default
   NONE).
5. Scope growth: a "smallest repair" wants to rewrite a document, restructure a tree not in
   the queue, or add uncited content.
6. Battery-relevant surface touched outside DOCCLEAN-E (quarantine breach).
7. DOCCLEAN-E battery red after the session-diff revert (baseline itself broken — report with
   the failure output; do NOT bisect app code, that is not this phase's mandate).
8. DOCCLEAN-F unexplained delta (an instrument moved without a logged cause).
9. A queue row is misfiled (demands app-code change, contradicts a certification/truth-lock,
   or targets frozen content) — report, never execute.
10. Corpus drift from non-campaign activity mid-phase (baseline counts diverge unexplained).

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-7 row: which DOCCLEAN-* is next; battery
   baseline.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + environment) → parent
   [PHASE_05_DOCUMENTATION_FOUNDATION.md](PHASE_05_DOCUMENTATION_FOUNDATION.md) → the Standard
   (`docs/DOC_STANDARDS.md`) → [PHASE_06_DOCUMENTATION_DISCOVERY.md](PHASE_06_DOCUMENTATION_DISCOVERY.md)
   + `docs/DOCUMENT_DISCOVERY_REPORT.md` (the work queue) → this contract → the PHASE_04
   protocol (§6.1 lifecycle shape) → `docs/DOCUMENT_CLEANUP_LOG.md` if it exists (absent ⇒
   next = DOCCLEAN-0).
3. Verify read-only: quarantine list current (re-derive from the live manifest — it may have
   been refreshed already if E closed); file-count ledger vs log; git HEAD vs status file.
4. Identify the next queue rows for the sub-phase from the log's validated-queue section
   (never from memory).
5. No app login needed; DOCCLEAN-E needs only the battery environment (venv + Postgres, per
   framework env facts).
6. Execute exactly ONE sub-phase per §7, items strictly serial. STOP per §16.
7. Anything inconsistent across status file / Standard / discovery report / cleanup log /
   this contract → report before working (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (DOCCLEAN-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| DC-D1 | Missing-doc venue | Missing-class rows are NOT created in Phase 7 (cleanup repairs, it does not author): generation-candidates → Phase 9; handwritten missing docs (unwritten REQUEST_JOURNEYS, PAGES backlog, history_service chokepoint page) → a named later venue per row (Phase 9 where generatable, else the residual register for owner scheduling) | **ACCEPT THE DEFAULT** (owner verbatim 2026-07-13: "Phase 7 performs cleanup only. Missing documentation is never authored during cleanup. Generation-capable documents belong to Phase 9. Residual handwritten documentation remains in the residual register for future owner scheduling.") |
| DC-D2 | Archive scope | The Phase-6 archive-candidate register (already reconciled per-file vs DOCUMENT_ARCHIVE_REVIEW) is the complete move list — DOCUMENT_ARCHIVE_REVIEW families NOT confirmed by Phase 6 do not move | **ACCEPT THE DEFAULT** (owner verbatim: "The Phase-6 archive-candidate register is the complete archive scope. No additional archive candidates are introduced during Phase 7.") |
| DC-D3 | Deletions | ZERO deletions this campaign; REMOVE-LATER rows annotated + deferred post-deploy/post-soak with owner sign-off then (DOCUMENT_ARCHIVE_REVIEW rule carried) | **ACCEPT THE DEFAULT** (owner verbatim: "ZERO deletions during this campaign. REMOVE-LATER remains annotation-only.") |

Per-item owner-gate approvals (added as rows when owner-gated queue items arise):

- **2026-07-13 — Q-0a:** ACCEPT THE DEFAULT for every venue decision (history_service page ·
  AI_PATTERN family index · unwritten journeys · PAGES appetite → Phase-9 where generatable,
  else residual register).
- **2026-07-13 — Q-0b(1):** ACCEPT DEFAULT — "UI_COMPONENTS.md is the live vocabulary.
  Historical UI specification documents remain frozen references."
- **2026-07-13 — Q-0b(2):** ACCEPT DEFAULT — "PRODUCT_INTEGRATION_DESIGN.md remains ACTIVE"
  (removed from the Q-D2 move set).
- **2026-07-13 — Q-0b(3):** ACCEPT DEFAULT — "No AI_PATTERN naming renames during Phase 7.
  Treat the family as an accepted historical style pending a future DOC_STANDARDS
  amendment. Q-D7 therefore becomes moot."
- **2026-07-13 — the 8 owner-gated queue rows:** "I approve all eight owner-gated queue rows
  exactly as proposed" — Q-A4 · Q-C1b · Q-D1 · Q-D2 · Q-D3 · Q-D4 · Q-D6 · Q-D7(moot).

Date · answered by: **2026-07-13 · Owner (Umesh) — full decision pack answered verbatim in
one order; stop §16.2 clear for DOCCLEAN-A.**

## Dated amendments

- **2026-07-13 (owner rulings D-OR-1..7 + permanent guidance, at DOCCLEAN-D):**
  D-OR-1 approve the proposed AI_PATTERN KEEP set; archive only unambiguously-historical
  reports; never archive a living truth source or navigation dependency. D-OR-2 do NOT edit
  frozen truth-locks to complete archival — a move needing a frozen-doc edit leaves the target
  ACTIVE until a future owner change-control session. D-OR-3 foundation-chain + pkals_v2 stay
  ACTIVE (transitional) where frozen inbound depends on them. D-OR-4 design-system working-doc
  archival approved EXCEPT the confirmed KEEP set (DESIGN_SYSTEM_SPEC + UI_COMPONENTS_CATALOG).
  D-OR-5 DAR §3 dated-receipt archival approved where no frozen dependency + no discoverability
  risk. D-OR-6 banner/index backfill only where successor unambiguous; else classify. D-OR-7
  archive-citation relabel only AFTER archive state finalized (no speculative relabel).
  **PERMANENT guidance: Phase 7 maximizes KOS CORRECTNESS, not archived-file count; a doc
  required for navigation / historical traceability / AI discoverability / frozen-truth
  compatibility MAY stay active until a future campaign retires it; integrity > archive
  completeness.** Blocked-only-by-frozen-dependency items = Phase-7 residuals with evidence.
- **2026-07-13 (owner permanent clarification, at DOCCLEAN-0 close):** "Documentation
  Cleanup must never create new knowledge. Its responsibility is only to normalize,
  consolidate, repair, relink, banner, archive, annotate, and organize existing knowledge.
  Any new documentation or new knowledge belongs to its designated future phase." —
  restates/tightens §2.3+DC-D1; binding this phase and any future cleanup-class work.
  Reconciliation note: Q-A3 (worker-cert meta-audit evidence) remains in-scope — it
  CONSOLIDATES existing knowledge (certified verdict + surviving agent-memory detail) onto
  disk per the PHASE_06 Campaign-Approval amendment; it authors nothing new.

# Evidence note

All cleanup evidence lives in `docs/DOCUMENT_CLEANUP_LOG.md` (created at DOCCLEAN-0) —
contract = procedure, log = what was done (framework hierarchy rule). Phase 8 consumes the
DOCCLEAN-G handoff; it never re-cleans (a dirty-substrate discovery in Phase 8 returns here
via a dated amendment, mirroring the Phase-6→7 rule).
