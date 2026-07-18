---
id: docs-campaign-contracts-phase-00-safety-snapshot
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 0 Execution Contract — Safety Snapshot

> Authored 2026-07-12 under the contract-first directive. Inherits every universal invariant in
> [README.md](README.md) (U1–U14) — this contract only adds phase specifics and tightenings.
> **This is a DECISION FRAMEWORK + execution contract.** It deliberately does NOT choose a
> snapshot mechanism: §6 presents the four supported options neutrally; the owner chooses at the
> SNAP-0 decision point, and the decision is recorded in the Decision Record appendix of this
> file. Executable by Claude, GPT, Gemini, or a human engineer with no chat history.

## 1. Phase objective

Create at least one validated, restorable, off-working-tree copy of the campaign's uncommitted
body of work, so that no single mistake or failure can destroy it.

**Why this is critical before deployment:** every line of code and documentation produced since
2026-07-04 — the operational-foundation freeze closeout, R10 machines, OP-1 hardening, Phase-3
configuration, the entire V1.1 sprint, three role-certification campaigns with their security
fixes (S2 public-signup, S3 email-takeover, BUG-1/2/3, BUG-E1, MGT-B-1, #5, MGT-F-1), and all
campaign documents including these contracts — exists ONLY as bytes in one working tree on one
disk. The campaign's own no-commit rule (U2) means git protects none of it. A single accidental
`git checkout .`, `git clean -fd`, `git reset --hard`, an editor/tool mishap, or a disk failure
erases ~8 days of certified work with no recovery path. Every additional campaign session
increases the exposure. Phase 0 exists to close this window; phases 1–22 all depend on it.

## 2. Scope

### 2.1 Current repository facts (measured 2026-07-12 — re-verify at execution, §17.4)

| Fact | Value |
|---|---|
| Git toplevel | `/home/tech/umesh-personal` — a personal MONO-REPO; the project is the `django_inventory/` subdirectory; sibling dirs (`Django_app`, `DSA`, `sw obsidian`, …) are unrelated personal content |
| HEAD | `49404001` (2026-07-04, "docs: mark roadmap R1 completed") on branch `new_flask_app`; `main` exists |
| Remotes | `origin` + `upstream` → same GitHub repo (`github-personal:umesh29032/umesh-personal.git`, SSH) |
| Dirty state | 308 porcelain lines = **182 modified + 494 untracked files (dirs collapse in porcelain) + 1 working-tree deletion** (`config/production/templates/production/product_patterns_edit.html`) — ALL inside `django_inventory/`, 0 outside |
| Sizes | untracked payload ≈ 9 MB · project excl. venv ≈ 648 MB · venv `env/` 279 MB (rebuildable) · `.git` 100 MB · free disk 388 GB (space is a non-issue) |
| Pre-existing stashes | 2 (`stash@{0}` "arch wip" on new_flask_app, `stash@{1}` on main) — part of `.git` state, MUST NOT be touched or reused by this phase |
| Filesystem | ext-family on NVMe (`statfs` reports ext2/ext3-class) → **no btrfs/ZFS CoW snapshots available**; LVM availability unknown (executor checks `lsblk`/`lvs` if option D is chosen) |

### 2.2 Working-tree-only risk — assets INVISIBLE to git

`.gitignore` excludes three asset classes that are part of the real recovery picture and that
**no git-based snapshot (options A/B) can capture**:

| Asset | Why it matters |
|---|---|
| `.env` (django_inventory/) | secrets + environment config; without it the app does not run. Contains credentials — storage location of any snapshot that includes it must be treated as secret-bearing |
| `media/` + `config/media` | uploaded pattern photos/videos — append-only evidence data (U13); unrecoverable if lost |
| local PostgreSQL dev DB | not a file in the tree at all; holds the DEV worlds and probe targets every certification references (LOWER-002, XFB-001, worker pk=25, …). Capturable only via `pg_dump` |
| `env/` venv | rebuildable from requirements — capture optional, default skip |

**In scope:** deciding + executing + validating the snapshot; recording recovery procedures.
**Out of scope:** any application code change, any test, any migration, battery, certification
work, docs cleanup, pushing to remotes (unless the owner explicitly selects an offsite variant
in D2), touching the 2 pre-existing stashes, any `.git` maintenance (`gc`, `prune`,
`reflog expire` — FORBIDDEN here and until phase 22).

## 3. Success criteria

Phase 0 is DONE when ALL hold:
1. Owner decision recorded (Decision Record appendix): mechanism (D1), storage location (D2),
   scope of git-invisible assets (D3), refresh cadence (D4), retention (D5).
2. Snapshot artifact(s) exist at the recorded location(s), created by the chosen mechanism's
   §6 procedure.
3. Validation passed per §6's per-mechanism validation procedure INCLUDING a restore test to a
   scratch directory with spot-diffs (§5).
4. Live working tree proven unmutated: `git status --porcelain` output byte-identical
   before/after execution (option A excepted ONLY by its documented ref/tag mutations — tree and
   index still identical).
5. Recovery procedure for the chosen mechanism copy-pasted into the Decision Record (so recovery
   never requires re-deriving it).
6. Status file + this contract's Decision Record + memory (if available) updated; snapshot
   manifest (§8) written.

## 4. Rules of engagement (deltas beyond U1–U14)

- **Read-only until the owner decides.** SNAP-0 produces a recommendation + decision request and
  STOPS. No snapshot command runs before the Decision Record is filled.
- **U2 interaction is mechanism-specific and must be honored as documented in §6.** Options C/D
  are U2-clean (zero git interaction). Options A/B create git objects/refs: they require the
  owner's explicit U2 waiver, which the Decision Record captures. Even under a waiver: no push
  (unless D2 says offsite-git), no branch switch, no checkout of any other ref into the live
  tree, no history rewrite.
- **The live working tree is sacred.** No procedure step may run `git checkout <ref> -- .`,
  `git switch` to another branch, `git clean`, `git reset --hard`, or extract an archive over
  the live tree. Recovery always lands in a SEPARATE directory first (§6 recovery procedures).
- Snapshot artifacts live OUTSIDE the repo working tree (except option A's in-repo refs), at the
  D2-recorded path. If `.env` or a DB dump is included (D3), the artifact is secret-bearing:
  restrict filesystem permissions (`chmod 600`), never upload to any service the owner did not
  name in D2.
- This phase NEVER runs the battery and NEVER touches application code (tighter than U5: there
  is no code-change branch in this phase at all).

## 5. Evidence standard

Every claim in the evidence section carries its artifact:
- Exact commands executed + their output (success and failure).
- `sha256sum` of every produced artifact, recorded in the manifest.
- Pre/post `git status --porcelain | sha256sum` comparison (tree-unmutated proof, criterion §3.4).
- Restore-test proof: extraction/clone/copy into a scratch directory, then byte-diffs of at
  least: 1 modified file (e.g. `django_inventory/CLAUDE.md`), 1 untracked file (e.g. a campaign
  contract), the 1 deleted file proven ABSENT, and — if D3 included them — 1 media file and the
  `.env` (compare checksums, do not print contents).
- Counts census: files in artifact vs files expected (tar listing count / bundle `verify` output
  / `diff -r` summary), with the arithmetic shown.

## 6. Methodology — the option matrix, then per-mechanism procedures

### 6.0 The owner decision point (SNAP-0)

Present this section to the owner; record answers in the Decision Record appendix:

| # | Decision | Options |
|---|---|---|
| D1 | Mechanism | A git-commit-and-tag · B git bundle · C tarball · D filesystem copy/snapshot — or a combination (e.g. C now + A at phase 22; combinations are legitimate) |
| D2 | Storage location | same disk (weakest — survives mistakes, not disk failure) · second local disk/USB · offsite (private GitHub push [A/B only] or owner-named cloud/drive) — location string recorded verbatim |
| D3 | Git-invisible assets (§2.2) | include `.env`? include `media/`? include `pg_dump` of dev DB? include `env/` venv (default: no, rebuildable)? — options C/D can include all; options A/B can include NONE of them (choosing A/B alone = accepting those assets stay single-copy, or pairing with a small C-archive for just those assets) |
| D4 | Refresh cadence | once-now · at every phase close · at every session close (each refresh = re-run SNAP-1 validation; stale snapshots protect stale states) |
| D5 | Retention | keep all · keep last N (never silently overwrite the only copy — new artifact first, verify, then owner decides deletion of old) |

### 6.1 Option A — git commit + tag (in-repo, no branch switch)

Commit the working tree ON the current branch, tag it, then move the branch pointer back —
tree and index end byte-identical; the snapshot survives as a tagged commit.

```bash
cd /home/tech/umesh-personal
git add -A                                   # stages all 182M/494U/1D (respects .gitignore)
git commit -m "SNAPSHOT 2026-07-12: pre-deployment campaign working tree (Phase 0)"
git tag snapshot-campaign-2026-07-12
git reset --mixed HEAD~1                     # branch pointer back to 49404001; tree UNTOUCHED
git status --porcelain | wc -l               # must equal pre-snapshot count again
```

- **Advantages:** zero external storage; full git integrity (checksummed objects); trivial diffing
  against any ref; the phase-22 commit can later reference it; captures the deletion natively.
- **Disadvantages:** requires U2 waiver; single-disk unless pushed (D2); CANNOT capture §2.2
  assets; `git add -A` stages the whole mono-repo (currently safe — 0 dirty paths outside
  django_inventory/ — re-verify at execution); the tagged commit sits on the branch's history
  DNA only via the tag (branch itself is reset back).
- **Why not `git stash create`:** produces commit objects without touching anything, BUT ignores
  the 494 untracked files — inadequate; `stash push -u` mutates the tree — forbidden.
- **DANGER note:** never `git switch`/`checkout` to the tag or any branch afterward — that
  overwrites the live tree (§4).
- **Recovery:** `git worktree add /tmp/recovery snapshot-campaign-2026-07-12` (non-destructive,
  separate directory), copy needed files back manually; or clone the repo elsewhere and check
  the tag out there. NEVER check the tag out in the live tree.
- **Validation:** `git tag -l` shows the tag · `git diff snapshot-campaign-2026-07-12 --stat`
  vs live tree = empty (immediately after creation) · `git status` count restored · worktree
  restore-test + §5 spot-diffs · `git fsck --no-dangling` clean.
- **Failure scenarios:** commit hooks interfere (bypass with `--no-verify` if owner approves;
  record) · interrupted between commit and reset → branch points at snapshot: recover with
  `git reset --mixed 49404001` (tree stays intact; do NOT use --hard) · accidental push —
  forbidden unless D2 offsite.

### 6.2 Option B — git bundle (portable single file, builds on A)

A bundle needs commit objects, so B = A's commit/tag steps + `git bundle`, then the bundle file
can move offsite even though the repo never pushes.

```bash
# after A's commit+tag+reset:
git bundle create /path/from/D2/campaign-snapshot-2026-07-12.bundle snapshot-campaign-2026-07-12
git bundle verify /path/from/D2/campaign-snapshot-2026-07-12.bundle
```

- **Advantages:** single portable file with git integrity; movable to USB/cloud without any
  remote configured; verifiable anywhere (`git bundle verify`).
- **Disadvantages:** everything A has (U2 waiver, no §2.2 assets) + one more artifact to store;
  bundle contains full history reachable from the tag (~100 MB-class file).
- **Recovery:** `git clone /path/campaign-snapshot-2026-07-12.bundle /tmp/recovery` →
  `git -C /tmp/recovery checkout snapshot-campaign-2026-07-12`; copy files back manually.
- **Validation:** `git bundle verify` OK · clone-based restore test + §5 spot-diffs · sha256
  recorded.
- **Failure scenarios:** as A, plus bundle file truncation (verify catches) · storing the only
  bundle on the same failing disk (D2 exists to prevent this).

### 6.3 Option C — tarball archive (U2-clean, git-free)

```bash
cd /home/tech/umesh-personal
tar --exclude='django_inventory/env' \
    -czf /path/from/D2/django_inventory-snapshot-2026-07-12.tar.gz django_inventory
# D3 additions: drop the --exclude for env/ if owner wants venv; .env and media/ are inside
# django_inventory/ and are INCLUDED by default with this command — exclude them only if D3 says so.
# D3 DB dump (separate artifact):
#   pg_dump <dbname> | gzip > /path/from/D2/devdb-snapshot-2026-07-12.sql.gz
sha256sum /path/from/D2/*.tar.gz
```

- **Advantages:** zero git interaction (U2 pristine); captures EVERYTHING including §2.2 assets
  (.env, media) by default; restorable by any human with `tar`; simplest mental model; scoped to
  django_inventory only (mono-repo siblings untouched).
- **Disadvantages:** no dedup/history (each refresh ≈ 650 MB, or ~370 MB excluding media —
  irrelevant at 388 GB free); no git-level integrity (mitigated by sha256 manifest); the
  working-tree DELETION is captured only implicitly (file absent) — the manifest must note it;
  secret-bearing if `.env` included (chmod 600, D2-named location only).
- **Recovery:** `mkdir /tmp/recovery && tar -xzf <artifact> -C /tmp/recovery` → verify → copy
  needed files back manually. NEVER extract over the live tree.
- **Validation:** `tar -tzf` listing count vs `find django_inventory -type f | wc -l` arithmetic
  (minus excluded dirs) · sha256 recorded · restore test + §5 spot-diffs · gzip integrity
  (`gzip -t`).
- **Failure scenarios:** disk-full mid-write (388 GB free — unlikely; partial file caught by
  gzip -t) · tar warning "file changed as we read it" if anything writes during archiving (run
  with dev server stopped or accept + record) · silent path-exclusion typos (validation census
  catches).

### 6.4 Option D — filesystem copy / snapshot

ext-family FS → no CoW snapshot; the practical variant is an rsync mirror (LVM snapshot only if
`lvs` shows LVM with free extents — executor verifies before proposing).

```bash
rsync -aHAX --delete --exclude='env/' \
  /home/tech/umesh-personal/django_inventory/ /path/from/D2/django_inventory-mirror/
# D3: same rules as option C (includes .env + media by default; pg_dump separate).
```

- **Advantages:** U2-clean; captures §2.2 assets; incremental refresh is cheap (D4-friendly:
  re-running rsync updates only deltas); browsable copy (no unpacking).
- **Disadvantages:** a live mirror with `--delete` propagates FUTURE deletions on refresh — a
  mistake refreshed into the mirror destroys the mirror's protection (mitigate: refresh to a NEW
  dated directory, or drop `--delete`); weakest integrity story (no single checksummed artifact;
  mitigated by `rsync -c` verify pass); permissions/xattrs depend on target FS (use a Linux-native
  target, not FAT USB).
- **Recovery:** copy files back from the mirror manually, or rsync mirror→scratch then inspect.
  NEVER rsync mirror→live directly without owner order.
- **Validation:** `rsync -aHAXnc` (dry-run, checksum) live vs mirror = zero differences ·
  file-count census · §5 spot-diffs directly against mirror files.
- **Failure scenarios:** interrupted rsync (re-run — idempotent) · refresh-after-mistake
  overwrites good mirror (dated-directory rule above) · target FS drops permissions (validate
  a `chmod`-sensitive file).

### 6.5 Comparison table

| | A commit+tag | B bundle | C tarball | D rsync mirror |
|---|---|---|---|---|
| U2 interaction | waiver needed | waiver needed | none | none |
| Captures .env/media/DB | ✗ (git-blind) | ✗ (git-blind) | ✓ (default) | ✓ (default) |
| Survives disk failure | only if pushed (D2) | ✓ if file moved offsite | ✓ if file moved offsite | ✓ if target = other disk |
| Integrity | git object model | git + verify cmd | sha256 manifest | rsync -c re-verify |
| Restore complexity | worktree/clone (git skill) | clone (git skill) | tar -x (anyone) | file copy (anyone) |
| Refresh cost (D4) | new commit+tag each time | new bundle each time | full re-archive | incremental |
| Single-file portable | ✗ | ✓ | ✓ | ✗ |

No option is "the" answer; A/B protect history-integration, C/D protect the full runtime reality.
**Pairings are legitimate and the framework note stands: the owner may pick e.g. C (complete,
U2-clean, offsite-able) + A (git-native diffability) together.** The contract recommends nothing.

### 6.6 Execution order (SNAP-1, after decision)

1. Re-verify §2.1 facts (counts/HEAD/stashes); record drift in the evidence section.
2. Capture pre-state: `git status --porcelain | sha256sum` + counts.
3. Stop the :8003 dev server if running (consistent-read guarantee for C/D; restart after).
4. Execute the chosen mechanism's procedure verbatim (D3 inclusions applied).
5. Run that mechanism's validation + the §5 restore test.
6. Capture post-state; prove criterion §3.4.
7. Write the manifest (§8), fill the Decision Record execution half, sync docs (§11) + memory
   (§12). STOP.

## 7. Sub-phase breakdown

| # | Scope | Session type | Status |
|---|---|---|---|
| SNAP-0 | Present §6.0 decision matrix to owner · capture D1–D5 in the Decision Record · no snapshot commands run | decision (owner + any agent) | ☐ |
| SNAP-1 | Execute chosen mechanism per §6.6 · validate · manifest · docs/memory sync | execution (any agent or human) | ☐ |

SNAP-0 and SNAP-1 may collapse into one session ONLY if the owner is present and decides
interactively; the Decision Record is still written BEFORE the first snapshot command.

## 8. Deliverables

- Filled **Decision Record** (appendix of this file): D1–D5 verbatim + date + the chosen
  mechanism's recovery procedure copy-pasted.
- The snapshot artifact(s) at the D2 location.
- **Snapshot manifest** inside the Decision Record: artifact path(s) · sha256(s) · size(s) ·
  file-count census · created-at · includes/excludes (D3) · the noted working-tree deletion.
- SNAP-0/SNAP-1 evidence appended to this file (§5 standard).
- Updated DEPLOYMENT_CAMPAIGN_STATUS.md (Phase-0 row + dashboard) and memory (if available).

## 9. Files expected to change

**Docs only:** this file (Decision Record + evidence appendices — the frozen-contract rule
permits appending these designated sections) · `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` ·
`docs/campaign_contracts/README.md` (index tick) · memory files (if agent has memory).
**Artifacts:** snapshot file(s)/mirror/refs per D1–D2 — outside the working tree, except
option A/B's tag + temporary branch-pointer motion inside `.git`.

## 10. Files that must never change (touching one = STOP + report)

- ANY file under `django_inventory/` outside `docs/` — application code, tests, migrations,
  templates, settings, `.env`, media (read them, archive them, never write them).
- The 2 pre-existing stash entries; any existing branch/tag; the remotes' state (no push
  without D2 saying so).
