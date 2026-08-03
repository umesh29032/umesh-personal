---
id: deploy-course-02-how-the-internet-works
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 02 — How The Internet Works

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Prev: [01 — What Is Deployment](01_What_Is_Deployment.md). Next: [03 — HTTP & HTTPS](03_HTTP_HTTPS.md).

# Learning Objectives
By the end of this chapter you can:
- trace a request from a phone in the factory to your Django view
- explain packets, IP and routing without jargon
- say what a TCP handshake costs and why keep-alive matters
- name which hop is responsible when a page will not load

# Purpose
Before I can put my ERP "on the internet," I need to know what the internet *is* mechanically — how a tap on a worker's phone becomes bytes arriving at my VPS and a page coming back. Without this, terms like DNS, IP, port, TLS, and "reverse proxy" are magic words. With it, deployment is just wiring a pipe I understand.

# The Problem
My ERP runs on a computer (the VPS) in some data center. A worker holds a phone somewhere on a mobile network. These two machines have never met. Something has to (a) *find* my server among billions of machines, (b) open a *reliable, private* channel across untrusted networks, and (c) carry a *request* and bring back a *response*. "Deploying to the internet" means making my server a correct participant in that system.

# Theory (from zero)

### 1. It's all just computers sending numbered envelopes
The internet is millions of computers connected by cables and radios. They communicate by breaking every message into small **packets** (envelopes of bytes). Each packet carries a **destination address** and a **source address** and a chunk of data. Routers along the way read the destination and pass the packet toward it, hop by hop, like a postal system. Packets can take different routes, arrive out of order, or get lost.

### 2. Addresses = IP; the phonebook = DNS
Every machine on the internet has an **IP address** (e.g. `203.0.113.10`) — its postal address. Humans can't remember those, so we use **domain names** (`erp.example.com`) and a global phonebook called **DNS** turns the name into the IP. (DNS = [Ch 04](04_DNS_Domains.md); IPs/ports = [Ch 05](05_IP_Address_and_Ports.md).)

### 3. Reliable pipe out of unreliable packets = TCP
Packets alone are lossy and unordered. **TCP** is a protocol layered on top that gives a **reliable, ordered stream**: it numbers packets, re-sends lost ones, and reassembles them in order. When two machines "open a TCP connection," they first do a **handshake** (SYN → SYN-ACK → ACK — a three-step "can you hear me? yes, can you? yes"), then bytes flow both ways reliably. A web request rides on a TCP connection.

### 4. A connection targets an IP **and a port**
A server machine runs many programs. A **port** number says *which program* on that machine the connection is for. Web traffic uses **port 80** (HTTP) and **port 443** (HTTPS) by convention. So "connect to `erp.example.com`" really means "DNS-resolve it to an IP, then open a TCP connection to that IP on port 443." (Ports = [Ch 05](05_IP_Address_and_Ports.md).)

### 5. Privacy + trust = TLS (the S in HTTPS)
Raw TCP is readable by anyone on the path (wifi, ISP, routers). **TLS** wraps the TCP stream in encryption *and* proves the server is really `erp.example.com` (via a **certificate**, [Ch 03](03_HTTP_HTTPS.md)). HTTP over TLS = **HTTPS**. Without it, a worker's login password would travel in clear text.

### 6. The message itself = HTTP
Inside the encrypted TCP stream, the two machines speak **HTTP**: the client sends a **request** ("GET /production/my-work/ …"), the server sends a **response** ("200 OK … <html>…"). That's [Ch 03](03_HTTP_HTTPS.md).

### 7. Client vs server
The phone is the **client** (initiates the request). My VPS is the **server** (listens, responds). "Deploying" = making my machine a *server*: it must have a stable public address (IP), a name pointing to it (DNS), and a program *listening* on a port (Caddy on 443) ready to answer.

### The whole trip, once
Worker taps a link → phone asks **DNS** for `erp.example.com` → gets my VPS's **IP** → opens a **TCP** connection to that IP on **port 443** → **TLS** handshake sets up encryption + verifies the cert → phone sends the **HTTP** request inside → it arrives at my VPS, where **Caddy** is listening on 443 → Caddy forwards to **Gunicorn** → Django builds the page → back up the same pipe.

