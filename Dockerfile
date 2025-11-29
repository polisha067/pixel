# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости (для компиляции некоторых пакетов)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем backend код
COPY backend/ ./backend/

# Создаем директорию для frontend
RUN mkdir -p /app/frontend

# Копируем frontend файлы
COPY frontend/ ./frontend/

# Создаем директорию для базы данных (чтобы она сохранялась)
RUN mkdir -p /app/data

# Открываем порт 8001 для FastAPI
EXPOSE 8001

# Запускаем FastAPI сервер
# Используем 0.0.0.0 вместо 127.0.0.1 для Docker
CMD ["python", "backend/main.py"]
