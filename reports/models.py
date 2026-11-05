from django.conf import settings
from django.db import models


class Report(models.Model):
    """One student reporting one listing. Staff look at the reports in the admin."""

    # the reasons a student can pick from: (value saved in the database, text shown on the form)
    REASON_CHOICES = [
        ("scam", "Scam or fraud"),
        ("prohibited", "Prohibited or illegal item"),
        ("inappropriate", "Inappropriate or offensive"),
        ("misleading", "Misleading or wrong details"),
        ("spam", "Spam or duplicate"),
        ("other", "Something else"),
    ]

    # where the report is up to: staff start at "open" and move it on in the admin
    STATUS_CHOICES = [
        ("open", "Open"),
        ("reviewed", "Reviewed"),
        ("dismissed", "Dismissed"),
    ]

    # the listing being reported (if the listing is deleted, its reports go too)
    listing = models.ForeignKey("marketplace.Listing", on_delete=models.CASCADE, related_name="reports")

    # who reported it (SET_NULL: if that student deletes their account, the report stays)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="reports_made"
    )

    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    details = models.CharField(max_length=1000, blank=True)  # optional extra text, up to 1000 characters
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]  # newest reports first

    def __str__(self):
        return f"Report {self.pk}: {self.get_reason_display()} on listing {self.listing_id}"