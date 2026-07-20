# 04 — DNS & Domains

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Prev: [03 — HTTP & HTTPS](03_HTTP_HTTPS.md). Next: [05 — IP Addresses & Ports](05_IP_Address_and_Ports.md).

# Purpose
To understand how a human name like `erp.kapil.com` becomes the numeric address of my VPS, so that when I "point my domain at my server," I know *exactly* what I'm configuring, why it sometimes takes time to work, and how to debug "the domain doesn't resolve."

# The Problem
My VPS has an IP address like `203.0.113.10`. Nobody will type that, and if I ever move servers the IP changes. I need a stable human name that (a) everyone can remember and (b) I can re-point to a new IP without telling anyone. That indirection is **DNS**. Deploying means creating the right DNS records so the world can find my server by name — and TLS ([Ch 03](03_HTTP_HTTPS.md)) literally won't issue a certificate until DNS points at me.

# Theory (from zero)

### A domain is rented, hierarchical, and delegated
`erp.kapil.com` reads **right to left**:
- `.com` = the **top-level domain (TLD)**, run by a registry.
- `kapil.com` = the **domain** I rent from a **registrar** (GoDaddy, Namecheap, Cloudflare…). Renting gives me control of everything under it.
- `erp` = a **subdomain** I create freely (also `www`, `api`, `staging`…).

### DNS = the distributed phonebook
**DNS (Domain Name System)** maps names → IPs. It's a huge, cached, hierarchical lookup:
1. Your phone asks a **resolver** (usually your ISP's or `8.8.8.8`).
2. The resolver, if it doesn't have the answer cached, walks the hierarchy: root servers → `.com` servers → the **nameservers** for `kapil.com` (the ones your registrar points to).
3. Those authoritative nameservers hold your **records** and return the IP.
4. The answer is **cached** at each layer for a **TTL** (time-to-live, in seconds), so the next lookup is instant.

### The record types you actually use
- **A record** — name → IPv4 address. `erp.kapil.com → 203.0.113.10`. *This is the one you set to point your ERP at your VPS.*
- **AAAA record** — name → IPv6 address (same idea, newer address format).
- **CNAME** — name → *another name* (alias). `www.kapil.com → erp.kapil.com`. Can't be used on the bare/root domain in classic DNS.
- **MX** — mail servers (email, not web).
- **TXT** — arbitrary text; used for domain-ownership proofs and email security (SPF/DKIM). Some TLS/ACME challenges use TXT (DNS-01).
- **NS** — which nameservers are authoritative for the zone.

### TTL + propagation (why changes aren't instant)
Each record has a **TTL** (e.g. 300s = 5 min, 3600s = 1 hour). When you change a record, machines that cached the old value keep using it until their TTL expires. This lag is **"DNS propagation."** Practical rule: **lower the TTL (e.g. to 300s) a day *before* a planned IP change**, so the switch is fast; raise it back after.

### How this connects to TLS
Let's Encrypt (via Caddy, [Ch 12](12_Caddy.md)) must verify you control the domain before issuing a cert. The common **HTTP-01 challenge**: the CA connects to `http://erp.kapil.com/.well-known/acme-challenge/…` and expects Caddy to answer. That only works if the **A record already points at your VPS** and **port 80 is open**. So the order is: DNS first → then TLS works.

# Real World Example (My ERP)
- I rent `kapil.com` (example) at a registrar and set its **nameservers**.
- I create an **A record**: `erp.kapil.com → <my VPS public IP>`. (Optionally `www.kapil.com` as a CNAME to `erp.kapil.com`.)
- I put that exact host in my `.env`: `ALLOWED_HOSTS=erp.kapil.com` and `CSRF_TRUSTED_ORIGINS=https://erp.kapil.com`. Django then accepts requests whose `Host:` header is `erp.kapil.com` and trusts POSTs from that origin ([Ch 03](03_HTTP_HTTPS.md)).
- I tell **Caddy** the site name is `erp.kapil.com` (in `deploy/Caddyfile`); Caddy sees the A record, passes the ACME HTTP-01 challenge on port 80, and issues + renews the certificate automatically.
- If the owner later moves to a new VPS, I just change the A record's IP — the name, the Caddyfile, and `.env` stay the same. That's the whole point of the indirection.

# Visual Diagram
```
 you set (once, at registrar):   erp.kapil.com   A   203.0.113.10   TTL 300

 A worker's phone resolving the name:
   phone → resolver(8.8.8.8) → root(.) → .com registry → kapil.com nameservers
                                                                │
                                                   "erp.kapil.com = 203.0.113.10"
   phone ◄──────────────── cached for TTL seconds ─────────────┘
   phone → TCP 203.0.113.10:443  (now it can actually connect — Ch 02/05)

 Change server IP later:  edit ONE A record → 203.0.113.99
   name, Caddyfile, .env all unchanged.   (old value lingers only until TTL expires)
```

# Practical — how to inspect it
```bash
# What IP does the name resolve to? (the core check)
dig +short erp.kapil.com A          # prints the A-record IP(s)
dig erp.kapil.com                   # full answer: ANSWER SECTION + TTL remaining
```
`dig` asks DNS directly. The `TTL` column in the full output counts *down* — that's the cache clock.

```bash
# Which nameservers are authoritative? (did my registrar delegation take effect?)
dig +short NS kapil.com
```

```bash
# Ask a SPECIFIC resolver (bypass local cache; check "has it propagated?")
dig @8.8.8.8 +short erp.kapil.com   # ask Google's resolver
dig @1.1.1.1 +short erp.kapil.com   # ask Cloudflare's
```
If different resolvers return different IPs, your change is still propagating.

```bash
# The OS resolver's view (what your apps will actually use)
getent hosts erp.kapil.com
```

```bash
# Full reverse: does that IP host what I think? (sanity, not authoritative)
dig -x 203.0.113.10                 # reverse lookup (PTR) — often the host provider's name
```

# Beginner Mistakes
- **"DNS is set, so the site should work."** No — DNS only makes the *name resolve to an IP*. A server must still be *listening* ([Ch 05](05_IP_Address_and_Ports.md)) and the app running. "Resolves but refused/timeout" = server/proxy problem, not DNS.
- **Impatience during propagation.** You change a record and it "doesn't work" for you because your resolver cached the old value. Check with `dig @8.8.8.8`; wait for TTL.
- **High TTL right before a migration.** If TTL is 86400 (1 day), your IP change takes up to a day to fully take. Lower TTL *ahead* of planned changes.
- **CNAME on the root domain.** `kapil.com` (bare) usually can't be a CNAME; use an A record (or the registrar's "ALIAS/ANAME" feature).
- **Requesting TLS before DNS points at you.** Let's Encrypt HTTP-01 fails → Caddy can't get a cert → HTTPS errors. DNS first, then TLS.
- **`ALLOWED_HOSTS` mismatch.** DNS says `erp.kapil.com` but `.env` lists `kapil.com` → Django `400 Bad Request` on every hit. They must match the host users actually type.

