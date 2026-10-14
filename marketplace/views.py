from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ListingForm
from .models import Category, Listing, ListingImage


def home_view(request):
    recent = Listing.objects.filter(status="active").select_related("category")[:8]
    return render(request, "marketplace/home.html", {
        "categories": Category.objects.all(),
        "recent": recent,
        "campus_choices": Listing.CAMPUS_CHOICES,
    })


def browse_view(request):
    listings = Listing.objects.filter(status="active").select_related("category")

    category_slug = request.GET.get("category", "")
    campus = request.GET.get("campus", "")
    q = request.GET.get("q", "")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    sort = request.GET.get("sort", "newest")

    if category_slug:
        listings = listings.filter(category__slug=category_slug)
    if campus:
        listings = listings.filter(campus=campus)
    if q:
        listings = listings.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if min_price:
        listings = listings.filter(price__gte=min_price)
    if max_price:
        listings = listings.filter(price__lte=max_price)

    if sort == "price_asc":
        listings = listings.order_by("price")
    elif sort == "price_desc":
        listings = listings.order_by("-price")
    else:
        listings = listings.order_by("-created_at")

    paginator = Paginator(listings, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "marketplace/browse.html", {
        "page_obj": page_obj,
        "categories": Category.objects.all(),
        "current_category": category_slug,
        "current_campus": campus,
        "query": q,
        "sort": sort,
        "campus_choices": Listing.CAMPUS_CHOICES,
    })

# save a new images, create the images
def _save_new_images(listing, files):
    for f in files:
        ListingImage.objects.create(listing=listing, image=f)

# if the image is cover photo
def _ensure_primary(listing):
    """If the listing has live photos but none is the cover, make the oldest one the cover."""
    live = listing.images.filter(is_deleted=False)
    if live.exists() and not live.filter(is_primary=True).exists():
        first = live.first()
        first.is_primary = True
        first.save(update_fields=["is_primary"])

# detailed view of the listings
def listing_detail_view(request, pk):
    listing = get_object_or_404(Listing.objects.select_related("category", "seller"), pk=pk)
    is_owner = request.user.is_authenticated and listing.seller_id == request.user.id
    if listing.status == "removed" and not is_owner:
        raise Http404
    return render(request, "marketplace/listing_detail.html", {
        "listing": listing,
        "images": list(listing.images.filter(is_deleted=False)),  # cover photo first
        "is_owner": is_owner,
    })

# only login users
@login_required
# post a listing 
def post_listing_view(request):
    # it uses post request.
    if request.method == "POST":
        # get the form object
        form = ListingForm(request.POST, request.FILES)
        # check the form valud
        if form.is_valid():
            # groups all of them in one transaction
            with transaction.atomic():
                # assing the form values
                listing = form.save(commit=False)
                listing.seller = request.user
                listing.save()
                _save_new_images(listing, form.cleaned_data["images"])
                _ensure_primary(listing)
            messages.success(request, "Listing posted.")
            return redirect("listing_detail", pk=listing.pk)
    else:
        form = ListingForm()
    # send the renter data to the html
    return render(request, "marketplace/listing_form.html", {"form": form, "editing": False})



@login_required
def edit_listing_view(request, pk):
    # non-owners (and removed listings) get a 404, so a listing's existence isn't revealed
    listing = get_object_or_404(Listing.objects.exclude(status="removed"), pk=pk, seller=request.user)
    images = list(listing.images.filter(is_deleted=False))

    if request.method == "POST":
        delete_ids = {int(i) for i in request.POST.getlist("delete_images") if i.isdecimal()}
        keep_count = len([img for img in images if img.pk not in delete_ids])
        form = ListingForm(request.POST, request.FILES, instance=listing, existing_count=keep_count)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                for img in images:  # only this listing's own live photos can be removed
                    if img.pk in delete_ids:
                        img.is_deleted = True   # soft delete: row and file are kept
                        img.is_primary = False  # so a deleted cover never blocks a new one
                        img.save(update_fields=["is_deleted", "is_primary"])
                _save_new_images(listing, form.cleaned_data["images"])
                cover = request.POST.get("cover", "")
                if cover.isdecimal() and listing.images.filter(pk=int(cover), is_deleted=False).exists():
                    listing.images.update(is_primary=False)
                    listing.images.filter(pk=int(cover)).update(is_primary=True)
                _ensure_primary(listing)
            messages.success(request, "Listing updated.")
            return redirect("listing_detail", pk=listing.pk)
    else:
        form = ListingForm(instance=listing, existing_count=len(images))

    return render(request, "marketplace/listing_form.html", {
        "form": form, "editing": True, "listing": listing, "existing_images": images,
    })

@login_required
@require_POST
# make it as sold if the status =sold
def mark_sold_view(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user, status="active")
    listing.status = "sold"
    listing.save(update_fields=["status"])
    messages.success(request, "Marked as sold.")
    return redirect("listing_detail", pk=listing.pk)


@login_required
@require_POST
# delete the lsiting which will be sold delete.
def delete_listing_view(request, pk):
    # soft delete: the row stays in the database, it just disappears from the site
    listing = get_object_or_404(Listing.objects.exclude(status="removed"), pk=pk, seller=request.user)
    listing.status = "removed"
    listing.save(update_fields=["status"])
    messages.success(request, "Listing deleted.")
    return redirect("browse")