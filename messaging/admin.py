from django.contrib import admin
from django.db.models import Count

from .models import Conversation


# Staff can see that a conversation exists (who, which listing, how many messages) but NOT read it.
# Message text is private: there is deliberately no admin page for the Message model.
# Decide as a team when staff may read a chat (e.g. a reported one) before changing that.
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "listing",
        "buyer",
        "seller",
        "message_count",
        "last_message_at",
    )
    search_fields = ("listing__title", "buyer__email", "seller__email")
    ordering = ("-last_message_at",)  # most recently active first
    readonly_fields = ("listing", "buyer", "seller", "created_at", "last_message_at")

    def get_queryset(self, request):
        # count the messages in the same query (no extra database hit per row)
        return super().get_queryset(request).annotate(_message_count=Count("messages"))

    @admin.display(description="Messages", ordering="_message_count")
    def message_count(self, obj):
        return obj._message_count

    def has_add_permission(self, request):
        return False