- `.git` maintenance state: no `gc`, `prune`, `reflog expire`, `filter-*`, no history rewrite.
- Working tree byte-state (criterion §3.4) — the snapshot OBSERVES the tree, never edits it.

## 11. Documentation update rules

At SNAP-0 close: Decision Record (decision half) + status-file Phase-0 row ("decision recorded:
D1=…, awaiting SNAP-1" or "decided + executing"). At SNAP-1 close: Decision Record (execution
half + manifest) + evidence appendix + status-file Phase-0 row → ✅ with artifact pointer +
dashboard "Last docs sync". If D4 chose a refresh cadence: status-file dashboard gains a
"Snapshot freshness" row stating artifact date vs last session date, updated every campaign
session thereafter.

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-0
bullet: decision, artifact path, sha256 prefix, cadence) + MEMORY.md index line. Agents without
memory: skip — §11's on-disk records are complete; the manifest lives in this file, never only
in memory.

## 13. Battery policy

**Never runs in this phase.** No code change is possible under §10; there is nothing to test.
Baseline (1526/1526 at authoring) is untouched and NOT re-verified here.

## 14. Regression policy

- The only regression this phase can cause is tree mutation — guarded by criterion §3.4
  (pre/post porcelain-hash proof).
- Option A/B additionally prove: branch pointer restored to `49404001` (`git rev-parse HEAD`),
  index clean-identical (`git diff --cached --stat` empty after reset), stash list unchanged
  (`git stash list` = same 2 entries).
