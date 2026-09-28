from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from .models import Category, Listing


def home_view(request):
    # HOMEPAGE — runs when someone visits 
    recent = Listing.objects.filter(status="active").select_related("category")[:8]
     # Get the 8 newest active listings (category fetched in the same query for speed).
     # Send the categories, the 4 campuses, and the recent listings to the homepage template.
    return render(request, "marketplace/home.html", {
        "categories": Category.objects.all(),
        "recent": recent,
        "campus_choices": Listing.CAMPUS_CHOICES,
    })


def browse_view(request):
    # Start with ALL active listings
    listings = Listing.objects.filter(status="active").select_related("category")
   # Read each filter value from the URL (e.g. /browse/?campus=sydney)
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
