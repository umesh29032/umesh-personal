---
id: concept-auth-hardening
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "What actually protects this system's front door — and what real attacks were found and closed?"
related: [feature-rbac-access, project-people-and-roles, concept-testing-strategy]
---

# Auth Hardening — the front door, attacked on purpose

> 📂 [Security concepts](README.md) · [All concepts](../README.md) · [KOS home](../../README.md)

## 1. The project hook

Two REAL findings from this repo's own security certification:
**S2** — public signup was open: anyone on the internet could create a
LIVE user. **S3** — an email-change shadow-route allowed account takeover
by email swap. Both found by attacking the system like an outsider, both
closed, both pinned by tests. This page teaches the front-door defenses
through those scars.

## 2. 💡 Samjho Aise

Ghar ka main gate sirf tala nahi hota. Tala hai (password/OTP), gharwale
pehchano (anti-enumeration — ajnabi ko yeh bhi mat batao ki is naam ka
koi yahan rehta hai), baar-baar ghanti bajane wale ko roko (rate limit),
aur khud ko bahar lock mat kar lo (self-lockout protection). Aur sabse
zaroori: apne hi gate par chor ban ke haath maro — wahi S2/S3 mein hua.

## 3. Mental Model

> Authentication hardening = shrinking three surfaces: **what an attacker
> can TRY** (rate limits on every auth endpoint), **what they can LEARN**
> (uniform responses — no user-exists oracle), and **what a success is
> WORTH** (Argon2 makes stolen hashes expensive; session hygiene makes
> stolen pages stale). Then verify like an attacker, not like a developer.

## 4. Technical Deep Dive

**The stack** (accounts app — consolidated auth family, 37 security tests):

- **OTP-first login** — email + 6-digit code; no password to phish for
  most users. OTPs hashed at rest (`utils.py`), expiring, single-use.
- **Argon2 first** in `PASSWORD_HASHERS` (base.py) — PHC winner,
  OWASP-recommended; old PBKDF2 hashes upgrade transparently at next login
  ([settings §4](../django/settings.md)).
- **Cache-backed rate limiter** (`throttle.py`, no external deps) — every
  auth view rate-checks (`otp_send`, verify, password paths) **per-IP AND
  per-email**: neither one attacker hitting many accounts nor many IPs
  hitting one account slips under a single-key limit. Backed by
  Redis-in-prod ([tech-stack](../../project/tech-stack.md) — ephemeral
  state is EXACTLY what Redis is for; losing it loses nothing but
  counters).
- **Anti-enumeration** — password-reset/OTP endpoints answer UNIFORMLY
  whether the account exists or not; certification specifically probed
  the enumeration class (a real audit finding family: reset flows +
  cacheable auth pages + mixed-case email lockout — all fixed + pinned).
- **Self-lockout protection** — an admin can't rate-limit/lock themselves
  into an unrecoverable state; lockout paths keep a recovery lane.
- **No-cache auth pages** — login/OTP responses carry no-store headers
  (a cached OTP page on a shared factory device is a credential leak).
- **S2 closed** — public allauth signup disabled: users exist only via
  management creation ([people-and-roles](../../project/people-and-roles.md)).
- **S3 closed** — the email-change shadow-route (a second, unhardened path
  to change the login identifier) removed; identifier changes go through
  the guarded flow only.

**The meta-defense:** all 37 tests are REFUSAL pins
([testing-strategy §4](../testing/testing-strategy.md)) — throttle fires,
enumeration answers uniform, lockout recovers, signup 404s. The front
door's spec is executable.

## 5. Engineering Thinking

*Why OTP-primary instead of passwords?* Factory reality: shared devices,
non-technical users, password reuse — the email inbox is already the
recovery root of trust, so make it the login. Trade-off accepted: email
delivery becomes availability-critical for login. *Why per-IP AND
per-email limits?* Each alone has a bypass (botnet vs single-target); the
AND closes both cheaply. *Why did S3 exist at all?* The classic: the main
flow was hardened, a SECONDARY route (email change) touched the same
security property (login identifier) without the same guards. Lesson that
generalizes: **enumerate every path that writes a security-critical field
— the second door is always the one left open** (same instinct as C-TM's
no-second-door law for production truth). *What's deliberately absent:*
2FA hardware, SSO, OAuth-for-workers — no anchor in this factory's needs
yet (Project-Anchor Law applies to security features too).

## 6. How THIS project uses it

The certification method is the reusable asset: attack probes as tests —
CSRF-valid POSTs to forbidden endpoints, dual-identity sweeps, enumeration
oracles measured by response diffing. When the worker-role certification
says "0 global issues," it means those attacks RAN and failed. Copy the
method to any project: list the security properties (who exists, who's
locked, what leaks), write the attack for each, pin the refusal.

## 7. What breaks without it

