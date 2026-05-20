# Migrations & Seed Data Plan

## Migration order

| # | App / Migration | Purpose |
|---|---|---|
| 1 | `inventory/000N_add_accountant_role.py` | data: add `ROLE_ACCOUNTANT` to Role table |
| 2 | `raw_materials/0001_initial.py` | schema: ClothType, ClothColor, StorageLocation, ClothRoll |
| 3 | `raw_materials/0002_create_roll_id_sequence.py` | `RunSQL CREATE SEQUENCE cloth_roll_seq` |
| 4 | `production/0001_initial.py` | schema: Product, WorkflowStage, Adda, AddaStageRecord, LayeringRecord, CuttingRecord |
| 5 | `tracking/0001_initial.py` | schema: BatchBarcode, ClothRollHistory, AddaHistory, ProductHistory |
| 6 | `production/0002_seed_default_workflow.py` | data: 5 products + `[layering, cutting]` workflow each |
| 7 | `raw_materials/0003_seed_master_data.py` | data: storage locations, cloth types, cloth colors |

Order is enforced via Django `Migration.dependencies`. Cross-app FK `ClothRoll.adda -> 'production.Adda'` makes raw_materials depend on production at FK-resolution time.

## Postgres sequence migration

```python
# raw_materials/migrations/0002_create_roll_id_sequence.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [('raw_materials', '0001_initial')]
    operations = [
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS cloth_roll_seq START 1;",
            reverse_sql="DROP SEQUENCE IF EXISTS cloth_roll_seq;",
        ),
    ]
```

Postgres-only — note in ARCHITECTURE.md. If SQLite tests are needed, gate via `connection.vendor == 'postgresql'` in service.

## Workflow seed

```python
# production/migrations/0002_seed_default_workflow.py
from django.db import migrations

PRODUCTS = [
    ('3-PATTI', '3 Patti'),
    ('T-SHIRT', 'T-Shirt'),
    ('NIKKAR',  'Nikkar'),
    ('PAJAMA',  'Pajama'),
    ('1-6',     '1-6'),
]
STAGES = [(1, 'layering'), (2, 'cutting')]

def forwards(apps, schema_editor):
    Product       = apps.get_model('production', 'Product')
    WorkflowStage = apps.get_model('production', 'WorkflowStage')
    for code, name in PRODUCTS:
        prod, _ = Product.objects.get_or_create(code=code, defaults={'name': name})
        for order, stage_type in STAGES:
            WorkflowStage.objects.get_or_create(
                product=prod, order=order, defaults={'stage_type': stage_type},
            )

def reverse(apps, schema_editor):
    apps.get_model('production', 'Product').objects.filter(
        code__in=[c for c, _ in PRODUCTS]
    ).delete()

class Migration(migrations.Migration):
    dependencies = [('production', '0001_initial')]
    operations = [migrations.RunPython(forwards, reverse)]
```

Resulting Adda codes will read:
- `3-PATTI-001`, `T-SHIRT-001`, `NIKKAR-001`, `PAJAMA-001`, `1-6-001`

Note on `1-6` code: hyphen + digits valid in URL via `<str:code>`. Barcode parsing stays predictable since `piece_seq` is always the last `-NNNN` group (e.g. `1-6-001-0042` → adda=`1-6-001`, piece=`0042`).

## Master data seed

```python
# raw_materials/migrations/0003_seed_master_data.py
LOCATIONS = [
    ('Packing Factory', 'PACKING'),
    ('Rohini Factory',  'ROHINI'),
]
CLOTH_TYPES  = ['Cotton', 'Polyester', 'Silk', 'Linen']
CLOTH_COLORS = ['Red', 'Blue', 'Green', 'White', 'Black', 'Yellow']

def forwards(apps, schema_editor):
    ClothType       = apps.get_model('raw_materials', 'ClothType')
    ClothColor      = apps.get_model('raw_materials', 'ClothColor')
    StorageLocation = apps.get_model('raw_materials', 'StorageLocation')

    for name, code in LOCATIONS:
        StorageLocation.objects.get_or_create(code=code, defaults={'name': name})
    for n in CLOTH_TYPES:
        ClothType.objects.get_or_create(name=n)
    for n in CLOTH_COLORS:
        ClothColor.objects.get_or_create(name=n)

def reverse(apps, schema_editor):
    apps.get_model('raw_materials', 'StorageLocation').objects.filter(
        code__in=[c for _, c in LOCATIONS]
    ).delete()
    apps.get_model('raw_materials', 'ClothType').objects.filter(name__in=CLOTH_TYPES).delete()
    apps.get_model('raw_materials', 'ClothColor').objects.filter(name__in=CLOTH_COLORS).delete()
```

## Migration discipline

- Data migrations always use `apps.get_model('app', 'Model')` — never direct import.
- Every data migration includes reverse function.
- Cross-app data migration only in `inventory` (where Role lives).
- No `RunPython` body imports business logic from `services/` — historical apps registry only.

## requirements.txt additions

```
qrcode[pil]==7.4.2
```

`python-barcode` not needed — QR-only per [TRACKING.md](TRACKING.md) Decision #12.

## settings.py addition

```python
# config/settings/base.py
INSTALLED_APPS = [
    ...
    'raw_materials',
    'production',
    'tracking',
    # 'expense',   # future
]
```

App labels match directory names. Use `default_auto_field = 'django.db.models.BigAutoField'` in each `apps.py` to match the project default.
