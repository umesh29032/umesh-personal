---
id: docs-campaign-contracts-phase-14-knowledge-sync
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 14 Execution Contract — Automatic Knowledge Sync (knowledge_sync)

> Authored 2026-07-12 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md) and — as the FINAL CHILD of the parent contract
> [PHASE_05_DOCUMENTATION_FOUNDATION.md](PHASE_05_DOCUMENTATION_FOUNDATION.md) — the entire
> documentation architecture (validation dimensions §6.1.17, automation hooks §6.1.18,
> ownership/lifecycle/metadata rules), exactly as Phases 6–9 do. Additionally inherits:
> **PHASE_08** (the graph validator — extended, NEVER forked) · **PHASE_09** (the stale-output
> contract: recorded graph-hash ≠ current = STALE; fence rules; the regeneration runbook) ·
> **PHASE_11/12** (spec⇄seeder scenario-registry drift, handed off at SEED-F) · **PHASE_13**
> (report conventions, read-only purity pattern, the boundary law: 13 verifies DATA/CONFIG
> state, 14 detects CODE⇄DOCS⇄GRAPH drift — no overlap, same detect-and-notify law) · the
> **pkals_v2 heritage** (ADR-V2-P2 "detect-and-notify, never auto-rewrite"; its MUST list —
> change-impact tool, route-map drift, model-map drift, knowledge-sync hook — two of which
> already exist as `.claude/skills/find-canonical` + `/impact` wrapping
> `scripts/pkals_canonical.py` and the CHANGE_IMPACT_MATRIX). None restated; deltas only.
> **The engine is a PURE DETECTOR. It never modifies source code, documentation, the graph,
> manifests, or generated outputs — it detects, classifies, and reports. Repairs always
> belong to the owning phase/protocol.**
> Evidence doc (created at KS-0): `docs/KNOWLEDGE_SYNC_LOG.md`.

## 1. Phase objective

Implement **`manage.py knowledge_sync`** (KOS v3 core element 5): the standing drift detector
that answers "is the knowledge system still true?" across every boundary the campaign built —
code⇄docs, code⇄graph, docs⇄graph, generated-artifact staleness, manifest coherence,
ownership/metadata integrity, dataset-spec⇄seeder registry, verification-registry citations —
deterministically, read-only, with severity-classified machine- and human-readable reports
that name the OWNING repair venue for every finding. After this phase, documentation drift
(the "architecture bug" of CLAUDE.md rule 12) has a permanent instrument, and the
PHASE_05 family (5→14) is complete.

## 2. Scope

### 2.1 Facts of record (authoring-time; KS-0 re-verifies)

| Fact | Evidence |
|---|---|
| Charter form | master index: "`manage.py knowledge_sync` (KOS graph ⇄ code drift detection)" — a management command by charter |
| Detect-don't-repair is settled law | pkals_v2 ADR-V2-P2 (adopted permanently at PHASE_05 §6.1.16/6.1.17 and PHASE_09 GEN-D7): tooling DETECTS and NOTIFIES; a human/agent judges and writes |
| Existing detector heritage | `/impact` (changed files → CHANGE_IMPACT_MATRIX docs, "flags changed files that have no matrix row") · `/find-canonical` (manifest router) · `scripts/pkals_canonical.py` · `PkalsNavigationGuardTests` (dead manifest path fails the build) — knowledge_sync EXTENDS these, never duplicates (parent §6.1.18) |
| Consolidated drift contracts already specified | PHASE_08 §6.7 (sync re-checks graph invariants continuously; extends the validator) · PHASE_09 §6.6 (stale-output: output graph-hash vs current; fence integrity; hand-edit detection) · PHASE_12 SEED-F handoff (declared-vs-implemented scenarios, spec version pinning) · PHASE_13 §6.6 (registry/report conventions shared; boundary stated) |
| Read-only pattern | PHASE_13 purity test + runtime row-count-identity proof — reused verbatim for this engine (plus: zero FILE writes outside `var/`) |
| Git interaction | diff-scoped mode reads `git diff`/`git status` (read-only git = U2-compatible; no staging, no commits — the pkals_v2 hook design "git diff → matrix → touch these docs") |
| Battery mechanism | SEED-D4/VER-D6 precedent: new suite joins via dated framework-README amendment |

