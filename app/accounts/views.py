from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.utils import timezone
from django.urls import reverse
from .forms import (
    UserRegistrationForm, 
    PublishingOutletForm, 
    OrganisationForm, 
    OrganisationInviteForm,
    AddressForm,
    UserUpdateForm
)
from .models import (
    Organisation, 
    OrganisationInvite,
    Task,
    PublishingOutlet
)
from django.contrib.auth.decorators import login_required
from .decorators import profile_required
from django.contrib import messages

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("publications")
    else:
        form = UserRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        # Corrected field name from 'organization' to 'organisation'
        if not hasattr(self.request.user, 'organisation') or not self.request.user.organisation:
            return reverse('complete_profile')
        
        # Regular users go to publications
        return reverse('publications')
    
@login_required
def edit_personal_details(request):
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your personal details have been updated successfully.")
            return redirect("manage_profile")
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, "accounts/edit_personal_details.html", {"form": form})

@login_required
def complete_profile(request):
    if request.user.organisation:
        return redirect("manage_profile")
    
    if request.method == "POST":
        # Initialize forms with POST data
        org_form = OrganisationForm(request.POST) if 'create_organisation' in request.POST else OrganisationForm()
        invite_form = OrganisationInviteForm(request.POST) if 'join_organisation' in request.POST else OrganisationInviteForm()
        
        if 'create_organisation' in request.POST:
            if org_form.is_valid():
                organisation = org_form.save()
                request.user.organisation = organisation
                request.user.save()
                messages.success(request, "Organisation created successfully: " + organisation.name)
                return redirect("add_addresses")
        
        elif 'join_organisation' in request.POST:
            if invite_form.is_valid():
                try:
                    invite = OrganisationInvite.objects.get(invite_code=invite_form.cleaned_data['invite_code'])
                    request.user.organisation = invite.organisation
                    request.user.save()
                    messages.success(request, "Organisation joined: " + invite.organisation.name)
                    return redirect("manage_profile")
                except OrganisationInvite.DoesNotExist:
                    invite_form.add_error('invite_code', 'Invalid invite code')
    else:
        # Initialize empty forms for GET request
        messages.warning(request, "You need to create an organisation or join one before you can move on.")
        org_form = OrganisationForm()
        invite_form = OrganisationInviteForm()
    
    return render(request, "accounts/complete_profile.html", {
        "org_form": org_form,
        "invite_form": invite_form,
    })
    
@login_required
def add_addresses(request):
    if not request.user.organisation:
        messages.warning(request, "You need to create an organisation or join one before you can add an address.")
        return redirect("complete_profile")
    
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.organisation = request.user.organisation
            address.save()
            return redirect("manage_profile")
    else:
        form = AddressForm()
    
    return render(request, "accounts/add_addresses.html", {
        "form": form,
    })
    
@login_required
def edit_organisation(request):
    if not request.user.organisation:
        messages.warning(request, "You need to create or join an organisation before editing.")
        return redirect("complete_profile")
    
    organisation = request.user.organisation
    if request.method == "POST":
        form = OrganisationForm(request.POST, instance=organisation)
        if form.is_valid():
            form.save()
            messages.success(request, "Organisation details have been updated successfully.")
            return redirect("manage_profile")
    else:
        form = OrganisationForm(instance=organisation)
    
    return render(request, "accounts/edit_organisation.html", {"form": form})
    
@login_required
def manage_profile(request):
    organisation = request.user.organisation
    addresses = organisation.addresses.all() if organisation else []
    
    if request.method == "POST":
        # Handle POST actions if any
        if 'update_org' in request.POST:
            org_form = OrganisationForm(request.POST, instance=organisation)
            if org_form.is_valid():
                org_form.save()
                messages.success(request, "Organisation details updated successfully.")
                return redirect('manage_profile')
        elif 'join_org' in request.POST:
            invite_form = OrganisationInviteForm(request.POST)
            if invite_form.is_valid():
                try:
                    invite = OrganisationInvite.objects.get(
                        invite_code=invite_form.cleaned_data['invite_code']
                    )
                    request.user.organisation = invite.organisation
                    request.user.save()
                    messages.success(request, "Organisation joined successfully.")
                    return redirect("manage_profile")
                except OrganisationInvite.DoesNotExist:
                    invite_form.add_error('invite_code', 'Invalid invite code')
        elif 'generate_invite' in request.POST:
            invite_code = organisation.generate_invite_code()
            messages.success(request, f"Invite code generated: {invite_code}")
    
    return render(request, 'accounts/manage_profile.html', {
        'organisation': organisation,
        'addresses': addresses,
    })

@login_required
def add_outlet(request):
    if request.method == "POST":
        form = PublishingOutletForm(request.POST)
        if form.is_valid():
            outlet = form.save(commit=False)
            outlet.user = request.user
            outlet.created = timezone.now()
            outlet.modified = timezone.now()
            outlet.save()
            return redirect("publications")
    else:
        form = PublishingOutletForm()
    return render(request, "accounts/add_outlet.html", {"form": form})

@login_required
def publications(request):
    outlets = request.user.outlets.all()
    return render(request, "accounts/publications.html", {"outlets": outlets})

@login_required
def publication_detail(request, pk):
    outlet = get_object_or_404(PublishingOutlet, pk=pk, user=request.user)
    return render(request, "accounts/publication_detail.html", {"outlet": outlet})