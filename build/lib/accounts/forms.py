from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, PublishingOutlet

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class PublishingOutletForm(forms.ModelForm):
    class Meta:
        model = PublishingOutlet
        fields = ["name", "url", "description"]
