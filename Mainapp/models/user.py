from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid
from django.utils import timezone
from datetime import timedelta

from django.utils.timezone import now


class UserManager(BaseUserManager):
    def create_user(self, email_id, phone_no, password=None, **extra_fields):
        if not email_id:
            raise ValueError("The Email field must be set")

        email_id = self.normalize_email(email_id)

        # Extract and remove user_type from extra_fields to avoid passing it twice
        user_type = extra_fields.pop("user_type", User.UserTypeChoices.REPORTING)

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        if user_type == User.UserTypeChoices.ADMIN:
            extra_fields["is_staff"] = True
            extra_fields["is_superuser"] = True


        first_name = extra_fields.pop("first_name", "")
        last_name = extra_fields.pop("last_name", "")

        user = self.model(
            email_id=email_id,
            phone_no=phone_no,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type,  # Pass user_type separately to avoid duplication
            sub_user_type=extra_fields.get("sub_user_type", ""),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email_id, phone_no, password=None, **extra_fields):
        """Create a superuser with all required fields"""
        extra_fields.setdefault("user_type", User.UserTypeChoices.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not email_id:
            raise ValueError("Superusers must have an email address")
        if not phone_no:
            raise ValueError("Superusers must have a phone number")

        return self.create_user(email_id, phone_no, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class UserTypeChoices(models.TextChoices):
        REPORTING = "reporting", "Reporting"
        VOLUNTEER = "volunteer", "Volunteer"
        FAMILY = "family", "Family"
        ADMIN = "admin", "Admin"
        POLICE_STATION = "police_station", "Police Station"
        MEDICAL_STAFF = "medical_staff", "Medical Staff"

    class FamilySubTypeChoices(models.TextChoices):
        FATHER = "father", "Father"
        MOTHER = "mother", "Mother"
        SON = "son", "Son"
        DAUGHTER = "daughter", "Daughter"
        BROTHER = "brother", "Brother"
        SISTER = "sister", "Sister"
        RELATIVE = "relative", "Relative"

    class StatusChoices(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        HOLD = "hold", "Hold"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=20, choices=UserTypeChoices.choices, default=UserTypeChoices.REPORTING)
    sub_user_type = models.CharField(max_length=20, blank=True, default="")

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email_id = models.EmailField(max_length=50, unique=True)
    phone_no = models.CharField(max_length=10, unique=True)
    country_code = models.CharField(max_length=5, blank=True, null=True)

    password = models.CharField(max_length=255)
    password2 = models.CharField(max_length=255, blank=True, null=True)
    salt = models.CharField(max_length=7, blank=True, null=True)

    is_consent = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=StatusChoices.choices, default=StatusChoices.PENDING)  # Default Pending

    person = models.ForeignKey("Person", on_delete=models.SET_NULL, null=True, blank=True)
    contact = models.ForeignKey("Contact", on_delete=models.SET_NULL, related_name="user_contact", null=True, blank=True)
    consent_id = models.ForeignKey("Consent", on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    updated_by = models.UUIDField(null=True, blank=True)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email_id"
    REQUIRED_FIELDS = ["phone_no", "first_name", "last_name"]
    reset_token = models.CharField(max_length=255, blank=True, null=True)
    reset_token_created_at = models.DateTimeField(blank=True, null=True)

    def is_reset_token_valid(self):
        """Check if the reset token is valid (e.g., expires after 1 hour)."""
        if self.reset_token_created_at:
            return (now() - self.reset_token_created_at).total_seconds() < 3600  # 1 hour
        return False

    def save(self, *args, **kwargs):
        # Ensure only admin users can be staff or superusers
        if self.user_type != self.UserTypeChoices.ADMIN:
            self.is_staff = False
            self.is_superuser = False

        print(
            f"Saving User: {self.email_id}, {self.first_name}, {self.last_name}, {self.user_type}, {self.sub_user_type}"
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email_id} ({self.user_type} - {self.sub_user_type})" if self.sub_user_type else f"{self.email_id} ({self.user_type})"
