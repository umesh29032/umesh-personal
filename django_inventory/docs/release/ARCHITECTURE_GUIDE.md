---
id: release-architecture-guide
type: topic-canonical
status: active
owner: handwritten
scope: release-handbook
anchors: —
verified: 2026-07-19
---

# Architecture Guide — ERP v1.0 (the WHY behind every big decision)

> ADRs ([../adr/](../adr/)) binding decisions ka legal record hain. Yeh guide
> unka *teacher* hai — har decision ke peeche ki soch, Hinglish + English
> mein. Naye developer ko yeh samajh aana chahiye ki system aisa KYU hai,
> warna wo anjaane mein inhi rules ko todega.

## The one-paragraph philosophy / Ek paragraph mein poori soch

Yeh system ek asli factory ka **paisa** ginta hai. Isliye har design
decision ek hi sawaal se nikla hai: **"Agar 6 mahine baad koi number galat
dikhe, to kya hum raw tables se PROVE kar sakte hain ki sach kya hai?"**
Jahan bhi convenience aur provability ladte hain, provability jeetti hai.
Isi se aata hai: append-only ledger, single-writer services, frozen
snapshots, honest-NULL costing, aur "settlement hi money boundary hai".

## Decision 1 — Services own all writes; no signals (ADR-0001)

**English:** every multi-row write lives in `config/<app>/services/`; views
parse input and call exactly one service function. Django signals are
banned (zero receivers exist — verified at certification).

**Samjho aise:** signal ek chhupa hua side-effect hai — `save()` karo aur
kahin door kuch aur bhi ho gaya. Jab paise ka hisaab ho raha ho, "kahin aur
kuch aur" bhaari padta hai: debugging mein wo dikhata nahi, tests mein wo
chhoot jaata hai. Service function = ek darwaza, ek transaction, ek jagah
jahan poora business rule padha ja sakta hai. Isliye rule: **view sirf
parse karta hai, service sochti hai, model store karta hai.**

## Decision 2 — Single writer per money/audit table (ADR-0002)

**English:** `WorkerLedgerEntry` has exactly ONE writing function
(`ledger_service`); every `*History` table writes only via
`history_service`; advances, settlements, factory expenses — same pattern.

**Samjho aise:** agar ledger mein 10 jagah se rows ban sakti hain, to
"double credit kaise hua?" ka jawab dhundhne mein hafta lagega. Ek hi
darwaza ho to guard bhi ek hi jagah lagta hai (jaise double-credit guard,
amount>0 check). Certification mein yehi cheez **airtight** proved hui —
poore codebase mein WLE ki ek hi write-site hai, tests tak direct row nahi
banate.

## Decision 3 — Three-concept RBAC (ADR-0003)

```
 Role     = tum kaun ho          (super_admin / manager / worker / listing_team)
 Skill    = kis STAGE ko chhoo sakte ho   (cutting-master, stitching …)
 Sidebar  = kaunsa menu + URL khula hai   (SidebarItemRule + middleware)
```

**Kyu teen alag concepts?** Ek factory mein "worker" hona kaafi nahi batata
ki tum cutting kar sakte ho ya nahi — wo SKILL hai, role nahi. Aur menu
chhupa dena kaafi nahi hota (URL type karke koi bhi pahunch sakta hai) —
isliye `SidebarAccessMiddleware` menu-item aur uske URL ko **saath** mein
band karta hai. Views mein kabhi raw `is_superuser` check nahi —
`permission_service.user_has_role/user_has_perm` hi rasta hai, taaki policy
ek jagah rahe.

## Decision 4 — Settlement is the only money boundary (ADR-0007, "era-B")

**English:** production work creates *expected* earnings (frozen `expected_*`
snapshots = visibility for the worker); money books ONLY when a manager
finalizes an `AddaSettlement`. The ledger is append-only; corrections are
reversals, supersessions carry the chain.

**Samjho aise:** pehle system allocation ke waqt hi credit likh deta tha
(era-A). Problem: kaam baad mein badalta hai — alter aata hai, missing
nikalta hai, rate correct hota hai. Jo paisa pehle likh diya, use "un-likhna"
gadbad ka ghar hai. Isliye ulta kiya: **kaam ki ginti chalti rahe, paisa
sirf settlement par janme.** Ek rollback lever rakha hai
(`LEDGER_CREDIT_AT_ALLOCATION=True`) with a cross-era double-credit guard —
kyunki bhaari cutover mein wapas jaane ka tested rasta hona chahiye.
Four-way identity certification mein byte-exact nikli:
**ledger ≡ settlement total ≡ Σ items ≡ Σ earning-line snapshots.**

## Decision 5 — Cost truth: honest-NULL + one-rupee-once (ADR-0009)

