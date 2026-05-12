from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = 'Создаёт токен для указанного пользователя'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Имя пользователя (по умолчанию: admin)',
        )
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='Пересоздать токен, если существует',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        username = options['username']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Пользователь "{username}" не найден')
            )
            return

        if options['regenerate']:
            Token.objects.filter(user=user).delete()
            self.stdout.write(self.style.WARNING("Старый токен удалён"))

        token, created = Token.objects.get_or_create(user=user)

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Токен создан для пользователя "{username}"')
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Токен уже существует. Используйте --regenerate для пересоздания'
                )
            )

        self.stdout.write(f'Token: {token.key}')