> 💡 **Samjho aise:** Internet ek **courier network** hai. Aapka message chhote-chhote **packets** (lifafe) mein toot ke jaata hai, har lifafe pe pata (IP) likha hota hai, aur raste mein kai **router** (chhaanti karne wale daftar) use aage badhate hain. Lifafe alag-alag raste se ja sakte hain — pahunch ke dobara sahi kramm mein jud jaate hain.

# Real World Example (My ERP)
- The "stable public address" is my **VPS's public IP** (I get it from the hosting provider). 
- The name is whatever domain I point at it, configured in my **`.env`** as `ALLOWED_HOSTS=erp.example.com` and `CSRF_TRUSTED_ORIGINS=https://erp.example.com` — Django rejects requests whose `Host` header isn't in `ALLOWED_HOSTS` (a safety check that only works *because* the internet includes liars).
- The program **listening on 443** is my **Caddy** container (the only one publishing ports to the host). Gunicorn listens on 8000 but only on the **private Docker network** — unreachable from the internet, which is exactly the point of [Ch 01](01_What_Is_Deployment.md)'s shape.
- TLS is handled by **Caddy automatically** (Let's Encrypt) — [Ch 03](03_HTTP_HTTPS.md)/[Ch 12](12_Caddy.md).

# Visual Diagram
```
 WORKER PHONE (client)                                    MY VPS (server)
   │                                                          
   │ 1. "where is erp.example.com?"  ──────────►  DNS  ──►  203.0.113.10
   │ 2. open TCP to 203.0.113.10 : 443  ───────────────────────►  (SYN/ACK handshake)
   │ 3. TLS handshake (encrypt + verify certificate) ──────────►  CADDY listening :443
   │ 4. HTTP request (encrypted)  GET /production/my-work/ ────►  CADDY
   │                                                              │ forwards :8000 (private)
   │                                                              ▼
   │                                                          GUNICORN → Django → PG/Redis
   │ ◄──────────── 5. HTTP response (encrypted) 200 OK <html> ───┘
```

# Practical — how to inspect it
Run these from your **laptop** against any site (or your VPS once it's up). Every command explained.

```bash
# DNS: resolve a name to an IP (the phonebook lookup)
dig +short erp.example.com          # prints the IP(s) the name points to
getent hosts erp.example.com        # same idea, via the OS resolver
```
`dig` = "domain information groper", asks DNS directly. `+short` = just the answer.

```bash
# TCP+port: is something listening there? (open a raw connection)
nc -vz erp.example.com 443          # nc = netcat; -v verbose, -z just test, don't send data
```
"succeeded" = a program is listening on 443. "refused" = nothing there. "timed out" = a firewall is dropping it silently ([Ch 05](05_IP_Address_and_Ports.md)).

```bash
# The full HTTP+TLS round trip, verbose (see every step)
curl -v https://erp.example.com/    # -v prints DNS, TCP, TLS handshake, request + response headers
```
Read the `* ` lines: DNS resolve → `Connected to … port 443` (TCP) → `TLS handshake` + `Server certificate:` (TLS) → `> GET /` (your request) → `< HTTP/2 200` (the response). That's the whole trip in one screen.

```bash
# See the actual network path (the hops)
traceroute erp.example.com          # each line = one router your packets pass through
```

# Production Walkthrough
- A worker's phone on factory wifi → their ISP → the internet → your VPS's public IP → port 443 → **Caddy** → Gunicorn → Django → Postgres, and all the way back.
- **Every hop is a place it can fail**, which is why ch 39's debugging starts by asking *which hop*.
- TLS adds a handshake before any data moves; that is why keep-alive connections matter on mobile networks with high latency.
- The factory's real-world constraint is **latency, not bandwidth** — a phone on patchy wifi feels every extra round-trip, which is the same reason N+1 queries hurt (sql_course ch 16).

# Debugging Guide
"It doesn't load" — isolate the hop:
1. **Is it just this device?** Try another phone/network. Factory wifi is a real suspect.
2. **`ping` / `curl -I` the domain** — no response = DNS or network; response = the app layer.
3. **Does the IP resolve correctly?** `dig +short yourdomain` (ch 04).
4. **Is the port open?** A firewall closing 443 looks identical to "server down" from outside.
5. **Compare from inside the server** (`curl localhost`) — if that works, the problem is between the internet and Caddy, not in the app.

# Performance Notes
- Each new TCP+TLS connection costs multiple round-trips; HTTP keep-alive amortises that.
- Packet loss on wifi causes retransmits, which look like "the app is slow" to a user.
- Compression (Caddy does it) cuts bytes but not round-trips — reducing *requests* helps mobile more than shrinking them.
- Physical distance is a hard floor: a server far from the factory adds latency you cannot optimise away.

# Security Considerations
- Data crosses networks you do not control, which is the entire argument for HTTPS (ch 03).
- Anything on the public internet is scanned within minutes; assume every open port is being probed.
- Never trust the client's IP for authorisation — it is easy to forge and changes constantly on mobile.

# Architecture Decisions
- **One public entry point** (443) and nothing else exposed, so the attack surface is one process you configure carefully.
- **Host near the users** — for a single-factory ERP, a region close to the factory beats a "global" setup nobody needs.
- **HTTP/2 via Caddy** so many small requests on one connection stop being expensive.

# Best Practices
- Learn `curl -I` — it answers "which layer replied?" in one command.
- Keep payloads small for phones; the factory floor is not a fibre connection.
- Test on a real phone on real factory wifi before declaring a page fast.

# Beginner Mistakes
- **Confusing DNS with the server.** Pointing the domain (DNS) at the IP does *not* make the app work — a program must also be *listening* on the port. "DNS resolves but the site is down" = the server/proxy isn't running.
- **Forgetting the port.** `erp.example.com` with nothing listening on 443 = connection refused, even with perfect DNS.
- **Assuming the network is private.** Without TLS, everything (passwords!) is readable on the path. HTTPS is not optional for a login-bearing app.
- **Firewall confusion.** "It works from the server itself (`curl localhost`) but not from outside" almost always = the firewall/cloud security group isn't allowing 80/443 ([Ch 05](05_IP_Address_and_Ports.md)).

# Interview Questions
- **Junior:** "What is DNS?" — The system that translates a human domain name into the numeric IP address of the server, so clients can find it.

- **Mid:** "Walk me through what happens when a user opens `https://erp.example.com`." — DNS resolves the name to the server IP → TCP connection to that IP on port 443 (handshake) → TLS handshake (encrypt + verify certificate) → HTTP request sent inside the encrypted channel → server (Caddy) responds → response travels back over the same connection.

- **Senior:** "The domain resolves correctly but users get connection-refused. Where do you look?" — Something isn't listening on 443, or a firewall blocks it. Check: is the proxy (Caddy) container running and publishing 443 to the host? Is the VPS firewall / cloud security group allowing 80+443? Is DNS pointing at the *current* server IP? `nc -vz <ip> 443` from outside vs `curl localhost` on the box isolates network-vs-app.

- **Staff:** "Why terminate TLS at the edge (Caddy), and what are the trust-boundary implications for the hop to Gunicorn?" — Terminating at the edge centralizes cert management, offloads crypto from app workers, and lets the proxy inspect/limit/route. The Caddy→Gunicorn hop is plaintext but rides the **private Docker network** never exposed to the internet, so the trust boundary is the host + Docker network isolation; if that network were shared with untrusted tenants you'd re-encrypt (mTLS) that hop. For a single-tenant VPS, plaintext on the private net is the standard, accepted design.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Can you narrate one request end to end? | "The browser requests the page and the server sends it." | Name the **five steps in order**: DNS resolves the name → **TCP** handshake to that IP on 443 → **TLS** handshake (encrypt + verify the certificate) → HTTP request **inside** the encrypted channel → response back on the same connection. Interviewers listen for whether TLS comes before or after HTTP. |
| Can you split "network broken" from "app broken"? | "The site is down, so I would restart the server." | **`nc -vz <public-ip> 443` from outside vs `curl localhost` on the box** isolates it in two commands. Refused = nothing listening; timeout = firewall. Restarting first destroys the evidence. |
| Do you know where TLS should terminate? | "TLS should be end to end everywhere." | Terminate at the **edge** (Caddy): centralises cert management, offloads crypto from app workers, and lets the proxy limit and route. The Caddy→Gunicorn hop is plaintext **on the private Docker network** — a deliberate, standard single-tenant trade. |
| Do you know when that trade stops being acceptable? | "Private network means it is secure." | The trust boundary is **the host + Docker network isolation**. On a **shared/untrusted** network you would re-encrypt that hop with **mTLS**. Stating the condition under which your own design fails is the senior move. |

**The killer follow-up:** *"DNS resolves correctly but users get connection-refused. Where do you look?"* — refused means **something is not listening**, not that the network is down: is Caddy running and **publishing** 443 to the host, is the cloud security group open, and is DNS pointing at the **current** IP? Candidates who cannot separate those three will restart containers at random.

# Revision Notes
- Data travels as **packets** with addresses; routers forward them.
- Names → numbers via DNS (ch 04); numbers + ports reach a process (ch 05).
- TCP+TLS handshakes cost round-trips → latency is the mobile enemy.
- Your public entry point is **one port on one IP**: 443 → Caddy.
- Debug by asking **which hop**, not "why is it broken".

# Cheat Sheet
- **Internet = numbered packets** routed hop-to-hop; **TCP** makes a reliable ordered stream; **TLS** encrypts+authenticates it; **HTTP** is the message inside.
- **Find the server:** DNS (name→IP). **Reach the right program:** port (80/443). **Trust the channel:** TLS/cert.
- **The trip:** DNS → TCP:443 → TLS → HTTP request → Caddy → Gunicorn → response back.
- **Inspect:** `dig` (DNS), `nc -vz host 443` (port open?), `curl -v` (whole trip), `traceroute` (hops).
- Deploying = becoming a correct **server**: public IP + DNS name + a program listening on the port.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Public address | VPS public IP (from host provider) |
| Domain name | `.env` → `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` |
| Listener on 443 | Caddy container (only one publishing host ports) |
| Private app port | Gunicorn :8000 on the Docker network (not public) |
| TLS/cert | Caddy automatic (Let's Encrypt) — [Ch 12](12_Caddy.md) |
| Host-header safety | Django `ALLOWED_HOSTS` rejects unknown hosts |

# Practice Tasks
1. **Read the code:** find the ports published in `docker-compose.yml`. Which are public and which are private-network only?
2. **Debug:** run `curl -I https://<your-domain>` (or localhost) and identify from the response alone which component answered.
3. **Design:** a worker says the app is slow on the floor but fine in the office. List the three hops you would measure first.
4. **Architecture:** argue whether a CDN would help this ERP. What does it help, and what does it not?

# Homework
1. Run `curl -v https://<any-site>/` and label, in the output, the DNS step, the TCP connect, the TLS handshake, your request line, and the response status.
2. `dig +short <a-domain>` and `nc -vz <that-domain> 443`. Explain what each proves and what each does NOT prove about "is the site up?"
3. On your laptop, `python -m http.server 9000`, then from your phone open `http://<laptop-ip>:9000/`. You just became a server. Now stop it and try again — connection refused. Explain the difference in terms of "a program listening on a port."
4. Predict: if DNS points `erp.example.com` at my VPS but the Caddy container is stopped, what does a browser show, and why? (Then verify once the VPS exists.)

---

# Further Reading & Live Resources
- MDN — *How does the Internet work?*: https://developer.mozilla.org/en-US/docs/Learn/Common_questions/Web_mechanics/How_does_the_Internet_work
- Cloudflare Learning — *How the Internet works* hub: https://www.cloudflare.com/learning/network-layer/how-does-the-internet-work/
- **Free book** — *High Performance Browser Networking* (Ilya Grigorik; TCP/TLS/HTTP in depth, readable): https://hpbn.co/
- *How DNS Works* (illustrated comic — fun + accurate): https://howdns.works/
- Beej's Guide to Network Programming (packets/TCP/sockets from zero): https://beej.us/guide/bgnet/
- Julia Evans — networking zines (approachable diagrams): https://wizardzines.com/
- Cloudflare — *What is TCP/IP?*: https://www.cloudflare.com/learning/ddos/glossary/tcp-ip/
