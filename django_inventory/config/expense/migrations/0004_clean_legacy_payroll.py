"""Clean ledger debits that no longer fit the settlement model.

Runs as its own migration (separate transaction) BEFORE the schema change in
0005 — Postgres refuses to ALTER a table in the same transaction as a DELETE
with pending deferred-FK triggers.

Under the settlement design (docs/production/SETTLEMENT_ARCHITECTURE.md):
  • ADVANCE debits go away — advances are a SEPARATE loan pool, recovered at
    settlement, never a payable debit. WorkerAdvance rows are KEPT (they ARE the
    outstanding pool now).
  • PAYMENT debits + WorkerPayment rows go away — replaced by PayrollSettlement.
Earning credits + StageWorkAssignment rows are PRESERVED (earnings unchanged).
Dev test data only.
"""
from django.db import migrations


def clean_legacy_payroll(apps, schema_editor):
    L = apps.get_model('expense', 'WorkerLedgerEntry')
    WorkerPayment = apps.get_model('expense', 'WorkerPayment')
    L.objects.filter(category__in=['advance', 'payment']).delete()
    WorkerPayment.objects.all().delete()


def _noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('expense', '0003_workerledgerentry_uniq_one_reversal_per_entry'),
    ]

    operations = [
        migrations.RunPython(clean_legacy_payroll, _noop),
    ]
