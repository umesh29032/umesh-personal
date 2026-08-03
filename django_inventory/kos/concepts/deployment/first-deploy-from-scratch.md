---
id: concept-first-deploy-from-scratch
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "I have NEVER deployed anything — what exactly IS a deployment, what ingredients do I need, and what happens step by step when THIS project goes live?"
related: [concept-production-and-docker, concept-django-settings, project-dev-setup]
---

# First Deploy, From Scratch — what deployment actually is

> 📂 [Deployment concepts](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)
> The senior version (rollback lanes, DR drills) = [production-and-docker](production-and-docker.md).
> The full execution kit (every command + troubleshooting + deployment-day
> checklist, placeholders ready) = [DEPLOYMENT.md](../../../DEPLOYMENT.md).
> THIS page assumes you've never deployed anything. *(Pehli baar? Yahi se.)*

## 1. The project hook

This project sits finished on a laptop: tag `erp-v1.0.0`, 1,878 tests
green, runbook written. Between "works on my machine" and "the factory
uses it from their phones" stands exactly ONE process — deployment. Phase
19 of the campaign is blocked on nothing but the five purchased
ingredients below.

## 2. 💡 Samjho Aise

Deployment = **dukaan kholna**. Ghar mein khana banana aata hai (dev
machine), par dukaan ke liye chahiye: **kiraye ki jagah** (server) ·
**bijli-paani** (Docker/PG/Redis installed) · **bazaar mein naam-pata**
(domain + DNS) · **shutter ka taala** (TLS/HTTPS) · **tijori ki chaabi**
(.env secrets) · aur **aag lagne par bhaagne ka raasta** (backups).
Deployment in sab ko EK BAAR sahi order mein jodna hai — phir roz sirf
naya maal aata hai (redeploys).

## 3. Mental Model

> A deployment is **your app + its world, rebuilt somewhere you don't
> sit**. Locally, YOU are the world (you start PG, you know the secrets,
> you restart things). On a server, every job you did by hand must be
> done by a WRITTEN, ORDERED procedure — because at 2 AM the procedure
> is all there is. That's why the runbook's ORDER is the design
> ([production-and-docker §10](production-and-docker.md): deployment =
> topological sort of side effects).

## 4. The ingredients (what you must HAVE before any command)

| # | Ingredient | What it is | This project's spec (§P19.5) |
|---|---|---|---|
| 1 | **Server (VPS)** | a rented Linux computer that never sleeps | 2–4 GB RAM, India region (~₹350–450/mo — Contabo Mumbai / Vultr / DO Bangalore) |
| 2 | **Domain + DNS A record** | your name → the server's IP | must resolve BEFORE first start (TLS needs it) |
| 3 | **Runtime** | Docker + compose plugin | one install command |
| 4 | **Secrets (`.env`)** | SECRET_KEY, DB password, origins… | filled from `.env.example`, then INTO THE PASSWORD MANAGER (half your disaster-recovery pair) |
| 5 | **Backup target** | offsite storage + credentials | restic repo on B2/R2 (the other half of the DR pair) |

Everything else — the app image, PG 16.6, Redis, Caddy — arrives via the
repo's own `docker-compose` file. You buy 5 things; the repo brings the rest.

## 5. The steps, in order, with WHY (this project's runbook, taught)

