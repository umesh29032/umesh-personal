---
id: deploy-course-42-final-playbook
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 42 — The Final Deployment Playbook

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [41 — Scaling](41_Scaling.md). **The capstone — one page that ties the whole course together.**

> 💡 **Samjho aise:** Yeh course ka **aakhri parcha** hai — jo aap us raat haath mein rakhoge. Iska maqsad naya gyaan dena nahi, **kramm** dena hai: kya pehle, kya baad mein, kis cheez pe ruk jaana hai. Achha playbook wo hai jise thaka hua aadmi aadhi raat ko bhi bina soche follow kar sake.

# Learning Objectives
By the end of this chapter you can:
- operate this deployment without re-reading the course
- find the right chapter for any symptom in seconds
- run the recurring routines from memory
- teach someone else the same system

# Purpose
The single reference you keep open on deploy day and for every day after. Everything from Chapters 01–41 condensed into commands, orders, and numbers — with a link back to the chapter that explains the *why*. If you internalize one file, it's this one. This is where "I've never deployed" becomes "I have a playbook."

# The Problem
A 42-chapter course is understanding; a playbook is *operational memory*. Under pressure you don't re-read theory — you follow a checklist you trust. This chapter is that checklist: deploy, update, verify, back up, recover, debug, scale — each a few lines, each pointing to its chapter.

# Theory (from zero) — why a playbook beats knowledge
Knowledge is what you can reconstruct when calm. A playbook is what you can
execute when you are not. Deployment failures arrive at bad times: a worker
cannot report production, the factory is waiting, and you are the only person
who can fix it. Under that pressure, three things collapse — memory, ordering,
and judgement about what is safe.

A playbook replaces all three with **written order**. It does not make you
smarter; it makes you *repeatable*. That is why every entry here is a sequence
rather than an explanation, and why each one links back to the chapter that
holds the reasoning. Read the reasoning on a calm day. Follow the sequence on a
bad one.

The other half of the theory is **honesty about gaps**. This deployment has no
CI (ch 33), no error tracker (ch 32) and no dashboards (ch 30). A playbook that
pretends otherwise fails exactly when it is needed, so the gaps are listed as
plainly as the procedures.

# Real World Example (My ERP) — the playbook that shipped this system
This is not a generic template. Every number in it came from this project:
- **1,408 tests**, run sequentially against a fresh database, because the money
  paths use advisory locks (ch 33).
- **Golden settlement totals** used as post-deploy proof — a page that renders
  proves nothing; a matching settlement total proves the deploy (ch 35, ch 37).
- **`seed_master_data`** on any fresh database, because a new production DB
  gets only 4 of the 21 workflow stages from migrations alone; the entrypoint runs it
  every boot (idempotent, additive) so a fresh deploy can actually run a batch.
- **Two-command deploy and a known rollback**, because the compose file *is*
  the deployment (ch 18).
- **`verify_production`** as the assertion that the deploy succeeded (ch 30).

# Practical — rehearse the playbook before you need it
```bash
# Deploy rehearsal (safe, local — no server involved)
docker compose config >/dev/null && echo "compose OK"
env/bin/python config/manage.py check --deploy --settings=config.settings.local

# Verify rehearsal: the three commands you will run after every real deploy
docker compose ps
env/bin/python config/manage.py verify_production --settings=config.settings.local
curl -sI http://localhost:8000/ | head -3

# Incident rehearsal: prove you can read every layer in one pass (ch 31)
for svc in caddy web db redis; do echo "── $svc"; docker compose logs --tail 5 $svc; done

# Recovery rehearsal: prove your kit is complete (ch 40) — four items, no more
ls -l .env && git rev-parse HEAD && ls -lh backups/ | tail -3
```
Do this once a month. The rehearsal is cheap; discovering a gap during a real
incident is not.

# Visual Diagram — the whole stack in one picture
```
  Internet ──HTTPS/443──▶ CADDY (auto-TLS, Let's Encrypt, only published ports 80/443)
                              │ reverse_proxy app:8000, sets X-Forwarded-Proto
                              ▼  (private Docker network — db/redis/backup NOT exposed)
                          APP  gunicorn config.wsgi:application --workers 3   [non-root uid 1000]
                              │  entrypoint: wait healthy db+redis → migrate → seed_master_data → collectstatic → exec
                     ┌────────┼─────────┐
                     ▼        ▼         ▼
                  POSTGRES  REDIS    media volume        BACKUP (nightly pg_dump+media → restic → B2/R2)
                  (pgdata★) (cache+  (uploads★)          02:00 IST · 7d/4w/6m · weekly check
                            rate-limit)
  Pinned: caddy 2.9.1 · postgres 16.6 · redis 7.4.2 · python 3.10.16   |   Tag: erp-v1.0.0
  ★ = business data, backed up. Config in .env (0600, gitignored, + password manager).
```

