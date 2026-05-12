from django.core.management import BaseCommand
from django.db import transaction

from shopapp.models import Product


class Command(BaseCommand):
    help = 'Создаёт или обновляет тестовые товары'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить все товары перед созданием',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Create products")

        if options['clear']:
            deleted, _ = Product.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} products"))

        products_data = [
            {
                "name": "Ноутбук",
                "price": 75000,
                "discount": 5,
                "description": "Мощный игровой ноутбук с процессором Intel Core i7, видеокартой RTX 4060 и 16 ГБ оперативной памяти",
            },
            {
                "name": "Смартфон",
                "price": 45000,
                "discount": 10,
                "description": "Флагман с отличной камерой",
            },
            {
                "name": "Наушники",
                "price": 5000,
                "discount": 0,
                "description": "Беспроводные, шумоподавление",
            },
            {
                "name": "Клавиатура",
                "price": 3500,
                "discount": 15,
                "description": "Механическая, RGB подсветка",
            },
        ]

        created_count = 0
        updated_count = 0

        for product_data in products_data:
            product, created = Product.objects.update_or_create(
                name=product_data["name"],
                defaults={
                    "price": product_data["price"],
                    "discount": product_data["discount"],
                    "description": product_data["description"],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created: {product.name}")
            else:
                updated_count += 1
                self.stdout.write(f"Updated: {product.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Products ready! Created: {created_count}, Updated: {updated_count}"
            )
        )