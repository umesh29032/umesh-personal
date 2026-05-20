# `production` — Products, Adda, Workflows, Stage Records

## Models

```python
# production/models.py

class Product(TimeStampedModel):
    code         = CharField(max_length=30, unique=True)   # BEDSHEET, T-SHIRT
    name         = CharField(max_length=120)
    description  = TextField(blank=True)
    is_active    = BooleanField(default=True)
    adda_counter = PositiveIntegerField(default=0)         # per-product Adda numbering


class WorkflowStage(TimeStampedModel):
    class StageType(TextChoices):
        LAYERING = 'layering', 'Layering'
        CUTTING  = 'cutting',  'Cutting'
        # extend: PACKING, DELIVERY, ...

    product    = FK(Product, on_delete=CASCADE, related_name='workflow_stages')
    order      = PositiveIntegerField()
    stage_type = CharField(max_length=32, choices=StageType.choices)

    class Meta:
        unique_together = [('product', 'order'), ('product', 'stage_type')]
        ordering = ['product', 'order']


class Adda(TimeStampedModel):
    class Status(TextChoices):
        IN_PROGRESS = 'in_progress', 'In Progress'
        ON_HOLD     = 'on_hold',     'On Hold'
        COMPLETED   = 'completed',   'Completed'
        CANCELLED   = 'cancelled',   'Cancelled'

    code          = CharField(max_length=40, unique=True, editable=False)  # T-SHIRT-001
    product       = FK(Product, on_delete=PROTECT, related_name='addas')
    current_stage = FK(WorkflowStage, on_delete=PROTECT, null=True, blank=True, related_name='+')
    status        = CharField(max_length=16, choices=Status.choices, default=Status.IN_PROGRESS)
    started_at    = DateTimeField(auto_now_add=True)
    completed_at  = DateTimeField(null=True, blank=True)
    created_by    = FK(settings.AUTH_USER_MODEL, on_delete=PROTECT, null=True, related_name='+')

    class Meta:
        indexes = [
            Index(fields=['status']),
            Index(fields=['product', 'status']),
            Index(fields=['current_stage']),
        ]
        ordering = ['-started_at']


class AddaStageRecord(TimeStampedModel):
    """Common parent for all stage records. One row per (Adda, WorkflowStage)."""
    adda           = FK(Adda, on_delete=CASCADE, related_name='stage_records')
    workflow_stage = FK(WorkflowStage, on_delete=PROTECT, related_name='+')
    workers        = M2M(settings.AUTH_USER_MODEL,
                         related_name='stage_assignments', blank=True)
    completed_at   = DateTimeField(null=True, blank=True)
    completed_by   = FK(settings.AUTH_USER_MODEL, on_delete=PROTECT, null=True, related_name='+')

    class Meta:
        unique_together = [('adda', 'workflow_stage')]
        ordering = ['adda', 'workflow_stage__order']


class LayeringRecord(TimeStampedModel):
    stage_record     = OneToOneField(AddaStageRecord, on_delete=CASCADE, related_name='layering')
    lay_count        = PositiveIntegerField()                              # manual: layers laid on table
    total_colors     = PositiveIntegerField()                              # snapshot of distinct color count
    duration_minutes = PositiveIntegerField()                              # manual: time spent
    rolls_used       = M2M('raw_materials.ClothRoll', related_name='layering_records')
    started_at       = DateTimeField(auto_now_add=True)
    notes            = TextField(blank=True)


class CuttingRecord(TimeStampedModel):
    stage_record = OneToOneField(AddaStageRecord, on_delete=CASCADE, related_name='cutting')
    pieces_cut   = PositiveIntegerField()                                 # triggers BatchBarcode gen
    notes        = TextField(blank=True)
```

### Key model decisions
- `Adda.code` editable=False; generated atomically in `AddaService.create_adda` (see below).
- `AddaStageRecord` is the polymorphic seam — every stage type hangs a typed record off it via `OneToOneField`.
- `Adda.current_stage` points at the **next pending** WorkflowStage; goes `null` when status=COMPLETED.
- `workers` M2M lifts to parent → every stage type tracks workers uniformly. Future `expense.StageWorkAssignment` slots in as `through=`.
- `LayeringRecord.rolls_used` is M2M (not derived) — freezes the snapshot at completion so history survives later roll edits.
- `total_colors` is stored, not derived — preserves snapshot, saves a `COUNT(DISTINCT)` per dashboard row.

## Atomic Adda code generation

