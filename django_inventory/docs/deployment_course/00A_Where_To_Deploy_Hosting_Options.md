# 00A — Where Can We Deploy This ERP? (Hosting Options)

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). ⭐ **Skim early** — this is a "decide before you build/buy" reference, not lesson 1. Pairs with [00B — Costs & Free Alternatives](00B_Deployment_Costs_And_Free_Alternatives.md).
>
> **Heads-up (if you're brand new):** this chapter names tools — Docker, Caddy, Postgres, serverless, Kubernetes — that are *taught later*. Skim now just for the **decision** (where to host); come back after [Ch 16](16_Docker.md)–[Ch 21](21_PostgreSQL.md) for full understanding. The from-zero teaching starts at [01](01_What_Is_Deployment.md).

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

# Beginner Mistakes
- **Reaching for Kubernetes/serverless for one small app** — huge complexity + code changes for scale you don't have. Match the host to the *actual* load.
- **PaaS sticker shock at scale** — the free/cheap tier is fine to learn, but managed DB + always-on + bandwidth add up; know the real bill before committing.
- **On-prem with no off-site backup** — a factory fire/theft/disk-death loses everything. On-prem *requires* off-site backups ([Ch 28](28_Backups.md)).
- **Choosing a host that fights your artifacts** — you built Compose+Caddy; picking Cloud Run means redoing media/`$PORT` (RC1). Deploy where your artifacts already fit unless there's a strong reason.
- **Under-provisioning RAM** — Django+Postgres+Redis+Caddy on a 512 MB box will OOM-kill under load. 2 GB floor.

# Interview Questions
**Junior — "What's a VPS?"** A rented virtual Linux server in a data center — you get root and a public IP and run your own software on it, for a small monthly fee.

**Mid — "VPS vs PaaS — when would you pick each?"** VPS when you want control + low cost + to manage the stack yourself (and learn); PaaS when you want to push code and never touch the OS, accepting higher cost and less control. For a small, steady app on a budget, VPS; for a team that wants zero ops, PaaS.

**Senior — "This app is built as Docker Compose with local-filesystem media. What has to change to run it on Cloud Run, and would you?"** Cloud Run is stateless + multi-instance: media on local disk vanishes (move to S3/GCS via Django `STORAGES`), the container must honor `$PORT` (not hardcode `:8000`), and migrations must move to a one-off job (not per-instance entrypoint, to avoid races). For a steady small ERP I wouldn't — a single VPS matches the artifacts, costs less, and avoids the rework; Cloud Run earns its keep only with spiky/large traffic.

**Staff — "Design hosting for a garment ERP used mostly on the factory LAN but also remotely by the owner, on a tight budget, that must survive a site disaster."** Run the Compose stack on a factory-local mini-PC (LAN speed, internet-independent for the floor) **or** a cheap VPS; expose the owner's remote access via HTTPS (Caddy) + a domain, or a VPN if factory-local. Regardless of location, push **nightly encrypted off-site backups** (restic → cheap object storage) so a fire/theft is recoverable; rehearse the restore. Keep it single-box until user growth or reliability needs justify a load-balanced pair. Optimize for: floor uptime, tiny bill, and a survivable disaster story — not for scale the factory doesn't have.

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

# Homework
1. Answer the 4 decision questions (Practical) for *your* situation and write your host choice + one sentence why.
2. Open two VPS pricing pages (Hetzner, DigitalOcean) and find the cheapest plan with ≥2 GB RAM. Note the €/$ per month (feeds [00B](00B_Deployment_Costs_And_Free_Alternatives.md)).
3. Read your `docker-compose.yml` service list — confirm it's the single-box stack this chapter recommends a VPS for.
4. Write the pros/cons of running this ERP on a mini-PC *at the factory* vs a cloud VPS, in your own words. Which fits the owner's needs?

---

## Further Reading & Live Resources
- Hetzner Cloud pricing (cheapest solid VPS): https://www.hetzner.com/cloud
- DigitalOcean Droplets pricing: https://www.digitalocean.com/pricing/droplets
- Oracle Cloud **Always Free** (free ARM VM forever): https://www.oracle.com/cloud/free/
- Render (PaaS) — docs + pricing: https://render.com/pricing · Fly.io: https://fly.io/docs/ · Railway: https://railway.app/
- Google Cloud Run (serverless containers): https://cloud.google.com/run
- DigitalOcean — *Choosing a hosting type* / community tutorials hub: https://www.digitalocean.com/community/tutorials
- *The Twelve-Factor App* (why stateless matters for PaaS/serverless): https://12factor.net/
