from django.contrib import admin

from .models import Author, Category, Tag, Article


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["pk", "name"]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["pk", "name"]

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["pk", "name"]

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["pk", "title", "author", "category", "pub_date"]
    list_filter = ["category", "author"]
    filter_horizontal = ["tags"]
