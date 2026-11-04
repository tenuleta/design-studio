from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Property, PropertyImage, Booking, Review

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'landlord', 'city', 'price_per_month', 'is_available')
    list_filter = ('is_available', 'city', 'property_type')
    search_fields = ('title', 'city', 'description')
    inlines = [PropertyImageInline]

class BookingAdmin(admin.ModelAdmin):
    list_display = ('property', 'tenant', 'booking_date', 'status')
    list_filter = ('status', 'booking_date')

admin.site.register(User, UserAdmin)
admin.site.register(Property, PropertyAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Review)
