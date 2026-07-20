# 40 — Disaster Recovery

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [39 — Debugging Production](39_Debugging_Production.md). Next: [41 — Scaling](41_Scaling.md).

# Purpose
The plan for when it *all* goes wrong — the disk dies, the VPS is terminated, a migration corrupts the database, or `.env` is lost. Disaster recovery (DR) is the rehearsed procedure that turns "we lost the factory's data" into "we're back in a few hours." Backups ([Ch 28](28_Backups.md)) are the ingredients; DR is the recipe you've cooked before.

# The Problem
Everything fails eventually: hardware, providers, humans. For a factory whose payroll and production truth live in one database, "we lost it" isn't an option. But an *untested* recovery plan fails exactly when you need it — wrong command, missing password, unreachable backup, a step no one rehearsed. DR is about making total loss **survivable and boring** through preparation and drills.

# Theory (from zero)

### RPO and RTO (the two numbers that define DR)
- **RPO (Recovery Point Objective)** — how much data you can afford to lose = the backup interval. Nightly ⇒ **RPO ≤ 24h**.
- **RTO (Recovery Time Objective)** — how long recovery may take = how fast you can execute the runbook. Target: a few hours for total loss.
Every DR decision trades cost against shrinking these two numbers.

### The disaster-recovery *pair* (the core idea)
To rebuild from nothing you need **exactly two things**, and losing either makes the other useless:
1. The **off-site restic repository** — the encrypted data ([Ch 28](28_Backups.md)).
2. The **`.env`** — holds `RESTIC_PASSWORD` (decrypts the repo) + DB creds — kept in a **password manager** ([Ch 23](23_Environment_Variables.md)).
Repo without password = undecryptable. Password without repo = nothing to decrypt. Keep both, separately, off the VPS.

### Failure scenarios → response (know each cold)
| Disaster | Response | RPO impact |
|---|---|---|
| Container crash / VPS reboot | `restart: unless-stopped` auto-recovers ([Ch 10](10_Systemd.md)) | none |
| Bad migration / corrupt data | restore the **predeploy dump** ([Ch 29](29_Restore.md)) | since last deploy dump |
| Accidental `down -v` / volume loss | restore from restic (DB + media) | ≤ 24h |
| Disk failure | new disk → restore from restic | ≤ 24h |
| **VPS destroyed / provider gone** | **new box → full total-loss runbook** ([Ch 36](36_My_ERP_Deployment.md) + restore) | ≤ 24h |
| Ransomware / compromise | rebuild clean box from repo + rotate all secrets | ≤ 24h |
| **Lost `.env` (no copy)** | ⚠ backups undecryptable — unrecoverable | catastrophic |

### Defense layers by durability (match effort to value)
- **In-box:** `restart` (crashes) + named volumes (container churn) — instant, but die with the box.
- **Beyond-box:** off-site encrypted restic (disk/VPS/ransomware) — the real safety net.
- **Beyond-provider:** replicate the restic repo to a *second* provider/region — removes the single-repo SPOF.

### DR is a practiced procedure, not a document
The single biggest DR failure is a plan no one ran. **Drill it**: restore into a scratch stack, assert known truths (my sentinels/goldens), measure the RTO. A drill converts hope into a measured capability ([Ch 29](29_Restore.md)).

