from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier for authentication
    instead of usernames.
    """

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_approved', True)
        extra_fields.setdefault('role', User.Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        CASE_MANAGER = 'case_manager', 'Case Manager'
        INVESTIGATOR = 'investigator', 'Investigator/Advocate'
        CUSTODIAN = 'custodian', 'Evidence Custodian'
        REVIEWER = 'reviewer', 'Read-only Reviewer'

    username = None  # We use email as username
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.INVESTIGATOR)
    phone = models.CharField(max_length=20, blank=True)
    is_approved = models.BooleanField(default=False)
    otp_secret = models.CharField(max_length=32, blank=True)  # TOTP secret
    otp_enabled = models.BooleanField(default=False)
    dark_mode = models.BooleanField(default=False)

    # Notification preferences
    notify_email = models.BooleanField(default=True)
    notify_sms = models.BooleanField(default=False)
    notify_inapp = models.BooleanField(default=True)

    # Reminder preferences (minutes before)
    hearing_reminder_minutes = models.JSONField(default=list, blank=True)  # e.g. [10080, 1440, 120]
    deadline_reminder_minutes = models.JSONField(default=list, blank=True)  # e.g. [4320, 1440]

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['is_approved']),
        ]

    def __str__(self):
        full_name = self.get_full_name().strip()
        display_name = full_name if full_name else self.email
        return f'{display_name} ({self.get_role_display()})'

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_case_manager(self) -> bool:
        return self.role == self.Role.CASE_MANAGER

    @property
    def is_reviewer(self) -> bool:
        return self.role == self.Role.REVIEWER

    @property
    def is_investigator(self) -> bool:
        return self.role == self.Role.INVESTIGATOR

    @property
    def is_custodian(self) -> bool:
        return self.role == self.Role.CUSTODIAN


class EmailOTPChallenge(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='email_otp_challenge')
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