- No pins, no tests — nothing to pin (U4 vacuously satisfied).

## 15. Rollback policy

- The snapshot IS the campaign's rollback instrument; this phase itself must be safely
  abortable at any step:
  - C/D: delete the partial artifact/mirror, re-run. Working tree untouched by construction.
  - A: interrupted between `commit` and `reset` → `git reset --mixed 49404001` restores the
    branch pointer; the tree was never touched. NEVER `--hard`. If the tag exists but the
    commit is wrong, delete ONLY the just-created tag (`git tag -d snapshot-campaign-…`) and
    re-run; never delete pre-existing refs.
  - B: as A; a bad bundle file is deleted and re-created (verify before trusting).
- Artifact deletion (D5 retention) always happens AFTER a newer artifact is validated, and only
  on explicit owner confirmation — never automatically.
- If validation fails (checksum mismatch, census mismatch, restore-diff differences): keep the
  failed artifact for forensics, report per §16, do not overwrite it with a retry — retry to a
  NEW dated path.

## 16. Stop conditions (end session immediately, report, await owner)

1. SNAP-0 complete with decision request delivered (normal stop if owner not present).
2. SNAP-1 complete (normal stop).
3. Owner decision missing/ambiguous on any of D1–D5 at execution time.
4. Any §10 file would be modified, or pre/post tree-state proof (§3.4) FAILS.
5. Validation failure per §15 (keep artifact, report).
6. Git error mid-procedure (option A/B) leaving the branch pointer anywhere other than
   `49404001` — report exact ref state BEFORE attempting the §15 recovery if anything about the
   situation deviates from the documented interrupt case.
