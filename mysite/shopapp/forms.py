import magic
from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

from .models import Product, Order


ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'image/jpeg', 'image/png']
MAX_IMAGE_SIZE_MB = 5
MAX_DOCUMENT_SIZE_MB = 10
MAX_CSV_SIZE_MB = 5


def validate_file_size(max_size_mb):
    """Валидация размера файла"""
    def validator(file):
        max_size = max_size_mb * 1024 * 1024
        if file.size > max_size:
            raise ValidationError(
                _("File size must not exceed %(size)s MB. Current size: %(current).2f MB") % {
                    'size': max_size_mb,
                    'current': file.size / (1024 * 1024)
                }
            )

    return validator

def validate_csv_file(file):
    """Валидация CSV файла по MIME-типу"""
    mime = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)

    allowed_types = ['text/csv', 'text/plain', 'application/csv']
    if mime not in allowed_types:
        raise ValidationError(
            _("Only CSV files are allowed. Received type: %(mime)s") % {'mime': mime}
        )
    return file

def validate_image_file(file):
    """Валидация изображения по MIME-типу и размеру"""
    if file:
        # Проверка MIME-типа
        mime = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)  # Возвращаем указатель в начало файла
        if mime not in ALLOWED_IMAGE_TYPES:
            raise ValidationError(
                _("Only images are allowed: JPEG, PNG, WebP, GIF. Received type: %(mime)s") % {'mime': mime}
            )
        # Проверка размера
        if file.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            raise ValidationError(
                _("Image must not exceed %(size)s MB") % {'size': MAX_IMAGE_SIZE_MB}
            )
    return file

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name"]

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "name", "price", "description", "discount", "preview"

    images = MultipleFileField(required=False, label=_("Images"))

    def clean_preview(self):
        preview = self.cleaned_data.get('preview')
        if preview:
            validate_image_file(preview)
        return preview

    def clean_images(self):
        images = self.cleaned_data.get('images')
        if images:
            for image in images:
                if image:
                    validate_image_file(image)
        return images

class ProductCSVImportForm(forms.Form):
    """Форма для импорта товаров из CSV"""
    csv_file = forms.FileField(
        label=_("CSV file"),
        validators=[
            FileExtensionValidator(allowed_extensions=['csv']),
            validate_file_size(MAX_CSV_SIZE_MB),
        ],
        help_text=_("Max file size: %(size)s MB. Format: CSV") % {'size': MAX_CSV_SIZE_MB}
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data.get('csv_file')
        if csv_file:
            validate_csv_file(csv_file)
        return csv_file

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "delivery_address", "promocode", "user", "products"

    def clean_receipt(self):
        receipt = self.cleaned_data.get('receipt')
        if receipt:
            mime = magic.from_buffer(receipt.read(2048), mime=True)
            receipt.seek(0)
            if mime not in ALLOWED_DOCUMENT_TYPES:
                raise ValidationError(
                    _("Only PDF and images are allowed. Received type: %(mime)s") % {'mime': mime}
                )
            if receipt.size > MAX_DOCUMENT_SIZE_MB * 1024 * 1024:
                raise ValidationError(
                    _("File must not exceed %(size)s MB") % {'size': MAX_DOCUMENT_SIZE_MB}
                )
        return receipt

class OrderCSVImportForm(forms.Form):
    """Форма для импорта заказов из CSV"""
    csv_file = forms.FileField(
        label=_("CSV file with orders"),
        validators=[
            FileExtensionValidator(allowed_extensions=['csv']),
            validate_file_size(MAX_CSV_SIZE_MB),
        ],
        help_text=_("Format: user_id,delivery_address,promocode,product_ids. Max size: %(size)s MB") % {
            'size': MAX_CSV_SIZE_MB
        }
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data.get('csv_file')
        if csv_file:
            validate_csv_file(csv_file)
        return csv_file
