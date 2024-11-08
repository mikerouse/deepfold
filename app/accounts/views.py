from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import UserRegistrationForm, PublishingOutletForm
from django.contrib.auth.decorators import login_required

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