7. Discovery that §2.1 facts drifted materially (e.g. new dirty paths OUTSIDE
   django_inventory/, HEAD moved, stash count changed) — re-assess before snapshotting the
   wrong thing.
8. Disk/permission errors at the D2 location.

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-0 row: decision recorded? executed?
2. Read `docs/campaign_contracts/README.md` (invariants + environment) → this contract fully.
3. Check this file's Decision Record appendix: empty → next work = SNAP-0 (present §6.0 to the
   owner). Decision half filled, execution half empty → next work = SNAP-1 per §6.6.
   Both filled → Phase 0 is done; verify the artifact still exists + sha256 matches before
   relying on it; if D4 set a cadence, check freshness.
4. Re-verify §2.1 facts read-only (`git rev-parse HEAD`, porcelain counts, `git stash list`,
   free disk). Material drift → stop condition 7.
5. No password needed for this phase (no app login involved).
6. Execute exactly one sub-phase. STOP per §16.

---

# Decision Record (appended at SNAP-0/SNAP-1 — the ONLY sections of this frozen contract that get filled in later)

## Decision half (SNAP-0)

| Field | Value |
|---|---|
| Date | **2026-07-13** (owner answers received verbatim in the decision session) |
| D1 mechanism | **Option C (tarball only).** |
| D2 storage location(s) | ~~Original (2026-07-13): external SSD/USB primary + optional private-cloud copy; "Do not rely on the same disk."~~ **AMENDED 2026-07-13 by owner execution directive, recorded BEFORE SNAP-1 began (an owner decision, not an implementation improvisation), verbatim:** *"Primary snapshot location: `/home/tech/django backup/`. This replaces the previously selected external SSD/USB requirement."* — Path is OUTSIDE the repo working tree (§4 satisfied) but ON THE SAME PHYSICAL DISK (nvme0n1): per this contract's own §6.0 D2 matrix, same-disk = "weakest — survives mistakes, not disk failure" — the owner amends with that tradeoff on record (context: no external device enumerated at the block layer after two verification attempts). Secret-bearing artifact rules (§4, chmod 600) apply. An off-disk/cloud second copy remains available to the owner at any time per D5's keep-all posture |
| D3 inclusions | .env: **YES** · media: **YES** · pg_dump dev DB: **YES** · venv: **NO** |
| D4 refresh cadence | Owner verbatim: *"Create a fresh validated snapshot at major campaign milestones (recommended after Phases 4, 9, 14, 18, and immediately before Phase 20), or whenever I explicitly request one."* (Each refresh = full SNAP-1 validation; status dashboard carries a Snapshot-freshness row per §11) |
| D5 retention | Owner verbatim: *"Keep all validated snapshots. Never overwrite the only copy. New snapshot first, validate it, then retain all unless I explicitly decide otherwise."* |
| U2 waiver (required for A/B) | **Not applicable — Option C only.** Owner verbatim: *"No git commits, tags, bundles, branch movement, or repository mutations are authorized."* |
| Recovery procedure (copy §6.x here verbatim once D1 known) | §6.3 verbatim: *"`mkdir /tmp/recovery && tar -xzf <artifact> -C /tmp/recovery` → verify → copy needed files back manually. NEVER extract over the live tree."* — For the D3 DB-dump companion artifact: restore via `pg_restore` into a scratch/rebuilt database (the deploy/README restore-drill lineage), never over a live DB without owner order. |

