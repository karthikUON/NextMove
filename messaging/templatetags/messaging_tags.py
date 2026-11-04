from django import template
from django.db.models import Q

from messaging.forms import MessageForm
from messaging.models import Conversation, Message

register = template.Library()

# This provides the navbar badge count and the “Message seller” box, so none of your marketplace views need to change.


@register.simple_tag(takes_context=True)
# unread messages which are fresh
def unread_message_count(context):
    """How many unread messages the logged-in student has (for the navbar badge)."""
    request = context.get("request")
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return 0
    # return the converseation accordingly 
    return (
        Message.objects.filter(read_at__isnull=True)
        .filter(Q(conversation__buyer=user) | Q(conversation__seller=user))
        .exclude(sender=user)
        .count()
    )

# Took this from one of the git repo for showing message seeler 
@register.inclusion_tag("messaging/_message_seller.html", takes_context=True)
# show the message seller box
def message_seller_box(context, listing):
    """The 'Message seller' form on a listing page (or a link to the existing chat)."""
    user = context["request"].user
    conversation = None
    can_start = False
    if user.is_authenticated and listing.seller_id and listing.seller_id != user.id:
        conversation = Conversation.objects.filter(listing=listing, buyer=user).first()
        can_start = conversation is None and listing.status == "active"
    return {
        "listing": listing,
        "conversation": conversation,
        "can_start": can_start,
        "form": MessageForm(),
        "csrf_token": context.get("csrf_token"),
    }
