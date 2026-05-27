"""Introduce Stage model + replace WorkflowStage.stage_type CharField with FK.

Sequence (all in one migration to keep atomicity):
  1. Create Stage table
  2. Add WorkflowStage.stage FK (nullable initially so existing rows survive)
  3. Data migration:
       - Seed Stage rows from distinct WorkflowStage.stage_type values
       - Copy StageAccessRule.allowed_skills / allowed_roles → Stage M2Ms
       - Backfill WorkflowStage.stage from stage_type lookup
  4. Make WorkflowStage.stage non-nullable
  5. Swap unique_together: (product, stage_type) → (product, stage)
  6. Drop WorkflowStage.stage_type column
  7. Drop StageAccessRule model entirely
"""
import django.db.models.deletion
from django.db import migrations, models


KNOWN_STAGES = [
    # (code, name, default_skills_by_name, default_roles_by_code)
    ('layering', 'Layering', ['cutting_master', 'cutting_master_helper'], []),
    ('cutting',  'Cutting',  ['cutting_master'], []),
]


def seed_and_backfill(apps, schema_editor):
    Stage = apps.get_model('production', 'Stage')
    WorkflowStage = apps.get_model('production', 'WorkflowStage')
    StageAccessRule = apps.get_model('production', 'StageAccessRule')
    Skill = apps.get_model('accounts', 'Skill')
    Role = apps.get_model('inventory', 'Role')

    # 1. Seed Stage rows for every known stage_type. If new stage_types exist
    #    in WorkflowStage that aren't in KNOWN_STAGES, seed those too (just
    #    name from .title() of the code; admin can rename later).
    known_codes = {code for code, *_ in KNOWN_STAGES}
    extra_codes = set(
        WorkflowStage.objects.values_list('stage_type', flat=True).distinct()
    ) - known_codes

    skill_lookup = {s.name: s for s in Skill.objects.all()}
    role_lookup = {r.code: r for r in Role.objects.all()}

    for code, name, skill_names, role_codes in KNOWN_STAGES:
        stage, _ = Stage.objects.get_or_create(
            code=code,
            defaults={'name': name, 'is_active': True},
        )
        stage.access_by_skill.set([skill_lookup[s] for s in skill_names if s in skill_lookup])
        stage.access_by_role.set([role_lookup[c] for c in role_codes if c in role_lookup])

    for code in extra_codes:
        Stage.objects.get_or_create(
            code=code,
            defaults={'name': code.replace('_', ' ').title(), 'is_active': True},
        )

    # 2. Copy StageAccessRule data into Stage M2Ms (overrides seeded defaults).
    for rule in StageAccessRule.objects.all():
        stage = Stage.objects.filter(code=rule.stage_type).first()
        if not stage:
            continue
        skills = list(rule.allowed_skills.all())
        roles = list(rule.allowed_roles.all())
        # Cast managed-by-this-migration models to live Skill/Role rows.
        if skills:
            stage.access_by_skill.set([
                skill_lookup[s.name] for s in skills if s.name in skill_lookup
            ])
        if roles:
            stage.access_by_role.set([
                role_lookup[r.code] for r in roles if r.code in role_lookup
            ])

    # 3. Backfill WorkflowStage.stage FK from stage_type string.
    stage_by_code = {s.code: s for s in Stage.objects.all()}
    for ws in WorkflowStage.objects.all():
        target = stage_by_code.get(ws.stage_type)
        if target is None:
            raise RuntimeError(
                f"Cannot map WorkflowStage(id={ws.id}, stage_type={ws.stage_type!r}) "
                f"to a Stage row — seed it manually before re-running."
            )
        ws.stage = target
        ws.save(update_fields=['stage'])


def reverse_seed(apps, schema_editor):
    # Best-effort reverse: clear stage FK on WorkflowStages, drop seeded Stages.
    WorkflowStage = apps.get_model('production', 'WorkflowStage')
    Stage = apps.get_model('production', 'Stage')
    WorkflowStage.objects.update(stage=None)
    Stage.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0010_seed_stage_access_rules'),
        ('accounts', '0010_add_cutting_master_helper_skill'),
        ('inventory', '0013_seed_accountant_role'),
    ]

    operations = [
        # ── 1. Create Stage table ─────────────────────────────────────────
        migrations.CreateModel(
            name='Stage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.SlugField(max_length=32, unique=True,
                    help_text="Stable identifier used in URLs + services (e.g. 'layering').")),
                ('name', models.CharField(max_length=64,
                    help_text="Display label shown in flow pipeline (e.g. 'Layering').")),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('access_by_skill', models.ManyToManyField(
                    blank=True, related_name='accessible_stages', to='accounts.skill',
                    help_text='Users with ANY of these skills can access this stage.')),
                ('access_by_role', models.ManyToManyField(
                    blank=True, related_name='accessible_stages', to='inventory.role',
                    help_text='Users whose role (or extra_roles) matches any of these.')),
            ],
            options={'ordering': ['name']},
        ),
        # ── 2. Add WorkflowStage.stage FK (nullable for backfill) ─────────
        migrations.AddField(
            model_name='workflowstage',
            name='stage',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='workflow_stages', to='production.stage',
            ),
        ),
        # ── 3. Seed + backfill ─────────────────────────────────────────────
        migrations.RunPython(seed_and_backfill, reverse_seed),
        # ── 4. Make stage non-null ────────────────────────────────────────
        migrations.AlterField(
            model_name='workflowstage',
            name='stage',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='workflow_stages', to='production.stage',
            ),
        ),
        # ── 5. Swap unique_together to use stage FK ───────────────────────
        migrations.AlterUniqueTogether(
            name='workflowstage',
            unique_together={('product', 'order'), ('product', 'stage')},
        ),
        # ── 6. Drop WorkflowStage.stage_type ──────────────────────────────
        migrations.RemoveField(model_name='workflowstage', name='stage_type'),
        # ── 7. Drop StageAccessRule entirely ──────────────────────────────
        migrations.DeleteModel(name='StageAccessRule'),
    ]
