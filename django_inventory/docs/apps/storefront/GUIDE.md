---
id: apps-storefront-guide
type: app-guide
status: active
owner: handwritten
scope: storefront
anchors: config/storefront/
verified: 2026-07-13
---

# storefront app — file-by-file GUIDE (public site; commerce future home)

> Business view: [config/storefront/README.md](../../../config/storefront/README.md).

| File | What |
|---|---|
| `models.py` | display-config rows (HomePageConfig, FeaturedProduct FREE-TEXT — G6 SKU hi link banayega, Category, cards/links) |
| `services/image_service.py` | croppable image pipeline — the ONE side-effecting write (old ListingService pass-through removed; single-row CRUD = CBV-owned) |
| `views/public_views.py` | no-auth homepage composition (ADR-0008 face) |
| `templates/public_home.html` (project templates/) | anonymous landing page — hero + marquee ribbon + categories/products/why-us (DB rows) + **static About/Our-Story section `#about` (2026-07-20: public company story + 5-step process timeline; hardcoded copy, no models)** + CTA + footer; stat count-up + scroll-progress inline; **hero `{% else %}` = CSS-art "atelier" fallback (KE medallion + orbit rings + floating glass chips) so zero showcase rows never leaves the hero half-empty; cat/product grids `auto-fit+justify-center` (sparse rows center, full rows fill); scroll cue; SVG favicon + theme-color + og meta**; breakpoints 1024/768/480 + prefers-reduced-motion |
| `static/storefront/js/ke-particles.js` | **vanilla canvas "thread-spark" engine (2026-07-20, no library):** copper/cream dust + constellation lines, cursor repulsion (fine pointers), DPR-capped, pauses on tab-hidden/offscreen (IO), refuses to start under prefers-reduced-motion, no-ops on hidden hosts. Shared: homepage hero + login brand panel |
| `static/storefront/vendor/` + `static/storefront/js/home-motion.js` | **motion stack (2026-07-20): GSAP 3.13 + ScrollTrigger + SplitText + Lenis — VENDORED (no CDN; GSAP 100% free incl. ex-premium plugins since Webflow acquisition Apr-2025, standard license).** `home-motion.js` = ONE owner of homepage choreography: kinetic hero/section typography (masked SplitText), Lenis smooth scroll (drives ScrollTrigger via gsap.ticker; anchors offset −84), parallax (deco/showcase/panel), process-thread `--draw` scrub, marquee velocity-skew (wrapper, not track — CSS loop owns track transform), fine-pointer-only magnetic CTAs + 3D card tilt + trailing cursor ring. Fallback chain: reduced-motion or libs missing → plain IO reveals (pre-GSAP behavior). NOT ignored by git (`poc/patterns_ai/vendor/` pattern is poc-scoped) |
| `views/listing_views.py` | listing_team editor — all 8 CBVs gated by `LoginRequiredMixin + ListingTeamMixin` (= `STOREFRONT_ROLES`: super_admin + listing_team; managers/workers blocked) |
| `processors.py` · `widgets.py` · `forms.py` | image widget machinery. **UI-audit 2026-07-20 (`templates/storefront/widgets/croppable_image.html`): `.cw-preview-box` ab `width:100%; max-width:{preview_width}px; aspect-ratio` — pehle fixed `width:400px` tha jo grid track ka min-content 450px force karta tha (specified px width intrinsic sizing mein count hota hai, `max-width:100%` percentage IGNORED) → product/category form ke saare inputs 390px viewport se bahar clip. Lesson: mobile-safe fixed-size preview = `width:100% + max-width:px`, kabhi `width:px + max-width:100%` nahi** |
| `urls.py` | / public + /storefront/ editor |

LAW (ADR-0008/0010 §5): production se koi paisa/quantity yahan nahi; Order→Adda
FK kabhi nahi — G6→G5→G2 raasta locked.

Worker-role certification: **Phase G CERTIFIED 2026-07-12, 0 bugs, 0 changes**
(shell 3-role matrix + browser + CSRF-POST inertia) —
[docs/WORKER_ROLE_CERTIFICATION.md](../../WORKER_ROLE_CERTIFICATION.md).

## Topics yahan use hote hain — kahan padhein
Har concept ka official link + "is project me kahan" mapping:
[../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
App ka business-view: README (code ke saath). Deep lessons: [docs/LEARNING/](../../LEARNING/README.md).
