from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # added this by karthik for accounts
    path("accounts/", include("accounts.urls")),
    path("", include("marketplace.urls")),
]
