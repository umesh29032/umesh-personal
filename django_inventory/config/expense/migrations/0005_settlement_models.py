"""Settlement schema: drop WorkerPayment, add PayrollSettlement +
PayrollSettlementItem + WorkerProfile, add ledger.settlement FK + categories.

Depends on 0004 (legacy-payroll clean) which removes the WorkerPayment rows +
PAYMENT/ADVANCE ledger debits in a prior transaction, so these ALTERs run with
no pending trigger events.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expense', '0004_clean_legacy_payroll'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workerledgerentry',
            name='payment',
        ),
        migrations.AlterField(
            model_name='workerledgerentry',
            name='category',
            field=models.CharField(choices=[('stage_earning', 'Stage Earning'), ('production_earning', 'Production Earning'), ('advance', 'Advance'), ('payment', 'Payment'), ('settlement_payment', 'Settlement Payment'), ('advance_recovery', 'Advance Recovery'), ('deduction', 'Deduction'), ('adjustment', 'Adjustment'), ('reversal', 'Reversal')], max_length=24),
        ),
        migrations.CreateModel(
            name='PayrollSettlement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reference', models.CharField(max_length=20, unique=True)),
                ('settlement_date', models.DateField()),
                ('payable_before', models.DecimalField(decimal_places=2, max_digits=12)),
                ('advance_outstanding_before', models.DecimalField(decimal_places=2, max_digits=12)),
                ('advance_deducted', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('amount_paid', models.DecimalField(decimal_places=2, max_digits=12)),
                ('method', models.CharField(choices=[('cash', 'Cash'), ('bank', 'Bank Transfer'), ('upi', 'UPI'), ('other', 'Other')], default='cash', max_length=8)),
                ('notes', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('worker', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='settlements', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-settlement_date', '-created_at'],
            },
        ),
        migrations.AddField(
            model_name='workerledgerentry',
            name='settlement',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ledger_entries', to='expense.payrollsettlement'),
        ),
        migrations.CreateModel(
            name='PayrollSettlementItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_recovered', models.DecimalField(decimal_places=2, max_digits=12)),
                ('advance', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='recoveries', to='expense.workeradvance')),
                ('settlement', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='items', to='expense.payrollsettlement')),
            ],
        ),
        migrations.CreateModel(
            name='WorkerProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('bank_account_name', models.CharField(blank=True, max_length=120)),
                ('bank_account_number', models.CharField(blank=True, max_length=40)),
                ('bank_ifsc', models.CharField(blank=True, max_length=20)),
                ('upi_id', models.CharField(blank=True, max_length=80)),
                ('joining_date', models.DateField(blank=True, null=True)),
                ('opening_advance', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('is_active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='worker_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.DeleteModel(
            name='WorkerPayment',
        ),
        migrations.AddIndex(
            model_name='payrollsettlement',
            index=models.Index(fields=['worker', '-settlement_date'], name='expense_pay_worker__f64c84_idx'),
        ),
        migrations.AddIndex(
            model_name='payrollsettlementitem',
            index=models.Index(fields=['advance'], name='expense_pay_advance_740cb6_idx'),
        ),
    ]
