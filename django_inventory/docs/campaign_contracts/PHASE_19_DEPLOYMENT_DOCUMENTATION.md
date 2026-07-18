---
id: docs-campaign-contracts-phase-19-deployment-documentation
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 19 Execution Contract — Deployment Documentation

> Authored 2026-07-12 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md), the PHASE_05 documentation architecture (the runbook = a
> `handwritten` T2 canonical — P09 §6.7: never whole-file generated; fenced structural
> sections only via GEN-D9), the PHASE_18 protocol (FFD-D9: features owe runbook-impact
> notes; deployment-doc OWNERSHIP lands here), the PHASE_13 instrument (VER-D8: pre-deploy
> rehearsal + mandatory post-deploy `verify_production`), and the PHASE_14 instrument
> (SYNC-D9: a pre-deploy sweep joins the readiness inputs). Deltas only.
> **This phase is DOCUMENTATION ONLY** — it refreshes and completes the operational
> documentation that Phase 20 will execute verbatim and Phase 21 will attest against.
> Nothing is provisioned, deployed, or executed here.
> Evidence doc (created at DEP-0): `docs/DEPLOYMENT_DOCS_LOG.md`.

## 1. Phase objective

Bring the deployment documentation to campaign truth: refresh the existing owner-approved
runbook (`deploy/README.md`, direction C — single-VPS Docker Compose, Caddy auto-TLS,
gunicorn, Postgres 16.6 + Redis 7.4, nightly restic to B2/R2, restore drill) so it matches
the system the campaign actually built (new apps, new commands, new migrations, the
verification and knowledge instruments, and the uncommitted-tree reality), and complete the
operational documentation set — deployment checklists, rollback documentation, release
documentation, operational ownership — so that Phase 20 can deploy by reading, not by
remembering.

## 2. Scope

### 2.1 Facts of record (authoring-time, verified 2026-07-12; DEP-A censuses fully)

