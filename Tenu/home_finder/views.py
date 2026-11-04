from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date
from .models import User, Property, PropertyImage, Booking


def authenticate_by_username(username, password):
    """
    Authenticate using username only (case-insensitive fallback).
    """
    normalized = username.strip()
    user = authenticate(username=normalized, password=password)
    if user is not None:
        return user

    # Fallback for case-insensitive username input.
    user_obj = User.objects.filter(username__iexact=normalized).first()
    if user_obj is not None:
        return authenticate(username=user_obj.username, password=password)

    return None


def get_unavailable_booking(property_obj):
    """
    Return the most relevant confirmed booking to show availability status.
    Prefers current/upcoming bookings, otherwise falls back to the latest past one.
    """
    today = date.today()
    confirmed = [b for b in property_obj.bookings.all() if b.status == 'confirmed']
    if not confirmed:
        return None

    upcoming_or_current = [
        b for b in confirmed
        if (b.end_date or b.booking_date) >= today
    ]
    if upcoming_or_current:
        return sorted(upcoming_or_current, key=lambda b: b.booking_date)[0]

    return sorted(confirmed, key=lambda b: b.booking_date, reverse=True)[0]


def attach_availability_flags(properties):
    """
    Add template-friendly availability flags on each property object.
    """
    for prop in properties:
        booking = get_unavailable_booking(prop)
        prop.unavailable_booking = booking
        prop.is_unavailable = booking is not None
    return properties


# ─────────────────────────────────────────────
# 1. HOME PAGE
# ─────────────────────────────────────────────

def home(request):

    """
    Shows the homepage with a selection of featured properties.
    - Fetches the 6 most recently added available properties.
    - Passes them to the template so they can be displayed.
    """
    # Query the database: get available properties, newest first, limit to 6
    featured_properties = Property.objects.prefetch_related('bookings').order_by('-created_at')[:6]
    featured_properties = attach_availability_flags(featured_properties)

    # render() builds the HTML page using the template file and the data we pass
    return render(request, 'home.html', {
        'featured_properties': featured_properties
    })

