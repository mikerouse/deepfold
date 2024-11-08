from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    email = models.EmailField(unique=True)
    organisation = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.username

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    awesomeness_score = models.IntegerField(default=0)
    organisation = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True)

class Task(models.Model):
    TASK_TYPES = [
        ('PROFILE', 'Complete Profile'),
        ('ORG', 'Join Organization'),
        ('OUTLET', 'Add Publishing Outlet'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    task_type = models.CharField(max_length=50, choices=TASK_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    email = models.EmailField(unique=True, verbose_name='email address')
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
    
class Organisation(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    postcode = models.CharField(max_length=10)
    admin_email = models.EmailField()
    
    def generate_invite_code(self):
        import random
        import string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        OrganisationInvite.objects.create(
            organisation=self,
            invite_code=code
        )
        return code

    def __str__(self):
        return self.name

class OrganisationInvite(models.Model):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    invite_code = models.CharField(max_length=10, unique=True)
    invited_email = models.EmailField()

    def __str__(self):
        return f"{self.invite_code} for {self.organisation.name}"
    
class PublishingOutlet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="outlets")
    name = models.CharField(max_length=255)
    url = models.URLField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
    

@receiver(post_save, sender=User)
def create_user_profile_handler(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)