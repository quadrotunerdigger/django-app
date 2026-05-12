import logging
import time
from csv import DictReader
from io import TextIOWrapper
from typing import Tuple, List

from django.contrib.auth.models import User
from django.db import transaction

from shopapp.models import Product, Order

logger = logging.getLogger(__name__)


def clean_string(value: str, max_length: int = 255) -> str:
    """Очистка и ограничение длины строки"""
    if value is None:
        return ""
    return str(value).strip()[:max_length]

def clean_decimal(value: str) -> str:
    """Очистка числового значения"""
    if value is None:
        return "0"
    # Убираем пробелы и заменяем запятую на точку
    return str(value).strip().replace(",", ".").replace(" ", "")

@transaction.atomic
def save_csv_products(file, encoding) -> Tuple[int, List[str]]:
    """
    Импорт товаров из CSV файла.

    Использует транзакцию — либо все записи создаются, либо ни одна.
    Возвращает кортеж (количество созданных, список ошибок).
    """
    start_time = time.time()
    errors = []

    csv_file = TextIOWrapper(
        file,
        encoding=encoding or 'utf-8',
    )

    reader = DictReader(csv_file)

    products_to_create = []
    row_number = 1

    for row in reader:
        row_number += 1
        try:
            # Очистка и валидация данных
            clean_data = {
                'name': clean_string(row.get('name', ''), max_length=100),
                'description': clean_string(row.get('description', ''), max_length=1000),
                'price': clean_decimal(row.get('price', '0')),
                'discount': int(clean_decimal(row.get('discount', '0'))),
            }

            if not clean_data['name']:
                errors.append(f"Row {row_number}: Name is required")
                continue

            products_to_create.append(Product(**clean_data))

        except (ValueError, KeyError) as e:
            errors.append(f"Row {row_number}: {e}")
            continue

    # Пакетная вставка
    if products_to_create:
        Product.objects.bulk_create(products_to_create)

    duration = time.time() - start_time
    logger.info(
        f"Products import completed: {len(products_to_create)} records in {duration:.2f}s. "
        f"Errors: {len(errors)}"
    )

    return len(products_to_create), errors

@transaction.atomic
def save_csv_orders(file, encoding) -> Tuple[int, List[str]]:
    """
    Импорт заказов из CSV файла.

    Формат CSV: user_id,delivery_address,promocode,product_ids
    Пример: 1,ул. Ленина д.10,SALE123,1;2;3

    Использует транзакцию — либо все записи создаются, либо ни одна.
    Возвращает кортеж (количество созданных, список ошибок).
    """
    start_time = time.time()
    errors = []

    csv_file = TextIOWrapper(
        file,
        encoding=encoding or 'utf-8',
    )

    reader = DictReader(csv_file)

    orders_created = 0
    row_number = 1

    for row in reader:
        row_number += 1
        try:
            # Валидация user_id
            user_id = row.get("user_id", "").strip()
            if not user_id:
                errors.append(f"Row {row_number}: user_id is required")
                continue

            try:
                user = User.objects.get(pk=int(user_id))
            except User.DoesNotExist:
                errors.append(f"Row {row_number}: User with id={user_id} not found")
                continue
            except ValueError:
                errors.append(f"Row {row_number}: Invalid user_id: {user_id}")
                continue

            # Очистка данных
            delivery_address = clean_string(row.get("delivery_address", ""), max_length=200)
            if not delivery_address:
                errors.append(f"Row {row_number}: delivery_address is required")
                continue

            promocode = clean_string(row.get("promocode", ""), max_length=50)

            # Создание заказа
            order = Order.objects.create(
                user=user,
                delivery_address=delivery_address,
                promocode=promocode,
            )

            # Привязка товаров (формат: 1;2;3)
            product_ids_str = row.get("product_ids", "").strip()
            if product_ids_str:
                try:
                    product_ids = [
                        int(pid.strip())
                        for pid in product_ids_str.split(";")
                        if pid.strip()
                    ]
                    products = Product.objects.filter(pk__in=product_ids, archived=False)

                    if products.count() != len(product_ids):
                        found_ids = set(products.values_list('pk', flat=True))
                        missing_ids = set(product_ids) - found_ids
                        if missing_ids:
                            errors.append(
                                f"Row {row_number}: Products not found or archived: {missing_ids}"
                            )

                    order.products.set(products)
                except ValueError as e:
                    errors.append(f"Row {row_number}: Invalid product_ids format: {e}")

            orders_created += 1

        except Exception as e:
            errors.append(f"Row {row_number}: Unexpected error: {e}")
            logger.exception(f"Error importing order from row {row_number}")
            continue

    duration = time.time() - start_time
    logger.info(
        f"Orders import completed: {orders_created} records in {duration:.2f}s. "
        f"Errors: {len(errors)}"
    )

    return orders_created, errors
