# accounts/admin.py (updated)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Skill

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)

@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ('email', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)  # Changed from 'username' to 'email'

    fieldsets = (
        ('Personal Info', {
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'birth_date', 'bio', 'profile_picture')
        }),
        ('Permissions', {
            'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'skills')
        }),
        ('Financial Info', {
            'fields': ('salary',)
        }),
        ('Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )
    filter_horizontal = ('skills',)  # For multiple selection of skills
    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at')  # Make these fields readonly