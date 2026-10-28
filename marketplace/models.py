from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Listing(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("sold", "Sold"),
        ("removed", "Removed"),
        ("on_hold", "On hold"),   # Week 7: auto-set when a banned word is found in listing
    ]
#available campus filters   
    CAMPUS_CHOICES = [
        ("callaghan", "Callaghan"),
        ("ourimbah", "Ourimbah"),
        ("sydney", "Sydney"),
        ("port_macquarie", "Port Macquarie"),
    ]

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings", null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="listings")
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    campus = models.CharField(max_length=20, choices=CAMPUS_CHOICES, default="callaghan")
    location = models.CharField(max_length=200, blank=True)
    is_tradeable = models.BooleanField(default=False)
    trade_notes = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    # Week 7: True when the keyword scan put this listing on hold
    auto_flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
            models.Index(fields=["campus"]),
        ]

    def __str__(self):
        return self.title

    # Week 7: look at the title + description for any banned word.
    def scan_for_blocked_keywords(self):
        text = f"{self.title} {self.description}".lower()
        for kw in ModerationKeyword.objects.all():
            if kw.keyword.lower() in text:
                return kw
        return None

    # Week 7: run the scan automatically whenever an ACTIVE listing is saved.
    def save(self, *args, **kwargs):
        matched = None
        if self.status == "active":
            matched = self.scan_for_blocked_keywords()
            if matched:
                self.status = "on_hold"
                self.auto_flagged = True
        super().save(*args, **kwargs)
        if matched and not self.flags.filter(keyword=matched).exists():
            ListingFlag.objects.create(listing=self, keyword=matched, reason=matched.keyword)

    @property
    def primary_image(self):
        return self.images.filter(is_deleted=False).first()


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="listings/%Y/%m/")
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "id"]

    def __str__(self):
        return f"Photo {self.pk} for listing {self.listing_id}"



# Week 7: Moderation & Favorites


class ModerationKeyword(models.Model):
    CATEGORY_CHOICES = [
        ("adult", "Adult"),
        ("illegal", "Illegal"),
        ("exploitation", "Exploitation"),
        ("other", "Other"),
    ]
    keyword = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="other")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.keyword


class ListingFlag(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="flags")
    keyword = models.ForeignKey(ModerationKeyword, on_delete=models.CASCADE, related_name="listing_flags")
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Flag on listing {self.listing_id}: {self.reason}"


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "listing")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} saved {self.listing}"

       #note: #unique_together = ("user", "listing") tells the database: the combination of (user + listing) must be uniquecd C:\Project\nextmove