### 2.2 In / out

**In:** the `knowledge_sync` command + detector core (home per SYNC-D1) · the 8-domain
detector inventory (§6.3) · severity classification · full-sweep + diff-scoped modes ·
deterministic reporting (P13 conventions) · the owner-selected CI/test-guard subset (SYNC-D4)
· read-only purity proofs · tests + battery integration · docs + handoffs.
**Out:** ANY repair of ANY finding (a sync run that edits is a corrupter — the cardinal sin
mirrors PHASE_13 §16.3) · regeneration itself (sync PRINTS the regeneration command from the
Phase-9 runbook/output banners; a human/agent runs it) · graph rebuilding (prints the Phase-8
builder command) · schedulers, cron, CI workflows, git hooks, GitHub Actions (cadence intent
recorded at SYNC-D9; wiring = out) · new invariants or new doc standards (owner/ADR/Standard
amendment territory) · schema changes (no models; needing one = stop) · the skills' removal
(`/impact`/`/find-canonical` remain; sync wraps/extends per SYNC-D9).

## 3. Success criteria

Phase 14 is DONE when ALL hold:
1. `manage.py knowledge_sync` exists at the SYNC-D1 home with full-sweep + `--diff` modes,
   deterministic (body-hash-stable) reports, and exit codes (0 = no findings at/above the
   ratified failure threshold; nonzero otherwise, counts in the envelope).
2. **Detector inventory complete:** every §6.3 domain implemented or registered
   deferred-with-reason — counted against the inherited drift contracts (each PHASE_08/09/12/13
   handoff obligation → a detector or a deferral row).
3. **Pure-detector proven:** purity test (zero ORM writes AND zero file writes outside
   `var/`) + runtime proof (full sweep leaves repo tree + DB byte-identical — tree-hash
   pre/post, the Phase-0 porcelain-proof pattern reused).
4. **Every finding names its repair venue:** the report schema carries owning-phase/protocol
   routing per finding class (docs → U6/CHANGE_IMPACT + Phase-7-style repair · generated →
   Phase-9 regeneration runbook · graph → Phase-8 rebuild · code → Phase-4 protocol/U12 ·
   spec/registry → dated amendments) — no orphan findings.
5. **Severity classification live** (SYNC-D3 tiers), with constructed-fail proofs per domain
   (a planted drift of each class is caught at its expected severity: a hand-edited fence, a
   stale generated output, a deleted doc path, a matrix-less changed file, a renamed URL, a
   spec-registry mismatch, a broken check-citation).
6. The owner-selected CI/test-guard subset (SYNC-D4) is implemented as battery tests (the
   PkalsNavigationGuardTests extension pattern) and green; everything else is report-only.
7. Determinism proven (same tree ⇒ identical report bodies); diff-mode proven against a
   constructed working-tree change.
8. Battery green at the new baseline (entry + this suite; framework amendment recorded);
   primary dev DB + repo corpus untouched throughout (proofs recorded).
9. U6 docs complete; Phase-18/19/22 handoffs written; status + memory synced every sub-phase.

## 4. Rules of engagement (deltas beyond U1–U14 + inheritance)

- **Purity-first:** the no-writes purity test (DB + files) lands before any detector logic
  (guards/purity-before-features, the P12/P13 pattern extended to file writes).
- **Extend, never fork:** graph checks import the Phase-8 validator; generated-artifact
  checks import the Phase-9 validation suite; seed-registry checks read the P12 machine-
  readable registry; verification-registry checks read the P13 registry. Duplicated check
  logic = structural defect (single-source law).
- **Findings are routed, never judged final:** sync classifies severity + venue; whether a
  WARN is acceptable is the owning phase's/owner's call. Sync never suppresses: acceptance
  lists (known-and-accepted findings) are a REPORT feature (visible, dated, owner-attributed
  per SYNC-D5), never silent filters.
