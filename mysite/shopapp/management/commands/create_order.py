from typing import Sequence

from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.db import transaction

from shopapp.models import Order, Product


class Command(BaseCommand):
    help = 'Создаёт тестовый заказ'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Имя пользователя для заказа (по умолчанию: admin)',
        )
        parser.add_argument(
            '--address',
            type=str,
            default='ул. Победы, д.6',
            help='Адрес доставки',
        )
        parser.add_argument(
            '--promocode',
            type=str,
            default='SALE12345',
            help='Промокод',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Create order")

        username = options['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Пользователь "{username}" не найден')
            )
            return

        products: Sequence[Product] = Product.objects.only("id", "name").all()

        if not products.exists():
            self.stdout.write(
                self.style.ERROR('Нет товаров. Сначала выполните: python manage.py create_products')
            )
            return

        order, created = Order.objects.get_or_create(
            delivery_address=options['address'],
            promocode=options['promocode'],
            user=user,
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created order {order}"))
        else:
            self.stdout.write(self.style.WARNING(f"Order already exists: {order}"))

        for product in products:
            order.products.add(product)
            self.stdout.write(f"Added: {product.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Order #{order.pk} has {order.products.count()} products"
            )
        )