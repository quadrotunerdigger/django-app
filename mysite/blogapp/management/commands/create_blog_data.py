from django.core.management import BaseCommand
from django.db import transaction

from blogapp.models import Author, Category, Tag, Article


class Command(BaseCommand):
    help = 'Создаёт тестовые данные для блога'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Создание данных для блога...")

        # Создаём авторов
        author1, _ = Author.objects.get_or_create(
            name="Иван Петров",
            defaults={"bio": "Python-разработчик с 5-летним опытом"}
        )
        author2, _ = Author.objects.get_or_create(
            name="Мария Сидорова",
            defaults={"bio": "Frontend-разработчик, любит React"}
        )

        # Создаём категории
        cat_python, _ = Category.objects.get_or_create(name="Python")
        cat_django, _ = Category.objects.get_or_create(name="Django")
        cat_frontend, _ = Category.objects.get_or_create(name="Frontend")

        # Создаём теги
        tag_tutorial, _ = Tag.objects.get_or_create(name="tutorial")
        tag_beginner, _ = Tag.objects.get_or_create(name="beginner")
        tag_advanced, _ = Tag.objects.get_or_create(name="advanced")
        tag_tips, _ = Tag.objects.get_or_create(name="tips")

        # Создаём статьи
        article1, created = Article.objects.get_or_create(
            title="Введение в Django",
            defaults={
                "content": "Django — это мощный веб-фреймворк на Python...",
                "author": author1,
                "category": cat_django,
            }
        )
        if created:
            article1.tags.add(tag_tutorial, tag_beginner)

        article2, created = Article.objects.get_or_create(
            title="Оптимизация запросов в Django ORM",
            defaults={
                "content": "select_related и prefetch_related помогают избежать N+1...",
                "author": author1,
                "category": cat_django,
            }
        )
        if created:
            article2.tags.add(tag_advanced, tag_tips)

        article3, created = Article.objects.get_or_create(
            title="React для начинающих",
            defaults={
                "content": "React — это библиотека для создания UI...",
                "author": author2,
                "category": cat_frontend,
            }
        )
        if created:
            article3.tags.add(tag_tutorial, tag_beginner)

        self.stdout.write(self.style.SUCCESS("Данные для блога созданы!"))