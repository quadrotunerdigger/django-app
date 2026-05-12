from django.urls import path

from .views import ArticlesListView, ArticleDetailView, AuthorDetailView, LatestArticlesFeed
app_name = "blogapp"

urlpatterns = [
    path("articles/", ArticlesListView.as_view(), name="articles_list"),
    path("articles/<int:pk>/", ArticleDetailView.as_view(), name="article_detail"),
    path("authors/<int:pk>/", AuthorDetailView.as_view(), name="author_detail"),
    path("articles/latest/feed", LatestArticlesFeed(), name="latest_articles_feed"),
]