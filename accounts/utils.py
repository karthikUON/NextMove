import secrets
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

# for we decided to keep  the max attempts were only 3
OTP_MAX_ATTEMPTS = 3
# otp locksout if more than 1 hour.
OTP_LOCKOUT_MINUTES = 60

# this helps to generat the code
def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


# pass the user obj and get the otp and 
def send_otp_email(user) -> str:
    # generate otp
    otp = generate_otp()
    user.otp_code = otp
    # created time
    user.otp_created_at = timezone.now()
    user.otp_attempts = 0
    user.otp_locked_until = None
    #
    user.save(update_fields=["otp_code", "otp_created_at", "otp_attempts", "otp_locked_until"])
    # send the email
    send_mail(
        subject="Your NextMove verification code",
        message=(
            f"Your NextMove verification code is: {otp}\n\n"
            f"Enter this on the verification page to activate your account. "
            f"You have {OTP_MAX_ATTEMPTS} attempts before a temporary lockout."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return otp


def is_locked(user) -> bool:
    return bool(user.otp_locked_until and user.otp_locked_until > timezone.now())

# theis method helps for lockout message
def lockout_message(user) -> str:
    minutes_left = int((user.otp_locked_until - timezone.now()).total_seconds() // 60) + 1
    return f"Too many incorrect attempts. Try again in {minutes_left} minute(s)."

# verify the otp and check submitted_code
def check_otp(user, submitted_code: str) -> dict:
    if is_locked(user):
        return {"ok": False, "locked": True, "error": lockout_message(user), "attempts_left": 0}

    # check the code if it matches and manage the fields
    if submitted_code == user.otp_code:
        user.is_verified = True
        user.otp_code = None
        user.otp_attempts = 0
        user.otp_locked_until = None
        user.save(update_fields=["is_verified", "otp_code", "otp_attempts", "otp_locked_until"])
        return {"ok": True, "locked": False, "error": None, "attempts_left": None}
    # increase the otp attempt
    user.otp_attempts += 1
    if user.otp_attempts >= OTP_MAX_ATTEMPTS:
        user.otp_locked_until = timezone.now() + timedelta(minutes=OTP_LOCKOUT_MINUTES)
        user.save(update_fields=["otp_attempts", "otp_locked_until"])
        return {"ok": False, "locked": True, "error": "Too many incorrect attempts. Try again in 1 hour.", "attempts_left": 0}
    # save the fields and remaining attempts
    user.save(update_fields=["otp_attempts"])
    remaining = OTP_MAX_ATTEMPTS - user.otp_attempts
    return {"ok": False, "locked": False, "error": f"Incorrect code. {remaining} attempt(s) remaining.", "attempts_left": remaining}