| Fact | Evidence |
|---|---|
| The runbook EXISTS and is owner-approved | `deploy/README.md` (2026-06-11, "direction C"): first-deploy checklist (11 steps incl. **step 8 = the clean-start-vs-dev-dump owner decision, already reserved**), nightly restic backups (7d/4w/6m retention, weekly check, pre-deploy dump via deploy.sh), a from-nothing restore drill ("re-run monthly"), deploys/updates section; companions `deploy/{deploy.sh, backup.sh, Caddyfile, entrypoint.sh}` (entrypoint waits db/redis → migrate → collectstatic → gunicorn) |
| Adjacent operational docs | `docs/ENFORCEMENT_ROLLOUT_RUNBOOK_2026_06_14.md` (the R11 flag-flip procedure — post-deploy, owner-sequenced; U10) · `docs/SOAK_TRACKER.md` (soak evidence log) · `docs/ARCH_READINESS_REVIEW_2026_06_12.md` (the old deployment-gate validation; archives post-soak) |
| The runbook PREDATES the campaign | 2026-06-11 vs the July body of work: it knows nothing of machines/patterns_ai-era state, the campaign's new apps (verification in BASE settings; devseed local-only + its deploy EXCLUSION), phases 16/17 migrations, `verify_production`/`knowledge_sync` steps, or the certificate |
| **The artifact tension (real)** | runbook step 4 = `git clone <repo>` — but the LOCKED order puts Deployment (20) BEFORE First Commit (22), and the entire July system is uncommitted (U2). What Phase 20 transfers to the VPS is NOT decidable from the record → DEP-D2 (cross-references Phase-0's D1 mechanism; the owner may alternatively re-sequence 22 — the order is the owner's to change, never the agent's) |
| Media + secrets reality | `.env` + `media/` are git-invisible (Phase-0 §2.2); the runbook already treats the filled `.env` + restic repo as the disaster-recovery pair (password manager) |
| Enforcement flags | OFF at deploy and beyond, until R11 (U10; owner rollout policy) — the runbook refresh must state this explicitly for the deploy operator |

### 2.2 In / out

**In:** the runbook refresh (campaign deltas) · deployment checklists (pre-deploy / deploy /
post-deploy / rollback — each step numbered, owner-attributable, evidence-noted) · rollback
documentation (triggers deferred to PD-D3; MECHANICS documented here: pre-deploy dump +
restic restore + compose rollback per deploy.sh) · release documentation (what THIS release
contains: the campaign delta summary, migrations list, new commands, new apps, flag state) ·
operational ownership (who runs what, when — per DEP-D7) · deployment knowledge
synchronization (the runbook's Standard metadata + index rows + FFD-D9 duty wiring; a
pre-deploy `knowledge_sync` sweep + `verify_production` rehearsal step WRITTEN INTO the
checklist per VER-D8/SYNC-D9) · a tabletop validation of the whole set against the Phase-20
contract.
**Out:** ANY execution (no provisioning, no deploys, no drills run, no backups triggered —
tabletop only) · application code, tests, battery · the GO decision and evidence pack
(Phase 20/21) · the R11 flag flip (post-campaign; ENFORCEMENT_ROLLOUT_RUNBOOK owns it —
pointer only) · re-sequencing the locked order (DEP-D2 presents options; the owner rules) ·
duplicating procedure into the contracts (the runbook is THE procedure of record; Phases
20/21 reference its sections, never restate them).

## 3. Success criteria

Phase 19 is DONE when ALL hold:
1. The DEP-A census table is complete: every runbook statement classified current /
   stale-with-campaign-delta / owner-decision-needed — counted, with the compose/env-example
   files checked against the campaign's new apps and settings shape.
2. `deploy/README.md` refreshed IN PLACE (one-canonical; DEP-D8): campaign deltas
   incorporated (new apps + devseed exclusion + verification app presence, 16/17 migration
   notes, the flags-stay-OFF statement, the verify_production + sweep steps, the DEP-D2
   artifact ruling), Standard metadata added, step-8 and all owner decisions surfaced as
   explicit checklist gates rather than prose asides.
3. The four checklists exist (pre-deploy / deploy / post-deploy / rollback), each step
   mapping to a runbook section (no orphan steps, no undocumented steps) — proven by the
   tabletop.
4. Release documentation exists for the campaign release (delta summary, migrations,
   commands, apps, flag state, known open items pointer).
5. Operational ownership recorded (DEP-D7): every recurring duty (nightly backup check,
   monthly restore drill, sweep cadence) has a named owner and a written trigger.
6. **Tabletop validation passed:** a full walkthrough of the Phase-20 contract's sub-phases
   against the refreshed docs — every PD-* step finds its runbook/checklist home; gaps fixed
   in the docs before certification (the tabletop is a READING exercise; nothing runs).
7. Zero code changes; battery untouched and NOT re-run; knowledge_sync diff-mode clean over
   the touched docs at close.
8. Handoffs written: Phase 20 (the procedure of record + checklist set) · Phase 21 (the
   runbook/checklist references its evidence spec consumes) · post-campaign ops (cadence
   register). Status + memory synced every sub-phase.

## 4. Rules of engagement (deltas beyond U1–U14 + inheritance)

- **Docs-only, tabletop-only:** no command from the runbook is executed in this phase — not
  a backup, not a compose build, not a DNS check. Verification of procedure = reading +
  cross-reference, not running (execution belongs to Phase 20).
- **The runbook stays the single procedure of record:** checklists and release docs REFERENCE
  its sections; the Phase-20/21 contracts already reference rather than restate — this phase
  must not create a second place where a procedure lives (one-canonical-per-topic).
- **Owner decisions become gates, not prose:** every decision the runbook already reserves
  (step 8) or this phase surfaces (DEP-D2 artifact, DEP-D5 migration window) is written as an
  explicit named gate in the checklists, so Phase 20 cannot drift past one.
- **Secrets discipline:** the refresh never records secret VALUES anywhere; it documents
  WHERE they live (the password-manager pair) and who holds them (DEP-D4).
- This phase's own edits follow the PHASE_18 §6.2 duties (U6, matrix, index rows, diff-mode
  at close) — the protocol self-applies.

