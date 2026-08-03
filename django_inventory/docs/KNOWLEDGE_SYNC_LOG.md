---
id: docs-knowledge-sync-log
type: receipt
status: active
owner: append-only
scope: campaign
anchors: —
verified: 2026-07-18
---

# KNOWLEDGE SYNC LOG — Campaign Phase 14 (append-only evidence)

> Contract: [campaign_contracts/PHASE_14_KNOWLEDGE_SYNC.md](campaign_contracts/PHASE_14_KNOWLEDGE_SYNC.md)
> (frozen; Design Record = its Appendix A; sub-phases named KS-0..KS-E there — the owner's
> "SYNC-0" = KS-0, one and the same). Parent: 🔒
> [PHASE_05_DOCUMENTATION_FOUNDATION.md](campaign_contracts/PHASE_05_DOCUMENTATION_FOUNDATION.md)
> — **Phase 14 is the FINAL CHILD (5→6→7→8→9→14): with its close, every §6.1.18 automation
> hook is delivered and the Documentation Foundation family is complete.**
> **THE ENGINE IS A PURE DETECTOR:** it never modifies source, docs, the graph, manifests, or
> generated outputs — detect · classify · report · name the owning repair venue. A `--fix`
> flag will never exist.

## KS-0 (SYNC-0) — Charter + gate + ratification — ⏸ DECISION PACK PENDING OWNER (opened 2026-07-17)

### 1. Gate — ✅ PASS (re-verified live this session)

| Gate item | Proof |
|---|---|
| Phase 13 closed correctly | VERIFICATION_ENGINE_LOG §VER-E.5: "PHASE 13 COMPLETE — VERIFICATION ENGINE CERTIFIED (engine 1.0.0)" — owner-accepted; the whole locked 5→13 chain precedes |
| Verification Engine operational + certified | all five commands live (VER-B/C) · determinism certified ×5 commands cross-session (VER-D) · read-only purity pins in the battery |
| Certified report schema = the baseline | engine v1.0.0 envelope/body key sets, `test_certification.py` = the tripwire — **Phase 14 reuses these conventions verbatim (SYNC-D5)** |
| Phase-13 handoff available | VERIFICATION_ENGINE_LOG §VER-E.3.1: certified schema + 19-check census + citation law + SPEC_VERSION cross-pin + the boundary law (13 = DATA/CONFIG state · 14 = CODE⇄DOCS⇄GRAPH drift) |
| Phase-8 inheritance live | `docs/knowledge_graph.json` + `knowledge_graph.schema.json` (cert: 1,345n/635e · schema 1.0.1 · hash `85b7fd6d…`) · `scripts/build_knowledge_graph.py` + `validate_knowledge_graph.py` |
| Phase-9 inheritance live | `docs/features/` = **558 generated files**, each stamped `verified: graph:85b7fd6d5204` + the regeneration banner (`scripts/generate_docs.py`, template versions) — the domain-4 stale-output/hand-edit anchors exist EXACTLY as the detector needs them |
| Phase-12 inheritance live | `devseed.scenarios.SCENARIOS` (24 slugs, machine-readable) + `guard.SPEC_VERSION` — the SEED-F drift-detector handoff inputs |
| Detector heritage live | `.claude/skills/{impact,find-canonical}` · `scripts/pkals_canonical.py` + `pkals_impact.py` · `PkalsNavigationGuardTests` (config/core/tests.py) · CHANGE_IMPACT_MATRIX — knowledge_sync EXTENDS these (parent §6.1.18), never duplicates |
| Battery entry baseline | **1678/1678** (FINAL Phase-13 baseline, re-verified at VER-E this same session) |
| Tree + DB anchors (KS-0 baselines) | git `49404001` · 2 stashes · `git status --porcelain` = 512 entries, sha256 `d4323026a122ebe4…` (the tree-state anchor for the pure-detector identity proofs) · primary `inventory_db` sentinels: ledger 170/Σ₹10,880.25 · users 48 · dev.min 0 (full 34-anchor census EXACT at VER-E, same session) |

### 2. Reconciliation (objectives vs the knowledge estate — read-only)

| Surface | State found | Phase-14 interface |
|---|---|---|
| Documentation Foundation (PHASE_05 §6.1.17/18) | validation dimensions + automation hooks defined; knowledge_sync = the LAST undelivered hook | the §6.3 detector inventory maps 1:1 onto §6.1.17 dimensions; KS-E records family closure |
| PKALS / pkals_v2 heritage | ADR-V2-P2 detect-and-notify law settled; `/impact` + `/find-canonical` + `scripts/pkals_canonical.py`/`pkals_impact.py` live; PkalsNavigationGuardTests = the CI-guard precedent | domain 1 (diff-mode) extends `/impact`'s matrix logic; domain 5 report-sides the guard-test concern; skills REMAIN (SYNC-D9) |
| AI Agent Guide + canonical_manifest | `docs/LEARNING_2_0/AI_AGENT_GUIDE/canonical_manifest.json` — **HANDWRITTEN + CI-guarded per Phase-9 Amendment A1 (owner Option (b), 2026-07-16)**; graph = the only machine source EXCEPT the manifest | domain 5 consumes the manifest read-only — see AMBIGUITY A-1 below |
| DOCUMENTATION_INDEX | current through P13; rows for every campaign evidence doc | domain 6 input (index-reachability); this log's row added at KS-0 |
| CHANGE_IMPACT_MATRIX | current (devseed + verification rows added P12/P13); the `/impact` data source | domain 1's diff-mode row source; matrix-less-changed-file = a WARN class |
| Verification Engine outputs | certified report schema (envelope/body) · 19-check census · citation law · `var/verification_reports/` | SYNC-D5 reuses the schema conventions VERBATIM; domain 8 checks the P13 citations still resolve |
| OWNERSHIP_MATRIX | `docs/LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/OWNERSHIP_MATRIX.md` (extended DOCCLEAN-B; GEN-E row live) | domain 6 input (rows vs census) |
| Generated corpus | 558 files, graph-hash-stamped, banner-carrying, fence rules per P9 | domain 4 inputs exist exactly as specified |

