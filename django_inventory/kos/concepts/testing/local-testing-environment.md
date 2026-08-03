---
id: concept-local-testing-environment
type: concept
verified: 2026-07-27
knowledge_confidence: production_verified
answers: "My local database is full of old test junk — how do I get a CLEAN factory to hand-test on, without destroying what I already have?"
related: [concept-testing-strategy, feature-rbac-access, feature-cutting, concept-production-and-docker]
---

# Local Testing Environment — a clean factory in five minutes

> 📂 [Testing](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)

## Read this first: one command does everything

Forget every other command on this page. There is **one** tool:

```bash
./scripts/db.sh
```

Run it with no arguments and it prints its own help. Here is the whole thing:

| I want to… | Type this |
|---|---|
| **start testing from scratch (create + switch + login)** | `./scripts/db.sh fresh test_production` |
| **run the app** on whatever database I'm on | `./scripts/db.sh run` |
| **is this database ready to run a batch?** | `./scripts/db.sh check` |
| see my databases, what's in each, which I'm using | `./scripts/db.sh list` |
| which one am I on? | `./scripts/db.sh current` |
| **save-point before I test something risky** | `./scripts/db.sh branch before_settlement` |
| make an empty one (without switching) | `./scripts/db.sh new test_02` |
| switch to one | `./scripts/db.sh use test_02` |
| save a copy as a real file I keep | `./scripts/db.sh save` |
| see my saved copies | `./scripts/db.sh backups` |
| bring a saved copy back | `./scripts/db.sh restore <file> --into test_03` |
| delete one | `./scripts/db.sh delete test_02 --yes-delete test_02` |

You never type a database password — the tool reuses what `.env` already has.

### `list` tells you what each database IS

Five test databases with cryptic names is the same clutter problem again, so
`list` shows the contents of each:

```
 → inventory_db          26 MB    23 stages ·  19 products ·  28 addas · 106 users
   test_production       18 MB    21 stages ·   5 products ·   0 addas ·   0 users
```

0 addas + 0 users = an untouched fresh one. That one line tells you which
database is which without opening any of them.

### `check` — the tool tells YOU what is missing

Instead of reading a checklist and guessing:

```
$ ./scripts/db.sh check

   ✗  login (superuser)                          0 superuser(s)
   ✓  platform stages seeded                     21 stages, 24 access links
   ✓  product exists                             5 product(s)
   ✗  a RUNNABLE product (sizes + flow + rates)  0 runnable · not ready:
        3-PATTI (no sizes; 2 stage(s); unrated: cutting)
   ✗  cloth roll available                       0 roll(s)
   ✗  workers have skills                        0 user(s) with >=1 skill
```

Every line mirrors a row of
[docs/FRESH_DB_REQUIREMENTS.md](../../../docs/FRESH_DB_REQUIREMENTS.md) §3 —
which explains *why* each one is required and what breaks without it.

### `branch` — save-points for your data, like git branches

Setting up a product, its sizes, its flow with rates, cloth and workers is slow,
fiddly work. Do not throw it away to test one risky thing:

```bash
./scripts/db.sh branch before_settlement --use   # fork; you are now on the copy
# …test settlement, break things, make a mess…
./scripts/db.sh use test_production              # your setup is untouched
```

Branches **nest** — branch off a branch off a branch. Each one is simply a full
database, so there is no chain to break and nothing to merge.

> 💡 **Samjho aise:** Game mein **save point** jaisa. Mehnat se setup banaya
> (product, rates, cloth, workers) — ab kuch risky test karna hai? Pehle
> `branch` maar do. Test bigad gaya to koi baat nahi: purani wali DB waise ki
> waise padi hai. Branch **copy** hai, move nahi.

### The honest answer about "keeping my database in my project folder"

A very reasonable thing to want. But:

> ❌ **Postgres databases cannot live in your project folder.** They live inside
> Postgres's own storage (on this machine: `/var/lib/postgresql/14/main`), owned
> and managed by the Postgres program. Copying those files by hand corrupts them.
> This is not a limitation to work around — it is how the database protects your
> data from being half-copied.

**But the thing you actually want IS possible**, and this is how professionals do it:

> ✅ **Keep *backups* in your project folder.** `./scripts/db.sh save` writes a
> complete copy of a database into `db_backups/` as one `.sql` file. That file is
> yours: copy it, move it, email it, restore it on another machine. **That** is
> "my data, in my folder, under my control".

> 💡 **Samjho aise:** Database ek **chalta hua bank** hai — uski tijori bank ke
> andar hi rehti hai, aap use ghar nahi le ja sakte. Par aap **bank statement**
> (backup file) ghar rakh sakte ho, aur us statement se poora khaata dobara bana
> sakte ho. `db.sh save` wahi statement banata hai.

⚠️ `db_backups/` is **gitignored on purpose**. A dump contains real workers'
details and password hashes — it must never be committed. `.env.bak` too.

### Why you can create as many as you like

Postgres holds **many databases at once**, side by side, completely separate. So
yes — make `test_01`, `test_02`, `experiment_rates`, whatever. They cost only
disk space (~18 MB each when empty of business data). Switch between them freely;
the one you are not using is simply asleep.

### The safety promises (all tested)

- **Deleting takes a backup FIRST**, automatically. So even a delete is undoable.
- It **refuses to delete the database you are currently using** — you must switch
  away first, which means you cannot destroy your own working data by reflex.
- **Delete needs the name typed twice** (`delete x --yes-delete x`), so it can
  never happen by muscle memory.
