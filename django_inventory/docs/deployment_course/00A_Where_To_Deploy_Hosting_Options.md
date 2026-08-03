---
id: deploy-course-00a-where-to-deploy-hosting-options
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 00A — Where Can We Deploy This ERP? (Hosting Options)

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). ⭐ **Skim early** — this is a "decide before you build/buy" reference, not lesson 1. Pairs with [00B — Costs & Free Alternatives](00B_Deployment_Costs_And_Free_Alternatives.md).
>
> **Heads-up (if you're brand new):** this chapter names tools — Docker, Caddy, Postgres, serverless, Kubernetes — that are *taught later*. Skim now just for the **decision** (where to host); come back after [Ch 16](16_Docker.md)–[Ch 21](21_PostgreSQL.md) for full understanding. The from-zero teaching starts at [01](01_What_Is_Deployment.md).

# Learning Objectives
By the end of this chapter you can:
- name the five places software can run, and their trade-offs
- pick a host for this ERP and defend the choice
- recognise when a "free" option costs more than a paid one
- say what would make you change hosts later

# Purpose
Before typing a single deploy command, decide **where** the ERP runs. This chapter lists every realistic place we *can* put it, what each means, the trade-offs (control vs convenience vs cost), and the honest recommendation for *this* garment-factory ERP at *this* stage. Picking the wrong host = paying too much, or fighting the platform forever.

# The Problem
"Deploy it" is meaningless until you answer: on whose computer, managed how much, at what cost, with what failure modes? A one-person factory ERP has different needs than a 100-engineer SaaS. Choose for *my* reality: small user count (a factory's staff), money matters, I'm learning ops, and it must be reliable enough that the floor trusts it daily.

# Theory (from zero) — the five places software runs

### 1. A single VPS (Virtual Private Server) — *rent one Linux computer*
A VPS is a slice of a real server in a data center, rented by the month. You get a whole Ubuntu box ([Ch 06](06_Linux_Basics.md)) with root, a public IP, and a bill (~$4–6/mo for a small one). **You install and run everything** (Docker, Caddy, Postgres…). Maximum control, minimum cost, maximum learning — you touch every concept in this course. Providers: **Hetzner, DigitalOcean, Vultr, Linode/Akamai, Oracle Cloud (free tier!)**.
- **Pros:** cheapest real option, full control, all-in-one (app+DB+cache on one box via Docker Compose), teaches you everything.
- **Cons:** *you* are the ops team — OS patching, firewall, backups, uptime are on you.

### 2. PaaS (Platform-as-a-Service) — *push code, platform runs it*
You hand the platform your repo/Dockerfile; it builds, runs, gives HTTPS + a domain, restarts on crash, and often bundles a managed Postgres/Redis. You never touch the OS. Providers: **Render, Railway, Fly.io, Heroku, Koyeb**.
- **Pros:** fastest to live, no OS/firewall/cert/backup babysitting, easy rollbacks, git-push deploy.
- **Cons:** pricier as you grow, less control, some vendor lock-in, managed add-ons (DB/Redis) cost extra. Free tiers sleep/limit.

### 3. Serverless containers — *autoscale, pay per request*
Your container runs on demand and scales to zero when idle (you pay only when handling requests). Providers: **Google Cloud Run, AWS Fargate/App Runner, Azure Container Apps**.
- **Pros:** scales automatically, cheap when traffic is spiky, no server management.
- **Cons:** the app must be **stateless** — no local files (uploads/media vanish), migrations need a separate step, cold starts. Your RC1 report flagged the exact blockers (hardcoded `:8000` not reading `$PORT`; local-FS media). Good for high/spiky scale, **overkill + extra work for a steady small ERP.**

### 4. Managed Kubernetes — *an orchestra conductor for many containers*
K8s (GKE/EKS/AKS/DO Kubernetes) runs fleets of containers across many machines with self-healing + rolling deploys. **Massive overkill for one ERP on one box.** Skip until you're running many services at real scale ([Ch 41](41_Scaling.md)).

### 5. On-premises / self-hosted at the factory — *a computer at the factory*
Because this is a **garment factory**, a real option: a mini-PC/server on the **factory's own LAN**, running the same Docker Compose stack. Workers/managers hit it over local wifi.
- **Pros:** works even if the internet drops (LAN-only), no monthly cloud bill, data stays physically on-site, low latency on the floor.
- **Cons:** *you* own power/UPS, hardware failure, off-site backups (a fire shouldn't lose the data), remote access + security, and updates. No public access unless you add a domain + port-forward/VPN.
- **Great hybrid:** factory-local box for daily floor use **+** nightly encrypted backups off-site (cloud) so a hardware disaster is survivable ([Ch 28](28_Backups.md)/[Ch 40](40_Disaster_Recovery.md)).

### The trade-off in one line
**Control & cheapness ↔ convenience.** VPS = most control, least cost, most to learn. PaaS = least ops, more money. Serverless = best for spiky scale, needs code changes. On-prem = best for a single-site factory that wants independence, most physical responsibility.

# Real World Example (My ERP)
The project is **already built for a single VPS + Docker Compose + Caddy** (RC1's named target): `docker-compose.yml` (Caddy + web/gunicorn + Postgres + Redis), `deploy/entrypoint.sh`, `deploy/Caddyfile`, restic backups. That means:
- **Best fit today: a single small VPS** (Hetzner CX22 or DigitalOcean $6). One box runs the whole stack; ~$5–6/mo; you learn every concept in this course; the artifacts already match.
- **Strong free/learning option: Oracle Cloud Always-Free ARM VM** — genuinely free forever, big enough for this ERP ([00B](00B_Deployment_Costs_And_Free_Alternatives.md)).
- **Factory-floor option:** the *same* Compose stack on a mini-PC at the factory for LAN use, with off-site nightly backups. Compelling if the factory wants internet-independence.
- **Not now:** Cloud Run (needs the RC1 stateless fixes — `$PORT`, S3 media), Kubernetes (overkill), PaaS (works but pays for convenience you don't need yet + would sideline the Compose setup you already have).

# Visual Diagram
```
  CONTROL ▲                                                     ▼ CONVENIENCE
          │  On-prem     Single VPS      PaaS        Serverless    Kubernetes
          │  (factory)   (Hetzner/DO)  (Render/Fly)  (Cloud Run)   (GKE/EKS)
  cost/mo │   $0 + HW     $4–6          $7–25+        pay-per-use   $$$ + effort
  you run │   EVERYTHING  the OS+stack  just the app  just the app  nothing (K8s does)
  best for│   1 site,     small app,    fast launch,  spiky scale,  many services,
          │   LAN, indep. cheap+learn   hate ops      autoscale     big team
                              ▲
                        ◄── MY ERP fits here (artifacts already built for it)
```

# Practical — how to inspect / decide
```bash
# On any candidate VPS, sanity-check it can run the stack:
nproc                # CPU cores (2 is plenty to start; gunicorn workers ~ 2*cores+1 → Ch14)
free -h              # RAM (2 GB min for Django+PG+Redis+Caddy small; 4 GB comfortable)
df -h                # disk (25 GB+ ; DB + images + backups grow)
cat /etc/os-release  # Ubuntu LTS?
docker --version && docker compose version   # runtime present? (else Ch16 install)
```
```bash
# Decide with 4 questions:
#  1. Does it need public internet access, or only the factory LAN?   → on-prem vs cloud
#  2. Is a monthly bill OK, or must it be $0?                          → paid VPS vs Oracle-free/on-prem
#  3. Do I want to LEARN ops, or never see a server?                   → VPS vs PaaS
#  4. Is traffic steady (a factory's staff) or spiky/huge?             → VPS vs serverless
# For this ERP the answers point to: single small VPS (or Oracle free / factory box).
```

# Production Walkthrough
- The choice made here: **one small VPS running Docker Compose** (ch 03, ch 36). A single factory's staff is not a load problem; simplicity is the win.
- What that buys: full control over Postgres, Redis, media volumes and backups, at a predictable monthly cost.
- What it costs: you own the operating system — patching, firewall, disk, backups (ch 34, ch 28).
- A PaaS would remove ops work but fight this app's needs: persistent media volumes, advisory-lock money paths, and a database you can `psql` into during an audit.

# Debugging Guide
1. **"Is it the host or my app?"** — reproduce locally with the same compose file. If it works there, look at the host: memory, disk, network.
2. **Random container kills** = out of memory. Check the host's memory before rewriting code.
3. **Slow disk** shows as slow COMMITs, not slow queries (ch 21).
4. **Free-tier surprise** — bandwidth or CPU-credit limits throttle you silently. Read the fine print before blaming the app.

# Performance Notes
- For this workload, RAM and disk speed matter more than CPU core count.
- A 2 GB VPS runs this stack; 4 GB gives headroom for backups running alongside traffic.
- Colocate the app and database on the same host — the network hop you avoid is free performance (ch 19).

# Security Considerations
- **You own the OS on a VPS.** Unpatched kernels and open ports are your responsibility (ch 05).
- Shared/free hosts may have weaker isolation; do not put worker wage data somewhere you cannot inspect.
- Check where the provider stores data — personal data has jurisdiction implications.
- Provider account security *is* infrastructure security: enable two-factor authentication on it.

# Architecture Decisions
- **VPS over PaaS**, because this app needs volumes, a real Postgres and a shell.
- **VPS over on-premise**, because workers use phones outside the factory LAN.
- **One host over many**, sized to one factory (ch 41).
- **Portability preserved**: everything is Docker Compose, so moving host is a rebuild, not a rewrite (ch 40).

# Best Practices
- Choose by four questions: public access? budget floor? want to learn ops? traffic shape?
- Prefer a provider you can leave — no proprietary services in the critical path.
- Start smaller than you think and resize; vertical scaling is one reboot.
- Write down why you chose it, so the next decision has a baseline.

# Beginner Mistakes
- **Reaching for Kubernetes/serverless for one small app** — huge complexity + code changes for scale you don't have. Match the host to the *actual* load.
- **PaaS sticker shock at scale** — the free/cheap tier is fine to learn, but managed DB + always-on + bandwidth add up; know the real bill before committing.
- **On-prem with no off-site backup** — a factory fire/theft/disk-death loses everything. On-prem *requires* off-site backups ([Ch 28](28_Backups.md)).
- **Choosing a host that fights your artifacts** — you built Compose+Caddy; picking Cloud Run means redoing media/`$PORT` (RC1). Deploy where your artifacts already fit unless there's a strong reason.
- **Under-provisioning RAM** — Django+Postgres+Redis+Caddy on a 512 MB box will OOM-kill under load. 2 GB floor.

# Interview Questions
- **Junior:** "What's a VPS?" — A rented virtual Linux server in a data center — you get root and a public IP and run your own software on it, for a small monthly fee.

- **Mid:** "VPS vs PaaS – when would you pick each?" — VPS when you want control + low cost + to manage the stack yourself (and learn); PaaS when you want to push code and never touch the OS, accepting higher cost and less control. For a small, steady app on a budget, VPS; for a team that wants zero ops, PaaS.

- **Senior:** "This app is built as Docker Compose with local-filesystem media. What has to change to run it on Cloud Run, and would you?" — Cloud Run is stateless + multi-instance: media on local disk vanishes (move to S3/GCS via Django `STORAGES`), the container must honor `$PORT` (not hardcode `:8000`), and migrations must move to a one-off job (not per-instance entrypoint, to avoid races). For a steady small ERP I wouldn't — a single VPS matches the artifacts, costs less, and avoids the rework; Cloud Run earns its keep only with spiky/large traffic.

- **Staff:** "Design hosting for a garment ERP used mostly on the factory LAN but also remotely by the owner, on a tight budget, that must survive a site disaster." — Run the Compose stack on a factory-local mini-PC (LAN speed, internet-independent for the floor) **or** a cheap VPS; expose the owner's remote access via HTTPS (Caddy) + a domain, or a VPN if factory-local. Regardless of location, push **nightly encrypted off-site backups** (restic → cheap object storage) so a fire/theft is recoverable; rehearse the restore. Keep it single-box until user growth or reliability needs justify a load-balanced pair. Optimize for: floor uptime, tiny bill, and a survivable disaster story — not for scale the factory doesn't have.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| VPS vs PaaS — do you have a decision rule? | "PaaS is easier, VPS is cheaper." | Decide on **who owns the OS**. VPS: control, low cost, you patch and firewall it (and you learn). PaaS: push code and never touch the OS, at higher cost and less control. For a stack needing **volumes, a real Postgres and shell access**, VPS wins on requirements, not price. |
| Do you know what breaks this app on a stateless platform? | "It is containerised, so it runs anywhere." | On Cloud Run (**stateless, multi-instance**) **media on local disk vanishes** — you must move to object storage via Django `STORAGES` first. "It is in Docker" is not the same as "it is stateless". |
| Do you know which resource actually matters here? | "More CPU cores for better performance." | **RAM and disk speed** dominate for this workload: each Gunicorn worker loads the whole app, and commit rate is bounded by **WAL fsync**, not CPU. Buying cores is the wrong upgrade. |
| ⚠️ Do you know what a free tier costs? | "Free tiers are good enough to start." | They **throttle silently** (bandwidth, CPU credits), **expire**, and often have weaker isolation — which matters when the data is **worker wages and receipts**. And the provider account itself is infrastructure: **enable two-factor on it.** |

**The killer follow-up:** *"Design hosting for a factory ERP used mostly on the LAN, remotely by the owner, on a tight budget, that must survive a site disaster."* — the interesting answer is **a factory-local box for LAN speed and internet independence, plus off-site encrypted backups** so a fire does not end the business. Reaching straight for "a VPS" misses that the factory floor still works when the internet does not.

# Revision Notes
- Five places: on-prem · VPS · managed PaaS · serverless · hybrid.
- Chosen: **one small VPS + Docker Compose** — control, real Postgres, volumes, predictable cost.
- Trade: you own the OS (patching, firewall, disk, backups).
- PaaS fights this app: needs volumes, advisory locks, shell access to the DB.
- Free tiers throttle silently; "free" can cost more than $6/month.

# Cheat Sheet
- **5 options:** on-prem (factory box) · single VPS · PaaS · serverless · Kubernetes.
- **Axis:** control+cheap (VPS/on-prem) ↔ convenience+cost (PaaS/serverless). K8s = scale/teams only.
- **My ERP → single small VPS** (artifacts already built for it); free-learning = **Oracle Always-Free**; interesting = **factory-local box + off-site backups**.
- **Not now:** Cloud Run (needs stateless fixes — RC1), K8s (overkill), PaaS (pays for ops you don't need yet).
- **Min box:** 2 vCPU / 2–4 GB RAM / 25 GB disk / Ubuntu LTS.
- On-prem **must** have off-site backups.

# My ERP Section
| Question | Answer for my ERP |
|---|---|
| Built-for target | single VPS + Docker Compose + Caddy (RC1) |
| Cheapest good fit | Hetzner CX22 (~€4) / DigitalOcean ($6) |
| $0 learning fit | Oracle Cloud Always-Free ARM VM |
| Factory-floor fit | same Compose stack on a factory LAN mini-PC + off-site backups |
| Needs code changes | Cloud Run (`$PORT` + S3 media, per RC1) — avoid for now |
| Overkill | Kubernetes |

# Practice Tasks
1. **Read the code:** list every stack requirement (volumes, Postgres version, Redis, shell) and check it against one PaaS's limits.
2. **Debug:** on a candidate VPS, run the stack and record memory and disk use at rest.
3. **Design:** answer the four questions for this factory and write the one-line decision.
4. **Architecture:** name the event that would make you move host, and what the move would involve (ch 40).

# Homework
1. Answer the 4 decision questions (Practical) for *your* situation and write your host choice + one sentence why.
2. Open two VPS pricing pages (Hetzner, DigitalOcean) and find the cheapest plan with ≥2 GB RAM. Note the €/$ per month (feeds [00B](00B_Deployment_Costs_And_Free_Alternatives.md)).
3. Read your `docker-compose.yml` service list — confirm it's the single-box stack this chapter recommends a VPS for.
4. Write the pros/cons of running this ERP on a mini-PC *at the factory* vs a cloud VPS, in your own words. Which fits the owner's needs?

---

> 💡 **Samjho aise:** Yeh chapter **kiraya tay karne** wala hai, ghar banane wala nahi. Ek kamra
> (chhota VPS) sasta hai par sab kaam khud karna padta hai; poora flat (managed
> platform) mehnga hai par plumbing kisi aur ki zimmedari. Hamari factory ke liye
> **ek kamra kaafi hai** — traffic steady aur chhota hai. Naam (Docker, Caddy…) abhi
> na samjhein to theek — yahan sirf **faisla** lena hai.

# Further Reading & Live Resources
- Hetzner Cloud pricing (cheapest solid VPS): https://www.hetzner.com/cloud
- DigitalOcean Droplets pricing: https://www.digitalocean.com/pricing/droplets
- Oracle Cloud **Always Free** (free ARM VM forever): https://www.oracle.com/cloud/free/
- Render (PaaS) — docs + pricing: https://render.com/pricing · Fly.io: https://fly.io/docs/ · Railway: https://railway.app/
- Google Cloud Run (serverless containers): https://cloud.google.com/run
- DigitalOcean — *Choosing a hosting type* / community tutorials hub: https://www.digitalocean.com/community/tutorials
- *The Twelve-Factor App* (why stateless matters for PaaS/serverless): https://12factor.net/
