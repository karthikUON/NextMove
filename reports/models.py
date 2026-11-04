from django.conf import settings
from django.db import models

MAX_DETAILS_LENGTH = 1000

# Added there to create the report model
class Report(models.Model):
    """A student telling us that a listing is a problem. Staff review it in the admin."""
    # listing reason choices  
    REASON_CHOICES = [
        ("scam", "Scam or fraud"),
        ("prohibited", "Prohibited or illegal item"),
        ("inappropriate", "Inappropriate or offensive content"),
        ("misleading", "Misleading or wrong details"),
        ("spam", "Spam or duplicate listing"),
        ("other", "Something else"),
    ]
    # status choices 
    STATUS_CHOICES = [
        ("open", "Open"),
        ("reviewed", "Reviewed"),
        ("actioned", "Actioned (listing removed)"),
        ("dismissed", "Dismissed"),
    ]
    # get the foreign key 
    listing = models.ForeignKey("marketplace.Listing", on_delete=models.CASCADE, related_name="reports")
    # SET_NULL: if the reporter deletes their account, the report (the evidence) stays
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="reports_made"
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reports_reviewed"
    )
    # order by created_dat
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["listing", "status"]),
        ]

    def __str__(self):
        return f"Report {self.pk}: {self.get_reason_display()} on listing {self.listing_id}"