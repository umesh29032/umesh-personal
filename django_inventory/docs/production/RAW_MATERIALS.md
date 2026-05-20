# `raw_materials` — Cloth Inventory & Master Data

## Models

```python
# raw_materials/models.py

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class ClothType(TimeStampedModel):
    name      = CharField(max_length=80, unique=True)
    is_active = BooleanField(default=True)


class ClothColor(TimeStampedModel):
    name      = CharField(max_length=80, unique=True)
    hex_code  = CharField(max_length=7, blank=True)   # optional UI swatch
    is_active = BooleanField(default=True)


class StorageLocation(TimeStampedModel):
    name      = CharField(max_length=120, unique=True)
    code      = CharField(max_length=20, unique=True)   # PACKING, ROHINI
    is_active = BooleanField(default=True)


WIDTH_CHOICES = [(i, f'{i}"') for i in range(36, 45)]   # 36..44 inches


class ClothRoll(TimeStampedModel):
    class Status(TextChoices):
        NOT_USED = 'not_used', 'Not Used'
        USED     = 'used',     'Used'

    roll_id          = CharField(max_length=20, unique=True, editable=False)
    purchased_date   = DateField()
    cloth_type       = FK(ClothType,  on_delete=PROTECT, related_name='rolls')
    cloth_color      = FK(ClothColor, on_delete=PROTECT, related_name='rolls')
    width_inch       = IntegerField(choices=WIDTH_CHOICES, null=True, blank=True)
    weight_kg        = DecimalField(8, 2, null=True, blank=True)
    supplier         = CharField(max_length=200, blank=True)        # role-gated
    cost_per_kg      = DecimalField(10, 2, null=True, blank=True)   # role-gated
    storage_location = FK(StorageLocation, on_delete=PROTECT, related_name='rolls')
    adda             = FK('production.Adda', on_delete=PROTECT, null=True, blank=True, related_name='rolls')
    status           = CharField(max_length=16, choices=Status.choices, default=Status.NOT_USED)
    used_at          = DateTimeField(null=True, blank=True)
    used_by          = FK(settings.AUTH_USER_MODEL, on_delete=PROTECT, null=True, blank=True, related_name='+')

    class Meta:
        indexes = [
            Index(fields=['status']),
            Index(fields=['cloth_type', 'cloth_color']),
            Index(fields=['storage_location', 'status']),
        ]
        ordering = ['-created_at']
```

### Key model decisions
- `roll_id` is `editable=False` — only `RollService.bulk_create_rolls` writes it.
- `weight_kg` + `width_inch` nullable — captured at assignment, **not** at intake.
- `adda` FK uses string `'production.Adda'` to avoid circular import.
- `PROTECT` everywhere on master-data FKs — soft archive via `is_active` only.

## Roll ID generation

Postgres sequence created in dedicated migration. Service-only writer.

```python
# raw_materials/migrations/0002_create_roll_id_sequence.py
operations = [
    migrations.RunSQL(
        sql="CREATE SEQUENCE IF NOT EXISTS cloth_roll_seq START 1;",
        reverse_sql="DROP SEQUENCE IF EXISTS cloth_roll_seq;",
    )
]

# raw_materials/services/roll_service.py
def _next_roll_id():
    with connection.cursor() as cur:
        cur.execute("SELECT nextval('cloth_roll_seq')")
        n = cur.fetchone()[0]
    return f"CR-{n:06d}"
```

## Service surface

