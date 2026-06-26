from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models


class Property(models.Model):
    LISTING_TYPES = [
        ("sale", "For Sale"),
        ("rent", "For Rent"),
    ]

    listing_type = models.CharField(max_length=10, choices=LISTING_TYPES, default="sale")
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    image = models.FileField(
        upload_to="property_images/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp", "gif"])],
    )
    brochure = models.FileField(
        upload_to="property_brochures/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["pdf"])],
    )
    listed_date = models.DateTimeField(auto_now_add=True)
    sold = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        status = " (Sold)" if self.sold else ""
        return f"{self.title}{status}"


class Inquiry(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="inquiries")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="property_inquiries")
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Inquiry for {self.property.title} from {self.name}"


class Favorite(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="favorites")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_properties")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["property", "user"], name="unique_property_favorite")
        ]

    def __str__(self):
        return f"{self.user.username} saved {self.property.title}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} · {self.subject}"
