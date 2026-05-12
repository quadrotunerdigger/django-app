from django.core.management import BaseCommand
from django.db.models import Avg, Max, Min, Count

from shopapp.models import Product


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write("Start demo aggregate")

        result = Product.objects.filter(
            name__contains='Монитор'
        ).aggregate(
            avg_price=Avg('price'),
            max_price=Max('price'),
            min_price=Min('price'),
            count=Count('id'),
        )
        print(result)

        self.stdout.write("Done")