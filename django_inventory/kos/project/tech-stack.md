---
id: project-tech-stack
type: project
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "What technologies run this system, and why was each one chosen over the fashionable alternative?"
related: [project-system-map, concept-django-transactions]
---

# Tech Stack — deliberately boring, provably right

> 📂 [Project — the WHY layer](README.md) · [LOS home](../README.md)

## Business Purpose

One developer, one factory, real money. Every technology choice optimizes
for the same thing: **a system one person can fully understand, debug at
2 AM, and trust with wages.** The stack is boring on purpose — every
"exciting" alternative was considered and rejected for a reason worth learning.

## 💡 Samjho Aise

Dukaan ke liye truck nahi, mazboot haath-gaadi chahiye. Har fancy cheez
(microservices, SPA, Kubernetes) ek aur cheez hai jo raat ko toot sakti
hai. Yahan har piece PURANA aur PAKKA hai — kyunki naya seekhne ki jagah
factory chalani hai, aur paisa galat nahi ho sakta.

## Technical Deep Dive

| Layer | Choice | Why (the engineering lesson) |
|---|---|---|
| Framework | **Django 5.0.1**, server-rendered templates | Batteries included: ORM, migrations, auth, admin. One deployable unit — no API/frontend drift. Version pinned; upgrades deliberate (5.0.1 gotcha: `CheckConstraint` uses `check=`, not `condition=`) |
| Database | **PostgreSQL** | The system's real spine: 88 live constraints, partial-unique indexes, advisory locks (5374/5375), `FILTER` aggregates, transactional DDL. Truth lives HERE, defended even against app bugs |
| Frontend | Server-rendered + base.html canon CSS, **mobile-first** | Workers report from phones on the floor — mobile-first is a FUNCTIONAL requirement (standing rule 11), not polish. No SPA = no client-state bugs in money screens |
| Auth | **Argon2** password hashing + rate limiting | OWASP-recommended winner; listed first so new passwords upgrade transparently |
| Cache/shared state | **Redis** (prod) / LocMem (dev) | Ephemeral ONLY — rate-limit counters, cache. **Never business truth**: losing Redis loses nothing provable |
| Config | `.env` + `python-decouple`, **fail-fast** | Production settings have NO defaults for secrets — missing config crashes at boot, never limps. Settings split base/local/production |
| Deploy | **VPS + Docker Compose + Caddy** (`deploy/`) | One machine, one compose file, auto-TLS. Runbook-driven (deploy.sh, backup.sh, entrypoint.sh); rollback = tag / dump-restore / feature-flag |
| Backups | `pg_dump -Fc` + restic, **drilled restores** | A backup that was never restored is a rumor. Dev-DB sentinel rows (170 / Σ₹10,880.25) prove a restore actually worked |
| Testing | Django test runner — **1878 tests, sequential fresh-DB** | Never `--keepdb`, never parallel (cross-suite poison, learned the hard way). Golden journeys assert byte-identical money; refusals are pinned as tests too |
| Boundaries | import-linter + CI write-site gates | Architecture rules that a machine enforces survive; rules only in docs drift |

**Rejected on purpose** (each rejection is a lesson):

| Fashionable | Why not here |
|---|---|
| Microservices | One factory's load fits one process; distributed transactions would UNSOLVE the settlement atomicity this system depends on |
| SPA (React) + REST | Two codebases to drift apart; server-rendered pages + one service layer = one truth. Internal service functions ARE the API |
| Celery/queues | No workload needs async yet (Project-Anchor Law: it enters the KOS when the project adopts it) |
| Kubernetes | A compose file a human can read beats a cluster nobody needs |
| Signals/implicit hooks | BANNED (ADR-0001 territory) — invisible writers are how money breaks |

**Where things live:** app code `config/<app>/` · settings
`config/config/settings/{base,local,production}.py` · deploy `deploy/` ·
run: `env/bin/python config/manage.py <cmd>`.

## Interview corner

*Interview Signal: 🔴 Staff — technology judgment + trade-off defense.*

**Q. "Why didn't you use microservices / React / Kubernetes?"** *(the maturity test — they're probing judgment, not stack knowledge)*
- *Short answer:* Because every technology is a liability until the problem pays for it — one factory's load fits one process, and money code needs single-transaction atomicity that distribution would destroy.
- *Senior answer:* Walk the rejected-table: each fashionable choice, the specific cost it adds HERE (distributed transactions unsolve settlement atomicity; SPA splits one truth into two codebases; K8s adds a cluster nobody debugs at 2 AM), and the trigger that would change the answer (Project-Anchor Law — adopt when the project demands, never before).
- *Project example:* this page's table, plus the counter-evidence that boring ≠ sloppy: 88 constraints, 1878 tests, drilled restores.
- *Follow-ups:* "When WOULD you split services?" (when team/scale makes the monolith the bottleneck — and the service layer is the pre-marked amputation line) · "Isn't this resume-driven-development in reverse?" (judgment IS the resume).

## 🧠 Remember This

Stack ka har piece ek hi kasauti se guzra: **"kya main ise 2 baje raat
akela debug kar sakta hoon, aur kya paisa provable rahega?"** Django sab
deta hai, PostgreSQL sach ka rakhwala hai, Redis sirf yaadash hai (kitab
nahi), aur deploy itna simple ki runbook ek page ka hai. Boring = bharosa.

## Implementation References

- Deploy + ops: `deploy/README.md` · [docs/release/](../../docs/release/) (v1.0 Operations Handbook)
- Test law: battery facts in [docs/DEPLOYMENT_CAMPAIGN_STATUS.md](../../docs/DEPLOYMENT_CAMPAIGN_STATUS.md) · goldens: [docs/FACTORY_OPERATIONS_MASTER.md](../../docs/FACTORY_OPERATIONS_MASTER.md)
- Boundaries: [config/.importlinter](../../config/.importlinter) · house rules: [CLAUDE.md](../../CLAUDE.md)

## Code References
- Settings: `config/config/settings/base.py` (fail-fast pattern, Argon2, DB config)

