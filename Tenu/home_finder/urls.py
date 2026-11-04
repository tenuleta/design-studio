
from django.urls import path
from . import views   # Import all our view functions from views.py

urlpatterns = [

    # ── PUBLIC PAGES ──────────────────────────────────────────

    # Homepage — e.g. http://127.0.0.1:8000/
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),


    # Property listing page — e.g. http://127.0.0.1:8000/properties/
    path('properties/', views.property_list, name='property_list'),

    # Property detail page — e.g. http://127.0.0.1:8000/properties/3/
    # <int:id> is a dynamic part of the URL. Django captures the number
    # and passes it to the view as a parameter called "id".
    path('properties/<int:id>/', views.property_detail, name='property_detail'),


    # ── AUTHENTICATION PAGES ──────────────────────────────────

    # Login page — e.g. http://127.0.0.1:8000/login/
    path('login/', views.login_view, name='login'),

    # Register / Sign Up page
    path('register/', views.register_view, name='register'),

    # Logout — visiting this URL logs the user out and redirects home
    path('logout/', views.logout_view, name='logout'),


    # ── PROTECTED PAGES (login required) ─────────────────────

    # User dashboard — e.g. http://127.0.0.1:8000/dashboard/
    # (redirects to login page if user is not logged in)
    path('dashboard/', views.dashboard, name='dashboard'),

    # Add a new property listing — only for logged-in landlords
    path('add-property/', views.add_property, name='add_property'),

    # Landlord inquiry actions
    path('inquiries/<int:booking_id>/<str:status>/', views.update_inquiry_status, name='update_inquiry_status'),

]