- It **refuses to overwrite** an existing database.
- It refuses invalid names and tells you the rule (lowercase, numbers, `_`).

### The name guard, and why it only applies to `delete`

`delete` refuses names that look live (`prod`, `production`, `live`) — **but only
when nothing marks the name as disposable.** A name containing `test`, `dev`,
`local`, `tmp`, `scratch`, `sandbox`, `demo`, `staging`, `copy` or `rehearsal`
wins, so `test_production` ("my rehearsal of production") is perfectly allowed:

```
./scripts/db.sh new test_production            ✓ fine — creating destroys nothing
./scripts/db.sh delete test_production …        ✓ allowed — "test" marks it disposable
./scripts/db.sh delete inventory_production …   ✗ refused — do that by hand in psql
```

> 💡 **Samjho aise:** Sochne ka tareeka yeh hai — **banane se kuch nahi bigadta,
> mitane se bigadta hai.** Isliye pehra sirf *delete* pe hai, `new` pe nahi.
> `new` pe naam ki rok lagana bekaar tang karna tha, suraksha nahi.

**Why this is worth understanding** (it is a real engineering lesson, not a
config detail): a safety check that fires on the *safe* operation trains you to
ignore it. Then it is noise when it fires on the dangerous one. **Put the guard
on the irreversible verb only** — here, dropping. This tool originally got that
wrong and refused `test_production` on create; the fix was to remove the guard
from `new` entirely and make it smarter on `delete`.

---

## Absolute-beginner on-ramp (start here if you've never done this)

**First, the one idea that makes everything else make sense:**

> Your data does **not** live in the project folder. It lives in a separate
> program called **PostgreSQL** ("Postgres"), which is running quietly on your
> machine. Postgres can hold **many databases** at once, side by side, each one
> completely separate. Your project currently uses one called `inventory_db`.
> The project folder only holds *code*; the code just asks Postgres "give me the
> database named X".

> 💡 **Samjho aise:** Postgres ek almirah hai. Us almirah mein kai alag-alag
> **drawers** ho sakte hain. `inventory_db` ek drawer hai jisme aapka teen mahine
> ka kaam pada hai. Hum us drawer ko **haath nahi lagayenge** — hum ek **nayi
> khaali drawer** banayenge aur project se kahenge "ab is wali ko kholo".

### "I switched database and now I can't log in" — the #1 lost moment

