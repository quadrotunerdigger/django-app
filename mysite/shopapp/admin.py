from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import path

from .common import save_csv_products, save_csv_orders
from .models import Product, Order, ProductImage
from .admin_mixins import ExportAsCSVMixin, ImportCSVMixin
from .forms import ProductCSVImportForm, OrderCSVImportForm


class OrderInline(admin.TabularInline):
    model = Product.orders.through

class ProductImageInline(admin.StackedInline):
    model = ProductImage

@admin.action(description="Archive products")
def mark_archived(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet):
    queryset.update(archived=True)

@admin.action(description="Unarchive products")
def mark_unarchived(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet):
    queryset.update(archived=False)

@admin.register(Product)
class ProductAdmin(ImportCSVMixin, ExportAsCSVMixin, admin.ModelAdmin):
    # Настройки ImportCSVMixin
    import_csv_form_class = ProductCSVImportForm
    import_csv_template = "admin/csv_form.html"
    import_csv_url_name = "import_products_csv"
    import_csv_save_func = staticmethod(save_csv_products)

    actions = [
        mark_archived,
        mark_unarchived,
        "export_csv",
    ]

    inlines = [
        OrderInline,
        ProductImageInline,
    ]

    list_display = "pk", "name", "description_short", "price", "discount", "archived"
    list_display_links = "pk", "name"
    ordering = "-name", "pk"
    search_fields = "name", "description"
    fieldsets = [
        (None, {
            "fields": ("name", "description"),
        }),
        ("Price options", {
            "fields": ("price", "discount"),
            "classes": ("wide", "collapse"),
        }),
        ("Images", {
            "fields": ("preview",),
        }),
        ("Extra options", {
            "fields": ("archived",),
            "classes": ("collapse",),
            "description": "Extra options. Field 'archived' is for soft delete",
        })
    ]

    change_list_template = "shopapp/products_changelist.html"

    def description_short(self, obj: Product) -> str:
        if len(obj.description) < 48:
            return obj.description
        return obj.description[:48] + "..."

    def export_all_csv(self, request: HttpRequest) -> HttpResponse:
        """Экспорт всех товаров в CSV"""
        return self.export_csv(request, Product.objects.all())

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [
            path(
                "import-products-csv/",
                self.import_csv,
                name="import_products_csv",
            ),
            path(
                "export-products-csv/",
                self.export_all_csv,
                name="export_products_csv",
            ),
        ]
        return new_urls + urls

class ProductInline(admin.StackedInline):
    model = Order.products.through

class OrderProductInline(admin.TabularInline):
    model = Order.products.through

@admin.register(Order)
class OrderAdmin(ImportCSVMixin, ExportAsCSVMixin, admin.ModelAdmin):
    # Настройки ImportCSVMixin
    import_csv_form_class = OrderCSVImportForm
    import_csv_template = "admin/csv_form.html"
    import_csv_url_name = "import_orders_csv"
    import_csv_save_func = staticmethod(save_csv_orders)

    inlines = [
        OrderProductInline,
    ]
    list_display = "pk", "delivery_address", "promocode", "created_at", "user_verbose"

    change_list_template = "shopapp/orders_changelist.html"

    def get_queryset(self, request):
        return Order.objects.select_related("user").prefetch_related("products")

    def user_verbose(self, obj: Order) -> str:
        return obj.user.first_name or obj.user.username

    def export_all_csv(self, request: HttpRequest) -> HttpResponse:
        """Экспорт всех заказов в CSV"""
        return self.export_csv(request, Order.objects.all())

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [
            path(
                "import-orders-csv/",
                self.import_csv,
                name="import_orders_csv",
            ),
            path(
                "export-orders-csv/",
                self.export_all_csv,
                name="export_orders_csv",
            ),
        ]
        return new_urls + urls


