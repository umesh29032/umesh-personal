---
id: deploy-course-05-ip-address-and-ports
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 05 — IP Addresses & Ports

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Prev: [04 — DNS & Domains](04_DNS_Domains.md). Next: [06 — Linux Basics](06_Linux_Basics.md). *(Completes Term 1 — Fundamentals.)*

# Learning Objectives
By the end of this chapter you can:
- explain IP + port as building + flat number
- say why `127.0.0.1` is safer than `0.0.0.0`
- list which ports this project exposes, and which it must never expose
- read a `ports:` line in docker-compose and predict the consequence

# Purpose
To make three fuzzy things precise: **which address** a program listens on (`127.0.0.1` vs `0.0.0.0` vs a public IP), **which port** identifies a program, and **the firewall** that decides what the outside world may reach. These three explain most "works on the server but not from outside" and "port already in use" mysteries, and they're exactly the knobs my `docker-compose.yml` and VPS firewall set.

# The Problem
A single machine (my VPS) runs Caddy, Gunicorn, Postgres, and Redis at once. When a packet arrives, the OS must know *which* of those four programs it's for — that's the **port**. And I must decide *who* can reach *what*: the internet may reach Caddy (443) but must never reach Postgres (5432). Get the address/port/firewall wrong and either nothing is reachable, or everything is — including your database, to attackers.

# Theory (from zero)

### IP address = machine address; two kinds
- **Public IP** — globally routable, reachable from the internet (my VPS has one, e.g. `203.0.113.10`).
- **Private IP** — only routable inside a local network (`10.x.x.x`, `172.16–31.x.x`, `192.168.x.x`). Home routers + Docker networks use these. Not reachable from the internet.
- **Loopback / localhost** — `127.0.0.1` (and name `localhost`): "this same machine, never leaves it."

