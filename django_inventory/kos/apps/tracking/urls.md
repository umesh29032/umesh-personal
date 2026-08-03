---
id: app-tracking-urls
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "Where are tracking's URLs? (The absence IS the lesson — and here's the map to the real surface.)"
related: [app-tracking, app-inventory-urls]
---

# tracking — URL knowledge (zero routes, by architecture)

> 📂 [tracking app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

> 💡 **Samjho aise** — URLs = **address book**
>
> Yeh file batati hai kaunsa web address (jaise `/production/addas/`) kis view pe jaata hai. Jab aapko pata na ho ki koi page kis code se banta hai — **hamesha yahin se shuru karo**.
>
> *(`tracking` app ka kaam: **history aur barcode** — kya hua, kab hua, kisne kiya.)*

## The absence, explained (learn from it)

`config/tracking/` mounts NO URLConf and its `views/` package is an empty
husk. This is the P4.2 D1 boundary decision, executed: the /tracking/
SURFACE (13 routes, `tracking:` namespace) lives in
`config/inventory/tracking_urls.py` with views in `config/inventory/views/
tracking_*.py` — so this data app imports no production code, while every
template's `{% url 'tracking:...' %}` kept working (namespace preserved).

**Engineering Decision (the move).** *Problem:* tracking views imported
production models → a data app dragging domain weight. *Options:* (A) live
with it; (B) split views into a new app; (C) move views to the shell app
that already owns cross-domain surfaces, keep the namespace. *Chosen:* C.
*Trade-off:* "tracking's screens aren't in tracking" — THIS page exists to
kill that surprise. *Still today?* Yes — the empty views/ husk is the
receipt.

## Where every route actually lives

All 13 documented individually at
**[inventory urls.md §§8–20](../inventory/urls.md)**: dashboard · barcode
list/print/quick-export · scan + scan-status · roll/adda history ·
export manifest + 3 tracked triggers + re-download.

## Direct paths

Surface: `config/inventory/tracking_urls.py` + `config/inventory/views/tracking_*.py`
· Data+logic (HERE): `config/tracking/models.py` · `config/tracking/services/`

## Learning Graph

**Before:** [README](README.md) Mental Model. **After:** [inventory §§8–20](../inventory/urls.md) — the surface these records power.
