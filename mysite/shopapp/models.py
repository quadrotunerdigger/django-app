from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

def validate_file_size(file, max_size_mb=5):
    """Проверка размера файла"""
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Файл не должен превышать {max_size_mb} МБ")

def product_preview_directory_path(instance: "Product", filename: str) -> str:
    return "products/product_{pk}/preview/{filename}".format(
        pk=instance.pk,
        filename=filename,
    )

class Product(models.Model):
    """
    Модель Product представляет товар,
    который можно продавать в интернет-магазине.

    Заказы тут: `shopapp.Order`
    """
    class Meta:
        ordering = ["name", "price"]
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        permissions = [
            ("can_publish_product", "Can publish product"),
            ("can_archive_product", "Can archive product"),
            ("can_view_archived_products", "Can view archived products"),
        ]

    name = models.CharField(max_length=200, verbose_name=_("Name"), db_index=True)
    description = models.TextField(null=False, blank=True, verbose_name=_("Description"), db_index=True)
    price = models.DecimalField(
        default=0,
        max_digits=8,
        decimal_places=2,
        validators=[
            MinValueValidator(0),  # Цена не может быть отрицательной
        ],
        verbose_name=_("Price"),
    )
    discount = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),    # Скидка не меньше 0%
            MaxValueValidator(100),  # Скидка не больше 100%
        ],
        verbose_name=_("Discount"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    archived = models.BooleanField(default=False, verbose_name=_("Archived"))
    preview = models.ImageField(null=True, blank=True, upload_to=product_preview_directory_path, verbose_name=_("Preview"))
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name=_("Created by"),
    )

    def clean(self):
        super().clean()
        if self.preview and self.preview.size > 5 * 1024 * 1024:
            raise ValidationError({"preview": _("Image must not exceed 5 MB")})

    def get_absolute_url(self):
        return reverse("shopapp:product_details", kwargs={"pk": self.pk})

    def __str__(self):
        return f"Product(pk={self.pk}, name={self.name!r})"

def product_images_directory_path(instance: "ProductImage", filename: str) -> str:
    return "products/product_{pk}/images/{filename}".format(
        pk=instance.product.pk,
        filename=filename,
    )

class ProductImage(models.Model):
    class Meta:
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images", verbose_name=_("Product"))
    image = models.ImageField(null=True, blank=True, upload_to=product_images_directory_path, verbose_name=_("Image"))
    description = models.CharField(max_length=200, null=False, blank=True, verbose_name=_("Description"))

    def clean(self):
        super().clean()
        if self.image and self.image.size > 5 * 1024 * 1024:
            raise ValidationError({"image": _("Image must not exceed 5 MB")})

class Order(models.Model):
    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        permissions = [
            ("can_cancel_order", "Can cancel order"),
            ("can_process_order", "Can process order"),
        ]

    delivery_address = models.TextField(null=True, blank=True, verbose_name=_("Delivery address"),)
    promocode = models.CharField(max_length=20, null=False, blank=True, verbose_name=_("Promocode"),)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_("User"))
    products = models.ManyToManyField(Product, related_name="orders", verbose_name=_("Products"))
    receipt = models.FileField(null=True, upload_to="orders/receipts/", verbose_name=_("Receipt"))

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders_created",
        verbose_name=_("Created by"),
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders_updated",
        verbose_name=_("Updated by"),
    )

    def clean(self):
        super().clean()
        if self.receipt and self.receipt.size > 10 * 1024 * 1024:
            raise ValidationError({"receipt": _("File must not exceed 10 MB")})

    def __str__(self):
        return f"Order(pk={self.pk}, user={self.user.username!r})"