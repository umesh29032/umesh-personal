---
id: docs-campaign-contracts-phase-18-future-feature-documentation-updates
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 18 Execution Contract — Future Feature Documentation Updates

> Authored 2026-07-12 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md), the ENTIRE PHASE_05 documentation architecture (tiers, typology,
> ownership classes, lifecycle, metadata, mapping laws, one-canonical-per-topic, fences —
> [PHASE_05_DOCUMENTATION_FOUNDATION.md](PHASE_05_DOCUMENTATION_FOUNDATION.md), none
> restated), the pipeline mechanics of Phases 6–9
> (census/cleanup/graph/generation — esp. **PHASE_09's regeneration workflow: fix source →
> rebuild graph → regenerate**, and its battery-bearing manifest-regeneration class), the
> **PHASE_14 knowledge_sync instrument** (whose handoff DEFINES this phase's close condition:
> "Phase 18 closes when a full sweep is BLOCKER/WARN-clean or acceptance-listed by the
> owner"), the per-wave documentation discipline already embedded in the feature contracts
> (P15 §11 · P16 §11 · P17 §11: U6 same-session, PDD amendment entries, spec amendments,
> diff-mode dispositions), and the **PHASE_04 permanence precedent** (a contract may BE a
> permanent protocol). Deltas only.
> **Owner designation (2026-07-12): this contract is the campaign's PERMANENT
> feature-documentation protocol** — every future feature (campaign phases 15–17 at
> execution, and all post-campaign product work) follows §6's lifecycle; later work states
> only deltas. A pointer enters `docs/DOC_STANDARDS.md` via its own dated amendment process
> (FFD-D1).
> Evidence doc (created at FFD-0): `docs/FEATURE_DOC_SYNC_LOG.md`.

## 1. Phase objective

Two inseparable jobs: (a) **codify the permanent protocol** by which every future feature
stays documentation-complete — what must exist before coding, during coding, before a wave
closes, and after implementation, with ownership, validation, and acceptance gates all named;
and (b) **execute the first run of that protocol** as the reality-sync for the feature arc:
after phases 15–17 ship, bring the PDD amendment register, feature docs, URL cards, graph,
generated artifacts, and every matrix/index into truth — closing on a knowledge_sync full
sweep that is BLOCKER/WARN-clean or owner-accepted. After this phase, "the docs lag the
product" is a detected, routed, owned condition — never an ambient state.

## 2. Scope

### 2.1 Facts of record (authoring-time; FFD-0 re-verifies)

| Fact | Evidence |
|---|---|
| The law already exists | U6 + CLAUDE.md rule 12 + PKALS-LIVE ("drift = an architecture bug") + CHANGE_IMPACT_MATRIX (changed-file → docs) + the `/impact` skill — this phase CODIFIES and completes; it does not invent the obligation |
| The instrument already exists (by contract) | knowledge_sync (P14): diff-mode per wave, full sweep with BLOCKER/WARN/INFO + owning-venue routing, visible acceptance lists — named the Phase-18 enforcement instrument in its own §6.6 |
| The repair venues already exist (by contract) | docs repairs = U6/P7-style at the owning doc · generated artifacts = the P9 regeneration runbook (commands printed by sync) · graph = the P8 builder · code-side findings = the P4 protocol/U12 · spec/registry mismatches = dated amendments at owning contracts |
| The feature contracts already embed the per-wave duties | P15/P16/P17 §11: app README/GUIDE per wave, PDD amendment entries at charter, P11 spec amendments for scenarios, diff-mode dispositions per wave close — Phase 18's lifecycle GENERALIZES what they instantiate |
| Feature-close docs duty is already declared | PHASE_05 §6.1.19 (phases 15–17 row): "a new feature ships with its feature doc + cards + PDD/ADR routing — docs-complete is part of feature-DONE" |
| Roadmap ambiguity (real) | the roadmap of record (IMPLEMENTATION_ROADMAP_PDD_V1) is "superseded for current state by MANUFACTURING_V1_FREEZE"; the freeze package is a truth-lock — WHICH planning doc the 15–17 reality-sync updates is not decidable from the record → FFD-D3 |
| Battery exposure | this phase is docs-side EXCEPT the P9-class manifest regeneration (CI-guarded) — exactly one battery-bearing step class, isolated (DOCCLEAN-E/GEN-D precedent) |

### 2.2 In / out

**In:** the §6 protocol (permanent) · the 15–17 reality-sync executed AS that protocol's
first run: stale-census via a full knowledge_sync sweep → work queue → repairs at owning
venues → graph rebuild + regeneration where stale → registers/matrices/indexes current →
close-sweep · the protocol's acceptance demonstration (one shipped feature walked through
the checklist end-to-end) · handoffs (P19 doc duties; P22 pre-checkpoint sweep already
mandated by P14).
**Out:** implementing/altering any feature (15–17 are closed by their own contracts before
this runs) · generating NEW documentation classes (targets = GEN-D9 amendments at P9) ·
editing PDD BODY / ADRs / freeze packages / the Standard (amendment registers + change-
control only) · new detectors or sync behavior (P14 amendments) · repairing code-side
findings (P4 protocol) · touching tests/battery outside the one manifest-regeneration class
· inventing planning-doc structure (FFD-D3 owner call).

