"""
Django Admin registrations for User and Skill.

The Django Admin at /admin/ is a backup management interface — the main user
management UI lives at /app/users/ (accounts views, Super Admin only).
"""
from django.contrib import admin
from .models import User, Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # Show enough columns to spot the right user at a glance without loading the row.
    list_display = (
        "email",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    search_fields = ("email",)
    ordering = ("email",)
