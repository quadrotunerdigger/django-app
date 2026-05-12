from string import ascii_letters
from random import choices

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.core.files.uploadedfile import SimpleUploadedFile

from shopapp.models import Product, Order
from .utils import add_two_numbers
from .forms import ProductForm


class AddTwoNumbersTestCase(TestCase):
    def test_add_two_numbers(self):
        result = add_two_numbers(2, 3)
        self.assertEqual(result, 5)


class ProductCreateViewTestCase(TestCase):
    def setUp(self) -> None:  # setUp, не setup!
        self.product_name = "".join(choices(ascii_letters, k=10))
        Product.objects.filter(name=self.product_name).delete()

        # Создаём пользователя с правом добавлять продукты
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        permission = Permission.objects.get(codename='add_product')
        self.user.user_permissions.add(permission)

    def test_create_product(self):
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(
            reverse("shopapp:product_create"),
            {
                "name": self.product_name,
                "price": "123.45",
                "description": "A good table",
                "discount": "10",
            }
        )
        self.assertRedirects(response, reverse("shopapp:products_list"))
        self.assertTrue(Product.objects.filter(name=self.product_name).exists())

    def test_create_product_without_permission(self):
        # Пользователь без прав — должен получить 403
        user_no_perm = User.objects.create_user(
            username='noperm',
            password='testpass123'
        )
        self.client.login(username='noperm', password='testpass123')

        response = self.client.post(
            reverse("shopapp:product_create"),
            {"name": "Test", "price": "100", "description": "", "discount": "0"}
        )
        self.assertEqual(response.status_code, 403)

class ProductFormValidationTestCase(TestCase):
    def test_preview_file_too_large(self):
        """Проверка отклонения файла больше 5 МБ"""
        # Создаём "большой" файл (для теста достаточно проверить логику)
        large_content = b'x' * (6 * 1024 * 1024)  # 6 МБ
        large_file = SimpleUploadedFile(
            name='large.jpg',
            content=large_content,
            content_type='image/jpeg'
        )

        form = ProductForm(
            data={'name': 'Test', 'price': '100', 'description': '', 'discount': '0'},
            files={'preview': large_file}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('preview', form.errors)

    def test_preview_invalid_mime_type(self):
        """Проверка отклонения файла с неверным MIME-типом"""
        # Текстовый файл с расширением .jpg
        fake_image = SimpleUploadedFile(
            name='fake.jpg',
            content=b'This is not an image',
            content_type='image/jpeg'
        )

        form = ProductForm(
            data={'name': 'Test', 'price': '100', 'description': '', 'discount': '0'},
            files={'preview': fake_image}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('preview', form.errors)

class ProductDetailsViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = Product.objects.create(name="".join(choices(ascii_letters, k=10)))

    @classmethod
    def tearDownClass(cls):
        cls.product.delete()
        super().tearDownClass()

    def test_get_product_details(self):
        response = self.client.get(
            reverse("shopapp:product_details", kwargs={"pk": self.product.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_get_product_details_and_check_content(self):
        response = self.client.get(
            reverse("shopapp:product_details", kwargs={"pk": self.product.pk})
        )
        self.assertContains(response, self.product.name)

class ProductListViewTestCase(TestCase):
    fixtures = [
        'products-fixtures.json',
    ]

    def test_products(self):
        response = self.client.get(reverse("shopapp:products_list"))
        self.assertQuerySetEqual(
            qs=Product.objects.filter(archived=False).all(),
            values=[product_from_context.pk for product_from_context in response.context["products"]],
            transform=lambda products_from_db: products_from_db.pk,
        )
        self.assertTemplateUsed(response, "shopapp/products-list.html")

class ProductsExportViewTestCase(TestCase):
    fixtures = [
        'products-fixtures.json',
    ]

    def test_get_products_view(self):
        response = self.client.get(reverse("shopapp:products_export_data"))
        self.assertEqual(response.status_code, 200)
        products = Product.objects.order_by("pk").all()
        expected_data = [
            {
                "pk": product.pk,
                "name": product.name,
                "price": str(product.price),
                "archived": product.archived,
            }
            for product in products
        ]
        products_data = response.json()
        self.assertEqual(
            products_data["products"],
            expected_data,
        )


class OrdersListViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser', password='testpass123')

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        super().setUpClass()

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_order_view(self):
        response = self.client.get(reverse("shopapp:orders_list"))
        self.assertContains(response, "Orders")

    def test_orders_view_not_authenticated(self):
        self.client.logout()
        response = self.client.get(reverse("shopapp:orders_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(settings.LOGIN_URL), response.url)

class OrderDetailViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Добавляем право на просмотр заказа
        permission = Permission.objects.get(codename='view_order')
        cls.user.user_permissions.add(permission)

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        super().tearDownClass()

    def setUp(self):
        self.client.force_login(self.user)
        self.order = Order.objects.create(
            delivery_address="ул. Тестовая, д.1",
            promocode="TESTCODE",
            user=self.user,
        )

    def tearDown(self):
        self.order.delete()

    def test_order_details(self):
        response = self.client.get(
            reverse("shopapp:order_detail", kwargs={"pk": self.order.pk})
        )
        self.assertEqual(response.status_code, 200)
        # Проверяем адрес в теле ответа
        self.assertContains(response, self.order.delivery_address)
        # Проверяем промокод в теле ответа
        self.assertContains(response, self.order.promocode)
        # Проверяем, что в контексте тот же заказ
        self.assertEqual(response.context["object"].pk, self.order.pk)

class OrdersExportViewTestCase(TestCase):
    fixtures = [
        'orders-fixtures.json',
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='staff_user',
            password='testpass123',
            is_staff=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        super().tearDownClass()

    def setUp(self):
        self.client.force_login(self.user)

    def test_get_orders_view(self):
        response = self.client.get(reverse("shopapp:orders_export_data"))
        self.assertEqual(response.status_code, 200)

        orders = Order.objects.order_by("pk").all()
        expected_data = [
            {
                "id": order.pk,
                "delivery_address": order.delivery_address,
                "promocode": order.promocode,
                "user_id": order.user.pk,
                "products_ids": [product.pk for product in order.products.all()],
            }
            for order in orders
        ]
        orders_data = response.json()

        print("\n" + "=" * 60)
        print("ДАННЫЕ ИЗ БАЗЫ ДАННЫХ (expected_data):")
        print("=" * 60)
        for item in expected_data:
            print(item)

        print("\n" + "=" * 60)
        print("ДАННЫЕ ИЗ ОТВЕТА API (orders_data['orders']):")
        print("=" * 60)
        for item in orders_data["orders"]:
            print(item)

        print("\n" + "=" * 60)
        print("РЕЗУЛЬТАТ СРАВНЕНИЯ:")
        print("=" * 60)
        print(f"Данные совпадают: {orders_data['orders'] == expected_data}")
        print("=" * 60 + "\n")

        self.assertEqual(orders_data["orders"], expected_data)

    def test_orders_export_not_staff_forbidden(self):
        # Пользователь без is_staff не должен иметь доступ
        regular_user = User.objects.create_user(
            username='regular_user',
            password='testpass123',
            is_staff=False,
        )
        self.client.force_login(regular_user)
        response = self.client.get(reverse("shopapp:orders_export_data"))
        self.assertEqual(response.status_code, 403)
        regular_user.delete()

