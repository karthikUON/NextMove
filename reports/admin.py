from django.contrib import admin
from django.contrib.admin.models import CHANGE, LogEntry
from django.db.models import Count, Q
from django.utils import timezone

from marketplace.admin import ListingAdmin
from marketplace.models import Listing

from .models import Report

# reports that still need a decision
UNRESOLVED = ["open", "reviewed"]


def _audit(request, objects, message):
    """Write each decision to the admin history (who did what), so moderation can be checked later."""
    objects = list(objects)
    if objects:
        LogEntry.objects.log_actions(request.user.pk, objects, CHANGE, message)


def _has_field(model, name):
    return any(f.name == name for f in model._meta.get_fields())


class ReportInline(admin.TabularInline):
    """The reports about a listing, shown on the listing's own admin page."""

    model = Report
    fk_name = "listing"
    extra = 0
    can_delete = False
    fields = ("reason", "reporter", "status", "details", "created_at")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


# Extend the existing Listing admin (it already has "Approve") with Reject and Hold actions.
try:
    admin.site.unregister(Listing)
except admin.sites.NotRegistered:
    pass


@admin.register(Listing)
class ListingModerationAdmin(ListingAdmin):
    actions = list(getattr(ListingAdmin, "actions", None) or []) + ["reject_listings", "hold_listings"]
    inlines = list(getattr(ListingAdmin, "inlines", None) or []) + [ReportInline]
    list_display = tuple(ListingAdmin.list_display) + ("open_reports",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _open_reports=Count("reports", filter=Q(reports__status="open"))
        )

    @admin.display(description="Open reports", ordering="_open_reports")
    def open_reports(self, obj):
        return obj._open_reports

    # Every action below uses .update(), not .save(), ON PURPOSE: it skips the keyword scan,
    # so a decision made by staff is never undone by an automatic re-check.

    @admin.action(description="Reject selected listings (remove them from the site)")
    def reject_listings(self, request, queryset):
        affected = list(queryset.exclude(status="removed"))
        ids = [listing.pk for listing in affected]
        changes = {"status": "removed"}
        if _has_field(Listing, "auto_flagged"):
            changes["auto_flagged"] = False
        Listing.objects.filter(pk__in=ids).update(**changes)
        Report.objects.filter(listing_id__in=ids, status__in=UNRESOLVED).update(
            status="actioned", reviewed_at=timezone.now(), reviewed_by=request.user
        )
        _audit(request, affected, "Rejected in bulk: listing removed from the site.")
        self.message_user(request, f"{len(ids)} listing(s) rejected and removed from the site.")

    @admin.action(description="Put selected listings on hold for review")
    def hold_listings(self, request, queryset):
        affected = list(queryset.filter(status="active"))
        Listing.objects.filter(pk__in=[listing.pk for listing in affected]).update(status="on_hold")
        _audit(request, affected, "Put on hold for review in bulk.")
        self.message_user(request, f"{len(affected)} active listing(s) put on hold for review.")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "listing", "reason", "reporter", "status", "created_at")
    list_filter = ("status", "reason")
    list_select_related = ("listing", "reporter")
    search_fields = ("listing__title", "reporter__email", "details")
    date_hierarchy = "created_at"
    readonly_fields = ("listing", "reporter", "reason", "details", "created_at", "reviewed_at", "reviewed_by")
    actions = ["mark_reviewed", "dismiss_reports", "remove_listings_and_close"]

    def has_add_permission(self, request):
        return False  # reports only come from students

    @admin.action(description="Mark selected reports as reviewed")
    def mark_reviewed(self, request, queryset):
        affected = list(queryset.filter(status="open"))
        Report.objects.filter(pk__in=[r.pk for r in affected]).update(
            status="reviewed", reviewed_at=timezone.now(), reviewed_by=request.user
        )
        _audit(request, affected, "Marked as reviewed.")
        self.message_user(request, f"{len(affected)} report(s) marked as reviewed.")

    @admin.action(description="Dismiss selected reports (no action needed)")
    def dismiss_reports(self, request, queryset):
        affected = list(queryset.filter(status__in=UNRESOLVED))
        Report.objects.filter(pk__in=[r.pk for r in affected]).update(
            status="dismissed", reviewed_at=timezone.now(), reviewed_by=request.user
        )
        _audit(request, affected, "Dismissed: no action needed.")
        self.message_user(request, f"{len(affected)} report(s) dismissed.")

    @admin.action(description="Remove the reported listings and close these reports")
    def remove_listings_and_close(self, request, queryset):
        chosen = list(queryset.filter(status__in=UNRESOLVED))
        listing_ids = {r.listing_id for r in chosen}
        changes = {"status": "removed"}
        if _has_field(Listing, "auto_flagged"):
            changes["auto_flagged"] = False
        removed = list(Listing.objects.filter(pk__in=listing_ids).exclude(status="removed"))
        Listing.objects.filter(pk__in=[l.pk for l in removed]).update(**changes)
        # every unresolved report about those listings is now settled, not just the selected ones
        Report.objects.filter(listing_id__in=listing_ids, status__in=UNRESOLVED).update(
            status="actioned", reviewed_at=timezone.now(), reviewed_by=request.user
        )
        _audit(request, removed, "Removed from the site after a report.")
        self.message_user(request, f"{len(removed)} listing(s) removed and their reports closed.")