## 5. Evidence standard

The census table (runbook line → classification → delta/citation) · the refresh diff summary
with per-delta campaign citations (which contract/log makes each statement true) · the
checklist↔runbook mapping table · the tabletop walkthrough record (PD-* step → doc home →
verdict) · knowledge_sync diff-mode output at close · every owner decision quoted verbatim in
the Design Record. Sub-agent doc sweeps supplemental (U7); the census classifications, the
refresh, the tabletop, and certification = main-thread.

## 6. Methodology

### 6.1 Census first (DEP-A)

Read `deploy/README.md` + the four companion files against campaign reality: settings shape
(base/local/production; verification app in BASE; devseed local-only — the runbook must state
the devseed EXCLUSION explicitly, P12 §6.7), migrations inventory (16/17 additive tables —
entrypoint auto-migrates; DEP-D5 confirms the window posture), `.env.example` completeness vs
every setting the campaign-era code reads, backup scope vs the git-invisible set (Phase-0
§2.2: `.env`, media, DB — the runbook's DR pair already covers them; verify nothing new is
missed), and the artifact question (§2.1). Output: the classified census + the DEP-D decision
inputs.

### 6.2 Refresh + completion (DEP-B/C)

Refresh in place (cited deltas only — the P7 stale-repair discipline: rewrite falsified
spans, never rewrite the document). Add: the release doc (`docs/RELEASE_NOTES_V1.md`-class
per DEP-D8 naming), the four checklists (inside the runbook or beside it per DEP-D8), the
rollback doc (mechanics: pre-deploy dump → restic restore → compose re-pin per deploy.sh;
triggers = PD-D3 placeholder cross-reference), the ops-ownership register, and the
verify/sweep steps at their checklist positions (pre-deploy rehearsal, post-deploy
verify_production, pre-deploy sweep — VER-D8/SYNC-D9 wiring).

### 6.3 Tabletop validation (DEP-D)

Walk the PHASE_20 contract sub-phase by sub-phase; for each step confirm a runbook/checklist
home exists, is current, and names its evidence + its owner gate. Then walk the restore
drill and rollback docs the same way. Gaps → fix in the docs (still this phase's license) →
re-walk. The tabletop record is the phase's central evidence.

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); evidence into the log; **battery never runs**
(docs-only phase; nothing code-adjacent is touchable).

| # | Scope · Key proofs · Stop deltas |
|---|---|
| **DEP-0** — Charter + gate + ratification | Gate: Phase 18 closed (locked order; the doc protocol + instruments exist). Owner answers DEP-D1..DEP-D9 (the artifact ruling D2 may be deferred to PD-0 ONLY by explicit owner note — it blocks Phase 20 either way). Log skeleton. **Stop:** gate fails; D-items unanswered without a deferral note. |
| **DEP-A** — Census | §6.1 classified census + compose/env/settings cross-checks; decision-input tables for the D-items. Read-only. **Stop:** a census finding contradicts a certification or truth-lock (conflict rule). |
| **DEP-B** — Runbook refresh + release doc | §6.2 refresh (cited deltas) + release documentation + flags-OFF statement + devseed exclusion + migration notes. **Stop:** a delta has no campaign citation (nothing enters the runbook on memory). |
| **DEP-C** — Checklists + rollback + ownership | The four checklists (owner gates explicit) + rollback mechanics doc + ops-ownership register + verify/sweep step wiring. **Stop:** a checklist step has no runbook home (either the runbook gains the section or the step is wrong). |
| **DEP-D** — Tabletop + certification + handoffs | §6.3 walkthrough vs the PHASE_20 contract + restore/rollback docs; gap-fix loop; diff-mode clean; U6/index rows; handoffs to 20/21 + the post-campaign cadence register; PHASE-19 VERDICT. **Stop:** an unresolvable gap (a PD step with no possible doc home = a Phase-20 contract defect → dated amendment there, owner). |

