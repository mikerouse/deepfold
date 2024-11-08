"""deepfold URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView
from accounts.views import register, add_outlet, publications, publication_detail, CustomLoginView

urlpatterns = [
    path("", CustomLoginView.as_view(), name="login"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("register/", register, name="register"),
    path("add_outlet/", add_outlet, name="add_outlet"),
    path("publications/", publications, name="publications"),
    path("publications/<int:pk>/", publication_detail, name="publication_detail"),
]
