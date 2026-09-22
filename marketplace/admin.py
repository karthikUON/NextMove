from django.contrib import admin
from .models import Category, Listing


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "campus", "price", "status", "created_at")
    list_filter = ("status", "category", "campus")
    search_fields = ("title", "description")
