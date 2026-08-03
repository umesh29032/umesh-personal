"""seed_master_data — the PLATFORM master data a factory cannot run without.

WHY THIS EXISTS
───────────────
Migrations only seed a starter subset (4 stages, 2 skills, 7 stage-access
links). A real factory needs 21 stages, 10 skills and 24 access links, and
until AUDIT-2 (2026-07-27) those existed **only as hand-made rows in the
owner's dev database**. A fresh production database therefore came up unable
to run a single Adda: no Overlock, no Checking, no Packing, and — because
`Stage.access_by_skill` was empty for them — no worker could open any stage.

WHAT IT SEEDS (platform data — the same in every factory)
    StageCategory · MachineType · Skill · Stage · Stage.access_by_skill

WHAT IT DELIBERATELY DOES **NOT** SEED (your business data — you enter it)
    Products, ProductSizes, WorkflowStages + their cost rates, cloth
    types/colours/storage, rolls, users. Those differ per factory and per
    season; inventing them would be inventing your money.

THE TWO GUARANTEES
    1. **Idempotent.** Natural-key `get_or_create`. Run it a hundred times —
       after the first, it creates nothing.
    2. **Never overwrites your edits.** An existing row is left EXACTLY as it
       is: renamed a stage, re-pointed a machine type, changed who can access
       it — all preserved. The seed only fills in what is missing. (Owner
       requirement: "seeds ... stay in it until user wants to edit".)
       `--repair-access` is the one opt-in exception, and it only ADDS missing
       skill links; it never removes one you deliberately took away.

Unlike `devseed`, this command is **production-safe by design**: it writes only
platform reference rows, no demo/fake business data, so it carries no DEBUG or
database-name guard and is meant to run on the real server.

    python manage.py seed_master_data --dry-run     # show what WOULD change
    python manage.py seed_master_data               # apply
    python manage.py seed_master_data --repair-access
"""
from django.core.management.base import BaseCommand
from django.db import transaction

# (code, name, display_order)
CATEGORIES = [
    ('pre_production', 'Pre Production', 10),
    ('stitching',      'Stitching',      20),
    ('printing',       'Printing',       25),
    ('finishing',      'Finishing',      30),
    ('dispatch',       'Dispatch',       40),
]

# (code, name)
MACHINE_TYPES = [
    ('cutting_machine',       'Cutting Machine'),
    ('overlock_machine',      'Overlock Machine'),
    ('flatlock_machine',      'Flatlock Machine'),
    ('single_needle_machine', 'Single Needle Machine'),
    ('elastic_machine',       'Elastic Machine'),
]

# (name, label) — `name` is the code the access gate matches on.
SKILLS = [
    ('cutting_master',         'Cutting Master'),
    ('cutting_master_helper',  'Cutting Master Helper'),
    ('overlock_operator',      'Overlock Operator'),
    ('flatlock_operator',      'Flatlock Operator'),
    ('single_needle_operator', 'Single Needle Operator'),
    ('sleeve_operator',        'Sleeve Operator'),
    ('elastic_operator',       'Elastic Operator'),
    ('checker',                'Checker (QC)'),
    ('iron_master',            'Iron Master'),
    ('finishing_helper',       'Finishing Helper'),
]

