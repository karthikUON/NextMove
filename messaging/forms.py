from django import forms

from .models import MAX_MESSAGE_LENGTH


class MessageForm(forms.Form):
    body = forms.CharField(
        max_length=MAX_MESSAGE_LENGTH,
        strip=True,
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": "Write a message..."}),
    )