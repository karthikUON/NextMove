from datetime import timedelta
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

from marketplace.models import Category, Listing, ListingImage

User = get_user_model()
import textwrap

# Every demo account shares this password. Dev/demo data only: never run this seed on a real deployment.
DEMO_PASSWORD = "NextMove2026!"

CATEGORIES = [
    ("Furniture", "furniture"),
    ("Electronics", "electronics"),
    ("Cars & Transport", "cars-transport"),
    ("Accommodation", "accommodation"),
    ("Textbooks", "textbooks"),
    ("Jobs", "jobs"),
    ("Services", "services"),
]

# verified, active students who own the demo listings
SELLERS = {
    "aarav": ("aarav.mehta@uon.edu.au", "Aarav"),
    "priya": ("priya.nair@uon.edu.au", "Priya"),
    "liam": ("liam.oconnor@uon.edu.au", "Liam"),
    "sara": ("sara.khan@uon.edu.au", "Sara"),
    "tom": ("tom.nguyen@uon.edu.au", "Tom"),
}

# Colour used for the generated demo photos, per category
PHOTO_COLOURS = {
    "furniture": (176, 137, 104),
    "electronics": (70, 110, 160),
    "cars-transport": (90, 120, 100),
    "accommodation": (160, 100, 120),
    "textbooks": (130, 90, 160),
    "jobs": (200, 150, 60),
    "services": (60, 140, 140),
}

