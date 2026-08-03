"""Engine behind ./scripts/db.sh — one friendly tool for local databases.

Read scripts/db.sh for the human-facing help. Everything here is deliberately
boring: it uses the credentials Django already has (so you never type a
password), and it refuses anything that could lose data by accident.

Design rules:
  • never touch a database that is currently in use by .env
  • never delete without taking a backup first (unless you say --no-backup)
  • never overwrite an existing database
  • refuse to DELETE a name that looks live (create is unrestricted —
    creating cannot destroy, so a name guard there is pure friction)
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'config'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

import django  # noqa: E402

django.setup()

from django.db import connection  # noqa: E402

DB = dict(connection.settings_dict)
ENV_FILE = os.path.join(REPO, '.env')

# ── DATABASE_URL kills this tool silently — refuse to run under it. ─────────
# settings/base.py: a non-empty DATABASE_URL makes Django IGNORE DB_NAME/DB_*
# entirely. Every command here steers via DB_NAME (env override + .env line),
# so under DATABASE_URL: `new X` migrates the WRONG database while X stays
# tableless, `use X` claims success while Django keeps serving the URL's DB,
# and `check` probes the wrong place. Worse, .env.example ships DATABASE_URL
# uncommented, so "cp .env.example .env" walks straight into this. Fail loud.
def _database_url_set():
    if os.environ.get('DATABASE_URL', '').strip():
        return True
    try:
        with open(ENV_FILE) as f:
            for ln in f:
                m = re.match(r'\s*DATABASE_URL\s*=\s*(\S+)', ln)
                if m and m.group(1).strip('\'"'):
                    return True
    except OSError:
        pass
    return False


if _database_url_set():
    sys.exit(
        '\n  ✗ DATABASE_URL is set (in .env or the environment).\n'
        '    When DATABASE_URL is set, Django ignores DB_NAME completely — so\n'
        '    every db.sh command would silently act on the WRONG database.\n'
        '    db.sh manages local DB_NAME-style setups only.\n\n'
        '    Fix: comment out the DATABASE_URL line in .env (put # in front),\n'
        '    then run this again. (DATABASE_URL belongs on the SERVER, not on\n'
        '    your laptop.)\n')
BACKUP_DIR = os.path.join(REPO, 'db_backups')
SETTINGS = 'config.settings.local'
PY = os.path.join(REPO, 'env', 'bin', 'python')
MANAGE = os.path.join(REPO, 'config', 'manage.py')

# Words that suggest a name belongs to the real, live system.
PROD_WORDS = ('prod', 'production', 'live')
# Words that prove intent to throw it away. These WIN over PROD_WORDS, so
# `test_production` ("my rehearsal of production") is allowed — it is obviously
# not the real thing. Without this, the guard fires on exactly the names a
# careful person would choose.
TEST_WORDS = ('test', 'dev', 'local', 'tmp', 'temp', 'scratch',
              'sandbox', 'demo', 'staging', 'copy', 'backup', 'rehearsal')


def looks_like_production(name):
    """True only when the name claims to be live AND nothing marks it disposable.

    Deliberately asymmetric: this gates DELETE, not create. Creating a database
    cannot destroy anything, so refusing a create on name alone is pure friction.
    Dropping one called `inventory_production` is the accident worth preventing.
    """
    if any(t in name for t in TEST_WORDS):
        return False
    return any(w in name for w in PROD_WORDS)


def die(msg):
    print(f'\n  ✗ {msg}\n')
    sys.exit(1)


def ok(msg):
    print(f'  ✓ {msg}')


def check_name(name, *, block_prod=False):
    """Validate a database name. `block_prod` is passed ONLY by delete."""
    if not re.fullmatch(r'[a-z_][a-z0-9_]*', name or ''):
        die(f"'{name}' is not a valid database name.\n"
            "    Use lowercase letters, numbers and underscores only "
            "(e.g. test_01) — no spaces, no dashes, no capitals.")
    if block_prod and looks_like_production(name):
        die(f"'{name}' looks like the REAL live database, so this tool will not\n"
            "    drop it. If you genuinely mean to, do it in psql by hand —\n"
            "    deleting production should never be one command away.\n"
            f"    (Names containing {'/'.join(TEST_WORDS[:4])}/… are allowed.)")
    return name


def admin_conn():
    """Connect to the 'postgres' maintenance database, not a project one."""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    c = psycopg2.connect(
        dbname='postgres', user=DB['USER'], password=DB['PASSWORD'],
        host=DB['HOST'] or 'localhost', port=DB['PORT'] or 5432)
    c.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return c


def all_databases():
    c = admin_conn()
    with c.cursor() as cur:
        cur.execute("""
            SELECT datname, pg_size_pretty(pg_database_size(datname))
            FROM pg_database
            WHERE datistemplate = false AND datname <> 'postgres'
            ORDER BY datname
        """)
        rows = cur.fetchall()
    c.close()
    return rows


def db_exists(name):
    c = admin_conn()
    with c.cursor() as cur:
        cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', (name,))
        found = cur.fetchone() is not None
    c.close()
    return found


def active_db():
    """Which database .env currently points at (what Django resolved)."""
    return DB['NAME']


def pg_env():
    e = dict(os.environ)
    e['PGPASSWORD'] = DB['PASSWORD'] or ''
    return e


def run_manage(dbname, *args):
    e = dict(os.environ)
    e['DB_NAME'] = dbname
    r = subprocess.run([PY, MANAGE, *args, f'--settings={SETTINGS}'],
                       cwd=REPO, env=e)
    if r.returncode != 0:
        die(f'`manage.py {args[0]}` failed on {dbname}.')


# ── commands ───────────────────────────────────────────────────────────────
def peek(name):
    """One-line summary of what is INSIDE a database, via plain SQL.

    Raw SQL on purpose: booting Django once per database would make `list` slow,
    and a very old database might not even import cleanly. Anything unreadable
    is reported as '?' rather than crashing the listing.
    """
    import psycopg2
    q = ("SELECT (SELECT count(*) FROM production_product),"
         "       (SELECT count(*) FROM production_adda),"
         "       (SELECT count(*) FROM accounts_user),"
         "       (SELECT count(*) FROM production_stage)")
    try:
        c = psycopg2.connect(
            dbname=name, user=DB['USER'], password=DB['PASSWORD'],
            host=DB['HOST'] or 'localhost', port=DB['PORT'] or 5432,
            connect_timeout=4)
        with c.cursor() as cur:
            cur.execute(q)
            p, ad, u, st = cur.fetchone()
        c.close()
        return f'{st:>3} stages · {p:>3} products · {ad:>3} addas · {u:>3} users'
    except Exception:
        return 'not readable (different schema?)'


def cmd_list(a):
    cur = active_db()
    rows = all_databases()
    print('\n  Your databases — "→" is the one in use:\n')
    for name, size in rows:
        mark = '→' if name == cur else ' '
        print(f'   {mark} {name:<26}{size:>9}   {peek(name)}')
    print(f'\n  in use by .env : {cur}')
    print(f'  backups folder : db_backups/  ({len(_backups())} file(s))')
    print('\n  A database with 0 addas and 0 users is an untouched fresh one.'
          '\n  Ready-to-run check for the CURRENT one:  ./scripts/db.sh check\n')


def cmd_current(a):
    print(active_db())


def cmd_new(a):
    name = check_name(a.name)
    if name == active_db():
        die(f"'{name}' is the database you are already using.")
    if db_exists(name):
        die(f"'{name}' already exists. Pick another name, or delete it first.")
    c = admin_conn()
    with c.cursor() as cur:
        cur.execute(f'CREATE DATABASE "{name}"')
    c.close()
    ok(f'created empty database {name}')
    print('  … building tables (this is the slow part, ~30-60s)')
    run_manage(name, 'migrate', '--no-input')
    ok('tables built')
    print('  … adding factory master data (stages, skills, access)')
    run_manage(name, 'seed_master_data', '--repair-access')
    print(f"""
  ✓ READY: {name}   (empty of business data, full of factory setup)

  Next:
     ./scripts/db.sh use {name}
     env/bin/python config/manage.py createsuperuser
     env/bin/python config/manage.py runserver --settings={SETTINGS}
