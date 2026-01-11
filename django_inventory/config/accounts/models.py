from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone


class Skill(models.Model):
    SKILL_TYPE_CHOICES = (
        ("cutting_master", "Cutting Master"),
        ("dhage_katne_wala", "Dhage Katne Wala"),
        ("embroidery", "Embroidery"),
        ("tailoring", "Tailoring"),
        ("other", "Other"),
    )
    name = models.CharField(max_length=50, choices=SKILL_TYPE_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()


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
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('karigar', 'Karigar'),
        ('helper', 'Helper'),
    )

    username = None
    email = models.EmailField(unique=True, verbose_name="Email Address")
    
    # Basic fields
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='karigar', verbose_name="User Type")
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

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