## 3. Success criteria

Phase 18 is DONE when ALL hold:
1. **The protocol is codified** (§6), owner-ratified, and pointed to from the Standard via
   its dated amendment (FFD-D1) — every lifecycle stage with its mandatory artifacts, owner,
   validation, and gate named; nothing left as folklore.
2. **The reality-sync is complete:** the FFD-A sweep's every finding is repaired at its
   owning venue, regenerated, or owner-accepted (visible acceptance list) — arithmetic:
   findings in = dispositions out.
3. Post-sync truth state proven: every 15–17 route has its URL card (one-card-per-URL law) ·
   feature docs exist per the R3 taxonomy for the shipped features · the graph validates and
   its census floors include the new routes/models/services · generated artifacts carry
   current graph hashes · OWNERSHIP_MATRIX + DOCUMENTATION_INDEX + GUIDEs current · the PDD
   amendment register entries for 15–17 verified + cross-linked (D5) · the FFD-D3-ruled
   planning doc synced.
4. **The close-sweep is green:** a full knowledge_sync sweep BLOCKER-clean and WARN-clean or
   owner-accepted (the P14-defined close condition, quoted in evidence with the report
   body-hash).
5. **The acceptance demonstration passed:** one shipped feature (owner picks from 15–17)
   walked through the §6 checklist end-to-end with every artifact located and cited — the
   protocol proven executable, not just written.
6. Zero application-code changes; battery untouched EXCEPT the isolated manifest-regeneration
   step (arithmetic recorded there; expected = entry baseline); every regeneration
   deterministic (byte-stable double-run, P9 law).
