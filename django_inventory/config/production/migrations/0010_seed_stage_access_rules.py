"""Seed default StageAccessRule rows so existing skill gates keep working
after the hardcoded _access_for() is replaced by DB lookups.

Mirrors the pre-existing hardcoded logic from production/views/adda_views.py:
  layering → cutting_master + cutting_master_helper
  cutting  → cutting_master

Super Admin + Manager are always allowed at the service layer (built-in),
so they don't need to be seeded as Role rows.
"""
from django.db import migrations


LAYERING_SKILLS = ['cutting_master', 'cutting_master_helper']
CUTTING_SKILLS = ['cutting_master']


def seed_rules(apps, schema_editor):
    StageAccessRule = apps.get_model('production', 'StageAccessRule')
    Skill = apps.get_model('accounts', 'Skill')

    def _rule_with_skills(stage_type, skill_names):
        rule, _ = StageAccessRule.objects.get_or_create(stage_type=stage_type)
        skills = list(Skill.objects.filter(name__in=skill_names))
        rule.allowed_skills.set(skills)
        return rule

    _rule_with_skills('layering', LAYERING_SKILLS)
    _rule_with_skills('cutting', CUTTING_SKILLS)


def unseed_rules(apps, schema_editor):
    StageAccessRule = apps.get_model('production', 'StageAccessRule')
    StageAccessRule.objects.filter(stage_type__in=['layering', 'cutting']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('production', '0009_stage_access_rule'),
        ('accounts', '0010_add_cutting_master_helper_skill'),
    ]

    operations = [
        migrations.RunPython(seed_rules, unseed_rules),
    ]
