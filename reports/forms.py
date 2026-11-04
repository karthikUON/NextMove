from django import forms

from .models import MAX_DETAILS_LENGTH, Report

# separate form for adding the form details
class ReportForm(forms.ModelForm):
    details = forms.CharField(
        required=False,
        max_length=MAX_DETAILS_LENGTH,
        strip=True,
        label="More details (optional)",
        widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
    )

    class Meta:
        model = Report
        fields = ["reason", "details"]
        labels = {"reason": "What's the problem?"}
        widgets = {"reason": forms.Select(attrs={"class": "form-select"})}