**Ambiguities recorded (NOT solved here — §16 discipline):**
- **A-1 · Domain 5 vs Phase-9 Amendment A1 (the one real contract-vs-world mismatch):**
  contract §6.3.5 was authored 2026-07-12 assuming "post-Phase-9: manifest = generated view →
  regenerate-compare drift". The owner's GEN-D Amendment A1 (2026-07-16) ruled the manifest
  stays HANDWRITTEN + CI-guarded — the regenerate-compare leg has NO source to compare
  against. **Resolution belongs to the owner at ratification** (expected shape: a dated
  PHASE_14 amendment re-scoping domain 5 to path re-validation + topic-coverage-vs-graph,
  regenerate-compare N/A) — flagged under SYNC-D2 in the pack below, not decided.
- **A-2 · Frozen-doc hash anchors (domain 6):** the "frozen docs unmodified since freeze
  where a hash anchor exists" leg is self-limiting; WHICH frozen docs carry recorded content
  hashes = a KS-B census fact, not an owner decision. Recorded as a census obligation.
- **A-3 · scripts/ import mechanics:** `build_/validate_/generate_` live in repo-root
  `scripts/` (not an installed package); the extend-never-fork law means the detector core
  imports them (path-based import or subprocess-with-parse). KS-A design detail within the
  contract; recorded, not decided.
- **A-4 · Domain-8 citation-resolution rule granularity:** "cited sources exist and
  unchanged where hash-anchored" — the string→source resolution table (spec § / ADR file /
  golden value / CheckConstraint class) is KS-D design within the contract's wording;
  recorded.

### 3. Charter (the complete Phase-14 shape — from the frozen contract, condensed)

- **Objective:** `manage.py knowledge_sync` — the standing drift detector answering "is the
  knowledge system still true?" across every campaign boundary; deterministic, read-only,
  severity-classified, every finding naming its owning repair venue.
- **Scope in:** command + 8-domain detector core · severity engine · full-sweep/`--diff`/
  `--deep` modes · P13-convention deterministic reports · acceptance lists (visible, dated,
  owner-attributed) · owner-selected CI/test-guard subset · purity proofs · tests + battery ·
  docs + handoffs. **Out:** ANY repair · regeneration/rebuild themselves (prints the
  commands) · schedulers/CI wiring · new invariants/standards · schema changes · skill
  removal.
- **Architecture (SYNC-D1 default):** command + `knowledge/` detector core hosted in
  `devseed` (charter widens to "dev tooling"); one module per domain; pure functions over
  (tree, graph, registries, git-diff) → Finding[]; report reuses P13 conventions;
  `acceptance.py`; no models/migrations/URLs. Alternative: a third dev-only app (P12
  pattern).
- **Boundaries:** pure detector (DB + FILE write purity, landed first) · git reads only ·
  extend-never-fork (P8 validator, P9 validation, P12/P13 registries imported) · findings
  routed, never judged final · cost humility (casual full sweep; `--deep` for expensive
  tiers; no silent skips).
- **Inputs:** knowledge_graph.json + schema + cert hash · 558 generated outputs + banners ·
  canonical_manifest (handwritten, A-1) · DOC_STANDARDS/frontmatter rules · OWNERSHIP_MATRIX
  · CHANGE_IMPACT_MATRIX · DOCUMENTATION_INDEX · devseed scenario registry + SPEC_VERSION ·
  verification check registry + citations · git diff/status (read-only) · URL/model censuses.
- **Outputs:** machine + human reports → `var/knowledge_sync_reports/` (gitignored) ·
  exit codes vs the ratified threshold · acceptance-list echoes. ZERO writes anywhere else.
- **Invariants:** detect-don't-repair (ADR-V2-P2) · every detector cites an ALREADY-BINDING
  rule · every finding has id/domain/severity/evidence/venue/acceptance-status · determinism
  (body-hash-stable) · no `--fix`, ever.
- **Interfaces:** consumes P8/P9/P12/P13 artifacts (above); serves P15–18 (diff-mode after
  feature waves = the U6 work queue), P19 (drift-clean sweep joins readiness inputs), P22
  (mandatory pre-checkpoint full sweep).
- **Implementation waves:** KS-A skeleton + purity-first + reporting → KS-B docs-domain
  detectors (1, 6, +5 per A-1 ruling) → KS-C graph + generation detectors (2, 3, 4, 5) →
  KS-D registry detectors (7, 8) + severity + determinism + the full constructed-drift
  matrix → KS-E guard subset + completeness census + handoffs + VERDICT + **family closure**.
- **Battery plan:** entry **1678/1678**; suite joins via the SYNC-D8 dated framework
  amendment (recorded on ratification, the SEED-D4/VER-D6 mechanism); battery at every
  code-wave close; the SYNC-D4 guard subset becomes permanent battery guards.
- **Documentation touchpoints:** THIS log (created now) · home-app README/GUIDE per wave ·
  DOCUMENTATION_INDEX rows · CHANGE_IMPACT_MATRIX row (KS-A) · framework README battery
  amendment (on ratification) · PHASE_14 Appendix A (Design Record + any A-1 amendment) ·
  status + memory per wave · at KS-E: the PHASE_05-family closure note in the status file.
- **Phase interfaces:** 5 (family closure) · 8/9/12/13 (consumed, extend-never-fork) ·
  15–18 (U6 enforcement instrument) · 19 (readiness input) · 22 (pre-checkpoint sweep).

### 4. ⏸ Decision pack — SYNC-D1..SYNC-D9 (defaults binding unless overridden; → contract Appendix A)