# Interview Questions
**Junior — "What is DNS and what's an A record?"** DNS translates domain names to IP addresses. An A record maps a name to an IPv4 address — the record you set to point a domain at a server.

**Mid — "You changed the A record but the site still hits the old server. Why?"** Caching: resolvers and clients hold the old value until the record's TTL expires (propagation). Verify with `dig @8.8.8.8`; the fix is time, and pre-lowering TTL before planned changes.

**Mid — "Difference between an A record and a CNAME?"** A points a name at an IP; CNAME points a name at *another name* (alias) which is then resolved. CNAME can't sit on the root domain in classic DNS.

**Senior — "New domain, TLS won't issue. Walk your checks."** Confirm the A record points at *this* server (`dig @8.8.8.8 +short`), that nameserver delegation is correct (`dig NS`), that ports 80+443 are open to the internet (ACME HTTP-01 uses 80), and that Caddy's site name exactly matches the DNS name. Order matters: DNS + open 80 → then cert issues.

**Staff — "Design DNS for zero-downtime server migration of this ERP."** Ahead of time, drop the A-record TTL to ~60–300s. Stand up the new VPS, deploy, restore the DB, verify with a hosts-file override or a temporary subdomain. Then flip the A record to the new IP; within one TTL window traffic drains to the new box while the old one still serves stragglers. Keep the old box up one extra TTL, confirm zero traffic, then decommission. Raise TTL back. (For truly seamless, put both behind a load balancer and shift there instead — [Ch 41](41_Scaling.md).)

# Cheat Sheet
- **Domain** rented from a registrar; **subdomain** (`erp.`) you make freely.
- **A record** = name→IPv4 (the one you set for the VPS). **CNAME** = name→name. **TTL** = cache seconds (lower before changes).
- **DNS only resolves a name to an IP** — it does not make the server run or listen.
- **Order:** set A record + open port 80 → *then* TLS issues.
- **Inspect:** `dig +short name A`, `dig @8.8.8.8 name` (bypass cache), `dig NS domain`.
- `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` must equal the DNS name users type.

# My ERP Section
| Concept | In my ERP |
|---|---|
| The name | `erp.<mydomain>` (A record → VPS IP) |
| Where the name lives in config | `.env` → `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` |
| Who uses the name for TLS | Caddy site block in `deploy/Caddyfile` |
| Move servers | change ONE A record; Caddyfile + `.env` unchanged |
| TLS dependency | A record + open :80 must exist before Caddy gets a cert |

# Homework
1. `dig +short google.com A` then `dig google.com` — find the TTL and watch it count down on repeat calls.
2. `dig @8.8.8.8 +short <your-domain>` vs `dig @1.1.1.1 +short <your-domain>` — same answer? (If you don't own one, try any site.)
3. `dig +short NS <a-domain>` — who are its authoritative nameservers?
4. Write the exact A record you will create for your ERP: `______  A  ______  TTL ____`. Then write the matching `.env` `ALLOWED_HOSTS` line. Confirm they're identical hostnames.
5. Explain in one sentence why Caddy can't get an HTTPS certificate until *after* the A record is live.

---

## Further Reading & Live Resources
- Cloudflare Learning — *What is DNS?* (best plain-English intro): https://www.cloudflare.com/learning/dns/what-is-dns/
- Cloudflare Learning — *DNS record types* (A / AAAA / CNAME / MX / TXT): https://www.cloudflare.com/learning/dns/dns-records/
- *How DNS Works* (illustrated): https://howdns.works/
- MDN — *What is a domain name?*: https://developer.mozilla.org/en-US/docs/Learn/Common_questions/Web_mechanics/What_is_a_domain_name
- **Live tool** — DNS Checker (see propagation across the globe): https://dnschecker.org/
- **Live tool** — Google Admin Toolbox Dig (browser `dig`): https://toolbox.googleapps.com/apps/dig/
- Let's Encrypt — *Challenge Types* (HTTP-01 vs DNS-01, ties to [Ch 12](12_Caddy.md)): https://letsencrypt.org/docs/challenge-types/
