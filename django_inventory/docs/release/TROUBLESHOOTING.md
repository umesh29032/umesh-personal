---
id: release-troubleshooting
type: topic-canonical
status: active
owner: handwritten
scope: release-handbook
anchors: —
verified: 2026-07-19
---

# Troubleshooting — ERP v1.0 (production problems, field-guide style)

> Format har issue ka ek hi hai: **Symptoms → Root cause → Diagnosis → Fix →
> Verification.** Pehle failure-class pehchano, phir lever chuno — panic mein
> "sab restore kar do" sabse mehngi galti hai.

## 1. Site down — Caddy 502 / connection refused

- **Symptoms:** browser 502; `docker compose ps` mein `app` restart-loop.
- **Root cause (common order):** (a) `.env` mein missing/typo value → app ka
  fail-fast crash (SECRET_KEY/REDIS_URL/CSRF_TRUSTED_ORIGINS); (b) DB not
  healthy; (c) bad deploy.
- **Diagnosis:** `docker compose logs --tail 100 app` — fail-fast crash apna
  naam khud bolta hai ("SECRET_KEY is not set", "connection refused").
- **Fix:** (a) `.env` theek karo → `docker compose up -d`; (b) `docker
  compose logs db`, disk full check (`df -h`); (c) rollback lever
  (DEPLOYMENT_GUIDE §Rollback).
- **Verification:** site loads + `verify_production` PASS.

## 2. Har form submit 403 de raha hai (GETs theek hain)

- **Symptoms:** login/settlement/koi bhi POST → 403 CSRF error.
- **Root cause:** `CSRF_TRUSTED_ORIGINS` mein scheme-sahit domain nahi hai,
  ya DNS/domain badla aur .env update nahi hua. (Behind-TLS-proxy Django ka
  documented behavior.)
- **Diagnosis:** error page/log mein "Origin checking failed".
- **Fix:** `.env` → `CSRF_TRUSTED_ORIGINS=https://<domain>` → restart app.
- **Verification:** login POST succeed.

## 3. TLS certificate nahi ban raha (first boot)

- **Symptoms:** `caddy` logs mein ACME challenge failures; site sirf HTTP.
- **Root cause:** DNS A record VPS-IP par resolve nahi ho raha tha jab Caddy
  ne challenge kiya; ya port 80 ufw mein band hai.
- **Diagnosis:** `dig <domain>` (IP match?); `ufw status` (80/443 open?).
- **Fix:** DNS theek karo → `docker compose restart caddy`.
- **Verification:** `https://<domain>` green lock.

## 4. Login ho hi nahi raha / account lock

- **Symptoms:** sahi password par bhi "try later" — rate-limit message.
- **Root cause:** per-email/per-IP throttle trip hua (brute-force protection
  — Redis counters). Ya user `is_active=False` hai (leaver).
- **Diagnosis:** security log: `docker compose logs app | grep " security "`
  — throttle/lockout events named hote hain. Inactive user → `/accounts/inactive/`
  redirect distinct pattern.
- **Fix:** genuine user ke liye throttle window ka wait; admin-side unlock =
  `reset_throttle` (accounts/throttle.py) via shell; inactive = admin se
  reactivate (soft-state hai, DELETE kabhi nahi tha).
- **Verification:** login OK; security log mein success entry.

## 5. "Yeh number galat lag raha hai" (costing / earnings / settlement)

**Sabse pehle:** number galat *dikhna* aur galat *hona* alag cheez hai. Is
system mein har figure derive hota hai — to pehle derive ko samjho.

- **Symptoms:** owner/manager bolta hai "is Adda ka cost zyada/kam hai" ya
  "worker ka expected alag tha".
- **Root cause candidates:** (a) unpriced roll → material INCOMPLETE flag
  (yeh bug nahi, honest-NULL hai — banner dikhega "consumed rolls without a
  purchase price"); (b) verified-vs-reported quantity difference (settlement
  `verified ?? reported` resolver use karta hai); (c) rate galat tha →
  rate-correction flow; (d) genuinely stale snapshot — rare, kyunki
  snapshots frozen by design.
