"""Layer 2 — cast (writer-map row: accounts users via the User manager's
create_user — the same hashing path production uses; role FK = accounts.Role,
migration-seeded baseline consumed, never created)."""

from django.apps import apps

from devseed.layers import DivergenceError

CAST_PASSWORD = "Dev@12345"  # the owner's DEV cast credential (Test-Data rule 2026-07-04)


def seed_cast(cast_spec):
    User = apps.get_model("accounts", "User")
    Role = apps.get_model("accounts", "Role")
    created = skipped = 0
    actors = {}
    for row in cast_spec:
        handle, role_code = row["handle"], row["role"]
        role = Role.objects.get(code=role_code)  # baseline row — must pre-exist
        user = User.objects.filter(email=handle).first()
        if user is None:
            user = User.objects.create_user(
                handle, CAST_PASSWORD, role=role,
                first_name=row.get("first_name", ""), last_name=row.get("last_name", ""),
                is_active=row.get("active", True),
            )
            # PHASE_03 D1 composite identities: extra_roles M2M union.
            if row.get("extra_roles"):
                Role_ = apps.get_model("accounts", "Role")
                user.extra_roles.set(Role_.objects.filter(code__in=row["extra_roles"]))
            # skills: "*" = every Skill row (stage access is skill-gated —
            # access_service.user_can_access_stage reads Stage.access_by_skill).
            if row.get("skills") == "*":
                Skill = apps.get_model("accounts", "Skill")
                user.skills.set(Skill.objects.all())
            created += 1
        else:
            if user.role_id != role.pk:
                raise DivergenceError(
                    f"cast {handle}: existing role "
                    f"'{user.role.code if user.role else None}' != scenario role '{role_code}'"
                )
            skipped += 1
        actors[handle] = user
    return {"created": created, "skipped": skipped, "actors": actors}