def about(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == 'POST':
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('contact')
    return render(request, 'contact.html')



# ─────────────────────────────────────────────
# 2. PROPERTY LISTING PAGE
# ─────────────────────────────────────────────

def property_list(request):
    """
    Shows all available properties with optional filtering.
    Filters are read from the URL query string, e.g.:
      /properties/?type=apartment&min_price=1000
    """
    # Start with all properties so unavailable homes can be shown with status.
    properties = Property.objects.prefetch_related('bookings').all()

    # --- Apply Filters (if the user submitted the filter form) ---

    # Filter by property type (e.g. apartment, house)
    property_type = request.GET.get('type')   # request.GET reads the URL query parameters
    if property_type:
        properties = properties.filter(property_type=property_type)

    # Filter by minimum price
    min_price = request.GET.get('min_price')
    if min_price:
        # __gte means "greater than or equal to" in Django's query language
        properties = properties.filter(price_per_month__gte=min_price)

    # Filter by amenity
    amenity = request.GET.get('amenity')
    if amenity == 'pool':
        properties = properties.filter(has_pool=True)
    elif amenity == 'gym':
        properties = properties.filter(has_gym=True)
    elif amenity == 'parking':
        properties = properties.filter(has_parking=True)

    properties = attach_availability_flags(properties)

    return render(request, 'properties/property_list.html', {
        'properties': properties
    })


# ─────────────────────────────────────────────
# 3. PROPERTY DETAIL PAGE
# ─────────────────────────────────────────────

def property_detail(request, id):
    """
    Shows the full details of a single property.
    'id' comes from the URL, e.g. /properties/5/ → id=5
    """
    # get_object_or_404: tries to find the property by its ID.
    # If it doesn't exist, it automatically shows a "404 Not Found" page
    # instead of crashing the app.
    property = get_object_or_404(Property.objects.prefetch_related('bookings'), id=id)
    unavailable_booking = get_unavailable_booking(property)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in as a tenant to send an inquiry.')
            return redirect('login')

        if request.user.role != 'tenant':
            messages.error(request, 'Only tenant accounts can send inquiries.')
            return redirect('property_detail', id=id)

        if property.landlord_id == request.user.id:
            messages.error(request, 'You cannot send an inquiry to your own property.')
            return redirect('property_detail', id=id)

        start_date_raw = (request.POST.get('start_date') or '').strip()
        end_date_raw = (request.POST.get('end_date') or '').strip()
        message = (request.POST.get('message') or '').strip()

        if not start_date_raw or not end_date_raw:
            messages.error(request, 'Please provide both start date and end date.')
            return redirect('property_detail', id=id)

        try:
            start_date = date.fromisoformat(start_date_raw)
            end_date = date.fromisoformat(end_date_raw)
        except ValueError:
            messages.error(request, 'Please provide valid dates.')
            return redirect('property_detail', id=id)

        if end_date < start_date:
            messages.error(request, 'End date cannot be earlier than start date.')
            return redirect('property_detail', id=id)

        Booking.objects.create(
            tenant=request.user,
            property=property,
            booking_date=start_date,
            end_date=end_date,
            message=message,
        )
        messages.success(request, 'Inquiry sent successfully.')
        return redirect('property_detail', id=id)

    return render(request, 'properties/property_detail.html', {
        'property': property,
        'unavailable_booking': unavailable_booking,
    })


# ─────────────────────────────────────────────
# 4. LOGIN VIEW
# ─────────────────────────────────────────────

def login_view(request):
    """
    Handles the login page.
    - GET request  → just show the login form (someone navigated to /login/)
    - POST request → process the form (user submitted email & password)
    """
    if request.method == 'POST':
        # Read the submitted form fields
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'auth/login.html')

        # Authenticate using username only.
        user = authenticate_by_username(username, password)

        # Step 3: If we found and verified the user, log them in
        if user is not None:
            login(request, user)             # Creates a session (keeps them logged in)
            # Tenants go directly to property listings; landlords go to dashboard.
            if user.role == 'tenant':
                return redirect('property_list')
            return redirect('dashboard')
        else:
            # Show an error message if login failed
            messages.error(request, 'Invalid username or password. Please try again.')

    # If it's a GET request (or login failed), just show the form
    return render(request, 'auth/login.html')


# ─────────────────────────────────────────────
# 5. REGISTER VIEW
# ─────────────────────────────────────────────

def register_view(request):
    """
    Handles the registration page.
    - GET request  → show the registration form
    - POST request → create a new user account
    """
    if request.method == 'POST':
        # Read all the submitted form fields
        role             = request.POST.get('role')             # 'tenant' or 'landlord'
        fullname         = (request.POST.get('fullname') or '').strip()
        username         = (request.POST.get('username') or '').strip().lower()
        email            = (request.POST.get('email') or '').strip().lower()
        password         = request.POST.get('password') or ''
        confirm_password = request.POST.get('confirm_password') or ''

        # --- Validation Checks ---

        # Check 1: Do the two passwords match?
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register.html')

        if not username:
            messages.error(request, 'Please choose a username.')
            return render(request, 'auth/register.html')

        if not email:
            messages.error(request, 'Please enter a valid email.')
            return render(request, 'auth/register.html')

        # Check 2: Is this username already registered?
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'This username is already taken.')
            return render(request, 'auth/register.html')

        # Check 3: Is this email already registered?
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'auth/register.html')

        # --- Create the User ---
        # create_user() is a built-in Django method that hashes (encrypts)
        # the password before saving it — never store plain-text passwords!
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.first_name = fullname   # Store their full name
        user.role = role             # Set their role (tenant or landlord)
        user.save()                  # Save the changes to the database

        # Redirect to login page after successful registration.
        messages.success(request, 'Account created successfully. Please log in with your username.')
        return redirect('login')

    # Show the registration form (GET request)
    return render(request, 'auth/register.html')


# ─────────────────────────────────────────────
# 6. LOGOUT VIEW
# ─────────────────────────────────────────────

def logout_view(request):
    """
    Logs the user out by clearing their session,
    then redirects them to the homepage.
    """
    logout(request)
    return redirect('home')


# ─────────────────────────────────────────────
# 7. DASHBOARD VIEW
# ─────────────────────────────────────────────

