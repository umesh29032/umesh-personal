"""Owner ruling 2026-08-02: `/learn/` becomes a controlled, read-only surface.

WHY. The course reader shipped ungated — every authenticated user saw "Learn",
including factory workers, who have no use for SQL/deployment courses. The owner
wants to hand the link to peers (and, later, to paying students) WITHOUT exposing
the factory. So:

  1. a new **`student`** role — can log in, read courses, touch no business data;
  2. a `SidebarItemRule` for `learning:index` so the **Access Control page owns the
     switch** from now on (tick a role → that role sees Learn; untick → it does not).

`super_admin` is never listed: the service layer always lets it through, by design,
so an admin cannot lock themselves out (accounts.models.SidebarItemRule docstring).

`manager` is deliberately NOT seeded. Add it in Access Control if the owner wants
managers to have the courses — that is exactly the choice this row now enables.

⚠️ The rule row alone is NOT the whole gate. `can_access_url_name()` returns True
for any url_name with no rule, so a row on `learning:index` would block `/learn/`
while leaving `/learn/sql/14-indexes/` reachable by typing it. The companion change
in `learning/views.py` makes EVERY learning view honour this single row, which is
the documented "the view's own mixin gates it = defense in depth" contract.

`is_system=True` on the role: it now backs an access rule, so deleting it from the
Role editor would silently strip access from every student. System roles cannot be
deleted — that is the protection we want here.
"""
from django.db import migrations

ROLE_CODE = 'student'
ROLE_NAME = 'Student'
ROLE_DESCRIPTION = (
    'Read-only learner. Sees the /learn/ courses and nothing else — no production, '
    'no money, no factory data. Intended for peers and (later) paying students.'
)

# section + label must match the MenuItem in permission_service.SIDEBAR so the
# Access Control page renders this row under the right heading.
ITEM = ('Main', 'Learn', 'learning:index')


def seed(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    SidebarItemRule = apps.get_model('accounts', 'SidebarItemRule')

    role, _ = Role.objects.update_or_create(
        code=ROLE_CODE,
        defaults={'name': ROLE_NAME,
                  'description': ROLE_DESCRIPTION,
                  'is_system': True},
    )
    # No permissions on purpose: a student holds ZERO business permissions. Their
    # only reach is the learning app, granted by the rule below.
    role.permissions.clear()

    section, label, url_name = ITEM
    rule, _ = SidebarItemRule.objects.update_or_create(
        url_name=url_name, defaults={'section': section, 'label': label})
    rule.allowed_roles.set([role])
    rule.allowed_skills.clear()   # skills are production-stage access; irrelevant here


def unseed(apps, schema_editor):
    """Reverse cleanly: drop the rule (Learn returns to ungated) and the role.

    Users still pointing at the role would be left role-less, so we only delete the
    role when nothing references it — losing a rule is recoverable, silently
    orphaning users is not.
    """
    Role = apps.get_model('accounts', 'Role')
    SidebarItemRule = apps.get_model('accounts', 'SidebarItemRule')
    SidebarItemRule.objects.filter(url_name=ITEM[2]).delete()
    role = Role.objects.filter(code=ROLE_CODE).first()
    # related_name='users' on User.role (accounts/models.py:190) — NOT user_set.
    if role is not None and not role.users.exists():
        role.delete()


class Migration(migrations.Migration):
    dependencies = [('accounts', '0019_seed_my_assigned_work_sidebar')]
    operations = [migrations.RunPython(seed, unseed)]
