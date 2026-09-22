from django.contrib import admin
from django.urls import path, include

urlpatterns = [
<<<<<<< HEAD
    path('admin/', admin.site.urls),
    # added this by karthik for accounts
    path("accounts/", include("accounts.urls")),
=======
    path("admin/", admin.site.urls),
    path("", include("marketplace.urls")),
>>>>>>> 25e5b92 (Week 5: add Listing model, campus field, home and browse pages)
]
