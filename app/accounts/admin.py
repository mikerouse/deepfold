# accounts/admin.py
from django.contrib import admin
from .models import User, UserProfile, Task, Organisation, OrganisationInvite, PublishingOutlet

admin.site.register(User)
admin.site.register(UserProfile)
admin.site.register(Task)
admin.site.register(Organisation)
admin.site.register(OrganisationInvite)
admin.site.register(PublishingOutlet)