from django.shortcuts import render, redirect
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
    AddressForm
)
from .models import (
    Organisation, 
    OrganisationInvite,
    AddressConfiguration,
    Task
)
from django.contrib.auth.decorators import login_required
from .decorators import profile_required

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = UserRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        # Corrected field name from 'organization' to 'organisation'
        if not hasattr(self.request.user, 'organisation') or not self.request.user.organisation:
            return reverse('complete_profile')
        
        # Regular users go to dashboard
        return reverse('dashboard')

@login_required
def complete_profile(request):
    if request.user.organisation:
        return redirect("dashboard")
    if request.method == "POST":
        if 'create_organisation' in request.POST:
            org_form = OrganisationForm(request.POST)
            if org_form.is_valid():
                organisation = org_form.save()
                request.user.organisation = organisation
                request.user.save()
                return redirect("dashboard")
        elif 'join_organisation' in request.POST:
            invite_form = OrganisationInviteForm(request.POST)
            if invite_form.is_valid():
                try:
                    invite = OrganisationInvite.objects.get(invite_code=invite_form.cleaned_data['invite_code'])
                    request.user.organisation = invite.organisation
                    request.user.save()
                    return redirect("dashboard")
                except OrganisationInvite.DoesNotExist:
                    invite_form.add_error('invite_code', 'Invalid invite code')
    else:
        org_form = OrganisationForm()
        invite_form = OrganisationInviteForm()
    return render(request, "accounts/complete_profile.html", {
        "org_form": org_form,
        "invite_form": invite_form,
    })
    
@login_required
def manage_profile(request):
    if request.method == "POST":
        if 'update_org' in request.POST:
            org_form = OrganisationForm(request.POST, instance=request.user.organisation)
            if org_form.is_valid():
                org_form.save()
                
                # Mark the 'Complete Your Profile' task as completed
                try:
                    task = request.user.tasks.get(task_type='PROFILE')
                    if not task.completed:
                        task.completed = True
                        task.completed_at = timezone.now()
                        task.save()
                except Task.DoesNotExist:
                    pass
                
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
                    return redirect("manage_profile")
                except OrganisationInvite.DoesNotExist:
                    invite_form.add_error('invite_code', 'Invalid invite code')
        elif 'generate_invite' in request.POST:
            invite_code = request.user.organisation.generate_invite_code()
            org_form = OrganisationForm(instance=request.user.organisation)
            invite_form = OrganisationInviteForm()
            return render(request, 'accounts/manage_profile.html', {
                'org_form': org_form,
                'invite_form': invite_form,
                'invite_code': invite_code
            })
    else:
        org_form = OrganisationForm(instance=request.user.organisation)
        invite_form = OrganisationInviteForm()
    
    return render(request, 'accounts/manage_profile.html', {
        'org_form': org_form,
        'invite_form': invite_form,
    })

@login_required
def add_outlet(request):
    if request.method == "POST":
        form = PublishingOutletForm(request.POST)
        if form.is_valid():
            outlet = form.save(commit=False)
            outlet.user = request.user
            outlet.save()
            return redirect("dashboard")
    else:
        form = PublishingOutletForm()
    return render(request, "accounts/add_outlet.html", {"form": form})

@login_required
def dashboard(request):
    outlets = request.user.outlets.all()
    return render(request, "accounts/dashboard.html", {"outlets": outlets})