## 8. Deliverables

- Refreshed `deploy/README.md` (campaign-true, Standard metadata, owner gates explicit).
- The four deployment checklists · rollback documentation · release documentation · the
  operational-ownership + cadence register.
- The tabletop validation record; `docs/DEPLOYMENT_DOCS_LOG.md` (census · refresh evidence ·
  mapping tables · walkthrough · certification + handoffs).
- Filled Design Record (DEP-D1..DEP-D9); status + memory per sub-phase.

## 9. Files expected to change

**Docs only:** `deploy/README.md` (the refresh — its companion scripts are READ, not edited;
a script found stale = a finding for Phase 20's gate, not a Phase-19 edit: scripts are
executable code) · the release/checklist/rollback/ownership docs (locations per DEP-D8;
default: checklists+rollback inside the runbook, release notes as a new docs/ file) ·
`docs/DEPLOYMENT_DOCS_LOG.md` (new) · `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` ·
`docs/DOCUMENTATION_INDEX.md` (+ START_HERE operational row if DEP-D8 says so) · this file
(Design Record + amendments) · memory files.

## 10. Files that must never change (touching one = STOP + report)

- `deploy/{deploy.sh, backup.sh, Caddyfile, entrypoint.sh}` — executable deployment CODE:
  read + censused here; a needed change = a Phase-20-gate finding with owner approval there
  (or the Phase-4 protocol if it is a defect), never a docs-phase edit.
- ANY application file, settings, `.env`/`.env.example` CONTENT (censused; a gap = a
  documented finding for the PD-0 gate) · migrations · tests.
- `docs/ENFORCEMENT_ROLLOUT_RUNBOOK_2026_06_14.md` (R11 procedure — its own owner process) ·
  truth-locks · the Standard body · generated artifacts (regeneration only, via P18 rules —
  none expected here).
- The PRIMARY dev DB · production anything (nothing exists yet) · the 2 stashes · `.git`
  state (U2 — no git writes of any kind).

## 11. Documentation update rules

At every sub-phase close, same session: (a) log section appended (closed sections
append-only, corrections dated); (b) status-file Phase-19 row + dashboard + "Next action";
(c) PHASE_18 §6.2 self-application: matrix consultation for touched docs, index rows for new
docs, diff-mode disposition at DEP-D; (d) the runbook's Standard metadata + OWNERSHIP_MATRIX
row land with the refresh; (e) owner decisions quoted verbatim in the Design Record the
session they are given.

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-19
bullet: sub-phase closed, census counts, D-item states, log pointer) + MEMORY.md index line
at each sub-phase close. Agents without memory: skip — the log + the refreshed runbook are
the complete binding record.

## 13. Battery policy

**Never runs in this phase.** No code-adjacent file is touchable (§10 keeps even the deploy
scripts read-only). Baseline untouched and NOT re-verified here.

## 14. Regression policy

- The only regression surface = the runbook's existing correctness: guarded by the
  cited-deltas rule (§6.2 — every change carries its campaign citation) and the tabletop.
- The tabletop's PD-step mapping = the forward-regression guard (Phase 20 cannot meet an
  undocumented step).
- knowledge_sync diff-mode at close guards the doc-system integration.
- No pins, no tests (U4 vacuously satisfied).

## 15. Rollback policy

- Doc edits revert per-file (the runbook refresh is one reviewable diff; both sides logged).
- The log + Design Record are append-only (dated amendments).
- Session crash: next session re-reads the log's last closed section, diffs the runbook
  against it, completes or reverts the open span before new work.

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. DEP-0 gate fails or D-items unanswered without an explicit owner deferral note.
3. A deploy SCRIPT needs changing (executable code — Phase-20-gate finding/P4 protocol,
   never here).
4. A runbook delta has no campaign citation, or a census finding contradicts a
   certification/truth-lock.
