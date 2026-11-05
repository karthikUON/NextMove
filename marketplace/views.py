from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import ListingForm

# added fav in w7
from .models import Category, Favorite, Listing, ListingImage


# Week 7: the set of listing IDs the current user has favorited.
# This card template uses it to decide, filled heart or empty heart? which indicates the favs
def _favorited_ids(request):
    if request.user.is_authenticated:
        return set(
            Favorite.objects.filter(user=request.user).values_list(
                "listing_id", flat=True
            )
        )
    # not logged in, no favorites, so every heart shows empty
    return set()


def home_view(request):
    recent = Listing.objects.filter(status="active").select_related("category")[:8]
    return render(
        request,
        "marketplace/home.html",
        {
            "categories": Category.objects.all(),
            "recent": recent,
            "campus_choices": Listing.CAMPUS_CHOICES,
            # added in week 7
            "favorited_ids": _favorited_ids(request),
        },
    )


def browse_view(request):
    # listings = Listing.objects.filter(status="active").select_related("category")
    # Everyone can browse active listings.
    # saw this from stackoverall to pass with Q Query tree
    visible = Q(status="active")
    # Q(...) | Q(...) means either condition can match. Our existing search, category, campus, and price filters still apply afterward.
    # The creator can also see their own held listings.
    if request.user.is_authenticated:
        visible |= Q(
            seller=request.user,
            status="on_hold",
        )

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

    return render(
        request,
        "marketplace/browse.html",
        {
            "page_obj": page_obj,
            "categories": Category.objects.all(),
            "current_category": category_slug,
            "current_campus": campus,
            "query": q,
            "sort": sort,
            "campus_choices": Listing.CAMPUS_CHOICES,
            # added in week 7
            "favorited_ids": _favorited_ids(request),
        },
    )


@login_required
def my_listings_view(request):
    # Only fetch listings created by the logged user added by karthik
    # Includes active, on-hold, sold and removed listings.
    listings = Listing.objects.filter(seller=request.user).exclude(status="removed")

    paginator = Paginator(listings, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "marketplace/my_listings.html",
        {
            "page_obj": page_obj,
            "favorited_ids": _favorited_ids(request),
        },
    )


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


# @login_required
# # detailed view of the listings
# def listing_detail_view(request, pk):
#     listing = get_object_or_404(
#         Listing.objects.select_related("category", "seller"), pk=pk
#     )
#     # added by chinni for the owners and checking for staf (admin maybe)
#     is_owner = request.user.is_authenticated and listing.seller_id == request.user.id
#     # is_owner = request.user.is_authenticated and listing.seller_id == request.user.id
#     is_staff = request.user.is_authenticated and request.user.is_staff
#     # removed listings: owner only. On-hold listings: owner and staff only.
#     if listing.status == "removed" and not is_owner:
#         raise Http404
#     if listing.status == "on_hold" and not (is_owner or is_staff):
#         raise Http404
#     # renter the listings details
#     return render(
#         request,
#         "marketplace/listing_detail.html",
#         {
#             "listing": listing,
#             "images": list(
#                 listing.images.filter(is_deleted=False)
#             ),  # cover photo first
#             "is_owner": is_owner,
#             # added in w7, tells the detail page whether this listing is saved.
#             "is_favorited": request.user.is_authenticated
#             and listing.pk in _favorited_ids(request),
#             "flags": list(listing.flags.all()) if is_staff else [],
#         },
#     )


