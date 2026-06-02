"""Admin registration for tracking models."""
from django.contrib import admin

from tracking.models import AddaHistory, BarcodeBatch, BatchBarcode, ClothRollHistory, ProductHistory


@admin.register(BarcodeBatch)
class BarcodeBatchAdmin(admin.ModelAdmin):
    list_display = (
        'adda', 'product', 'bundle', 'size', 'color',
        'start_seq', 'end_seq', 'total_pieces',
    )
    list_filter = ('product', 'size', 'color')
    search_fields = ('adda__code',)
    readonly_fields = ('start_seq', 'end_seq', 'total_pieces', 'created_at')


@admin.register(BatchBarcode)
class BatchBarcodeAdmin(admin.ModelAdmin):
    list_display = (
        'value', 'adda', 'piece_seq', 'pattern', 'size', 'color',
        'status', 'last_scanned_at',
    )
    list_filter = ('status', 'pattern', 'size', 'color', 'adda')
    search_fields = ('value',)
    readonly_fields = ('value', 'piece_seq', 'adda', 'created_at')


@admin.register(ClothRollHistory)
class ClothRollHistoryAdmin(admin.ModelAdmin):
    list_display = ('roll', 'change_type', 'actor', 'created_at')
    list_filter = ('change_type',)
    search_fields = ('roll__roll_id',)
    readonly_fields = [f.name for f in ClothRollHistory._meta.fields]


@admin.register(AddaHistory)
class AddaHistoryAdmin(admin.ModelAdmin):
    list_display = ('adda', 'change_type', 'actor', 'created_at')
    list_filter = ('change_type',)
    search_fields = ('adda__code',)
    readonly_fields = [f.name for f in AddaHistory._meta.fields]


@admin.register(ProductHistory)
class ProductHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'change_type', 'actor', 'created_at')
    list_filter = ('change_type',)
    readonly_fields = [f.name for f in ProductHistory._meta.fields]
