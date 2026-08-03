---
id: app-storefront-services
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "image_service — the upload boundary; and where storefront's future service surface will grow."
related: [app-storefront, pattern-validation-chain]
---

# storefront — service knowledge

> 📂 [storefront app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

> 💡 **Samjho aise** — Services = **counter ke peeche baitha clerk**
>
> **Asli kaam yahin hota hai** — database mein likhna, hisaab lagana, rules lagana. Is project ka sabse bada niyam: *har likhne ka kaam service mein hoga, view mein kabhi nahi*. Isi wajah se paisa surakshit rehta hai — har table ka **ek hi** likhne wala hota hai.
>
> *(`storefront` app ka kaam: public website — featured products aur categories jo bahar dikhte hain.)*

## `image_service.py` — the upload boundary

`process_and_attach(instance, field_specs, cleaned_data=, form_data=)` —
every listing upload passes through: validate type/size → process/normalize
→ attach. Files are the one INPUT this app accepts beyond text fields, and
files are hostile until proven otherwise ([validation-chain](../../concepts/patterns/validation-chain.md)
applied to bytes). Callers: the listing CRUD forms/views.
Failure modes: refused uploads with form errors (never a 500 for a bad file).

## The thin-by-design service layer (and its future)

One service module is HONEST for what this app is today: presentation CRUD
+ one input boundary. The G2 future (order capture) will grow real verbs
here — order intake, idempotency, the internal handoff bridge — and THEY
will follow the house laws (sole writers, atomic verbs, refusal messages).
The seam is marked in urls.py's docstring; the discipline is already
documented; the code arrives when the business does.

## Adding/changing — checklist

New input from the street? → boundary project (README REQ #1), owner-gated ·
new upload field → through `process_and_attach` · never a write into
another app's tables · kos-sync.

## Required Knowledge (this page)

- [ ] The validation chain → [pattern](../../concepts/patterns/validation-chain.md)
- [ ] Service-layer laws (for the G2 future) → [service-layer](../../concepts/architecture/service-layer.md)

## Learning Graph

**Before:** [models.md](models.md). **After:**
[auth-hardening](../../concepts/security/auth-hardening.md) — the other
outside-facing boundary, hardened; compare the two walls.
