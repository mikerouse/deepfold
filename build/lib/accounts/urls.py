from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("add_outlet/", views.add_outlet, name="add_outlet"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