7. Handoffs written: P19 (deployment-doc duties fold into this lifecycle — D9) · P22 (the
   pre-checkpoint sweep obligation restated with this phase's acceptance-list state) ·
   post-22 permanence adaptation confirmed (D7).
8. Status file + memory synced every sub-phase.

## 4. Rules of engagement (deltas beyond U1–U14 + inheritance)

- **The sweep is the census (no parallel discovery):** FFD-A's work queue comes from the
  knowledge_sync full sweep + the feature contracts' own §11 records — not from ad-hoc
  re-reading (the P7 queue-only discipline applied to feature-doc sync). An off-queue defect
  = a dated amendment to the owning phase's record, per standing rules.
- **Repairs at owning venues only:** doc content repairs edit the OWNING canonical
  (cited-truth spans, P7 §6.1 discipline) · generated content is NEVER hand-fixed (regenerate
  or fix source — P9 law) · fences untouchable by hand · code-side findings routed out (P4),
  never fixed here.
- **Regeneration authority:** this phase RUNS the P8 rebuild + P9 regeneration commands the
  sync report prints — that is its licensed execution surface (the human/agent the
  detect-don't-repair law defers to). Manifest regeneration = the battery-bearing step,
  isolated in its own session-wave with the quarantine discipline (P7/P9 precedent).
- **Protocol fidelity in its own execution:** this phase's doc edits themselves follow §6
  (U6 same-session, matrix consultation, index rows) — the protocol eats its own cooking.
- One venue-class wave at a time (serial discipline); acceptance decisions = owner-attributed,
  visible, never silent (P14 rule).

## 5. Evidence standard

The sweep reports (pre + post, body-hashes quoted) · the work-queue table (finding → venue →
disposition → evidence link) · per-repair cited-truth notes (P7 §5 style) · regeneration
evidence (commands + determinism double-run hashes; battery arithmetic at the manifest step)
· the truth-state proofs of §3.3 (counted: routes vs cards, features vs docs, graph floors)
· the acceptance-demonstration walkthrough (checklist stage → artifact path → citation) ·
the DOC_STANDARDS amendment quoted with owner approval. Sub-agent sweeps supplemental (U7);
dispositions, acceptance decisions, the demonstration, and certification = main-thread.

## 6. Methodology — THE PERMANENT FEATURE-DOCUMENTATION PROTOCOL

Normative for every future feature. Stages gate each other; artifacts name their owners
(PHASE_05 ownership classes bind throughout). "Wave" = a campaign sub-phase session now, a
working session/PR post-22 (D7 adaptation).

### 6.1 BEFORE coding (the charter stage — nothing product-shaped starts undocumented)

Mandatory artifacts: **the PDD change-control entry** (amendment register/ADR ref — the
P15/16/17 precedent: an unanswered charter blocks the feature) · **the execution contract or
post-campaign equivalent** (Design Record for every owner decision; unknowns never defaulted)
· **the feature slug** reserved in the R3 taxonomy (the graph/features layer key) · **the
dataset scenario decision** (a `seed_feature <slug>` P11 amendment, or an explicit
not-needed note) · **the change-impact pre-read** (`/impact`-class matrix consultation of the
intended surface — know the doc blast-radius before the first edit). Owner of this stage:
the feature's charter owner (the product owner).

### 6.2 DURING coding (per wave — the U6 law, instrumented)

Every wave that changes files: **same-session U6** — app README (business view) + app GUIDE
rows (every new file) + every CHANGE_IMPACT_MATRIX-mapped doc updated or N/A-stated ·
**knowledge_sync diff-mode at wave close** (findings dispositioned or carried with reason —
a BLOCKER never carries) · **fence discipline** (generated sections never hand-edited; a
needed change goes source→rebuild→regenerate) · new docs get Standard metadata + an index/
parent-index row at birth (no orphans). Owner of this stage: the implementing agent; the
wave's evidence log records the dispositions.

### 6.3 BEFORE wave/feature merge-equivalent (the completeness gate)

A wave closes only when: diff-mode is BLOCKER-clean (WARNs dispositioned) · GUIDE/README
current · new URLs noted for card generation · tests/battery per the owning contract.
Post-22: this gate runs pre-commit — docs travel IN THE SAME COMMIT as the code they
describe (the U2-era "same session" becomes "same commit", D7).

### 6.4 AFTER implementation (the feature-close stage — docs-complete IS feature-DONE)

In order: **graph rebuild** (P8 builder; validator green) → **regeneration** (P9: url-cards
for every new route — one-card-per-URL; feature doc for the slug; touched fenced sections;
manifest-view regen where topics changed = the battery-bearing step) → **registers current**
(OWNERSHIP_MATRIX rows for new docs · DOCUMENTATION_INDEX/START_HERE routing where a new
surface warrants it · the FFD-D3 planning doc entry · dataset spec + verification-registry
amendments if the feature touched scenarios/invariants) → **ADR rule:** any durable
architectural decision the feature locked gets its own ADR (append-only, supersede-not-
rewrite; doc files never lock decisions — P05 §6.1.7) → **the certification sweep:** a full
knowledge_sync sweep BLOCKER/WARN-clean or owner-accepted = the feature's documentation
acceptance gate. Owner of this stage: the feature's closing agent; the acceptance decision:
the owner.

### 6.5 Rollback documentation (features that retreat)

A reverted wave reverts its doc deltas in the same diff (docs travel with code BOTH
directions). A withdrawn/superseded FEATURE: its docs are never deleted — feature doc +
cards get supersession banners with the successor/withdrawal note (P05 lifecycle), the graph
rebuild drops/marks its nodes per schema rules, the PDD register records the withdrawal via
change-control, and a sync sweep confirms no orphaned references.

### 6.6 Ownership summary (who updates what)

Per PHASE_05 typology: app README/GUIDE = the implementing agent, same session · PDD
register/ADRs = the owner via change-control · feature docs + url-cards + manifest-view =
GENERATED (nobody hand-edits; the closing agent triggers regeneration) · graph = rebuilt,
never edited · OWNERSHIP_MATRIX/indexes = the agent whose change created the row-need ·
acceptance lists = the owner, attributed · this protocol itself = frozen contract; changes =
dated amendments here + the Standard's pointer stays current.

### 6.7 The 15–17 reality-sync (this phase's first-run execution)

The protocol's §6.4 stage executed retroactively for the shipped feature arc, driven by the
FFD-A sweep: repairs → rebuild → regeneration → registers → close-sweep, per the sub-phase
table. (If phases 15–17 executed cleanly under their own §11 duties, this sync is small —
the sweep tells the truth either way.)

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); evidence into the log; battery ONLY at the
manifest-regeneration step.

| # | Scope · Key proofs · Stop deltas |
|---|---|
| **FFD-0** — Charter + gate + ratification | Gate: Phase 17 closed (the feature arc exists to sync; transitively the pipeline + instruments live). Owner ratifies FFD-D1..FFD-D9 (incl. the D3 planning-doc ruling + the D1 Standard-amendment). Log skeleton. **Stop:** gate fails; any FFD-D unanswered. |
| **FFD-A** — The census sweep | Full knowledge_sync sweep (pre-state, body-hash recorded) + the feature contracts' §11 records cross-checked → the typed work queue (finding → owning venue → proposed disposition). NO repairs yet. **Stop:** sweep BLOCKERs indicating hand-edited fences or truth-lock contradictions (owner before proceeding — those are incidents, not queue rows). |
| **FFD-B** — Owning-venue repairs (docs-only) | Execute the queue's doc-side rows: cited-truth span repairs at owning canonicals, register/matrix/index rows, PDD-register verification + cross-links (D5), the D3 planning-doc sync. P7 discipline throughout (append-only receipts, banners not deletions, no off-queue work). **Stop:** a repair needs uncited content or an owner ruling; a code-side finding tempts an inline fix (→ P4/U12). |
| **FFD-C** — Rebuild + regeneration (manifest step battery-bearing) | P8 graph rebuild + validator green → P9 regeneration for stale/missing artifacts (cards for 15–17 routes, feature docs, fenced sections) with determinism double-runs → the manifest-view regen AS ITS OWN ISOLATED WAVE with full battery (expected = entry baseline). **Stop:** validator red (fix-at-source routing); determinism failure; battery red after the revert procedure (P9 §16 rules apply verbatim). |
| **FFD-D** — Protocol acceptance demonstration | Walk one owner-picked shipped feature through §6.1–6.4 end-to-end: locate + cite every mandatory artifact; gaps become queue rows (loop to B/C once); the demonstration table is the protocol's executability proof. **Stop:** a checklist stage has no locatable artifact class (protocol defect → dated amendment here, owner). |
| **FFD-E** — Close-sweep + certification + handoffs | Full knowledge_sync sweep (post-state): BLOCKER/WARN-clean or owner-accepted (visible list) — the P14-defined close condition; queue arithmetic (in = out); §3.3 truth-state counts; the DOC_STANDARDS pointer amendment recorded (D1); P19/P22/post-22 handoffs (D7/D9); PHASE-18 VERDICT + **the permanence declaration** (this protocol governs all future feature work). **Stop:** unaccounted finding; close-sweep not clean and not accepted. |

## 8. Deliverables

- **The permanent protocol** (§6, ratified) + its DOC_STANDARDS pointer amendment.
- The completed 15–17 reality-sync: repaired canonicals, rebuilt graph, regenerated
  artifacts (incl. cards for every feature-arc route), current registers, verified PDD
  entries, the synced planning doc.
- The acceptance-demonstration record; the pre/post sweep reports (hashes) + the visible
  acceptance list.
- `docs/FEATURE_DOC_SYNC_LOG.md`: ratifications · queue + dispositions · repair/regeneration
  evidence · demonstration · certification + handoffs.
- Filled Design Record (FFD-D1..FFD-D9); status + memory per sub-phase.

## 9. Files expected to change

**Docs (queue-scoped, P7-style license):** owning canonicals named by queue rows · app
READMEs/GUIDEs (verification-level touch-ups only — the features' own phases did the heavy
lifting) · OWNERSHIP_MATRIX · DOCUMENTATION_INDEX / START_HERE rows · the D3 planning doc ·
the PDD amendment register (verification/cross-links via change-control) ·
`docs/DOC_STANDARDS.md` Design-Record/amendment section ONLY (the D1 pointer, per its own
process) · `docs/FEATURE_DOC_SYNC_LOG.md` (new) · status file · this file (Design Record +
amendments) · memory. **Generated (via tooling only):** `knowledge_graph.json` (rebuild) ·
`docs/features/**` + fenced sections + `canonical_manifest.json` (regeneration; manifest =
the battery step). **Nothing hand-written lands in any generated artifact.** NO application
files, NO tests, NO scripts.

## 10. Files that must never change (touching one = STOP + report)

- ANY application file (code/tests/migrations/templates/settings/`.env`) — code-side findings
  route to P4/U12.
- PDD BODY · ADR bodies (new ADRs append; existing never rewritten) · freeze packages · T1
  truth-locks · the Standard's BODY (pointer via amendment section only).
- Generated artifacts BY HAND (rebuild/regenerate only — the cardinal fence law) · the P8
  builder / P9 generators / P12–P14 engines themselves (their changes = their own contracts'
  amendments).
- Closed phase logs (dated amendments per their own rules) · acceptance lists never edited
  silently.
- The PRIMARY dev DB · non-DEV data · scratch worlds it didn't create · the 2 stashes ·
  `.git` state (U2 — reads only for diff-mode).

## 11. Documentation update rules

At every sub-phase close, same session: (a) log section appended (closed sections append-only,
corrections dated); (b) status-file Phase-18 row + dashboard (battery row updates ONLY at the
manifest step) + "Next action"; (c) this phase's own edits obey §6.2 verbatim
(matrix-consulted, indexed, metadata-borne — the protocol self-applies); (d) the D1 Standard
amendment + D3 planning-doc entry + PDD-register cross-links recorded at their owning
documents per those documents' own rules; (e) acceptance-list changes always owner-attributed
and dated.

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-18
bullet: sub-phase closed, sweep states, queue arithmetic, log pointer; at FFD-E the
permanence declaration) + MEMORY.md index line at each sub-phase close. Agents without
memory: skip — the log + the sweep reports (quoted) + the owning registers are the complete
binding record.