""")


def superuser_count(dbname):
    """How many superusers exist in that database (0 = you cannot log in)."""
    e = dict(os.environ)
    e['DB_NAME'] = dbname
    r = subprocess.run(
        [PY, MANAGE, 'shell', f'--settings={SETTINGS}', '-c',
         'from accounts.models import User;'
         'print(User.objects.filter(is_superuser=True).count())'],
        cwd=REPO, env=e, capture_output=True, text=True)
    for line in reversed(r.stdout.strip().splitlines()):
        if line.strip().isdigit():
            return int(line.strip())
    return 0


def cmd_fresh(a):
    """new + use + createsuperuser in ONE command — the usual reason you are here."""
    name = check_name(a.name)
    if db_exists(name):
        die(f"'{name}' already exists.\n"
            f"      To use it as-is:   ./scripts/db.sh use {name}\n"
            f"      To start over:     ./scripts/db.sh delete {name} "
            f"--yes-delete {name}   (backs up first)")
    # Remember where we came FROM, before `use` rewrites .env — otherwise the
    # "go back" hint below would point at the database we just switched to.
    previous = active_db_from_env()
    cmd_new(argparse.Namespace(name=name))
    cmd_use(argparse.Namespace(name=name))
    print('  Now create your login (a new database has ZERO users).')
    print('  Password stays invisible while you type — that is normal.\n')
    subprocess.run([PY, MANAGE, 'createsuperuser', f'--settings={SETTINGS}'],
                   cwd=REPO)
    # Trust the DATABASE, not the exit code: createsuperuser can exit 0 without
    # creating anyone (e.g. no terminal attached). Claiming success when there
    # is no login is worse than saying nothing — you would only find out at the
    # login screen.
    if superuser_count(name) > 0:
        ok('login created')
        login_note = ''
    else:
        login_note = ('\n  ⚠ NO LOGIN YET — you cannot sign in until you run:\n'
                      '       env/bin/python config/manage.py createsuperuser'
                      f' --settings={SETTINGS}\n')
    print(f"""
  ────────────────────────────────────────────────
  READY on {name}. Start the app:

     ./scripts/db.sh run

  Then open http://127.0.0.1:8000 and begin at Product.
  Back to your real data any time:  ./scripts/db.sh use {previous}
  ────────────────────────────────────────────────
{login_note}""")


def active_db_from_env():
    """Re-read .env for display (DB dict was captured at import time)."""
    try:
        with open(ENV_FILE) as f:
            for ln in f:
                m = re.match(r'\s*DB_NAME\s*=\s*(\S+)', ln)
                if m:
                    # decouple strips quotes when Django reads .env, so we must
                    # too — DB_NAME="test_01" would otherwise leak the quotes
                    # into branch/check and every name comparison.
                    return m.group(1).strip('\'"')
    except OSError:
        pass
    return 'inventory_db'


def cmd_run(a):
    """Start the dev server on whatever database .env points at."""
    name = active_db_from_env()
    print(f'\n  starting the app on database: {name}')
    print('  open http://127.0.0.1:8000   ·   Ctrl+C to stop\n')
    os.execv(PY, [PY, MANAGE, 'runserver', f'--settings={SETTINGS}'])


def cmd_branch(a):
    """Fork the CURRENT database into a new one — a save-point you can return to.

    Think git branch, for data. You set up a product, cloth and workers (slow,
    fiddly work); you branch; then you test something destructive on the branch
    and the setup is still sitting untouched on the original.

    Branches nest naturally: branch off a branch off a branch. Each one is just
    a full database, so there is no chain to break and nothing to "merge".
    """
    target = check_name(a.name)
    source = active_db_from_env()
    if db_exists(target):
        die(f"'{target}' already exists. Pick another branch name.")
    print(f'\n  branching {source}  →  {target}')
    saved = cmd_save(argparse.Namespace(name=source))
    cmd_restore(argparse.Namespace(file=saved, into=target))
    if a.use:
        cmd_use(argparse.Namespace(name=target))
    print(f"""  ────────────────────────────────────────────────
  BRANCH READY: {target}   (a full copy of {source} as of now)

  {'You are now ON it.' if a.use else f'Switch to it:  ./scripts/db.sh use {target}'}
  Go back to the original at any time:  ./scripts/db.sh use {source}

  Nothing about {source} changed — a branch is a copy, never a move.
  ────────────────────────────────────────────────
