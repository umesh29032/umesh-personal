"""Admin registration for production app."""
from django.contrib import admin

from production.models import (
    Adda,
    CuttingBundle,
    CuttingBundleItem,
    CuttingPatternSizeAllocation,
    CuttingPatternVerification,
    CuttingPieceBreakup,
    Product,
    ProductSize,
    Stage,
    WorkflowStage,
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'adda_counter', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(WorkflowStage)
class WorkflowStageAdmin(admin.ModelAdmin):
    list_display = ('product', 'order', 'stage')
    list_filter = ('stage', 'product')


@admin.register(Adda)
class AddaAdmin(admin.ModelAdmin):
    list_display = ('code', 'product', 'current_stage', 'status', 'started_at')
    list_filter = ('status', 'product')
    search_fields = ('code',)
    readonly_fields = ('code', 'started_at')


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ('product', 'code', 'label', 'display_order', 'is_active')
    list_filter = ('product', 'is_active')
    search_fields = ('code', 'label', 'product__code')
    ordering = ('product', 'display_order', 'code')


@admin.register(CuttingPatternVerification)
class CuttingPatternVerificationAdmin(admin.ModelAdmin):
    list_display = ('record', 'assignment', 'verified_by', 'verified_at')
    search_fields = ('record__stage_record__adda__code',)
    readonly_fields = ('verified_at', 'created_at', 'updated_at')


@admin.register(CuttingPatternSizeAllocation)
class CuttingPatternSizeAllocationAdmin(admin.ModelAdmin):
    list_display = ('record', 'size', 'proportion_pct')
    search_fields = ('record__stage_record__adda__code', 'size__code')


@admin.register(CuttingPieceBreakup)
class CuttingPieceBreakupAdmin(admin.ModelAdmin):
    list_display = ('cutting_record', 'pattern', 'size', 'color', 'count', 'roll')
    list_filter = ('pattern', 'size', 'color')
    search_fields = ('cutting_record__stage_record__adda__code',)


@admin.register(CuttingBundle)
class CuttingBundleAdmin(admin.ModelAdmin):
    list_display = (
        'cutting_record', 'size', 'total_pieces', 'bundle_number',
    )
    list_filter = ('size',)
    search_fields = (
        'cutting_record__stage_record__adda__code',
        'bundle_number',
    )


@admin.register(CuttingBundleItem)
class CuttingBundleItemAdmin(admin.ModelAdmin):
    list_display = ('bundle', 'pattern', 'color', 'count')
    list_filter = ('pattern', 'color')
    search_fields = ('bundle__cutting_record__stage_record__adda__code',)
