# accounts/admin.py
from django.contrib import admin
from .models import (
    User,
    UserProfile,
    Task,
    Organisation,
    OrganisationInvite,
    PublishingOutlet,
    Address,
)
    
class AddressInline(admin.StackedInline):
    model = Address
    
@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ['name', 'admin_email']
    search_fields = ['name', 'admin_email']
    inlines = [AddressInline]

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'address_type', 'organisation']
    list_filter = ['address_type', 'country']
    search_fields = ['line1', 'line2', 'line3', 'city', 'region', 'postal_code', 'country']

admin.site.register(User)
admin.site.register(UserProfile)
admin.site.register(Task)
admin.site.register(OrganisationInvite)
admin.site.register(PublishingOutlet)