# Playbook A — First Deploy ([Ch 36](36_My_ERP_Deployment.md))
```
1  VPS: Ubuntu LTS, 2-4GB, India region                              (Ch36)
2  SSH: ssh-keygen ed25519 → copy key → PasswordAuthentication no    (Ch07)
3  Firewall: ufw allow 22,80,443/tcp ; ufw enable  (22 FIRST)        (Ch05)
4  Docker: curl -fsSL https://get.docker.com | sh                    (Ch16)
5  DNS: A erp→IP ; dig +short = IP   ── BEFORE step 8 (TLS callback) (Ch04/12)
6  Code: git clone … ; git checkout erp-v1.0.0                       (Ch27/33)
7  Config: cp .env.example .env ; fill 21 vars ; chmod 600 ; → pw mgr(Ch23)
8  Start: docker compose up -d --build ; logs -f app caddy           (Ch18/09)
9  createsuperuser                                                    (Ch36)
10 Data decision: clean start vs dev dump (owner call)               (Ch36)
11 Verify: verify_production + check --deploy + browser smoke        (Ch30)
12 Backup landed: logs backup → "[backup] done" ; restic snapshots   (Ch28)
13 Restore drill scheduled (assert goldens)                          (Ch29)
```
Top first-boot failures: `ufw enable` before allowing 22 (lockout) · `up` before DNS (no TLS + rate-limit) · `POSTGRES_PASSWORD` ≠ password in `DATABASE_URL` (120s entrypoint timeout).

# Playbook B — Update Deploy ([Ch 33](33_CI_CD.md)/[Ch 37](37_Post_Deployment.md))
```
# Pre-flight (local): ruff · makemigrations --check · test (1878, fresh DB) · verify_production
git fetch --tags && git checkout <new-tag>
sh deploy/deploy.sh        # ① pg_dump(rollback anchor) ② pull ③ build app ④ up -d(migrate+collectstatic) ⑤ prune ⑥ smoke
docker compose exec app python manage.py verify_production   # post-deploy gate
```
Rollback: bad release → `git checkout <prev tag> && sh deploy/deploy.sh` · bad migration → restore `predeploy-*.dump` ([Ch 29](29_Restore.md)).

# Playbook C — Verify It's Healthy ([Ch 30](30_Monitoring.md)/[Ch 34](34_Production_Security.md))
```
docker compose ps                                     # all healthy/serving
curl -sI https://erp.example.com | grep -i strict-transport-security   # TLS+HSTS
curl -sI http://erp.example.com | grep -i location    # 301→https (no loop)
docker compose exec app python manage.py verify_production   # data invariants (0 red)
docker compose exec app python manage.py check --deploy      # config hardening
docker compose exec app whoami                        # app (non-root)
docker compose ps --format '{{.Name}} {{.Ports}}'     # only caddy published
```
Known truth to assert: tests **1878** · goldens **₹344.25 / ₹801 / ₹633** · sentinel **170 / ₹10,880.25**.

# Playbook D — Backups & Recovery ([Ch 28](28_Backups.md)/[Ch 29](29_Restore.md)/[Ch 40](40_Disaster_Recovery.md))
```
# Health
docker compose logs backup | grep -i done            # nightly ran
docker compose exec backup restic snapshots          # off-site, < 26h, retention 7d/4w/6m
docker compose exec backup restic check              # integrity (auto weekly Sun)
# Total-loss recovery: new box → Ch36 steps → restore .env(pw mgr) → up db+backup →
#   restic restore latest → pg_restore + cp media → up -d → assert 170/₹10,880.25 + goldens
```
DR pair (both, off the VPS): **restic repo + `.env`(RESTIC_PASSWORD) in a password manager.** RPO ≤ 24h.

# Playbook E — Debug Production ([Ch 39](39_Debugging_Production.md)/[Ch 38](38_Common_Production_Bugs.md))
```
# DEBUG stays FALSE. Method: observe → evidence → hypothesis → test safely → root fix → verify.
docker compose logs --since 30m app | grep -iE '500|error|traceback'
docker compose logs app | grep '<request-id>'         # one request's full story (Ch31)
docker compose exec db psql … -c "SELECT pid,state,query,wait_event FROM pg_stat_activity WHERE state<>'idle';"
git log --oneline <last-good-tag>..HEAD               # deploy bisect
```
Signature → fix: no CSS→collectstatic · 400→ALLOWED_HOSTS · 403→CSRF_TRUSTED_ORIGINS+proxy header · redirect loop→SECURE_PROXY_SSL_HEADER · 502→app/worker · `too many clients`→conn_max_age×workers · concurrency 500→atomic+locks.

