from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.translation import activate


class GetCookieViewTestCase(TestCase):
    def setUp(self):
        # Обычный пользователь
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Суперпользователь
        self.admin = User.objects.create_superuser(
            username='admin',
            password='admin',
            email='admin@example.com'
        )

    def test_get_cookie_view_regular_user(self):
        self.client.login(username='testuser', password='testpass123')  # Исправлено
        response = self.client.get(reverse("myauth:cookie-get"))
        self.assertContains(response, "Cookie value")

    def test_get_cookie_view_superuser(self):
        self.client.login(username='admin', password='admin')
        response = self.client.get(reverse("myauth:cookie-get"))
        self.assertContains(response, "Cookie value")

    def test_set_cookie_view_superuser_only(self):
        # set_cookie_view требует is_superuser
        self.client.login(username='admin', password='admin')
        response = self.client.get(reverse("myauth:cookie-set"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cookie set")

    def test_set_cookie_view_regular_user_forbidden(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse("myauth:cookie-set"))
        # user_passes_test редиректит на login при неудаче
        self.assertEqual(response.status_code, 302)

    def test_get_cookie_view_anonymous_redirects(self):
        response = self.client.get(reverse("myauth:cookie-get"))
        self.assertEqual(response.status_code, 302)

class FooBarViewTestCase(TestCase):
    def test_foo_bar_value(self):
        activate('en')
        response = self.client.get(reverse("myauth:foo-bar"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers['content-type'], 'application/json',
        )
        expected_data = {'foo': 'bar', 'spam': 'eggs'}
        self.assertJSONEqual(response.content, expected_data)