| # | Decision | Default in one line | Charter notes |
|---|---|---|---|
| SYNC-D1 | Engine home | `devseed` hosts `knowledge_sync` + the `knowledge/` detector core; the app's charter widens to "dev tooling" (README updated); alternative = a third dev-only app (P12 pattern) | dev-only is correct: repo-side maintenance, never production-runtime; devseed's guard factors don't gate a read-only sweep (the command is NOT a seeder — polarity/guard shape = KS-A design); scripts/ import mechanics = A-3 |
| SYNC-D2 | Detector inventory | the 8 §6.3 domains, each mapped to its inherited contract; unmapped detectors don't merge | **⚠ requires the A-1 ruling:** domain 5's regenerate-compare leg is void under GEN-D A1 (manifest handwritten) — expected: dated PHASE_14 amendment re-scoping domain 5 (path re-validation + topic-coverage vs graph) |
| SYNC-D3 | Severity + threshold | BLOCKER/WARN/INFO per §6.4; **exit-code failure threshold = any BLOCKER** (WARN/INFO report-only); acceptance lists visible + owner-attributed, never silent | |
| SYNC-D4 | CI/test-guard subset | permanent battery guards = dead-CI-guarded-path + hand-edit-in-fence + graph-invariant classes (the PkalsNavigationGuardTests extension pattern); everything else report-only | promoted classes become build-red forever |
| SYNC-D5 | Report format + acceptance | P13 envelope/body conventions VERBATIM; `var/knowledge_sync_reports/`; acceptance entries dated + owner-attributed, always printed | the P13 certified schema is the baseline (gate row 3) |
| SYNC-D6 | Modes | full sweep (default) + `--diff` (read-only git, changed-files scope) + `--deep` (expensive tiers); skips always printed | |
| SYNC-D7 | Graph-staleness method | cheap tier = census-counts vs graph (default sweep); deep tier = builder dry-run rebuild + body-hash compare (`--deep`); costs declared per detector | |
| SYNC-D8 | Battery membership | the suite joins the canonical battery as the FIFTH sequential member (dated framework-README amendment, SEED-D4/VER-D6 mechanism) | recorded on ratification |
| SYNC-D9 | Cadence + skills | on-demand + diff-mode after feature waves (15–18) + MANDATORY pre-checkpoint full sweep (22) + pre-deploy sweep (19 input); `/impact` + `/find-canonical` REMAIN (sync extends; retirement = later owner decision); cron/CI wiring OUT | |

**Rulings requested — including the A-1 disposition under SYNC-D2. On ratification:** answers
land in the contract's Appendix A (dated), the SYNC-D8 framework amendment is recorded, and
KS-A (skeleton + no-writes purity FIRST + reporting) is authorized (owner-gated).

### 5. KS-0 accounting

- **Git:** HEAD `49404001` · 0 staged · 2 stashes · 512 porcelain entries (the standing
  uncommitted campaign tree) · tree-state anchor sha256 `d4323026a122ebe4…` — reads only.
- **Battery:** **1678/1678** entry baseline (final Phase-13 4-suite run, re-verified this
  same session); NOT re-run at KS-0 (zero code — charter only).
- **Primary DB:** `inventory_db` sentinels ledger 170/Σ₹10,880.25 · users 48 · dev.min 0
  (full 34-anchor census EXACT at VER-E, same session); read-only census only.
- **Production safety:** nothing this sub-phase touches production or any runtime path —
  zero code, zero tests, zero migrations, zero corpus-doc edits (working documents only:
  this log + the campaign status/index/memory records).
- **Implementation status:** NOTHING implemented — no command, no detectors, no tests.
  KS-A is gated on the owner's SYNC-D1..D9 rulings (incl. A-1).

## KS-0 ratification — owner 2026-07-17 (verbatim)

> "I accept the defaults for SYNC-D1 through SYNC-D9 with one explicit clarification."
> SYNC-D1 approved exactly as proposed · **SYNC-D2 approved WITH the owner ruling replacing
> A-1: Phase-9 Amendment A1 remains authoritative; the manifest remains HANDWRITTEN and
> CI-guarded; domain 5 is PERMANENTLY re-scoped to manifest path validation + canonical
> topic coverage vs the graph + consistency validation; regenerate-compare is NOT part of
> Phase 14 and shall not be implemented** (recorded as the dated amendment in PHASE_14
> Appendix A) · SYNC-D3..D9 approved exactly as proposed. KS-0 accepted and closed; KS-A
> authorized.

Also recorded: the SYNC-D8 battery amendment (framework README, dated) — per SYNC-D1 the
engine is hosted in `devseed`, so its tests live in the EXISTING devseed suite (the third
sequential member's scope widens to seeder + knowledge_sync; no fifth suite — the D1⊓D8
coherent reading, disclosed).

## KS-A — Skeleton + purity + reporting — ✅ DONE 2026-07-17 · BATTERY 1691/1691

### 1. What landed (zero detector domains — skeleton/foundation ONLY, as ordered)

| Piece | Content |
|---|---|
| `devseed/knowledge/__init__.py` | The detector architecture: `Finding` (frozen: id · domain · severity · evidence · venue · accepted) · `SEVERITIES` (BLOCKER/WARN/INFO, SYNC-D3) · `DOMAINS` (the 8-domain inventory, each mapped to its inherited contract; **domain 5 encoded per the A-1 owner ruling** — manifest-sync: path validation + topic coverage + consistency, regenerate-compare absent by law) · `VENUES` (the 6 owning repair venues incl. the U8 money route) |
| `devseed/knowledge/report.py` | Deterministic report scaffolding (SYNC-D5 = the P13 conventions as FORMAT law): sorted body · sha256 body-hash · the run timestamp as the ONLY volatile field · totals per severity + accepted count · skips always printed · `SYNC_ENGINE_VERSION 0.1.0` · `FAILURE_THRESHOLD = BLOCKER` (SYNC-D3 ratified; changing it = owner + dated amendment, asserted in code) · **THE single write site** (report writer → `var/knowledge_sync_reports/`, gitignored) |
| `devseed/knowledge/acceptance.py` | Acceptance-list mechanics: dated + owner-attributed entries IN CODE (reviewed like any change); accepted findings keep severity, stay in every report, and are exempt ONLY from the exit threshold — never filtered |
| `devseed/knowledge/gitio.py` | Read-only git plumbing for `--diff`: verb ALLOW-LIST (`diff status log rev-parse ls-files show`) enforced at runtime (non-listed verb → ValueError) · `changed_files()` (diff vs HEAD + untracked) · `porcelain_hash()` (the Phase-0 tree-fingerprint, powering the identity proofs) |
| `manage.py knowledge_sync` | The command skeleton: `--diff` / `--deep` / `--report DIR` / `--skip DETECTOR` · runs the (EMPTY) detector registry · acceptance pass · deterministic report → var/ · exit per threshold · **prints "0 detector domains registered (KS-A skeleton)"** — an empty sweep is honest AND is the runtime identity proof. Help text states the no-`--fix` law |
| Purity-first tests (`test_knowledge_purity.py`, 8) | **LANDED WITH (not after) the foundation:** single-file-write-site pin (only report.py; target pinned to `var/knowledge_sync_reports`) · zero destructive filesystem calls · zero non-read-only git verbs (static) + the gitio allow-list runtime refusal · **no-`--fix` static pin** · domain/venue registry shape (incl. the A-1 encoding) · **runtime proof: full sweep AND diff-mode leave `git status --porcelain` hash + every model's row count byte-identical** |
| Report tests (`test_knowledge_report.py`, 5) | Sorted/hash-stable/envelope-only-timestamp · totals + threshold exit (WARN/INFO report-only; 1 unaccepted BLOCKER → exit 1) · **accepted BLOCKER printed-but-exempt** · explicit skips · disk round-trip |

