from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    
    # You can add more custom fields here in the future
    
    def __str__(self):
        return self.username

class PublishingOutlet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="outlets")
    name = models.CharField(max_length=255)
    url = models.URLField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name