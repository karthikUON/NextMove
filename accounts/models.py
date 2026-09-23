from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

UON_DOMAINS = ("uon.edu.au", "newcastle.edu.au")
def validate_uon_email(value):
    domain = value.split("@")[-1].lower()
    if domain not in UON_DOMAINS:
        raise ValidationError("Please use your UoN email address (@uon.edu.au or @newcastle.edu.au).")


class User(AbstractUser):
    email = models.EmailField(unique=True, validators=[validate_uon_email])
    is_verified = models.BooleanField(default=False)
    # added otp attributes by karthik
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    otp_attempts = models.PositiveSmallIntegerField(default=0)
    otp_locked_until = models.DateTimeField(blank=True, null=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email