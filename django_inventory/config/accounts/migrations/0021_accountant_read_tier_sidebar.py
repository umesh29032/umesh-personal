"""Owner ruling 2026-08-02 — give the `accountant` role a job it can actually do.

CONTEXT. Every financial page was `_ManagementOnly`, i.e. read AND write behind one
gate. So a *pure* accountant login had **no reachable page at all**: their
`FINANCIAL_ROLES` capability (view + edit Supplier and Cost Per KG) was unreachable
dead code, and their dashboard showed WORKER copy ("Jab manager aapko kaam dega").

The code half of the fix lives in `permission_service.FINANCIAL_READ_ROLES`, the
`_FinancialRead` view mixin and `ProductionOrAccountantMixin`. This migration is the
DATA half: any menu item that already has a `SidebarItemRule` row is governed by the
DB, and the DB **overrides** the in-code predicate — so widening the predicate alone
would have left the accountant locked out of exactly those items.

`raw_materials:roll-list` is the one that matters: it had `roles=['manager']`, so
without this row-edit the accountant still could not open the page their whole role
exists for.

WRITES ARE NOT TOUCHED. `expense:advance-add`, settlement start/finalize, pay-basis,
FnF, expense void and template edits all keep management/super-admin gates at BOTH
the view and the service layer. Settlement remains the single money-write boundary.

Reversible: `unseed` removes ONLY the accountant from the rows this added it to, so
running it backwards restores the previous configuration exactly without disturbing
whatever the owner has since ticked for other roles.
"""
from django.db import migrations

ROLE_CODE = 'accountant'

# Rows the accountant is added to. Reads only — every one of these is a list,
# detail or report page.
GRANT_URL_NAMES = (
    'raw_materials:roll-list',   # THE one: supplier + cost-per-kg live here
)


def seed(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    SidebarItemRule = apps.get_model('accounts', 'SidebarItemRule')
    role = Role.objects.filter(code=ROLE_CODE).first()
    if role is None:          # pragma: no cover - role seeded long before this
        return
    for rule in SidebarItemRule.objects.filter(url_name__in=GRANT_URL_NAMES):
        # .add() is idempotent and leaves every other role on the row untouched.
        rule.allowed_roles.add(role)


def unseed(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    SidebarItemRule = apps.get_model('accounts', 'SidebarItemRule')
    role = Role.objects.filter(code=ROLE_CODE).first()
    if role is None:          # pragma: no cover
        return
    for rule in SidebarItemRule.objects.filter(url_name__in=GRANT_URL_NAMES):
        rule.allowed_roles.remove(role)


class Migration(migrations.Migration):
    dependencies = [('accounts', '0020_student_role_and_learning_access')]
    operations = [migrations.RunPython(seed, unseed)]
