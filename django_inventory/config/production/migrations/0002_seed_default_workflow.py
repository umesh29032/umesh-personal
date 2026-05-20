"""5 products + unka [layering, cutting] workflow seed migration.

YEH FILE KYU HAI?
─────────────────
Day-zero pe products aur unke workflow stages exist hone chahiye — warna user
Adda nahi start kar paayega (create_adda service first_stage check karta hai).

V1 hardcode kyun?
────────────────
WorkflowStage CRUD UI defer kiya gaya — naya product workflow rare event hai,
data migration likhna acceptable hai (production team flag kar dega).
"""
from django.db import migrations


PRODUCTS = [
    ('3-PATTI', '3 Patti'),
    ('T-SHIRT', 'T-Shirt'),
    ('NIKKAR',  'Nikkar'),
    ('PAJAMA',  'Pajama'),
    ('1-6',     '1-6'),
]
# Saare products ka same workflow for v1 — future me per-product custom flows
STAGES = [(1, 'layering'), (2, 'cutting')]


def forwards(apps, schema_editor):
    """Products + WorkflowStages seed. get_or_create se re-run safe (idempotent)."""
    Product = apps.get_model('production', 'Product')
    WorkflowStage = apps.get_model('production', 'WorkflowStage')
    for code, name in PRODUCTS:
        prod, _ = Product.objects.get_or_create(code=code, defaults={'name': name})
        for order, stage_type in STAGES:
            WorkflowStage.objects.get_or_create(
                product=prod, order=order,
                defaults={'stage_type': stage_type},
            )


def reverse(apps, schema_editor):
    """`migrate production 0001` chala to ye undo — Products delete.
    CASCADE FK ki wajah se WorkflowStage rows bhi automatically delete ho jaayengi."""
    apps.get_model('production', 'Product').objects.filter(
        code__in=[c for c, _ in PRODUCTS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [('production', '0001_initial')]
    operations = [migrations.RunPython(forwards, reverse)]
