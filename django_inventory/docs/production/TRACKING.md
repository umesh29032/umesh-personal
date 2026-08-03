---
id: production-tracking
type: topic-canonical
status: active
owner: handwritten
scope: production subsystem
anchors: —
verified: 2026-07-13
---

# `tracking` — Barcodes + Per-Domain Audit History

## Models

```python
# tracking/models.py

class BatchBarcode(TimeStampedModel):
    class Status(TextChoices):
        PENDING    = 'pending',    'Pending'      # generated, not yet attached/scanned
        PACKED     = 'packed',     'Packed'
        DISPATCHED = 'dispatched', 'Dispatched'
        MISSING    = 'missing',    'Missing'

    adda            = FK('production.Adda', on_delete=PROTECT, related_name='barcodes')
    piece_seq       = PositiveIntegerField()                          # 1..N
    value           = CharField(max_length=60, unique=True)           # T-SHIRT-001-0042
    status          = CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    last_scanned_at = DateTimeField(null=True, blank=True)
    last_scanned_by = FK(settings.AUTH_USER_MODEL, on_delete=PROTECT, null=True, blank=True, related_name='+')

    class Meta:
        unique_together = [('adda', 'piece_seq')]
        indexes = [Index(fields=['adda', 'status']), Index(fields=['status'])]
        ordering = ['adda', 'piece_seq']


class ClothRollHistory(TimeStampedModel):
    class ChangeType(TextChoices):
        CREATED        = 'created',         'Created'
        STATUS_CHANGED = 'status_changed',  'Status Changed'
        LOCATION_MOVED = 'location_moved',  'Location Moved'
        WEIGHT_UPDATED = 'weight_updated',  'Weight Updated'
        ARCHIVED       = 'archived',        'Archived'

    roll        = FK('raw_materials.ClothRoll', on_delete=PROTECT, related_name='history')
    change_type = CharField(max_length=32, choices=ChangeType.choices)
    actor       = FK(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name='+')
    field_name  = CharField(max_length=64, blank=True)
    old_value   = CharField(max_length=200, blank=True)
    new_value   = CharField(max_length=200, blank=True)
    note        = CharField(max_length=200, blank=True)

    class Meta:
        indexes = [Index(fields=['roll', '-created_at'])]
        ordering = ['-created_at']


class AddaHistory(TimeStampedModel):
    class ChangeType(TextChoices):
        CREATED        = 'created',         'Created'
        STAGE_ADVANCED = 'stage_advanced',  'Stage Advanced'
        STATUS_CHANGED = 'status_changed',  'Status Changed'
        ROLL_ASSIGNED  = 'roll_assigned',   'Roll Assigned'
        COMPLETED      = 'completed',       'Completed'

    adda        = FK('production.Adda', on_delete=PROTECT, related_name='history')
    change_type = CharField(max_length=32, choices=ChangeType.choices)
    actor       = FK(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name='+')
    stage_from  = FK('production.WorkflowStage', on_delete=PROTECT, null=True, blank=True, related_name='+')
    stage_to    = FK('production.WorkflowStage', on_delete=PROTECT, null=True, blank=True, related_name='+')
    roll        = FK('raw_materials.ClothRoll', on_delete=PROTECT, null=True, blank=True, related_name='+')
    note        = CharField(max_length=200, blank=True)

    class Meta:
        indexes = [Index(fields=['adda', '-created_at'])]
        ordering = ['-created_at']


class ProductHistory(TimeStampedModel):
    class ChangeType(TextChoices):
        CREATED  = 'created',  'Created'
        UPDATED  = 'updated',  'Updated'
        ARCHIVED = 'archived', 'Archived'

    product     = FK('production.Product', on_delete=PROTECT, related_name='history')
    change_type = CharField(max_length=32, choices=ChangeType.choices)
    actor       = FK(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name='+')
    field_name  = CharField(max_length=64, blank=True)
    old_value   = CharField(max_length=200, blank=True)
    new_value   = CharField(max_length=200, blank=True)

    class Meta:
        indexes = [Index(fields=['product', '-created_at'])]
        ordering = ['-created_at']
```

## Barcode generation (atomic, idempotent)

```python
# tracking/services/barcode_service.py

@transaction.atomic
def generate_for_cutting(cutting_record):
    adda  = cutting_record.stage_record.adda
    count = cutting_record.pieces_cut
    if BatchBarcode.objects.filter(adda=adda).exists():
        raise IntegrityError("barcodes already generated for this Adda")  # one-shot
    BatchBarcode.objects.bulk_create([
        BatchBarcode(adda=adda, piece_seq=i, value=f"{adda.code}-{i:04d}")
        for i in range(1, count + 1)
    ])
```

500-row bulk_create = single Postgres INSERT, sub-second.

## QR rendering

Each barcode prints as a **QR code encoding a full URL**. Phone camera scans → opens detail page natively. No app required.

```python
# tracking/services/barcode_service.py
import qrcode, io, base64
from django.urls import reverse

def qr_data_uri(barcode, base_url):
    payload = base_url.rstrip('/') + reverse('tracking:scan', args=[barcode.value])
    img = qrcode.make(payload)
    buf = io.BytesIO(); img.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
```

Print template uses `<img src="{{ bc|qr_uri }}">` in a grid. QR images regenerated on-demand — never stored as binary in DB.

Sticker layout:
```
┌─────────────────┐
│ ███████  ██ ███ │   QR (full URL payload)
│ █ █ █    █  ███ │
│ ███████  ██ █ █ │
│ T-SHIRT-001-0042│   text fallback
└─────────────────┘
```

Requirements addition: `qrcode[pil]==7.4.2`.

## Scan endpoint

```python
# tracking/views/scan.py
@login_required
def scan_piece(request, value):
    bc = get_object_or_404(BatchBarcode, value=value)
    bc.last_scanned_at = timezone.now()
    bc.last_scanned_by = request.user
    bc.save(update_fields=['last_scanned_at', 'last_scanned_by'])
    return render(request, 'tracking/scan_detail.html', {'barcode': bc})
```

Auth: session-based today (factory-internal). Future: mobile app token.

## History service — single writer rule

`ClothRollHistory`, `AddaHistory`, `ProductHistory` are written **only** from `tracking.services.history_service.log_*`. No signals. No views. No model `save()` overrides. Linted via code review.

```python
# tracking/services/history_service.py
def log_roll(roll, change_type, actor, **kwargs):
    return ClothRollHistory.objects.create(roll=roll, change_type=change_type, actor=actor, **kwargs)

def log_adda(adda, change_type, actor, **kwargs):
    return AddaHistory.objects.create(adda=adda, change_type=change_type, actor=actor, **kwargs)

def log_product(product, change_type, actor, **kwargs):
    return ProductHistory.objects.create(product=product, change_type=change_type, actor=actor, **kwargs)
```

This is the new app's analog to `StockService.log` referenced in CLAUDE.md rule #5.

## URLs

```
/tracking/barcodes/<str:adda_code>/         list barcodes for Adda
/tracking/barcodes/<str:adda_code>/print/   bulk print sheet (QR grid, @media print)
/tracking/scan/<str:value>/                 scan handler (called by QR URL)
/tracking/history/roll/<int:roll_pk>/       cloth roll history timeline
/tracking/history/adda/<str:adda_code>/     Adda history timeline
```

## Templates

```
tracking/templates/tracking/
├── barcode_list.html              # piece-level status, filter by Adda
├── barcode_print_sheet.html       # @media print rules, QR grid 4×6 per A4 page
├── scan_detail.html               # piece info after phone scan
└── history/_timeline.html         # included from roll_detail + adda_detail
```
