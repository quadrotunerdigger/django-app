"""
В этом модуле лежат различные наборы представлений.

Разные view интернет-магазина: по товарам, заказам и т.д.
"""

import logging
from csv import DictWriter

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.contrib.syndication.views import Feed
from django.core.cache import cache
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .common import save_csv_products
from .forms import GroupForm, ProductForm, OrderForm
from .models import Product, Order, ProductImage
from .serializers import ProductSerializer, OrderSerializer
from .pagination import StandardResultsSetPagination

from datetime import datetime

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary='Список всех товаров',
        description='Возвращает список товаров с пагинацией, поиском и сортировкой',
    ),
    create=extend_schema(
        summary='Создать товар',
        description='Создаёт новый товар. Требуется авторизация.',
    ),
    retrieve=extend_schema(
        summary='Получить товар по ID',
        description='Возвращает детали товара или 404',
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(description='Товар не найден'),
        }
    ),
    update=extend_schema(
        summary='Обновить товар',
        description='Полное обновление товара. Требуется авторизация.',
    ),
    partial_update=extend_schema(
        summary='Частичное обновление товара',
        description='Обновляет отдельные поля товара.',
    ),
    destroy=extend_schema(
        summary='Архивировать товар',
        description='Архивирует товар (не удаляет из базы).',
    ),
)
class ProductViewSet(ModelViewSet):
    """
    ViewSet для Product с поиском, сортировкой и пагинацией.
    Чтение доступно всем, изменение — только авторизованным.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [
        SearchFilter,
        OrderingFilter,
    ]
    search_fields = [
        "name",
        "description",
    ]
    ordering_fields = [
        "name",
        "price",
        "discount",
    ]

    @method_decorator(cache_page(60 * 2))
    def list(self, *args, **kwargs):
        # print("hello products list")
        return super().list(*args, **kwargs)

    @extend_schema(
        summary='Get one product by ID',
        description='Retrieves **product**, return 404 if not found.',
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(description='Empty response, product by id not found'),
        }
    )
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Товар успешно создан", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"error": "Ошибка валидации", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.archived = True
        instance.save()
        return Response(
            {"message": f"Товар '{instance.name}' архивирован"},
            status=status.HTTP_200_OK
        )

    @action(methods=["get"], detail=False)
    def download_csv(self, request: Request):
        response = HttpResponse(content_type="text/csv")
        filename = "products-export.csv"
        response['Content-Disposition'] = f'attachment; filename={filename}'
        queryset = self.filter_queryset(self.get_queryset())
        fields = [
            "name",
            "description",
            "price",
            "discount",
        ]
        queryset = queryset.only(*fields)
        writer = DictWriter(response, fieldnames=fields)
        writer.writeheader()

        for product in queryset:
            writer.writerow({
                field: getattr(product, field)
                for field in fields
            })

        return response

    @action(methods=["post"], detail=False, parser_classes=[MultiPartParser])
    def upload_csv(self, request: Request):
        products = save_csv_products(
            request.FILES["file"].file,
            encoding=request.encoding
        )
        serializer = self.get_serializer(data=products, many=True)
        return Response(serializer.data)

class LatestProductsFeed(Feed):
    title = "Shop products (latest)"
    description = "Updates on new products in the shop"
    link = reverse_lazy("shopapp:products_list")

    def items(self):
        return (
            Product.objects
            .filter(archived=False)
            .order_by("-pk")[:5]
        )

    def item_title(self, item: Product):
        return item.name

    def item_description(self, item: Product):
        return item.description[:200] if item.description else ""

    def item_link(self, item: Product):
        return item.get_absolute_url()

@extend_schema_view(
    list=extend_schema(
        summary='Список всех заказов',
        description='Возвращает список заказов. Требуется авторизация.',
    ),
    create=extend_schema(
        summary='Создать заказ',
        description='Создаёт новый заказ.',
    ),
    retrieve=extend_schema(
        summary='Получить заказ по ID',
        description='Возвращает детали заказа.',
    ),
    update=extend_schema(
        summary='Обновить заказ',
        description='Полное обновление заказа.',
    ),
    partial_update=extend_schema(
        summary='Частичное обновление заказа',
        description='Обновляет отдельные поля заказа.',
    ),
    destroy=extend_schema(
        summary='Удалить заказ',
        description='Удаляет заказ из базы.',
    ),
)
class OrderViewSet(ModelViewSet):
    """
    ViewSet для Order с фильтрацией, сортировкой и защитой.
    Доступ только для авторизованных пользователей.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
    ]
    filterset_fields = [
        "user",
        "promocode",
        "delivery_address",
    ]
    ordering_fields = [
        "created_at",
        "user",
    ]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Заказ успешно создан", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"error": "Ошибка создания заказа", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        order_id = instance.pk
        self.perform_destroy(instance)
        return Response(
            {"message": f"Заказ #{order_id} удалён"},
            status=status.HTTP_200_OK
        )

