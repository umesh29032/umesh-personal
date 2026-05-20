"""Admin registration for production app."""
from django.contrib import admin

from production.models import Adda, Product, WorkflowStage


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'adda_counter', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(WorkflowStage)
class WorkflowStageAdmin(admin.ModelAdmin):
    list_display = ('product', 'order', 'stage_type')
    list_filter = ('stage_type', 'product')


@admin.register(Adda)
class AddaAdmin(admin.ModelAdmin):
    list_display = ('code', 'product', 'current_stage', 'status', 'started_at')
    list_filter = ('status', 'product')
    search_fields = ('code',)
    readonly_fields = ('code', 'started_at')