# Real World Example (My ERP)
- **The pair, concretely:** off-site restic repo on **Backblaze B2 / Cloudflare R2** + the filled **`.env` in a password manager** (`RESTIC_PASSWORD` is *not resettable* — losing it loses every backup; this is stated in `.env.example` itself). This is the whole recovery capability in two artifacts.
- **RPO/RTO:** nightly ~02:00 IST ⇒ **RPO ≤ 24h**; total-loss RTO ≈ the time to provision a box + run the 13-step deploy + `restic restore` (mostly download time) — a few hours.
- **Layered defenses present:** `restart: unless-stopped` (self-heal), named volumes `pgdata`/`media` (container churn), restic off-site (beyond-box), `deploy.sh` predeploy dump (bad-migration rollback anchor). Weekly `restic check` guards against silent repo corruption.
- **Total-loss runbook = [Ch 36](36_My_ERP_Deployment.md) + restore-B:** new VPS → Docker → clone repo → **restore `.env` from password manager** → `up db backup` → `restic restore latest` → `pg_restore` + copy media → `up -d` → verify with **sentinel 170 / ₹10,880.25** + **goldens ₹344.25 / ₹801 / ₹633**.
- **Drill mandate:** Step 13 of the deploy makes the restore drill a launch requirement, not an afterthought.
- **Honest gap (tracked):** the restic repo is currently a **single** off-site target — replicating to a second provider/region is the recommended DR hardening (removes the last SPOF).

# Visual Diagram
```
  DURABILITY LAYERS (match effort to value):
   crash/reboot ─ restart: unless-stopped ───────────── in-box (instant)
   container churn ─ named volumes (pgdata/media) ───── in-box
   disk/VPS/ransomware ─ off-site restic (B2/R2) ─────── BEYOND-box  ★ the safety net
   provider outage ─ replicate repo to 2nd region ───── beyond-provider (recommended add)

  THE DR PAIR (both required, kept OFF the VPS):
     restic repo (encrypted data)  +  .env in password manager (RESTIC_PASSWORD)
        lose repo ⇒ nothing to restore | lose .env ⇒ can't DECRYPT ⇒ catastrophic

  TOTAL LOSS RUNBOOK: new box → Docker → clone → RESTORE .env → up db+backup →
     restic restore latest → pg_restore + cp media → up -d → ASSERT 170/₹10,880.25 + goldens
  RPO ≤ 24h (loss window)   ·   RTO = runbook speed (few hrs)   ·   DRILL it (Ch29)
```

# Practical — DR readiness checks
```bash
# Is the pair intact?
docker compose exec backup restic snapshots            # repo reachable + recent snapshot
# → confirm the .env is ALSO in your password manager (manual check — the other half)
```
```bash
# Rehearse total-loss restore into a SCRATCH stack (never prod) — measure RTO
docker compose exec backup restic restore latest --target /drill
# load /drill/backups into a scratch DB, then assert:
#   count/sum → 170 / ₹10,880.25 ; settlement goldens → ₹344.25 / ₹801 / ₹633
# time the whole thing → that's your measured RTO
```
```bash
# Repo integrity (silent-corruption guard; also auto weekly)
docker compose exec backup restic check
```

# Beginner Mistakes
- **Only `.env` on the VPS** → the box dies, you can't decrypt backups. Password manager copy = non-negotiable.
- **Never drilling** → the runbook fails live. Rehearse into scratch + assert numbers ([Ch 29](29_Restore.md)).
- **Single off-site repo** → provider outage/account loss = no backups. Replicate to a 2nd region.
- **Treating volumes as DR** → they die with the box. In-box ≠ beyond-box ([Ch 20](20_Docker_Volumes.md)).
- **No pre-deploy dump** → a bad migration has no fast rollback. `deploy.sh` takes one first.
- **Unknown RTO** → you promise "back soon" with no basis. Measure it in a drill.
- **Forgetting secret rotation after compromise** → you restore *with the leaked secrets*. Rotate on rebuild.

# Interview Questions
**Junior — "What are RPO and RTO?"** RPO = how much data you can lose (= backup interval; ≤24h here). RTO = how long recovery may take (= runbook speed; a few hours for total loss).

**Mid — "What two things do you need to recover from total loss, and why both?"** The off-site restic repository (the data) and the `.env` from a password manager (holds `RESTIC_PASSWORD` to decrypt it + DB creds). Repo without the password is undecryptable; the password without the repo has nothing to decrypt.

