"""Admin registration for raw_materials master data + ClothRoll."""
from django.contrib import admin

from raw_materials.models import ClothColor, ClothRoll, ClothType, StorageLocation


@admin.register(ClothType)
class ClothTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(ClothColor)
class ClothColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')


@admin.register(ClothRoll)
class ClothRollAdmin(admin.ModelAdmin):
    list_display = ('roll_id', 'cloth_type', 'cloth_color', 'storage_location', 'status', 'created_at')
    list_filter = ('status', 'cloth_type', 'cloth_color', 'storage_location')
    search_fields = ('roll_id',)
    readonly_fields = ('roll_id', 'created_at', 'updated_at')