```python
# raw_materials/services/roll_service.py

@transaction.atomic
def bulk_create_rolls(user, *, cloth_type, location, purchased_date,
                      supplier=None, cost_per_kg=None, breakup):
    """
    breakup: list[{'color': ClothColor, 'qty': int}]
    Returns: list[ClothRoll]
    Raises: PermissionDenied if supplier/cost_per_kg set by non-accountant.
    """
    if (supplier or cost_per_kg is not None) and not user_can_edit_financials(user):
        raise PermissionDenied("supplier / cost_per_kg restricted")

    rolls = []
    for row in breakup:
        for _ in range(row['qty']):
            rolls.append(ClothRoll(
                roll_id          = _next_roll_id(),
                purchased_date   = purchased_date,
                cloth_type       = cloth_type,
                cloth_color      = row['color'],
                storage_location = location,
                supplier         = supplier or '',
                cost_per_kg      = cost_per_kg,
            ))
    ClothRoll.objects.bulk_create(rolls)
    for r in rolls:
        history_service.log_roll(r, ClothRollHistory.ChangeType.CREATED, user)
    return rolls


@transaction.atomic
def assign_roll_to_adda(user, roll, adda, weight_kg, width_inch):
    if roll.status != ClothRoll.Status.NOT_USED:
        raise ValidationError("roll already used")
    if adda.status != Adda.Status.IN_PROGRESS:
        raise ValidationError(f"Adda {adda.code} is not in-progress")
    if adda.current_stage.stage_type != WorkflowStage.StageType.LAYERING:
        raise ValidationError("rolls only assignable during Layering stage")

    roll.adda = adda
    roll.weight_kg = weight_kg
    roll.width_inch = width_inch
    roll.status = ClothRoll.Status.USED
    roll.used_at = timezone.now()
    roll.used_by = user
    roll.save(update_fields=['adda','weight_kg','width_inch','status','used_at','used_by'])

    history_service.log_roll(
        roll, ClothRollHistory.ChangeType.STATUS_CHANGED, user,
        field_name='status', old_value='not_used', new_value='used',
        note=f"assigned to {adda.code}",
    )
    history_service.log_adda(adda, AddaHistory.ChangeType.ROLL_ASSIGNED, user, roll=roll)
    return roll


# raw_materials/services/master_service.py
@transaction.atomic
def archive_cloth_type(user, ct):
    ct.is_active = False
    ct.save(update_fields=['is_active'])
    # no history table for master data in v1; can add MasterHistory later if needed

@transaction.atomic
def hard_delete_master(user, instance):
    """Only allowed when usage_count == 0. Form/view computes usage and disables button otherwise."""
    instance.delete()  # PROTECT FK will raise if still in use — defensive
```

## URLs

```
/raw-materials/                          dashboard       (RoleRequiredMixin: PRODUCTION_ROLES)
/raw-materials/rolls/                    list
/raw-materials/rolls/bulk-add/           bulk create
/raw-materials/rolls/<int:pk>/           detail (+ history timeline)
/raw-materials/rolls/<int:pk>/edit/      update
/raw-materials/rolls/<int:pk>/assign/    assign to Adda
/raw-materials/cloth-types/              list + CRUD
/raw-materials/cloth-colors/             list + CRUD
/raw-materials/storage-locations/        list + CRUD
```

## Templates

Per `feedback_ui_polish` + `project_form_shell`: hero strip + numbered panels + cream inputs + sticky CTA on every create/edit. Page CSS scoped under page class in `{% block extra_head %}`.

```
raw_materials/templates/raw_materials/
├── cloth_dashboard.html                # KPI: total rolls, available, used, location breakdown
├── roll_list.html                      # DataTable; filters OUTSIDE .table-responsive
├── roll_bulk_form.html                 # two-step shell: meta + (color, qty) rows
├── roll_detail.html                    # info + ClothRollHistory timeline
├── roll_assign_form.html               # picks Adda; user enters weight + width
├── cloth_type_list.html  + _form.html  + _confirm_archive.html
├── cloth_color_list.html + _form.html  + _confirm_archive.html
└── storage_list.html     + _form.html  + _confirm_archive.html
```

## Bulk roll form shape

Single page. Shared meta on top, breakup rows below.

```
ClothType:        [Cotton    ▾]
Purchase date:    [2026-05-19]
Storage location: [Rohini    ▾]
Supplier:         [...]                 ← rendered only if user_can_edit_financials
Cost per KG:      [...]                 ← same

Breakup
  + Add row
  Color [Red   ▾]  Qty [80]
  Color [Blue  ▾]  Qty [70]
  Total: 150 rolls

[Submit]  →  RollService.bulk_create_rolls(...) → 150 ClothRoll objects, sequential roll_ids
```

`breakup` is a JS-driven repeating row group; server receives parallel arrays (`color[]`, `qty[]`) and parses into the list passed to the service.
