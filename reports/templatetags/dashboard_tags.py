from datetime import timedelta

from django import template
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone

from marketplace.models import Listing
from reports.models import Report

register = template.Library()


@register.simple_tag
def dashboard_stats():
    """The numbers for the dashboard at the top of the admin home page.

    The admin home template calls it like this:  {% dashboard_stats as dash %}
    """
    week_ago = timezone.now() - timedelta(days=7)

    # How many listings are in each status, e.g. {"active": 12, "sold": 3}.
    # order_by() with no arguments switches off the default ordering, which would break the counting.
    by_status = dict(
        Listing.objects.order_by().values_list("status").annotate(Count("id"))
    )

    stats = {
        "students": get_user_model().objects.count(),
        "active": by_status.get("active", 0),
        "sold": by_status.get("sold", 0),
        "held": by_status.get("on_hold", 0),
        "removed": by_status.get("removed", 0),
        "new_listings": Listing.objects.filter(
            created_at__gte=week_ago
        ).count(),  # posted in the last 7 days
        "open_reports": Report.objects.filter(status="open").count(),
    }

    # Listings waiting for a staff decision (oldest first), at most 10.
    held = (
        Listing.objects.filter(status="on_hold")
        .select_related("seller")
        .order_by("created_at")[:10]
    )

    # Listings with open reports, the most reported first, at most 10.
    most_reported = (
        Listing.objects.annotate(
            open_reports=Count("reports", filter=Q(reports__status="open"))
        )
        .filter(open_reports__gt=0)
        .select_related("seller")
        .order_by("-open_reports")[:10]
    )

    return {"stats": stats, "held": held, "most_reported": most_reported}