### The critical trio: `127.0.0.1` vs `0.0.0.0` vs a specific IP (bind address)
When a program "listens," it binds to an address that decides *who can connect*:
- **`127.0.0.1`** — accept connections **only from this machine**. (Your `runserver` default → why your phone couldn't reach it in [Ch 01](01_What_Is_Deployment.md) homework.)
- **`0.0.0.0`** — accept on **all** the machine's network interfaces (localhost + LAN + public). "Listen everywhere."
- **a specific IP** — only on that one interface.

This is the #1 beginner confusion. `runserver 127.0.0.1:8000` = reachable only from the box. `runserver 0.0.0.0:8000` = reachable from other devices (and, on a public box with an open firewall, the internet).

### Port = which program on the machine
A **port** is a number (0–65535) that routes a connection to a specific listening program. Conventions:
- **80** = HTTP, **443** = HTTPS (the web).
- **22** = SSH ([Ch 07](07_SSH.md)).
- **5432** = PostgreSQL, **6379** = Redis, **8000** = common dev/app port (Gunicorn here).
An "address:port" pair a program listens on is a **socket**, e.g. `0.0.0.0:443`. Only **one** program can listen on a given address:port at a time → "address already in use" errors.

### Firewall = who may reach which port
The OS/cloud **firewall** allows or blocks incoming connections per port. A server should expose the *minimum*: on my VPS, allow **22 (SSH), 80 (HTTP→redirect + ACME), 443 (HTTPS)** — and block everything else. Postgres (5432) and Redis (6379) must **never** be open to the internet. Two layers usually apply: the **cloud provider's security group** (outside the VM) and the VM's own firewall (`ufw` on Ubuntu).

### How Docker changes the picture (preview of [Ch 19](19_Docker_Networking.md))
Containers get **private** IPs on a Docker network and talk to each other **by service name** (`db`, `redis`). A container's port is only reachable from the host/internet if you explicitly **publish** it (`ports:` in compose). In my stack, **only Caddy publishes 80/443 to the host**; Gunicorn/Postgres/Redis publish nothing — they're reachable only inside the private Docker network. That's a firewall you get "for free" from not publishing.

### The two-firewall mental model for my VPS
```
Internet ──► [cloud security group: allow 22,80,443] ──► VM
                                                          [ufw: allow 22,80,443]
                                                          Docker: only Caddy publishes 80,443
                                                          (db 5432 / redis 6379 = private, unpublished)
```

> 💡 **Samjho aise:** IP **building ka pata** hai, port us building ka **flat number**. Ek hi server pe website (80/443), database (5432), aur Redis (6379) — sab alag flat mein. Aur `127.0.0.1` matlab *"isi building ke andar"* — bahar se koi us flat tak pahunch hi nahi sakta.

# Real World Example (My ERP)
- **Caddy** binds `0.0.0.0:80` and `0.0.0.0:443` *inside its container* and **publishes** them to the host (`docker-compose.yml` `ports: ["80:80","443:443"]` on the caddy service only). So the internet reaches Caddy.
- **Gunicorn** binds `0.0.0.0:8000` inside its container but the `web` service has **no `ports:`** → not published → unreachable from the internet, only from Caddy over the private network. (Binding `0.0.0.0` *inside* a container is fine precisely because the container isn't published.)
- **Postgres** listens on 5432, **Redis** on 6379 — both **unpublished**; Django reaches them by name via `DATABASE_URL=…@db:5432/…` and `REDIS_URL=redis://redis:6379/0` ([Ch 21](21_PostgreSQL.md)/[Ch 22](22_Redis.md)).
- **VPS firewall**: allow 22/80/443 only. If I ever "can't connect to the site from outside but `curl localhost` works on the box," the firewall/security group is blocking 443.
- **Django's own port**: none directly — it's served by Gunicorn; Django never opens a socket itself in production.

# Visual Diagram
```
                 MY VPS (public IP 203.0.113.10)
 Internet ─443─►  ┌──────────────────────────────────────────┐
 Internet ─80──►  │ firewall: ALLOW 22, 80, 443  (deny rest)  │
 SSH ─────22──►   │                                           │
                  │   Docker private network 172.x            │
                  │   ┌────────┐ published 80,443             │
                  │   │ caddy  │◄── only container facing host │
                  │   └────────┘                              │
                  │       │ 8000 (private)                    │
                  │   ┌────────┐   ┌──────┐ 5432   ┌───────┐  │
                  │   │  web   │──►│  db  │        │ redis │  │
                  │   │gunicorn│   │ 5432 │        │ 6379  │  │
                  │   └────────┘   └──────┘        └───────┘  │
                  │   (web/db/redis publish NOTHING to host)  │
                  └──────────────────────────────────────────┘

 127.0.0.1 = only this machine   |   0.0.0.0 = every interface   |   port = which program
```

# Practical — how to inspect it
```bash
# What is this machine's IPs?
ip addr            # all interfaces + their IPs (look for the public one, and docker0)
curl -s ifconfig.me ; echo     # what the internet sees as my public IP
```

```bash
# What is LISTENING, on which address:port, and which process?
sudo ss -tulpn     # s=sockets: t=tcp u=udp l=listening p=process n=numeric
#   LISTEN 0 511 0.0.0.0:443  →  caddy      (public)
#   LISTEN 0 511 127.0.0.1:...                (localhost-only)
```
`ss` (or older `netstat -tulpn`) is the single most useful "who's on which port" command. If `0.0.0.0:5432` ever shows up on a public box, your DB is exposed — fix immediately.

```bash
# Is a port reachable FROM OUTSIDE? (run from your laptop, not the server)
nc -vz 203.0.113.10 443     # open? → firewall+listener OK.  refused → nothing listening. timeout → firewall blocks.
```
"refused" vs "timeout" is diagnostic: refused = reached the box, nothing on that port; timeout = firewall silently dropping.

```bash
# The VPS firewall (Ubuntu ufw)
sudo ufw status verbose      # see allowed ports
sudo ufw allow 443/tcp       # (example) open HTTPS
```

```bash
# Docker: which container ports are PUBLISHED to the host?
docker compose ps            # PORTS column — expect only caddy mapping 0.0.0.0:80/443
docker port <caddy-container># explicit published mappings
```

# Production Walkthrough
- **Public:** 80 (redirects to HTTPS) and 443. That is the entire public surface.
- **Private:** Postgres 5432 and Redis 6379 exist **only on the Docker network** — no `ports:` line publishes them, and that omission is a security control, not an oversight.
- Containers reach each other by **service name** (`db`, `redis`), so no IP is ever hardcoded (ch 19).
- On your laptop the same services bind to localhost, which is why `db.sh` connects without any firewall concern.

# Debugging Guide
1. **"Connection refused"** = nothing is listening there. **"Timeout"** = something is filtering (firewall).
2. **`ss -tlnp`** on the server — what is actually listening, and on which interface?
3. **Bound to `127.0.0.1` but you need external access?** That is a binding problem, not a firewall one.
4. **`docker compose ps`** shows published ports; if Postgres shows one, that is a finding.
5. Test from **inside** the container (`docker compose exec web curl db:5432`) to separate networking from application errors.

# Performance Notes
- Localhost/private-network traffic never touches the physical network — effectively free.
- Port exhaustion is a real limit under very high connection churn; keep-alive and pooling avoid it.
- Each listening service is a process with memory cost; do not run what you do not need.

# Security Considerations
- **Publishing 5432 to the internet is the single most common fatal mistake** in self-hosted Postgres. Scanners find it within minutes.
- `0.0.0.0` means "every interface" — only Caddy should ever do that.
- The firewall should default-deny and allow 22/80/443 only.
- SSH on 22 is fine *with keys*; the port number is not the protection (ch 07).

# Architecture Decisions
- **Explicitly do not publish database/cache ports.** Access is via the app's private network only.
- **One public process** (Caddy), so hardening effort concentrates in one config file.
- **Service-name addressing** inside Compose so containers can be replaced without touching config.

# Best Practices
- Audit `ports:` in compose before every deploy — it is a two-line diff that can expose a database.
- Bind admin tooling to localhost and reach it over SSH, never open a port for it.
- Keep the firewall rules in the runbook, not only in someone's memory.

# Beginner Mistakes
- **Binding `0.0.0.0` on a public box with an open firewall by accident** → exposing a dev server / DB to the internet. On a *public* host, "listen everywhere" + "firewall allows it" = "the world can connect."
- **Publishing the DB port** (`ports: ["5432:5432"]`) "to connect with pgAdmin" → your database is now internet-reachable. Use an SSH tunnel instead ([Ch 07](07_SSH.md)).
- **"It works on the server, not from outside."** Classic firewall/security-group block on 80/443. `curl localhost` (on box) vs `nc -vz <public-ip> 443` (from laptop) pinpoints it.
- **"Address already in use."** Two programs fighting for one port; find the holder with `ss -tulpn` and stop it.
- **Confusing container-internal `0.0.0.0:8000` with "exposed."** Inside an unpublished container it's private; publishing is what exposes it.

# Interview Questions
- **Junior:** "Difference between `127.0.0.1` and `0.0.0.0` when a server binds?" — `127.0.0.1` accepts connections only from the same machine; `0.0.0.0` accepts on all network interfaces (reachable from other machines, subject to the firewall).

- **Junior:** "What's a port?" — A number identifying a specific listening program on a machine, so incoming connections reach the right service (80=HTTP, 443=HTTPS, 22=SSH, 5432=Postgres).

- **Mid:** "Site unreachable from the internet but `curl localhost` works on the VPS. Diagnose." — The app/proxy is fine; the network path is blocked. Check the cloud security group + `ufw` allow 80/443, confirm the proxy publishes those ports, and test from outside with `nc -vz <public-ip> 443` (refused vs timeout tells you listener-vs-firewall).

- **Senior:** "How do you connect a DB GUI to production Postgres without exposing 5432?" — Don't publish 5432. Use an SSH tunnel: `ssh -L 5432:localhost:5432 user@vps` (or `db:5432` via the container), then point the GUI at `localhost:5432`. The DB stays private; access rides the authenticated SSH channel.

- **Staff:** "Design the port/firewall posture for this ERP and justify each open port." — Public: 443 (HTTPS app), 80 (HTTP→HTTPS redirect + ACME challenge), 22 (SSH, ideally key-only and IP-restricted). Everything else denied at both the cloud security group and host `ufw`. Postgres/Redis unpublished (private Docker net) so they're unreachable even if the host firewall were misconfigured — defense in depth. Rationale: minimize attack surface to the two ports the public genuinely needs plus admin access, and make the data stores unreachable by construction, not just by rule.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| `127.0.0.1` vs `0.0.0.0` — do you know it is a security decision? | "They both mean this machine." | `127.0.0.1` accepts **only local** connections; `0.0.0.0` accepts on **every interface**. Binding 0.0.0.0 by accident is how a "local" admin service becomes internet-facing. |
| Reachable locally, not from outside — can you diagnose in one step? | "The app must be down." | It is not — `curl localhost` proved that. It is the **network path**: cloud security group, host `ufw`, and whether the proxy actually **publishes** the port. **`nc -vz <public-ip> 443`: refused = no listener, timeout = firewall.** That distinction is the whole answer. |
| Can you reach production Postgres without exposing it? | "Open 5432 to my office IP." | **Do not publish 5432 at all.** `ssh -L 5432:localhost:5432 user@vps`, then point the GUI at `localhost:5432`. Access rides the **authenticated SSH channel** and disappears when you close it — no permanent surface to forget about. |
| Can you justify every open port? | "80, 443, 22 and 5432 for admin." | Public: **443** (app), **80** (redirect + ACME), **22** (key-only, ideally IP-restricted). Everything else denied at **both** the cloud security group and host `ufw`. Postgres/Redis **unpublished**, so they are unreachable *by construction* even if a firewall rule is wrong — defence in depth. |

**The killer follow-up:** *"Your firewall rule is misconfigured. Is your database exposed?"* — with unpublished ports, **no** — there is nothing listening publicly to reach. That is the difference between a rule you must get right and an architecture that cannot be got wrong, and it is the point of the whole chapter.

# Revision Notes
- IP = building, **port = flat number**; both needed to reach a process.
- `127.0.0.1` = this machine only · `0.0.0.0` = every interface (public).
- This project: **80/443 public; 5432 and 6379 private, never published**.
- "Refused" = nothing listening · "timeout" = firewall.
- Compose services talk by **name**, not IP.

# Cheat Sheet
- **IP** = machine (public = internet-reachable, private/`10./172./192.168.` = LAN, `127.0.0.1` = this box only).
- **Bind address:** `127.0.0.1` = local-only, `0.0.0.0` = all interfaces, specific-IP = one interface.
- **Port** = which program (80 http, 443 https, 22 ssh, 5432 pg, 6379 redis, 8000 gunicorn). `address:port` = socket; one listener each.
- **Firewall:** open the minimum (22/80/443); never expose 5432/6379.
- **Inspect:** `ss -tulpn` (who's listening), `nc -vz host port` (reachable from outside?), `ufw status`, `docker compose ps` (published ports).
- Docker: containers are private; only **published** ports reach the host/internet — in my stack, only Caddy.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Public ports | 443 + 80 (Caddy), 22 (SSH) |
| Published to host | only the `caddy` service (`docker-compose.yml` `ports:`) |
| Gunicorn port | 8000, private (no `ports:` on `web`) |
| Postgres/Redis | 5432 / 6379, private, reached by name `db`/`redis` |
| Firewall | VPS `ufw` + cloud security group: allow 22/80/443 |
| DB admin access | SSH tunnel, never a published 5432 |

# Practice Tasks
1. **Read the code:** list every `ports:` entry in `docker-compose.yml`. Which are public? Is any of them a mistake?
2. **Debug:** run `ss -tlnp` locally and identify what is listening on 5432 and on which interface.
3. **Design:** you need temporary direct psql access to production. Design the safe way (hint: not a firewall rule).
4. **Architecture:** argue whether moving SSH off port 22 improves security, and what actually does.

# Homework
1. On any Linux box: `sudo ss -tulpn` — list every listener, its bind address, and process. Which are `0.0.0.0` (exposed if firewall allows) vs `127.0.0.1` (local only)?
2. Reproduce [Ch 01](01_What_Is_Deployment.md)'s finding: `python -m http.server 8080 --bind 127.0.0.1` (phone can't reach) vs `--bind 0.0.0.0` (phone can). Explain in terms of bind address.
3. From your laptop, `nc -vz <some-public-site> 443` and `nc -vz <same> 5432`. Explain why one connects and one refuses/times-out.
4. Write your VPS firewall plan: which ports open, which closed, and one sentence why 5432 stays closed.
5. Predict what `docker compose ps` PORTS column will show for `caddy` vs `db` in your stack, and why.

---

# Further Reading & Live Resources
- Cloudflare Learning — *What is an IP address?*: https://www.cloudflare.com/learning/dns/glossary/what-is-my-ip-address/
- Cloudflare Learning — *What is a computer port?*: https://www.cloudflare.com/learning/network-layer/what-is-a-computer-port/
- Wikipedia — *List of TCP and UDP port numbers* (reference): https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers
- DigitalOcean — *UFW Essentials: Common Firewall Rules and Commands*: https://www.digitalocean.com/community/tutorials/ufw-essentials-common-firewall-rules-and-commands
- Docker docs — *Container networking / published ports*: https://docs.docker.com/network/
- `ss` manual (util-linux/iproute2): https://man7.org/linux/man-pages/man8/ss.8.html
- Julia Evans — *Networking tools/zines* (beginner-friendly): https://wizardzines.com/
- **Free book** — Beej's Guide to Network Programming (sockets, ports, from zero): https://beej.us/guide/bgnet/
