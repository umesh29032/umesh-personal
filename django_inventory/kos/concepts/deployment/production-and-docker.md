---
id: concept-production-and-docker
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "How does one person run this system in production and sleep at night — and rebuild it from nothing by evening if the VPS dies?"
related: [concept-django-settings, concept-testing-strategy, project-tech-stack]
---

# Production & Docker — drilled recovery, boring on purpose

> 📂 [Deployment concepts](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)
> Execution layer: [deploy/README.md](../../../deploy/README.md) (runbook) ·
> [DEPLOYMENT.md](../../../DEPLOYMENT.md) (the P19.5 step-by-step kit).

## 1. The project hook

This system's release had a blocking condition most tutorials never
mention: **the deploy literally could not happen while work sat
uncommitted** — deploy.sh pulls from git; uncommitted code doesn't exist
to production. The whole deployment design is built from such
unglamorous, real constraints: one VPS, one operator, real money, and the
question that grades everything: *"naya VPS + repo + password-manager
.env + offsite backup — kya main aaj shaam tak system wapas khada kar
sakta hoon?"* If not, the design is incomplete.

## 2. 💡 Samjho Aise

Dukaan ka shutter design karo, mahal ka darwaza nahi. Ek aadmi kholega,
ek aadmi band karega, aur aag lag jaaye to USI aadmi ko shaam tak nayi
dukaan khadi karni hai. Isliye: har cheez ki chaabi likhi hui (runbook),
har taala boring aur PINNED (exact versions), aur bhaagne ka raasta
pehle se rehearse kiya hua (restore drill). Chamak resume ke liye hoti
hai; dukaan bharose ke liye.

## 3. Mental Model

> Production readiness = three rehearsed answers, not ten technologies:
> **(1) Misconfiguration fails LOUD at boot** (never silently insecure).
> **(2) Every failure class has a pre-written rollback lane** (tag / dump /
> flag — pick by class, not by panic). **(3) Recovery is DRILLED, not
> documented** — a backup that was never restored is a rumor.

## 4. Technical Deep Dive

**The stack** (deploy/, owner-approved direction C): Caddy (auto-TLS) →
gunicorn → PostgreSQL 16.6 + Redis 7.4, single VPS, Docker Compose,
nightly restic backups offsite (B2/R2). Every image **exact-pinned**
(`postgres:16.6-alpine`, never `:16`, never `:latest` — upgrades are a
conscious diff, not a surprise at 3 AM).

**Compose lessons that actually bit (absorbed from the release):**
- **`depends_on` ≠ ready.** Belt AND braces: compose
  `condition: service_healthy` + the entrypoint's own wait-loop — the
  first-boot migration race dies here.
