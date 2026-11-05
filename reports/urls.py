from django.urls import path

from . import views

urlpatterns = [
    # /listings/5/report/  : the "report this listing" form
    path("listings/<int:pk>/report/", views.report_listing_view, name="report_listing"),
    # /dashboard/  : the staff-only statistics page
    path("dashboard/", views.dashboard_view, name="dashboard"),
]