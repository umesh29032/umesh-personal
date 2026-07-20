# 05 — IP Addresses & Ports

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Prev: [04 — DNS & Domains](04_DNS_Domains.md). Next: [06 — Linux Basics](06_Linux_Basics.md). *(Completes Term 1 — Fundamentals.)*

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

# Beginner Mistakes
- **Binding `0.0.0.0` on a public box with an open firewall by accident** → exposing a dev server / DB to the internet. On a *public* host, "listen everywhere" + "firewall allows it" = "the world can connect."
- **Publishing the DB port** (`ports: ["5432:5432"]`) "to connect with pgAdmin" → your database is now internet-reachable. Use an SSH tunnel instead ([Ch 07](07_SSH.md)).
- **"It works on the server, not from outside."** Classic firewall/security-group block on 80/443. `curl localhost` (on box) vs `nc -vz <public-ip> 443` (from laptop) pinpoints it.
- **"Address already in use."** Two programs fighting for one port; find the holder with `ss -tulpn` and stop it.
- **Confusing container-internal `0.0.0.0:8000` with "exposed."** Inside an unpublished container it's private; publishing is what exposes it.

# Interview Questions
**Junior — "Difference between `127.0.0.1` and `0.0.0.0` when a server binds?"** `127.0.0.1` accepts connections only from the same machine; `0.0.0.0` accepts on all network interfaces (reachable from other machines, subject to the firewall).

**Junior — "What's a port?"** A number identifying a specific listening program on a machine, so incoming connections reach the right service (80=HTTP, 443=HTTPS, 22=SSH, 5432=Postgres).

**Mid — "Site unreachable from the internet but `curl localhost` works on the VPS. Diagnose."** The app/proxy is fine; the network path is blocked. Check the cloud security group + `ufw` allow 80/443, confirm the proxy publishes those ports, and test from outside with `nc -vz <public-ip> 443` (refused vs timeout tells you listener-vs-firewall).

**Senior — "How do you connect a DB GUI to production Postgres without exposing 5432?"** Don't publish 5432. Use an SSH tunnel: `ssh -L 5432:localhost:5432 user@vps` (or `db:5432` via the container), then point the GUI at `localhost:5432`. The DB stays private; access rides the authenticated SSH channel.

**Staff — "Design the port/firewall posture for this ERP and justify each open port."** Public: 443 (HTTPS app), 80 (HTTP→HTTPS redirect + ACME challenge), 22 (SSH, ideally key-only and IP-restricted). Everything else denied at both the cloud security group and host `ufw`. Postgres/Redis unpublished (private Docker net) so they're unreachable even if the host firewall were misconfigured — defense in depth. Rationale: minimize attack surface to the two ports the public genuinely needs plus admin access, and make the data stores unreachable by construction, not just by rule.

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

# Homework
1. On any Linux box: `sudo ss -tulpn` — list every listener, its bind address, and process. Which are `0.0.0.0` (exposed if firewall allows) vs `127.0.0.1` (local only)?
2. Reproduce [Ch 01](01_What_Is_Deployment.md)'s finding: `python -m http.server 8080 --bind 127.0.0.1` (phone can't reach) vs `--bind 0.0.0.0` (phone can). Explain in terms of bind address.
3. From your laptop, `nc -vz <some-public-site> 443` and `nc -vz <same> 5432`. Explain why one connects and one refuses/times-out.
4. Write your VPS firewall plan: which ports open, which closed, and one sentence why 5432 stays closed.
5. Predict what `docker compose ps` PORTS column will show for `caddy` vs `db` in your stack, and why.

---

## Further Reading & Live Resources
- Cloudflare Learning — *What is an IP address?*: https://www.cloudflare.com/learning/dns/glossary/what-is-my-ip-address/
- Cloudflare Learning — *What is a computer port?*: https://www.cloudflare.com/learning/network-layer/what-is-a-computer-port/
- Wikipedia — *List of TCP and UDP port numbers* (reference): https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers
- DigitalOcean — *UFW Essentials: Common Firewall Rules and Commands*: https://www.digitalocean.com/community/tutorials/ufw-essentials-common-firewall-rules-and-commands
- Docker docs — *Container networking / published ports*: https://docs.docker.com/network/
- `ss` manual (util-linux/iproute2): https://man7.org/linux/man-pages/man8/ss.8.html
- Julia Evans — *Networking tools/zines* (beginner-friendly): https://wizardzines.com/
- **Free book** — Beej's Guide to Network Programming (sockets, ports, from zero): https://beej.us/guide/bgnet/
