from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("browse/", views.browse_view, name="browse"),
    path("post-listing/", views.post_listing_view, name="post_listing"),
    path("listings/<int:pk>/", views.listing_detail_view, name="listing_detail"),
    path("listings/<int:pk>/edit/", views.edit_listing_view, name="edit_listing"),
    path("listings/<int:pk>/mark-sold/", views.mark_sold_view, name="mark_sold"),
        path("listings/<int:pk>/delete/", views.delete_listing_view, name="delete_listing"),
    # Week 7: favorites
    path("listings/<int:pk>/favorite/", views.toggle_favorite_view, name="toggle_favorite"),
    path("favorites/", views.favorites_view, name="favorites"),
    path("my-listings/", views.my_listings_view, name="my_listings"),
]