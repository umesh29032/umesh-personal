"""
Custom user model + skills + user types.

Identity concepts (NEVER gate access on user_type — Role does that):
  UserType  — "who the user is" display label; admin-managed from UI, no code changes needed.
  Skill     — "what production work the user can do"; admin-managed from UI.
  role      — FK to inventory.Role, RBAC source of truth for module/sidebar access.

Why a custom user? Django's default User uses `username` for login. We want
email-only login, so we subclass `AbstractUser`, drop `username`, and make
`email` the `USERNAME_FIELD`. AUTH_USER_MODEL='accounts.User' in settings
tells Django to use this class everywhere `request.user` appears.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone


class UserType(models.Model):
    """
    Defines what type of user this is — a display/classification concept only.

    WHY: Replaces the hardcoded USER_TYPE_CHOICES CharField so admins can add
    new user types (e.g. "Supplier", "Franchise Owner") from the UI without code
    changes. Does NOT gate access — Role does that.

    Examples: Super Admin, Admin, Worker, Supplier, Normal User.
    """
    # Stable code key used in permission_service legacy fallback mapping.
    # SlugField = URL-safe, lowercase, no spaces — same pattern as Role.code.
    code = models.SlugField(
        max_length=32, unique=True,
        help_text="Stable identifier (e.g. 'worker'). Never change after seeding.",
    )
    label = models.CharField(
        max_length=64,
        help_text="Display name shown in UI (e.g. 'Worker').",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['label']
        verbose_name = 'User Type'
        verbose_name_plural = 'User Types'

    def __str__(self):
        return self.label


class Skill(models.Model):
    """
    Defines what production work a user can perform.

    WHY: Replaces hardcoded SKILL_TYPE_CHOICES so admins can add new skills
    (e.g. 'stitching_master', 'finishing_helper') from the UI without code
    changes. Skill does NOT grant module access — Role does that.

    `name` = stable code key (slug, mirrors constants in accounts/skills.py).
    `label` = human-readable display name.
    `get_name_display()` kept as back-compat shim for all existing call-sites.
    """
    name = models.SlugField(
        max_length=64, unique=True,
        help_text="Stable code key (e.g. 'cutting_master'). Must match skills.py constant if used in services.",
    )
    label = models.CharField(
        max_length=100,
        help_text="Human-readable display name (e.g. 'Cutting Master').",
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['label']

    def __str__(self):
        return self.label or self.name

    def get_name_display(self):
        """Back-compat shim — replaces Django's auto choices display method."""
        return self.label or self.name


class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model:
    - No username
    - Email is unique and used for login
    """

    username = None
    email = models.EmailField(unique=True, verbose_name="Email Address")

    # Classification label ONLY — never gates access (Role does that).
    # FK to UserType so admins can add new types from UI without code changes.
    user_type = models.ForeignKey(
        UserType,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='users',
        verbose_name="User Type",
        help_text="What type of user this is (display/classification only). Role controls access.",
    )
    first_name = models.CharField(max_length=30, blank=True, verbose_name="First Name")
    last_name = models.CharField(max_length=30, blank=True, verbose_name="Last Name")

    # Status fields
    is_active = models.BooleanField(default=True, verbose_name="Active Status")
    is_staff = models.BooleanField(default=False, verbose_name="Staff Status")
    is_superuser = models.BooleanField(default=False, verbose_name="Superuser Status")

    # Date fields
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Date Joined")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    # Contact and personal info
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex], 
        max_length=15, 
        blank=True, 
        null=True, 
        verbose_name="Phone Number"
    )
    birth_date = models.DateField(blank=True, null=True, verbose_name="Birth Date")
    bio = models.TextField(blank=True, verbose_name="Biography")

    # Profile and work info
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        blank=True, 
        null=True, 
        verbose_name="Profile Picture"
    )
    salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        validators=[MinValueValidator(0)],
        verbose_name="Salary"
    )
    skills = models.ManyToManyField(
        Skill,
        related_name='users',
        blank=True,
        verbose_name="Skills"
    )
    role = models.ForeignKey(
        'accounts.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name="Role",
        help_text="Primary RBAC role — determines main permissions and sidebar.",
    )
    # Extra roles allow granting additional access on top of the primary role.
    # Example: a Manager who also needs listing_team access to manage storefront.
    # permission_service.user_has_role() checks both role and extra_roles.
    extra_roles = models.ManyToManyField(
        'accounts.Role',
        blank=True,
        related_name='extra_users',
        verbose_name="Extra Roles",
        help_text="Additional access grants. Stack on top of the primary role.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta(AbstractUser.Meta):
        # Inherit AbstractUser's verbose_name; add a salary DB guard (mirrors the
        # MinValueValidator above) + an index for the RBAC "active users with
        # role X" lookup that permission_service runs constantly.
        constraints = [
            models.CheckConstraint(
                check=models.Q(salary__gte=0),
                name='accounts_user_salary_nonneg',
            ),
        ]
        indexes = [
            models.Index(fields=['is_active', 'role']),
        ]

    def __str__(self):
        return self.email


# ── RBAC core ────────────────────────────────────────────────────────────────
# Role + SidebarItemRule live HERE (accounts), with User/Skill — identity + access
# control are one foundation the whole app depends on, and that depends on nothing
# domain-specific. (Relocated from the `inventory` app — `inventory.services` is a
# re-export shim so existing imports keep working.)

class Role(models.Model):
    """Named bundle of Django permissions. A User.role points to one Role.
    Superuser bypasses all checks; everyone else is gated by their role's permissions.
    Seeded defaults: Super Admin, Manager, Worker (see migration data).
    """
    name = models.CharField(max_length=64, unique=True)
    code = models.SlugField(max_length=32, unique=True)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(
        default=False,
        help_text="System roles (admin/manager/worker) cannot be deleted.",
    )
    permissions = models.ManyToManyField(
        'auth.Permission', blank=True, related_name='inventory_roles',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SidebarItemRule(models.Model):
    """Per-menu-item role visibility, driven by the Sidebar Access Control page.

    `url_name` is the stable identifier (Django URL name) for each sidebar entry —
    matches MenuItem.url_name in permission_service.SIDEBAR. Section + label are
    denormalized for display in the admin page so the table is self-contained.

    Super Admin is hardcoded-always-visible at the service layer — never gated
    here so an admin cannot accidentally lock themselves out.
    """

    url_name = models.CharField(
        max_length=128, unique=True,
        help_text="Django URL name, e.g. 'raw_materials:roll-list'.",
    )
    section = models.CharField(max_length=64, help_text="Display section header.")
    label = models.CharField(max_length=64, help_text="Display label in the sidebar.")
    allowed_roles = models.ManyToManyField(
        Role, blank=True, related_name='visible_sidebar_items',
        help_text="Roles allowed to see this menu item.",
    )
    allowed_skills = models.ManyToManyField(
        'accounts.Skill', blank=True, related_name='visible_sidebar_items',
        help_text="Users with ANY of these skills also see this menu item.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['section', 'label']

    def __str__(self):
        return f"{self.section} · {self.label}"