# @login_required → This is a "decorator". It protects this view so that
# only logged-in users can access it. If someone visits /dashboard/ without
# being logged in, they are redirected to the login page automatically.
@login_required
def dashboard(request):
    """
    The user's personal dashboard.
    - Landlords see their listed properties.
    - Tenants see a welcome screen with a browse link.
    """
    user    = request.user  # request.user is the currently logged-in user

    # Tenants do not use dashboard; send them to property listings.
    if user.role == 'tenant':
        return redirect('property_list')

    context = {}            # A dictionary of data we'll send to the template

    if user.role == 'landlord':
        # Get all properties that belong to this landlord
        properties = Property.objects.filter(landlord=user)
        context['properties'] = properties
        context['inquiries'] = Booking.objects.filter(
            property__landlord=user
        ).select_related('tenant', 'property').order_by('-created_at')

    # Render the dashboard template with the context data
    return render(request, 'dashboard/index.html', context)


@login_required
def update_inquiry_status(request, booking_id, status):
    """
    Landlord can accept (confirmed) or reject an inquiry.
    """
    if request.method != 'POST':
        return redirect('dashboard')

    if request.user.role != 'landlord':
        messages.error(request, 'Only landlords can update inquiry status.')
        return redirect('property_list')

    if status not in ('confirmed', 'rejected'):
        messages.error(request, 'Invalid status update.')
        return redirect('dashboard')

    inquiry = get_object_or_404(
        Booking,
        id=booking_id,
        property__landlord=request.user
    )

    if inquiry.status != 'pending':
        messages.error(request, 'This inquiry has already been processed.')
        return redirect('dashboard')

    inquiry.status = status
    inquiry.save(update_fields=['status'])

    property_obj = inquiry.property
    has_confirmed_booking = Booking.objects.filter(
        property=property_obj,
        status='confirmed'
    ).exists()
    property_obj.is_available = not has_confirmed_booking
    property_obj.save(update_fields=['is_available'])

    if status == 'confirmed':
        messages.success(request, 'Inquiry accepted successfully.')
    else:
        messages.success(request, 'Inquiry rejected successfully.')

    return redirect('dashboard')


# ─────────────────────────────────────────────
# 8. ADD PROPERTY VIEW
# ─────────────────────────────────────────────

@login_required
def add_property(request):
    """
    Allows a landlord to list a new rental property.
    - GET request  → show the "Add Property" form
    - POST request → save the new property to the database
    """
    if request.method == 'POST':

        # --- Read All Form Fields ---
        title       = request.POST.get('title')
        price       = request.POST.get('price')
        category    = request.POST.get('category')    # e.g. 'apartment'
        description = request.POST.get('description')
        address     = request.POST.get('address')
        city        = request.POST.get('city')

        # --- Read Amenity Checkboxes ---
        # Checkboxes send 'on' when checked, or nothing when unchecked.
        # So we check if the value is 'on' and convert to True/False.
        has_ac      = request.POST.get('has_ac')      == 'on'
        has_pool    = request.POST.get('has_pool')    == 'on'
        has_gym     = request.POST.get('has_gym')     == 'on'
        has_parking = request.POST.get('has_parking') == 'on'

        # --- Save the Property to the Database ---
        # Property.objects.create() creates and saves a new row in one step.
        property = Property.objects.create(
            landlord        = request.user,  # The logged-in user is the landlord
            title           = title,
            price_per_month = price,
            property_type   = category,
            description     = description,
            location        = address,
            city            = city,
            has_ac          = has_ac,
            has_pool        = has_pool,
            has_gym         = has_gym,
            has_parking     = has_parking,
        )

        # --- Handle Uploaded Images ---
        # request.FILES contains uploaded files.
        # getlist('images') gets all files from the multi-file input named 'images'.
        images = request.FILES.getlist('images')
        for image in images:
            # Create a PropertyImage record linking each file to the property
            PropertyImage.objects.create(property=property, image=image)

        # Show a success message and redirect back to the listing form
        messages.success(request, f'"{title}" has been listed successfully!')
        return redirect('add_property')

    # Show the add-property form (GET request)
    return render(request, 'properties/property_form.html')
