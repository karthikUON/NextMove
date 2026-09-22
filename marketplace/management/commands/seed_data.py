from django.core.management.base import BaseCommand
from marketplace.models import Category, Listing

CATEGORIES = [
    ("Furniture", "furniture"), ("Electronics", "electronics"),
    ("Cars & Transport", "cars-transport"), ("Accommodation", "accommodation"),
    ("Textbooks", "textbooks"), ("Jobs", "jobs"), ("Services", "services"),
]

CAMPUSES = ["callaghan", "ourimbah", "sydney", "port_macquarie"]

# (category_slug, title, description, price, location)
LISTINGS = [
    ("furniture", "IKEA study desk", "White IKEA desk, 120x60cm, great for a dorm room. Minor scuff on one leg.", 45, "Callaghan"),
    ("furniture", "Queen mattress, 1 year old", "Clean, no stains, from a smoke-free home. Selling as I'm moving.", 120, "Jesmond"),
    ("furniture", "5-tier bookshelf", "Sturdy bookshelf, holds a full semester of textbooks easily.", 20, "Broadmeadow"),
    ("electronics", "Dell laptop - i5, 8GB RAM", "Two years old, good battery, comes with charger. Great for coursework.", 320, "Callaghan"),
    ("electronics", "Noise-cancelling headphones", "Sony WH-1000XM3, barely used, box included.", 150, "Jesmond"),
    ("electronics", "24 inch monitor", "Full HD, no dead pixels, HDMI cable included. Great for a dual-screen setup.", 80, "Callaghan"),
    ("cars-transport", "2014 Toyota Corolla", "Reliable car, recent service, RWC included. Finishing my degree, must sell.", 8500, "Newcastle"),
    ("cars-transport", "Electric scooter", "Barely used, great for getting around campus. Battery holds charge well.", 210, "Callaghan"),
    ("cars-transport", "Mountain bike - medium frame", "Recently serviced, new tyres. Perfect for the campus bike paths.", 180, "Ourimbah"),
    ("accommodation", "Room near campus", "3-bed share house, 10 min walk to campus. Bills included, available now.", 220, "Callaghan"),
    ("accommodation", "Studio sublet - 3 months", "Subletting while on exchange. Fully furnished, close to bus stop.", 260, "Sydney"),
    ("textbooks", "Data Structures & Algorithms", "Used for COMP2230, good condition, minor highlighting.", 40, "Callaghan"),
    ("textbooks", "Financial Accounting 12th ed.", "Like new, barely opened. Textbook for ACCT1010.", 55, "Ourimbah"),
    ("jobs", "Tutor needed - first year calculus", "Weekly calculus help wanted, casual rate, flexible timing.", 0, "Callaghan"),
    ("services", "Airport pickup/drop-off", "Reliable airport transfers for students, reasonable rates.", 25, "Newcastle"),
    ("services", "Resume review & career advice", "Final-year student offering resume and cover letter reviews.", 15, "Sydney"),
]


class Command(BaseCommand):
    help = "Seeds the database with sample categories and listings across all campuses"

    def handle(self, *args, **options):
        for name, slug in CATEGORIES:
            Category.objects.get_or_create(slug=slug, defaults={"name": name})
        categories = {c.slug: c for c in Category.objects.all()}

        for i, (cat_slug, title, desc, price, location) in enumerate(LISTINGS):
            Listing.objects.get_or_create(
                title=title,
                defaults=dict(
                    category=categories[cat_slug], description=desc, price=price,
                    location=location, campus=CAMPUSES[i % len(CAMPUSES)],
                ),
            )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {Category.objects.count()} categories and {Listing.objects.count()} listings."
        ))