```python
# production/services/adda_service.py

@transaction.atomic
def create_adda(user, product):
    prod = Product.objects.select_for_update().get(pk=product.pk)   # blocks concurrent inserts
    prod.adda_counter += 1
    prod.save(update_fields=['adda_counter'])

    first_stage = prod.workflow_stages.order_by('order').first()
    adda = Adda.objects.create(
        code          = f"{prod.code}-{prod.adda_counter:03d}",
        product       = prod,
        current_stage = first_stage,
        created_by    = user,
    )
    history_service.log_adda(adda, AddaHistory.ChangeType.CREATED, user)
    return adda
```

## Stage advancement

`AddaStageService.complete_*` writes the typed record, attaches workers, then calls `_advance_to_next_stage`.

```python
# production/services/stage_service.py

@transaction.atomic
def complete_layering(adda, lay_count, duration_minutes, worker_ids, notes, user):
    stage = adda.current_stage
    if stage is None or stage.stage_type != WorkflowStage.StageType.LAYERING:
        raise ValidationError("Adda is not at Layering stage")

    sr = AddaStageRecord.objects.create(
        adda=adda, workflow_stage=stage,
        completed_at=timezone.now(), completed_by=user,
    )
    sr.workers.set(worker_ids)

    rolls = list(adda.rolls.all())
    total_colors = ClothRoll.objects.filter(adda=adda).values('cloth_color').distinct().count()

    lr = LayeringRecord.objects.create(
        stage_record=sr, lay_count=lay_count,
        total_colors=total_colors, duration_minutes=duration_minutes,
        notes=notes,
    )
    lr.rolls_used.set(rolls)
    _advance_to_next_stage(adda, user)
    return lr


@transaction.atomic
def complete_cutting(adda, pieces_cut, worker_ids, notes, user):
    stage = adda.current_stage
    if stage is None or stage.stage_type != WorkflowStage.StageType.CUTTING:
        raise ValidationError("Adda is not at Cutting stage")

    sr = AddaStageRecord.objects.create(
        adda=adda, workflow_stage=stage,
        completed_at=timezone.now(), completed_by=user,
    )
    sr.workers.set(worker_ids)
    cr = CuttingRecord.objects.create(stage_record=sr, pieces_cut=pieces_cut, notes=notes)

    barcode_service.generate_for_cutting(cr)   # bulk_create N rows
    _advance_to_next_stage(adda, user)
    return cr


def _advance_to_next_stage(adda, user):
    """Bump current_stage by order. Mark Adda completed when no next stage."""
    cur = adda.current_stage
    nxt = adda.product.workflow_stages.filter(order__gt=cur.order).order_by('order').first()
    history_service.log_adda(
        adda, AddaHistory.ChangeType.STAGE_ADVANCED, user,
        stage_from=cur, stage_to=nxt,
    )
    if nxt is None:
        adda.status = Adda.Status.COMPLETED
        adda.completed_at = timezone.now()
        adda.current_stage = None
    else:
        adda.current_stage = nxt
    adda.save(update_fields=['current_stage', 'status', 'completed_at'])
```

## URLs

```
/production/                              dashboard
/production/products/                     list
/production/products/add/                 create   (super_admin only)
/production/products/<int:pk>/edit/       update
/production/products/<int:pk>/archive/    archive
/production/addas/                        list
/production/addas/start/                  create
/production/addas/<str:code>/             detail (tabs: rolls / stages / history)
/production/addas/<str:code>/layering/    complete layering
/production/addas/<str:code>/cutting/     complete cutting
/production/addas/<str:code>/advance/     advance stage (manual button)
```

## User dashboard query (worker view)

```python
# inventory/views/dashboard.py — add panel
my_active_stages = (
    AddaStageRecord.objects
    .filter(workers=request.user,
            completed_at__isnull=True,
            adda__status=Adda.Status.IN_PROGRESS)
    .select_related('adda', 'workflow_stage')
    .order_by('-created_at')
)
# template: "My Active Stages" — list of (adda.code, workflow_stage.stage_type)
```

## Templates

```
production/templates/production/
├── adda_dashboard.html        # KPI: in_progress / on_hold / completed today; stage filter pills
├── adda_list.html             # DataTable; current_stage + status badges
├── adda_detail.html           # tabs: rolls, stage timeline, history
├── adda_form.html             # picks product
├── layering_form.html         # lay_count, duration, worker chip picker
├── cutting_form.html          # pieces_cut, worker chip picker
└── product_list.html + _form.html + _confirm_archive.html
```