- **Diagnosis:** shell mein service-truth recompute (READ-ONLY):
  ```python
  from production.services import cost_service
  cost_service.full_cost_for_adda(adda)     # components alag-alag dikhte hain
  cost_service.material_cost_for_adda(adda) # 'unpriced_rolls' count dekho
  ```
  Settlement side: ADST detail page ke items vs
  `WorkerLedgerEntry.objects.filter(assignment__adda_settlement=s)` — yeh
  four-way identity certification mein byte-exact proven hai; agar yeh toote
  to REAL bug hai, turant report.
- **Fix:** (a) roll ka price record karo (purchase fact) — derive khud sahi
  ho jaayega; (b/c) in-app correction flows (verify-quantity page,
  super-admin `rerate_stage_role` — audit row banta hai); (d) service-layer
  bug = STOP + owner report (Money-Write discipline).
- **Verification:** page refresh = service recompute match; audit row exists.

## 6. Settlement finalize refuse kar raha hai

- **Symptoms:** finalize par clear error message (reopen guard / recon
  block / era guard).
- **Root cause:** yeh REFUSALS features hain: downstream-consumer reopen
  guard, over-allocation refusal, S5 reconciliation gate (agar flag ON ho),
  era armor (superseded/reversed settlements ke against).
- **Diagnosis:** error message ACTIONABLE likha hai (kaunsa stage/blocker,
  kya action) — use poora padho, wo hi diagnosis hai.
- **Fix:** message jo bolta hai (reverse/void/reopen chain peel karo). Flag
  wala block super-admin audited-override ke saath bhi khul sakta hai
  (`SettlementReconciliationEvidence` row banta hai).
- **Verification:** finalize succeeds; evidence/audit rows present.

## 7. Static files / CSS gayab after deploy

- **Symptoms:** site chalta hai par bina styling.
- **Root cause:** collectstatic fail hua tha entrypoint mein (disk full ya
  permissions) — ya browser cache.
- **Diagnosis:** `docker compose logs app | grep collectstatic`.
- **Fix:** space banao → `docker compose restart app` (entrypoint dobara
  collect karega).
- **Verification:** `/static/...` URLs 200 + styled page.

## 8. Media file 404/403 (pattern photos, receipts)

- **Symptoms:** upload hua tha, ab nahi khul raha; ya anonymous ko khul raha
  hai (!).
- **Root cause:** media Django-view-gated hai (deliberate — private files).
  403 anon ke liye CORRECT hai. 404 = volume mount issue ya restore ke baad
  media copy nahi hui.
- **Diagnosis:** `docker compose exec app ls /srv/app/media/...`; restore ke
  baad? → restore drill step 5 (media copy) chhoota to yehi hota hai.
- **Fix:** restic se media restore → volume mein copy (runbook §Restore).
- **Verification:** logged-in user ko file khulti hai, anon ko 403.

## 9. `verify_production` FAIL after deploy

- **Symptoms:** deploy smoke to theek, gate red.
- **Root cause:** gate ka poora kaam hi yehi hai — unapplied migration, dev
  contamination (`dev.*` user production mein!), settings mismatch
  (DEBUG on), money-integrity drift.
- **Diagnosis:** command output check-by-check named hai; report JSON
  `var/verification_reports/` mein.
- **Fix:** jo check bola: migration → `migrate`; contamination → wo data
  production mein aana hi nahi chahiye tha, import decision review karo;
  settings → `.env`.
- **Verification:** re-run ALL PASS. Gate pass hue bina deploy DONE nahi
  hota — yeh discipline hi iska value hai.

## 10. Test battery locally red (jo CI-green thi)

- **Symptoms:** wahi code, tumhare machine par fails.
- **Root cause (documented flake modes):** `--parallel` (patterns_ai) ya
  `--keepdb` (Role rows truncate) use kiya; ya scratch-DB env var leak.
- **Fix:** battery ka 4-group sequential fresh-DB law follow karo
  (DEVELOPER_GUIDE §Testing).
- **Verification:** 1878/1878.

## Escalation rule / Kab rukna hai

Money-table mein direct SQL fix karne ka mann kare — **MAT KARO.** Ledger
append-only hai; har correction ka in-app rasta hai (reverse, void,
supersede, rerate — sab audited). Agar sach mein service-layer bug mila hai:
evidence collect karo (request-id, shell recompute, audit rows) aur owner ko
STOP-report do. Yeh Money-Write STOP rule ka production avatar hai.