## 13. Battery policy

**Docs-side phase: battery never runs — with exactly one exception:** the manifest-view
regeneration wave inside FFD-C (CI-guarded artifact; full sequential fresh-DB battery per U5;
expected = entry baseline, no pins; red ⇒ revert the regeneration diff → green → report —
the P9 GEN-D procedure verbatim). Graph rebuilds and features-tree regeneration have no test
surface (battery not triggered). Arithmetic recorded at the one step.

## 14. Regression policy

- The pre/post sweep pair is the phase's regression instrument (every delta explained by a
  logged disposition — the P7 DOCCLEAN-F rule).
- Regeneration determinism double-runs guard the generated layer; the validator guards the
  graph; PkalsNavigationGuardTests guards the manifest (at the battery step).
- Certified truths, closed certifications, and shipped-feature behavior are inputs — a doc
  found contradicting them is repaired TO them (evidence-doc-wins), and a doc found
  CORRECTLY describing broken behavior routes the code-side finding out (P4/U12), never
  "fixes" the doc to match a bug.
- No pins, no tests (U4 — the one battery step adds none).

## 15. Rollback policy

- Doc repairs revert per-file (cited spans, both sides logged); register rows revert cleanly.
- Regenerated artifacts are disposable (re-run = rollback); the manifest step reverts
  wholesale on red (P9 rule).