class ShopIndexView(View):

    # @method_decorator(cache_page(60 * 2))
    def get(self, request: HttpRequest) -> HttpResponse:
        context = {
            "user_name": "гость магазина",
            "current_date": datetime.now(),
            "links": [
                {"url": "shopapp:products_list", "name": "Продукты"},
                {"url": "shopapp:orders_list", "name": "Заказы"},
                {"url": "shopapp:groups_list", "name": "Группы"},
            ],
            "items": 1,
            "description": "Наш магазин предлагает широкий ассортимент электроники и аксессуаров.",
        }
        print("shop index context", context)
        return render(request, 'shopapp/shop-index.html', context=context)

class GroupsListView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        context = {
            "form": GroupForm(),
            "groups": Group.objects.prefetch_related('permissions').all(),
        }
        return render(request, 'shopapp/groups-list.html', context=context)

    def post(self, request: HttpRequest):
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect(request.path)

class ProductDetailsView(DetailView):
    template_name = "shopapp/product-details.html"
    context_object_name = "product"
    queryset = Product.objects.filter(archived=False).prefetch_related("images")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message"] = "Детали продукта"
        return context

class ProductListView(ListView):
    template_name = "shopapp/products-list.html"
    context_object_name = "products"
    queryset = Product.objects.filter(archived=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_products"] = self.queryset.count()
        return context

class ProductCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "shopapp.add_product"
    model = Product
    form_class = ProductForm
    success_url = reverse_lazy("shopapp:products_list")

    def dispatch(self, request, *args, **kwargs):
        logger.info(f"User {request.user} creating product from IP: {request.META.get('REMOTE_ADDR')}")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # Сохраняем без preview
        preview = form.cleaned_data.get('preview')
        form.instance.preview = None
        response = super().form_valid(form)

        # Теперь pk есть, сохраняем preview
        if preview:
            self.object.preview = preview
            self.object.save()

        # Сохраняем дополнительные изображения
        for image in form.files.getlist("images"):
            ProductImage.objects.create(
                product=self.object,
                image=image,
            )
        return response

class ProductUpdateView(UserPassesTestMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name_suffix = "_update_form"

    def test_func(self):
        product = self.get_object()
        user = self.request.user

        # Суперпользователю можно всегда
        if user.is_superuser:
            return True

        # Остальным: permission + автор продукта
        has_permission = user.has_perm("shopapp.change_product")
        is_author = product.created_by == user

        return has_permission and is_author

    def dispatch(self, request, *args, **kwargs):
        logger.info(f"User {request.user} updating product {kwargs.get('pk')}")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            "shopapp:product_details",
            kwargs={"pk": self.object.pk}
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        for image in form.files.getlist("images"):
            ProductImage.objects.create(
                product=self.object,
                image=image,
            )
        return response

class ProductDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = "shopapp.can_archive_product"
    model = Product
    success_url = reverse_lazy("shopapp:products_list")

    def dispatch(self, request, *args, **kwargs):
        logger.info(f"User {request.user} archiving product {kwargs.get('pk')}")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.archived = True
        self.object.save()
        logger.info(f"Product {self.object.pk} archived successfully")
        return HttpResponseRedirect(success_url)

class ProductsDataExportView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        cache_key = "products_data_export"
        products_data = cache.get(cache_key)
        if products_data is None:
            products_from_db = Product.objects.order_by("pk").all()
            products_data = [
                {
                    "pk": product_from_db.pk,
                    "name": product_from_db.name,
                    "price": str(product_from_db.price),
                    "archived": product_from_db.archived,
                }
                for product_from_db in products_from_db
            ]
            cache.set(cache_key, products_data, timeout=60 * 5)
        return JsonResponse({"products": products_data})


class OrdersListView(LoginRequiredMixin, ListView):
    queryset = (
        Order.objects
        .select_related("user")
        .prefetch_related("products")
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_orders"] = self.queryset.count()
        return context

class OrderDetailsView(PermissionRequiredMixin, DetailView):
    permission_required = "shopapp.view_order"
    queryset = (
        Order.objects
        .select_related("user")
        .prefetch_related("products")
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products_count"] = self.object.products.count()
        return context

class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    success_url = reverse_lazy("shopapp:orders_list")

    def dispatch(self, request, *args, **kwargs):
        logger.info(f"User {request.user} creating order from IP: {request.META.get('REMOTE_ADDR')}")
        return super().dispatch(request, *args, **kwargs)

class OrderUpdateView(LoginRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name_suffix = "_update_form"

    def dispatch(self, request, *args, **kwargs):
        logger.info(f"User {request.user} updating order {kwargs.get('pk')}")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            "shopapp:order_detail",
            kwargs={"pk": self.object.pk}
        )

class OrderDeleteView(LoginRequiredMixin, DeleteView):
    model = Order
    success_url = reverse_lazy("shopapp:orders_list")

    def dispatch(self, request, *args, **kwargs):
        logger.warning(f"User {request.user} deleting order {kwargs.get('pk')}")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        logger.warning(f"Order {self.object.pk} deleted by user")
        return super().form_valid(form)

class OrdersDataExportView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request: HttpRequest) -> JsonResponse:
        orders_from_db = (
            Order.objects
            .select_related("user")
            .prefetch_related("products")
            .order_by("pk")
            .all()
        )
        orders_data = [
            {
                "id": order_from_db.pk,
                "delivery_address": order_from_db.delivery_address,
                "promocode": order_from_db.promocode,
                "user_id": order_from_db.user.pk,
                "products_ids": [product.pk for product in order_from_db.products.all()],
            }
            for order_from_db in orders_from_db
        ]
        return JsonResponse({"orders": orders_data})


class UserOrdersListView(LoginRequiredMixin, ListView):
    """
    Список заказов конкретного пользователя.
    Доступен только авторизованным пользователям.
    """
    template_name = "shopapp/user_orders_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        # Получаем пользователя по user_id из URL
        user_id = self.kwargs.get("user_id")
        self.owner = get_object_or_404(User, pk=user_id)
        return (
            Order.objects
            .filter(user=self.owner)
            .select_related("user")
            .prefetch_related("products")
            .order_by("pk")
        )
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["owner"] = self.owner
        return context

class UserOrdersExportView(LoginRequiredMixin, View):
    """
    Экспорт заказов пользователя в JSON с кэшированием.
    """
    def get(self, request: HttpRequest, user_id: int) -> JsonResponse:
        # Генерируем уникальный ключ кэша для пользователя
        cache_key = f"user_{user_id}_orders_export"
        # Пробуем получить данные из кэша
        orders_data = cache.get(cache_key)

        if orders_data is None:
            # Данных в кэше нет — загружаем из БД
            logger.info(f"Cache MISS for {cache_key} - loading from DB")
            owner = get_object_or_404(User, pk=user_id)
            orders = (
                Order.objects
                .filter(user=owner)
                .select_related("user")
                .prefetch_related("products")
                .order_by("pk")
            )
            # Сериализуем данные
            serializer = OrderSerializer(orders, many=True)
            orders_data = serializer.data
            # Сохраняем в кэш на 5 минут
            cache.set(cache_key, orders_data, timeout=60 * 5)
        else:
            logger.info(f"Cache HIT for {cache_key}")

        return JsonResponse({"user_id": user_id, "orders": orders_data})