# Playbook F — Day-2 Cadence ([Ch 37](37_Post_Deployment.md))
```
Continuous (auto): monitoring/alerts · nightly backup · Caddy TLS renew · restart:unless-stopped
Weekly:  df -h · logs errors · restic snapshots (freshness) · TLS days-left
Monthly: pip-audit + build --pull (CVEs) · restore drill (assert goldens) · access review
When signals trend bad → scale (Ch41): vertical → DB(indexes/PgBouncer) → media→CDN → horizontal.
```

# The 10 Laws (the course in ten lines)
1. **Config in the environment, secrets in `.env`** (0600, gitignored, + password manager); critical vars **fail-fast** ([Ch 23](23_Environment_Variables.md)).
2. **`DEBUG=False` in prod, always.** Real domain in `ALLOWED_HOSTS` ([Ch 24](24_Django_Settings.md)).
3. **One TLS terminator (Caddy); Django trusts `X-Forwarded-Proto`** (`SECURE_PROXY_SSL_HEADER`) ([Ch 11](11_Reverse_Proxy.md)/[Ch 12](12_Caddy.md)).
4. **Only the proxy is public**; db/redis/app private; firewall to 22/80/443 ([Ch 05](05_IP_Address_and_Ports.md)/[Ch 34](34_Production_Security.md)).
5. **State lives in named volumes** (`pgdata`/`media`); **`down -v` deletes your DB** ([Ch 20](20_Docker_Volumes.md)).
6. **Migrate at boot, expand→contract, back up first**; money-semantic changes are soak-gated ([Ch 27](27_Migrations.md)).
7. **A backup is unproven until a restore reproduces known numbers** ([Ch 28](28_Backups.md)/[Ch 29](29_Restore.md)).
8. **Deploy is scripted, from a tag, backup-first, reversible** (`deploy.sh`) ([Ch 33](33_CI_CD.md)).
9. **Verify, don't hope**: `verify_production` + smoke + backup-landed before "done" ([Ch 30](30_Monitoring.md)).
10. **Scale on measurement, not hunch; add complexity only when a ceiling forces it** ([Ch 41](41_Scaling.md)).

# Production Walkthrough
The whole course, condensed into what you actually do:

**Deploy** — battery green → `check --deploy` → `.env` complete → backup + size-check → review migrations → `docker compose up -d --build` → verify (`ps`, `verify_production`, styling, one upload, one known total) → rollback identified (ch 35).

**Daily** — is it up, any restarts, disk free (ch 30, ch 06).

**Weekly** — read logs, confirm backups exist and are off-site and sized (ch 28, ch 31).

**Monthly** — restore drill, patch the host, rebuild images (ch 29, ch 34).

**Incident** — observe → reproduce → isolate layer → one hypothesis → fix forward or roll back (ch 39).

**Compromise** — preserve evidence → rotate secrets → patch → restore (ch 34).

**Symptom index**: DisallowedHost ch 24 · unstyled ch 26 · broken images ch 25 · 502 ch 14/31 · 504 ch 39 · CSRF ch 24 · `db` name ch 19 · disk full ch 06 · lost data ch 29 · cannot start an Adda → run `seed_master_data`.

**Open items, honestly**: no CI (ch 33), no error tracker (ch 32), no dashboards (ch 30), fresh-database seeding required.

# Debugging Guide
1. **Symptom → chapter**, using the index above. Do not start from theory.
2. **One layer at a time**, downward (ch 31).
3. **Wrong data is an incident**, not a debugging session (ch 29).
4. **Stuck for 30 minutes with users blocked?** Roll back and think afterwards.
5. **Every fix earns a pin** — a test or a checklist line.

# Performance Notes
- Measure, then act. Query count first, then `EXPLAIN ANALYZE`, then infrastructure (ch 41).
- Serve files with Caddy, keep workers for Python (ch 13, ch 14).
- Reuse connections, cache aggregates, index what you filter on.

# Security Considerations
- The permanent list: `DEBUG=False` · real `ALLOWED_HOSTS` · HTTPS+HSTS · secure cookies · key-only SSH · firewall 22/80/443 · no DB/Redis ports · encrypted off-site backups · rotate on suspicion (ch 34).
- Never `ALLOWED_HOSTS=['*']`, never `DEBUG=True` in production, never `down -v` on real data.
- Never add a money-write path outside the approved single-writer services — stop and report.

