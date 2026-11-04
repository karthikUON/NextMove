from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from marketplace.models import (
    Category,
    Favorite,
    Listing,
    ListingFlag,
    ModerationKeyword,
)

from .models import Report

# chart days
CHART_DAYS = 14


# percentage form
def _pct(part, whole):
    return round(100 * part / whole) if whole else 0


# dashboard stats
def dashboard_stats(now=None):
    """Every number on the admin dashboard. Counts only: no message text, no personal details."""
    # get the present date
    now = now or timezone.now()
    week_ago = now - timedelta(days=7)
    # get user model
    User = get_user_model()

    users = {
        "total": User.objects.count(),
        "verified": User.objects.filter(is_verified=True).count(),
        "new_week": User.objects.filter(date_joined__gte=week_ago).count(),
    }

    # listings 
    by_status = {
        # listing status 
        r["status"]: r["n"]
        # listing 
        for r in Listing.objects.values("status").annotate(n=Count("id")).order_by()
    }
    total = sum(by_status.values())
    status_rows = [
        {
            "key": key,
            "label": label,
            "count": by_status.get(key, 0),
            "pct": _pct(by_status.get(key, 0), total),
        }
        for key, label in Listing.STATUS_CHOICES
    ]
    listings = {
        "total": total,
        "active": by_status.get("active", 0),
        "new_week": Listing.objects.filter(created_at__gte=week_ago).count(),
        "tradeable": Listing.objects.filter(status="active", is_tradeable=True).count(),
    }

    categories = [
        {"name": c.name, "count": c.n}
        for c in Category.objects.annotate(
            n=Count("listings", filter=Q(listings__status="active"))
        ).order_by("-n", "name")[:8]
    ]
    most = max([c["count"] for c in categories] or [0])
    for c in categories:
        c["pct"] = _pct(c["count"], most)

    campus_names = dict(Listing.CAMPUS_CHOICES)
    campuses = [
        {"name": campus_names.get(r["campus"], r["campus"]), "count": r["n"]}
        for r in Listing.objects.filter(status="active")
        .values("campus")
        .annotate(n=Count("id"))
        .order_by("-n")
    ]

    # ---- new listings per day, last 14 days (zero-filled)
    first_day = (now - timedelta(days=CHART_DAYS - 1)).date()
    per_day = {
        r["day"]: r["n"]
        for r in Listing.objects.filter(created_at__date__gte=first_day)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(n=Count("id"))
        .order_by()
    }
    series = []
    for i in range(CHART_DAYS):
        day = first_day + timedelta(days=i)
        series.append({"day": day, "count": per_day.get(day, 0)})
    peak = max([d["count"] for d in series] or [0])
    for d in series:
        d["height"] = max(3, round(60 * d["count"] / peak)) if peak else 3

    # ---- moderation
    held_qs = (
        Listing.objects.filter(status="on_hold")
        .select_related("seller")
        .prefetch_related("flags")
    )
    held = []
    for listing in held_qs.order_by("created_at")[:10]:
        reasons = [
            getattr(f, "reason", "") or str(f.keyword) for f in listing.flags.all()
        ]
        held.append({"listing": listing, "reasons": reasons})
    moderation = {
        "held_count": held_qs.count(),
        "keywords": ModerationKeyword.objects.count(),
        "flags_week": ListingFlag.objects.filter(created_at__gte=week_ago).count(),
    }

    # ---- reports
    reason_names = dict(Report.REASON_CHOICES)
    open_reports = Report.objects.filter(status="open")
    reports = {
        "open": open_reports.count(),
        "new_week": Report.objects.filter(created_at__gte=week_ago).count(),
        "by_reason": [
            {"name": reason_names.get(r["reason"], r["reason"]), "count": r["n"]}
            for r in open_reports.values("reason")
            .annotate(n=Count("id"))
            .order_by("-n")
        ],
        "top": [
            {"listing": l, "open": l.n}
            for l in Listing.objects.annotate(
                n=Count("reports", filter=Q(reports__status="open"))
            )
            .filter(n__gt=0)
            .select_related("seller")
            .order_by("-n", "created_at")[:10]
        ],
    }

    # ---- engagement (messaging is optional: the dashboard still works without it)
    engagement = {"favorites": Favorite.objects.count(), "messaging": None}
    try:
        from messaging.models import Conversation, Message
    except ImportError:
        pass
    else:
        engagement["messaging"] = {
            "conversations": Conversation.objects.count(),
            "messages": Message.objects.count(),
            "messages_week": Message.objects.filter(created_at__gte=week_ago).count(),
        }

    return {
        "users": users,
        "listings": listings,
        "status_rows": status_rows,
        "categories": categories,
        "campuses": campuses,
        "series": series,
        "held": held,
        "moderation": moderation,
        "reports": reports,
        "engagement": engagement,
    }
