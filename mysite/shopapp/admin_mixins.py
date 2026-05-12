import io
import logging
import time
from csv import DictWriter

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.utils.encoding import escape_uri_path

logger = logging.getLogger(__name__)


class ExportAsCSVMixin:
    """Миксин для экспорта данных в CSV"""
    export_csv_filename = None

    def export_csv(self, request: HttpRequest, queryset: QuerySet):
        """Экспорт выбранных записей в CSV"""
        start_time = time.time()

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv; charset=utf-8')

        filename = self.export_csv_filename or f"{meta.model_name}_export.csv"
        response[
            'Content-Disposition'] = f"attachment; filename=\"{filename}\"; filename*=UTF-8''{escape_uri_path(filename)}"

        # Добавляем BOM для корректного отображения в Excel
        response.write('\ufeff')

        writer = DictWriter(response, fieldnames=field_names)
        writer.writeheader()

        count = 0
        for obj in queryset:
            writer.writerow({field: getattr(obj, field) for field in field_names})
            count += 1

        duration = time.time() - start_time
        logger.info(f"CSV export completed: {count} records in {duration:.2f}s")

        return response

    export_csv.short_description = "Export as CSV"

class StreamingExportCSVMixin:
    """Миксин для потокового экспорта больших данных в CSV"""
    export_csv_filename = None

    def export_csv_streaming(self, request: HttpRequest, queryset: QuerySet):
        """Потоковый экспорт для больших объёмов данных"""
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        def generate():
            buffer = io.StringIO()
            writer = DictWriter(buffer, fieldnames=field_names)

            # BOM для Excel
            yield '\ufeff'

            # Заголовок
            writer.writeheader()
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

            # Данные порциями
            for obj in queryset.iterator(chunk_size=1000):
                writer.writerow({field: getattr(obj, field) for field in field_names})
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

        filename = self.export_csv_filename or f"{meta.model_name}_export.csv"

        response = StreamingHttpResponse(generate(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f"attachment; filename=\"{filename}\""

        return response

    export_csv_streaming.short_description = "Export as CSV (streaming)"

class ImportCSVMixin:
    """
    Миксин для импорта CSV в админке.

    Требует определить в дочернем классе:
    - import_csv_form_class: класс формы
    - import_csv_template: путь к шаблону
    - import_csv_url_name: имя URL для импорта
    - import_csv_save_func: функция сохранения данных
    - import_csv_field_name: имя поля файла в форме
    """
    import_csv_form_class = None
    import_csv_template = "admin/csv_form.html"
    import_csv_url_name = "import_csv"
    import_csv_save_func = None
    import_csv_field_name = "csv_file"

    def import_csv(self, request: HttpRequest) -> HttpResponse:
        from django.shortcuts import render, redirect

        if request.method == "GET":
            form = self.import_csv_form_class()
            context = {"form": form}
            return render(request, self.import_csv_template, context)

        form = self.import_csv_form_class(request.POST, request.FILES)
        if not form.is_valid():
            context = {"form": form}
            return render(request, self.import_csv_template, context, status=400)

        try:
            result = self.import_csv_save_func(
                file=form.files[self.import_csv_field_name].file,
                encoding=request.encoding,
            )

            if isinstance(result, tuple):
                count, errors = result
                if errors:
                    for error in errors[:10]:  # Показываем первые 10 ошибок
                        self.message_user(request, error, level="WARNING")
                    if len(errors) > 10:
                        self.message_user(
                            request,
                            f"... and {len(errors) - 10} more errors",
                            level="WARNING"
                        )
                self.message_user(request, f"Successfully imported: {count} records")
            else:
                self.message_user(request, "Data from CSV was imported")

        except Exception as e:
            logger.exception("CSV import error")
            self.message_user(request, f"Import error: {e}", level="ERROR")

        return redirect("..")
