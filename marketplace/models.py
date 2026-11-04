from django.conf import settings
from django.db import models
import re

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
    # added by chinni for the class using static methods for description
    # remember the title/description as loaded, so save() can tell whether the text was edited
    @classmethod
    def from_db(cls, db, field_names, values, *args, **kwargs):
        # *args/**kwargs: newer Django versions add arguments (e.g. fetch_mode in 6.1)
        instance = super().from_db(db, field_names, values, *args, **kwargs)
        if "title" in field_names and "description" in field_names:
            instance._loaded_text = (instance.title, instance.description)
        else:
            instance._loaded_text = None
        return instance

    # Week 7: every blocked keyword found in the title or description.
    # Whole words/phrases only, any case, extra spaces ignored ("ass" must not match "class")
    # This code comes from  chinni .
    def scan_for_blocked_keywords(self):
        text = " ".join(f"{self.title} {self.description}".lower().split())
        found = []
        for kw in ModerationKeyword.objects.all():
            phrase = " ".join(kw.keyword.lower().split())
            if re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text):
                found.append(kw)
        return found
    # save the fields and will fo it from them - @chinni
    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        touches_text = update_fields is None or bool({"title", "description"} & set(update_fields))
        text_changed = self._state.adding or getattr(self, "_loaded_text", None) != (self.title, self.description)

        # Scan only when the text is new or was edited. A save that doesn't change the text
        # (mark as sold, a price edit, staff approving a held listing) must NOT re-scan,
        # or an approval would be undone straight away.
        matched = []
        if touches_text and text_changed and self.status in ("active", "sold"):
            matched = self.scan_for_blocked_keywords()
        if matched:
            self.status = "on_hold"
            self.auto_flagged = True
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"status", "auto_flagged"}
        elif self.status != "on_hold":
            self.auto_flagged = False   # an approved listing is no longer "flagged"

        super().save(*args, **kwargs)

        for kw in matched:
            if not self.flags.filter(keyword=kw).exists():
                ListingFlag.objects.create(listing=self, keyword=kw, reason=kw.keyword)
        self._loaded_text = (self.title, self.description)

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