S2's world: strangers create accounts → the RBAC walls guard a door
standing open. Unthrottled OTP: 6 digits = 10⁶ space, brute-forceable in
hours without limits. Enumeration: a harvested employee list is a phishing
target-pack. Fast hashes: one DB leak = offline cracking farm. Each
defense maps to a boring, well-documented attack.

## 8. Common mistakes (humans)

- Hardening login but not reset/change flows (S3's whole story).
- Different error messages for "no such user" vs "wrong password" — the
  oracle is the message DIFFERENCE.
- Rate limiting by IP only (proxies/NAT: one office = one IP — you lock
  out the factory, not the attacker).
- Treating lockout as pure security — without a recovery lane it's a
  self-DoS feature.

## 9. AI Implementation Pitfalls

- ❌ Adding any new route that creates users or changes email/identifier
  without the full guard set — the S2/S3 classes reborn.
- ❌ "Helpful" specific error messages on auth failures — uniformity IS
  the defense.
- ❌ Moving throttle counters to the database — ephemeral belongs in
  cache; a DB row per attempt is a write-amplification attack surface.
- ❌ Loosening a throttle to fix a support complaint — tune with the
  self-lockout lane, never by widening the attacker's budget.
- ✅ Always verify: new auth-adjacent route ⇒ throttle + uniform errors +
  no-cache + a refusal pin, and the 37-test suite stays green.

## 10. DSA & Complexity

Rate limiting here = counter-with-TTL in cache — the simplest of the
limiter family (vs token bucket/sliding window). Know the ladder for
interviews: fixed window (this repo's shape — burst at boundary, fine for
auth) → sliding window (smooth, more state) → token bucket (rate+burst
control). Auth needs the SIMPLE one: the goal is making 10⁶ OTP guesses
infeasible, not traffic shaping.

## 11. Interview corner

*Interview Signal: 🟡 Mid — auth hardening basics are mid; the S3 second-door story reads senior.*

**Q. "Harden a login system."**
- *Short:* Strong slow hash (Argon2), rate limit per-IP AND per-identifier, uniform responses (no enumeration), no-cache auth pages, single-use expiring tokens, and — most missed — the SAME guards on every secondary path that touches identity.
- *Senior:* Model it as three surfaces (try/learn/worth) and enumerate ALL writers of security-critical fields — takeovers come through the forgotten second door (email change, invite flows, admin resets). Then make the spec executable: every defense gets an attack-shaped test. Security that isn't pinned regresses like performance does.
- *Project example:* S2 (open signup) and S3 (email shadow-route) — found by self-attack, closed, pinned; per-IP+email throttle; OTP-primary with hashed single-use codes; 37 refusal pins.
- *Follow-ups:* "Why Argon2 over bcrypt?" (memory-hardness vs GPU farms; PHC winner) · "Rate limit storage?" (cache with TTL — ephemeral by nature) · "How do you FIND an S3-class bug?" (grep every write-site of the identifier field — the single-writer census instinct, applied to security).

## 12. 🧠 Remember This

Teen surface chhote karo: koshish (throttle), jaankari (uniform jawab),
inaam (Argon2). Har woh raasta gino jo pehchaan badal sakta hai — chori
hamesha DOOSRE darwaze se hoti hai (S3). Aur suraksha ka spec test mein
jinda rehta hai — 37 keelein thoki hui hain.

## 13. 30-Second Revision

- OTP-primary (hashed, expiring, single-use) · Argon2 first = transparent upgrades
- Throttle: cache-backed, per-IP AND per-email, every auth view · self-lockout lane kept
- Anti-enumeration: uniform responses · no-cache auth pages · mixed-case email lesson
- S2: public signup CLOSED · S3: identifier shadow-route CLOSED — both pinned
- Law: every writer of a security-critical field gets the SAME guards

## 14. What You Should Now Understand

The three-surface model, why secondary paths are where takeovers live, how
this repo's throttle/enumeration/hashing choices map to named attacks, and
the attack-as-test method. Shaky? Read `config/accounts/README.md` — the
door's own manual.

**Recommended next topic:** back to
[testing-strategy](../testing/testing-strategy.md) if you skipped it —
security here is just refusal-pinning with an adversary's eyes.

## Implementation References

- Findings: S2/S3 in [docs/WORKER_ROLE_CERTIFICATION.md](../../../docs/WORKER_ROLE_CERTIFICATION.md) · hardening baseline: accounts security audit (Phase 02, production audit)

## Code References
- Canonical: `config/accounts/README.md` (flows, throttle, 37-test census) · code: `config/accounts/` (`throttle.py`, `utils.py`, views)
- Settings side: Argon2 block in `config/config/settings/base.py`

## Further Reading

- Official: [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html) · [Django — password management](https://docs.djangoproject.com/en/5.0/topics/auth/passwords/)

## Related

[rbac-access](../../features/rbac-access.md) · [people-and-roles](../../project/people-and-roles.md) ·
[testing-strategy](../testing/testing-strategy.md) · [settings](../django/settings.md)
