from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Ensure every User always has a Profile with the correct role.
    - Superusers/staff → "admin"
    - Others → keep existing or default "customer"/"vendor"
    """
    if created:
        # Assign role based on type of user
        role = "admin" if (instance.is_superuser or instance.is_staff) else "customer"
        Profile.objects.create(user=instance, role=role)

    else:
        # Update role if already has profile
        if hasattr(instance, "profile"):
            if instance.is_superuser or instance.is_staff:
                if instance.profile.role != "admin":
                    instance.profile.role = "admin"
                    instance.profile.save()
        else:
            # If profile missing, create one
            role = "admin" if (instance.is_superuser or instance.is_staff) else "customer"
            Profile.objects.create(user=instance, role=role)
