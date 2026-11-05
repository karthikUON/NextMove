from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Manage students: verify an account by hand, disable a bad one, give someone staff access."""

    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_verified",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = (
        "is_verified",
        "is_active",
        "is_staff",
    )  # the filter box on the right
    search_fields = ("email", "first_name", "last_name")  # the search box at the top
    ordering = ("-date_joined",)  # newest students first

    # The edit page: who they are (read only) and the three switches staff may change.
    # The password is not shown at all.
    fields = (
        "email",
        "first_name",
        "last_name",
        "date_joined",
        "last_login",
        "is_verified",
        "is_active",
        "is_staff",
    )
    readonly_fields = ("email", "first_name", "last_name", "date_joined", "last_login")

    actions = ["verify_users", "disable_users", "enable_users"]

    def has_add_permission(self, request):
        return False  # students sign up on the site (with the email code), staff don't add accounts here

    def has_delete_permission(self, request, obj=None):
        # Don't delete accounts: deleting a student would also delete their listings and chats.
        # Use "Disable selected accounts" instead.
        return False

    @admin.action(description="Mark selected students as verified")
    def verify_users(self, request, queryset):
        count = queryset.filter(is_verified=False).update(is_verified=True)
        self.message_user(request, f"{count} account(s) marked as verified.")

    @admin.action(description="Disable selected accounts (they can no longer log in)")
    def disable_users(self, request, queryset):
        # never disable yourself or another admin by accident
        count = (
            queryset.filter(is_active=True, is_superuser=False)
            .exclude(pk=request.user.pk)
            .update(is_active=False)
        )
        self.message_user(request, f"{count} account(s) disabled.")

    @admin.action(description="Re-enable selected accounts")
    def enable_users(self, request, queryset):
        count = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(request, f"{count} account(s) re-enabled.")
