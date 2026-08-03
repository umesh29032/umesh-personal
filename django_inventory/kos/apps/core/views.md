---
id: app-core-views
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "core's views — none exist; templatetags and observability are the only render-adjacent citizens."
related: [app-core]
---

# core — handler knowledge (none, by constitution)

> 📂 [core app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

> 💡 **Samjho aise** — Views = **reception counter**
>
> Browser se request aati hai to sabse pehle yahin aati hai. View ka kaam sirf teen cheezein hai: **request padho → permission check karo → service ko bhej do**. View khud database mein likhta **nahi** — isiliye yeh files patli hoti hain. Moti view = design ki galti.
>
> *(`core` app ka kaam: saara project jo cheezein baar-baar use karta hai (jaise har table ka created_at/updated_at) — iska apna koi table nahi.)*

No views module at all — not even an empty husk (contrast tracking's
husk-with-history: core never HAD views to remove; the purity was original).

**Render-adjacent citizens:** `templatetags/` (shared template helpers —
grammar for templates, same philosophy) · `observability.py` (logging/
metrics plumbing — a cross-cut that IS model/infra-layer, hence lives here;
request-layer cross-cuts live in inventory's middleware — each concern at
its own layer, the cross-cutting doctrine in practice).

**Rule of thumb:** if you're about to write a view "in core," you're
holding a domain feature — find its owner app.

## Learning Graph

**Before:** [urls.md](urls.md). **After:** [models.md](models.md) — the grammar itself.
