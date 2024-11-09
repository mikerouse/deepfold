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
        configuration = kwargs.pop('configuration', None)
        super().__init__(*args, **kwargs)
        if configuration:
            enabled_fields = configuration.fields.filter(enabled=True)
            for field in enabled_fields:
                self.fields[field.name].label = field.label
                self.fields[field.name].required = field.required

class OrganisationForm(forms.ModelForm):
    class Meta:
        model = Organisation
        fields = ['name', 'admin_email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Existing organisation: bind address_form with instance and data
            self.address_form = AddressForm(
                self.data if self.is_bound else None,
                instance=self.instance.address,
                prefix='address',
                configuration=self.instance.address.configuration
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

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            address = self.address_form.save()
            instance.address = address
            instance.save()
        return instance

class OrganisationInviteForm(forms.Form):
    invite_code = forms.CharField(max_length=10)

class PublishingOutletForm(forms.ModelForm):
    class Meta:
        model = PublishingOutlet
        fields = ["name", "url", "description"]