**Senior — "Walk the total-loss recovery for this ERP and how you'd know it worked."** Provision a new India-region VPS, install Docker, clone the repo at the certified tag, restore `.env` from the password manager, bring up db+backup, `restic restore latest`, `pg_restore` the dump + copy media into the volume, `up -d`, then **verify against known truth** — the sentinel row-count/total (170 / ₹10,880.25) and golden settlements (₹344.25/₹801/₹633). Matching numbers prove the data and the whole restore path; the elapsed time is the measured RTO.

**Staff — "Design and defend the DR posture for this factory system."** Layer durability to data value: `restart` for crashes, volumes for churn, off-site encrypted restic for disk/VPS/ransomware, and repo replication to a second region for provider loss. Protect the DR pair (repo + `.env` escrowed in a password manager + a sealed offline copy) since losing `RESTIC_PASSWORD` is the one unrecoverable event. Set RPO ≤ 24h (tighten with WAL/PITR only if the business can't lose a day of settlements) and prove RTO with a scheduled drill that restores into a scratch stack and asserts sentinels/goldens, alerting on mismatch — so a broken backup is caught in days, not during a fire. Document the runbook, rehearse it, and rotate secrets on any compromise-driven rebuild. The invariant: total loss is a *practiced, measured, verifiable* procedure, and no single artifact's loss is fatal except the deliberately-escrowed encryption key.

# Cheat Sheet
- **RPO ≤ 24h** (nightly) · **RTO = runbook speed** (few hrs; measure it in a drill).
- **DR pair (both, off the VPS):** restic repo + `.env`(RESTIC_PASSWORD) in a password manager. Lose `.env` = catastrophic.
- **Scenarios:** crash→`restart` · bad migration→predeploy dump · volume/disk/VPS loss→restic restore · lost `.env`→unrecoverable.
- **Durability layers:** in-box (`restart`/volumes) → beyond-box (off-site restic ★) → beyond-provider (2nd region — recommended).
- **Total-loss runbook** = [Ch 36](36_My_ERP_Deployment.md) + restore; **verify with sentinel 170/₹10,880.25 + goldens**.
- **DR is practiced, not documented** — drill into scratch, assert numbers, rotate secrets after compromise.

# My ERP Section
| Concept | In my ERP |
|---|---|
| RPO / RTO | ≤ 24h / few hours (total loss) |
| DR pair | restic repo (B2/R2) + `.env` in password manager |
| Self-heal | `restart: unless-stopped` + Docker on boot |
| Bad-migration rollback | predeploy dump (`deploy.sh`) |
| Total-loss runbook | Ch36 deploy + `restic restore` + `pg_restore` + media |
| Verify | sentinel 170/₹10,880.25 + goldens ₹344.25/₹801/₹633 |
| Integrity | weekly `restic check` |
| Tracked hardening | replicate repo to a 2nd provider/region |

# Homework
1. State your RPO and RTO. What single change would cut RPO below 24h, and when is it worth the complexity?
2. Name the DR pair. Where does each half live, and what happens if you lose each one?
3. Do a scratch-stack restore drill and **time it** — that's your real RTO. Which sentinel/golden numbers did you assert?
4. Match each of the 7 disaster scenarios to its response from memory. Which one is unrecoverable, and how do you prevent it?
5. Why replicate the restic repo to a second region? What failure does that remove that a single repo can't survive?

---

## Further Reading & Live Resources
- Google SRE Book — *Data Integrity: restore is what matters*: https://sre.google/sre-book/data-integrity/
- restic — *Restore / repository integrity (`check`)*: https://restic.readthedocs.io/en/stable/050_restore.html · https://restic.readthedocs.io/en/stable/077_troubleshooting.html
- AWS — *Disaster recovery: RPO/RTO & strategies* (concepts apply anywhere): https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html
- Backblaze — *3-2-1 backup* + *testing restores*: https://www.backblaze.com/blog/the-3-2-1-backup-strategy/
- PostgreSQL — *Continuous archiving & PITR* (tightening RPO below 24h): https://www.postgresql.org/docs/current/continuous-archiving.html
