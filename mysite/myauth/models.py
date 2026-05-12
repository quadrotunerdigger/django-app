from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


def avatar_upload_path(instance: "Profile", filename: str) -> str:
    return "profiles/user_{pk}/avatar/{filename}".format(
        pk=instance.user.pk,
        filename=filename,
    )

class Profile(models.Model):
    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))
    bio = models.TextField(max_length=500, blank=True, verbose_name=_("Bio"))
    agreement_accepted = models.BooleanField(default=False, verbose_name=_("Agreement accepted"))
    avatar = models.ImageField(
        null=True,
        blank=True,
        upload_to=avatar_upload_path,
        verbose_name=_("Avatar"),
    )

    def clean(self):
        super().clean()
        if self.avatar and self.avatar.size > 2 * 1024 * 1024:
            raise ValidationError({"avatar": _("Avatar must not exceed 2 MB")})

    def __str__(self):
        return f"Profile(user={self.user.username!r})"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)