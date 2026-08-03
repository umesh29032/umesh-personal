---
id: release-operations-manual
type: topic-canonical
status: active
owner: handwritten
scope: release-handbook
anchors: deploy/
verified: 2026-07-19
---

# Operations Manual — ERP v1.0

> **Kaun padhe:** jo bhi system ko roz chalata hai (abhi: owner khud).
> Yeh manual "kya karna hai aur KYU karna hai" dono sikhata hai — sirf
> commands ki list nahi. English + Hinglish dono mein, taaki 2 saal baad
> naya developer bhi seedha samajh jaye.

## The operator's mental model / Operator ka nazariya

System ke 4 hisse hain jo kabhi bhi bigad sakte hain:

```
 1. App (gunicorn)      → restart se theek hota hai, data safe rehta hai
 2. Database (Postgres) → YAHI asli keemti cheez hai — ledger, settlements
 3. Redis               → sirf cache + rate-limit counters; kho jaye to bhi
                          koi money-data nahi jaata
 4. Media volume        → pattern photos, receipts — backup mein shamil
```

**Golden rule:** Database + `.env` (password manager wala) + restic repo =
poora system dobara khada ho sakta hai. Baaki sab replaceable hai.

## Daily operations / Roz ka kaam

| Check | Command | Kyu |
|---|---|---|
| App zinda hai? | site kholo; ya `docker compose ps` — sab `Up (healthy)` | Caddy 502 dikhaye to app container dekho |
| Logs mein error? | `docker compose logs --since 24h app \| grep -iE "error\|traceback"` | 500-errors stdout par aate hain; roz 2 minute ka scan chhoti problem ko badi hone se rokta hai |
| Security log | `docker compose logs --since 24h app \| grep " security "` | failed logins / rate-limit hits yahan dikhte hain — brute-force attempt ka pehla signal |
| Kal ka backup bana? | `docker compose exec backup restic snapshots --last 1` | backup **hamesha** verify karo — "chal raha hoga" assumption hi DR ko maarta hai |

**Business-side daily:** workers apna kaam report karte hain; manager verify
karta hai. In-app data-entry mistakes ke liye ops ko kuch nahi karna —
system mein reverse/void/supersede ke raste bane hue hain (append-only
philosophy: galti DELETE nahi hoti, nayi row se correct hoti hai).

## Weekly operations / Hafte ka kaam

1. **`restic check`** (backup service khud weekly karta hai — logs mein
   confirm karo). Kyu: bit-rot ya adhura upload restore ke waqt pata chale,
   isse pehle pata chalna chahiye.
2. **Disk space:** `df -h` on the VPS. Docker images + local dumps jagah
   khaate hain; `docker image prune -f` deploy script khud karta hai, par
   volume growth par nazar rakho.
3. **Settlement queue saaf hai?** `/expense/settlements/` — jo Addas "ready"
   dikh rahe hain unhe settle karo. Kyu: jitna lamba unsettled kaam, utna
   bada expected-vs-actual gap workers ke mann mein.

## Monthly operations / Mahine ka kaam

1. **Restore drill** (runbook ka rule: mahine mein ek baar):
   ```
   # test DB mein restore karke sentinel ginti check karo — production ko
   # chhue bina. Poora procedure: deploy/README.md §Restore drill.
   ```
   Kyu: backup jo kabhi restore nahi hua, wo sirf ek ummeed hai. Release ke
   waqt yeh drill REAL data par pass ho chuki hai (ledger 170 rows /
   Σ₹10,880.25 byte-exact wapas aaye the) — wahi standard maintain karo.
2. **Monthly expenses generate karo:** `/expense/generate/` (ya
   `manage.py generate_monthly_expenses`). Preview → confirm. Engine
   idempotent hai — do baar confirm karne par duplicate NAHI banta
   (DB-level partial-unique constraint rokta hai).
3. **Monthly payroll rhythm:** settlements finalize → worker payments
   (`/expense/workers/<id>/settle/`) → advances recover ho jaate hain
   payment ke waqt.
4. **Dependency glance:** `env/bin/pip list --outdated` (dev machine par).
   Security patches ke liye Django minor releases follow karo. Upgrade =
   normal deploy flow + full battery pehle dev par.

