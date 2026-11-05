from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

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
    if Report.objects.filter(
        listing=listing, reporter=request.user, status="open"
    ).exists():
        messages.info(
            request, "You've already reported this listing. Our team will review it."
        )
        return redirect("listing_detail", pk=listing.pk)

    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(
                commit=False
            )  # build the Report but don't save it yet...
            report.listing = (
                listing  # ...fill in the parts the student doesn't choose...
            )
            report.reporter = request.user
            report.save()  # ...and save it
            messages.success(request, "Thanks. Your report has been sent to our team.")
            return redirect("listing_detail", pk=listing.pk)
    else:
        # first visit: show an empty form. /listings/5/report/?reason=scam pre-selects "Scam or fraud"
        # (the scam warning in a chat links here)
        form = ReportForm(initial={"reason": request.GET.get("reason", "")})
    return render(
        request, "reports/report_form.html", {"form": form, "listing": listing}
    )


@login_required
def dashboard_view(request):
    # The dashboard now lives on the admin home page. This keeps the old /dashboard/ address
    # working: staff are sent to the admin home, everyone else gets a 404.
    if not request.user.is_staff:
        raise Http404
    return redirect("admin:index")
