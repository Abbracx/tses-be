import random
import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumber, PhoneNumberField

from .managers import CustomUserManager


class Gender(models.TextChoices):
    MALE = 'Male', _("Male")
    FEMALE = 'Female', _("Female")
    OTHER = 'Other', _("Other")


class User(AbstractBaseUser, PermissionsMixin):
    pkid = models.BigAutoField(primary_key=True, editable=False)
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    username = models.CharField(verbose_name=_("Username"), max_length=255, unique=True, db_index=True)
    first_name = models.CharField(verbose_name=_("First Name"), max_length=50, db_index=True)
    last_name = models.CharField(verbose_name=_("Last Name"), max_length=50, db_index=True)
    email = models.EmailField(verbose_name=_("Email Address"), unique=True, db_index=True)
    gender = models.CharField(verbose_name=_("Gender"), choices=Gender.choices, default=Gender.OTHER, max_length=20)
    phone_number = PhoneNumberField(verbose_name=_("Phone Number"), max_length=30, default="+234123456789")
    profile_photo = models.ImageField(verbose_name=_("Profile photo"), default='/profile_default.png')
    country = CountryField(verbose_name=_("Country"), default="NG", blank=False, null=False)
    city = models.CharField(verbose_name=_("City"), max_length=180, default="Abuja", blank=False, null=False)
    is_staff = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    date_joined = models.DateTimeField(default=timezone.now, db_index=True)
    failed_login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False, db_index=True)
    
    # OTP fields
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    max_otp_try = models.IntegerField(default=3)
    otp_try_count = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False, db_index=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['username', 'is_active']),
            models.Index(fields=['is_staff', 'is_active']),
            models.Index(fields=['date_joined', 'is_active']),
            models.Index(fields=['is_locked', 'failed_login_attempts']),
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['is_verified', 'is_active']),
            models.Index(fields=['otp_expiry']),
        ]

    def __str__(self):
        return self.username

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.username

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.otp_expiry = timezone.now() + timezone.timedelta(minutes=5)
        self.otp_try_count = 0
        self.save(update_fields=['otp', 'otp_expiry', 'otp_try_count'])
        return self.otp

    def verify_otp(self, otp):
        if not self.otp or not self.otp_expiry:
            return False
        
        if timezone.now() > self.otp_expiry:
            return False
        
        if self.otp_try_count >= self.max_otp_try:
            return False
        
        if self.otp == otp:
            self.is_verified = True
            self.otp = None
            self.otp_expiry = None
            self.otp_try_count = 0
            self.save(update_fields=['is_verified', 'otp', 'otp_expiry', 'otp_try_count'])
            return True
        else:
            self.otp_try_count += 1
            self.save(update_fields=['otp_try_count'])
            return False