# @login_required
# def edit_listing_view(request, pk):
#     # non-owners (and removed listings) get a 404, so a listing's existence isn't revealed
#     listing = get_object_or_404(
#         Listing.objects.exclude(status="removed"), pk=pk, seller=request.user
#     )
#     images = list(listing.images.filter(is_deleted=False))
#     if request.method == "POST":
#         delete_ids = {
#             int(i) for i in request.POST.getlist("delete_images") if i.isdecimal()
#         }
#         keep_count = len([img for img in images if img.pk not in delete_ids])
#         form = ListingForm(
#             request.POST, request.FILES, instance=listing, existing_count=keep_count
#         )
#         if form.is_valid():
#             with transaction.atomic():
#                 form.save()
#                 for img in images:  # only this listing's own live photos can be removed
#                     if img.pk in delete_ids:
#                         img.is_deleted = True  # soft delete: row and file are kept
#                         img.is_primary = (
#                             False  # so a deleted cover never blocks a new one
#                         )
#                         img.save(update_fields=["is_deleted", "is_primary"])
#                 _save_new_images(listing, form.cleaned_data["images"])
#                 cover = request.POST.get("cover", "")
#                 if (
#                     cover.isdecimal()
#                     and listing.images.filter(pk=int(cover), is_deleted=False).exists()
#                 ):
#                 if listing.status == "on_hold":
#                     messages.warning(request, "Listing posted, but it's on hold while it's reviewed. It will appear once approved.")
#                 else:
#                     messages.success(request, "Listing posted.")
#                     listing.images.update(is_primary=False)
#                     listing.images.filter(pk=int(cover)).update(is_primary=True)
#                 _ensure_primary(listing)
#             messages.success(request, "Listing updated.")
#             return redirect("listing_detail", pk=listing.pk)
#     else:
#         form = ListingForm(instance=listing, existing_count=len(images))

#     return render(
#         request,
#         "marketplace/listing_form.html",
#         {
#             "form": form,
#             "editing": True,
#             "listing": listing,
#             "existing_images": images,
#         },
#     )


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
    listing = get_object_or_404(
        Listing.objects.exclude(status="removed"), pk=pk, seller=request.user
    )
    listing.status = "removed"
    listing.save(update_fields=["status"])
    messages.success(request, "Listing deleted.")
    return redirect("browse")


# Week 7: Favorites
# user must login

# @login_required
# @require_POST
# def toggle_favorite_view(request, pk):
#     """One button that both saves and un-saves."""
#     # only visible listings can be saved (not removed or on-hold ones)
#     listing = get_object_or_404(Listing, pk=pk, status__in=["active", "sold"])
#     if listing.seller_id == request.user.id:
#         messages.info(request, "You can't save your own listing.")
#     else:
#         favorite, created = Favorite.objects.get_or_create(user=request.user, listing=listing)
#         if created:
#             messages.success(request, "Saved to your favorites.")
#         else:
#             favorite.delete()  # already saved, so this click removes it
#             messages.info(request, "Removed from your favorites.")
#     # send the student back to the page they clicked from, but only to a page on this site
#     next_url = request.POST.get("next", "")
#     # check the newxt url and if url has allowerd
#     # used to check whether a given redirect URL is safe by verifying that its scheme is http or https (or strictly https) and that its host matches a trusted allowlist (allowed_hosts)
#     if next_url and url_has_allowed_host_and_scheme(
#         next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
#     ):
#         return redirect(next_url)
#     return redirect("listing_detail", pk=listing.pk)


# @login_required
# def favorites_view(request):
#     """The 'My favorites' page."""
#     favorites = (
#         # only visible listings (active or sold); held and removed ones stay hidden
#         Favorite.objects.filter(user=request.user, listing__status__in=["active", "sold"])
#         .select_related("listing", "listing__category")
#     )
#     listings = [f.listing for f in favorites]
#     return render(request, "marketplace/favorites.html", {
#         "listings": listings,
#         "favorited_ids": {l.pk for l in listings},
#     })


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
            # decided AFTER save(), because the keyword scan runs inside save()
            if listing.status == "on_hold":
                messages.warning(
                    request,
                    "Listing posted, but it's on hold while it's reviewed. It will appear once approved.",
                )
            else:
                messages.success(request, "Listing posted.")
            return redirect("listing_detail", pk=listing.pk)
    else:
        form = ListingForm()
    # send the renter data to the html
    return render(
        request, "marketplace/listing_form.html", {"form": form, "editing": False}
    )


