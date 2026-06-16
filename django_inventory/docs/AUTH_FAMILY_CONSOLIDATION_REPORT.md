# Auth Family Consolidation Report (Phase D — Auth subset)

> **Evidence-based synthesis of the HTML-by-HTML audit, Phase D auth cluster.**
> Source: [HTML_AUDIT_LEDGER.md](HTML_AUDIT_LEDGER.md) (HTML-026/027/028/029/030/031/032) +
> [HTML_CANONICAL_CANDIDATES.md](HTML_CANONICAL_CANDIDATES.md) (CC-22 form-system · CC-23 OTP-widget ·
> CC-24 validation · CC-04 comment-hygiene; FROZEN 2026-06-16).
>
> **Status: EVIDENCE + RECOMMENDATIONS ONLY.** Nothing implemented. **UI_COMPONENTS.md unchanged.**
> No standardization / migration / fix / promotion authorized here.
>
> Date 2026-06-16 · Branch `new_flask_app` · browser-verified where reachable; render-blocked pages
> marked honestly (NOT marked clean). **CC-22 / CC-23 / CC-24 kept SEPARATE — not merged into one
> "auth cleanup". Purpose = preserve root causes independently.**

---

## 0. Coverage + completeness

Full grep of `accounts/templates/accounts/*.html` + route check (`accounts/urls.py`) → **7 auth templates**,
all audited. Browser/render status (honesty rule):

| HTML | Page | Reachable? | Evidence level |
|---|---|---|---|
| 026 | forgot_password | ✅ live | **browser-verified** (1280/320/375/390/414) |
| 027 | login | ✅ live | **browser-verified** (split-screen) |
| 028 | login_password | ✅ live | **browser-verified** (split-screen) |
| 029 | otp | ⛔ flow-gated (`/app/verify-otp/` redirects w/o pending-OTP session; email step rate-limits — **not triggered**) | code-read (NOT clean) |
| 030 | reset_otp | ✅ live (`/app/reset-password/verify/` renders directly) | **browser-verified** — **OTP-widget render proxy** |
| 031 | signup | ⛔ DISABLED/unrouted (PA-02-OPEN-SIGNUP) | code-read (NOT clean) |
| 032 | signup_otp | ⛔ DORMANT/unrouted | template-render-verified (NOT browser; NOT clean) |

**4 of 7 browser-verified · 3 render-blocked (honestly marked).** reset_otp (030) is the OTP-widget render
proxy (same widget family as 029/032). No flow/email/rate-limit was triggered to reach gated pages.

---

## 1. How many auth form implementations actually exist?

**SEVEN templates · SEVEN independent implementations.** Every auth page is a **standalone HTML document**
(no `{% extends %}` of base.html — deliberate: pre-auth pages carry no app chrome) with its **own inline
`<style>`**, its own copy of the design tokens (`:root --ink/--copper/--cream…`), and its own `.field` /
`.alert` / `.btn-cta` rules.

Two layout sub-shapes (still 7 separate CSS copies):
- **Split-screen** (left brand panel + right form): login (027) · login_password (028) · signup (031).
- **Centered single-card**: forgot_password (026) · otp (029) · reset_otp (030) · signup_otp (032).

login_password (028) is explicitly **a copy of login (027) with drift** (ledger HTML-028). → **CC-22**.

---

## 2. Shared foundation vs copy-paste ownership

**NO shared foundation. 100% copy-paste.** There is no `base_auth.html`, no shared auth partial, no shared
auth stylesheet. Each of the 7 pages re-declares the same tokens + `.field` + `.alert` + `.btn-cta`.

| Owner pattern | Reality |
|---|---|
| Shared base/partial | ❌ none exists |
| Per-page inline copy | ✅ all 7 (each its own `<style>`) |

**Consequence:** any auth-wide change (token, focus ring, touch height, button style) = 7 edits, and copies
already drift (028 from 027). This is **CC-22 — Auth Form System Fragmentation (7 owners)**.

---

## 3. Validation systems and ownership model

**TWO competing validation strategies in the auth family** (grep-proven across all 7):