## Backup policy / Backup ki niti

| Cheez | Kya | Kahan | Retention |
|---|---|---|---|
| Nightly | `pg_dump -Fc` + `/media` | restic → B2/R2 (offsite) + 3 local dumps | 7 daily / 4 weekly / 6 monthly |
| Pre-deploy | `pg_dump -Fc` | local `backups` volume | har deploy se pehle automatic (`deploy.sh`) |
| DR pair | filled `.env` | password manager | permanent |

Kyu yeh design: **RPO 24 ghante** chhoti factory ke liye accepted trade-off
hai (din bhar ka data-loss worst case). Agar business badhe to RPO ghatana =
WAL archiving ya managed Postgres — runbook ke "future exits" mein recorded.

## Restore policy / Wapas laane ki niti

Teen scenarios, teen raste (details: deploy/README.md):

1. **Ek galat deploy:** `predeploy-*.dump` restore + code tag rollback.
2. **VPS hi mar gaya:** naya VPS → repo clone → password-manager se `.env` →
   restic se latest snapshot restore → `docker compose up -d`. **From
   NOTHING, sirf 3 cheezon se** — yahi is design ka poora point hai.
3. **Sirf ek galat business entry:** restore MAT karo. App ke andar
   reverse/void/supersede use karo — poora DB peeche le jaana ek entry ke
   liye baaki sab ka data kho dena hai.

## Monitoring & log inspection

Aaj kya hai: structured logs (har line mein request-id — ek request ki poori
kahani `grep <request-id>` se nikal jaati hai), alag security logger,
db/redis healthchecks, aur `verify_production` (correctness gate — sirf
startup nahi, SAHI chal raha hai yeh batata hai).

Kya abhi NahiN hai (temporary accepted — release log C2 record): Sentry,
`/healthz`, uptime alerts. **First deploy ke turant baad yeh menu lagao** —
sab config-level hai (DEPLOYMENT_GUIDE §Health checks). Tab tak: roz ka log
scan hi monitoring hai, isliye usse skip mat karo.

**Log padhne ka tarika (example scenario):** user bolta hai "settlement
finalize par error aaya 2 baje ke aas-paas":
```
docker compose logs --since 6h app | grep -i "adda_settlement"
# → milega: adda_settlement.finalize ref=ADST-00xx ... ya traceback
# traceback mile to request-id utha kar poori request trace karo:
docker compose logs app | grep "<request-id>"
```
Money-mutations ke liye logs se bhi aage: **persisted audit rows** hain
(RateCorrectionAudit, WorkerPayBasisAudit, ExpenseTemplateAmountAudit, void
reasons, supersession chains) — investigation kabhi sirf logs par depend
nahi karti. Yeh design decision hai: logs ephemeral hote hain, audit rows
nahi.

## Maintenance rhythm / Rakh-rakhav

- **OS patches:** VPS par unattended-upgrades on rakho; quarterly reboot
  window (compose `restart: unless-stopped` sab wapas utha lega).
- **Docker image refresh:** pinned versions hain (postgres 16.6, redis
  7.4.2, caddy 2.9.1) — inhe upgrade karna = conscious decision + test, kabhi
  `latest` mat karo. Pin isliye hai taaki "aaj achanak naya postgres aa
  gaya" wala surprise kabhi na ho.
- **Certificate renewals:** Caddy automatic. Kabhi manual mat karo.

## Release process (ops side) / Naya version nikalna

1. Dev machine par: full battery green (4 groups, sequential fresh-DB —
   DEVELOPER_GUIDE mein law likha hai) + `knowledge_sync` clean.
2. Tag banao (`erp-v1.x.y`), push karo. Tag hi rollback vocabulary hai.
3. VPS par `./deploy/deploy.sh` (pre-deploy dump automatic).
4. Smoke + **`verify_production`** — pass nahi to deploy adhura hai.
5. Kuch bigda? → Rollback section (DEPLOYMENT_GUIDE) — lever failure-class
   ke hisaab se chuno, panic mein sab kuch restore mat karo.