@login_required
def edit_listing_view(request, pk):
    # non-owners (and removed listings) get a 404, so a listing's existence isn't revealed
    listing = get_object_or_404(
        Listing.objects.exclude(status="removed"), pk=pk, seller=request.user
    )
    images = list(listing.images.filter(is_deleted=False))
    if request.method == "POST":
        delete_ids = {
            int(i) for i in request.POST.getlist("delete_images") if i.isdecimal()
        }
        keep_count = len([img for img in images if img.pk not in delete_ids])
        form = ListingForm(
            request.POST, request.FILES, instance=listing, existing_count=keep_count
        )
        if form.is_valid():
            with transaction.atomic():
                form.save()
                for img in images:  # only this listing's own live photos can be removed
                    if img.pk in delete_ids:
                        img.is_deleted = True  # soft delete: row and file are kept
                        img.is_primary = (
                            False  # so a deleted cover never blocks a new one
                        )
                        img.save(update_fields=["is_deleted", "is_primary"])
                _save_new_images(listing, form.cleaned_data["images"])
                cover = request.POST.get("cover", "")
                if (
                    cover.isdecimal()
                    and listing.images.filter(pk=int(cover), is_deleted=False).exists()
                ):
                    listing.images.update(is_primary=False)
                    listing.images.filter(pk=int(cover)).update(is_primary=True)
                _ensure_primary(listing)
            if listing.status == "on_hold":
                messages.warning(
                    request, "Listing updated, but it's on hold while it's reviewed."
                )
            else:
                messages.success(request, "Listing updated.")
            return redirect("listing_detail", pk=listing.pk)
    else:
        form = ListingForm(instance=listing, existing_count=len(images))

    return render(
        request,
        "marketplace/listing_form.html",
        {
            "form": form,
            "editing": True,
            "listing": listing,
            "existing_images": images,
        },
    )


# Week 7: Favorites
# user must login
@login_required
@require_POST
def toggle_favorite_view(request, pk):
    # Only active or sold listings can be saved.
    listing = get_object_or_404(
        Listing,
        pk=pk,
        status__in=["active", "sold"],
    )

    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        listing=listing,
    )

    if created:
        messages.success(request, "Saved to your favorites.")
    else:
        favorite.delete()
        messages.info(request, "Removed from your favorites.")

    # Return to the current page only when the URL is safe.
    next_url = request.POST.get("next", "")

    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)

    return redirect("listing_detail", pk=listing.pk)


@login_required
def favorites_view(request):
    """The 'My favorites' page."""
    favorites = (
        # only visible listings (active or sold); held and removed ones stay hidden
        Favorite.objects.filter(
            user=request.user, listing__status__in=["active", "sold"]
        )
        # one query, no N+1
        .select_related("listing", "listing__category")
    )
    listings = [f.listing for f in favorites]
    return render(
        request,
        "marketplace/favorites.html",
        {
            "listings": listings,
            # tells the user every one here IS a favorite, fav tab
            "favorited_ids": {l.pk for l in listings},
        },
    )


@login_required
# detailed view of the listings
def listing_detail_view(request, pk):
    listing = get_object_or_404(
        Listing.objects.select_related("category", "seller"), pk=pk
    )
    # added by chinni for the owners and checking for staf (admin maybe)
    is_owner = request.user.is_authenticated and listing.seller_id == request.user.id
    # is_owner = request.user.is_authenticated and listing.seller_id == request.user.id
    is_staff = request.user.is_authenticated and request.user.is_staff
    # Removed listings (deleted by the seller, or rejected by staff) are gone for everyone, the owner included.
    # The row stays in the database, so staff can still see it in the admin.
    if listing.status == "removed":
        raise Http404
    # On-hold listings: owner and staff only.
    if listing.status == "on_hold" and not (is_owner or is_staff):
        raise Http404
    # renter the listings details
    return render(
        request,
        "marketplace/listing_detail.html",
        {
            "listing": listing,
            "images": list(
                listing.images.filter(is_deleted=False)
            ),  # cover photo first
            "is_owner": is_owner,
            # added in w7, tells the detail page whether this listing is saved.
            "is_favorited": request.user.is_authenticated
            and listing.pk in _favorited_ids(request),
            "flags": list(listing.flags.all()) if is_staff else [],
        },
    )