- **Git reads only** (diff-mode): `git diff --name-only`/`status` class commands; no staging,
  no checkout, nothing that touches the index (U2).
- **Cost humility:** the full sweep must be runnable casually (minutes, not hours); expensive
  detectors (graph dry-run rebuild) declare their cost and may be `--deep`-gated (SYNC-D7) —
  but never silently skipped (skips print into the report, the P13 no-silent-skip rule).
- One detector-domain wave at a time (serial discipline); scratch-DB law inherited where a
  detector needs a DB at all (most are file/graph-side).

## 5. Evidence standard

Per wave: detector-inventory table (detector id · domain · inherited contract it satisfies ·
severity mapping · mode [sweep/diff/deep] · guard-subset?) · constructed-drift proofs (plant →
catch → severity → venue quoted from the report) · purity + tree/DB-identity proofs ·
determinism body-hash pairs · diff-mode proof · battery arithmetic per wave · report samples
quoted into the log. Sub-agent scaffolding sweeps supplemental (U7); detector-inventory
completeness, severity rules, guard-subset selection, and certification = main-thread.

## 6. Methodology

### 6.1 Synchronization philosophy

Drift is an architecture bug (CLAUDE.md rule 12; PKALS-LIVE) — but the FIX is always human/
agent judgment through the owning protocol; automation's whole job is to make drift
IMPOSSIBLE TO MISS, not to make it disappear. knowledge_sync is therefore the standing
instrument of U6: after any change, one command lists exactly what knowledge became stale,
how bad it is, and which venue repairs it. It asserts nothing new: every detector implements
an ALREADY-BINDING rule (a Standard clause, a graph invariant, a stale-output contract, a
registry pin) — the P13 codify-don't-legislate law applied to knowledge.

### 6.2 Architecture (SYNC-D1 default)

The `knowledge_sync` command + a `knowledge/` detector core in the DEV-ONLY tooling home
(default: the `devseed` app hosts the command — dev-only is correct because drift detection
is a repo-side maintenance concern, never a production-runtime one; the app's charter widens
from "seeder" to "dev tooling", noted in its README; a separate third app remains the
owner-selectable alternative). Detector core: one module per domain (§6.3), each detector a
pure function over (repo tree, graph, registries, git-diff) → Finding[]; `report.py` REUSES
the P13 envelope/body conventions (shared format = the P13 handoff); `acceptance.py` (the
visible acceptance-list mechanism). No models, no migrations, no URLs.

### 6.3 Detector domains (SYNC-D2 — the inventory)

1. **code ⇄ documentation:** diff-mode: changed files → CHANGE_IMPACT_MATRIX rows → the
   docs-to-touch list + matrix-less-file findings (the `/impact` logic, extended); sweep-mode:
   route-map drift (URL census vs url-cards/URL knowledge) + model-map drift (model census vs
   README/DATABASE_GUIDE coverage) — the pkals_v2 MUST detectors, implemented against the
   graph's mapping-law floors.
