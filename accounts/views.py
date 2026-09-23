from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import SignupForm, OTPForm
from .models import User
from .utils import send_otp_email, check_otp, is_locked, lockout_message

# signup method, get the form details, send the otp and verify
def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_otp_email(user)
            request.session["pending_verification_email"] = user.email
            return redirect("verify_email")
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})


# get the email, if clocked and pass the otp form
def verify_email_view(request):
    email = request.GET.get("email") or request.session.get("pending_verification_email")
    user = get_object_or_404(User, email=email) if email else None
    locked = is_locked(user) if user else False
    error = lockout_message(user) if (user and locked) else None
    otp_form = OTPForm()

    if request.method == "POST" and user and not locked:
        otp_form = OTPForm(request.POST)
        if otp_form.is_valid():
            result = check_otp(user, otp_form.cleaned_data["otp_code"])
            if result["ok"]:
                request.session.pop("pending_verification_email", None)
                messages.success(request, "Email verified! You can now log in.")
                return redirect("login")
            error = result["error"]
            locked = result["locked"]

    return render(request, "accounts/verify_email.html", {"email": email, "form": otp_form, "error": error, "locked": locked})

# this method helps to resend_otp_view and make the changes
def resend_otp_view(request):
    if request.method == "POST":
        email = request.POST.get("email") or request.session.get("pending_verification_email")
        user = get_object_or_404(User, email=email)
        if not is_locked(user):
            send_otp_email(user)
            messages.info(request, "A new verification code has been sent.")
        request.session["pending_verification_email"] = user.email
    return redirect("verify_email")

# login view check if email/pass and and auth_login from django
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user is None or not user.check_password(password):
            messages.error(request, "Incorrect email or password.")
        elif not user.is_active:
            messages.error(request, "This account has been disabled by an admin.")
        elif not user.is_verified:
            messages.error(request, "Please verify your email before logging in.")
        else:
            auth_login(request, user)
            return redirect("login")  # TEMP: change to "home" once Week 5's homepage URL exists
    return render(request, "accounts/login.html")

# logout view for now it is login but needs to be home
def logout_view(request):
    auth_logout(request)
    return redirect("home")


@login_required
def profile_view(request):
    return render(request, "accounts/profile.html")