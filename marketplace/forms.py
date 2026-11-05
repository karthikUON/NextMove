from django import forms
from .models import Listing
from dotenv import load_dotenv
import os

load_dotenv()

# Maximum photos per listing
MAX_IMAGES = int(os.getenv("MAX_IMAGES", "6"))

# Maximum file size per photo: defaults to 5 MB
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", str(5 * 1024 * 1024)))

# Allowed image formats
ALLOWED_FORMATS = {
    fmt.strip().upper()
    for fmt in os.getenv("ALLOWED_FORMATS", "JPEG,PNG,WEBP,GIF").split(",")
    if fmt.strip()
}

# setting flag for allowing multiple file inputs
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

# 
class MultipleImageField(forms.ImageField):
    """An ImageField that accepts several files and returns a list."""

    def __init__(self, *args, **kwargs):
        # sets the defaults and accepts multiple fileinputs, making sure only images accepts
        kwargs.setdefault("widget", MultipleFileInput(attrs={"accept": "image/*"}))
        # iniiatlizes the super calls
        super().__init__(*args, **kwargs)
    # should clean the image
    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            # cleans all the images on the list and returns cleaned ones
            return [single_clean(d, initial) for d in data if d]
        return [single_clean(data, initial)] if data else []


class ListingForm(forms.ModelForm): 
    images = MultipleImageField(required=False, label="Photos")

    class Meta:
        model = Listing
        fields = ["title", "description", "category", "price", "campus", "location", "is_tradeable", "trade_notes", "status"]
        labels = {"is_tradeable": "Open to trade", "trade_notes": "What would you trade for?"}
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, existing_count=0, **kwargs):
        super().__init__(*args, **kwargs)
        #  # photos the listing will keep 
        # stores the photo count    
        self.existing_count = existing_count
        # iterate through each field 
        for field in self.fields.values():
            widget = field.widget
            #  if it is tradeable
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"
            # if it is a category from select dropdown use the bootstrap classes
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            # Title, description, price, photos
            else:
                widget.attrs["class"] = "form-control"
        # Status dropdown: only when EDITING a listing that is Active or Sold, and only those two choices.
        # "On hold" and "Removed" are decided by staff, so a seller can never pick them (or un-hold a listing).
        if self.instance.pk and self.instance.status in ("active", "sold"):
            self.fields["status"].choices = [("active", "Active"), ("sold", "Sold")]
            self.fields["status"].widget.attrs["class"] = "form-select"
        else:
            del self.fields["status"]

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price < 0:
            raise forms.ValidationError("Price can't be negative.")
        return price

    def clean_images(self):
        files = self.cleaned_data["images"]
        if self.existing_count + len(files) > MAX_IMAGES:
            raise forms.ValidationError(f"A listing can have at most {MAX_IMAGES} photos.")
        for f in files:
            if f.size > MAX_IMAGE_BYTES:
                raise forms.ValidationError(f"{f.name} is larger than 5 MB.")
            if f.image.format not in ALLOWED_FORMATS:
                raise forms.ValidationError(f"{f.name}: only JPEG, PNG, WebP or GIF photos are allowed.")
        return files

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("is_tradeable"):
            cleaned["trade_notes"] = ""
        return cleaned