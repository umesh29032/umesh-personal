from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator, MinValueValidator
# from django.contrib.postgres.fields import ArrayField


class UserManager(BaseUserManager):
    """
    Custom user manager for the User model.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        """
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')
        return self.create_user(email, password, **extra_fields)

class Skill(models.Model):
    """
    Model to represent skills that users can have.
    """
    SKILL_TYPE_CHOICES = (
        ("cutting_master", "Cutting Master"),
        ("dhage_katne_wala", "Dhage Katne Wala"),
        ("embroidery", "Embroidery"),
        ("tailoring", "Tailoring"),
        ("other", "Other"),
    )
    name = models.CharField(max_length=20, choices=SKILL_TYPE_CHOICES, unique=True)
    description = models.TextField(blank=True, help_text="Detailed description of the skill")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'

    def __str__(self):
        return self.name

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that uses email as the unique identifier instead of username.
    """
    USER_TYPE_CHOICES = (
        ("admin", "Admin"),
        ("supplier", "Supplier"),
        ("karigar", "Karigar"),
        ("kapde_wala", "Kapde Wala"),
    )

    # Basic fields
    email = models.EmailField(unique=True, verbose_name="Email Address")
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='karigar', verbose_name="User Type")
    first_name = models.CharField(max_length=30, blank=True, verbose_name="First Name")
    last_name = models.CharField(max_length=30, blank=True, verbose_name="Last Name")
    
    # Status fields
    is_active = models.BooleanField(default=True, verbose_name="Active Status")
    is_staff = models.BooleanField(default=False, verbose_name="Staff Status")
    is_superuser = models.BooleanField(default=False, verbose_name="Superuser Status")
    
    # Date fields
    last_login = models.DateTimeField(null=True, blank=True, verbose_name="Last Login")
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
    
    # Manager
    objects = UserManager()

    # Required fields for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """
        Ensure admin users have staff status.
        """
        if self.user_type == 'admin':
            self.is_staff = True
        super().save(*args, **kwargs)

    @property
    def is_authenticated(self):
        """
        Always return True for authenticated User instances.
        """
        return True

    @property
    def is_anonymous(self):
        """
        Always return False for authenticated User instances.
        """
        return False
    
    @property
    def full_name(self):
        """
        Return the user's full name.
        """
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.email

    def __str__(self):
        return self.email