---
id: release-developer-guide
type: topic-canonical
status: active
owner: handwritten
scope: release-handbook
anchors: config/
verified: 2026-07-19
---

# Developer Guide — ERP v1.0 (andar kaam kaise karein)

> Tum Django jaante ho, yeh ERP nahi — yeh guide wahi gap bharti hai.
> Pehle [ARCHITECTURE_GUIDE](ARCHITECTURE_GUIDE.md) padho (KYU), phir yeh
> (KAISE). Har rule ke saath uski wajah likhi hai, kyunki bina wajah ke rule
> yaad nahi rehte.

## Getting started / Shuruat

```bash
# repo root = /home/tech/umesh-personal (monorepo); ERP = django_inventory/
cd django_inventory
env/bin/python config/manage.py runserver          # settings default = local
# .env chahiye (SECRET_KEY etc.) — bina uske app fail-fast karega (yeh feature hai)
```

Dev server template-cache karta hai — **template edit ke baad RESTART karo**
(certification-era ka documented lesson; warna "change dikh kyu nahi raha"
mein ghanta jaayega).

## Folder structure / Dhaancha

```
django_inventory/
├── config/                  ← Django project (manage.py yahin hai)
│   ├── config/settings/     ← base.py / local.py / production.py
│   ├── <app>/               ← 13 apps (README har app mein)
│   │   ├── models.py (ya models/)
│   │   ├── services/        ← SAARA business logic + writes
│   │   ├── views.py (ya views/)  ← sirf parse → service → render
│   │   ├── tests/           ← app battery
│   │   └── README.md        ← app ka sach
│   └── manage.py
├── deploy/                  ← runbook + compose assets
├── docs/                    ← documentation estate (index: DOCUMENTATION_INDEX.md)
│   └── release/             ← YEH handbook
├── scripts/                 ← knowledge-graph build/validate, ds_lint, docs generate
└── env/                     ← venv (git-ignored)
```

## The layering law / Parat ka kanoon

```
 template ── view ── service ── model ── DB
             │         │
             │         └── transactions, guards, multi-row writes YAHAN
             └── request parse + permission gate + ek service call. Bas.
```

**Kyu:** paisa ginne wala system hai — business logic ek jagah (service)
rahe to review, test aur audit teeno sasste hote hain. Signals BANNED hain.
Agar tumhara view do models ko save kar raha hai, tum galat parat mein ho.

## Money rules / Paise ke niyam (yeh todna = STOP)

1. **Naya money-write path chahiye?** RUKO. Pehle dekho kaunsa single-writer
   service already hai (`ledger_service`, `adda_settlement_service`,
   `advance_service`, `settlement_service`, `expense_service`,
   `payroll_service`). Naya writer banana = design review + owner sign-off
   (Money-Write STOP rule — standing owner order).
2. Ledger/history/audit rows **kabhi UPDATE/DELETE nahi** — reversal ya
   supersession se correct karo.
3. `amount` fields hamesha positive; direction `entry_type` batata hai
   (DB CheckConstraints yeh enforce bhi karte hain — negative probe fail
   hoga, certification mein 10/10 refuse hue the).
4. Monthly-salary worker settlement lines mein kabhi nahi aata (ADR-0011).
5. Costing mein "0 maan lo" kabhi nahi — honest-NULL (ADR-0009).

## RBAC in practice / Permission kaise lagayein

```python
# view mein KABHI raw is_superuser mat likho. Yeh likho:
from accounts.services.permission_service import user_has_role
from accounts.services import ROLE_SUPER_ADMIN

# stage-level access (production):
from production.services.access_service import user_can_access_stage
```
Menu + URL saath mein khulte/band hote hain (`SidebarItemRule` +
middleware) — naya page banaya to uska MenuItem/sidebar rule bhi socho,
warna URL khula reh jaayega ya middleware use kaat dega.

## Testing / Battery ka kanoon

```bash
# THE battery — 4 groups, HAMESHA isi tarah (sequential, fresh DB):
env/bin/python config/manage.py test accounts core raw_materials production \
    tracking expense storefront inventory machines bod
env/bin/python config/manage.py test patterns_ai
env/bin/python config/manage.py test devseed
env/bin/python config/manage.py test verification
# v1.0 baseline: 1132 + 528 + 140 + 78 = 1878 — sab green
```

**Do cheezein KABHI mat karo (documented flake modes):**
- `--parallel` — patterns_ai suite parallel-safe nahi hai (media tempdirs).
- `--keepdb` across suites — TransactionTestCase migration-seeded Role rows
  truncate kar deta hai; agla suite `Role.DoesNotExist` se girta hai.

