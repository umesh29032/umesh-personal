---
id: concept-django-settings
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "How does this repo guarantee production can never accidentally run with dev secrets, dev DB, or missing config?"
related: [project-tech-stack, concept-django-migrations, concept-service-layer]
---

# Settings — fail at boot, never at midnight

> 📂 [Django concepts](README.md) · [All concepts](../README.md) · [KOS home](../../README.md)

## 1. The project hook

`config/config/settings/production.py`, line 60:

```python
SECRET_KEY = config('SECRET_KEY')   # config() bina default ke — agar .env
                                    # mein nahi hai toh crash karo
```

No default. Missing `.env` value = the process REFUSES TO START. That one
missing argument is the repo's entire config philosophy: **a service that
can't be configured correctly must not run at all** — because a Django app
limping on a default SECRET_KEY isn't degraded, it's compromised.

## 2. 💡 Samjho Aise

Hawai-jahaaz ka pre-flight check. Fuel gauge kaam nahi kar raha? Jahaaz
UDTA HI NAHI — aisa nahi ki "chalo, andaaze se dekh lenge." Config bhi
wahi hai: DB kahan hai, secret kya hai, Redis kahan — yeh sab udaan se
PEHLE pakka hona chahiye. Runway par rukna sasta hai; hawa mein pata
chalna haadsa hai.

## 3. Mental Model

> Configuration has exactly two respectable states: **explicitly provided,
> or fatal at boot.** The third state — silently defaulted — is where
> production incidents incubate. Corollary: defaults are fine for things
> that only make dev CONVENIENT (`DB_USER='postgres'` locally); defaults
> are forbidden for anything that makes production SAFE (secrets, hosts,
> origins).

## 4. Technical Deep Dive

**The three-tier split** (`config/config/settings/`):

| File | Role | Default policy |
|---|---|---|
| `base.py` | everything shared: apps, middleware, Argon2 hashers, templates, DB via `config()` | dev-convenient defaults OK (`DB_PASSWORD` default `postgres`) |
| `local.py` | dev: DEBUG, LocMem cache, runserver niceties | permissive |
| `production.py` | the strict overlay: `SECRET_KEY`/`REDIS_URL`/`CSRF_TRUSTED_ORIGINS` — **no defaults** | fail-fast |

Values flow through `python-decouple`'s `config()`: code reads NAMES,
`.env` holds VALUES, the repo holds NEITHER secret nor environment noise.
Type discipline at the edge: `config('X', cast=bool/int)` — strings from
env become typed exactly once, at the boundary (same PA-07-2 instinct as
`Decimal(str(x))` in services: parse at the edge, trust inside).

**The settings-module double wall** (deploy hardening, DEP-F1 register):
production containers BAKE `DJANGO_SETTINGS_MODULE=config.settings.production`
into the image — being in the production container IS being on production
settings; no operator memory involved. The wsgi default is the registered
second half of that wall.

**Two real safety behaviors worth copying:**
- `CSRF_TRUSTED_ORIGINS = [o.strip() for o in config(...).split(',') if o.strip()]`
  — parse, trim, drop empties: env-string hygiene at the edge, so a
  trailing comma in `.env` can't produce a phantom origin.
- Argon2 listed FIRST in `PASSWORD_HASHERS` (base.py): new passwords get
  the strongest hash; old PBKDF2 hashes upgrade transparently at next
  login — a config ORDERING carrying a security migration.

**What is deliberately NOT in settings:** business behavior. The
enforcement levers (`ENFORCE_ALLOCATION_BOUND`,
`LEDGER_CREDIT_AT_ALLOCATION`) read env because they're OPERATIONAL
switches (deploy→soak→enable), documented in runbooks with default-OFF —
not because settings is a junk drawer. Rule of thumb: settings hold
*where/how to run*, services hold *what is true*.

## 5. Engineering Thinking

