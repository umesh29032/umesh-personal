"""
Migration 0012: Dynamic UserType model + free-form Skill (remove hardcoded choices).

Changes:
  1. Create UserType model (code, label, description, is_active).
  2. Skill: add `label` + `description` fields; alter `name` to SlugField (drop choices).
  3. User: add `user_type_fk` FK column (nullable); remove old `user_type` CharField;
     rename `user_type_fk` → `user_type`.

Data migrations (RunPython):
  a. Seed 5 UserType rows from the old USER_TYPE_CHOICES.
  b. Populate Skill.label from old SKILL_TYPE_CHOICES display values.
  c. Map each User's old user_type string → UserType FK.
"""
from django.db import migrations, models
import django.db.models.deletion


# Old USER_TYPE_CHOICES values → (code, label) pairs for seeding.
_USER_TYPES = [
    ('superadmin', 'Super Admin'),
    ('admin',      'Admin'),
    ('worker',     'Worker'),
    ('supplier',   'Supplier'),
    ('normal',     'Normal User'),
]

# Old SKILL_TYPE_CHOICES display values for back-filling Skill.label.
_SKILL_LABELS = {
    'cutting_master':        'Cutting Master',
    'cutting_master_helper': 'Cutting Master Helper',
    'dhage_katne_wala':      'Dhage Katne Wala',
    'embroidery':            'Embroidery',
    'tailoring':             'Tailoring',
    'other':                 'Other',
}


def seed_user_types(apps, schema_editor):
    """Create UserType rows from the old hardcoded choices."""
    UserType = apps.get_model('accounts', 'UserType')
    for code, label in _USER_TYPES:
        UserType.objects.get_or_create(code=code, defaults={'label': label})


def backfill_skill_labels(apps, schema_editor):
    """Populate Skill.label from old choices display values."""
    Skill = apps.get_model('accounts', 'Skill')
    for skill in Skill.objects.all():
        if not skill.label:
            skill.label = _SKILL_LABELS.get(skill.name, skill.name.replace('_', ' ').title())
            skill.save(update_fields=['label'])


def migrate_user_type_to_fk(apps, schema_editor):
    """Map each User's old user_type CharField value → UserType FK."""
    User = apps.get_model('accounts', 'User')
    UserType = apps.get_model('accounts', 'UserType')
    type_map = {ut.code: ut for ut in UserType.objects.all()}
    for user in User.objects.all():
        # At this point in the migration, `user_type` is still the old CharField.
        old_code = user.user_type or 'worker'
        user.user_type_fk = type_map.get(old_code, type_map.get('worker'))
        user.save(update_fields=['user_type_fk'])


def reverse_user_type_fk(apps, schema_editor):
    """Reverse: copy FK code back to the old CharField before re-adding it."""
    User = apps.get_model('accounts', 'User')
    for user in User.objects.select_related('user_type_fk').all():
        if user.user_type_fk:
            user.user_type = user.user_type_fk.code
            user.save(update_fields=['user_type'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_alter_user_user_type'),
    ]

    operations = [
        # ── 1. Create UserType model ────────────────────────────────────────
        migrations.CreateModel(
            name='UserType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(max_length=32, unique=True, help_text="Stable identifier (e.g. 'worker'). Never change after seeding.")),
                ('label', models.CharField(max_length=64, help_text="Display name shown in UI (e.g. 'Worker').")),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['label'], 'verbose_name': 'User Type', 'verbose_name_plural': 'User Types'},
        ),

        # ── 2a. Seed UserType rows ──────────────────────────────────────────
        migrations.RunPython(seed_user_types, reverse_code=migrations.RunPython.noop),

        # ── 3a. Skill: rename old `name` → temp hold (keep data) ────────────
        # Add label + description to Skill (nullable first, back-fill, then set not-null)
        migrations.AddField(
            model_name='skill',
            name='label',
            field=models.CharField(max_length=100, default='', help_text="Human-readable display name (e.g. 'Cutting Master')."),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='skill',
            name='description',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),

        # ── 3b. Back-fill Skill.label from old choices display values ───────
        migrations.RunPython(backfill_skill_labels, reverse_code=migrations.RunPython.noop),

        # ── 3c. Alter Skill.name: drop choices constraint, change to SlugField
        migrations.AlterField(
            model_name='skill',
            name='name',
            field=models.SlugField(
                max_length=64, unique=True,
                help_text="Stable code key (e.g. 'cutting_master'). Must match skills.py constant if used in services.",
            ),
        ),

        # ── 4a. Add new FK column alongside old CharField ───────────────────
        migrations.AddField(
            model_name='user',
            name='user_type_fk',
            field=models.ForeignKey(
                'accounts.UserType',
                on_delete=django.db.models.deletion.SET_NULL,
                null=True, blank=True,
                related_name='users',
                verbose_name='User Type',
                help_text='What type of user this is (display/classification only). Role controls access.',
            ),
        ),

        # ── 4b. Copy old user_type string → FK ─────────────────────────────
        migrations.RunPython(migrate_user_type_to_fk, reverse_code=reverse_user_type_fk),

        # ── 4c. Remove old CharField ────────────────────────────────────────
        migrations.RemoveField(model_name='user', name='user_type'),

        # ── 4d. Rename FK → user_type ───────────────────────────────────────
        migrations.RenameField(model_name='user', old_name='user_type_fk', new_name='user_type'),
    ]