2. **code ⇄ graph:** graph staleness — cheap tier: census counts (routes/models/services) vs
   graph node counts; deep tier (`--deep`, SYNC-D7): builder dry-run rebuild + body-hash
   compare ("rebuild would differ" = stale). Plus the Phase-8 validator re-run (invariants
   still hold against today's tree — doc-path existence especially).
3. **documentation ⇄ graph:** doc nodes vs frontmatter (tier/type/ownership/status agree);
   supersession edges vs banners; index-reachability vs graph edges.
4. **generated-artifact drift:** the PHASE_09 stale-output contract (recorded graph-hash ≠
   current graph = STALE, with the regeneration command printed); fence integrity corpus-wide;
   **hand-edit-in-fence detection** (content-hash mismatch = BLOCKER — someone edited
   generated content).
5. **canonical-manifest synchronization:** post-Phase-9 (manifest = generated view):
   regenerate-compare drift; its paths re-validated (the PkalsNavigationGuardTests concern,
   report-side); topic coverage vs graph.
6. **ownership + metadata synchronization:** OWNERSHIP_MATRIX rows vs census (new docs
   without owners; owners of deleted docs); frontmatter completeness/validity per the
   R2-ratified scope; lifecycle-state consistency (superseded ⇒ banner + successor;
   `frozen` docs unmodified since freeze where a hash anchor exists).
7. **dataset-specification drift:** P11 spec scenario registry vs P12 implemented registry
   (declared-not-implemented / implemented-not-declared / spec-version pin mismatch) — the
   SEED-F detector spec.
8. **verification-registry drift:** P13 check registry citations still resolve (cited spec
   §/ADR/manifest-rule/golden-value sources exist and unchanged where hash-anchored);
   registry machine-readability intact.

### 6.4 Severity classification (SYNC-D3 default)

**BLOCKER** — knowledge lies: hand-edit-in-fence · dead CI-guarded path · truth-lock
contradiction signal · graph invariant violation. **WARN** — knowledge is stale but honest:
stale generated output · matrix-less changed file · missing frontmatter in scope · registry
pin mismatch · unowned doc. **INFO** — hygiene: stale `verified:` dates · cosmetic naming
deviations · accepted-list items (always shown). Exit-code failure threshold default = any
BLOCKER (WARN/INFO report-only) — ratify. Every finding: id, domain, severity, evidence
(path/line/hash pair), owning repair venue, acceptance status.

### 6.5 Regeneration + repair workflow (detect-side only)

For every stale/drifted artifact the report prints the EXACT owning remedy: the Phase-9
regeneration command (from the output banner/runbook) · the Phase-8 rebuild command · the U6
doc-repair pointer (matrix row + GUIDE path) · the Phase-4 intake note for code-side findings
(observation → U12/ledger; U8 wording if money-adjacent) · the dated-amendment pointer for
spec/registry mismatches. Sync stops at printing. A `--fix` flag will never exist (stated in
the CLI so nobody adds one casually — owner/ADR to ever change).

### 6.6 Handoffs

**Phase 18 (Future Feature Documentation Updates):** knowledge_sync is the enforcement
instrument for U6 during feature phases 15–17 — run diff-mode after each feature wave; the
findings list IS the docs work queue; Phase 18 closes when a full sweep is BLOCKER/WARN-clean
(or acceptance-listed by the owner). **Phase 19–21 (deployment):** a drift-clean sweep
(threshold per owner) joins the readiness inputs alongside PHASE_13's green
verify_production; the runbook names both. **Phase 22 (First Git Checkpoint):** a mandatory
pre-checkpoint full sweep — the ONE commit captures a drift-clean knowledge corpus (finding
residue = owner-accepted, listed in the checkpoint record).

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); evidence into the log; **battery at every
code-wave close**.