# photos = how many photos to generate (0 = no photo, shows the placeholder)
# trade  = trade note (makes the listing "open to trade")
# status = "sold" / "removed" (default "active")
LISTINGS = [
    dict(
        cat="furniture",
        title="IKEA study desk",
        price=45,
        campus="callaghan",
        loc="Callaghan",
        seller="aarav",
        photos=2,
        desc="White IKEA desk, 120x60cm, great for a dorm room. Minor scuff on one leg.",
    ),
    dict(
        cat="furniture",
        title="Queen mattress, 1 year old",
        price=120,
        campus="callaghan",
        loc="Jesmond",
        seller="priya",
        photos=1,
        desc="Clean, no stains, from a smoke-free home. Selling as I'm moving.",
    ),
    dict(
        cat="furniture",
        title="5-tier bookshelf",
        price=20,
        campus="callaghan",
        loc="Broadmeadow",
        seller="liam",
        photos=2,
        trade="A desk chair in good condition",
        desc="Sturdy bookshelf, holds a full semester of textbooks easily.",
    ),
    dict(
        cat="electronics",
        title="Dell laptop - i5, 8GB RAM",
        price=320,
        campus="callaghan",
        loc="Callaghan",
        seller="sara",
        photos=3,
        deleted_photo=True,  # also gets one soft-deleted photo, to test that it stays hidden
        desc="Two years old, good battery, comes with charger. Great for coursework.",
    ),
    dict(
        cat="electronics",
        title="Noise-cancelling headphones",
        price=150,
        campus="callaghan",
        loc="Jesmond",
        seller="tom",
        photos=1,
        trade="A mechanical keyboard or a decent monitor",
        desc="Sony WH-1000XM3, barely used, box included.",
    ),
    dict(
        cat="electronics",
        title="24 inch monitor",
        price=80,
        campus="callaghan",
        loc="Callaghan",
        seller="aarav",
        photos=1,
        status="sold",
        desc="Full HD, no dead pixels, HDMI cable included. Great for a dual-screen setup.",
    ),
    dict(
        cat="cars-transport",
        title="2014 Toyota Corolla",
        price=8500,
        campus="callaghan",
        loc="Newcastle",
        seller="liam",
        photos=3,
        desc="Reliable car, recent service, RWC included. Finishing my degree, must sell.",
    ),
    dict(
        cat="cars-transport",
        title="Electric scooter",
        price=210,
        campus="callaghan",
        loc="Callaghan",
        seller="priya",
        photos=2,
        trade="Would swap for a good road bike",
        desc="Barely used, great for getting around campus. Battery holds charge well.",
    ),
    dict(
        cat="cars-transport",
        title="Mountain bike - medium frame",
        price=180,
        campus="ourimbah",
        loc="Ourimbah",
        seller="sara",
        photos=2,
        desc="Recently serviced, new tyres. Perfect for the campus bike paths.",
    ),
    dict(
        cat="accommodation",
        title="Room near campus",
        price=220,
        campus="callaghan",
        loc="Callaghan",
        seller="tom",
        photos=3,
        desc="3-bed share house, 10 min walk to campus. Bills included, available now.",
    ),
    dict(
        cat="accommodation",
        title="Studio sublet - 3 months",
        price=260,
        campus="sydney",
        loc="Sydney",
        seller="priya",
        photos=2,
        desc="Subletting while on exchange. Fully furnished, close to bus stop.",
    ),
    dict(
        cat="textbooks",
        title="Data Structures & Algorithms",
        price=40,
        campus="callaghan",
        loc="Callaghan",
        seller="aarav",
        photos=1,
        trade="Swap for any 3000-level COMP textbook",
        desc="Used for COMP2230, good condition, minor highlighting.",
    ),
    dict(
        cat="textbooks",
        title="Financial Accounting 12th ed.",
        price=55,
        campus="ourimbah",
        loc="Ourimbah",
        seller="liam",
        photos=1,
        status="sold",
        desc="Like new, barely opened. Textbook for ACCT1010.",
    ),
    dict(
        cat="jobs",
        title="Tutor needed - first year calculus",
        price=0,
        campus="callaghan",
        loc="Callaghan",
        seller="sara",
        photos=0,
        desc="Weekly calculus help wanted, casual rate, flexible timing.",
    ),
    dict(
        cat="services",
        title="Airport pickup/drop-off",
        price=25,
        campus="callaghan",
        loc="Newcastle",
        seller="tom",
        photos=0,
        desc="Reliable airport transfers for students, reasonable rates.",
    ),
    dict(
        cat="services",
        title="Resume review & career advice",
        price=15,
        campus="sydney",
        loc="Sydney",
        seller="priya",
        photos=0,
        desc="Final-year student offering resume and cover letter reviews.",
    ),
    dict(
        cat="accommodation",
        title="Room in Port Macquarie share house",
        price=190,
        campus="port_macquarie",
        loc="Port Macquarie",
        seller="sara",
        photos=2,
        desc="Furnished room, 15 min from the campus, shared kitchen and a big backyard.",
    ),
    dict(
        cat="textbooks",
        title="Nursing clinical skills textbook set",
        price=90,
        campus="port_macquarie",
        loc="Port Macquarie",
        seller="liam",
        photos=1,
        trade="Would swap for a good stethoscope",
        desc="Three-book set used across first and second year. Some highlighting.",
    ),
    dict(
        cat="electronics",
        title="Bar fridge",
        price=60,
        campus="port_macquarie",
        loc="Port Macquarie",
        seller="tom",
        photos=1,
        desc="Small bar fridge, works perfectly. Ideal for a student room.",
    ),
    dict(
        cat="furniture",
        title="Desk lamp and chair set",
        price=35,
        campus="sydney",
        loc="Sydney CBD",
        seller="aarav",
        photos=2,
        desc="Adjustable desk lamp plus a comfortable chair. Pickup near Town Hall.",
    ),
    dict(
        cat="services",
        title="Maths & stats tutoring",
        price=30,
        campus="ourimbah",
        loc="Ourimbah",
        seller="priya",
        photos=0,
        desc="Postgrad offering tutoring for first and second year maths and stats.",
    ),
    dict(
        cat="furniture",
        title="Old couch (deleted by seller)",
        price=50,
        campus="callaghan",
        loc="Callaghan",
        seller="aarav",
        photos=1,
        status="removed",  # soft-deleted: should be hidden everywhere except from its owner
        desc="Listing the seller deleted. Used to test that removed listings stay hidden.",
    ),
]


def make_photo(title, slug, n):
    """A plain coloured 640x440 JPEG with the listing title in the middle (demo photo).

    The text is centred, inside a full-width band, because cards crop photos from the
    centre (object-fit: cover): anything near the left or right edge gets cut off.
    """
    base = PHOTO_COLOURS.get(slug, (100, 100, 100))
    colour = tuple(min(255, c + 22 * n) for c in base)
    img = Image.new("RGB", (640, 440), colour)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 120, 640, 320], fill=tuple(max(0, c - 60) for c in colour))
    lines = "\n".join(textwrap.wrap(title, 16)[:3])
    draw.multiline_text(
        (320, 200),
        lines,
        fill="white",
        font=ImageFont.load_default(size=34),
        anchor="mm",
        align="center",
        spacing=6,
    )
    draw.text(
        (320, 298),
        f"Demo photo {n + 1}",
        fill="white",
        font=ImageFont.load_default(size=20),
        anchor="mm",
    )
    buf = BytesIO()
    img.save(buf, "JPEG", quality=85)
    return ContentFile(buf.getvalue())


