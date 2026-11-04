from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from marketplace.models import Listing
from messaging.models import Conversation, Message

User = get_user_model()

# the demo students created by `seed_data`
EMAILS = {
    "aarav": "aarav.mehta@uon.edu.au",
    "priya": "priya.nair@uon.edu.au",
    "liam": "liam.oconnor@uon.edu.au",
    "sara": "sara.khan@uon.edu.au",
    "tom": "tom.nguyen@uon.edu.au",
}

# (buyer, listing title, [(who writes, text), ...]). The LAST message is left unread.
CHATS = [
    ("priya", "IKEA study desk", [
        ("priya", "Hi! Is the desk still available?"),
        ("aarav", "Hey Priya, yes it is. Pickup is from Callaghan, any weekday after 3."),
        ("priya", "Great! Would $40 work for you?"),
    ]),
    ("liam", "Dell laptop - i5, 8GB RAM", [
        ("liam", "Does the laptop come with the charger?"),
        ("sara", "Yes, charger included, and the battery lasts about five hours."),
    ]),
    ("tom", "Electric scooter", [
        ("tom", "Would you swap it for a road bike?"),
        ("priya", "Possibly! What model is it?"),
        ("tom", "A Giant Escape, bought in 2021, serviced this year."),
    ]),
]


class Command(BaseCommand):
    help = "Adds a few demo conversations between the seeded students (run `seed_data` first). Safe to run twice."

    def handle(self, *args, **options):
        users = {key: User.objects.filter(email=email).first() for key, email in EMAILS.items()}
        made = 0
        for buyer_key, title, lines in CHATS:
            listing = Listing.objects.filter(title=title).first()
            buyer = users[buyer_key]
            if listing is None or listing.seller_id is None or buyer is None:
                self.stdout.write(f"  skipped '{title}' (run seed_data first)")
                continue
            if Conversation.objects.filter(listing=listing, buyer=buyer).exists():
                continue
            conversation = Conversation.objects.create(listing=listing, buyer=buyer, seller=listing.seller)
            start = timezone.now() - timedelta(hours=3)
            for i, (who, text) in enumerate(lines):
                sender = users[who]
                when = start + timedelta(minutes=25 * i)
                message = Message.objects.create(conversation=conversation, sender=sender, body=text)
                # spread the times out and mark everything read except the newest message
                Message.objects.filter(pk=message.pk).update(
                    created_at=when, read_at=None if i == len(lines) - 1 else when + timedelta(minutes=5)
                )
                Conversation.objects.filter(pk=conversation.pk).update(last_message_at=when)
            made += 1
        self.stdout.write(self.style.SUCCESS(
            f"Added {made} demo conversation(s). {Conversation.objects.count()} in total, {Message.objects.count()} messages."
        ))