The devseed ORM-purity suite (P12) automatically covers the new package — zero ORM writes,
scanned by the existing pins. Import-linter: zero new edges (the knowledge core imports
nothing above devseed).

### 2. Certification

- **Battery — NEW BASELINE 1691/1691** (4 sequential fresh-DB suites): 9-app 1002 (187.1s)
  + patterns_ai 528 (159.7s) + **devseed 83** (45.0s — 70 + 13 knowledge tests, the SYNC-D8
  amendment shape) + verification 78 (37.9s runner-total). Arithmetic: 1678 + 13 ✓.
- **Primary EXACT:** ledger 170/Σ₹10,880.25 · users 48 · dev.min 0.
- Git `49404001` · 0 staged · 2 stashes · porcelain 513 (KS-0's 512 + this phase's own new
  evidence log — expected, disclosed; the runtime identity proofs compare within-run).
- Zero detector domains, zero graph/docs/registry checks (as ordered) · zero corpus-doc
  edits · zero migrations · production untouched.

**Next: KS-B — docs-domain detectors (domains 1, 6, 5-as-rescoped): change-impact diff-mode
· route/model-map sweep · ownership/metadata/lifecycle · manifest path/coverage/consistency
— owner-gated.**

_KS-A closed 2026-07-17._

## KS-B — Docs-domain detectors — ✅ DONE 2026-07-17 · BATTERY 1705/1705

**Owner authorization (2026-07-17):** domains 1, 6, and 5-as-A-1-rescoped ONLY. Honored —
zero graph/generation/registry detectors; the manifest stays authoritative-handwritten;
regenerate-compare does not exist anywhere; zero documentation modified; zero findings
repaired.

### 1. Detector inventory (9 detectors registered; each cites its inherited contract)

