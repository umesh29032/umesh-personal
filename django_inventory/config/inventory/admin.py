from django.contrib import admin
from .models import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_system')
    search_fields = ('name', 'code')
    list_filter = ('is_system',)