# (code, name, work_type, category_code, machine_type_code, [skill names])
# Mirrors the owner's real factory library. The historical `verify` /
# `verify-<hash>` rows in the dev database are TEST RESIDUE and are not seeded.
STAGES = [
    # ── Pre Production ────────────────────────────────────────────────────
    ('layering',           'Layering',           'manual',  'pre_production', None,
     ['cutting_master', 'cutting_master_helper']),
    ('cutting_pattern',    'Pattern Design',     'manual',  'pre_production', None,
     ['cutting_master', 'cutting_master_helper']),
    ('cutting',            'Cutting',            'machine', 'pre_production', 'cutting_machine',
     ['cutting_master', 'cutting_master_helper']),
    ('barcode_generation', 'Barcode Generation', 'manual',  'pre_production', None,
     ['cutting_master', 'cutting_master_helper']),
    ('cross_cutting',      'Cross Cutting',      'manual',  None, None, []),
    # ── Stitching ─────────────────────────────────────────────────────────
    ('overlock',        'Panel Join',        'machine', 'stitching', 'overlock_machine',
     ['cutting_master', 'overlock_operator']),
    ('shoulder_join',   'Shoulder Join',     'machine', 'stitching', 'overlock_machine',
     ['overlock_operator']),
    ('neck_join',       'Neck Join',         'machine', 'stitching', 'overlock_machine',
     ['overlock_operator']),
    ('side_seam_close', 'Side Seam Close',   'machine', 'stitching', 'overlock_machine',
     ['overlock_operator']),
    ('sleeve_join',     'Sleeve Join',       'machine', 'stitching', 'overlock_machine',
     ['sleeve_operator']),
    ('sleeve_fold',     'Sleeve Fold',       'machine', 'stitching', 'flatlock_machine',
     ['flatlock_operator']),
    ('bottom_fold',     'Bottom Fold',       'machine', 'stitching', 'flatlock_machine',
     ['flatlock_operator']),
    ('leg_binding',     'Leg Binding (Patti)', 'machine', 'stitching', 'flatlock_machine',
     ['flatlock_operator']),
    ('elastic_attach',  'Elastic Attach',    'machine', 'stitching', 'elastic_machine',
     ['elastic_operator']),
    ('collar_attach',   'Collar Attach',     'machine', 'stitching', 'single_needle_machine',
     ['single_needle_operator']),
    ('label_attach',    'Label Attach',      'machine', 'stitching', 'single_needle_machine',
     ['single_needle_operator']),
    # ── Finishing ─────────────────────────────────────────────────────────
    ('thread_cutting', 'Thread Cutting', 'manual', 'finishing', None, ['finishing_helper']),
    ('checking',       'Checking',       'manual', 'finishing', None, ['checker']),
    ('iron_press',     'Iron',           'manual', 'finishing', None, ['iron_master']),
    ('packing',        'Packing',        'manual', 'finishing', None, ['finishing_helper']),
    # ── Dispatch ──────────────────────────────────────────────────────────
    ('dispatch', 'Dispatch', 'manual', 'dispatch', None, []),
]


