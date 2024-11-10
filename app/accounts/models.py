from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

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
    points = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        
class AddressFieldConfiguration(models.Model):
    configuration = models.ForeignKey(
        'AddressConfiguration',
        on_delete=models.CASCADE,
        related_name='fields'
    )
    name = models.CharField(max_length=100)  # e.g. "postcode", "zip_code"
    label = models.CharField(max_length=100)  # Display label
    required = models.BooleanField(default=True)
    enabled = models.BooleanField(default=True)
    order = models.IntegerField()
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.label} ({'required' if self.required else 'optional'})"

class AddressConfiguration(models.Model):
    name = models.CharField(max_length=100, unique=True)  # e.g. "UK", "US"
    is_default = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default configuration
            AddressConfiguration.objects.filter(
                is_default=True
            ).update(is_default=False)
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.name} {'(Default)' if self.is_default else ''}"
    
class Organisation(models.Model):
    name = models.CharField(max_length=255)
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
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name
    
class Address(models.Model):
    
    ADDRESS_TYPE_CHOICES = [
        ('HO', 'Home'),
        ('WO', 'Work'),
        ('HQ', 'Headquarters'),
        ('PR', 'Printers'),
        ('BL', 'Billing'),
        ('SH', 'Shipping'),
        ('P1', 'Primary'),
        ('P2', 'Secondary'),
        ('P3', 'Alternative'),
        ('P4', 'Backup'),
        ('SU', 'Supplier'),
        ('CU', 'Customer'),
        ('VE', 'Vendor'),
        ('CO', 'Correspondence'),
        ('CR', 'Creditor'),
        ('DE', 'Debtor'),
        ('RE', 'Registered Office'),
        ('LE', 'Legal Notices'),
        ('OT', 'Other'),
    ]
    
    address_type = models.CharField(max_length=2, choices=ADDRESS_TYPE_CHOICES, default='P1')

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
     
    line1 = models.CharField(max_length=255, blank=True)
    line2 = models.CharField(max_length=255, blank=True)
    line3 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    region = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, blank=True)
    
    def clean(self):
        required_fields = ['line1', 'city', 'postal_code', 'country']  # Define required fields here
        for field in required_fields:
            if not getattr(self, field):
                raise ValidationError(f"{field.replace('_', ' ').title()} is required")

    def __str__(self):
        parts = [self.line1, self.city, self.region, self.postal_code, self.country]
        return ", ".join(filter(None, parts))
    

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile_handler(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)