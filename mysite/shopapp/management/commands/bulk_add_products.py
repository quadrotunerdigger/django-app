from django.core.management import BaseCommand

from shopapp.models import Product


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write("Start demo bulk actions")

        info = [
            ('Монитор 1', 201),
            ('Монитор 2', 202),
            ('Монитор 3', 203),
        ]
        products = [
            Product(name=name, price=price)
            for name, price in info
        ]

        result = Product.objects.bulk_create(products)

        for object in result:
            print(object)

        self.stdout.write("Done")