from django.contrib import admin

from marketplace.admin import ListingAdmin
from marketplace.models import Listing

from .models import Report

# reports that still need a decision
UNRESOLVED = ["open", "reviewed"]


def remove_listings(listing_ids):
    """Take these listings off the site and mark every unresolved report about them as "rejected".

    Used by the three places below that reject something, so the rule is the same everywhere.
    Returns how many listings were newly removed.
    """
    newly_removed = (
        Listing.objects.filter(pk__in=listing_ids).exclude(status="removed").count()
    )
    Listing.objects.filter(pk__in=listing_ids).update(status="removed")
    Report.objects.filter(listing_id__in=listing_ids, status__in=UNRESOLVED).update(
        status="rejected"
    )
    return newly_removed


# ---------------------------------------------------------------------------
# Extra bulk actions for the Listing admin.
# The Listing admin already has "Approve" (from the keyword feature). We add two more
# to the same list: tick some listings, pick an action from the dropdown, press Go.
#
# Every action uses .update(), which writes straight to the database. That skips the keyword scan,
# so a decision made by staff is never undone by the automatic check.
# ---------------------------------------------------------------------------


@admin.action(description="Reject selected listings (remove them from the site)")
def reject_listings(modeladmin, request, queryset):
    ids = list(queryset.values_list("pk", flat=True))
    remove_listings(
        ids
    )  # removes them and marks the open reports about them as "rejected"
    modeladmin.message_user(
        request, f"{len(ids)} listing(s) rejected and removed from the site."
    )


@admin.action(description="Put selected listings on hold for review")
def hold_listings(modeladmin, request, queryset):
    ids = list(
        queryset.filter(status="active").values_list("pk", flat=True)
    )  # only active ones can be held
    Listing.objects.filter(pk__in=ids).update(status="on_hold")
    modeladmin.message_user(
        request, f"{len(ids)} active listing(s) put on hold for review."
    )


# add our two actions to the existing Listing admin
ListingAdmin.actions = list(ListingAdmin.actions or []) + [
    reject_listings,
    hold_listings,
]


# Listings are never hard-deleted from the admin. Removing a listing is a SOFT delete (its status becomes
# "removed" and the row stays in the database), so use the "Reject" action above.
# This also takes away the red Delete button and "Delete selected listings" from the Listings admin.
def no_hard_delete(modeladmin, request, obj=None):
    return False


ListingAdmin.has_delete_permission = no_hard_delete

# show the dashboard at the top of the admin home page (the page is reports/templates/reports/admin_index.html)
admin.site.index_template = "reports/admin_index.html"


# ---------------------------------------------------------------------------
# The Reports page in the admin.
# ---------------------------------------------------------------------------


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "listing",
        "reason",
        "reporter",
        "status",
        "created_at",
    )  # the columns in the list
    list_filter = ("status", "reason")  # the filter box on the right
    actions = ["mark_reviewed", "dismiss_reports", "reject_reports"]

    # the Reports list page = Django's normal page with the four dashboard cards added above it
    change_list_template = "reports/report_changelist.html"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Choosing "Rejected (listing removed)" in the Status drop-down removes the listing from the site.
        # (Only when the status was just changed to it, so saving an old report later can't remove
        # a listing that staff have since restored.)
        if "status" in form.changed_data and obj.status == "rejected":
            remove_listings([obj.listing_id])

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()  # adding a report by hand (handy for testing): every field can be filled in
        # an existing report: staff can read what the student wrote but not change it (they only change the status)
        return ("listing", "reporter", "reason", "details", "created_at")

    @admin.action(description="Mark selected reports as reviewed")
    def mark_reviewed(self, request, queryset):
        count = queryset.filter(status="open").update(status="reviewed")
        self.message_user(request, f"{count} report(s) marked as reviewed.")

    @admin.action(description="Dismiss selected reports (no action needed)")
    def dismiss_reports(self, request, queryset):
        count = queryset.exclude(status="dismissed").update(status="dismissed")
        self.message_user(request, f"{count} report(s) dismissed.")

    @admin.action(
        description="Reject selected reports (remove the reported listings from the site)"
    )
    def reject_reports(self, request, queryset):
        listing_ids = set(queryset.values_list("listing_id", flat=True))
        removed = remove_listings(listing_ids)
        queryset.update(
            status="rejected"
        )  # the selected reports themselves, whatever status they had
        self.message_user(
            request,
            f"{removed} listing(s) removed from the site and their reports rejected.",
        )
