from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("browse/", views.browse_view, name="browse"),
]
