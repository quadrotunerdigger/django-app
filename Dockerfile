FROM python:3.12

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Рабочая директория
WORKDIR /app

# Копируем и устанавливаем зависимости ДО копирования кода
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Копируем код приложения
COPY mysite .

CMD ["gunicorn", "mysite.wsgi:application", "--bind", "0.0.0.0:8000"]