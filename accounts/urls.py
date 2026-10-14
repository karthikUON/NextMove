from django.urls import path
from . import views


# the urls which needs for accounts application
urlpatterns = [
    # Karthik and chinna sat on this and included which are required for accounts.
    path("signup/", views.signup_view, name="signup"),
    path("verify-email/", views.verify_email_view, name="verify_email"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("resend-otp/", views.resend_otp_view, name="resend_otp"),
    # karthik added the forgot password, as Jay raised an issue at the testing that forgot password is missing
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("reset-code/", views.reset_verify_view, name="reset_verify"),
    path("reset-password/", views.reset_password_view, name="reset_password"),
]