**Golden money tests:** teen journeys services ke through replay hoti hain
aur exact-decimal assert hoti hain (₹344.25 / ₹801.00 / ₹633.00 —
`devseed/tests/test_golden_journeys.py`). In par kabhi "approx" assert mat
lagana — byte-exact hi inka poora point hai. Perf pins (`assertNumQueries`)
named constants hain — pin girao to constant ke comment mein WAJAH likho,
chupke se number mat badhao.

## Dev data / Duniya banani ho to

```bash
# PRIMARY dev DB ko kabhi seed mat karo — seeder allowlisted scratch DBs par hi chalta hai:
DB_NAME=inventory_seed_scratch_2 env/bin/python config/manage.py seed_factory
DB_NAME=inventory_seed_scratch_2 env/bin/python config/manage.py seed_feature <slug>
# 21 executable scenarios (factory / feature-* / edge-*); idempotent — dobara
# chalao to created=0. Verify:
DB_NAME=inventory_seed_scratch_2 env/bin/python config/manage.py verify_factory
```
Cast credentials sab jagah `dev.*` / `Dev@12345`. Test-data freely banao
(DEV-marked) — owner ka standing permission hai; bas future-phase dependency
mat banana.

## Verification engine / Bharosa ka auzaar

`verification` app 5 read-only commands deta hai: `verify_factory`,
`verify_feature <slug>`, `verify_demo`, `verify_all`, `verify_production`.
Yeh tests ka replacement nahi — yeh **live world** ki correctness jaanchte
hain (goldens, manifests, contamination, settings sanity). Deploy ke baad
`verify_production` MANDATORY gate hai. Naya feature-world banaya to uske
checks registry mein add hote hain — pattern ke liye devseed/README.

## Knowledge graph & docs / Likhai ka anushasan

**DOCS-SYNC (standing owner rule, VERY IMPORTANT):** code change ⇒ usi
session mein uski md bhi update. Lookup order:
`docs/apps/<app>/GUIDE.md` → `config/<app>/README.md` →
[../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) canonical.

Machine side: `docs/knowledge_graph.json` estate ka nervous system hai —
```bash
env/bin/python scripts/build_knowledge_graph.py     # rebuild (deterministic)
env/bin/python scripts/validate_knowledge_graph.py  # invariants
env/bin/python config/manage.py knowledge_sync --deep  # 23 drift-detectors
```
Naya doc/model/service/url add kiya? → graph rebuild + sync clean karke hi
kaam ko "done" bolo (devseed guards warna battery mein pakad lenge — floors
by design). Expected clean state: `BLOCKER=0 / WARN=2` (do accepted WARNs).

## Coding rules that bite / Jo rules kaat te hain

- **Edit karo, rewrite nahi** — existing file par Edit tool/patch;
  wholesale rewrite review ko andha karta hai.
- **Frontmatter** har docs/*.md par (id/type/status/owner/scope/verified).
- **Templates:** `{# #}` sirf single-line; multi-line = `{% comment %}` —
  warna text page par leak hota hai (repeat-regression tha). Inline raw
  `#hex`/`font-size:Npx` mat likho — tokens use karo (`var(--…)`), ds-lint
  ratchet commit par pakadta hai.
- **Mobile-first is FUNCTIONAL requirement** — har naya UI mobile+tablet+
  desktop verify hue bina complete nahi (standing rule, strengthened
  2026-07-17). Worker pages phone par pehle designe hote hain.
- **FancySelect everywhere** — native `<select>` reject hota hai; dates =
  `data-fancy-date` (base.html ka MutationObserver auto-upgrade karta hai).
- **Migrations:** Django 5.0.1 mein CheckConstraint par `check=` use hota
  hai (`condition=` nahi) — repo ka documented gotcha.

## How to safely add a feature / Naya feature — 8 kadam

1. **Padho:** CLAUDE.md rules + us area ka GUIDE/README + relevant ADR
   (costing/money chhoo rahe ho to 0009/0011 MUST).
2. **Design:** kaunsi service extend hogi? Naya writer to nahi ban raha?
   (ban raha hai → STOP, owner review.)
3. **Model change?** Migration additive rakho; reverse path sochkar likho;
   money-adjacent table = owner-gated (campaign U14 tradition).
4. **Service pehle, view baad, template aakhir.** Har layer ka test us layer
   ke saath.
5. **Battery** (4-group law) + naye tests. Perf-sensitive page = query pin.
6. **Browser verify** — 3 widths (360/768/1280). Screenshot lo.
7. **Docs-sync same session** + graph/sync clean.
8. **Commit** conventional-message ke saath; hooks chalne do (ruff + ds-lint
   ratchet) — bulk-bypass sirf release-class commits ke liye tha.