- The graph re-rebuilds from sources at any time (P8 disposability).
- The log + Design Record + acceptance lists append-only (dated amendments).
- Session crash mid-wave: next session re-runs diff-mode over the touched set FIRST,
  reconciles the log, completes or reverts the half-done row before new work.

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. FFD-0 gate fails (Phase 17 not closed) or any FFD-D1..D9 unanswered.
3. Sweep BLOCKERs of the incident class (hand-edited fence, truth-lock contradiction) at any
   point — owner before proceeding.
4. Off-queue repair temptation; an inline code-side fix temptation (P4/U12 routing).
5. Any hand-edit to a generated artifact, the graph, or the manifest outside the licensed
   tooling runs.
6. The manifest-step battery red after revert; a regeneration determinism failure surviving
   one source-side fix routing.
7. A protocol checklist stage proves un-executable at FFD-D (protocol defect → dated
   amendment, owner).
8. The close-sweep is neither clean nor owner-accepted (the phase cannot self-certify past
   its own gate).
9. A needed policy has no repository basis and no FFD-D slot (report; never invent).

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-18 row: which FFD-* is next.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + env) → the parent PHASE_05 → the
   Standard → PHASE_09 §6.6 + PHASE_14 §6.3/§6.6 (regeneration + sweep mechanics) → this
   contract FULLY (§6 = the protocol) → `docs/FEATURE_DOC_SYNC_LOG.md` if it exists
   (absent ⇒ next = FFD-0).
