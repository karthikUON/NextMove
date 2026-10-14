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
        # added the removed which is for sold delete flag
        ("removed", "Removed"),
    ]

    CAMPUS_CHOICES = [
        ("callaghan", "Callaghan"),
        ("ourimbah", "Ourimbah"),
        ("sydney", "Sydney"),
        ("port_macquarie", "Port Macquarie"),
    ]

    # null True only so listings that existed before this field was added can migrate;
    # every listing created through the post form gets a seller.
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings", null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="listings")
    title = models.CharField(max_length=200)
    # description of the field can be added
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    campus = models.CharField(max_length=20, choices=CAMPUS_CHOICES, default="callaghan")
    location = models.CharField(max_length=200, blank=True)
    # also added is_tradeable to check the flag if any trades exist
    is_tradeable = models.BooleanField(default=False)
    # added the notes here so it context near from the trade can be added
    trade_notes = models.CharField(max_length=300, blank=True)
    # status of the listing/ad
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    # when it is created for the timestamp
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

    # return the first image for the listing, so that it acts as cover photo 
    @property
    def primary_image(self):
        # images are ordered cover-first (see ListingImage.Meta), so first() is the cover photo
        return self.images.filter(is_deleted=False).first()

# Images class
class ListingImage(models.Model):
    # listing id
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="images")
    # image 
    image = models.ImageField(upload_to="listings/%Y/%m/")
    # for cover pic
    is_primary = models.BooleanField(default=False)
    # timestamp for the uploaded at
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # soft delete flag for images deletion
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "id"]

    def __str__(self):
        return f"Photo {self.pk} for listing {self.listing_id}"