| Strategy | Pages | Mechanism |
|---|---|---|
| **A — `form.errors`** | **signup (031) ONLY** | `{% if form.errors %}` → `field.errors` + `non_field_errors` aggregated to top `.alert-error` blocks; **no messages block** |
| **B — Django messages framework** | login · login_password · forgot_password · otp · reset_otp · signup_otp (6) | `{% for message in messages %}` → `.alert-{{tags}}`; view pushes `messages.error/success` |

reset_otp (030) additionally has a `.field-error` for its password field (a 3rd micro-pattern, page-local).

**Ownership:** each page owns its own `.alert` CSS + chooses its own strategy. No shared validation/error
component. **Scope (render-confirmed):** signup's own OTP step (signup_otp) uses **B**, so the signup *flow*
is internally split (step1 A → step2 B) ⇒ **strategy A is isolated to signup.html ALONE** — a one-page
outlier across the entire auth surface. This is **CC-24 — Auth Validation Fragmentation**.

**Latent (dormant) consequence:** signup (031) renders no messages block, yet `SignupView` calls
`messages.error()` on throttle → that message would be **invisible** if signup is re-enabled. Logged, not
fixed (unrouted).

---

## 4. OTP widget implementations and drift

**THREE inline OTP widgets · NO shared partial.** Same conceptual widget (6 `.otp-digit` numeric inputs +
hidden field + JS controller: sync, auto-advance, backspace, arrow-nav, paste-fill, autofocus), duplicated
inline in 3 pages — and they have **drifted**:

| Page | OTP variant | countdown | resend | auto-submit |
|---|---|---|---|---|
| otp (029) | **FULL** | ✅ | ✅ | (code-read) |
| signup_otp (032) | **FULL** | ✅ | ✅ | ✅ `form.submit()` at 6 (render-confirmed) |
| reset_otp (030) | **REDUCED** | ❌ | ❌ | ❌ |

So the 3 copies = **2 full + 1 reduced**; reset_otp is the lone feature-incomplete copy
(**browser-confirmed**: no countdown/resend element in its live render, but auto-advance + paste-fill work).
This is **CC-23 — OTP Widget Fragmentation (2-full + 1-reduced, drift)**.

**Also (CC-04):** signup_otp (032) lines 74-76 contain a 3-line `{# … #}` comment (single-line-only syntax)
→ **template-render-verified to leak** as visible text. Same class as the HTML-002 live bug. **But
dormant/unrouted = not user-facing today** → logged, NOT fixed, NOT elevated (owner dormant-bug doctrine).

---

## 5. Intentional vs accidental divergence

**Intentional (legitimate):**
- **Standalone (no base.html)** for pre-auth pages — they correctly carry no sidebar/app chrome before login.
- **Split-screen vs single-card** layouts — plausible deliberate design per page purpose.
- **OTP rendered as a 6-box widget** (not one text input) — deliberate UX.

**Accidental / divergent (the findings):**
- **7 copies of `.field`/`.alert`/tokens** with no shared owner (CC-22); login_password drifted from login.
- **OTP 2-full + 1-reduced** — reset_otp missing countdown/resend/auto-submit the others have (CC-23). Almost
  certainly era/author divergence, not a "reset needs no resend" decision.
- **signup on `form.errors` while all others (incl. its own OTP step) use messages** (CC-24) — inconsistent
  validation contract, not a design choice.
- **CC-04 comment leak** in dormant signup_otp.

---

## 6. Sustainable ownership model

**None of the 7 is currently sustainable** — every page is its own owner (per-page inline copy). The only
sustainable model is a **single shared auth foundation**:

| Layer | Sustainable owner (future) |
|---|---|
| Tokens + `.field` + `.alert` + `.btn-cta` + layout shells | one shared auth base/partial (split-screen + single-card variants) → dedupes CC-22 |
| OTP widget | one shared OTP partial (the FULL version) → dedupes CC-23, kills reset_otp drift |
| Validation render | one auth validation contract → resolves CC-24 |

Today: **0 shared owners; 7 independent copies + 3 OTP copies + 2 validation strategies.**

---

## 7. True defects vs architectural fragmentation

**True defects (functional):** NONE live/user-facing. The 4 reachable pages (026/027/028/030) are
browser-verified working — touch ≥44-47px, OTP boxes fit at 320, auto-advance + paste-fill work, 0 console
errors. The only true-bug findings are **both dormant**:
- CC-04 comment leak (signup_otp) — dormant/unrouted.
- signup invisible-throttle-message (CC-24 note) — dormant/unrouted.
Both surface only **if signup is re-enabled**.

