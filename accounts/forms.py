from django import forms
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from .models import User


class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["first_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "you@uon.edu.au"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("password1", "password2"):
            self.fields[field_name].widget.attrs["class"] = "form-control"
        self.fields["first_name"].label = "Full name"
        self.fields["email"].label = "UoN email"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"].split("@")[0]
        user.is_verified = False
        if commit:
            user.save()
        return user


class OTPForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control text-center",
                "placeholder": "6-digit code",
                "autofocus": True,
            }
        ),
        label="Verification code",
    )


class ResetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