*(Canonical commands: [deploy/README.md](../../../deploy/README.md) steps
1–11. Here's what each step MEANS.)*

**Step 1 — Prepare the server.** Create the VPS · log in by SSH KEY only
(passwords get guessed; keys don't) · firewall: allow only 22/80/443
(every closed port = an attack surface that doesn't exist).
*Why first:* an unhardened box on the public internet gets scanned within minutes.

**Step 2 — Install Docker + compose.** One script. *Why Docker:* the
server runs the SAME pinned containers you tested (postgres:16.6-alpine
etc.) — "works on my machine" becomes "works, period."

**Step 3 — Point DNS at the server.** A record: `yourdomain.in → VPS IP`.
*Why BEFORE starting anything:* Caddy auto-issues the HTTPS certificate on
first boot by proving it owns the domain — if DNS doesn't resolve yet,
issuance fails and you debug a ghost.

**Step 4 — Clone the repo.** `git clone … && cd …`. *Why git, not
copy-paste:* deploys must be reproducible from a tagged commit — the
release literally could not ship while work sat uncommitted (lived lesson).

**Step 5 — Create the `.env`.** `cp .env.example .env`, fill EVERY value,
then store the filled file in your password manager. *Why fail-fast:*
production settings have NO defaults — a missing secret crashes at boot,
never limps insecurely ([settings](../django/settings.md)). *Why the
password manager:* `.env` + restic repo = the pair that can rebuild
EVERYTHING; lose the .env and you lose secrets, sessions, access.

**Step 6 — First start.** `docker compose up -d --build`, then watch logs.
What happens inside, in order: db+redis boot → healthchecks pass → the
app's entrypoint WAITS for them → runs `migrate` (schema built from zero,
the same chain CI replays daily) → `collectstatic` → gunicorn serves →
Caddy gets its certificate → **https://yourdomain.in is alive.**
*Why the waits:* `depends_on` ≠ ready — the wait-loop kills the first-boot
migration race ([production-and-docker §4](production-and-docker.md)).

**Step 7 — Create the first superuser + real data decision.** The DEP-R5
choice: start CLEAN (fresh admin, factory enters real data) vs import the
dev dump (carries 33 dev.* users — hygiene decision, owner's call at
runbook step 8).

**Step 8 — Wire the backups.** restic → B2/R2, nightly dump+media,
retention 7d/4w/6m, weekly `restic check`. *Why now, not "later":* a
backup configured after the first real settlement is a gamble you already
lost once in your head. The core restore drill is ALREADY PROVEN on real
data (sentinels byte-exact) — this step just points it offsite.

**Step 9 — Run `verify_production`.** The read-only gate: DEBUG off?
migrations consistent? zero dev.* contamination? money identities hold?
*Why:* "it started" and "it is correct" are different sentences — the
deploy is DONE only when this passes.

**Step 10 — Smoke-test as a human.** Log in over HTTPS · open the
dashboard · walk one worker report → one settlement preview on test data.
The machine said yes; now YOUR eyes say yes.

**Step 11 — Record the state.** Note the deployed tag, the `.env`
snapshot's location, backup's first successful run. *Why:* the next deploy
(and the first incident) starts from this record.

**Every LATER deploy** is smaller: `deploy.sh` = pre-deploy DB dump FIRST
(the rollback anchor) → `git pull --ff-only` → build → up → verify. Order
is the safety.

## 6. What breaks without each ingredient (learn the ingredients by their absence)

No firewall → bot logins by breakfast · DNS after Caddy → TLS issuance
loop · defaults in .env → silently insecure instead of loudly dead ·
skipped healthcheck-wait → app boots before PG, migration race · no
offsite backup → the VPS provider's bad day becomes the factory's last
day · skipped verify_production → dev data or DEBUG=True meets real users.

## 7. Common mistakes (first-timers)

- Buying the server LAST — buy it first, harden it, THEN everything else
  has a home.
- Testing HTTPS with the IP address (certificates bind to the NAME).
- Treating `.env` like a file instead of like the tijori ki chaabi.
- "I'll set backups after launch" — launch day IS the day data starts
  being irreplaceable.
- Debugging on the server by editing files — everything flows through git
  + the script, or it doesn't exist ([production-and-docker §9](production-and-docker.md)).

## 8. AI Implementation Pitfalls

- ❌ Improvising steps or reordering the runbook — the ORDER is the design.
- ❌ Generating a .env with placeholder secrets that "work" — fail-fast
  exists to refuse exactly that.
- ❌ Marking deploy done at "containers up" — done = verify_production PASS.
- ✅ Always verify: every command from [deploy/README](../../../deploy/README.md),
  every gap reported, nothing simulated (the P19 record's own standard).

## 9. 🧠 Remember This

Paanch cheezein KHAREEDO (server · naam+DNS · docker · .env-tijori ·
backup-thikana), gyarah kadam EK order mein (taala → bijli → naam →
saaman → chaabi → shutter-up → pehla grahak → beema → jaanch → khud
dekho → likh lo). Pehla deploy mushkil, har agla = dump → pull → up →
verify. *Order hi suraksha hai.*

## 10. 30-Second Revision

- Buy 5: VPS (2–4GB India) · domain+DNS · docker · filled .env→password-manager · restic/B2
- Order: harden → install → DNS → clone → .env → up (wait→migrate→static→serve→TLS) → superuser/data-decision → backups → verify_production → human smoke → record
- DNS BEFORE Caddy · .env has NO defaults · backup = DR pair's other half
- Later deploys: dump FIRST → pull → build → up → verify
- Done ≠ started; done = verify_production PASS

## What You Should Now Understand

What deployment IS (your app + its world, rebuilt by written procedure),
the five purchasable ingredients, why each of the eleven steps sits where
it sits, and what "done" means. Shaky? Read
[deploy/README.md](../../../deploy/README.md) beside this page — commands
there, meaning here.

**Recommended next topic:** [production-and-docker](production-and-docker.md)
— rollback lanes, the DR drill, and sleeping at night.

## Implementation References

- THE runbook: [deploy/README.md](../../../deploy/README.md) (steps 1–11) · human handbook: [docs/release/](../../../docs/release/)
- Current position: P19 §P19.5 owner list in [docs/RELEASE_CERTIFICATION_LOG.md](../../../docs/RELEASE_CERTIFICATION_LOG.md)

## Code References

- `deploy/deploy.sh` · `deploy/entrypoint.sh` · `deploy/Caddyfile` · `deploy/backup.sh` · `config/config/settings/production.py`

## Further Reading

- Official: [Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https) · [Docker Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/)

## Related

[production-and-docker](production-and-docker.md) · [settings](../django/settings.md) ·
[dev-setup](../../project/dev-setup.md) (the laptop twin of this page)