| # | Scope · Key proofs · Stop deltas |
|---|---|
| **KS-0** — Charter + gate + ratification | Gate: Phase 13 closed (per locked order the whole 5→13 chain precedes). Owner ratifies SYNC-D1..SYNC-D9 (incl. failure threshold, guard subset, battery amendment). Baselines: battery entry; tree-hash + dev-DB census anchors. **Stop:** gate fails; any SYNC-D unanswered. |
| **KS-A** — Skeleton + purity + reporting (battery-bearing) | Command shell + detector-core scaffolding at the SYNC-D1 home; **the no-writes purity test (DB + files) lands first**; P13-convention report envelope/body + acceptance-list mechanics; diff-mode git plumbing (read-only). **Proofs:** purity green; tree/DB-identity on an empty sweep; battery = entry + new tests. **Stop:** any conceivable write path (DB or repo file). |
| **KS-B** — Docs-domain detectors (battery-bearing) | Domains 1, 6 (+ 5's pre-conversion form if Phase 9's manifest conversion state requires): change-impact diff-mode, route/model-map sweep, ownership/metadata/lifecycle checks. Constructed-drift proofs per detector. **Stop:** a detector needs a rule the Standard doesn't state (→ owner/Standard amendment, never invented). |
| **KS-C** — Graph + generation detectors (battery-bearing) | Domains 2, 3, 4, 5: validator re-run integration (import, not fork), census-vs-graph tiers, `--deep` dry-run compare, stale-output + fence-integrity + hand-edit detection, manifest regenerate-compare. **Stop:** single-source breach (any re-implemented validator/generator logic); `--deep` cost unbounded. |
| **KS-D** — Registry detectors + severity + determinism (battery-bearing) | Domains 7, 8; severity engine + threshold; full-sweep determinism body-hash pairs; the full constructed-drift matrix (every domain × plant-catch-severity-venue); `--diff` end-to-end proof. **Stop:** a finding class with no owning venue (routing hole → owner). |
| **KS-E** — Guard subset + certification + handoffs | Implement the SYNC-D4 owner-selected CI/test-guard subset (PkalsNavigationGuardTests extension pattern; battery); detector-inventory completeness census vs the inherited drift contracts; final battery arithmetic; tree/DB untouched proofs; §6.6 handoffs (incl. the Phase-22 pre-checkpoint sweep obligation); U6 docs; PHASE-14 VERDICT — **and the PHASE_05-family closure note: hooks 6.1.18 all live**. **Stop:** unaccounted inherited obligation. |

## 8. Deliverables

- `manage.py knowledge_sync` (full-sweep, `--diff`, `--deep`, acceptance lists, thresholds) +
  the 8-domain detector core — pure-detector proven.
- The owner-selected battery guard subset; the engine's test suite in the battery
  (+ the ratified framework amendment).
- `docs/KNOWLEDGE_SYNC_LOG.md`: ratifications · per-wave evidence · constructed-drift matrix ·
  determinism proofs · certification + handoffs + the family-closure note.
- U6 docs (home app README/GUIDE updates, index rows); filled Design Record
  (SYNC-D1..SYNC-D9); status + memory per sub-phase.

## 9. Files expected to change

**New (code):** the detector core + command (+ tests) at the SYNC-D1 home. **Updated
(code-adjacent):** the home app's existing files only as far as registering the command/core
(if SYNC-D1 = a NEW third app instead: its tree + one local.py line + one .importlinter row —
the P12 pattern). **Docs:** `docs/KNOWLEDGE_SYNC_LOG.md` (new) ·
`docs/DEPLOYMENT_CAMPAIGN_STATUS.md` · `docs/DOCUMENTATION_INDEX.md` · framework README
(battery amendment, dated) · the home app's README/GUIDE (U6) · this file (Design Record +
amendments) · memory files. **Runtime:** `var/knowledge_sync_reports/` (gitignored). Nothing
else — in particular ZERO corpus docs, ZERO generated artifacts, ZERO graph/manifest bytes.

## 10. Files that must never change (touching one = STOP + report)

- EVERY existing domain app's code · every corpus doc · `knowledge_graph.json` + schema ·
  ALL generated outputs + fences · `canonical_manifest.json` · `docs/DOC_STANDARDS.md` ·
  T1 truth-locks · closed phase logs (dated amendments per their own rules only) — **the
  engine's entire subject matter is read-only to it, by definition.**
- `config/config/settings/base.py` + `production.py`; enforcement flags (U10); `.env`.
- The PRIMARY dev database (census only) · non-DEV data · scratch worlds it didn't create.
- The Phase-8 builder/validator + Phase-9 generators + Phase-12/13 engines beyond importing
  them (extend-never-fork; their changes go through their own contracts' amendment rules).
- `.claude/skills/*` (they remain; SYNC-D9 records their relationship) · the 2 stashes ·
  `.git` state (U2 — reads only).

## 11. Documentation update rules

At every sub-phase close, same session: (a) log section appended (closed sections append-only,
corrections dated); (b) status-file Phase-14 row + dashboard (battery per wave) + "Next
action"; (c) **U6 fully applies** (new code): home-app README/GUIDE current per wave;
CHANGE_IMPACT_MATRIX consulted per changed file; DOCUMENTATION_INDEX rows; (d) framework
battery amendment at KS-0; (e) at KS-E: the PHASE_05-family closure recorded in the status
file (parent §6.1.18 hooks all delivered).

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-14
bullet: wave closed, detector counts, battery arithmetic, log pointer; at KS-E the
family-closure note) + MEMORY.md index line at each sub-phase close. Agents without memory:
skip — the log + status file + machine reports (quoted where binding) are the complete record.

