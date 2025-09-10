from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.username
    
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_user')
    address = models.TextField(default='', null=True,blank=True)
    phone = models.CharField(max_length=255,default='', null=True, blank=True)

    #signal to create  profile when user is created
    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)
        else:
            instance.profile_user.save()

      