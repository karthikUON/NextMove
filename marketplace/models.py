from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError



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
    ]

    CAMPUS_CHOICES = [
        ("callaghan", "Callaghan"),
        ("ourimbah", "Ourimbah"),
        ("sydney", "Sydney"),
        ("port_macquarie", "Port Macquarie"),
    ]

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="listings")
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    campus = models.CharField(max_length=20, choices=CAMPUS_CHOICES, default="callaghan")
    location = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
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
