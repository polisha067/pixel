# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем backend код
COPY backend/ ./backend/

# Создаем директорию для frontend
RUN mkdir -p /app/frontend

# Копируем frontend файлы
COPY frontend/ ./frontend/

# Открываем порт 8001 для FastAPI
EXPOSE 8001

# Запускаем FastAPI сервер
CMD ["python", "backend/main.py"]
