from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Author(models.Model):
    """Автор статьи"""
    name = models.CharField(max_length=100, verbose_name="Name")
    bio = models.TextField(blank=True, verbose_name="Biography")

    class Meta:
        verbose_name = _("Author")
        verbose_name_plural = _("Authors")

    def __str__(self):
        return self.name

class Category(models.Model):
    """Категория статьи"""
    name = models.CharField(max_length=40, verbose_name="Title")

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.name

class Tag(models.Model):
    """Тег статьи"""
    name = models.CharField(max_length=20, verbose_name="Title")

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    def __str__(self):
        return self.name

class Article(models.Model):
    """Статья"""
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    content = models.TextField(blank=True, verbose_name=_("Content"))
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Publication date"))
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name=_("Author"),
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name=_("Category"),
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="articles",
        verbose_name=_("Tags"),
    )

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
        ordering = ["-pub_date"]

    def get_absolute_url(self):
        return reverse("blogapp:article_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return self.title