**English:** material cost derives from raw tables at read time (verified kg
× the SOURCE roll's ₹/kg); an unpriced consumed roll makes the figure
INCOMPLETE (counted + flagged), never ₹0; a leftover reused by another Adda
carries its source price so every rupee of intake is counted exactly once;
material cost and full cost render as separate figures, never silently summed
with the payable-standard.

**Samjho aise:** costing mein sabse aasan jhooth hai "jo pata nahi use 0 maan
lo". 0 dikhte hi total believable lagta hai aur galat decision hota hai.
Humne ulta chuna: **adhura number = flagged number.** Aur "one-rupee-once"
ka matlab: kapda ek Adda se bach kar doosre mein laga to uska daam do jagah
na gine — source Adda apne remnant ka credit deta hai, consumer usi price par
intake ginta hai. Yeh identity test-pinned hai aur live bhi executed
(Σ periods ≡ Σ Addas).

## Decision 6 — Salary is factory-level, never per-Adda (ADR-0011)

**Samjho aise:** monthly-salary wala helper kisi ek batch ka cost nahi hai —
wo factory chalane ka kharcha hai. Agar salary ko Addas par baant do to har
batch ka cost "kitne batches the us mahine" par depend karega — jo costing ko
noise bana deta hai. Isliye: salary = `FactoryExpense` (monthly engine
generate karta hai), settlement lines mein monthly workers structurally
excluded (DB CHECK tak hai: salary template par worker FK zaroori).

## Decision 7 — Append-only history + soft-state (data principles)

**Samjho aise:** "kaam jo ho gaya" ko UPDATE karna history ko jhooth banana
hai. Isliye: ledger/history/audit tables mein rows kabhi edit nahi hoti
(certification ne 610 PRIMARY rows par 0 edits prove kiya — microsecond
insert-skew tak alag se explain hua). Worker chala gaya? `is_active=False`
— DELETE kabhi nahi, kyunki uske ledger rows PROTECT FK se latakte hain.
Identity permanence bhi isi ka hissa: Adda codes kabhi reuse nahi hote
(sequence mein gap dikhe to wo FEATURE hai, bug nahi — ADR-0010).

## Decision 8 — BOD is a window, never an engine

**Samjho aise:** owner-dashboard sabse aasaan jagah hai jahan "bas ek chhota
sa write" ghus jaata hai aur phir wahi dashboard alag numbers dikhane lagta
hai jo asli pages dikhate hain. Isliye `bod` app mein **models.py hi nahi
hai** — zero ORM writes, zero POST (certification mein grep-proven). Har
widget kisi existing service-truth ko hi render karta hai; naya KPI chahiye
to Widget Registry + Metric Ladder ke through aata hai.

## Decision 9 — Commerce boundary (ADR-0008) & growth fences (ADR-0006/0010)

**Samjho aise:** production models mein price/revenue fields daalna aasaan
hai aur wapas nikaalna namumkin. Isliye storefront (listing/catalog) aur
production ke beech deewar hai — production models mein zero commerce
fields (grep-certified). Multi-factory, barcode-e-commerce, piece-level
models — sab future ke liye **fence** kiye gaye hain ADRs mein: jab aayenge
to soch-samajh kar aayenge, chupke se nahi.

## Decision 10 — Dev/prod structural separation

**Samjho aise:** seeder (devseed) sirf `local.py` ke through installed hai —
production settings mein wo app **exist hi nahi karta**, isliye uske
commands wahan discoverable nahi (guard ka structural factor). Upar se
seeder sirf allowlisted scratch databases par chalta hai
(`inventory_seed_scratch_1/2`) — PRIMARY kabhi target nahi ban sakta.
`verification` app iska ulta hai: production-PRESENT by design, kyunki
`verify_production` deploy gate wahi hai — read-only, no models, no URLs.

## How the apps depend on each other / Import discipline

```
        core  ◀── sab (abstract bases)
   accounts  ◀── sab (User, roles)          [foundation: kisi domain app ko
                                              import NAHI karta — enforced]
 raw_materials ──▶ production ──▶ tracking   (upward reads, one-way)
        expense ◀── production (SWA facade — documented, future-redesign tagged)
        bod / patterns_ai / storefront: leaf apps, andar ki taraf read-only
```

`lint-imports` (import-linter) do contracts chalata hai: foundation purity
**ENFORCED** (build fail karta hai), acyclic-target **REPORT-ONLY by design**
— uski violation list hi documented coupling-worklist hai. Certification:
zero cycles; saare 22 runtime edges pehle se documented.

## Where to read the binding text

| Topic | Binding doc |
|---|---|
| The 11 decisions verbatim | [../adr/](../adr/) — 0009 + 0011 padhe bina costing/money design mat karo |
| Product truth (frozen) | [../PRODUCT_DESIGN_DOCUMENT.md](../PRODUCT_DESIGN_DOCUMENT.md) + amendment register |
| Settlement architecture deep-dive | [../ARCHITECTURE_V2.md](../ARCHITECTURE_V2.md) |
| Working rules (must-follow) | [../../CLAUDE.md](../../CLAUDE.md) |
