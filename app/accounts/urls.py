from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("complete_profile/", views.complete_profile, name="complete_profile"),
    path("add_outlet/", views.add_outlet, name="add_outlet"),
    path("publications/", views.publications, name="publications"),
    path("profile/", views.manage_profile, name="manage_profile"),
]
