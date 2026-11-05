from django import forms

from .models import Report


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "details"]
        widgets = {
            "reason": forms.Select(attrs={"class": "form-select"}),
            "details": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Explain the issue (optional)",
            }),
        }