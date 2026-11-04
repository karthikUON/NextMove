from django.contrib import admin
from .models import Category, Favorite, Listing, ListingFlag, ModerationKeyword


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


# W7: show a listing's flags right on the listing's own admin page.
class ListingFlagInline(admin.TabularInline):
    model = ListingFlag
    extra = 0
    readonly_fields = ("keyword", "reason", "created_at")
    can_delete = False


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "campus", "price", "status", "auto_flagged", "created_at")
    list_filter = ("status", "auto_flagged", "category", "campus")   
    search_fields = ("title", "description")
    inlines = [ListingFlagInline]       
    actions = ["approve_listings"]      

    # Week 7: tick listings -> choose this action -> they go back to Active.
    # We use .update() (not .save()) ON PURPOSE: it writes straight to the DB and
    # SKIPS the save() scan, so an approved listing isn't instantly re-held.
    @admin.action(description="Approve selected listings (set to Active)")
    def approve_listings(self, request, queryset):
        updated = queryset.filter(status="on_hold").update(status="active", auto_flagged=False)
        self.message_user(request, f"{updated} listing(s) approved and set to Active.")


@admin.register(ModerationKeyword)
class ModerationKeywordAdmin(admin.ModelAdmin):
    list_display = ("keyword", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("keyword",)


@admin.register(ListingFlag)
class ListingFlagAdmin(admin.ModelAdmin):
    list_display = ("listing", "keyword", "reason", "created_at")
    list_filter = ("keyword__category",)
    search_fields = ("listing__title", "reason")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "listing", "created_at")
    search_fields = ("user__email", "listing__title")