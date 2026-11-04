from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, OuterRef, Q, Subquery
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from marketplace.models import Listing

from .forms import MessageForm
from .models import MAX_MESSAGE_LENGTH, Conversation, Message

# simple spam brake: at most this many messages per person per minute
RATE_LIMIT = 10


# if sending too fast
def _sending_too_fast(user):
    since = timezone.now() - timedelta(minutes=1)
    # check the late limit
    return (
        Message.objects.filter(sender=user, created_at__gte=since).count() >= RATE_LIMIT
    )


# send the message
def _send(conversation, sender, body):
    now = timezone.now()
    message = Message.objects.create(
        conversation=conversation, sender=sender, body=body
    )
    # update the last message to now.
    Conversation.objects.filter(pk=conversation.pk).update(last_message_at=now)
    return message


@login_required
@require_POST
# start the conversation
def start_conversation_view(request, listing_pk):
    """'Message seller' on a listing: starts the chat (or reuses the one you already have) and sends the first message."""
    # new chats only on listings that are only active
    listing = get_object_or_404(Listing, pk=listing_pk, status="active")
    # adding condition t check message to own listings
    if listing.seller_id is None or listing.seller_id == request.user.id:
        messages.info(request, "You can't message yourself about your own listing.")
        return redirect("listing_detail", pk=listing.pk)
    # create the form object
    form = MessageForm(request.POST)
    # check if it is valid or not
    if not form.is_valid():
        messages.error(
            request, f"Please write a message (up to {MAX_MESSAGE_LENGTH} characters)."
        )
        return redirect("listing_detail", pk=listing.pk)
    # check if sending too fast
    if _sending_too_fast(request.user):
        messages.error(
            request, "You're sending messages too quickly. Please wait a minute."
        )
        return redirect("listing_detail", pk=listing.pk)
    # create the conversation object 
    conversation, _ = Conversation.objects.get_or_create(
        listing=listing, buyer=request.user, defaults={"seller_id": listing.seller_id}
    )
    # send the object to the user along with the form data
    _send(conversation, request.user, form.cleaned_data["body"])
    messages.success(request, "Message sent.")
    return redirect("conversation", pk=conversation.pk)


@login_required
def inbox_view(request):
    # get the user
    me = request.user
    # order the message in the newest
    newest = Message.objects.filter(conversation=OuterRef("pk")).order_by(
        "-created_at", "-id"
    )
    # copied this from online to show according how to arrange the message
    conversations = (
        Conversation.objects.filter(Q(buyer=me) | Q(seller=me))
        .select_related("listing", "buyer", "seller")
        .annotate(
            last_body=Subquery(newest.values("body")[:1]),
            last_sender_id=Subquery(newest.values("sender_id")[:1]),
            unread=Count(
                "messages",
                filter=Q(messages__read_at__isnull=True) & ~Q(messages__sender=me),
            ),
        )
        # newest message first (Django ignores the model's default ordering once a query counts rows)
        .order_by("-last_message_at", "-pk")
    )
    page_obj = Paginator(conversations, 20).get_page(request.GET.get("page"))
    for c in page_obj:
        c.other = c.other_party(me)  # the person I'm talking to
        c.buying = c.buyer_id == me.id  # True = I'm the buyer, False = I'm the seller
    return render(request, "messaging/inbox.html", {"page_obj": page_obj})


@login_required
def conversation_view(request, pk):
    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "buyer", "seller"), pk=pk
    )
    if not conversation.is_participant(request.user):
        raise Http404  # a 404, so other people's chats can't even be discovered

    # opening the chat marks what the other person wrote as read
    conversation.messages.filter(read_at__isnull=True).exclude(
        sender=request.user
    ).update(read_at=timezone.now())

    return render(
        request,
        "messaging/conversation.html",
        {
            "conversation": conversation,
            "thread": conversation.messages.select_related("sender"),
            "other": conversation.other_party(request.user),
            "can_reply": conversation.can_reply(),
            "form": MessageForm(),
        },
    )


@login_required
@require_POST
def send_message_view(request, pk):
    conversation = get_object_or_404(
        Conversation.objects.select_related("listing"), pk=pk
    )
    if not conversation.is_participant(request.user):
        raise Http404
    if not conversation.can_reply():
        messages.error(
            request,
            "This listing is no longer available, so you can't send new messages.",
        )
        return redirect("conversation", pk=conversation.pk)

    form = MessageForm(request.POST)
    if not form.is_valid():
        messages.error(
            request, f"Please write a message (up to {MAX_MESSAGE_LENGTH} characters)."
        )
    elif _sending_too_fast(request.user):
        messages.error(
            request, "You're sending messages too quickly. Please wait a minute."
        )
    else:
        _send(conversation, request.user, form.cleaned_data["body"])
    return redirect("conversation", pk=conversation.pk)
