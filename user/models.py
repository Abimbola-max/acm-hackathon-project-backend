import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField

class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    avatar_url = CloudinaryField('avatar', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=2, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    genres = models.JSONField(default=list, blank=True)
    social_links = models.JSONField(default=dict, blank=True)
    total_platforms = models.IntegerField(default=0)

    USERNAME_FIELD = 'email'  # Use email for authentication
    REQUIRED_FIELDS = ['username']  # Username still required for admin, but can be set during registration

    def __str__(self):
        return self.username or self.email