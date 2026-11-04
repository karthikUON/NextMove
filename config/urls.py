from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # added this by karthik for accounts
    path("accounts/", include("accounts.urls")),
    path("admin/", admin.site.urls),
    path("", include("marketplace.urls")),
]

# added by karthik - development only: serve uploaded photos from /media/ (works while DEBUG = True)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)