5. Execution temptation: any urge to "just run" a backup/compose/DNS command to check —
   tabletop only.
6. The DEP-D2 artifact question proves unanswerable without re-sequencing the locked order —
   report the options (Phase-0-artifact transfer · owner re-sequences 22 · other), decide
   nothing.
7. A PD-* step cannot be given a doc home (Phase-20 contract defect → dated amendment there).

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-19 row: which DEP-* is next.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + env) → `deploy/README.md` AS-IS +
   its four scripts (read-only) → PHASE_13 VER-D8 + PHASE_14 SYNC-D9 + PHASE_18 FFD-D9 (the
   inherited duties) → the PHASE_20 + PHASE_21 contracts (the consumers) → this contract →
   `docs/DEPLOYMENT_DOCS_LOG.md` if it exists (absent ⇒ next = DEP-0).
3. Verify read-only: runbook mtime/content vs the log's census; D-item states.
4. Nothing is ever executed from the runbook in this phase.
5. No battery environment needed.
6. Execute exactly ONE sub-phase per §7. STOP per §16.
7. Anything inconsistent across status file / runbook / census / this contract → report
   before working (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (DEP-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| DEP-D1 | Target environment | The runbook's direction C stands (single VPS, India region, 2–4 GB, Docker Compose, Caddy TLS) — owner re-confirms for July-2026 reality (provider, size, region) | _(pending)_ |
| DEP-D2 | **Deployable artifact** | NOT decidable from the record: runbook step 4 assumes committed code, but the locked order deploys (20) before the first commit (22). Options presented, owner rules: (a) transfer the working tree via the Phase-0 mechanism (tarball/rsync/bundle — makes Phase-0 execution a HARD Phase-20 gate), (b) owner re-sequences Phase 22 before 20 (the order is the owner's alone), (c) other owner instruction. Cross-references Phase-0 D1 | _(pending)_ |
| DEP-D3 | Initial production data | The runbook step-8 decision, now formal: START CLEAN (re-enter masters via admin UIs — the runbook's own recommendation; dev DB holds validation rows) vs import the dev dump; if clean: WHO enters what, from which reference doc | _(pending)_ |
| DEP-D4 | Secrets custody | The password-manager pair (filled `.env` + restic credentials) confirmed as the DR pair; custodian named; no secret values in any doc | _(pending)_ |
| DEP-D5 | Migration execution posture | Entrypoint auto-migrate on boot stands (runbook behavior) incl. the 16/17 additive tables; maintenance-window/downtime tolerance stated | _(pending)_ |
| DEP-D6 | Rollback mechanics ratification | Pre-deploy dump (deploy.sh) + restic restore + compose image re-pin = THE rollback mechanism; reverse migrations NOT a rollback path (restore is); triggers = PD-D3 | _(pending)_ |
| DEP-D7 | Operational ownership | Default: the owner operates solo (deploys, backup checks, monthly restore drill, sweep cadence) — named explicitly with each duty's trigger; any delegation recorded | _(pending)_ |
| DEP-D8 | Doc form + locations | Runbook refreshed IN PLACE (one canonical); checklists + rollback section INSIDE it; release notes = new `docs/` file; Standard metadata on all; START_HERE operational row | _(pending)_ |
| DEP-D9 | Post-deploy ops cadence | Monthly restore drill (runbook), nightly-backup confirmation, sweep + verify_production cadence (on-demand + post-deploy per VER-D9/SYNC-D9), R11 sequencing = ENFORCEMENT_ROLLOUT_RUNBOOK's own process (pointer only) | _(pending)_ |

Date · answered by: _(pending)_

## Dated amendments

_(none)_

# Evidence note

All census/refresh/tabletop evidence lives in `docs/DEPLOYMENT_DOCS_LOG.md` (created at
DEP-0) — contract = procedure, log = what was made true (framework hierarchy rule). The
runbook remains the single procedure of record; Phases 20 and 21 read it, execute it, and
attest against it — they never fork it.