## 13. Battery policy

Sequential fresh-DB canonical (U5), **at every code-wave close (KS-A..KS-E)**. Arithmetic:
entry baseline (status dashboard at KS-0) + this suite's cumulative count per wave; suite
membership = the SYNC-D8 framework amendment (SEED-D4/VER-D6 mechanism). The SYNC-D4 guard
subset becomes part of the permanent battery (drift classes the owner promotes to
build-red). knowledge_sync runs never substitute for the battery, and a red sync never
blocks a battery run (independent instruments).

## 14. Regression policy

- Full existing battery + FoundationPurityTests green every wave = do-no-harm proof.
- The purity test (DB + file writes) + the tree/DB-identity runtime proofs are permanent pins
  of the pure-detector property.
- The constructed-drift matrix guards against a detector that can only say yes (P13 rule
  generalized): every domain must demonstrably catch its planted failure class before
  certification.
- Single-source imports (validator/generators/registries) are structurally asserted (an
  import-graph check in this engine's own tests) — forks regress the whole knowledge system.
- Incidental defects discovered = observations → U12 backlog (+U8 stop if money); pins-for-
  fixes only via the Phase-4 protocol (cross-logged).

## 15. Rollback policy

- The engine is additive: a bad wave reverts file-scoped; battery to green; report.
- Reports/acceptance lists are runtime artifacts (`var/`) — disposable; acceptance decisions
  are owner records QUOTED into the log (the `var/` copy is never the only record).
- The log + Design Record are append-only (dated amendments).
- Session crash mid-wave: next session re-runs the wave's tests FIRST, reconciles the log,
  completes or reverts before new work; an interrupted sweep leaves nothing to clean by
  construction (read-only).

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. KS-0 gate fails (Phase 13 not closed) or any SYNC-D1..D9 unanswered.
3. Any engine write path — DB, corpus file, graph, manifest, generated output, git index —
   the cardinal sin (report includes how it was possible).
4. A detector requires a rule no Standard/contract states (invention pressure → owner/
   Standard amendment), or a finding class has no owning repair venue.
5. Single-source breach: validator/generator/registry logic re-implemented instead of
   imported.
6. `--fix`-shaped pressure (any pathway by which sync would repair) — the flag must never
   exist; report the pressure.
7. U8 wording: a money-adjacent finding is REPORTED with U8 routing; any temptation to
   "verify by correcting" = STOP.
8. Battery red beyond the wave's own new tests' target behavior; tree-hash/dev-DB census
   drift.
9. Inherited-obligation mismatch: a PHASE_08/09/12/13 handoff cannot be satisfied as
   specified (→ dated amendment to the owning contract; never silent divergence).

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-14 row: which KS-* is next; battery
   arithmetic.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + env + battery amendments) → the parent
   [PHASE_05_DOCUMENTATION_FOUNDATION.md](PHASE_05_DOCUMENTATION_FOUNDATION.md) (§6.1.17/18)
   → `docs/DOC_STANDARDS.md` → the PHASE_08/09/12/13 contracts' handoff sections + their
   logs (the inherited drift contracts) → this contract → `docs/KNOWLEDGE_SYNC_LOG.md` if it
   exists (absent ⇒ next = KS-0).
3. Verify read-only: purity tests green in THIS tree before any manual sweep; the graph
   validates (P08 rule: hash-mismatched graph = treat as absent); registries readable;
   tree-hash + dev-DB census vs anchors.
