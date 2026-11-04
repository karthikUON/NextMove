from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from marketplace.models import Listing

from .forms import ReportForm
from .models import Report
from .stats import dashboard_stats

# at most this many reports per student per day (stops report spam)
DAILY_REPORT_LIMIT = 10


def staff_required(view):
    """Staff only. Anyone else gets a 404, so the page's existence isn't revealed."""
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404
        return view(request, *args, **kwargs)
    return wrapper


@login_required
def report_listing_view(request, pk):
    # only listings a student can actually see can be reported
    listing = get_object_or_404(Listing, pk=pk, status__in=["active", "sold"])
    if listing.seller_id == request.user.id:
        messages.info(request, "You can't report your own listing.")
        return redirect("listing_detail", pk=listing.pk)
    if Report.objects.filter(listing=listing, reporter=request.user, status="open").exists():
        messages.info(request, "You've already reported this listing. Our team will review it.")
        return redirect("listing_detail", pk=listing.pk)

    if request.method == "POST":
        since = timezone.now() - timedelta(days=1)
        if Report.objects.filter(reporter=request.user, created_at__gte=since).count() >= DAILY_REPORT_LIMIT:
            messages.error(request, "You've sent a lot of reports today. Please try again tomorrow.")
            return redirect("listing_detail", pk=listing.pk)
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.listing = listing
            report.reporter = request.user
            report.save()
            messages.success(request, "Thanks. Your report has been sent to our team.")
            return redirect("listing_detail", pk=listing.pk)
    else:
        form = ReportForm()
    return render(request, "reports/report_form.html", {"form": form, "listing": listing})


@staff_required
def dashboard_view(request):
    stats = dashboard_stats()
    for item in stats["held"]:
        item["admin_url"] = reverse("admin:marketplace_listing_change", args=[item["listing"].pk])
    for item in stats["reports"]["top"]:
        item["admin_url"] = reverse("admin:marketplace_listing_change", args=[item["listing"].pk])
    links = {
        "admin": reverse("admin:index"),
        "held": reverse("admin:marketplace_listing_changelist") + "?status__exact=on_hold",
        "reports": reverse("admin:reports_report_changelist") + "?status__exact=open",
    }
    return render(request, "reports/dashboard.html", {"stats": stats, "links": links})