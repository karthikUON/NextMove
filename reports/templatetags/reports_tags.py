from django import template

from reports.models import Report

register = template.Library()


@register.inclusion_tag("reports/_report_link.html", takes_context=True)
def report_link(context, listing):
    """'Report this listing' under a listing (nothing for the owner, logged-out visitors or hidden listings)."""
    user = context["request"].user
    show = already = False
    if user.is_authenticated and listing.seller_id != user.id and listing.status in ("active", "sold"):
        already = Report.objects.filter(listing=listing, reporter=user, status="open").exists()
        show = not already
    return {"listing": listing, "show": show, "already": already}