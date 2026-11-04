from django.urls import path

from . import views

urlpatterns = [
    path("listings/<int:pk>/report/", views.report_listing_view, name="report_listing"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
]