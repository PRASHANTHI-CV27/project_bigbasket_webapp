from django.db import models
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.username
    
    
class Profile(models.Model):
    ROLE_CHOICES = (
        ("customer", "Customer"),
        ("vendor", "Vendor"),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="customer")
    address = models.TextField(default='', null=True,blank=True)
    phone = models.CharField(max_length=255,default='', null=True, blank=True)
    
    def __str__(self):
        return f"Profile of {self.user.email}"

    #signal to create  profile when user is created
    @receiver(post_save, sender=User)
    def create_or_update_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)
        else:
            instance.profile.save()

class OTP(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP {self.code} for {self.email}"

    def is_expired(self, expiry_minutes=5):
        return timezone.now() > self.created_at + timedelta(minutes=expiry_minutes)
      