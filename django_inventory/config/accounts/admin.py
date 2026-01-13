from django.contrib import admin
from .models import User, Skill

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    This controls how User appears in Django Admin
    """

    list_display = (
        "email",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    search_fields = ("email",)
    ordering = ("email",)
