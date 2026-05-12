from django.core.management import BaseCommand
from django.db import transaction

from shopapp.models import Order, Product


class Command(BaseCommand):
    help = 'Обновляет заказ - добавляет все товары'

    def add_arguments(self, parser):
        parser.add_argument(
            '--order-id',
            type=int,
            help='ID заказа для обновления (по умолчанию: первый заказ)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить товары перед добавлением',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Update order")

        order_id = options.get('order_id')

        if order_id:
            try:
                order = Order.objects.get(pk=order_id)
            except Order.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Заказ #{order_id} не найден")
                )
                return
        else:
            order = Order.objects.first()
            if not order:
                self.stdout.write(
                    self.style.ERROR("Нет заказов. Сначала выполните: python manage.py create_order")
                )
                return

        products = Product.objects.filter(archived=False).only("id", "name")

        if not products.exists():
            self.stdout.write(
                self.style.ERROR("Нет активных товаров")
            )
            return

        if options['clear']:
            order.products.clear()
            self.stdout.write(self.style.WARNING("Товары очищены"))

        order.products.set(products)

        self.stdout.write(
            self.style.SUCCESS(
                f"Order #{order.pk} updated with {products.count()} products"
            )
        )