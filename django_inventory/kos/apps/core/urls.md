---
id: app-core-urls
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "core's URLs — there are none, and that absence is the chapter's first lesson."
related: [app-core]
---

# core — URL knowledge (zero routes, the deepest absence)

> 📂 [core app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

> 💡 **Samjho aise** — URLs = **address book**
>
> Yeh file batati hai kaunsa web address (jaise `/production/addas/`) kis view pe jaata hai. Jab aapko pata na ho ki koi page kis code se banta hai — **hamesha yahin se shuru karo**.
>
> *(`core` app ka kaam: saara project jo cheezein baar-baar use karta hai (jaise har table ka created_at/updated_at) — iska apna koi table nahi.)*

## The absence, explained

Core mounts NOTHING. No urls.py in the request path, no view answers for
it, no user has ever "visited core" — yet every request touches it
(timestamps stamped, bases inherited, guards enforced at build time).

**The lesson:** foundations exert influence without surface. A layer that
needed URLs to matter would be a domain wearing a foundation's name.
Compare the system's other great absences — no signup route (S2), no
delete on money, no scheduling on machines — and notice the pattern the
LOS has taught nine times: **what a system refuses to have is as designed
as what it has.** *(Jo nahi hai, wo bhi design hai.)*

## Where core actually "runs"

Model save (timestamps) · manager resolution (`Model.active`) · history
row shapes · BUILD TIME (the five test suites — core's real "endpoints"
are CI assertions). Details: [services.md](services.md).

## Learning Graph

**Before:** [README](README.md) — the five values. **After:** [services.md](services.md) — where core actually "runs" (build time).