## Execution half + manifest (SNAP-1)

| Field | Value |
|---|---|
| Executed at / by | **2026-07-13, Claude (Fable 5), owner-attended session** — per the amended D2 (see decision half) |
| Artifact path(s) | `/home/tech/django backup/django_inventory-snapshot-2026-07-13.tar.gz` · `/home/tech/django backup/devdb-snapshot-2026-07-13.sql.gz` · `/home/tech/django backup/SHA256SUMS-2026-07-13.txt` — all `chmod 600` (secret-bearing: .env + DB dump) |
| sha256(s) | tarball `22dca50a2f98da56987b3d0153e8e6fa5e5a096be570cfe3988461a5cfa44f4a` · DB dump `493e30a588fd671adc9d5195e3377e07909c5db67b5f2a539b1a6390ec3881d8` (manifest file carries both) |
| Size(s) / file-count census | tarball 215M (224,954,629 B) — **14,044 tar entries = 14,036 regular files (disk census, env/ excluded) + 8 symlinks (patterns_ai compute/poc sub-venv python links; tar lists links, `find -type f` does not) — arithmetic exact** · DB dump 179K (183,061 B), plain-SQL gz, header marker "PostgreSQL database dump" verified · gzip -t clean on both · tar stderr EMPTY (no "file changed" warnings — :8003 stopped during archive, restarted after) |
| Includes/excludes applied | per D3: `.env` INCLUDED · `media/` + `config/media` INCLUDED · main venv `django_inventory/env/` EXCLUDED · pg_dump of `inventory_db` (postgresql@localhost, user postgres; password sourced from settings, never displayed) as separate artifact. Disclosed extra: two small patterns_ai sub-venvs (`compute/`, `poc/`) ride along inside the tarball (D3 excluded only the main env/) — harmless bytes, noted |
| Noted working-tree deletion captured how | `config/production/templates/production/product_patterns_edit.html` proven ABSENT in the live tree AND absent from the restored archive (spot-diff 3) — captured implicitly per §6.3, recorded here |
| Restore test | extracted to scratchpad `recovery1/`; spot-diffs: (1) modified `CLAUDE.md` IDENTICAL · (2) untracked `PHASE_21` contract IDENTICAL · (3) deleted file absent both sides OK · (4) media sample `config/media/profile_pics/Screenshot_from_2026-01-09_19-02-55.png` sha256 pair MATCH (`7cd10de36338bae39a15…`) · (5) `.env` byte-identical via `cmp` exit 0 (contents never displayed) — ALL PASS |
| Tree-unmutated proof | pre-state and post-state `git status --porcelain` outputs **byte-identical**: sha256 `9393c032c6030e5b001e18ea03cf97c15f187b6c77bf19e878a4bf1beaaf2b66` both sides (308 lines = 182 M + 125 ?? + 1 D, matching §2.1 exactly); HEAD `49404001` unchanged; 2 pre-existing stashes untouched; **zero git mutations of any kind** (reads only, per the owner's recorded supplementary instruction) |

# Evidence sections (SNAP-0, SNAP-1 — appended at close)

## SNAP-0 — Decision session (2026-07-13) ✅

- Governing docs read in full from disk at session start (status file → framework →
  CAMPAIGN_APPROVAL_REPORT → this contract); Decision Record confirmed empty → SNAP-0.
- The §6.0 matrix presented with per-option trade-offs (§6.1–6.5) + the §4-mandated
  recommendation (C+A pairing recommended; owner chose C only — recorded above).
- **Fact-drift disclosure given:** §2.1 was measured 2026-07-12; since then the campaign
  added the contract corpus (~24 files, ~8k lines, all inside `django_inventory/docs/`) —
  risk shape unchanged (all inside django_inventory/; git-invisible set unchanged); exact
  fresh counts are SNAP-1 step 1 (§6.6) before any command runs.
- Cross-reference noted to the owner: the D1/D2 choice may double as the DEP-D2 deployable-
  artifact path (Phase 19/20) — tarball is DEP-D2-compatible.
- D1–D5 + waiver answered by the owner and recorded verbatim in the Decision half.
- **Owner supplementary instruction (2026-07-13, binding on SNAP-1's executor, verbatim):**
  *"When executing SNAP-1, use the chosen tarball mechanism only. Do not substitute any
  git-based mechanism, do not create temporary commits or tags, and do not perform any
  repository mutation beyond what the Phase 0 contract explicitly permits."* — reinforces
  the D1/U2-waiver rows: SNAP-1 is git-read-only in its entirety (porcelain-hash proofs are
  reads); any git-object-creating step is out of mandate regardless of convenience.
- **No snapshot command was run; no file outside this Decision Record + the §11 sync set was
  touched.** SNAP-0 closes per §16.1. Next: SNAP-1 (execution + validation) per §6.6 —
  prerequisites: the external drive mounted (its verbatim path recorded then), the dev
  :8003 server stopped during archiving (consistent-read, §6.6 step 3), and the dev DB name
  confirmed for `pg_dump`.

## SNAP-1 — Execution + validation (2026-07-13) ✅

- **Prerequisite history (honest record):** two SNAP-1 attempts were BLOCKED at the
  external-drive prerequisite — kernel-level verification (`lsblk`, `/proc/partitions`,
  `/dev/sd*`) showed NO second physical device attached despite connection attempts; no
  same-disk improvisation was made. The owner then formally AMENDED D2 (decision half,
  dated) to `/home/tech/django backup/` before execution began.
- **§6.6 step 1 fact re-verification — drift verdict: NONE at porcelain level.** 308 lines
  (182 M + 125 ?? + 1 D) exactly matching §2.1; the campaign's contract corpus grew INSIDE
  already-collapsed untracked directories (docs/campaign_contracts/ etc.), so file-level
  growth is real but line-level state is identical. HEAD `49404001`, branch new_flask_app,
  2 stashes, 0 dirty paths outside django_inventory/, 387G free — all re-verified.
- Steps 2–6 executed per §6.3 verbatim (tarball mechanism ONLY; zero git writes): pre-state
  hash → :8003 stopped (three stale runserver processes found and stopped; :8003 restarted
  and confirmed listening after the archive) → tar (23.7s, stderr empty) → pg_dump
  companion → sha256 manifest → gzip/tar/census validation → restore test + 5/5 spot-diffs →
  post-state hash identical. Full values in the execution half above.
- **Timing note:** this Decision-Record execution half + evidence section + §11 status sync
  postdate the archive by nature (a snapshot cannot contain its own completion record);
  the archived tree contains the decision half incl. the D2 amendment.
- **D4 freshness obligation begins:** next refreshes at post-Phase-4/9/14/18 milestones +
  immediately before Phase 20, or on owner request — status dashboard row live.
- **Owner follow-up available anytime (D2 optional second copy):** copy the three artifacts
  to the private cloud after validation — they are secret-bearing (chmod 600); only to a
  location the owner names.
- SNAP-1 closes per §16.2. **Phase 0 COMPLETE.** Next campaign step: Phase 2 → OWN-A.

## SNAPSHOT REFRESH #1 — post-Phase-4 milestone (2026-07-13) ✅ — D4 cadence honored, full SNAP-1 validation re-run

- **Trigger:** D4 verbatim cadence ("after Phases 4, 9, 14, 18, and immediately before Phase
  20") — Phase 4 CLOSED CERTIFIED 2026-07-13; owner ordered the refresh same day.
- **§6.6 step 1 fact re-verify — drift verdict: in-repo docs growth only, NOT material.**
  HEAD `49404001` unchanged · 2 stashes unchanged · porcelain 313 lines (was 308 at SNAP-1;
  +5 = the documented campaign chain 308→311→312→313, all inside `django_inventory/docs/`,
  incl. the new CONFIRMED_FINDINGS_LEDGER.md) · **0 dirty paths outside django_inventory/** ·
  388G free. Stop-condition 7 not triggered.
- **D5 honored:** prior 2026-07-13 artifacts NOT overwritten (verified present, byte-counts
  intact before writing); refresh artifacts carry a distinct `-post-phase4` suffix. Keep-all
  stands — old-artifact deletion remains an explicit owner decision, not taken.
- **Execution (Option C verbatim, zero git writes):** pre-state porcelain sha256
  `9b8b1451040e4b12365b9157b844f18c08b024bfc23d0ceb7d2816ab54f76384` (313 lines) → :8003
  dev server stopped (pid 2878569) → `tar --exclude='django_inventory/env' -czf …` (23.97s,
  **stderr EMPTY**, exit 0) → `pg_dump inventory_db | gzip` companion (password sourced from
  Django settings, never displayed; "PostgreSQL database dump" header verified) → :8003
  restarted + confirmed listening → sha256 manifest → chmod 600 ×3.
- **Artifacts (all chmod 600, secret-bearing):**
  `/home/tech/django backup/django_inventory-snapshot-2026-07-13-post-phase4.tar.gz`
  (225,336,608 B, sha256 `778d6840212e44efc698253141f1c91d3b0d8666d1c002e8850894d1e7b2700c`) ·
  `/home/tech/django backup/devdb-snapshot-2026-07-13-post-phase4.sql.gz` (192,106 B, sha256
  `8715cf274b3a927d090c1c4a438b01bbbe5490c064e0b12d7a7b06b3af793abc`) ·
  `/home/tech/django backup/SHA256SUMS-2026-07-13-post-phase4.txt` (both hashes).
- **Validation (SNAP-1 standard, ALL PASS):** gzip -t clean ×2 · **entry census EXACT:
  15,384 tar entries = 14,078 regular files + 8 symlinks + 1,298 directories (env/ excluded;
  counting method notes dirs explicitly — file growth vs SNAP-1 = +42, the Phase-2/3/4 docs)**
  · restore test to scratchpad `recovery2/`: **5/5 spot-diffs PASS** — (1) modified CLAUDE.md
  IDENTICAL · (2) untracked Phase-4 CONFIRMED_FINDINGS_LEDGER.md IDENTICAL (refresh provably
  captures the post-Phase-4 state) · (3) deleted `product_patterns_edit.html` absent both
  sides · (4) media sample sha pair MATCH (`7cd10de3…` ×2) · (5) `.env` cmp exit 0 (contents
  never displayed) · extract REMOVED after validation (secret-bearing).
- **Tree-unmutated proof:** post-state porcelain sha256 **identical** `9b8b1451…76384`
  (313 lines) · HEAD `49404001` · 2 stashes · zero git mutations (reads only).
- **Freshness obligation:** next refresh due post-Phase-9 (then 14, 18, immediately pre-20,
  or owner request). Optional owner second copy (cloud) remains available — chmod-600
  artifacts, owner-named location only.