def add_photos(listing, slug, count, deleted_photo=False):
    stem = slugify(listing.title)[:40]
    for n in range(count):
        photo = ListingImage(listing=listing, is_primary=(n == 0))
        photo.image.save(
            f"{stem}-{n + 1}.jpg", make_photo(listing.title, slug, n), save=False
        )
        photo.save()
    if deleted_photo:
        gone = ListingImage(listing=listing, is_primary=False, is_deleted=True)
        gone.image.save(
            f"{stem}-deleted.jpg", make_photo(listing.title, slug, count), save=False
        )
        gone.save()


def get_or_make_user(email, first_name, **extra):
    user = User.objects.filter(email=email).first()
    if user:
        return user
    return User.objects.create_user(
        username=email.split("@")[0],
        email=email,
        password=DEMO_PASSWORD,
        first_name=first_name,
        **extra,
    )


class Command(BaseCommand):
    help = "Seeds sample users, categories, listings (with sellers, trade info, statuses and photos) across all campuses"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-photos",
            action="store_true",
            help="Delete and regenerate the photos of the seeded demo listings (other listings are untouched)",
        )

    def handle(self, *args, **options):
        for name, slug in CATEGORIES:
            Category.objects.get_or_create(slug=slug, defaults={"name": name})
        categories = {c.slug: c for c in Category.objects.all()}

        sellers = {
            key: get_or_make_user(email, first, is_verified=True)
            for key, (email, first) in SELLERS.items()
        }

        # Extra accounts for testing the Week 4 login rules
        get_or_make_user(
            "mei.lin@uon.edu.au", "Mei", is_verified=False, otp_code="123456"
        )  # never expires (no timestamp)
        get_or_make_user(
            "sam.wilson@uon.edu.au", "Sam", is_verified=True, is_active=False
        )

        for i, spec in enumerate(LISTINGS):
            seller = sellers[spec["seller"]]
            trade = spec.get("trade", "")
            fields = dict(
                category=categories[spec["cat"]],
                description=spec["desc"],
                price=spec["price"],
                campus=spec["campus"],
                location=spec["loc"],
                seller=seller,
                is_tradeable=bool(trade),
                trade_notes=trade,
                status=spec.get("status", "active"),
            )
            listing = Listing.objects.filter(title=spec["title"]).first()
            if listing is None:
                listing = Listing.objects.create(title=spec["title"], **fields)
                # spread the posting dates so "newest first" looks natural
                Listing.objects.filter(pk=listing.pk).update(
                    created_at=timezone.now() - timedelta(days=(i * 2) % 28, hours=i)
                )
            elif listing.seller_id is None:
                # a row from the older seed (made before sellers existed): bring it up to date
                for field, value in fields.items():
                    setattr(listing, field, value)
                listing.save()
                
            if options.get("reset_photos"):
                for old in listing.images.all():
                    old.image.delete(save=False)  # remove the file too
                    old.delete()

            if not listing.images.exists():
                add_photos(
                    listing,
                    spec["cat"],
                    spec["photos"],
                    spec.get("deleted_photo", False),
                )

        live = Listing.objects.filter(status="active").count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Category.objects.count()} categories, {User.objects.count()} users, "
                f"{Listing.objects.count()} listings ({live} active), {ListingImage.objects.count()} photos."
            )
        )
        self.stdout.write(f"Demo logins (password for all: {DEMO_PASSWORD}):")
        for email, _ in SELLERS.values():
            self.stdout.write(f"  {email}")
        self.stdout.write(
            "  mei.lin@uon.edu.au   (unverified; verify at /accounts/verify-email/?email=mei.lin@uon.edu.au with code 123456)"
        )
        self.stdout.write(
            "  sam.wilson@uon.edu.au (disabled account: login should be refused)"
        )
