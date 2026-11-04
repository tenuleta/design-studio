# ============================================================
# models.py — The "Blueprint" of our Database
# ============================================================
# In Django, a "Model" is a Python class that represents a
# table in the database. Each attribute of the class becomes
# a column in that table.
#
# Think of it like this:
#   - Model  = a spreadsheet template
#   - Field  = a column header (e.g. "Title", "Price")
#   - Object = one row of data (e.g. one property listing)
# ============================================================

from django.db import models

# We import Django's built-in User system and extend it
# so we can add our own custom fields (like "role").
from django.contrib.auth.models import AbstractUser


# ─────────────────────────────────────────────
# 1. USER MODEL
# ─────────────────────────────────────────────
# Django already has a built-in User model with fields like
# username, email, and password. We extend it (AbstractUser)
# to add our own "role" field so we know if someone is a
# Tenant or a Landlord.

class User(AbstractUser):

    # ROLE_CHOICES defines the allowed values for the "role" field.
    # Format: (value_stored_in_db, human_readable_label)
    ROLE_CHOICES = (
        ('tenant',   'Tenant'),    # Someone looking to rent
        ('landlord', 'Landlord'),  # Someone listing a property
    )

    # The "role" field stores whether this user is a tenant or landlord.
    # max_length=20  → the text can be at most 20 characters long
    # choices=...    → only the values above are allowed
    # default='tenant' → if no role is given, assume they are a tenant
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='tenant'
    )

    # Optional phone number field.
    # blank=True → the form won't require it
    # null=True  → it's okay to save NULL in the database
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    # __str__ controls what text appears when we print/display a User object.
    # For example, in the admin panel it will show the username.
    def __str__(self):
        return self.username


# ─────────────────────────────────────────────
# 2. PROPERTY MODEL
# ─────────────────────────────────────────────
# This stores all the information about a rental property
# (apartment, house, villa, etc.).

class Property(models.Model):

    # These are the allowed property types.
    PROPERTY_TYPES = (
        ('apartment', 'Apartment'),
        ('house',     'House'),
        ('villa',     'Villa'),
        ('studio',    'Studio'),
    )

    # ForeignKey creates a link (relationship) between two tables.
    # Here, every Property must belong to ONE User (the landlord).
    # on_delete=models.CASCADE → if the landlord account is deleted,
    #   all their properties are deleted too.
    # related_name='properties' → lets us write landlord.properties.all()
    #   to get all properties belonging to a landlord.
    landlord = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='properties'
    )

    # Basic text fields
    title       = models.CharField(max_length=255)   # Short text, e.g. "Cozy Studio in Bole"
    description = models.TextField()                  # Long text, e.g. a paragraph about the property
    location    = models.CharField(max_length=255)    # Full street address
    city        = models.CharField(max_length=100)    # City name
    zip_code    = models.CharField(max_length=20, blank=True, null=True)

    # Property category (apartment, house, etc.)
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPES)

    # Price: DecimalField is used for money to avoid rounding errors.
    # max_digits=10    → up to 10 digits in total (e.g. 99,999,999.99)
    # decimal_places=2 → 2 digits after the decimal point
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2)

    # Property specifications
    bedrooms  = models.IntegerField(default=1)         # Whole number, e.g. 2 bedrooms
    bathrooms = models.FloatField(default=1.0)          # Can be e.g. 1.5 bathrooms
    size_sqft = models.IntegerField(null=True, blank=True)  # Optional square footage

    # Amenity flags — BooleanField stores True or False
    has_pool    = models.BooleanField(default=False)
    has_gym     = models.BooleanField(default=False)
    has_parking = models.BooleanField(default=False)
    has_ac      = models.BooleanField(default=False)

    # Status and timestamps
    is_available = models.BooleanField(default=True)      # Is the property available to rent?
    created_at   = models.DateTimeField(auto_now_add=True) # Set automatically when created
    updated_at   = models.DateTimeField(auto_now=True)     # Updated automatically on every save

    def __str__(self):
        # Example: "Cozy Studio (Addis Ababa)"
        return f"{self.title} ({self.city})"

    def get_main_image(self):
        """Returns the URL of the first uploaded image, or None if no image exists."""
        if self.images.exists():
            return self.images.first().image.url
        return None


# ─────────────────────────────────────────────
# 3. PROPERTY IMAGE MODEL
# ─────────────────────────────────────────────
# A property can have multiple photos. This model stores
# each photo and links it back to the property it belongs to.

class PropertyImage(models.Model):

    # Links each image to a specific property.
    # related_name='images' → lets us write property.images.all()
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='images'
    )

    # ImageField stores the photo on disk and the file path in the database.
    # upload_to='property_images/' → files are saved inside the "media/property_images/" folder
    image = models.ImageField(upload_to='property_images/')

    def __str__(self):
        return f"Image for {self.property.title}"


# ─────────────────────────────────────────────
# 4. BOOKING MODEL
# ─────────────────────────────────────────────
# When a tenant is interested in a property, they submit a
# "booking request". This model stores those requests.

class Booking(models.Model):

    # Possible statuses of a booking request
    STATUS_CHOICES = (
        ('pending',   'Pending'),    # Waiting for landlord response
        ('confirmed', 'Confirmed'),  # Landlord accepted
        ('rejected',  'Rejected'),   # Landlord rejected
        ('cancelled', 'Cancelled'),  # Tenant cancelled
    )

    # The tenant who made the request
    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    # The property being requested
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    message      = models.TextField(blank=True)   # Optional message from the tenant
    booking_date = models.DateField()              # Requested start date
    end_date     = models.DateField(null=True, blank=True)  # Requested end date
    status       = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking: {self.property.title} by {self.tenant.username}"


# ─────────────────────────────────────────────
# 5. REVIEW MODEL
# ─────────────────────────────────────────────
# After staying at a property, tenants can leave a star
# rating and a written comment.

class Review(models.Model):

    # Which property is being reviewed
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    # Who wrote the review
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Rating from 1 to 5 stars
    # We use a list comprehension to create: [(1,1), (2,2), (3,3), (4,4), (5,5)]
    rating  = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rating}★ review for {self.property.title}"
