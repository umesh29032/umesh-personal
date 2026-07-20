# 03 — HTTP & HTTPS

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Prev: [02 — How The Internet Works](02_How_The_Internet_Works.md). Next: [04 — DNS & Domains](04_DNS_Domains.md).

# Purpose
[Ch 02](02_How_The_Internet_Works.md) got the encrypted pipe open between phone and VPS. This chapter is about the *language* spoken inside that pipe — **HTTP** — and the encryption layer that makes it **HTTPS**. Once I can read a raw request and response, "the server returned a 500", "CSRF failed", "mixed content", and "cert expired" stop being scary and become obvious.

# The Problem
My Django app produces pages, but a page is not what travels over the wire — a precisely-formatted **HTTP message** is. If I don't know the anatomy (method, path, headers, status, body), I can't reason about why a request was rejected, why a cookie didn't stick, why the browser blocked something, or why a login must be over HTTPS. And HTTP by itself is plaintext — anyone on the path reads the worker's password. HTTPS fixes that; I must understand *how* so I configure it correctly.

# Theory (from zero)

### What HTTP is
**HTTP (HyperText Transfer Protocol)** is a simple text-based request/response protocol. The client sends a **request**; the server sends back one **response**. Stateless by default — each request stands alone (state is re-established with cookies, below).

**A request** has four parts:
```
GET /production/my-work/ HTTP/1.1        ← method + path + version   (the "request line")
Host: erp.example.com                    ← headers (key: value)
Cookie: sessionid=abc123
Accept: text/html
                                         ← blank line = end of headers
(body — empty for GET; form data for POST)
```
- **Method** = the verb: `GET` (read, no side effects), `POST` (create/submit), `PUT/PATCH` (update), `DELETE` (remove). Your worker submitting a report is a `POST`; opening the dashboard is a `GET`.
- **Path** = which resource (`/production/my-work/`).
- **Headers** = metadata: `Host` (which site — Django checks this against `ALLOWED_HOSTS`), `Cookie` (carries the session), `Content-Type`, `Accept`, etc.
- **Body** = the payload (form fields on a POST).

**A response**:
```
HTTP/1.1 200 OK                          ← status line: version + code + reason
Content-Type: text/html; charset=utf-8   ← headers
Set-Cookie: sessionid=abc123; HttpOnly; Secure; SameSite=Lax
                                         ← blank line
<html>… the page …</html>               ← body
```