**Architectural fragmentation (NOT defects — maintainability/consistency):** CC-22, CC-23, CC-24. These are
the substance of this report: the auth UX works, but it's built from copies that drift and have no single
owner. Kept **separate** (3 distinct root causes, 3 layers: form-CSS / OTP-JS / validation).

---

## 8. Recommended future canonical direction (if any)

> **Recommendations only — not authorized, not implemented. UI_COMPONENTS.md unchanged.**

1. **One shared auth foundation (resolves CC-22).** Introduce a `base_auth.html` (or shared `<style>`
   partial) owning tokens + `.field` + `.alert` + `.btn-cta` + the two layout shells (split-screen +
   single-card). Auth pages extend/include it → 1 owner instead of 7; ends the login/login_password drift.
2. **One OTP widget partial (resolves CC-23).** Extract the **FULL** OTP widget (boxes + controller +
   countdown + resend + auto-submit) to a single included partial; reset_otp adopts it (gains the missing
   features, or documents why it intentionally omits resend). Kills the 2-full/1-reduced drift.
3. **One auth validation contract (resolves CC-24).** Converge on **the messages framework** (6 of 7 already
   use it, incl. signup's own OTP step) — *or* deliberately keep `form.errors` for per-field display and roll
   it out consistently. Owner choice; messages is the lower-effort majority path. Either way, signup stops
   being a one-page outlier. (If messages is chosen, also fixes the dormant invisible-throttle bug.)
4. **CC-04 + invisible-throttle:** fix **only if/when signup is re-enabled** (both dormant today).

**Keep as documented exceptions:**
- Auth pages stay **standalone (no base.html app chrome)** — correct for pre-auth. (A shared *auth* base is
  not the app base.)
- OTP-as-6-box-widget stays the auth OTP pattern.

---

## 9. Decision asks (nothing happens without these)

1. Approve the **7-implementation / 0-shared-foundation** map (§1-§2) as the agreed Auth picture.
2. Confirm **CC-22 · CC-23 · CC-24 remain three separate findings** (this report keeps them separate).
3. Decide whether to pursue, in a future separately-approved standardization phase:
   - a shared auth foundation (CC-22),
   - a single OTP partial (CC-23),
   - a single validation contract + which one (CC-24).
4. Decide the **disposition of the dormant bugs** (CC-04 leak + invisible-throttle): leave dormant, or fix
   pre-emptively, or fix-on-re-enable.
5. Only then: any UI_COMPONENTS.md promotion or code change (separate, reviewed work).

**Until then: no changes. Auth evidence FROZEN. UI_COMPONENTS.md untouched.**

---

## Auth evidence — FROZEN 2026-06-16

CC-22 (form-system, 7 owners) · CC-23 (OTP-widget, 2-full+1-reduced) · CC-24 (validation, signup-isolated) ·
CC-04 (comment leak, dormant). Boundaries stable; no longer changing.

## Owner decisions — RECORDED 2026-06-16 (report ACCEPTED)

1. ✅ Approved the **7-implementation / 0-shared-foundation** map.
2. ✅ **CC-22 · CC-23 · CC-24 stay three separate findings** (not merged).
3. ✅ **Dormant bugs (CC-04 leak + invisible-throttle) = fix-on-re-enable** (leave dormant).
4. ✅ **No UI_COMPONENTS promotion.** 5. ✅ **No code changes.** 6. ✅ **No standardization during the audit.**

**Architecture direction (record only — NOT implementation):** long-term target = enterprise-style frontend
— one canonical impl + one CSS owner + one JS owner + one ownership source per control family; documented
exceptions only; eliminate accidental divergence + copy-paste ownership over time.

**Two distinct phases (kept separate):**
- **Audit phase (current):** discover → classify → prove → freeze. Output = evidence + Consolidation Reports.
- **Standardization phase (future, separate project):** design canonical → implement canonical → migrate
  consumers → remove duplication. (Canonicalization → UI_COMPONENTS promotion → shared-component extraction
  → migration.)

Next: Phase D non-auth form controls — HTML-033 skill_form, then 036-048…
