from django.contrib.auth.models import User

from django.core.management import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write("Start demo select fields")
        users_info = User.objects.values_list(
            "username",
            flat=True
        )
        print(list(users_info))
        for user_info in users_info:
            print(user_info)

        self.stdout.write("Done")