class Command(BaseCommand):
    help = ("Seed the platform master data a factory cannot run without "
            "(stage categories, machine types, skills, stages, stage access). "
            "Idempotent and non-destructive — existing rows are never modified.")

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Report what WOULD be created; write nothing.')
        parser.add_argument(
            '--repair-access', action='store_true',
            help='Also ADD any missing stage->skill links on stages that '
                 'already exist. Never removes a link you took away.')

    def handle(self, *args, **opts):
        from accounts.models import Skill
        from production.models import MachineType, Stage, StageCategory

        dry = opts['dry_run']
        repair = opts['repair_access']
        made = {'category': 0, 'machine_type': 0, 'skill': 0,
                'stage': 0, 'access': 0}
        kept = {'category': 0, 'machine_type': 0, 'skill': 0, 'stage': 0}

        def note(kind, label, created):
            if created:
                made[kind] += 1
                self.stdout.write(self.style.SUCCESS(f'  + {kind}: {label}'))
            else:
                kept[kind] = kept.get(kind, 0) + 1

        with transaction.atomic():
            cats = {}
            for code, name, order in CATEGORIES:
                if dry:
                    obj = StageCategory.objects.filter(code=code).first()
                    note('category', code, obj is None)
                    cats[code] = obj
                    continue
                obj, created = StageCategory.objects.get_or_create(
                    code=code, defaults={'name': name, 'display_order': order})
                note('category', code, created)
                cats[code] = obj

            mts = {}
            for code, name in MACHINE_TYPES:
                if dry:
                    obj = MachineType.objects.filter(code=code).first()
                    note('machine_type', code, obj is None)
                    mts[code] = obj
                    continue
                obj, created = MachineType.objects.get_or_create(
                    code=code, defaults={'name': name})
                note('machine_type', code, created)
                mts[code] = obj

            skills = {}
            for name, label in SKILLS:
                if dry:
                    obj = Skill.objects.filter(name=name).first()
                    note('skill', name, obj is None)
                    skills[name] = obj
                    continue
                obj, created = Skill.objects.get_or_create(
                    name=name, defaults={'label': label})
                note('skill', name, created)
                skills[name] = obj

            for code, name, work, cat, mt, skill_names in STAGES:
                existing = Stage.objects.filter(code=code).first()
                if dry:
                    note('stage', code, existing is None)
                    if existing is not None and repair:
                        have = set(existing.access_by_skill.values_list(
                            'name', flat=True))
                        missing = [s for s in skill_names if s not in have]
                        if missing:
                            made['access'] += len(missing)
                            self.stdout.write(self.style.WARNING(
                                f'  ~ access: {code} += {missing}'))
                    elif existing is None:
                        made['access'] += len(skill_names)
                    continue

                stage, created = Stage.objects.get_or_create(
                    code=code,
                    defaults={'name': name, 'work_type': work,
                              'category': cats.get(cat) if cat else None,
                              'machine_type': mts.get(mt) if mt else None})
                note('stage', code, created)
                # Access links: on CREATE always; on an existing stage only
                # with --repair-access, and only ever ADDITIVE.
                if created or repair:
                    have = set(stage.access_by_skill.values_list(
                        'name', flat=True))
                    for sn in skill_names:
                        if sn not in have and skills.get(sn):
                            stage.access_by_skill.add(skills[sn])
                            made['access'] += 1
                            if not created:
                                self.stdout.write(self.style.WARNING(
                                    f'  ~ access: {code} += {sn}'))

            if dry:
                transaction.set_rollback(True)

        # Loud self-check: a stage can exist while MISSING an access link the
        # factory needs — exactly what migrations leave behind (`cutting`
        # without `cutting_master_helper`), and a silent one, because the stage
        # looks present. Detect it and name the flag that repairs it.
        gaps = []
        if not dry and not repair:
            for code, _n, _w, _c, _m, skill_names in STAGES:
                if not skill_names:
                    continue
                st = Stage.objects.filter(code=code).first()
                if st is None:
                    continue
                have = set(st.access_by_skill.values_list('name', flat=True))
                missing = [s for s in skill_names if s not in have]
                if missing:
                    gaps.append((code, missing))

        self.stdout.write('')
        verb = 'WOULD create' if dry else 'created'
        self.stdout.write(
            f"{verb}: {made['category']} categories · {made['machine_type']} "
            f"machine types · {made['skill']} skills · {made['stage']} stages "
            f"· {made['access']} stage-access links")
        self.stdout.write(
            f"already present (left untouched): {kept.get('category', 0)} "
            f"categories · {kept.get('machine_type', 0)} machine types · "
            f"{kept.get('skill', 0)} skills · {kept.get('stage', 0)} stages")
        # The END STATE, not just the deltas. Reading "4 stages already present"
        # with no total made it look like nothing had been added — the reader
        # cannot tell a working database from a broken one without the totals.
        if not dry:
            self.stdout.write(
                f"NOW IN THIS DATABASE: {StageCategory.objects.count()} categories "
                f"· {MachineType.objects.count()} machine types "
                f"· {Skill.objects.count()} skills "
                f"· {Stage.objects.count()} stages (expected {len(STAGES)})")
            short = len(STAGES) - Stage.objects.count()
            if short > 0:
                self.stdout.write(self.style.WARNING(
                    f'  ⚠ {short} expected stage(s) still missing — re-run, or see '
                    'docs/FRESH_DB_REQUIREMENTS.md §2'))
        if dry:
            self.stdout.write(self.style.WARNING(
                'DRY RUN — nothing was written.'))
        else:
            self.stdout.write(self.style.SUCCESS('Master data ready.'))
            if gaps:
                self.stdout.write('')
                self.stdout.write(self.style.ERROR(
                    'ACTION NEEDED — these stages exist but are MISSING skill '
                    'links, so those workers cannot open them:'))
                for code, missing in gaps:
                    self.stdout.write(self.style.ERROR(
                        f'    {code} is missing {missing}'))
                self.stdout.write(self.style.ERROR(
                    '  Fix (additive only, removes nothing):  '
                    'python manage.py seed_master_data --repair-access'))
            if not Stage.objects.exclude(access_by_skill=None).exists():
                self.stdout.write(self.style.ERROR(
                    'WARNING: no stage has any skill link — workers will not '
                    'be able to open any stage. Re-run with --repair-access.'))