# Architecture Decisions
- **Simple, committed, recoverable**: one VPS, one compose file, everything in git, backups off-site.
- **Recovery before observation**; **correctness before throughput**; **honesty about gaps** so they stay actionable.
- **Written procedures**, because the point of this course is that you never have to be clever at 3 a.m.

# Best Practices
- Keep this chapter printed next to the terminal.
- Deploy small and often, with time to fix it.
- Drill the restore; an untested backup is a rumour.
- Teach it to one other person — that is the real completion test.

# Beginner Mistakes (the greatest hits)
- `ufw enable` before allowing 22 · `up` before DNS · `DEBUG=True` in prod · `.env` in git or not in a password manager · `down -v` on prod · declaring "done" at container-up · deploying a branch not a tag · flipping enforcement flags without a soak · scaling before measuring · hot-editing files on the server.

# Interview Questions (the whole course, four levels)
- **Junior:** "Walk me through deploying a Django app to a VPS at a high level." — Secure the host (SSH keys, firewall), install Docker, point DNS at it, put the code + `.env` on the box, `docker compose up` (which builds the app, runs migrations, collects static, starts Gunicorn behind Caddy for HTTPS), create an admin, then verify it works and back it up.

- **Mid:** "What are the failure points and how does this stack guard each?" — Host access (keys/firewall), TLS/DNS ordering (DNS before `up`, Caddy auto-TLS + proxy header), config bugs (fail-fast env, `check --deploy`), data loss (named volumes + nightly encrypted off-site backups + restore drills), bad deploys (scripted backup-first `deploy.sh` with tag-based rollback), and running-but-broken (`verify_production` + health checks).

- **Senior:** "Which decisions in this architecture are deliberate trade-offs, and why?" — Single-VPS Compose (right for one factory; scale path documented, not prematurely built); WhiteNoise not Nginx-for-static (simpler, one less component); Redis fail-fast (availability of the rate-limiter is a security control); no ledger-until-settlement + soak-gated enforcement flags (money-safety over speed); RPO 24h via logical dumps (simple + restorable vs PITR complexity). Each trades unneeded capability/complexity for simplicity + correctness at the current scale.

- **Staff:** "You're handed this system. How do you assure it's production-ready and keep it so?" — Assure: run the pre-flight gates (1878 fresh-DB tests, goldens, `verify_production`, `check --deploy`), confirm the security layers (firewall, private services, non-root, TLS/HSTS, secret hygiene), and **prove recovery** with a restore drill asserting sentinels/goldens — because untested backups are the top real failure. Keep it so: gated, scripted, reversible deploys from tags; a Day-2 cadence (monitoring/alerts, dependency patching, backup-freshness, restore drills, access reviews); close the tracked gaps (`/healthz`, external monitor, Sentry, pip-audit, second backup region); and scale only on measured signals. The throughline of the whole course: **externalize config, fail loud, verify everything, make data recovery a practiced procedure, and add complexity only when load demands it.**

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Can you give the whole deploy in one breath? | "Push the code and run docker compose up." | **Secure the host → install Docker → point DNS → code + `.env` on the box → `docker compose up`** (builds, migrates, collects static, starts Gunicorn behind Caddy for HTTPS) → create an admin → **verify** → back it up. Host-first and DNS-before-up are the two orderings people get wrong. |
| Can you name failure points *and* their guard? | "We handle errors as they come up." | Pair each one: host access → **keys + firewall** · TLS/DNS ordering → **DNS before `up`, persistent `caddy_data`** · config bugs → **fail-fast env + `check --deploy`** · data loss → **volumes + off-site encrypted backups + drills** · running-but-broken → **`verify_production`**. |
| Can you identify your own deliberate trade-offs? | "We used the standard setup." | Name them as choices: **single-VPS Compose** (right for one factory; scale path documented, not built) · **WhiteNoise over Nginx-for-static** (one component fewer) · **Redis fail-fast** (availability of the rate-limiter *is* a security control) · **no ledger until settlement**. A trade-off you cannot name was not a decision. |
| Can you say how you would keep it production-ready? | "Keep the tests passing." | **Assure**: pre-flight gates (fresh-DB battery, goldens, `verify_production`, `check --deploy`), confirm the security layers, and **prove recovery with a restore drill that asserts the goldens**. **Keep**: gated scripted reversible deploys from tags, a Day-2 cadence, and closing the tracked gaps. |

