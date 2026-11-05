from datetime import timedelta
from functools import wraps

from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, OuterRef, Q, Subquery
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import date as date_filter
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from marketplace.models import Listing

from .forms import MessageForm
from .models import MAX_MESSAGE_LENGTH, Conversation, Message
from .scam import scam_warnings

# simple spam brake: at most this many messages per person per minute
RATE_LIMIT = 10


def json_login_required(view):
    """Like login_required, but answers with a JSON 401 instead of redirecting (for the script's requests)."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "login"}, status=401)
        return view(request, *args, **kwargs)

    return wrapper


def _is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _message_json(message, me):
    mine = message.sender_id == me.id
    return {
        "id": message.id,
        "mine": mine,
        "body": message.body,  # plain text: the page script inserts it as text, never as HTML
        "time": date_filter(timezone.localtime(message.created_at), "j M, g:i a"),
        # scam shield: only the person who RECEIVED a message is warned about it (nothing is stored)
        "warnings": [] if mine else scam_warnings(message.body),
    }


def _can_report_listing(conversation, user):
    """Show "Report this listing" in the scam warning only to the buyer, for a listing that can still be reported."""
    if user.id != conversation.buyer_id or conversation.listing.status not in (
        "active",
        "sold",
    ):
        return False
    if not apps.is_installed("reports"):  # the reports app is optional
        return False
    from reports.models import Report

    return not Report.objects.filter(
        listing=conversation.listing, reporter=user, status="open"
    ).exists()


def _sending_too_fast(user):
    since = timezone.now() - timedelta(minutes=1)
    return (
        Message.objects.filter(sender=user, created_at__gte=since).count() >= RATE_LIMIT
    )


def _send(conversation, sender, body):
    now = timezone.now()
    message = Message.objects.create(
        conversation=conversation, sender=sender, body=body
    )
    Conversation.objects.filter(pk=conversation.pk).update(last_message_at=now)
    return message


@login_required
@require_POST
def start_conversation_view(request, listing_pk):
    """'Message seller' on a listing: starts the chat (or reuses the one you already have) and sends the first message."""
    # new chats only on listings that are live
    listing = get_object_or_404(Listing, pk=listing_pk, status="active")
    if listing.seller_id is None or listing.seller_id == request.user.id:
        messages.info(request, "You can't message yourself about your own listing.")
        return redirect("listing_detail", pk=listing.pk)

    form = MessageForm(request.POST)
    if not form.is_valid():
        messages.error(
            request, f"Please write a message (up to {MAX_MESSAGE_LENGTH} characters)."
        )
        return redirect("listing_detail", pk=listing.pk)
    if _sending_too_fast(request.user):
        messages.error(
            request, "You're sending messages too quickly. Please wait a minute."
        )
        return redirect("listing_detail", pk=listing.pk)

    conversation, _ = Conversation.objects.get_or_create(
        listing=listing, buyer=request.user, defaults={"seller_id": listing.seller_id}
    )
    _send(conversation, request.user, form.cleaned_data["body"])
    messages.success(request, "Message sent.")
    return redirect("conversation", pk=conversation.pk)


@login_required
def inbox_view(request):
    me = request.user
    newest = Message.objects.filter(conversation=OuterRef("pk")).order_by(
        "-created_at", "-id"
    )
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

    thread = list(conversation.messages.select_related("sender"))
    for m in thread:
        # scam shield: warn the person who RECEIVED a message that looks like a scam (nothing is stored)
        m.scam = [] if m.sender_id == request.user.id else scam_warnings(m.body)

    return render(
        request,
        "messaging/conversation.html",
        {
            "conversation": conversation,
            "thread": thread,
            "has_scam": any(m.scam for m in thread),
            "can_report": _can_report_listing(conversation, request.user),
            "last_id": thread[-1].id if thread else 0,
            "other": conversation.other_party(request.user),
            "can_reply": conversation.can_reply(),
            "form": MessageForm(),
        },
    )


@never_cache
@require_GET
@json_login_required
def messages_since_view(request, pk):
    """The chat page asks this every few seconds: 'anything newer than message <after>?'"""
    conversation = get_object_or_404(
        Conversation.objects.select_related("listing"), pk=pk
    )
    if not conversation.is_participant(request.user):
        raise Http404
    try:
        after = int(request.GET.get("after", 0))
    except ValueError:
        after = 0

    new = list(conversation.messages.filter(id__gt=after).order_by("id"))
    # the person has the chat open, so what the other side wrote counts as read
    conversation.messages.filter(read_at__isnull=True).exclude(
        sender=request.user
    ).update(read_at=timezone.now())
    return JsonResponse(
        {
            "messages": [_message_json(m, request.user) for m in new],
            "last_id": new[-1].id if new else after,
            "can_reply": conversation.can_reply(),
            "unread_total": Message.unread_count_for(request.user),
        }
    )


@never_cache
@require_GET
@json_login_required
def unread_count_view(request):
    """The navbar badge asks this every so often."""
    return JsonResponse({"unread": Message.unread_count_for(request.user)})


@login_required
@require_POST
def send_message_view(request, pk):
    conversation = get_object_or_404(
        Conversation.objects.select_related("listing"), pk=pk
    )
    if not conversation.is_participant(request.user):
        raise Http404
    ajax = _is_ajax(
        request
    )  # the page script sends with fetch(); a plain form post still works without JavaScript

    def refuse(error, status):
        if ajax:
            return JsonResponse({"ok": False, "error": error}, status=status)
        messages.error(request, error)
        return redirect("conversation", pk=conversation.pk)

    if not conversation.can_reply():
        return refuse(
            "This listing is no longer available, so you can't send new messages.", 409
        )
    form = MessageForm(request.POST)
    if not form.is_valid():
        return refuse(
            f"Please write a message (up to {MAX_MESSAGE_LENGTH} characters).", 400
        )
    if _sending_too_fast(request.user):
        return refuse("You're sending messages too quickly. Please wait a minute.", 429)

    message = _send(conversation, request.user, form.cleaned_data["body"])
    if ajax:
        return JsonResponse(
            {"ok": True, "message": _message_json(message, request.user)}
        )
    return redirect("conversation", pk=conversation.pk)