""")


def cmd_check(a):
    """Report the docs/FRESH_DB_REQUIREMENTS.md §3 checklist against this database.

    The point is that the TOOL tells you what is missing, instead of you reading
    a list and guessing. Every line here mirrors a row of that document — when a
    new requirement is discovered, add it in both places.
    """
    name = active_db_from_env()
    e = dict(os.environ)
    e['DB_NAME'] = name
    probe = r'''
from accounts.models import Skill, User
from inventory.models import Role
from production.models import (
    Adda, Product, ProductSize, Stage, WorkflowStage,
)
from raw_materials.models import ClothRoll

out = []
def row(label, ok, detail, blocking=True):
    out.append((label, bool(ok), detail, blocking))

su = User.objects.filter(is_superuser=True).count()
row('login (superuser)', su, f'{su} superuser(s)')

stages = Stage.objects.count()
links = sum(s.access_by_skill.count() for s in Stage.objects.all())
row('platform stages seeded', stages >= 21, f'{stages} stages, {links} access links')

prods = Product.objects.count()
row('product exists', prods, f'{prods} product(s)')

# A product is only USABLE with sizes + a flow + rates on payable stages.
usable, why = 0, []
for p in Product.objects.all():
    sizes = ProductSize.objects.filter(product=p, is_active=True).count()
    ws = list(p.workflow_stages.all())
    payable = [w for w in ws if w.credits_workers]
    # Rate needed only where the stage PAYS ITSELF: a cost-grouped member
    # (cost_billed_at -> another stage) legitimately has NO rate — the C-1
    # double-pay guard depends on that. And cost_rate=0 is a legal rate, so
    # test `is None`, never truthiness.
    unrated = [w.stage.code for w in payable
               if w.cost_billed_at_id is None and w.cost_rate is None]
    if sizes and len(ws) >= 3 and payable and not unrated:
        usable += 1
    else:
        bits = []
        if not sizes: bits.append('no sizes')
        if len(ws) < 3: bits.append(f'{len(ws)} stage(s)')
        if not payable: bits.append('no payable stage')
        if unrated: bits.append('unrated: ' + ','.join(unrated[:3]))
        why.append(f'{p.code} ({"; ".join(bits)})')
row('a RUNNABLE product (sizes + flow + rates)', usable,
    f'{usable} runnable' + (f' · not ready: {"; ".join(why[:3])}' if why else ''))

rolls = ClothRoll.objects.count()
row('cloth roll available', rolls, f'{rolls} roll(s)')

users = User.objects.count()
# Superusers bypass every role gate AND createsuperuser assigns no role — so
# counting them as "roleless" would flash a permanent false alarm at the owner's
# own fresh login. Only ordinary accounts need a role.
roleless = User.objects.filter(role__isnull=True, is_superuser=False).count()
row('users have roles', users and not roleless,
    f'{users} user(s), {roleless} non-admin without a role')

skilled = User.objects.filter(skills__isnull=False).distinct().count()
row('workers have skills', skilled, f'{skilled} user(s) with >=1 skill')

addas = Adda.objects.count()
row('an Adda has been started', addas, f'{addas} adda(s)', False)

print('___CHECK___')
for label, good, detail, blocking in out:
    print(f'{int(good)}|{int(blocking)}|{label}|{detail}')
'''
    r = subprocess.run([PY, MANAGE, 'shell', f'--settings={SETTINGS}', '-c', probe],
                       cwd=REPO, env=e, capture_output=True, text=True)
    if '___CHECK___' not in r.stdout:
        die('could not read the database:\n' + (r.stderr or r.stdout)[-700:])
    lines = r.stdout.split('___CHECK___', 1)[1].strip().splitlines()
    print(f'\n  Readiness of: {name}\n')
    missing = []
    for ln in lines:
        good, blocking, label, detail = ln.split('|', 3)
        mark = '✓' if good == '1' else ('✗' if blocking == '1' else '–')
        print(f'   {mark}  {label:<42} {detail}')
        if good == '0' and blocking == '1':
            missing.append(label)
    if missing:
        print(f'\n  ⚠ {len(missing)} thing(s) still needed before a full run:')
        for m in missing:
            print(f'      • {m}')
        print('\n  What each one is for, and what breaks without it:')
        print('     docs/FRESH_DB_REQUIREMENTS.md  §3\n')
    else:
        print('\n  ✓ Everything required is present — this database can run a batch.\n')


def cmd_use(a):
    name = check_name(a.name)
    if not db_exists(name):
        die(f"'{name}' does not exist. Create it first:\n"
            f"      ./scripts/db.sh new {name}")
    if not os.path.exists(ENV_FILE):
        die('.env not found — cannot switch.')
    with open(ENV_FILE) as f:
        lines = f.readlines()
    # Safety copy before we touch the file that holds your settings.
    with open(ENV_FILE + '.bak', 'w') as f:
        f.writelines(lines)
    out, replaced = [], False
    for ln in lines:
        if re.match(r'\s*DB_NAME\s*=', ln):
            out.append(f'DB_NAME={name}\n')
            replaced = True
        else:
            out.append(ln)
    if not replaced:
        out.append(f'\nDB_NAME={name}\n')
    with open(ENV_FILE, 'w') as f:
        f.writelines(out)
    ok(f'.env now points at {name}   (old .env saved as .env.bak)')
    print('\n  ⚠ RESTART the server (Ctrl+C then runserver) or you will still\n'
          '    be looking at the old database.')
    # The first wall on a fresh database is always "I cannot log in".
    if superuser_count(name) == 0:
        print('\n  ⚠ This database has NO LOGIN yet. Create one before you try\n'
              '    to sign in:\n'
              '       env/bin/python config/manage.py createsuperuser'
              f' --settings={SETTINGS}')
    print()


def _backups():
    if not os.path.isdir(BACKUP_DIR):
        return []
    return sorted(f for f in os.listdir(BACKUP_DIR) if f.endswith('.sql'))


def cmd_save(a):
    name = check_name(a.name) if a.name else active_db()
    if not db_exists(name):
        die(f"'{name}' does not exist.")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = os.path.join(BACKUP_DIR, f'{name}__{stamp}.sql')
    print(f'  … saving {name} → db_backups/{os.path.basename(path)}')
    with open(path, 'w') as out:
        r = subprocess.run(
            ['pg_dump', '-U', DB['USER'], '-h', DB['HOST'] or 'localhost',
             '-p', str(DB['PORT'] or 5432), '--clean', '--if-exists', name],
            stdout=out, env=pg_env())
    # A failed dump must not leave a corpse: a 0-byte/partial .sql sitting in
    # db_backups/ looks exactly like a real backup in `db.sh backups`, and
    # restoring it "succeeds" into an empty database — the worst possible lie.
    if r.returncode != 0:
        try:
            os.unlink(path)
        except OSError:
            pass
        die('pg_dump failed — no backup was written (partial file removed).')
    if os.path.getsize(path) < 1024:
        try:
            os.unlink(path)
        except OSError:
            pass
        die(f'pg_dump produced a suspiciously tiny file for {name} — '
            'refusing to keep it as a backup.')
    mb = os.path.getsize(path) / 1_048_576
    ok(f'saved ({mb:.1f} MB) — this file is a complete copy of {name}')
    print('\n  It lives in your project folder and is gitignored (it contains\n'
          '  real people\'s data, so it must NEVER be committed).\n')
    return path


def cmd_restore(a):
    target = check_name(a.into)
    src = a.file
    if not os.path.isabs(src):
        cand = os.path.join(BACKUP_DIR, src)
        src = cand if os.path.exists(cand) else src
    if not os.path.exists(src):
        die(f'backup file not found: {src}\n'
            f"      list them with:  ./scripts/db.sh backups")
    if os.path.getsize(src) < 1024:
        die(f'{os.path.basename(src)} is essentially empty ({os.path.getsize(src)} '
            'bytes) — not a real backup. Restoring it would "succeed" into an '
            'empty database. Delete the file and take a fresh save.')
    if target == active_db():
        die(f"'{target}' is in use. Switch away first: ./scripts/db.sh use <other>")
    if db_exists(target):
        die(f"'{target}' already exists — restore only into a NEW name.")
    c = admin_conn()
    with c.cursor() as cur:
        cur.execute(f'CREATE DATABASE "{target}"')
    c.close()
    ok(f'created {target}')
    print(f'  … restoring {os.path.basename(src)} into {target}')
    # ON_ERROR_STOP is the whole ballgame: without it psql walks PAST any SQL
    # error and exits 0, so a half-restored database gets a green checkmark —
    # and `branch` is built on this, so a "branch" could silently be a partial
    # copy the owner then trusts. Safe here because the target is always
    # freshly created (the dump's DROP ... IF EXISTS lines are notices, not
    # errors, on an empty database).
    with open(src) as f:
        r = subprocess.run(
            ['psql', '-q', '-v', 'ON_ERROR_STOP=1',
             '-U', DB['USER'], '-h', DB['HOST'] or 'localhost',
             '-p', str(DB['PORT'] or 5432), '-d', target],
            stdin=f, env=pg_env(),
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        # Don't leave a half-restored database lying around under the target
        # name — it would block the retry AND masquerade as a valid copy.
        c = admin_conn()
        with c.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{target}"')
        c.close()
        die(f'restore FAILED — {target} was removed again (a half-restored '
            f'database is worse than none):\n{(r.stderr or "")[-800:]}')
    ok(f'restored into {target}')
    print(f'\n  Use it:  ./scripts/db.sh use {target}\n')


def cmd_backups(a):
    files = _backups()
    if not files:
        print('\n  No backups yet. Make one:  ./scripts/db.sh save\n')
        return
    print('\n  Saved copies in db_backups/ :\n')
    for f in files:
        mb = os.path.getsize(os.path.join(BACKUP_DIR, f)) / 1_048_576
        print(f'   • {f:<48}{mb:>8.1f} MB')
    print('\n  Restore one into a NEW database:')
    print(f'     ./scripts/db.sh restore {files[-1]} --into restored_copy\n')


def cmd_delete(a):
    # The ONLY command that blocks production-looking names — dropping is the
    # single irreversible verb here.
    name = check_name(a.name, block_prod=True)
    if not db_exists(name):
        die(f"'{name}' does not exist (nothing to delete).")
    if name == active_db():
        die(f"'{name}' is the database you are USING right now.\n"
            '      Switch to another one first, then delete:\n'
            '        ./scripts/db.sh use <other_db>\n'
            f'        ./scripts/db.sh delete {name}')
    print(f'\n  About to DELETE the database: {name}')
    print('  This cannot be undone by itself — so a backup is taken first.\n')
    if a.confirm != name:
        die('Confirmation required. Re-run with the name repeated:\n'
            f'      ./scripts/db.sh delete {name} --yes-delete {name}')
    if not a.no_backup:
        saved = cmd_save(argparse.Namespace(name=name))
        ok(f'safety backup: db_backups/{os.path.basename(saved)}')
    c = admin_conn()
    with c.cursor() as cur:
        # Kick off any idle connection, else DROP DATABASE refuses.
        cur.execute("""
            SELECT pg_terminate_backend(pid) FROM pg_stat_activity
            WHERE datname = %s AND pid <> pg_backend_pid()
        """, (name,))
        cur.execute(f'DROP DATABASE "{name}"')
    c.close()
    ok(f'deleted {name}')
    if not a.no_backup:
        print('\n  Your backup is still in db_backups/ — restore it any time with:')
        print(f'     ./scripts/db.sh restore <file> --into {name}\n')


def main():
    p = argparse.ArgumentParser(prog='db.sh', add_help=True)
    sub = p.add_subparsers(dest='cmd', required=True)

    sub.add_parser('list', help='show all databases + which is in use').set_defaults(fn=cmd_list)
    sub.add_parser('current', help='print the database in use').set_defaults(fn=cmd_current)
    sub.add_parser('backups', help='list saved copies').set_defaults(fn=cmd_backups)

    s = sub.add_parser('fresh', help='ONE STEP: create + switch + make your login')
    s.add_argument('name'); s.set_defaults(fn=cmd_fresh)

    sub.add_parser('run', help='start the app on the current database').set_defaults(fn=cmd_run)
    sub.add_parser('check', help='is this database ready to run a batch?').set_defaults(fn=cmd_check)

    s = sub.add_parser('branch', help='fork the CURRENT database into a new one (a save-point)')
    s.add_argument('name')
    s.add_argument('--use', action='store_true', help='switch to it immediately')
    s.set_defaults(fn=cmd_branch)

    s = sub.add_parser('new', help='create a fresh database (migrate + seed)')
    s.add_argument('name'); s.set_defaults(fn=cmd_new)

    s = sub.add_parser('use', help='switch .env to this database')
    s.add_argument('name'); s.set_defaults(fn=cmd_use)

    s = sub.add_parser('save', help='save a copy into db_backups/')
    s.add_argument('name', nargs='?'); s.set_defaults(fn=cmd_save)

    s = sub.add_parser('restore', help='restore a backup into a NEW database')
    s.add_argument('file'); s.add_argument('--into', required=True)
    s.set_defaults(fn=cmd_restore)

    s = sub.add_parser('delete', help='delete a database (backs up first)')
    s.add_argument('name')
    s.add_argument('--yes-delete', dest='confirm', default=None)
    s.add_argument('--no-backup', action='store_true')
    s.set_defaults(fn=cmd_delete)

    a = p.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
