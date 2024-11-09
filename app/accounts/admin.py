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
    AddressConfiguration,
    AddressFieldConfiguration
)

class AddressFieldConfigurationInline(admin.TabularInline):
    model = AddressFieldConfiguration
    extra = 1

@admin.register(AddressConfiguration)
class AddressConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default']
    inlines = [AddressFieldConfigurationInline]

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'configuration']
    list_filter = ['configuration']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            enabled_fields = obj.configuration.fields.filter(
                enabled=True
            ).values_list('name', flat=True)
            for field_name, field in form.base_fields.items():
                if field_name not in enabled_fields:
                    field.widget.attrs['disabled'] = True
        return form

class AddressInline(admin.StackedInline):
    model = Address

@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    inlines = [AddressInline]

admin.site.register(User)
admin.site.register(UserProfile)
admin.site.register(Task)
admin.site.register(OrganisationInvite)
admin.site.register(PublishingOutlet)