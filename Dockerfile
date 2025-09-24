FROM python:3.13-slim

ENV PYTHONPATH=/app
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install poetry

# Копирование файлов зависимостей
COPY pyproject.toml poetry.lock ./

# Настройка Poetry
RUN poetry config virtualenvs.create false

# Установка зависимостей
RUN poetry install --no-interaction --no-root

# Копирование исходного кода
COPY . .

# Создание директорий
RUN mkdir -p /app/scripts /app/effective_mobile_fast_api/static /app/effective_mobile_fast_api/templates

EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "effective_mobile_fast_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]