*(Real question, 2026-08-01: "new db means 0 users, so how can we log in? Did we
already define the superadmin email/password somewhere? Is the superadmin
Django-project-oriented?")*

**The one idea:**

> **Users are DATA, not CODE.** The superadmin lives *inside* the database — in a
> table called `accounts_user` — exactly like products and addas do. A new database
> has no users for the **same reason** it has no addas: nobody has put any in yet.

**💡 Samjho aise:** Naya database = **nayi khaali dukaan**. Building ban gayi,
shelves lag gaye — par andar kuch nahi. Na saaman, na staff, **na chaabi**. Purani
dukaan ki chaabi is nayi dukaan mein **nahi lagegi**, kyunki taala hi naya hai.
Chaabi dukaan ke *andar* rakhi hoti hai, aapki jeb mein nahi.

| CODE — identical for every database | DATA — different in every database |
|---|---|
| Django + your Python files | 👤 **users, including the superadmin** |
| the login page itself | 📦 products · addas · cloth |
| `scripts/db.sh` | 💰 money · ledger |
| — | 🔧 stages · skills |

**Switching database = pointing the same machinery at a different factory's records.**

Three answers to the three things people assume:

- **The superadmin is not "part of Django".** Django is the *machinery*. The
  superadmin is a **row in a table** in whichever database `.env` points at.
- **There is no login in `.env`.** `.env` says *which database to talk to* and the
  password for **Postgres itself**. It contains **no user accounts**. (People open
  `.env` looking for the admin password — it was never there.)
- **`db.sh use` already warns you**: *"This database has NO LOGIN yet."* That line is
  not an error; it is the honest state of a brand-new factory.

**The fix — 3 steps:**

```bash
env/bin/python config/manage.py createsuperuser --settings=config.settings.local
```
It asks for **email**, then **password twice**. The password **does not appear as you
type** — that is normal, the terminal is not frozen. Expected:
`Superuser created successfully.`

```bash
./scripts/db.sh check
```
Expected: `✓  login (superuser)      1 superuser(s)` — it said `✗ 0 superuser(s)` before.

```bash
./scripts/db.sh run     # then log in at /app/login/password/
```

**The confusing bits, named:**

- **Every database needs its own login.** Create one in `test_from_zero` and
  `test_production` still has none. Separate factories, separate keys.
- **`inventory_db` already has ~106 users**, which is why this never came up before.
- **Restart the server after `db.sh use`** — a running server holds its old connection.
- `db.sh list` showing `0 users` is your proof you are on a fresh one.

**The undo:** `./scripts/db.sh use inventory_db` — back to your real data and its
users. Nothing done in a `test_*` database can touch it.

---

## 🔬 Behind the scenes — how Django actually finds your database

*(Every line number below is clickable. Open the file, read the line, come back.
This is the whole mechanism — there is no hidden magic left after this.)*

### The four layers (get this and everything else follows)

```
┌──────────────────────────────────────────────────────────────┐
│  PostgreSQL SERVER   one program, running on your machine    │
│  (listening on port 5432)                                    │
│                                                              │
│   ┌────────────────┐  ┌────────────────┐  ┌───────────────┐  │
│   │  DATABASE      │  │  DATABASE      │  │  DATABASE     │  │
│   │  inventory_db  │  │ test_from_zero │  │test_production│  │
│   │                │  │                │  │               │  │
│   │  ┌──────────┐  │  │  ┌──────────┐  │  │               │  │
│   │  │  TABLE   │  │  │  │  TABLE   │  │  │   …           │  │
│   │  │accounts_ │  │  │  │accounts_ │  │  │               │  │
│   │  │  user    │  │  │  │  user    │  │  │               │  │
│   │  ├──────────┤  │  │  ├──────────┤  │  │               │  │
│   │  │106 ROWS  │  │  │  │ 0 ROWS   │  │  │               │  │
│   │  │(logins)  │  │  │  │(no login)│  │  │               │  │
│   │  └──────────┘  │  │  └──────────┘  │  │               │  │
│   └────────────────┘  └────────────────┘  └───────────────┘  │
└──────────────────────────────────────────────────────────────┘
        ▲                       ▲
        │                       │
   your real work          you are here
```

**Server** holds many **databases**. Each database holds **tables**. Each table holds
**rows**. Your login is **one row** in the `accounts_user` table — verified live:

```
table       : accounts_user
login field : email
rows        : 0 user(s) in test_from_zero
```

> 💡 **Samjho aise:** Postgres = **poori building**. Har database = **ek flat**. Har
> table = **flat ke andar ek almari**. Har row = **almari mein ek file**. Aapka login
> ek *file* hai, `accounts_user` almari mein, `test_from_zero` flat ke andar. Doosre
> flat mein wo file nahi hai — kyunki aapne wahan rakhi hi nahi.

### The connection chain — 5 hops, all clickable

```
  YOU type:  env/bin/python config/manage.py runserver
                        │
   ① ────────────────── ▼ ──────────────────────────────────────────
      config/manage.py:9
      os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                            'config.settings.local')
      → "read my settings from config/settings/local.py"
                        │
   ② ────────────────── ▼ ──────────────────────────────────────────
      config/settings/base.py:16
      from decouple import config
      → the tool that READS THE .env FILE
                        │
   ③ ────────────────── ▼ ──────────────────────────────────────────
      config/settings/base.py:168
      'NAME': config('DB_NAME', default='inventory_db')
      → "which database? whatever DB_NAME says in .env"
                        │
   ④ ────────────────── ▼ ──────────────────────────────────────────
      .env  (NOT in git — your machine only)
      DB_NAME=test_from_zero
      → THIS ONE LINE decides everything
                        │
   ⑤ ────────────────── ▼ ──────────────────────────────────────────
      PostgreSQL on localhost:5432  →  opens database "test_from_zero"
```

| Hop | File | What it decides |
|---|---|---|
| ① | [manage.py:9](../../../config/manage.py#L9) | which settings file to use |
| ② | [base.py:16](../../../config/config/settings/base.py#L16) | that `.env` is the source of config |
| ③ | [base.py:168](../../../config/config/settings/base.py#L168) | `DB_NAME` names the database |
| ③b | [base.py:165-173](../../../config/config/settings/base.py#L165-L173) | the whole `DATABASES` dict (user, password, host, port) |
| ③c | [base.py:173](../../../config/config/settings/base.py#L173) | `CONN_MAX_AGE: 600` — reuse a connection for 10 min instead of reconnecting on every request |
| ④ | `.env` | **the actual answer** — one line, `DB_NAME=` |
| ⑤ | Postgres :5432 | hands over that database |

**So "switching database" is literally: change one line in `.env`.** Nothing else moves.
Not the code, not the tables' shapes, not Django.

### What `./scripts/db.sh use` physically does

It is not magic — it is a text edit on one line, with a backup first:

| Line | What happens |
|---|---|
| [_db_admin.py:447](../../../scripts/_db_admin.py#L447) | `cmd_use()` starts |
| [_db_admin.py:449](../../../scripts/_db_admin.py#L449) | refuses if that database does not exist (so you cannot point at nothing) |
| [_db_admin.py:457](../../../scripts/_db_admin.py#L457) | **writes `.env.bak` first** — your undo |
| [_db_admin.py:461-462](../../../scripts/_db_admin.py#L461-L462) | finds the `DB_NAME=` line and rewrites it |

That is the entire "switch". Which is why the tool then shouts **"RESTART the server"** —
see the next box for why that is unavoidable.

### ⚠️ Why you MUST restart the server after switching

```
  server START ──► reads settings ──► reads .env ──► opens DB ──┐
                        (ONCE)                                  │
                                                                ▼
  every request afterwards ─────────────────► reuses that open connection
                                              (CONN_MAX_AGE = 600s, base.py:173)
```

Django reads settings **once, at start-up**. A running server is already holding a
connection to the *old* database. Editing `.env` under a running server changes
nothing it can see — you would be reading the old factory and thinking the tool
failed.

**Rule: `db.sh use` → Ctrl+C → start again.** Every single time.

### So how does ONE user log in after switching?

Follow the row, not the code:

```
  1. createsuperuser        →  INSERT a row into accounts_user
                               (in the CURRENT database only)
                                        │
  2. you type email+password on /app/login/password/
                                        │
  3. Django: SELECT * FROM accounts_user WHERE email = <what you typed>
             ─ base.py tells it WHICH database to run that SELECT in
                                        │
  4. row found?  ──NO──►  "invalid login"   ← this is your 0-users case
                 ──YES─►  compare the password against the stored HASH
                                        │
  5. hash matches ──►  logged in
```

- The login field is **email**, not a username —
  [accounts/models.py:205](../../../config/accounts/models.py#L205) `USERNAME_FIELD = "email"`.
- The User model itself:
  [accounts/models.py:116](../../../config/accounts/models.py#L116).
- **Your password is never stored.** Only an **Argon2 hash** of it. That is why nobody —
  including you — can read a password out of the database, and why a stolen dump is
  survivable (sql_course ch 22).

**Therefore:** a new database = no row in `accounts_user` = step 4 finds nothing = you
cannot log in **until you create that row**. There is no project-wide login, because a
login is data and data lives in one database at a time.

### The commands, and what each one really is

| You type | What it actually is | Built-in or ours? |
|---|---|---|
| `createsuperuser` | an `INSERT` into `accounts_user` | **Django built-in** |
| `migrate` | creates/updates the **tables** (shapes, not data) | **Django built-in** |
| `runserver` | the dev web server | **Django built-in** |
| `shell` | a Python prompt with your models loaded | **Django built-in** |
| `dbshell` | drops you into raw `psql` on the current DB | **Django built-in** |
| `seed_master_data` | inserts the 21 stages, skills, access links | **ours** ([source](../../../config/production/management/commands/seed_master_data.py)) |
| `verify_production` | asserts the data is sane | **ours** |
| `db.sh new/use/save/…` | wraps `createdb`/`dropdb`/`pg_dump` + the `.env` edit | **ours** ([source](../../../scripts/_db_admin.py)) |

> 💡 **Samjho aise:** Django ke saath kai **ready-made commands** aate hain
> (`migrate`, `runserver`, `createsuperuser`). Humne apne factory ke liye kuch **apne**
> banaye (`seed_master_data`, `verify_production`). Dono ek hi tareeke se chalte hain:
> `manage.py <command>`. Naya command banana = `management/commands/` mein ek file.

### See it with your own eyes (safe, read-only)

```bash
# which database am I on, according to .env?
./scripts/db.sh current
```
Expected: `test_from_zero`

```bash
# ask Django itself — does it agree?
env/bin/python config/manage.py shell --settings=config.settings.local -c \
  "from django.conf import settings; print(settings.DATABASES['default']['NAME'])"
```
Expected: `test_from_zero` — the same name. **Now you have proved the chain yourself.**

```bash
# go into raw SQL and count the logins
env/bin/python config/manage.py dbshell --settings=config.settings.local
```
then at the `psql` prompt:
```sql
SELECT count(*) FROM accounts_user;   -- 0 on a fresh database
\dt                                   -- list every table
\q                                    -- quit
```

That `SELECT` is the exact query Django runs at step 3 above. Nothing is hidden from you.
> Purani drawer waise ki waise, band, safe.

**Which drawer the app opens is decided by ONE line** in a file called `.env`
in the project root:

```
DB_NAME=inventory_db
```

Change that line → app opens a different drawer. Change it back → old drawer
again. That is the entire "switch". Nothing is copied, moved, or deleted.

### The steps, one at a time (with what you will SEE)

**Step 0 — open a terminal in the project folder**

```bash
cd ~/umesh-personal/django_inventory
```
Every command below runs from here. If you get "file not found", you are almost
certainly in the wrong folder.

**Step 1 — check which database you are on right now**

```bash
./scripts/db.sh current
```
- You will see: `inventory_db`
- **Keep this command.** Any time you feel lost, run it — it always tells you the
  truth about which drawer is open. It is the single most useful line on this page.
- Want the full picture (all databases, sizes, which is active)?
  `./scripts/db.sh list`

**Step 2 — create the new empty database**

```bash
./scripts/db.sh new test_01
```
- `test_01` is just a name you chose. Lowercase letters, numbers, underscores —
  no spaces, no dashes, no capitals (the tool will tell you if you slip).
- It creates the database, builds every table inside it, then fills in the factory
  setup (stages, skills, who may do what).
- Takes 30–60 seconds and prints many lines like `Applying production.0041... OK`.
  **That is normal** — it is building tables one by one.
- Ends with `✓ READY: test_01`.

**Step 3 — point the app at it**

```bash
./scripts/db.sh use test_01
```
- This edits the one line in `.env` for you and keeps a safety copy at `.env.bak`.
- *(Doing it by hand instead is fine too: open `.env`, change
  `DB_NAME=inventory_db` to `DB_NAME=test_01`, save. The leading dot means `.env`
  is a hidden file — in a file manager you may need "show hidden files". Change
  nothing else.)*

**Step 4 — confirm the switch actually happened**

```bash
./scripts/db.sh current      # must now print: test_01
```
If it still says `inventory_db`, the switch did not take — run Step 3 again.

**Step 5 — create your login**

```bash
env/bin/python config/manage.py createsuperuser
```
- A brand-new database has **zero users** — without this you cannot log in at all.
- It asks for email, then password twice. **The password stays invisible while you
  type** — that is normal, keep typing.
- If it says the password is too simple it still offers
  `Bypass password validation? [y/N]` — type `y` for local testing.

**Step 6 — start the app**

```bash
env/bin/python config/manage.py runserver --settings=config.settings.local
```
Open <http://127.0.0.1:8000> and log in. Leave that terminal running; **Ctrl+C**
stops the server.

### Going back to your old data

```bash
./scripts/db.sh use inventory_db
```
- **Stop the server (Ctrl+C) and start it again**
- Everything is exactly as you left it — nothing was ever deleted

### Deleting a database you're finished with

```bash
./scripts/db.sh use inventory_db                       # 1. switch AWAY from it first
./scripts/db.sh delete test_01 --yes-delete test_01    # 2. name typed twice, on purpose
```
- It **takes a backup before deleting**, automatically. So even this is undoable:
  `./scripts/db.sh restore <file> --into test_01`
- You must type the name twice. That is not bureaucracy — it makes an accidental
  delete impossible to do by muscle memory.

> ⚠️ The server reads `.env` **only when it starts**. After editing `.env`, always
> restart — otherwise you are looking at the old database and wondering why
> nothing changed. This confuses everybody once.

### Why you cannot break anything here

- `new_local_db.sh` contains **no delete or drop command at all**. Its only power
  is to create. That is a design choice, not a promise.
- It refuses in three situations (all tested):
  - a production-looking name → *"REFUSED: looks like a production database name"*
  - a name that already exists → *"REFUSED: already exists — this script never overwrites"*
  - the database you are on → *"REFUSED: pick a NEW name so your current data stays safe"*
- Switching is one line of text. Nothing is copied, moved or erased.
- Worst case you create a database you don't want; it sits there harmlessly.

### The little bit of SQL you actually need

> 🎓 **Want the whole thing, not the little bit?** A full course taught from
> THIS project's own tables — with interviewer questions and free links — lives
> at [docs/sql_course/](../../../docs/sql_course/00_COURSE_OVERVIEW.md) — 25 chapters,
> basic to advanced, every example a real query on YOUR data. Practice branch first:
> `./scripts/db.sh branch sql_practice --use`.

Honestly — **almost none.** Django writes the SQL for you. Two ideas are enough:

- A **database** is a collection of **tables**. A table is like one Excel sheet:
  rows and columns. Your Addas live in a table called `production_adda`.
- **`migrate`** is the Django command that creates and updates those tables to
  match the code. You never write `CREATE TABLE` yourself.

If you ever want to look inside with real SQL:

```bash
env/bin/python config/manage.py dbshell --settings=config.settings.local
```
This opens Postgres' own prompt, already connected to whichever database `.env`
points at (so no password typing). Useful there:

| Command | What it does |
|---|---|
| `\dt` | list all tables |
| `\l` | list all databases (all your drawers) |
| `SELECT count(*) FROM production_adda;` | count Addas — SQL lines end with `;` |
| `\q` | quit |

> 🛟 **Safety rule while learning:** only run `SELECT`, which *reads*. Avoid
> `DELETE`, `DROP` and `UPDATE` — they change data and there is no undo.

---

> 📋 **The checklist of everything a new database needs** lives in
> [docs/FRESH_DB_REQUIREMENTS.md](../../../docs/FRESH_DB_REQUIREMENTS.md) — a LIVING
> document. When your testing finds something a fresh database was missing, add it
> there the same day. That file is what makes a future factory setup boring.

## What a database does NOT contain (read before you trust a backup)

Four facts, all verified in this repo's code, that surprise everyone once:

**1. Uploaded photos and videos are NOT in the database.**
The database stores only the *path* (a piece of text like
`cutting_pattern/3-PATTI-001/photos/x.jpg`). The actual file lives on disk at
**`config/media/`** — note: `config/media/`, *not* a `media/` folder at the repo
root. 13 upload fields across 5 apps (pattern photos/videos, profile pictures,
advance receipts, storefront images, pattern-AI captures) all point there.

> 💡 **Samjho aise:** Database ek **register** hai jisme likha hai *"photo almirah
> #3 mein hai"*. Photo khud register mein nahi hai — almirah mein hai. Register ka
> backup lene se photo ka backup **nahi** hota.

Consequences:
- `db.sh save` copies the register, **never the almirah** — a `.sql` file restored
  on another machine gives you a factory whose every photo link is dead (harmless,
  looks broken). The **production** backup (`deploy/backup.sh` → restic) does
  include both — DB dump + media — which is exactly why it exists.
- **All your databases share the ONE `config/media/` folder.** Adda codes repeat
  across databases (`3-PATTI-001` exists in each fresh DB), so two databases'
  files sit in the same directories.
- **Deleting a pattern photo in ANY database deletes the real file** — and if
  another database's rows (or an old backup) pointed at that same file, their
  link is now dead. Deleting a photo on a test DB can therefore blank a photo
  in a *restored copy* later. On a test database, prefer leaving photos alone.
- `db.sh delete` removes a database but **never** its uploaded files — they stay
  in `config/media/` as harmless orphans.

**2. Your login session lives INSIDE the database.**
`SESSION_ENGINE = db` — so **every `db.sh use` logs you out**. That is normal,
not a bug: your browser's cookie points at a session row in the *old* database.
Log in again. (Flip side: restoring an old backup resurrects the sessions that
existed when it was taken — they expire after 8 hours anyway.)

**3. The login rate-limit lives in NEITHER place.**
Wrong-password lockouts are counted in the process cache. Locally that means:
locked yourself out during testing? **Restarting `runserver` clears it** — no
database switch needed, and switching databases does NOT clear it.

**4. Backup files only travel one way between Postgres versions.**
Your laptop runs Postgres **14**; the production server runs **16**. A dump made
on 14 restores fine on 16 (old → new = OK). A dump made on 16 generally will
**not** restore on 14 (new → old = expect errors). And the server's restic
backups use `pg_dump -Fc` (a compressed format) — those need `pg_restore`, not
`psql`, and your local v14 `pg_restore` cannot read a v16 archive. Practical
rule: **rehearse restores on the machine that will do the restoring.**

> ⚠️ **One more trap, now guarded:** if `DATABASE_URL` is set in `.env`, Django
> ignores `DB_NAME` completely — so every `db.sh` command would act on the wrong
> database. The tool now refuses to run at all in that case and tells you to
> comment the line out. `DATABASE_URL` belongs on the server, never on your laptop.

## This is also your go-live dress rehearsal 🎭

Here is the part that makes this more than a cleanup trick:

> **A fresh local database is the SAME THING as a fresh production database.**
> Same migrations, same seed, same emptiness. So whatever you see on your laptop
> after `new_local_db.sh` is *exactly* what you will see on the server on day one.

That gives you three things for free:

- **You find out what the live app looks like with no data** — which screens are
  empty, which say "no products yet", where a new user gets stuck. Better to meet
  those on your laptop than on the day the factory is waiting.
- **The order you enter data locally becomes your go-live checklist.** Whatever
  you had to create before an Adda would start, you will have to create on the
  server too — in the same order.
- **Mistakes are free here.** Enter a wrong rate locally, see what it does to the
  settlement, throw the database away. On the live server that same wrong rate is
  a real worker's real wages.

> 💡 **Samjho aise:** Ye **rehearsal** hai — shaadi se pehle ki practice.
> Local wali khaali DB aur live wali khaali DB **bilkul ek jaisi** hoti hain.
> To yahan pe practice karlo: kya-kya banana padta hai, kis order mein, kahan
> atakte ho. Jab asli server pe jaoge, tab tumhe already sab pata hoga — pehli
> baar wahan soch-soch ke nahi karna padega.
>
> Aur sabse badi baat: **yahan galti free hai.** Galat rate daal do, dekho kya
> hota hai, DB phenk do. Live pe wahi galat rate kisi worker ki asli tankhwah hai.

**Do this while you rehearse:** keep a notepad open and write down every single
thing you had to create before the first Adda would run. That list *is* your
go-live data plan. The order is in
[How to hand-test a factory from zero](#how-to-hand-test-a-factory-from-zero)
below — follow it, and note anything that surprised you.

## Business Purpose

After a few months of building, the development database stops being a place you
can *judge* anything. Ours reached 19 products, 26 Addas and 106 users. Open any
list and it is noise: which Adda was the real test? which worker did I create for
what? A hand-audit becomes impossible, not because the software is wrong, but
because **you cannot see the signal**.

The instinct is to wipe the database. That instinct is wrong, and expensive: your
old Addas are the only record of journeys you have already proved (settled money,
completed flows, historical bugs). The professional move is to **stand up a second,
empty database beside the old one** and point the app at it. Nothing is destroyed;
you switch back with a one-line edit.

## 💡 Samjho Aise

Ek hi workbench pe teen mahine ka saamaan pada hai — ab usi table pe naya kaam
karoge to kuch dikhega hi nahi. Do options hain: (1) sab kuch phenk do, ya
(2) **doosri khaali table lagao**, uspe naya kaam karo, aur purani table waise ki
waise rehne do.

Hum hamesha (2) karte hain. Purana kaam bhi bacha, aur naya kaam saaf bhi.
`.env` mein ek line badli — table badal gayi. Wapas jaana ho? Line wapas badal do.

## Mental Model

> **A database has two kinds of rows, and only one of them should ever be seeded.**
>
> - **Platform master data** — stages, skills, which skill may open which stage,
>   machine types, stage categories. Identical in every factory. The app is
>   *unusable* without it. → **seed it, automatically.**
> - **Business data** — products, size charts, workflow rates, cloth, rolls,
>   Addas, workers. Different in every factory and every season. Seeding it means
>   inventing someone's money. → **you enter it, by hand, through the UI.**
>
> A fresh database should arrive at exactly that line: everything platform,
> nothing business.

## The three commands

```bash
# 1. Create a clean database beside your current one (destroys NOTHING)
./scripts/db.sh new test_01

# 2. Point the app at it
./scripts/db.sh use test_01

# 3. Make your login, then run
env/bin/python config/manage.py createsuperuser
env/bin/python config/manage.py runserver --settings=config.settings.local
```

To return to your old data: `./scripts/db.sh use inventory_db`. That is the whole
"reset" — no destructive step anywhere in the loop.

> `scripts/new_local_db.sh` still works but now simply forwards to
> `db.sh new` — **one tool, so there is only ever one thing to remember.**

### What you get, and what you deliberately do not

| Seeded for you (platform) | Count | You create by hand (business) |
|---|---|---|
| Stage categories | 5 | Products |
| Machine types | 5 | Product sizes |
| Skills | 10 | Workflow stages + cost rates |
| Stages | 21 | Cloth types / colours / storage |
| Stage → skill access links | 24 | Cloth rolls |
| | | Users (beyond your superuser) |
| | | Addas |

## Technical Deep Dive

**The seed command.** `production/management/commands/seed_master_data.py`:

```bash
python manage.py seed_master_data --dry-run        # show what WOULD change
python manage.py seed_master_data                  # apply
python manage.py seed_master_data --repair-access  # also ADD missing skill links
```

Two guarantees make it safe to run **on the live server**, not just locally:

1. **Idempotent** — natural-key `get_or_create`. Run it a hundred times; after
   the first it creates nothing. Proven: two consecutive runs on a fresh database
   both end at 21 stages / 24 links.
2. **Never overwrites your edits** — an existing row is left exactly as it is.
   Renamed a stage, re-pointed its machine type, changed who can access it: all
   preserved. The seed only fills in what is *missing*.

This is why it carries no DEBUG guard, unlike `devseed`. `devseed` writes fake
*business* data and is hard-blocked outside development; `seed_master_data`
writes only platform reference rows, so it is exactly what a production deploy
needs.

**Why this had to exist.** Migrations alone seed **4 of 21 stages** and **2 of 10
skills**. Everything else lived only as hand-made rows in one developer's
database. A fresh production deploy therefore came up unable to run a single
Adda — no Overlock, no Checking, no Packing, and no `Stage.access_by_skill` rows,
so no worker could open any stage at all. Found by AUDIT-2
([report](../../../docs/AUDIT2_PRODUCTION_ACCESS_FINANCIAL_2026_07_27.md)).

**The subtle one.** A stage can *exist* while missing an access link — the
migration-seeded `cutting` stage had `cutting_master` but not
`cutting_master_helper`, so a helper silently could not open Cutting. The stage
looked present, so nothing complained. `seed_master_data` now detects that case
and prints a loud `ACTION NEEDED` block naming the flag that repairs it.

## Engineering Thinking

**Why a management command and not a data migration?** A data migration runs
once per database, automatically, which is attractive. But it also runs *inside*
the migration graph, where a mistake is far more expensive to undo, and this
project gates every migration behind explicit owner approval. A command is
re-runnable, dry-runnable, inspectable, and can be re-executed after someone
edits a stage by hand. Deploy calls it once from the entrypoint; a human can call
it any time. Same effect, far less blast radius.

**Why "create beside" rather than "drop and recreate"?** Because destructive
tooling gets used at 2am. The project already proves the point: `devseed
reset_demo` *can* drop a database, and it is fenced behind a closed allowlist of
two names plus a per-name exact-string confirmation flag. `new_local_db.sh` needs
none of that armour — it has no delete path to begin with, so it cannot be
misused. **The safest destructive command is the one that does not exist.**

Its three refusals, all proven:

```
REFUSED: 'my_production_db' looks like a production database name.
REFUSED: database 'audit2_scripttest' already exists — this script never overwrites.
REFUSED: 'inventory_db' is the database you are already using. Pick a NEW name.
```

## How to hand-test a factory from zero

*(This same list is your **go-live data checklist** — see the rehearsal section
above. Whatever you create here, you will create on the live server too.)*

Fresh database, in the order the factory itself works. **Nothing later works
until the thing above it exists** — that is why the order matters, not taste:

| # | What you create | Where | Why it must come first |
|---|---|---|---|
| 1 | **Master data** — already seeded | check `/production/stages/` shows 21 | nothing can run without stages + skills |
| 2 | **Product** + its **sizes** | Products | an Adda is *a batch of a product* |
| 3 | **Workflow** — which stages, in what order, **and the ₹ rate per stage** | product's flow editor | no flow = no stages to work · no rate = no money |
| 4 | **Cloth** — type → colour → storage → **roll** | Raw Materials | Layering needs a real roll to lay |
| 5 | **People** — users with **roles**, workers with **skills** | Users | a worker without the matching skill is refused *by design* |
| 6 | **Adda** — start one, walk it stage by stage | Production | this is the actual test |
| 7 | **Settle** — then check the ledger total | Expense | money is the last truth |

**Step 6 in detail** (the loop you repeat per stage):
assign the roster (manager) → worker logs in on their own account and reports
their quantity → management verifies and completes the stage → next stage opens.

> ⚠️ **Step 3 is where money is decided.** The rate you type there is frozen onto
> the work when it happens. A wrong rate is not a display bug — it is a wrong wage.
> Locally: type a deliberately silly rate once and watch it flow to the settlement.
> Understanding that link on your laptop is worth more than reading ten pages.

**Two things a fresh database will teach you immediately:**

- You cannot log in until you run `createsuperuser` — a new database has **zero
  users**. This is the single most common "is it broken?" moment.
- You cannot start an Adda until steps 2–5 all exist. If the button refuses,
  the answer is almost always "something above it is missing", not a bug.

## Testing app by app on fresh databases (the owner's plan, 2026-08-01)

**One idea first:** you do **not** want a fresh database per app. Most apps sit on
top of setup that earlier apps create, so a truly fresh database per app means
re-typing the product, flow, rates, cloth and workers **every time**. Instead:
**build the setup once, save a checkpoint, and restore that checkpoint per app.**

**💡 Samjho aise:** ek naya database = **khaali dukaan**. Har app ke liye nayi khaali
dukaan lena matlab har baar shelf, saaman, staff — sab dobara lagana. Bekaar mehnat.
Isliye: **ek baar dukaan poori set karo, uska photo (checkpoint) le lo**, aur har app
test karne se pehle wahi photo wapas laga do. Dukaan hamesha same halat mein, test
hamesha saaf.

### The tiers — what each app actually needs

| Tier | Apps | Setup needed |
|---|---|---|
| **0** | `learning` (`/learn/`) · `storefront` (public site) | **nothing** — a bare fresh DB is fine |
| **1** | `accounts` (login, roles, users) · `inventory` (dashboards, access control) · `machines` | a **login** only (master data is already seeded) |
| **2** | `raw_materials` (cloth → roll) | + product exists |
| **3** | `production` (the big one) | + sizes, flow **with ₹ rates**, roll, workers **with skills** |
| **4** | `tracking` (barcodes/history) · `expense` (settlement, ledger) | + a batch actually worked through |
| **5** | `bod` · `verification` | read-only over everything above |
| — | `patterns_ai` | independent; needs a pattern image, nothing else |

**So the order is: 0 → 1 → 2 → 3 → 4 → 5.** Not preference — dependency. Tier 4 has
nothing to show until tier 3 has produced something.

### The checkpoint workflow (this is the time-saver)

```bash
# 1. one fresh factory to work in
./scripts/db.sh fresh test_apps
```
Expected: `✓ READY: test_apps` and, from the seeder,
`NOW IN THIS DATABASE: … 21 stages (expected 21)`.

```bash
# 2. is it actually ready? (honest checklist, not a guess)
./scripts/db.sh check
```
Expected: every line `✓` except the ones you have not done yet. It names what is
missing and points at `docs/FRESH_DB_REQUIREMENTS.md §3`.

```bash
# 3. do the tier 0-3 setup ONCE in the browser (product → sizes → flow+rates →
#    cloth roll → users with roles → workers with skills), then freeze it:
./scripts/db.sh save
```
Expected: `✓ saved (… MB)` and a filename under `db_backups/`. **That file is your
checkpoint.**

```bash
# 4. before EACH app's test, get back to that exact state:
./scripts/db.sh restore <that_file>.sql --into test_expense
./scripts/db.sh use test_expense
```
Now test one app, make any mess you like, and repeat step 4 with a new name for the
next app. Every app starts from identical, known data — which is what makes a
result mean something.

### What "working" looks like, per app

| App | The one thing to prove |
|---|---|
| `accounts` | a worker logs in on their **own** account and sees only their own work |
| `inventory` | hiding a menu item also **blocks its URL** (paste the URL directly — it must refuse) |
| `machines` | assign a machine to an operator, then check the possession window |
| `raw_materials` | a roll's remaining length **drops** after layering consumes it |
| `production` | one stage: assign roster → worker reports → management verifies → next stage opens |
| `tracking` | a barcode scan lands on the right batch, and history is **append-only** |
| `expense` | settle, then confirm **cost == earnings** and the ledger total moves by exactly that |
| `bod` | a money tile equals the page it links to (this is the cross-check that caught a real bug) |

### The undo — always available

```bash
./scripts/db.sh use inventory_db      # back to your real data, any time
./scripts/db.sh list                  # "→" shows which one you are on
```
Nothing you do in a `test_*` database can touch `inventory_db`. And `delete` takes a
safety backup **before** deleting, so even a wrong delete is recoverable.

### The confusing bits, named

- **A fresh database has ZERO users.** You cannot log in until `createsuperuser`
  (or `db.sh fresh`, which does it for you). This is the #1 "is it broken?" moment.
- **A refused button is usually missing setup, not a bug.** Cannot start an Adda?
  Something in tiers 2–3 is missing. `db.sh check` will say which.
- **A worker with no matching skill is refused *by design*.** Access to a stage =
  **skill ∩ assignment**. The refusal message looks like a bug and is not.
- **`db.sh list` counts are your truth.** `0 addas · 0 users` = untouched fresh.
- **⚠️ Rename a stage and the old name sticks until you restart the server.**
  `production/stages/base/registry.py` caches one handler instance per stage code in
  a module-level dict, and the cache is never invalidated. So after renaming a stage
  in the UI, some labels keep the old name for the life of the process.
  **Restart the server after renaming a stage** — otherwise you will hunt a bug that
  is really a cache. (Found 2026-08-01 while verifying the fresh-DB loop; the frozen
  R10-B module was left untouched, so this is a known behaviour, not a fix.)

## What breaks without it

- Deploy to a fresh server and the app comes up looking fine — until the first
  Adda, which cannot pass Layering because no worker can open any stage.
- Or: you keep testing on the cluttered database, and a real bug hides among 26
  Addas of noise. That is precisely how a whole product family stayed broken under
  a green test suite.

## Common mistakes

- **Wiping the dev database to "start clean".** You lose the settled journeys that
  are your only regression evidence. Create beside it instead.
- **Seeding business data to save time.** Invented rates become invented money;
  someone eventually trusts the number.
- Forgetting `createsuperuser` — a fresh database has **zero users**, so there is
  no way to log in at all.
- Editing `.env` and not restarting `runserver`.

## AI Implementation Pitfalls

- ❌ Adding products/rolls/workers to `seed_master_data` "so testing is faster" —
  that is business data; the platform/business line is the whole design.
- ❌ Making the seed *update* existing rows to "keep them in sync" — it would
  silently revert the owner's deliberate edits. Additive only.
- ❌ Reaching for `devseed` on production — it is DEBUG/database-name guarded and
  will refuse, correctly.
- ❌ Assuming a stage that exists is a stage a worker can open — check
  `access_by_skill`, the gate reads that, not the stage row.
- ✅ Always verify: on a throwaway database run `migrate → seed → seed again`; the
  second run must report zero creations.

## 🧠 Remember This

**Ek hi command yaad rakho: `./scripts/db.sh`** — `list` · `new` · `use` ·
`save` · `restore` · `delete`. Purani DB mat todo, **nayi banao aur switch karo**.
Seed sirf *platform* cheezein deta hai (stages, skills, access) — products aur
rates tum khud banao, kyunki wahi tumhara asli business hai. Seed dobara chalao
to kuch nahi badalta, aur tumhari edits kabhi overwrite nahi hoti.
