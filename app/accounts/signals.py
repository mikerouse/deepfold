# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile, Task

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile.objects.create(user=instance)
        
        Task.objects.create(
            user=instance,
            task_type='PROFILE',
            title='Complete Your Profile',
            description='Add your organisation details to unlock more features',
            points=10
        )