3. Verify read-only: the graph validates (hash check) before trusting any generated state;
   the last sweep report's body-hash vs the log; queue state vs dispositions.
4. Never hand-edit generated content to "quickly finish" a row — regeneration or
   source-repair only.
5. Battery environment needed ONLY for the manifest step (framework env facts).
6. Execute exactly ONE sub-phase per §7. STOP per §16.
7. Anything inconsistent across status file / sweep reports / queue / registers / this
   contract → report before working (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (FFD-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| FFD-D1 | Protocol home | THIS CONTRACT is the permanent protocol (PHASE_04 precedent); a pointer row enters `docs/DOC_STANDARDS.md` via its dated amendment process; a standalone canonical only if the owner orders one (then it supersedes §6 with a banner chain, one-canonical preserved) | **APPROVED 2026-07-18** |
| FFD-D2 | Feature-close sweep threshold | BLOCKER-clean mandatory; WARNs dispositioned or owner-accepted (visible, attributed); INFO reported — aligned with the P14 SYNC-D3 ratification | **APPROVED 2026-07-18** |
| FFD-D3 | Planning-doc ruling | WHICH document records post-freeze feature reality (the superseded roadmap? a new post-freeze feature register? the PDD amendment register alone?) — not decidable from the record; the freeze package stays a truth-lock regardless | **APPROVED 2026-07-18** — **D3 RULING: the Phase-18 Vision Package ([FUTURE_FEATURE_VISION_2026_07_18.md](../FUTURE_FEATURE_VISION_2026_07_18.md)) IS the planning document of record for post-freeze feature reality, until superseded by a future owner-approved planning document** |
| FFD-D4 | Regeneration authority | Phase 18 (and every future feature-close agent) RUNS the P8/P9 commands the sync report prints — the licensed human/agent side of detect-don't-repair; manifest regen always an isolated battery-bearing wave | **APPROVED 2026-07-18** |
| FFD-D5 | PDD-register consolidation | The 15–17 amendment entries verified, cross-linked to their contracts + logs, format per the register's own conventions; PDD body untouched | **APPROVED 2026-07-18** |
| FFD-D6 | Memory/doc synchronization | Protocol clause restated: docs are binding, agent memory is a mirror; nothing feature-related may exist only in memory; agents-without-memory rely wholly on §6's on-disk artifacts | **APPROVED 2026-07-18** |
| FFD-D7 | Post-22 adaptation | Same protocol with commit discipline: docs in the SAME COMMIT as their code; §6.3's gate runs pre-commit; the P14 pre-checkpoint sweep precedent generalizes to pre-release sweeps — confirm | **APPROVED 2026-07-18** |
| FFD-D8 | Applicability boundary | FEATURES follow this protocol; confirmed-bug FIXES follow the PHASE_04 lifecycle (whose Docs stage already binds U6) — the two protocols reference, never overlap; boundary confirmed here | **APPROVED 2026-07-18** |
| FFD-D9 | Deployment-doc duties | Features that change deploy-relevant behavior (routes, settings shape, migrations, commands) owe a runbook-impact note at feature-close; the runbook's OWNERSHIP lands in Phase 19's contract — this slot records the hook only | **APPROVED 2026-07-18** |

Date · answered by: **2026-07-18 · owner ("OWNER AUTHORIZATION — PHASE 18 / FFD-A": FFD-D1 through FFD-D9 APPROVED + the D3 ruling verbatim), recorded same session**

## Dated amendments

_(none)_

# Evidence note

All sync + protocol evidence lives in `docs/FEATURE_DOC_SYNC_LOG.md` (created at FFD-0) —
contract = the permanent procedure, log = its first run (framework hierarchy rule). From
FFD-E onward, every future feature's documentation completeness is judged against §6 and
certified by a sweep — the campaign's documentation system, closed into a loop.
