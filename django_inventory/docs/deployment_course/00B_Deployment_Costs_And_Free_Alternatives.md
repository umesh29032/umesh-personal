---
id: deploy-course-00b-deployment-costs-and-free-alternatives
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 00B — Deployment Costs & Free / Open-Source Alternatives

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). ⭐ **Skim early.** Pairs with [00A — Where To Deploy](00A_Where_To_Deploy_Hosting_Options.md). Prices are **approximate (2025) — always check current pricing**; the *reasoning* is what lasts.
>
> **Heads-up (if you're brand new):** this chapter mentions tools (Docker, Postgres, Redis, restic) taught later. Skim now for the **cost picture**; return after [Ch 16](16_Docker.md)–[Ch 22](22_Redis.md) for full understanding. The from-zero teaching starts at [01](01_What_Is_Deployment.md).

# Learning Objectives
By the end of this chapter you can:
- estimate this deployment's real monthly cost
- tell a genuine free tier from a deferred bill
- decide what is worth paying for and what is not
- keep costs from growing quietly

# Purpose
To know **exactly what a real deployment costs**, **why** each paid piece exists (what problem the money solves), and the **free or open-source substitute** for each — so I can deploy this ERP for as little as **$0–6/month**, and understand the trade-off every time I choose "pay" vs "self-host." Money spent without understanding is waste; money saved without understanding is risk. This chapter gives the understanding.

# The Problem
Cloud marketing makes it feel like you must buy a dozen managed services. You don't. Almost every paid managed service is a **convenience wrapper around free open-source software** you can run yourself in a container. Paying buys *someone else operating it* (patching, backups, uptime, scaling). For a small factory ERP, self-hosting most of it on one box is cheaper *and* more educational — but a few things (a domain, off-site backup storage, maybe email) are worth paying pennies for. Knowing which is which is the skill.

# Theory (from zero) — the mental model

### What am I actually paying for?
Every line item is one of:
1. **Compute** — a computer to run the app (VPS / PaaS / serverless).
2. **A name** — the domain (DNS).
3. **Trust** — TLS certificate (identity + encryption).
4. **Managed data** — Postgres/Redis run *for* you (vs you running them).
5. **Storage** — disk for files/backups (esp. *off-site* backups).
6. **Eyes** — monitoring, error tracking, uptime alerts.
7. **Delivery** — email (SMTP), CDN.
8. **Automation** — CI/CD build minutes.

For each, the question is: **is operating this myself cheap and safe, or worth paying to outsource?**

### The golden rule
**Managed service price = open-source software (free) + "we operate it for you" (the fee).** Self-host when operating it is easy and low-risk (Postgres/Redis/Caddy on one box). Pay when operating it well is genuinely hard (email deliverability, off-site durable storage, global CDN) or when your time is worth more than the fee.

# Real World Example (My ERP) — the full cost table

| # | Piece | Why you'd pay (what the money solves) | Typical paid price | Free / open substitute | My ERP choice |
|---|---|---|---|---|---|
| 1 | **Domain name** | A memorable, ownable name; required for real HTTPS + branding | ~$10–15/yr (.com; Cloudflare/Namecheap at cost) | Free subdomains: **DuckDNS**, `*.nip.io`, a free `.eu.org` — fine for learning, not for a real business | **Buy a cheap .com** (~$1/mo amortized) — a factory brand needs a real name |
| 2 | **Compute (server)** | A always-on computer to run the stack | VPS **$4–6/mo** (Hetzner/DO); PaaS $7–25+/mo | **Oracle Cloud Always-Free** ARM VM ($0 forever); a mini-PC/old laptop at the factory ($0 ongoing); local dev ($0) | **Single VPS $5/mo** or **Oracle free** (see [00A](00A_Where_To_Deploy_Hosting_Options.md)) |
| 3 | **TLS / SSL certificate** | Encryption + verified identity (HTTPS) | Paid CAs sell certs $50–200/yr (rarely needed) | **Let's Encrypt = FREE**, auto-issued + auto-renewed by **Caddy** ([Ch 12](12_Caddy.md)) | **Let's Encrypt via Caddy — $0** |
| 4 | **PostgreSQL (database)** | Managed = automated backups, patching, failover, tuning | DO/RDS/Cloud SQL **$15–60/mo**; free tiers: Supabase/Neon (small) | **Self-host Postgres in Docker** ($0 extra — shares the VPS) + your own restic backups | **Self-host in Docker — $0** ([Ch 21](21_PostgreSQL.md)) |
| 5 | **Redis (cache/rate-limit)** | Managed = HA, persistence, monitoring | Upstash/Redis Cloud **$0 tiny → $10–15/mo** | **Self-host Redis in Docker** ($0 extra) | **Self-host in Docker — $0** ([Ch 22](22_Redis.md)) |
| 6 | **Off-site backup storage** | Durable copy so a server disaster isn't fatal (the one thing you must NOT self-host on the same box) | **Backblaze B2 ~$6/TB/mo** (a small DB = pennies); Cloudflare R2 (10 GB free, no egress) | B2/R2 **free tiers** cover a small ERP; or a *second* machine/location. **Do not** rely only on same-box backups | **B2 or R2 free/near-free** ([Ch 28](28_Backups.md)) |
| 7 | **Error tracking** | Get told about 500s before the owner calls; stack traces + context | **Sentry** free tier (5k errors/mo) → $26+/mo | **Self-host GlitchTip** (open-source, Sentry-API-compatible) in Docker; or structured **stdout logs + logrotate** ($0, what you have) | **Logs now ($0)**; add Sentry free tier or GlitchTip later ([Ch 32](32_Sentry.md)) |
| 8 | **Transactional email (SMTP)** | Password resets / notifications that actually reach inboxes (deliverability is hard to self-host) | Brevo/SendGrid/Mailgun/Postmark: **free ~100–300/day**, then $10–20/mo | Self-hosting a mail server is possible but **deliverability is painful** — usually not worth it | **A provider's free tier** ([Ch 24](24_Django_Settings.md) email settings) |
| 9 | **Uptime monitoring / alerts** | Know the site is down (from outside) within a minute | Pingdom etc. $10+/mo | **UptimeRobot free** (50 monitors); **self-host Uptime Kuma** (open-source) in Docker ($0) | **UptimeRobot free** or **Uptime Kuma $0** ([Ch 30](30_Monitoring.md)) |
| 10 | **Metrics/dashboards** | Graphs of CPU/RAM/requests over time | Datadog/Grafana Cloud $$ | **Self-host Prometheus + Grafana** (open-source) in Docker ($0); or just `htop`/`docker stats` early | **Skip early**; Prometheus+Grafana $0 when needed ([Ch 41](41_Scaling.md)) |
| 11 | **CI/CD build minutes** | Auto-test + auto-deploy on push | GitHub Actions free **2,000 min/mo** (private), then usage-based | **Deploy via an SSH script** (`deploy/deploy.sh`) from your laptop ($0); self-hosted Actions runner ($0 compute-on-your-box) | **SSH script now ($0)**; GitHub Actions free tier later ([Ch 33](33_CI_CD.md)) |
| 12 | **CDN (static asset edge cache)** | Faster global asset delivery + DDoS shielding | Paid CDNs $$ | **Cloudflare free tier** (generous CDN + basic DDoS) in front of your domain | **Cloudflare free** if/when needed; WhiteNoise serves statics fine at this scale ([Ch 25](25_Static_vs_Media.md)) |
| 13 | **DNS hosting** | Serve your domain's records reliably | Usually included by registrar/Cloudflare | **Cloudflare DNS free**; registrar DNS free | **$0** (registrar or Cloudflare) ([Ch 04](04_DNS_Domains.md)) |
| 14 | **Secrets management** | Store `.env`/keys securely, rotate, audit | Vault/AWS Secrets Manager $$ | **A locked-down `.env` file** on the VPS (0600, not in git) is fine at this scale ([Ch 23](23_Environment_Variables.md)) | **`.env` file — $0** |

### The bottom line for my ERP
- **Rock-bottom real deployment:** VPS **$5/mo** + domain **~$1/mo** (amortized) + everything else self-hosted/free ≈ **$6/month total.**
- **$0 learning deployment:** Oracle Always-Free VM + free subdomain + self-hosted stack ≈ **$0/month** (real, works, teaches everything).
- The only things I'd actively *pay* for even on a budget: a **real domain** (business identity) and **off-site backup storage** (pennies, but non-negotiable for disaster survival — [Ch 40](40_Disaster_Recovery.md)). Email uses a free tier. Everything else = self-hosted open-source in the Compose stack you already have.

# Visual Diagram
```
  MANAGED (you pay to NOT operate it)        SELF-HOSTED (free OSS you operate)
  ────────────────────────────────────       ─────────────────────────────────
  Managed Postgres  $15–60/mo    ───────►     Postgres in Docker        $0
  Managed Redis     $10–15/mo    ───────►     Redis in Docker           $0
  Paid TLS cert     $50–200/yr   ───────►     Let's Encrypt + Caddy     $0
  Sentry SaaS       $26+/mo      ───────►     GlitchTip / logs          $0
  Pingdom           $10+/mo      ───────►     Uptime Kuma / UptimeRobot $0
  Datadog           $$$          ───────►     Prometheus + Grafana      $0
  GitHub Actions $  (over free)  ───────►     deploy.sh over SSH        $0

  WORTH PAYING (small, hard-to-self-host):
    Domain  ~$12/yr  |  Off-site backup storage  ~pennies (B2/R2)  |  Email free tier

  MY ERP TOTAL:  ~$6/month (VPS+domain)   OR   $0 (Oracle free + free subdomain)
```

# Practical — how to inspect / estimate
```bash
# Estimate your DB backup storage cost (drives the B2/R2 bill — usually pennies)
du -sh /var/lib/docker/volumes/*postgres*    # size of the DB on disk
#   a few hundred MB of DB → gzip'd backup is tiny → well under B2/R2 free tiers
```
```bash
# Right-size the VPS so you don't overpay: watch real usage under load
docker stats --no-stream     # per-container CPU/RAM — if idle RAM << plan, downsize
free -h ; nproc              # if you're using 800MB of 4GB, a 2GB plan is cheaper
```
```bash
# Prove you don't need managed DB/Redis: they're just containers
docker compose ps            # db + redis run beside the app — $0 extra
```

# Production Walkthrough
- The bill for this deployment is dominated by **one VPS**. Everything else — Caddy, Postgres, Redis, the app — is open source running on it, so it adds no licence cost (ch 36).
- Certificates are free (Let's Encrypt, ch 12). Backup storage is pennies because a compressed dump of this database is small (ch 28).
- The costs that are easy to forget: the domain (annual), backup egress, and your own time on operations.
- Self-hosting Postgres and Redis as containers is the single biggest saving versus managed equivalents, and here it costs little because they are already part of the compose file.

# Debugging Guide
1. **Bill higher than expected** — check bandwidth and snapshot storage first; those are the usual culprits.
2. **Free tier stopped working** — credits expired or a limit was hit. Free tiers change; a production system should not depend on one.
3. **Disk cost climbing** — old backups not being pruned (ch 28).
4. **Managed service creeping in** — every convenience service added is a recurring cost and a lock-in.

# Performance Notes
- Right-size by measuring: watch memory and CPU under real load before paying for more.
- Compressed backups cut storage and transfer noticeably (ch 28).
- Over-provisioning is cheaper than downtime, but only slightly — measure rather than guess.

# Security Considerations
- **Never cut cost by cutting backups.** That is the one line that must not move (ch 28).
- Free tiers with weak isolation are a poor home for wage and receipt data.
- Cheap hosts sometimes lack basic protections; check what the provider actually offers.
- Encrypting backups costs nothing and protects everything.

# Architecture Decisions
- **Self-host the data services** as containers, since the compose file already runs them well.
- **Pay for the VPS and the domain; take free where it is genuinely free** (TLS, open-source software).
- **Avoid managed lock-in**, so the whole system stays portable (ch 40).
- **Backups are non-negotiable spend**, however small.

# Best Practices
- Write the monthly cost table down and revisit it quarterly.
- Set a billing alert; quiet growth is the failure mode.
- Prune backups on a policy, not on panic.
- Count your own time — ops hours are the real cost of the cheapest option.

# Beginner Mistakes
- **Buying managed Postgres/Redis for a tiny app.** $25–75/mo for what a $0 Docker container does at this scale. Managed earns its price only at real scale/HA needs.
- **Paying for TLS certs.** Never needed — Let's Encrypt + Caddy is free + automatic.
- **Skipping off-site backups to "save money."** The one place NOT to cheap out. Same-box backups die with the box. B2/R2 costs pennies. ([Ch 28](28_Backups.md)/[Ch 40](40_Disaster_Recovery.md).)
- **Over-provisioning the VPS "to be safe."** Measure with `docker stats`; a small ERP rarely needs more than 2 vCPU/2–4 GB.
- **Self-hosting email.** Deliverability (SPF/DKIM/reputation) is a rabbit hole; use a free provider tier.
- **Forgetting free tiers expire / have limits.** PaaS free tiers sleep; free DB tiers cap rows/connections. Fine for learning, read the limits before betting production on them.
- **Committing `.env` to save "setup time."** Leaks every secret. `.env` is free but must be gitignored + `0600` ([Ch 23](23_Environment_Variables.md)).

# Interview Questions
- **Junior:** "What does managed PostgreSQL give you that self-hosting doesn't, and is it worth it for a small app?" — Managed handles backups, patching, failover, and monitoring for a monthly fee. For a small app it's usually not worth it — a self-hosted Postgres container plus your own backup script covers the need at $0; managed pays off at scale or when you need high-availability you can't operate yourself.

- **Mid:** "Deploy this ERP for under $10/month. Itemize." — VPS ~$5 + domain ~$1 (amortized) + TLS $0 (Let's Encrypt/Caddy) + Postgres/Redis $0 (Docker) + off-site backups ~$0–1 (B2/R2 free tier) + email $0 (provider free tier) + monitoring $0 (UptimeRobot) ≈ **$6/mo**.

- **Senior:** "Which components would you refuse to self-host on the same box, and why?" — Off-site backup storage (must survive the box dying — the whole point) and, in practice, transactional email (deliverability + IP reputation are hard and one misstep lands you in spam). Everything else (app, DB, cache, proxy, uptime, metrics) is safe and economical to self-host on one box for this scale.

- **Staff:** "Design a cost-scaling path for this ERP from $6/mo to a reliable production budget as the factory grows." — Start single-VPS self-hosted ($6). First upgrade: keep the box, add a paid off-site backup + Sentry free/GlitchTip + UptimeRobot ($0–5). Growth: separate managed Postgres (offload backups/HA) and bump VPS RAM; add Cloudflare (free CDN/DDoS). Real scale: load-balanced app instances + managed DB with read replicas ([Ch 41](41_Scaling.md)). Each step is triggered by a *measured* need (RAM pressure, downtime cost, ops time), never by default — spend to remove a proven pain, not to feel safe.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Can you itemise a real monthly cost? | "A small server, maybe $5 a month." | Itemise it: **VPS ~$5 + domain ~$1 amortised + TLS $0 (Let's Encrypt) + Postgres/Redis $0 (containers) + off-site backups ~$0–1 (B2/R2 free tier)**. The itemisation is the answer — a single number hides what you forgot. |
| Do you know what you must NOT self-host on the same box? | "Self-hosting everything saves the most money." | **Off-site backup storage** — hosting your backups on the box they protect defeats the entire point — and in practice **transactional email**, because deliverability and IP reputation are hard and outsourced cheaply. Everything else is fair game. |
| Is managed Postgres worth it here? | "Managed databases are the professional choice." | Managed buys **backups, patching, failover, monitoring** for a monthly fee. For one small app it is usually **not worth it** — a container plus a rehearsed restore covers the same risk far cheaper. The professional choice is the one you can justify. |
| ⚠️ Do you know the one line that must not move? | "We can trim backups to cut costs." | **Never save money by cutting backups.** Encryption is free, B2/R2 free tiers cover a small database, and the alternative is losing the factory's books. Every other line in the budget is negotiable; this one is not. |

**The killer follow-up:** *"What is the real cost of the cheapest option?"* — **your own time.** Self-hosting means you are the DBA, the sysadmin and the on-call engineer. A budget that does not count ops hours is not a budget — and it is the number most people leave out entirely.

# Revision Notes
- Cost ≈ **one VPS + a domain**. Caddy/Postgres/Redis/Django are free software.
- TLS is free (Let's Encrypt). Backup storage is pennies for a small DB.
- Forgotten costs: bandwidth, snapshot storage, domain renewal, **your ops time**.
- Free tier ≠ free forever — credits expire, limits throttle. Don't build production on one.
- ⚠️ **Never save money by skipping backups.** Encryption is free anyway.

# Cheat Sheet
- **Managed price = free OSS + "we run it."** Self-host when running it is easy/low-risk; pay when it's genuinely hard (email, off-site storage, global CDN) or your time > the fee.
- **Free/$0 in my stack:** TLS (Let's Encrypt/Caddy), Postgres, Redis, monitoring (Uptime Kuma/UptimeRobot), metrics (Prometheus/Grafana), CI (SSH deploy), CDN (Cloudflare free), DNS, secrets (`.env`).
- **Worth paying (small):** domain ~$12/yr, off-site backup storage ~pennies (B2/R2), email free tier.
- **My ERP total:** ~**$6/mo** (VPS+domain) or **$0** (Oracle free + free subdomain).
- **Never cheap out on:** off-site backups. **Never pay for:** TLS certs, managed DB/Redis at this scale.
- Right-size with `docker stats` / `free -h`; don't over-provision.

# My ERP Section
| Piece | My choice | Cost | Chapter |
|---|---|---|---|
| Compute | single VPS (or Oracle free) | $5 / $0 | [00A](00A_Where_To_Deploy_Hosting_Options.md) |
| Domain | cheap .com | ~$1/mo | [04](04_DNS_Domains.md) |
| TLS | Let's Encrypt + Caddy | $0 | [12](12_Caddy.md) |
| Postgres | Docker container | $0 | [21](21_PostgreSQL.md) |
| Redis | Docker container | $0 | [22](22_Redis.md) |
| Off-site backups | restic → B2/R2 | ~$0 | [28](28_Backups.md) |
| Error tracking | logs now; Sentry-free/GlitchTip later | $0 | [32](32_Sentry.md) |
| Email | provider free tier | $0 | [24](24_Django_Settings.md) |
| Uptime | UptimeRobot / Uptime Kuma | $0 | [30](30_Monitoring.md) |
| CI/CD | `deploy.sh` over SSH | $0 | [33](33_CI_CD.md) |
| Secrets | `.env` (0600, gitignored) | $0 | [23](23_Environment_Variables.md) |
| **Total** | | **~$6/mo or $0** | |

# Practice Tasks
1. **Read the code:** list every service in `docker-compose.yml` and its managed-equivalent monthly price.
2. **Debug:** measure this stack's memory and disk at rest, then pick the smallest VPS that fits.
3. **Design:** write the monthly cost table with a line for backups and one for your time.
4. **Architecture:** argue self-hosted Postgres versus managed for a factory with one maintainer.

# Homework
1. Build your own copy of the cost table for *your* chosen host: fill real prices from the provider pages. What's your monthly total?
2. `du -sh` your Postgres volume; estimate the gzipped backup size; confirm it fits B2/R2's free tier.
3. For each of Postgres, Redis, TLS, monitoring: write one sentence — "self-host because ___" or "pay because ___".
4. Name the ONE thing you will pay for even on a $0 budget, and why. (Hint: it survives the server dying.)
5. Decide your stack's total: the **$6/mo VPS path** or the **$0 Oracle-free path** — and write why for your situation.

---

> 💡 **Samjho aise:** Yahan **paisa** ki baat hai. "Free" tier waqai free hota hai — par uski keemat
> alag hoti hai: sone ke baad app so jaata hai, ya data ka backup aapka sirdard hai.
> Asli sawaal yeh nahi *"kitna sasta"*, balki *"kis cheez ka jhanjhat main khud
> uthaunga aur kis cheez ka paisa dekar hataunga"*.

# Further Reading & Live Resources
- Hetzner Cloud pricing: https://www.hetzner.com/cloud · DigitalOcean pricing: https://www.digitalocean.com/pricing
- Oracle Cloud Always Free: https://www.oracle.com/cloud/free/
- Let's Encrypt (free TLS): https://letsencrypt.org/
- Backblaze B2 pricing: https://www.backblaze.com/cloud-storage/pricing · Cloudflare R2 (10 GB free): https://developers.cloudflare.com/r2/pricing/
- Supabase (free Postgres tier): https://supabase.com/pricing · Neon (free Postgres): https://neon.tech/pricing
- GlitchTip (open-source, self-hosted Sentry alternative): https://glitchtip.com/ · Sentry pricing: https://sentry.io/pricing/
- Uptime Kuma (open-source uptime monitor): https://github.com/louislam/uptime-kuma · UptimeRobot free: https://uptimerobot.com/pricing/
- Brevo/SendGrid/Mailgun free email tiers: https://www.brevo.com/pricing/ · https://sendgrid.com/en-us/pricing · https://www.mailgun.com/pricing/
- Cloudflare (free CDN/DNS/DDoS): https://www.cloudflare.com/plans/
- GitHub Actions pricing (free minutes): https://github.com/pricing
- **awesome-selfhosted** (huge list of free/open replacements for paid services): https://github.com/awesome-selfhosted/awesome-selfhosted
