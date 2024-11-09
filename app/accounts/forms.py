from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import (
    User, 
    PublishingOutlet, 
    Organisation, 
    OrganisationInvite, 
    Address, 
    AddressConfiguration
)

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['line1', 'line2', 'line3', 'city', 'region', 'postal_code', 'country']

    def __init__(self, *args, **kwargs):
        self.configuration = kwargs.pop('configuration', None)
        super().__init__(*args, **kwargs)
        if self.configuration:
            enabled_fields = self.configuration.fields.filter(enabled=True)
            for field in enabled_fields:
                self.fields[field.name].label = field.label
                self.fields[field.name].required = field.required
    
    def save(self, commit=True):
        address = super().save(commit=False)
        if self.configuration:
            address.configuration = self.configuration
        if commit:
            address.save()
        return address

class OrganisationForm(forms.ModelForm):
    class Meta:
        model = Organisation
        fields = ['name', 'admin_email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance.pk:
            # Existing organisation: bind address_form with instance and data
            
            try:
                physical_address = self.instance.physical_address
            except Address.DoesNotExist:
                physical_address = None
                
            self.address_form = AddressForm(
                self.data if self.is_bound else None,
                instance=physical_address,
                prefix='address',
                configuration=physical_address.configuration if physical_address else None
            )
        else:
            # New organisation: use default AddressConfiguration
            default_config = AddressConfiguration.objects.filter(is_default=True).first()
            if not default_config:
                default_config = AddressConfiguration.objects.first()
            self.address_form = AddressForm(
                self.data if self.is_bound else None,
                prefix='address',
                configuration=default_config
            )
            
    def is_valid(self):
        return super().is_valid() and self.address_form.is_valid()

    def save(self, commit=True):
        organisation = super().save(commit=False)
        if commit:
            address = self.address_form.save(commit=False)
            address.organisation = organisation  # Associate Address with Organisation
            address.save()
            organisation.save()
        return organisation

class OrganisationInviteForm(forms.Form):
    invite_code = forms.CharField(max_length=10)

class PublishingOutletForm(forms.ModelForm):
    class Meta:
        model = PublishingOutlet
        fields = ["name", "url", "description"]