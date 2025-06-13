FROM python:3.12-slim

# Установка зависимостей системы
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копируем только requirements.txt, чтобы использовать кэш
COPY requirements.txt .

# Установка Python-зависимостей
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install uvicorn python-multipart

# Копируем код приложения
COPY ./app /app

# Устанавливаем рабочую директорию
WORKDIR /app

# Запуск приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--loop", "asyncio"]