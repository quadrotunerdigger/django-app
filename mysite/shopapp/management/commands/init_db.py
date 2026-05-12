from django.core.management import BaseCommand, call_command
from django.db import transaction


class Command(BaseCommand):
    help = 'Инициализирует базу данных: создаёт товары, заказ и токен'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Имя пользователя (по умолчанию: admin)',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        username = options['username']

        self.stdout.write(self.style.HTTP_INFO("=== Инициализация базы данных ==="))

        self.stdout.write("\n1. Создание товаров...")
        call_command('create_products')

        self.stdout.write("\n2. Создание заказа...")
        call_command('create_order', username=username)

        self.stdout.write("\n3. Создание токена...")
        call_command('create_token', username=username)

        self.stdout.write(
            self.style.SUCCESS("\n=== База данных инициализирована! ===")
        )