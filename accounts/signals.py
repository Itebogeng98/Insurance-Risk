from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_profile(sender, instance, created, **kwargs) -> None:
    if created:
        role = (
            UserProfile.Role.ADMINISTRATOR
            if instance.is_staff or instance.is_superuser
            else UserProfile.Role.UNDERWRITER
        )
        UserProfile.objects.create(user=instance, role=role)