4. Never run a sweep before KS-A's purity proofs are closed in the current tree.
5. Battery environment per framework env facts; git commands read-only.
6. Execute exactly ONE sub-phase per §7. STOP per §16.
7. Anything inconsistent across status file / Standard / inherited contracts / log / this
   contract → report before working (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (KS-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| SYNC-D1 | Engine home | `devseed` hosts the command + `knowledge/` detector core (dev-only is correct: repo-side maintenance concern; the app's charter widens to "dev tooling", README updated); alternative = a third dev-only app (P12 pattern) | _(pending)_ |
| SYNC-D2 | Detector inventory | The 8 domains of §6.3, each mapped to its inherited contract; unmapped detectors don't merge | _(pending)_ |
| SYNC-D3 | Severity + threshold | BLOCKER/WARN/INFO per §6.4; exit-code failure threshold = any BLOCKER; acceptance lists visible + owner-attributed, never silent | _(pending)_ |
| SYNC-D4 | CI/test-guard subset | Which detectors become permanent battery guards (default: dead-CI-guarded-path + hand-edit-in-fence + graph-invariant classes — the PkalsNavigationGuardTests extension pattern); all else report-only | _(pending)_ |
| SYNC-D5 | Report format + acceptance | P13 envelope/body conventions reused verbatim; `var/knowledge_sync_reports/`; acceptance list = dated + owner-attributed entries, always printed | _(pending)_ |
| SYNC-D6 | Modes | Full sweep (default) + `--diff` (read-only git, changed-files scope) + `--deep` (expensive tiers); skips always printed | _(pending)_ |
| SYNC-D7 | Graph-staleness method | Cheap tier = census-counts vs graph (default sweep); deep tier = builder dry-run rebuild + body-hash compare (`--deep`); costs declared per detector | _(pending)_ |
| SYNC-D8 | Battery membership | This suite joins the canonical battery (dated framework-README amendment, SEED-D4 mechanism) | _(pending)_ |
| SYNC-D9 | Cadence + skills relationship | On-demand + diff-mode after feature waves (Phase 15–18 discipline) + mandatory pre-checkpoint full sweep (Phase 22) + pre-deploy sweep (Phase 19 input); `/impact` + `/find-canonical` skills REMAIN (sync extends them; retirement = a later owner decision); cron/CI wiring OUT | **ACCEPTED (default)** |

Date · answered by: **2026-07-17 · owner, verbatim ("I accept the defaults for SYNC-D1
through SYNC-D9 with one explicit clarification.") — SYNC-D1 approved exactly as proposed ·
SYNC-D2 approved WITH the owner ruling replacing ambiguity A-1 (see the dated amendment
below) · SYNC-D3..D9 approved exactly as proposed without modification. KS-0 accepted and
closed; KS-A authorized same order.** (D1..D8 column values: **ACCEPTED (default)**; D2 =
**ACCEPTED + A-1 ruling**.)

## Dated amendments

- **2026-07-17 — A-1 disposition (owner ruling at KS-0 ratification, replacing the recorded
  ambiguity):** Phase-9 Amendment A1 remains authoritative — the canonical manifest remains
  **HANDWRITTEN and CI-guarded**. **Detector domain 5 (§6.3.5) is PERMANENTLY re-scoped to:
  (a) manifest path validation · (b) canonical topic coverage vs the knowledge graph ·
  (c) consistency validation. The regenerate-compare behavior is NOT part of Phase 14 and
  shall not be implemented.** Mirror record: KNOWLEDGE_SYNC_LOG §KS-0 ambiguity A-1.

# Evidence note

All implementation evidence lives in `docs/KNOWLEDGE_SYNC_LOG.md` (created at KS-0) —
contract = procedure, log = what was built and proven (framework hierarchy rule). With KS-E's
closure note, every automation hook the parent contract declared (§6.1.18) is delivered, and
the PHASE_05 Documentation Foundation family (5 → 6 → 7 → 8 → 9 → 14) is complete.