*Why three files instead of one file + env branching?* `if PROD:` branches
interleave two worlds in one namespace — you audit production by reading
dev code. Separate overlays make `production.py` a complete, short,
reviewable statement of what production IS. *Why decouple over
os.environ?* Casting + required-vs-default semantics in one call — the
fail-fast is a LIBRARY feature, not a convention. *Why bake the settings
module into the image?* Because every "wrong settings in prod" postmortem
is an operator-memory failure; images don't forget. *The assumption:*
`.env` itself is protected — which is why backups/DR treat `.env` recovery
as a first-class drill item (the ops handbook's restore story), and why
`.env` never enters git.

## 6. How THIS project uses it

Boot-time verification goes beyond Django: the deploy runbook's
`verify_production` gate checks the running config's shape after every
deploy (settings module, DB reachability, cache) — fail-fast extended from
import-time to deploy-time. Result: the entire class of "worked locally,
half-configured in prod" reduces to a red line in the deploy output,
BEFORE traffic. The certification honestly registered the residual
(DEP-F1 wsgi default) instead of hand-waving it — open items are data.

## 7. What breaks without it

The classics, all pre-empted: DEBUG=True leaking stack traces (strict
overlay), dev SECRET_KEY signing production sessions (no-default crash),
`ALLOWED_HOSTS=['*']` "temporarily" (explicit origins with hygiene),
running prod code on dev settings because a shell forgot an env var
(baked module). Every one is a famous postmortem somewhere else.

## 8. Common mistakes (humans)

- Adding a "safe" default to unblock a deploy — you just moved the failure
  from loud-at-boot to silent-at-runtime.
- Secrets in `base.py` "just for now" — git history is forever.
- Env parsing scattered through the codebase — types at the edge ONCE;
  everything downstream trusts.
- Testing against local settings and assuming production parity — the
  overlay is short; READ it before every deploy-affecting change.

## 9. AI Implementation Pitfalls

- ❌ `config('SECRET_KEY', default='...')` — the default IS the vulnerability.
- ❌ Reading `os.environ` directly in app code — all config through the
  settings layer; services never parse env.
- ❌ Adding business rules as settings ("SETTLEMENT_MAX=...") — behavior
  lives in services/DB; settings hold operational wiring.
- ❌ New required setting without updating `.env.example` + the deploy
  runbook — a fail-fast nobody can satisfy is an outage with good intentions.
- ✅ Always verify: fresh clone + documented `.env` boots; missing each new
  required var fails LOUDLY with a readable name.

## 10. DSA & Complexity

Not algorithmic — but note the structure: base + overlays is **prototype
inheritance** for config (child shadows parent), and fail-fast is
**precondition checking hoisted to load time** — the cheapest possible
place to fail, same reasoning as constraints-at-write vs
reconciliation-at-read.

## 11. Interview corner

*Interview Signal: 🟡 Mid — config discipline signals production experience.*

**Q. "How do you manage configuration across dev and production?"**
- *Short:* Settings overlays (base/local/production), values via env with typed parsing at the edge, NO defaults for anything safety-relevant — missing config kills boot.
- *Senior:* Classify every setting: convenience (default OK) vs safety (fail-fast) vs business behavior (doesn't belong in settings). Make production's identity structural (baked settings module) rather than procedural (operator remembers a flag). Extend fail-fast past import: a post-deploy verification gate that checks the LIVE config shape.
- *Project example:* the no-default SECRET_KEY line with its Hinglish why-comment; baked DJANGO_SETTINGS_MODULE; CSRF origins hygiene; Argon2-first as config-driven hash migration; verify_production as the deploy-time extension.
- *Follow-ups:* "Where do feature flags live?" (env-backed operational levers, default-OFF, runbook-documented — distinct from business rules) · "Secrets rotation?" (env only, never git — rotation = .env change + restart) · "Why not a config service?" (one VPS; the boring answer wins until scale asks otherwise).

## 12. 🧠 Remember This

Config ki do hi izzat-wali haalat: DI HUI, ya BOOT PAR MAUT. Chupchaap
default = aadhi raat ka incident kal ke liye. base = saajha, local =
aaraam, production = chhota-sakht-poora. Types darwaze par, secrets sirf
.env mein, aur production hona IMAGE mein baked — yaaddasht mein nahi.

## 13. 30-Second Revision

- 3 tiers: base (shared) · local (loose) · production (strict, NO defaults)
- `config('X')` no-default = boot crash; casts at the edge; .env never in git
- Baked DJANGO_SETTINGS_MODULE = structural prod identity (DEP-F1 = registered residual)
- CSRF origins: split/strip/filter — env hygiene
- Argon2 FIRST = transparent hash upgrades via ordering
- Settings = where/how to run; services/DB = what is true; flags = operational levers, default-OFF

## 14. What You Should Now Understand

The convenience/safety/behavior classification, why overlays beat
branching, how fail-fast extends from import to deploy, and what NEVER
belongs in settings. Shaky? Read `production.py` top to bottom — it's
shorter than this page.

**Recommended next topic:** [testing/testing-strategy](../testing/testing-strategy.md)
— the other half of "fail loudly, early, where it's cheap."

## Implementation References

- Ops story: [docs/release/DEPLOYMENT_GUIDE.md](../../../docs/release/DEPLOYMENT_GUIDE.md) · registered residual: DEP-F1 in [docs/PENDING_BACKLOG.md](../../../docs/PENDING_BACKLOG.md)

## Code References
- `config/config/settings/base.py` (Argon2 block, DB via config) · `production.py` (the strict overlay) · `deploy/` (baked module, verify gate)

## Further Reading

- Official: [Django — settings best practices](https://docs.djangoproject.com/en/5.0/topics/settings/) · python-decouple README

## Related

[tech-stack](../../project/tech-stack.md) · [migrations](migrations.md) ·
[testing-strategy](../testing/testing-strategy.md)