- **Bake catastrophic env into the image** — `DJANGO_SETTINGS_MODULE`
  baked ([settings §4](../django/settings.md)'s double wall); env-file
  alone is operator-memory.
- **Executable bits live in TWO places:** `chmod +x` inside the image for
  container scripts; git-tracked exec bit for operator-run scripts (a real
  fix commit exists for deploy.sh's mode).

**The deploy order** (deploy.sh — order IS the design):
```
pre-deploy DB dump FIRST   ← the rollback anchor exists BEFORE risk
→ git pull --ff-only → build → up
→ entrypoint: wait-for-healthy deps → migrate → collectstatic → serve
→ verify_production        ← deploy is DONE only when this PASSES
```

**`verify_production` — the post-deploy gate** (absorbing the
verification-engine idea): a READ-ONLY check suite against the LIVE world
— settings sanity (DEBUG off?), migration consistency, dev-data
contamination (any `dev.*` identity in prod = RED), money spot-identities.
Unit tests prove the CODE; this proves the WORLD. "It started" ≠ "it is
correct." (Full engine concept: registry of named checks, JSON report,
body_hash determinism — [testing-strategy](../testing/testing-strategy.md) §refs.)

**Rollback = three lanes, chosen by failure class:**

| Broke | Lane |
|---|---|
| Bad code | redeploy previous TAG |
| Bad migration | restore the pre-deploy dump |
| Risky behavior change | env FLAG lever (the deploy-OFF→soak→enable pattern — `ENFORCE_*` flags shipped exactly for this) |

**Backups & the DR pair:** nightly dump+media via restic + retention +
integrity checks + **monthly restore drill** — and the drill is REAL: this
repo's restore rehearsal brought sentinel rows back byte-exact
(170 rows / Σ₹10,880.25 as the correctness oracle). The disaster-recovery
PAIR is written down: the restic repo + the filled `.env` in the password
manager — those two rebuild everything; protect both.

**Redis's role (absorbed):** ephemeral shared state ONLY — cache +
auth-throttle counters. Losing Redis loses NOTHING provable (truth lives
in PG) — which is why backups deliberately EXCLUDE it and why the
throttle uses it ([auth-hardening](../security/auth-hardening.md)). The
transferable rule: **never business truth in Redis; use the DB's locks
when the truth lives in the DB.**

## 5. Engineering Thinking

*Why single VPS + compose over "proper" infra?* Failure modes scale with
parts. One machine, five containers, one runbook = a system ONE person can
hold in their head at 2 AM — and the honest load (one factory) never asked
for more. *What would change the answer:* real multi-node load, a team, or
uptime money — and then the migration path is boring too (managed PG
first, THEN orchestration). *The honesty pattern worth copying:* the
release registered its gaps openly — monitoring = temporary acceptance
with a queued menu (C2), latency testing deferred as an ACCEPTED RISK —
"record what you did NOT do" beats pretending completeness. *Assumption
this design makes:* the runbook stays true — which is why deploy steps
live in an executable script + a checklist doc, not in memory.

## 6. How THIS project uses it

Read the real artifacts, in order: [deploy/README.md](../../../deploy/README.md)
(the 11-step first-deploy checklist — DNS BEFORE Caddy start, `.env` into
the password manager as step 5) · `deploy/deploy.sh` (dump-first order) ·
`deploy/entrypoint.sh` (wait→migrate→collectstatic) · `deploy/Caddyfile`
(auto-TLS) · `deploy/backup.sh` + [docs/release/](../../../docs/release/)
(the human ops handbook: deployment guide, operations manual,
troubleshooting trees).

## 7. What breaks without it

Each rule maps to a night you don't want: unpinned image → surprise major
upgrade on rebuild · depends_on-as-ready → first-boot migration race ·
undrilled backup → the restore that fails during the disaster · no
pre-deploy dump → a bad migration with no anchor · deploy-from-git with
uncommitted work → the deploy that cannot happen (lived experience).

## 8. Common mistakes (humans)

- Testing the backup SCRIPT but never the restore.
- Starting Caddy before DNS resolves (cert issuance fails; first deploy
  checklist orders it correctly).
- Treating the `.env` as reproducible — it's half the DR pair; losing it
  = losing secrets, sessions, and access in one shot.
- "Quick" manual container fixes that drift from compose — the file is
  the truth; the running state is a cache of it.

## 9. AI Implementation Pitfalls

- ❌ Bumping image tags "while we're here" — pins change via conscious,
  separate diffs.
- ❌ Adding services to compose without healthcheck + wait discipline.
- ❌ Writing runtime state or queues into Redis as if durable — ephemeral
  by law here.
- ❌ "Fixing" a deploy by editing on the server — everything flows through
  git + deploy.sh, or it doesn't exist.
- ✅ Always verify: after ANY deploy-adjacent change, the checklist still
  runs top-to-bottom on a clean VM mentally — and `verify_production`
  still gates.

## 10. DSA & Complexity

Not algorithmic — but note the ORDERING arguments everywhere: dump before
pull (anchor before risk), DNS before TLS, healthy-deps before migrate,
migrate before serve. Deployment correctness is mostly **topological
sorting of side effects** — the same dependency-DAG thinking as
[migrations §10](../django/migrations.md).

## 11. Interview corner

*Interview Signal: 🟡 Mid — deployment/ops questions filter for production experience; the DR-pair answer reads senior.*

**Q. "Walk me through your deployment setup and what happens when it breaks."**
- *Short answer:* Single VPS, Docker Compose, pinned images, Caddy auto-TLS; dump-first deploy script; three rollback lanes by failure class; nightly offsite backups with monthly restore drills; a read-only post-deploy verification gate.
- *Senior answer:* The design optimizes recovery-time-by-one-person: loud config failures at boot, pre-written rollback lanes chosen by class, and a drilled DR pair (backup repo + secrets) proven to rebuild the world by evening. Complexity is added only when its problem arrives.
- *Project example:* the sentinel-verified restore drill (byte-exact rows back); the flag-lane (`ENFORCE_*` deploy-OFF→soak→enable); the uncommitted-work deploy block as a lived lesson.
- *Follow-ups:* "Zero-downtime?" (accepted risk at this scale; the seam is a second app container behind Caddy) · "Why not K8s?" ([tech-stack](../../project/tech-stack.md) rejected-table) · "What do you monitor?" (honest answer: registered gap C2 with a queued plan — knowing your gaps IS the senior answer).

## 12. 🧠 Remember This

Teen rehearsed jawab = production readiness: config galat → boot par
SHOR; kuch toota → class dekho, lane pakdo (tag/dump/flag); sab gaya →
restic + .env se shaam tak wapas. Image pin karo, ready ka intezar karo
(healthcheck+loop), aur restore ki practice backup se zyada zaroori hai.

## 13. 30-Second Revision

- Stack: Caddy→gunicorn→PG16.6+Redis7.4, compose, ALL pinned
- Order: dump → pull → build → up (wait→migrate→collectstatic) → verify_production
- Rollback lanes: tag (code) · dump (migration) · flag (behavior)
- DR pair: restic repo + password-manager .env — drilled monthly, sentinel-verified
- depends_on ≠ ready; bake settings module; exec bits in git AND image
- Redis = ephemeral only (cache/throttle); truth never leaves PG

## 14. What You Should Now Understand

The three rehearsed answers, why order carries the correctness, what the
DR pair is and why it's drilled, and Redis's deliberately small role.
Shaky? Read `deploy/README.md` — 11 steps, one page.

**Recommended next topic:** [testing-strategy](../testing/testing-strategy.md)
if you skipped it — `verify_production` is its fifth weapon wearing ops clothes.

## Implementation References

- Runbook: [deploy/README.md](../../../deploy/README.md) · human handbook: [docs/release/](../../../docs/release/) (DEPLOYMENT_GUIDE · OPERATIONS_MANUAL · TROUBLESHOOTING)
- Honesty registers: C2 monitoring acceptance + accepted risks in [docs/RELEASE_CERTIFICATION_LOG.md](../../../docs/RELEASE_CERTIFICATION_LOG.md)

## Code References

- `deploy/deploy.sh` (dump-first) · `deploy/entrypoint.sh` (wait→migrate→serve) · `deploy/Caddyfile` · `deploy/backup.sh` · `config/config/settings/production.py`

## Further Reading

- Official: [Docker Compose healthchecks](https://docs.docker.com/compose/how-tos/startup-order/) · restic docs (backup/restore)

## Related

[settings](../django/settings.md) · [testing-strategy](../testing/testing-strategy.md) ·
[tech-stack](../../project/tech-stack.md) · [auth-hardening](../security/auth-hardening.md)
