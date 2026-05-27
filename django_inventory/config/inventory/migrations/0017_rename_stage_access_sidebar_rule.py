"""Rename the SidebarItemRule from the legacy 'production:stage-access' URL
to the new 'production:stage-list'. Migration 0015 was authored before the
Stage Access page was rebuilt into a full Stage CRUD library, so its seed
points at a URL that no longer resolves. Fresh installs need this rename
before any non-superadmin can see the Stages menu entry.
"""
from django.db import migrations


def rename(apps, schema_editor):
    SidebarItemRule = apps.get_model('inventory', 'SidebarItemRule')
    rule = SidebarItemRule.objects.filter(url_name='production:stage-access').first()
    if rule is None:
        return
    target = SidebarItemRule.objects.filter(url_name='production:stage-list').first()
    if target is not None:
        # Merge: copy any granted roles/skills onto the existing target row,
        # then drop the legacy row so url_name stays unique.
        target.allowed_roles.add(*rule.allowed_roles.all())
        target.allowed_skills.add(*rule.allowed_skills.all())
        rule.delete()
        return
    rule.url_name = 'production:stage-list'
    rule.label = 'Stages'
    rule.save(update_fields=['url_name', 'label'])


def unrename(apps, schema_editor):
    SidebarItemRule = apps.get_model('inventory', 'SidebarItemRule')
    rule = SidebarItemRule.objects.filter(url_name='production:stage-list').first()
    if rule is None:
        return
    rule.url_name = 'production:stage-access'
    rule.label = 'Stage Access'
    rule.save(update_fields=['url_name', 'label'])


class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0016_sidebar_item_rule_skills'),
    ]
    operations = [
        migrations.RunPython(rename, unrename),
    ]