### Status codes (memorize the families)
- **2xx success** — `200 OK`, `201 Created`, `204 No Content`.
- **3xx redirect** — `301/302 Found` ("go here instead"; your unauthorized worker gets redirected), `304 Not Modified` (cached).
- **4xx client error** — `400 Bad Request`, `401 Unauthorized` (not logged in), `403 Forbidden` (logged in, not allowed — your worker hitting a management page), `404 Not Found`, `405 Method Not Allowed` (GET on a POST-only endpoint — your barcode export does this).
- **5xx server error** — `500 Internal Server Error` (your code raised an exception), `502 Bad Gateway` (proxy can't reach the app — Caddy up, Gunicorn down), `503 Service Unavailable`, `504 Gateway Timeout` (app too slow).

`502` vs `500` is a key production distinction: **500 = your Django code threw**; **502 = Caddy couldn't talk to Gunicorn** (Gunicorn crashed/not started). Different fix entirely.

### Cookies + why login needs them
HTTP is stateless, so after you log in, the server sends `Set-Cookie: sessionid=…`. The browser stores it and sends `Cookie: sessionid=…` on every later request; that's how the server knows "this is the same logged-in worker." Cookie flags matter for security:
- `HttpOnly` — JavaScript can't read it (blunts XSS stealing the session).
- `Secure` — only sent over HTTPS (never leaks over plain HTTP).
- `SameSite=Lax` — not sent on cross-site requests (blunts CSRF).
Your `base.py` sets `SESSION_COOKIE_HTTPONLY` and `SAMESITE=Lax`; `production.py` adds `SESSION_COOKIE_SECURE=True` + `CSRF_COOKIE_SECURE=True`.

### CSRF, briefly
Because the browser auto-sends cookies, a malicious site could trick your logged-in browser into POSTing to your ERP. Django's **CSRF protection** requires a secret token on every POST that only your own pages embed. That's why forms have `{% csrf_token %}` and why `CSRF_TRUSTED_ORIGINS` must list your domain in production.

### HTTPS = HTTP + TLS
Plain HTTP is readable by anyone on the network path. **TLS** wraps it so the connection is:
1. **Encrypted** — eavesdroppers see gibberish.
2. **Authenticated** — the client verifies the server really is `erp.example.com` via a **certificate**.
3. **Integrity-checked** — tampering is detected.

**A certificate** is a file, signed by a trusted **Certificate Authority (CA)**, that says "the holder of this private key owns `erp.example.com`." The browser trusts a built-in list of CAs. **Let's Encrypt** is a free, automated CA. The server proves it controls the domain (an ACME challenge), the CA issues a cert valid ~90 days, and it must be **renewed** before expiry. **Caddy does all of this automatically** — request, install, and renew — which is the single biggest reason this project uses Caddy ([Ch 12](12_Caddy.md)).

# Real World Example (My ERP)
- Worker submitting a report = a `POST` to `/production/addas/<code>/report/<stage>/` with `{% csrf_token %}` + the quantity fields in the body. My server validates the CSRF token, then the allocation bound.
- Worker hitting a management page they lack = `403` (a clean "Access denied" page, not a crash — RC1 verified).
- `GET` on the barcode export URL = `405` (it's POST-only) — correct, not a bug.
- If Django raises = `500`; if Gunicorn is down while Caddy is up = `502`.
- HTTPS + the redirect: `production.py` sets `SECURE_SSL_REDIRECT=True` (any HTTP request → 301 to HTTPS), `SECURE_HSTS_SECONDS=31536000` (tell browsers "always HTTPS for a year"), and `SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')` so Django trusts Caddy's "this was HTTPS" header (without it, the redirect would loop forever behind the proxy).
- Cookie security: `SESSION_COOKIE_SECURE` + `CSRF_COOKIE_SECURE` = `True` in production → the session + CSRF cookies never travel over plain HTTP.

# Visual Diagram
```
        CLIENT (browser)                           SERVER (Caddy → Django)
            │  ── TLS handshake: "prove you're erp.example.com" ──►
            │  ◄── certificate (signed by Let's Encrypt CA) ───────
            │  (browser checks CA trust + domain match → channel now encrypted)
            │
   REQUEST  │  POST /…/report/overlock/ HTTP/1.1
            │  Host: erp.example.com
            │  Cookie: sessionid=abc; csrftoken=xyz
            │  Content-Type: application/x-www-form-urlencoded
            │  (body) line-0-reported_quantity=50&csrfmiddlewaretoken=xyz
            │  ─────────────────────────────────────────────►
            │                                          Django: check Host∈ALLOWED_HOSTS,
            │                                          check CSRF token, run view
   RESPONSE │  ◄─────────────────────────────────────────────
            │  HTTP/1.1 302 Found        (redirect back to my-work after submit)
            │  Set-Cookie: sessionid=…; HttpOnly; Secure; SameSite=Lax
            │  Location: /production/my-work/

  status families:  2xx ok · 3xx redirect · 4xx you-messed-up · 5xx server-messed-up
  500 = Django threw   |   502 = Caddy can't reach Gunicorn
```

# Practical — how to inspect it
```bash
# See full request + response headers of a real page (follow redirects with -L)
curl -sSIL https://erp.example.com/            # -I = headers only, -L = follow redirects, -sS = quiet but show errors
```
Read the chain: a plain `http://` hit shows `301` → `Location: https://…` (that's `SECURE_SSL_REDIRECT`), then `200`.

```bash
# Prove HTTP→HTTPS redirect works
curl -sSI http://erp.example.com/              # expect: HTTP/1.1 301 + Location: https://…
```

```bash
# Inspect the TLS certificate (who issued it, when it expires)
echo | openssl s_client -connect erp.example.com:443 -servername erp.example.com 2>/dev/null \
  | openssl x509 -noout -issuer -subject -dates
#   issuer=Let's Encrypt … / subject=CN=erp.example.com / notAfter=… (expiry)
```

```bash
# Send a POST and see the status (e.g. a login) — verbose shows request+response
curl -v -X POST https://erp.example.com/accounts/login/ -d "login=x&password=y"
```

```bash
# In the browser: DevTools → Network tab. Click any request → see Method, Status,
# Request/Response Headers, Cookies, and the body. This is your #1 debugging view.
```

# Beginner Mistakes
- **Confusing 500 and 502.** 500 = fix your code/logs; 502 = your app process is down/unreachable. Chasing the wrong one wastes hours.
- **Serving login over HTTP.** Passwords in clear text. Always redirect to HTTPS (you do).
- **`Secure` cookie on an HTTP site.** The cookie is set with `Secure` but the page is HTTP → browser never sends it → "why am I logged out every request?" (Fixed by actually being on HTTPS.)
- **Mixed content.** An HTTPS page loading an `http://` script/image → browser blocks it. Keep all asset URLs relative or HTTPS.
- **Ignoring `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`.** Wrong/missing values → `400 Bad Request` (bad Host) or CSRF `403` on every POST in production.
- **Forgetting `SECURE_PROXY_SSL_HEADER` behind a proxy.** Django thinks requests are HTTP (Caddy terminated TLS) → infinite redirect loop.

# Interview Questions
**Junior — "What's the difference between GET and POST?"** GET reads a resource with no side effects and is safe to repeat/cache; POST submits data that changes server state (create/submit) and shouldn't be blindly repeated.

**Junior — "What does a 404 vs 403 vs 500 mean?"** 404 = resource not found; 403 = authenticated but not permitted; 500 = the server crashed handling the request.

**Mid — "How does a stateless protocol keep a user logged in?"** After login the server issues a session cookie (`Set-Cookie`); the browser returns it on every request (`Cookie`), letting the server re-identify the session. Security flags: HttpOnly, Secure, SameSite.

**Mid — "What is a TLS certificate and who issues it?"** A CA-signed file binding a public key to a domain, proving server identity so the client can trust the encrypted channel. Let's Encrypt issues them free/automatically; ~90-day validity requiring renewal (Caddy automates it).

**Senior — "Users report being logged out on every click in production. Diagnose."** Almost certainly the session cookie is `Secure` but the site is being served/hit over HTTP (or the proxy TLS header isn't trusted so Django/redirect logic misbehaves). Check the scheme actually reaching the browser, `SESSION_COOKIE_SECURE`, `SECURE_PROXY_SSL_HEADER`, and the redirect chain.

**Staff — "Design the TLS story for this ERP end to end, including renewal failure."** Caddy terminates TLS at the edge with Let's Encrypt certs, auto-renewing well before the 90-day expiry; HSTS (1yr, preload) forces HTTPS on clients; `SECURE_PROXY_SSL_HEADER` lets Django trust the edge; the Caddy→Gunicorn hop is plaintext on the private Docker net. Renewal-failure mode: Caddy retries automatically; monitor cert expiry (an alert at T-14 days) and ensure ports 80/443 stay open (the ACME HTTP-01 challenge needs 80). If renewal ever fails past expiry, browsers hard-fail — hence monitoring + keeping 80 open are non-negotiable.

# Cheat Sheet
- **HTTP = request (method+path+headers+body) → response (status+headers+body).**
- **Status:** 2xx ok · 3xx redirect · 4xx client wrong (401 no-auth, 403 forbidden, 404 missing, 405 wrong-method) · 5xx server wrong (**500 code threw**, **502 app unreachable**, 504 too slow).
- **State via cookies:** `Set-Cookie`/`Cookie`; flags `HttpOnly`, `Secure`, `SameSite`.
- **HTTPS = HTTP + TLS** (encrypt + authenticate via CA cert). **Let's Encrypt + Caddy = free, auto, auto-renew.**
- **Inspect:** `curl -sSIL <url>`, `openssl x509` for cert dates, browser DevTools → Network.
- Behind a proxy: set `SECURE_PROXY_SSL_HEADER` or die in a redirect loop.

# My ERP Section
| Concept | In my ERP |
|---|---|
| POST with CSRF | worker report / allocation forms (`{% csrf_token %}`) |
| 403 page | worker → management URL (clean deny) |
| 405 | GET on barcode export (POST-only) |
| HTTP→HTTPS | `SECURE_SSL_REDIRECT=True` (`production.py`) |
| HSTS | `SECURE_HSTS_SECONDS=31536000` + preload |
| Trust proxy TLS | `SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')` |
| Secure cookies | `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` = True |
| Host safety | `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` (from `.env`) |
| Cert issuance | Caddy + Let's Encrypt (automatic) |

# Homework
1. `curl -sSIL http://<a-site>/` — find the `301` and the `Location`. That's a redirect in the wild.
2. Inspect a real cert with the `openssl` command above; note issuer + `notAfter`. How many days left?
3. In browser DevTools → Network, log in somewhere and watch the `Set-Cookie` on the login response and the `Cookie` on the next request. Find the `HttpOnly`/`Secure`/`SameSite` flags.
4. In your ERP, submit a worker report and, in the Network tab, confirm it's a `POST` carrying `csrfmiddlewaretoken`, and note the response status (likely a `302` redirect).
5. Explain, in one sentence each, when you'd see `500` vs `502` in your ERP and what you'd check for each.

---

## Further Reading & Live Resources
- MDN — *An overview of HTTP* (the canonical, readable reference): https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview
- MDN — *HTTP response status codes* (all of them, explained): https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
- MDN — *Using HTTP cookies* (HttpOnly/Secure/SameSite): https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies
- Django docs — *Cross Site Request Forgery protection*: https://docs.djangoproject.com/en/5.0/ref/csrf/
- Django docs — *Security in Django* (XSS/CSRF/clickjacking/SSL): https://docs.djangoproject.com/en/5.0/topics/security/
- Let's Encrypt — *How it works* (ACME, challenges, renewal): https://letsencrypt.org/how-it-works/
- **Live tool** — SSL Labs server test (grade your HTTPS): https://www.ssllabs.com/ssltest/
- **Live tool** — securityheaders.com (grade your response headers): https://securityheaders.com/
- Cloudflare Learning — *What is HTTPS / TLS?*: https://www.cloudflare.com/learning/ssl/what-is-https/
