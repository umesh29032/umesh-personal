---
id: config-verification-readme
type: app-readme
status: active
owner: handwritten
scope: verification
anchors: config/verification/
verified: 2026-07-18
---

# verification — read-only Verification Engine (Campaign Phase 13)

**What:** the five verify commands — `verify_demo` · `verify_factory` ·
`verify_feature <slug>` · `verify_production` · `verify_all` — a strictly READ-ONLY,
deterministic check-runner proving a world (seeded DEV world or the production database)
conforms to its CERTIFIED invariants. **The permanent deployment-verification instrument**
(owner designation 2026-07-12): Phases 19–21 and post-campaign operations consume it.

**Where it exists:** registered in **BASE settings** (production-PRESENT — the inverse of
devseed; its read-only nature is what makes that safe). No models, no migrations, no URLs,
no templates. Import-linter: layered directly below `devseed` (which imports the shared
assertion library from here — SEED-D6); no domain app may import `verification`.

**Read-only is architectural, not behavioral:** the permanent purity suite
(`tests/test_purity.py`) pins zero ORM writes / instance saves / write-verb raw SQL / even
transaction management, in the battery forever — landed BEFORE any check logic
(guards-before-features law).

**Polarity (VER-D2):** dev-world commands (`verify_demo`/`verify_factory`/`verify_feature`)
REFUSE outside `config.settings.local` + DEBUG; `verify_production`/`verify_all` run
everywhere (a dev run = pre-deploy rehearsal). No bypass flags exist.

**Shared assertion library (`assertions.py`):** THE single implementation (spec §6.1.7,
owner ruling VER-D1 2026-07-17) — relocated here from devseed at VER-A; `devseed` imports
it for post-seed self-assertions; `verify_*` consume it from VER-B. One implementation, two
consumers, never forked (test-pinned).

**Check law (VER-D4):** every check cites the certified invariant it codifies (manifest
rule · spec § · ADR · golden value · CheckConstraint class); uncited checks don't merge;
new invariants = owner/ADR territory. A red check NEVER triggers a fix from this engine —
findings route per the campaign protocol; the exit code is the engine's whole authority.

**Reports (VER-D5):** JSON envelope (command, engine/spec versions, environment, totals,
body-hash, the ONLY timestamp) + deterministic sorted body → `var/verification_reports/`
(gitignored runtime). No silent skips — `--skip <category>` is recorded in the envelope.

**State (🏁 PHASE 13 CLOSED at VER-E, 2026-07-17 — engine v1.0.0 CERTIFIED): ALL FIVE
COMMANDS LIVE, report schema + determinism certified** (schema tripwire =
`tests/test_certification.py`; changing a certified key set = new engine version + dated
Design-Record amendment; body-hash pairs proven per command, cross-session identical).
Registry completeness census (19 check ids; every deferral reasoned) + the Phase
14/15/19/20/21 handoffs = [VERIFICATION_ENGINE_LOG §VER-E](../../docs/VERIFICATION_ENGINE_LOG.md).
**Deployment law (P19/20/21):** post-deploy `verify_production` is MANDATORY; GO/NO-GO =
exit code; the Phase-21 certificate cites a green prod report (envelope + independently
recomputed body-hash).
Dev-world (VER-B): manifest-REQUIRED → cited checks (manifest conformance · LIVE
shared-assertion re-run · golden totals ₹150/₹344.25/₹633/₹801 + certified worker items
from certified sources — ZERO golden literals, test-pinned) → smoke → deterministic report
→ exit code. Production-safe subset (VER-C, SELECT/aggregate only): DEV-contamination scan
(10 columns × the spec-§4 namespace; red in prod-mode, informational in dev rehearsal) ·
flags-vs-owner-DECLARATION (U10) · migrations consistency · settings sanity · integrity
self-consistency (items-Σ · reversal nets · constraint re-checks · supersession chain —
never point-in-time constants). `verify_all` = environment-aware run-all-then-aggregate
(dev: every manifest-present world + rehearsal; prod: subset only; absent worlds LISTED).
Next: VER-D (determinism certification) → VER-E (certification + handoffs).

**Tests:** the FOURTH sequential canonical-battery member (VER-D6 dated amendment,
framework README). Run: `env/bin/python config/manage.py test verification`.

**Evidence:** [docs/VERIFICATION_ENGINE_LOG.md](../../docs/VERIFICATION_ENGINE_LOG.md).
