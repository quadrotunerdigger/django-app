import magic
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Profile


ALLOWED_AVATAR_TYPES = ['image/jpeg', 'image/png', 'image/webp']
MAX_AVATAR_SIZE_MB = 2


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio", "avatar"]

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and hasattr(avatar, 'read'):
            # Проверка MIME-типа
            mime = magic.from_buffer(avatar.read(2048), mime=True)
            avatar.seek(0)
            if mime not in ALLOWED_AVATAR_TYPES:
                raise ValidationError(
                    _("Only JPEG, PNG, WebP are allowed. Received type: %(mime)s") % {'mime': mime}
                )
            # Проверка размера
            if avatar.size > MAX_AVATAR_SIZE_MB * 1024 * 1024:
                raise ValidationError(
                    _("Avatar must not exceed %(size)s MB") % {'size': MAX_AVATAR_SIZE_MB}
                )
        return avatar