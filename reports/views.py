from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from marketplace.models import Listing

from .forms import ReportForm
from .models import Report


@login_required  # only logged-in students can report
def report_listing_view(request, pk):
    # Only listings a student can actually see (active or sold) can be reported.
    # Anything else (held, removed, or a wrong id) gives a 404.
    listing = get_object_or_404(Listing, pk=pk, status__in=["active", "sold"])

    # You can't report your own listing.
    if listing.seller_id == request.user.id:
        messages.info(request, "You can't report your own listing.")
        return redirect("listing_detail", pk=listing.pk)

    # One open report per student per listing (stops the same person sending it again and again).
    if Report.objects.filter(listing=listing, reporter=request.user, status="open").exists():
        messages.info(request, "You've already reported this listing. Our team will review it.")
        return redirect("listing_detail", pk=listing.pk)

    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)  # build the Report but don't save it yet...
            report.listing = listing          # ...fill in the parts the student doesn't choose...
            report.reporter = request.user
            report.save()                     # ...and save it
            messages.success(request, "Thanks. Your report has been sent to our team.")
            return redirect("listing_detail", pk=listing.pk)
    else:
        form = ReportForm()  # first visit: show an empty form
    return render(request, "reports/report_form.html", {"form": form, "listing": listing})


@login_required
def dashboard_view(request):
    # Staff only. Everyone else gets a 404, as if the page didn't exist.
    if not request.user.is_staff:
        raise Http404

    week_ago = timezone.now() - timedelta(days=7)

    # How many listings are in each status, e.g. {"active": 12, "sold": 3}.
    # order_by() with no arguments switches off the default ordering, which would break the counting.
    by_status = dict(Listing.objects.order_by().values_list("status").annotate(Count("id")))

    stats = {
        "students": get_user_model().objects.count(),
        "active": by_status.get("active", 0),
        "sold": by_status.get("sold", 0),
        "held": by_status.get("on_hold", 0),
        "removed": by_status.get("removed", 0),
        "new_listings": Listing.objects.filter(created_at__gte=week_ago).count(),  # posted in the last 7 days
        "open_reports": Report.objects.filter(status="open").count(),
    }

    # Listings waiting for a staff decision (oldest first), at most 10.
    held = Listing.objects.filter(status="on_hold").select_related("seller").order_by("created_at")[:10]

    # Listings with open reports, the most reported first, at most 10.
    most_reported = (
        Listing.objects.annotate(open_reports=Count("reports", filter=Q(reports__status="open")))
        .filter(open_reports__gt=0)
        .select_related("seller")
        .order_by("-open_reports")[:10]
    )

    return render(request, "reports/dashboard.html", {
        "stats": stats,
        "held": held,
        "most_reported": most_reported,
    })