**The killer follow-up:** *"You are handed this system tomorrow. What is the first thing you do?"* — **prove you can recover it.** Not read the code, not audit the security — restore a backup into a scratch database and assert a known settlement total. Untested recovery is the top real-world failure, and everything else you might do first assumes the system survives.

# Revision Notes
- **Deploy:** battery → `check --deploy` → `.env` → backup → migrations → `up -d --build` → verify → rollback ready.
- **Rhythm:** daily up/restarts/disk · weekly logs+backups · monthly restore drill+patching.
- **Incident:** observe → reproduce → isolate → hypothesis → fix or roll back. **Compromise:** evidence → rotate → patch → restore.
- **Symptom index:** DisallowedHost 24 · unstyled 26 · images 25 · 502 14/31 · 504 39 · CSRF 24 · `db` 19 · disk 06 · data loss 29 · no Adda → seed.
- ⚠️ Never `ALLOWED_HOSTS=['*']`, `DEBUG=True` in prod, or `down -v` on real data.

# Cheat Sheet (the playbook's playbook)
- **Deploy:** A (first, 13 steps) · **Update:** B (`deploy.sh`, tag, backup-first, rollback) · **Verify:** C (`verify_production`+smoke+ports+TLS).
- **Recover:** D (restic repo + `.env` = DR pair; restore + assert goldens; RPO ≤ 24h).
- **Debug:** E (DEBUG false; logs+request-id; signature→fix; deploy bisect).
- **Operate:** F (continuous/weekly/monthly cadence; scale on signal).
- **Numbers:** tests **1878** · goldens **₹344.25/₹801/₹633** · sentinel **170/₹10,880.25** · pinned images + tag `erp-v1.0.0`.
- **10 Laws** ≈ the course. **Verify, don't hope.**

# My ERP Section
| Playbook | Canonical file in my repo |
|---|---|
| First deploy (teaching) | `DEPLOYMENT.md` (+ this course Ch36) |
| Expert steps 1–11 | `deploy/README.md` |
| Update / rollback | `deploy/deploy.sh` |
| Architecture of record | `docs/release/DEPLOYMENT_GUIDE`, this course [ARCHITECTURE.md](ARCHITECTURE.md) |
| Operations handbook | `docs/release/` (8 docs, EN + Hinglish) |
| Verify | `verify_production` + `check --deploy` |
| Backup/restore | `deploy/backup.sh` + restore drill |

# Practice Tasks
1. **Read the code:** rewrite the deploy sequence from memory, then check it against `deploy/README.md`.
2. **Debug:** cover the symptom index and name the chapter for each from memory.
3. **Design:** write your own one-page playbook card and pin it where you deploy from.
4. **Architecture:** explain this deployment to another developer in ten minutes. Where did they get confused? Fix that chapter.

# Homework (graduation)
1. Deploy the ERP to a real (or throwaway) VPS using **Playbook A** end to end. Where did you stumble, and which chapter fixed it?
2. Do an update with **Playbook B**, then practice **both** rollback paths. Time each.
3. Run **Playbook C** and record your known-truth numbers. Do the goldens reproduce?
4. Execute a full **Playbook D** restore into a scratch stack. Measure your RTO. Is the DR pair safe?
5. From memory, recite the **10 Laws**. For each, name the one command or setting that enforces it. That's the course — you're done.

---

# Further Reading & Live Resources
- The Twelve-Factor App (the whole philosophy in one place): https://12factor.net/
- Django — *Deployment checklist* (bookmark it): https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/
- Google SRE Book + Workbook (operating production for real): https://sre.google/books/
- Docker Compose in production (docs): https://docs.docker.com/compose/production/
- Caddy (auto-HTTPS) · Gunicorn (WSGI) · PostgreSQL · restic — the four pillars: https://caddyserver.com/docs/ · https://docs.gunicorn.org/ · https://www.postgresql.org/docs/ · https://restic.readthedocs.io/
- My canonical deploy kit: `DEPLOYMENT.md` · `deploy/README.md` · `docs/release/` · this course's [00_COURSE_OVERVIEW.md](00_COURSE_OVERVIEW.md) + [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 🎓 Course Complete
You've gone from "what is deployment?" ([Ch 01](01_What_Is_Deployment.md)) to a full production playbook — internet fundamentals, Linux, Docker, the reverse proxy, the database, config, backups, monitoring, security, CI/CD, the real deploy, and the day-after. **42 chapters, one running example: your ERP.** Keep this file open on deploy day. Then go deploy it for real — that's the only chapter left, and you write it.