| Detector id | Domain | Binding rule it implements | Severity classes | Mode |
|---|---|---|---|---|
| `code-docs.change-impact` | 1 | pkals_v2 MUST (`/impact` logic extended): changed config code/template files need a CHANGE_IMPACT_MATRIX row; matrix doc references must resolve | WARN (`d1.matrix.unrouted:` · `d1.matrix.dead-doc-ref:`) | diff + sweep |
| `code-docs.route-map` | 1 | graph mapping-law floor: live URL census ⇄ graph URL knowledge — **census + ids via the Phase-8 builder's own `walk_urls`/`url_node_id`, IMPORTED (extend-never-fork)** | WARN (`missing:`/`ghost:`) → venue graph | sweep |
| `code-docs.model-map` | 1 | same floor for models (builder's `project_apps` census) | WARN → venue graph | sweep |
| `ownership.matrix` | 6 | OWNERSHIP_MATRIX: every active doc has an owner concept (family-row matching w/ `<placeholder>` globs; census = the builder's own `doc_boundary()`) | WARN (`d6.ownership.unowned:`) | sweep |
| `ownership.metadata` | 6 | DOC_STANDARDS §13 (R2 7-field core; archive excluded by the census, matching "archive NEVER retrofitted") | WARN (missing-frontmatter · incomplete · bad-status) | sweep |
| `ownership.lifecycle` | 6 | DOC_STANDARDS §12 (superseded/archived ⇒ banner naming the successor) | WARN (`no-banner:`) | sweep |
| `manifest.paths` | 5 (A-1) | manifest path validation — the PkalsNavigationGuardTests class, report-side | **BLOCKER** (`d5.paths.dead:` · `unreadable` — the §6.4 dead-CI-guarded-path class) | sweep |
| `manifest.coverage` | 5 (A-1) | topic canonicals known to the graph (doc-node anchors) | WARN → venue graph | sweep |
| `manifest.consistency` | 5 (A-1) | handwritten-router consistency (non-empty topics; ambiguous match terms) | WARN + INFO | sweep |

Every finding carries the six fields (id · domain · severity · evidence · venue ·
accepted) — shape-pinned. **KS-B rule discovery (not an invention — a reading correction):**
§12 explicitly sanctions `frozen-vN` dated instances, and the Phase-9-ratified generated
layer carries `status: generated` (GEN-B validated 558/558 with it) — the first live sweep
flagged 560 false bad-status findings until the detector encoded the ACTUAL binding set;
fixed in-wave, test-pinned.

### 2. Constructed-drift proofs (every ordered class planted → caught, injected inputs only)

| Ordered failure class | Constructed case | Caught as |
|---|---|---|
| matrix routing failure | changed `config/production/views/unrouted.py` vs a matrix without its row | `d1.matrix.unrouted:` WARN (routed sibling NOT flagged) |
| matrix dead reference | row pointing at `docs/DEAD_REFERENCE.md` | `d1.matrix.dead-doc-ref:` WARN |
| route-map drift | live route absent from graph + graph ghost route | `missing:`/`ghost:` WARN both directions |
| model-map drift | same, models | both directions |
| ownership failure | orphan doc vs family+name rows | exactly `d6.ownership.unowned:` (owned docs clean) |
| metadata failures | no-frontmatter · 2-field frontmatter · `status: zombie` | missing-frontmatter · incomplete (names the missing fields) · bad-status (good doc clean) |
| lifecycle failure | superseded doc without banner | `d6.lifecycle.no-banner:` (bannered sibling clean) |
| manifest path failure | dead `also` path + unreadable manifest | **BLOCKER** ×2 classes |
| topic coverage failure | canonical unknown to the graph | `d5.coverage.graph-unknown:` WARN |
| consistency failures | empty topic + duplicated match term | WARN + INFO |

### 3. Live sweep (the real corpus — findings REPORTED, routed, untouched)

- **Full sweep ×2:** **0 BLOCKER · 356 WARN · 0 INFO** — exit 0 (WARN is report-only,
  SYNC-D3). Classes: `d6.metadata.missing-frontmatter` **136** (root canon like CLAUDE.md ·
  app READMEs · campaign evidence logs — the honest post-P7 state) ·
  `d6.ownership.unowned` **220** (matrix family rows lag the corpus growth). Both routed to
  venue `docs` (U6/matrix repair — the owner's queue, NOT this engine's). **Zero manifest
  BLOCKERs · zero route/model drift · zero dead matrix references** — manifest and graph are
  current.
- **Determinism:** body-hash identical ×2 (`DETERMINISM PAIR: True`).
- **Repository identity:** porcelain hash byte-identical around both sweeps; DB row counts
  identical (the KS-A runtime pins re-proven with 9 live detectors).
- **Diff-mode live (512-entry working tree):** 0 unrouted — every changed config code file
  matches a matrix family row (the planted case proves the detector still fires).

### 4. Certification

- Tests +14 (devseed suite 97): the constructed-drift matrix above + finding-shape +
  registry pin + report-order determinism. KS-A purity pins updated for a LIVE registry
  (sweep may raise on BLOCKERs — identity asserted regardless).
- **Battery — NEW BASELINE 1705/1705**: 9-app 1002 (182.4s) + patterns_ai 528 (166.2s) +
  **devseed 97** (46.2s) + verification 78. Arithmetic: 1691 + 14 ✓.
- **Primary EXACT:** ledger 170/Σ₹10,880.25 · users 48 · dev.min 0. Git `49404001` ·
  2 stashes · zero corpus-doc edits · zero repairs · zero migrations.

**Next: KS-C — graph + generation detectors (domains 2, 3, 4): validator re-run import ·
census-vs-graph tiers · `--deep` dry-run compare · stale-output + fence-integrity +
hand-edit detection — owner-gated.**

_KS-B closed 2026-07-17._

## KS-C — Graph + generation detectors — ✅ DONE 2026-07-17 · ⚠ §16.3 INCIDENT (disclosed, neutralized, pinned) · BATTERY 1723/1723

### 1. ⚠ INCIDENT KS-C-I1 — the imported validator's repro check REWROTE the graph (the R-10 hazard, fired under this engine)

**What happened:** the first KS-C sweep ran `graph.validator` — the IMPORTED Phase-8
validator's `main()` — whose **REPRODUCIBILITY check re-runs the builder as a SUBPROCESS
and rewrites `docs/knowledge_graph.json` IN PLACE** (validator line ~264; its own docstring:
"READ-ONLY **except** the reproducibility check"). This is exactly the Phase-8 R-10
residual ("in-place-repro hazard from the disclosed+restored overwrite incident") — fired
again, this time under knowledge_sync.

**How it evaded the KS-A guards:** (a) the write happens in a CHILD PROCESS — in-process
interception can't see it; (b) the runtime identity proof used `git status --porcelain`,
which is **BLIND to content changes in UNTRACKED files** — the graph (created Phase 8,
never committed under the campaign no-commit law) stayed a `??` entry before and after.

**Damage:** the CERTIFIED graph bytes (`sha256:85b7fd6d…`, KG cert 2026-07-16) were
replaced by an in-place rebuild of TODAY's tree (`sha256:203547859d65…`, `git_head:
"unknown"`, 12 apps incl. devseed+verification, 925-doc census). **No copy of the certified
bytes exists anywhere** (repo backups = 2026-07-13, pre-Phase-8; the graph was untracked).
The rebuilt graph is internally valid (self-hash ✓, schema ✓) and DETERMINISTIC (the
write-free dry-run reproduces it byte-identically) — but it is NOT the certified artifact,
and the KG certification's hash anchor no longer matches disk.

**Neutralization (in-wave, permanent):** the validator wrapper now **no-ops the repro
subprocess** for the duration (restored after); the thereby-vacuous check is DISCLOSED as a
standing INFO finding (`d2.validator.repro-check-neutralized`) on every run — never silent.
The write-free equivalent lives in `--deep graph.deep-rebuild` (in-memory dry-run compare).
**Two permanent pins added:** (1) the real-validator no-write pin (graph hash identical
across a wrapper run + subprocess.run restored); (2) the artifact-identity battery pin —
a FULL `--deep` sweep must leave the graph + all 558 generated files **byte-identical by
explicit hash** (the porcelain-blindness lesson, now unforgeable). Proven live: deep sweep
×2 → artifacts byte-identical · determinism pair TRUE.

**Owner decision required (routed, NOT taken by this engine):** either **(a)** accept the
2026-07-17 in-place rebuild as the current graph via a dated Phase-8-cert amendment, then
regenerate the 558 outputs per the Phase-9 runbook (the 558 stale findings then converge to
zero); or **(b)** direct a fresh Phase-8 build/validate ceremony to re-certify. Until then
the 558 `d4.stale` findings stand as the honest record.

### 2. Detector inventory (+8 → 17 registered; deep tier per SYNC-D7)

| Detector id | Domain | Inherited contract | Severity | Mode |
|---|---|---|---|---|
| `graph.validator` | 2 | PHASE_08 §6.7 validator re-run — IMPORTED (FATAL→BLOCKER · FINDINGS→WARN · INFO→INFO) + the standing repro-neutralized INFO | BLOCKER/WARN/INFO | sweep |
| `graph.deep-rebuild` | 2 | PHASE_08 §6.7 deep tier: builder dry-run **with its file-write captured in memory** (nothing touches disk) → content-hash compare; "rebuild would differ" = stale graph | WARN | **--deep** |
| `graph.census` | 3 | cheap-tier census counts vs graph node counts — live censuses = the builder's OWN importable walkers (apps · docs) | WARN | sweep |
| `graph.completeness` | 3 | disk→graph direction only (docs in the builder's boundary absent from the graph); graph→disk = the validator's own check, never duplicated | WARN | sweep |
| `graph.consistency` | 3 | graph self-integrity via the Phase-9 generator's OWN `load_graph()` gate (hash recompute + schema pin — the R-10 hand-edit guard, imported) | BLOCKER | sweep |
| `generated.stale-banner` | 4 | PHASE_09 §6.6 stale-output contract: stamped `graph:<hash12>` vs current (WARN, remedy quoted from the file's OWN banner) + banner/stamp corruption (BLOCKER — a generated file that stops declaring itself) | BLOCKER/WARN | sweep + diff |
| `generated.fences` | 4 | PHASE_09 fence integrity corpus-wide (begin/end pairing; markers quoted in code blocks = grammar documentation, stripped) | BLOCKER | sweep |
| `generated.hand-edit` | 4 | GEN-E hand-edit mechanics as a detector: IN-MEMORY render through the generator's own functions (`write()` never called) vs disk; current-stamp+diff = hand-edit (BLOCKER); old-stamp files belong to `stale`, orphans = WARN | BLOCKER/WARN | **--deep** |

Deep-gated detectors that don't run are RECORDED in the envelope (`(deep-gated)` suffix) —
never silent (test-pinned).

### 3. Constructed-drift proofs (all 10 ordered classes; injected inputs only)

stale generated doc (old stamp → WARN w/ remedy quoted) · graph hash mismatch
(refusing loader → BLOCKER) · banner corruption (missing Regenerate line → BLOCKER, names
the missing part) · fence corruption (orphan begin → BLOCKER; paired + clean + code-block
examples pass) · hand-edited generated doc (current-stamp + byte-diff → BLOCKER; stale file
NOT double-reported; orphan → WARN) · census mismatch (app 3≠1 → WARN) · completeness
failure (BRAND_NEW.md unindexed → WARN) · validator failure propagation (FATAL→BLOCKER +
WARN + INFO streams; crash → BLOCKER; clean → zero) · deep-mode builder comparison (differ →
WARN; equal → zero; live: the isolated dry-run proven file-untouched by mtime+bytes) ·
diff-mode reporting (changed-file scoping to `docs/features/` proven).

### 4. Live proofs (the real corpus)

- **Full deep sweep ×2:** `0 BLOCKER · 915 WARN · 2 INFO`, exit 0 — WARN = the 558
  `d4.stale` (the incident's honest residue) + 136 missing-frontmatter + 220 unowned +
  1 validator-routed finding; INFO = the validator's own info + the standing
  repro-neutralized disclosure. **Determinism pair TRUE (cheap AND deep) · knowledge
  artifacts byte-identical by explicit hash · porcelain identity TRUE · DB row counts
  identical.**
- **No `deep-rebuild.would-differ`:** the write-free dry-run reproduces the on-disk graph
  byte-for-byte — confirming the on-disk graph = a deterministic build of today's tree.
- **No hand-edit findings:** every diff vs the current-graph render is stamp-explained
  (stale, not edited) — the dedup design working as specified.
- **Fence detector refinement (in-wave):** the first sweep flagged the PHASE_05 contract —
  its fence-grammar EXAMPLE inside a markdown code block; markers in code blocks/spans are
  documentation, now stripped before scanning (test-pinned). GEN-C's zero-live-fences state
  re-confirmed.

### 5. Certification

- Tests +18 (devseed suite 115): the 10-class constructed matrix + the 2 incident pins +
  deep-gating transparency + registry pin (17 detectors + DEEP_ONLY set).
- **Battery — NEW BASELINE 1723/1723**: 9-app 1002 (186.5s) + patterns_ai 528 (160.1s) +
  devseed 115 (44.9s) + verification 78. Arithmetic: 1705 + 18 ✓.
- **Primary EXACT:** ledger 170/Σ₹10,880.25 · users 48 · dev.min 0. Git `49404001` ·
  2 stashes. No regeneration · no rebuild reached disk after neutralization · no doc/graph/
  report edits · no repairs.

**Next: KS-D — registry detectors (domains 7, 8) + severity engine certification + the full
constructed-drift matrix + `--diff` end-to-end — owner-gated. The KS-C-I1 graph decision
(a/b above) awaits the owner independently.**

_KS-C closed 2026-07-17._

## KS-C-I1 disposition — owner 2026-07-17 (verbatim)

> "I choose OPTION (a). Record a dated Phase-8 certification amendment accepting the
> deterministic rebuilt knowledge graph as the new certified baseline. Do NOT regenerate
> documentation during KS-D. The current stale-output findings remain the honest expected
> state until the future regeneration phase. This disposition changes only the graph
> certification baseline. It does NOT change any contracts, detector behavior, or reporting
> semantics."

**Recorded:** dated amendment appended to `docs/KNOWLEDGE_GRAPH_CERTIFICATION.md` — new
certified baseline `sha256:203547859d6561316de21b2e3e1fb05e1de70fef440e36e89ac461922f7dd372`
(12 apps · 925 docs census); the 558 `d4.stale` findings = the honest expected state until
the regeneration phase. Zero detector/report changes (as ruled).

## KS-D — Registry detectors + severity + determinism — ✅ DONE 2026-07-17 · ALL 8 DOMAINS LIVE (23 detectors) · BATTERY 1741/1741

### 1. Detector inventory (+6 → 23; each citing its inherited contract)

| Detector id | Domain | Inherited contract | Severity |
|---|---|---|---|
| `dataset.registry` | 7 | PHASE_12 SEED-F handoff §5.2 (declared-vs-implemented drift): registry shape (class ∈ the 6-class DATA-D4 taxonomy) · implemented-without-CONTENT · CONTENT-without-declaration · duplicate-golden hygiene | WARN + INFO |
| `dataset.spec-version` | 7 | SEED-F spec-version pinning — the THREE-WAY pin: `devseed.guard` ⇄ `verification.report` ⇄ the frozen spec §10 semver text | WARN |
| `dataset.golden-agreement` | 7 | spec §7 golden values = owner change-control: every registry `expected` must appear in the frozen spec text | WARN |
| `verification.registry` | 8 | PHASE_13 VER-E §1 certified 19-check census (quoted as the drift BASELINE, cited — not re-implemented): drift both directions + machine-readability | WARN |
| `verification.citations` | 8 | VER-D4 citation law: every statically-extracted check carries a citation; cited sources RESOLVE (the A-4 file-level resolution table) | WARN |
| `verification.report-schema` | 8 | VER-D certified schema (engine 1.0.0 envelope/body key sets — the P19/20/21 dependency); drift = dated-amendment territory | WARN |

All read their SINGLE sources (`SCENARIOS` · `CONTENT` · `SPEC_VERSION` pins · the live
`verification.checks` package via static extraction · a live schema probe through
`verification.report.build_report` itself) — nothing redefined.

### 2. Severity-engine certification + acceptance interactions

- Threshold re-certified: only UNACCEPTED BLOCKERs fail the exit (mixed-severity matrix).
- **Acceptance full cycle:** accepted BLOCKER = exempt from the threshold but PRINTED with
  its severity intact; **stale acceptance entries (an acceptance whose finding no longer
  fires) now SURFACE in the envelope + stdout** (`stale_acceptance`, sorted — the KS-A
  mechanic completed as promised; command-level proven).

### 3. Constructed-drift proofs (the 11 ordered classes; injected inputs only)

missing registry entry (CONTENT ghost-world → implemented-not-declared WARN) ·
implemented-state mismatch (declared-without-content WARN) · invalid registry reference
(class "mystery" → WARN) · duplicate registry entries (shared golden → INFO) · SPEC_VERSION
mismatch (doc v2.0.0 vs pins 1.0.0 → WARN naming all three surfaces) · scenario drift
(registry 777.77 absent from spec text → WARN) · verification check drift (uncertified +
vanished checks, both directions) · unreadable registry · missing citation (VER-D4 quoted) ·
broken citation target (dead ARCHITECTURE_V2 → WARN; resolving target clean) · report-schema
dependency drift (envelope+body key-set drift, P19/20/21 named) · acceptance interactions +
threshold behavior (above). **The eight-domain constructed matrix is COMPLETE** (KS-B: 10
classes · KS-C: 10 classes · KS-D: 11 classes) — meta-pinned: every DOMAINS key has a
registered detector, forever.

### 4. Live proofs (all 23 detectors, deep mode ×2)

- **d7/d8 live findings: NONE — the registries are CLEAN** (four-surface SEED-F agreement
  holds · the live check census == the certified 19 · every citation resolves · the live
  report schema == the certified key sets). Test-pinned as live-green assertions.
- Sweep totals unchanged from KS-C (0 BLOCKER · 915 WARN · 2 INFO — the disposition-expected
  residue) · **determinism pair TRUE · knowledge artifacts byte-identical by explicit hash ·
  porcelain tree identity TRUE · DB row counts identical** · `stale_acceptance: []`.

### 5. Certification

- Tests +18 (devseed suite 133): d7 ×7 · d8 ×7 · severity/acceptance ×3 · the eight-domain
  meta-pin · registry pin updated to 23 detectors.
- **Battery — NEW BASELINE 1741/1741**: 9-app 1002 (182.9s) + patterns_ai 528 (159.2s) +
  devseed 133 (44.6s) + verification 78 (20.0s). Arithmetic: 1723 + 18 ✓.
- **Primary EXACT:** ledger 170/Σ₹10,880.25 · users 48 · dev.min 0. Git `49404001` ·
  2 stashes. Zero repairs · zero regeneration · zero graph writes (the §16.3 pins stood
  guard throughout) · docs edits = the owner-ordered certification amendment + this log.

**Next: KS-E — the SYNC-D4 guard subset + detector-inventory completeness census vs the
inherited contracts + §6.6 handoffs (18/19/22) + U6 docs + PHASE-14 VERDICT + the
PHASE_05-family closure — owner-gated.**

_KS-D closed 2026-07-17._

## KS-E — Guard subset + certification + handoffs + family closure — ✅ DONE 2026-07-17 · 🏁 PHASE 14 CLOSED

### 1. Permanent detector completeness census — every inherited obligation accounted, exactly once

| Inherited contract requirement | Implementing detector(s) | Location | Owner |
|---|---|---|---|
| P5 §6.1.18 hook: change-impact tool (pkals_v2 MUST) | `code-docs.change-impact` (diff + sweep) | `knowledge/d1_code_docs.py` | Phase 14, permanent |
| P5 §6.1.17 / pkals_v2 MUST: route-map drift | `code-docs.route-map` (builder walkers imported) | d1 | " |
| P5 §6.1.17 / pkals_v2 MUST: model-map drift | `code-docs.model-map` | d1 | " |
| P8 §6.7: validator re-run against today's tree | `graph.validator` (imported; repro subprocess neutralized — KS-C-I1) | `knowledge/d2_graph.py` | " |
| P8 §6.7 deep tier: rebuild-would-differ | `graph.deep-rebuild` (`--deep`, in-memory write capture) | d2 | " |
| P8 §6.7 cheap tier: census counts vs graph | `graph.census` + `graph.completeness` (builder's own walkers; disk→graph direction only — graph→disk stays the validator's) | `knowledge/d3_graph_census.py` | " |
| P8/P9 graph self-integrity (R-10 hand-edit guard) | `graph.consistency` (the P9 `load_graph()` gate, imported) | d3 | " |
| P9 §6.6 stale-output contract (graph-hash stamps + regeneration remedy) | `generated.stale-banner` (+ banner corruption = BLOCKER) | `knowledge/d4_generated.py` | " |
| P9 fence rules corpus-wide | `generated.fences` | d4 | " |
| P9/GEN-E hand-edit detection | `generated.hand-edit` (`--deep`, in-memory render-compare, `write()` never called) | d4 | " |
| GEN-D A1 + A-1 owner ruling: manifest (handwritten) path/coverage/consistency — regenerate-compare NEVER | `manifest.paths` (BLOCKER class) + `manifest.coverage` + `manifest.consistency` | `knowledge/d5_manifest.py` | " |
| DOC_STANDARDS §11 / OWNERSHIP_MATRIX | `ownership.matrix` | `knowledge/d6_ownership_metadata.py` | " |
| DOC_STANDARDS §13 (R2 7-field core) | `ownership.metadata` | d6 | " |
| DOC_STANDARDS §12 lifecycle banners | `ownership.lifecycle` | d6 | " |
| P12 SEED-F §5.2: declared-vs-implemented + registry shape | `dataset.registry` | `knowledge/d7_dataset_spec.py` | " |
| P12 SEED-F: SPEC_VERSION pinning (three-way) | `dataset.spec-version` | d7 | " |
| P12/spec §7: golden owner-change-control agreement | `dataset.golden-agreement` | d7 | " |
| P13 VER-E §1: certified check census drift | `verification.registry` | `knowledge/d8_verification_registry.py` | " |
| P13 VER-D4: citation law + resolution | `verification.citations` | d8 | " |
| P13 VER-D: certified report schema (P19/20/21 dependency) | `verification.report-schema` | d8 | " |

**23 detectors · 8 domains · zero unaccounted obligations · zero duplicates** (each
requirement → exactly one detector; the eight-domain completeness meta-pin + the 23-id
registry pin keep it that way forever). The one contract line NOT implemented =
regenerate-compare, by OWNER LAW (A-1 dated amendment), encoded in the domain registry and
test-pinned.

### 2. The SYNC-D4 permanent guard subset + purity re-certification

**Guard subset (owner-ratified default; `tests/test_knowledge_guards.py`, +4 battery
tests):** dead-manifest-path · fence-corruption · graph-invariant-FATALs · hand-edited-graph
(the `load_graph` gate) — the four BLOCKER classes promoted to BUILD-RED forever, each a
LIVE run of its existing detector (the PkalsNavigationGuardTests extension pattern; no new
detection logic). Everything else stays report-only per SYNC-D3.

**Every permanent purity pin re-certified green (terminal run):** read-only behavior ·
single-file-write-site (report.py → `var/knowledge_sync_reports/` only) · zero destructive
filesystem calls · zero non-read-only git (static + runtime refusal) · zero ORM writes (the
devseed P12 pins cover the package) · no `--fix` (static pin) · **the §16.3 artifact pin:
a full `--deep` sweep leaves the graph + all 558 generated outputs byte-identical by
explicit hash.** Terminal live quartet: **DETERMINISM ✓ · ARTIFACTS ✓ · TREE ✓ · DB ✓**
(deep ×2, all four identities byte-exact).

### 3. Documentation reconciliation

KNOWLEDGE_SYNC_LOG (this close) · devseed README + GUIDE (terminal stamps) ·
DEPLOYMENT_CAMPAIGN_STATUS (Phase 14 COMPLETE; next = Phase 15) · DOCUMENTATION_INDEX (log
row = closed state) · campaign memory. Zero design/spec changes; the KS-C-I1 amendment
(KNOWLEDGE_GRAPH_CERTIFICATION) stands as recorded at KS-D.

### 4. Handoffs (§6.6 + the owner-ordered interfaces)

**4.1 → Phase 18 (Future Feature Documentation Updates; KOS-compat noted per the standing
owner guidance — record-only, no scope growth):** knowledge_sync = the U6 ENFORCEMENT
INSTRUMENT for feature phases 15–17: run `manage.py knowledge_sync --diff` after each
feature wave — the findings list IS the docs work queue (each finding names its venue);
Phase 18 closes when a FULL sweep is BLOCKER/WARN-clean or every residue is owner-accepted
(visible, dated, attributed — acceptance entries in `knowledge/acceptance.py`, decisions
quoted into the P18 record). The 558 `d4.stale` + 136 missing-frontmatter + 220 unowned
WARNs = the standing opening queue.

**4.2 → Phase 19 (deployment verification workflow):** a drift-clean sweep (threshold =
BLOCKER-free; WARN residue owner-judged) joins the READINESS INPUTS alongside Phase 13's
green `verify_production` — the runbook names BOTH instruments: `manage.py knowledge_sync`
(exit 0) + `manage.py verify_production` (exit 0). Sync is dev-side only (devseed is absent
in production — the deployed system never carries it); the pre-deploy sweep runs on the dev
tree that is about to ship.

**4.3 → Phase 22 (final deployment checkpoint):** a MANDATORY pre-checkpoint FULL sweep
(`--deep`) — the ONE commit captures a drift-clean knowledge corpus; any remaining findings
must be owner-accepted and LISTED in the checkpoint record (envelope totals + body_hash
quoted). The stale-output residue must be resolved by then (the future regeneration phase)
or explicitly owner-accepted into the checkpoint.

### 5. Terminal battery + certifications

- **TERMINAL PHASE-14 BASELINE 1745/1745** (4 sequential fresh-DB suites): 9-app 1002
  (188.0s) + patterns_ai 528 (158.9s) + **devseed 137** (44.3s — 70 seeder + 67 knowledge)
  + verification 78 (20.7s). Phase arithmetic: entry 1678 → +13 (A) +14 (B) +18 (C) +18 (D)
  +4 (E guards) = **1745 ✓**.
- Determinism/body-hash/report stability re-certified (terminal deep pair) · detector
  inventory pinned (23) · acceptance behavior certified (exempt-but-printed + stale
  surfacing) · repository identity ✓ · artifact identity ✓ · **primary database identity:
  ledger 170/Σ₹10,880.25 · users 48 · dev.min 0 — EXACT.** Git `49404001` · 2 stashes.

### 6. 🏁 PHASE-14 VERDICT

**PHASE 14 COMPLETE — KNOWLEDGE SYNC CERTIFIED.** `manage.py knowledge_sync`: **23
detectors · 8 domains · full-sweep/`--diff`/`--deep` · deterministic body-hash-stable
reports · severity-classified (threshold = any unaccepted BLOCKER) · every finding names
its owning repair venue · acceptance visible-never-silent · PURE DETECTOR (no `--fix`,
ever).** Permanent guarantees: the purity pin family (write-free by static scan + runtime
quartet + the §16.3 artifact pin) · the SYNC-D4 guard subset (4 BLOCKER classes =
build-red) · extend-never-fork (every census/gate/gate-function imported from its owning
phase). Incident KS-C-I1 disclosed → neutralized → owner-disposed (option (a), new
certified graph baseline `203547859d65…`) → pinned unforgeable. Battery **1745/1745** ·
primary EXACT · repository + artifacts byte-certified.

### 7. 🏁 PHASE_05 DOCUMENTATION FOUNDATION FAMILY — CLOSED

With knowledge_sync live, **every automation hook the parent contract declared (§6.1.18)
is delivered**: the graph builder (Phase 8) · the card/index generators (Phase 9) · the
`manage.py knowledge_sync` drift detector extending `scripts/pkals_canonical.py`, the
`/impact` + `/find-canonical` skills, and PkalsNavigationGuardTests (Phase 14) · the
CI-guard extension points (the SYNC-D4 subset). **The family 5 → 6 → 7 → 8 → 9 → 14 is
COMPLETE:** Standard (5) → census (6) → cleanup (7) → graph (8) → generation (9) →
standing drift detection (14). Documentation drift — "an architecture bug" (CLAUDE.md
rule 12) — now has its permanent instrument. **Next: Phase 15 (BOD) — owner-gated.**

_KS-E closed 2026-07-17 · Phase 14 closed 2026-07-17._
