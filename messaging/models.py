from django.conf import settings
from django.db import models
from django.utils import timezone

MAX_MESSAGE_LENGTH = 2000

# one chat per listings per user
class Conversation(models.Model):
    """One chat between a buyer and the seller of a listing. A buyer has one chat per listing."""

    # creating the model for listings, buyer and seller and usually created_at
    listing = models.ForeignKey("marketplace.Listing", on_delete=models.CASCADE, related_name="conversations")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations_as_buyer")
    # copied from the listing when the chat starts, so a chat keeps working if the listing's seller changes
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations_as_seller")
    created_at = models.DateTimeField(auto_now_add=True)

    # lets the inbox sort by the newest message
    last_message_at = models.DateTimeField(default=timezone.now)

    class Meta:
        # order by lastmessage_at
        ordering = ["-last_message_at"]
        constraints = [
            models.UniqueConstraint(fields=["listing", "buyer"], name="one_conversation_per_buyer_per_listing"),
        ]
        indexes = [
            models.Index(fields=["buyer", "-last_message_at"]),
            models.Index(fields=["seller", "-last_message_at"]),
        ]

    def __str__(self):
        return f"Conversation {self.pk} about listing {self.listing_id}"

    def is_participant(self, user):
        return user.id in (self.buyer_id, self.seller_id)

    # user is not a buyer else he is other party
    def other_party(self, user):
        return self.seller if user.id == self.buyer_id else self.buyer
    
    # chats will be forever until the listing is available, once listing is sold no one can chat
    def can_reply(self):
        """Chats stay readable forever, but you can only write while the listing is still visible."""
        return self.listing.status in ("active", "sold")


# starts with messages model
class Message(models.Model):
    # build the modle with conversation, sender and bosy and read at
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # set when the OTHER person opens the chat; empty = unread
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["conversation", "read_at"])]

    def __str__(self):
        return f"Message {self.pk} in conversation {self.conversation_id}"
    
    @classmethod
    def unread_count_for(cls, user):
        """Messages waiting for this user: written by the other person and not opened yet."""
        return (
            cls.objects.filter(read_at__isnull=True)
            .filter(models.Q(conversation__buyer=user) | models.Q(conversation__seller=user))
            .exclude(sender=user)
            .count()
    )

