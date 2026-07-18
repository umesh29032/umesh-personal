---
id: docs-html-fix-history
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# HTML_FIX_HISTORY — chronological fix log

Companion to [HTML_AUDIT_MASTER.md](HTML_AUDIT_MASTER.md). One row per committed fix,
newest at top. The audit trail of what changed, why, and the commit that landed it.

## Entry format

```
## <date> — HTML-NNN <path>
- Issue: <severity> — <what was wrong>
- Fix: <what changed>
- Files: <files touched>
- Canonical: <CC-NN promoted / UI_COMPONENTS section / none>
- Verified: <viewports + browser evidence>
- Commit: <hash>
```

A fix is logged here ONLY after owner review + commit (per the no-auto-commit rule).
Pre-commit work-in-progress lives in the HTML_AUDIT_LEDGER record (status FIXED).

---

## 2026-06-16 — CC-29 `production/pattern_form.html` (Phase D — HTML-040)

- Issue: MEDIUM (user-facing validation failure) — `pattern_form.html` rendered only
  `form.non_field_errors`; no per-field `{{ form.X.errors }}`. ProductPatternForm has required
  `code` + `name` (field-level errors) → invalid/empty submit re-rendered with **zero visible
  feedback** (browser-confirmed: empty submit → no error shown, no create).
- Fix: added per-field `{% if form.X.errors %}<div class="form-error">…</div>{% endif %}` to all 5
  fields, using the base-defined `.form-error` class (base.html:1303). Template-only (10+/2−).
- Files: `config/production/templates/production/pattern_form.html`.
- Canonical: none promoted. Logged **CC-29**. (CC-30A bare-inputs + CC-30B/XC-1 mobile-clip on the
  same page = record-only, owner-deferred.)
- Verified: browser (real Chromium) — empty submit → 2 visible "This field is required." under
  name+code; optional fields show none; non_field block untouched; console clean. No CSS/widget change.
- Commit: **`2e5910b9`**

## 2026-06-16 — CC-27 `accounts/forms.py` (Phase D — skill_form HTML-033 + usertype_form HTML-034)

- Issue: MEDIUM (validation broken) — `SkillForm.name` + `UserTypeForm.code` used
  `pattern=r'[-a-z0-9_]+'`. Chromium compiles the HTML `pattern` attribute with the `v`
  (unicodeSets) flag, where an unescaped `-` in a character class is a **SyntaxError** →
  the attribute threw on every `checkValidity()` (console error) AND the native slug
  constraint was **silently dropped** (no client-side validation). Browser-reproduced on
  skill_form; discovered during HTML-036.
- Fix: escape the dash → `r'[a-z0-9_\-]+'` (2 regex lines). Same char set; compiles under
  both `u` and `v`. NB owner's first proposal `[a-z0-9_-]+` (trailing dash) **also failed**
  `v`-mode — browser caught it; only the escaped form compiles.
- Files: `config/accounts/forms.py` (lines 28 + 43 only).
- Canonical: none promoted. Logged **CC-27**. Also corrected HTML-033's earlier "0 console
  errors / native pattern confirmed" (retracted — first console read pre-dated the validity
  trigger).
- Verified: browser (real Chromium) on **skill_form** + **usertype_form** — `new RegExp(p,'v')`
  compiles; anchored `checkValidity()` accepts `stitching_master`/`with-hyphen`/`franchise_owner`,
  rejects `Bad Slug!`/`BAD CODE`; no new console SyntaxError. No template/ownership change.
- Commit: **`20fccbd7`**

## 2026-06-15 — HTML-002 `accounts/user_form.html` (Phase A)

- Issue: MEDIUM (user-visible) — multi-line `{# … #}` template comment (lines 44–45)
  rendered as **visible text** on every Edit-User page (`{# #}` is single-line only;
  the text leaked between hero and Identity panel). Owner-recurring regression class.
- Fix: `{# … #}` → `{% comment %}…{% endcomment %}` (2 lines).
- Files: `config/accounts/templates/accounts/user_form.html`.
- Canonical: none promoted. Logged CC-04 (multi-line `{# #}` leak class; already
  canon in UI_COMPONENTS.md + feedback memory — enforcement-check candidate). Same
  class also found at `signup_otp.html:74` (dormant/unrouted, deferred to HTML-032).
- Verified: server restarted (template cache); leak gone in rendered body + 320
  screenshot; selects (role + user_type fancify/pick) + validation alert intact;
  0 console errors at 320/375/390/414/1280.
- Commit: **`bcf508f2`** (`bcf508f2eedd517aab39224bc9a391ca46b0b4ca`)

## 2026-06-15 — Step 0 (pre-work) fancy-date control

- Scope: not an HTML unit — pre-Phase-A review+commit of the uncommitted
  `fancy-date` calendar control sitting in the working tree (prior session).
- Change: opt-in custom calendar (`fancifyDate`) for `<input type=date>` carrying
  `[data-fancy-date]`; body-anchored `position:fixed` panel (escapes native
  popup misposition + desktop icon-only-click); only consumer = `user_form`
  birth_date. No new code from this session — review + document + commit.
- Files: `accounts/base.html` (+359 CSS+JS), `accounts/user_form.html`
  (birth_date → `data-fancy-date`), `UI_COMPONENTS.md` (+23: date-picker section
  + known-limitations), `docs/apps/accounts/GUIDE.md`, `docs/PENDING_BACKLOG.md`.
- Verified (real Chromium, fresh server): 1280 open/anchor/no-overflow · year nav
  (100y range) · select commit (`input.value` ISO + label) · **persistence
  round-trip** (Save → DB `1990-03-12` → reload renders) · Clear · 320/375/390/414
  panel fits + flips-above + 45px trigger + 0 page overflow · **0 console errors**
  at every width. DB restored to null after test (clean).
- Known limitations (accepted, NOT blockers — documented in UI_COMPONENTS.md):
  keyboard grid-nav/focus-trap/focus-return absent + no type-to-enter (a11y, same
  class as fancy-select); day cells 38px<44px at 320 (7-col floor); form-reset
  doesn't re-sync label (no reset form exists). Future keyboard-nav parity tracked
  as a shared candidate → HTML_CANONICAL_CANDIDATES CC-01.
- Commit: **`7e105b92`** (`7e105b92b13b14dd05ea1ee0d22c7400664e630c`)
