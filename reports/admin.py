from django.contrib import admin

from marketplace.admin import ListingAdmin
from marketplace.models import Listing

from .models import Report


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
    Listing.objects.filter(pk__in=ids).update(status="removed")
    # the open reports about these listings are dealt with now
    Report.objects.filter(listing_id__in=ids, status="open").update(status="reviewed")
    modeladmin.message_user(request, f"{len(ids)} listing(s) rejected and removed from the site.")


@admin.action(description="Put selected listings on hold for review")
def hold_listings(modeladmin, request, queryset):
    ids = list(queryset.filter(status="active").values_list("pk", flat=True))  # only active ones can be held
    Listing.objects.filter(pk__in=ids).update(status="on_hold")
    modeladmin.message_user(request, f"{len(ids)} active listing(s) put on hold for review.")


# add our two actions to the existing Listing admin
ListingAdmin.actions = list(ListingAdmin.actions or []) + [reject_listings, hold_listings]


# ---------------------------------------------------------------------------
# The Reports page in the admin.
# ---------------------------------------------------------------------------

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("listing", "reason", "reporter", "status", "created_at")  # the columns in the list
    list_filter = ("status", "reason")                                         # the filter box on the right
    # staff can read what the student wrote but not change it (they only change the status)
    readonly_fields = ("listing", "reporter", "reason", "details", "created_at")
    actions = ["mark_reviewed", "dismiss_reports"]

    def has_add_permission(self, request):
        return False  # reports only come from students, staff don't create them

    @admin.action(description="Mark selected reports as reviewed")
    def mark_reviewed(self, request, queryset):
        count = queryset.filter(status="open").update(status="reviewed")
        self.message_user(request, f"{count} report(s) marked as reviewed.")

    @admin.action(description="Dismiss selected reports (no action needed)")
    def dismiss_reports(self, request, queryset):
        count = queryset.exclude(status="dismissed").update(status="dismissed")
        self.message_user(request, f"{count} report(s) dismissed.")