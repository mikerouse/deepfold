from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, PublishingOutlet, Organisation, OrganisationInvite

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        
class OrganisationForm(forms.ModelForm):
    class Meta:
        model = Organisation
        fields = ['name', 'address', 'postcode', 'admin_email']

class OrganisationInviteForm(forms.Form):
    invite_code = forms.CharField(max_length=10)

class PublishingOutletForm(forms.ModelForm):
    class Meta:
        model = PublishingOutlet
        fields = ["name", "url", "description"]