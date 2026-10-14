import secrets
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

# for we decided to keep  the max attempts were only 3
OTP_MAX_ATTEMPTS = 3
# otp locksout if more than 1 hour.
OTP_LOCKOUT_MINUTES = 60
# otp expiry is 15 mins
OTP_EXPIRY_MINUTES = 15
# resend can be only sent after 1 hr
OTP_RESEND_COOLDOWN_SECONDS = 60

# this helps to generat the code
def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


# pass the user obj and get the otp and 
def send_otp_email(user, purpose="verify") -> str:
    # generate the otp
    otp = generate_otp()
    user.otp_code = otp
    user.otp_created_at = timezone.now()
    user.otp_attempts = 0
    user.otp_locked_until = None
    user.save(update_fields=["otp_code", "otp_created_at", "otp_attempts", "otp_locked_until"])

    # check the purspose if it is reset, like forgot password
    if purpose == "reset":
        subject = "Your NextMove password reset code"
        action = "Enter this code on the password reset page."
    # else the otp is regarding activations
    else:    
        subject = "Your NextMove verification code"
        action = "Enter this on the verification page to activate your account."

    send_mail(
        subject=subject,
        message=(
            f"Your NextMove code is: {otp}\n\n{action}\n"
            f"It expires in {OTP_EXPIRY_MINUTES} minutes, and you have {OTP_MAX_ATTEMPTS} attempts "
            f"before a temporary lockout.\n\nIf you didn't request this, you can ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return otp

def is_locked(user) -> bool:
    return bool(user.otp_locked_until and user.otp_locked_until > timezone.now())


# False while locked out, or if a code was sent less than a minute ago.
def can_send_otp(user) -> bool:
    if is_locked(user):
        return False
    if user.otp_created_at and (timezone.now() - user.otp_created_at).total_seconds() < OTP_RESEND_COOLDOWN_SECONDS:
        return False
    return True


# theis method helps for lockout message
def lockout_message(user) -> str:
    minutes_left = int((user.otp_locked_until - timezone.now()).total_seconds() // 60) + 1
    return f"Too many incorrect attempts. Try again in {minutes_left} minute(s)."

# verify the otp and check submitted_code
def check_otp(user, submitted_code: str) -> dict:
    if is_locked(user):
        return {"ok": False, "locked": True, "error": lockout_message(user), "attempts_left": 0}

    if user.otp_created_at and timezone.now() - user.otp_created_at > timedelta(minutes=OTP_EXPIRY_MINUTES):
        return {"ok": False, "locked": False, "error": "This code has expired. Please request a new one.", "attempts_left": None}
    # check if the submitted otp is same
    if submitted_code == user.otp_code:
        user.is_verified = True
        user.otp_code = None
        user.otp_attempts = 0
        user.otp_locked_until = None
        user.save(update_fields=["is_verified", "otp_code", "otp_attempts", "otp_locked_until"])
        return {"ok": True, "locked": False, "error": None, "attempts_left": None}

    user.otp_attempts += 1
    if user.otp_attempts >= OTP_MAX_ATTEMPTS:
        user.otp_locked_until = timezone.now() + timedelta(minutes=OTP_LOCKOUT_MINUTES)
        user.save(update_fields=["otp_attempts", "otp_locked_until"])
        return {"ok": False, "locked": True, "error": "Too many incorrect attempts. Try again in 1 hour.", "attempts_left": 0}

    user.save(update_fields=["otp_attempts"])
    remaining = OTP_MAX_ATTEMPTS - user.otp_attempts
    return {"ok": False, "locked": False, "error": f"Incorrect code. {remaining} attempt(s) remaining.", "attempts_left": remaining}