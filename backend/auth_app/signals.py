from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from auth_app.models import Profile, ensure_role_detail, role_for_user


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_for_user(sender, instance, created, raw=False, **kwargs):
    if raw or not created:
        return
    Profile.objects.get_or_create(
        user=instance,
        defaults={"role": role_for_user(instance)},
    )


@receiver(post_save, sender=Profile)
def create_role_detail_for_profile(sender, instance, raw=False, **kwargs):
    if raw:
        return
    ensure_role_detail(instance)
