from django.contrib.syndication.views import Feed
from django.views.generic import ListView, DetailView
from django.urls import reverse, reverse_lazy
from .models import Article, Author


class ArticlesListView(ListView):
    """
    Список статей с оптимизированными запросами.

    select_related — для ForeignKey (author, category)
    prefetch_related — для ManyToMany (tags)
    defer — исключаем неиспользуемые поля (content)
    """
    template_name = "blogapp/article_list.html"
    context_object_name = "articles"
    queryset = (
        Article.objects
        .filter(pub_date__isnull=False)
        .order_by("-pub_date")
        .select_related("author", "category")
        .prefetch_related("tags")
        .defer("content")
    )

class ArticleDetailView(DetailView):
    """
    Детали статьи.
    """
    template_name = "blogapp/article_detail.html"
    context_object_name = "article"
    queryset = (
        Article.objects
        .select_related("author", "category")
        .prefetch_related("tags")
    )

class AuthorDetailView(DetailView):
    """
    Информация об авторе и его статьи.
    """
    template_name = "blogapp/author_detail.html"
    context_object_name = "author"
    queryset = Author.objects.prefetch_related("articles")

class LatestArticlesFeed(Feed):
    title = "Blog articles (latest)"
    description = "Updates on changes and addition blog articles"
    link = reverse_lazy("blogapp:articles_list")

    def items(self):
        return (
            Article.objects
            .filter(pub_date__isnull=False)
            .order_by("-pub_date")[:5]
        )

    def item_title(self, item: Article):
        return item.title

    def item_description(self, item: Article):
        return item.content[:200] if item.content else ""

    def item_link(self, item: Article):
        return item.get_absolute_url()