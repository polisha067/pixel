# Banking Assistant - Backend (FastAPI)

## Установка и запуск

1. **Установите Python зависимости:**
```bash
pip install -r requirements.txt
```

2. **Настройте переменные окружения:**
Создайте файл `.env` в папке backend со следующим содержимым:
```
OPENAI_API_KEY=your_openai_api_key_here
```
Получите API ключ на [OpenAI Platform](https://platform.openai.com/api-keys)

3. **Запустите сервер:**
```bash
python main.py
```

Сервер будет доступен по адресу: http://localhost:8000

## API Эндпоинты

### `GET /`
Проверка работоспособности API

### `POST /api/analyze`
Анализ входящего письма

**Request:**
```json
{
  "text": "Текст письма для анализа"
}
```

**Response:**
```json
{
  "type": "complaint",
  "type_display": "Жалоба/Претензия",
  "urgency": "high",
  "urgency_display": "Высокая срочность (ответ в течение 3 дней)",
  "key_params": ["список ключевых параметров"]
}
```

### `POST /api/generate`
Генерация ответа на письмо

**Request:**
```json
{
  "letter_type": "complaint",
  "style": "official",
  "original_text": "Текст оригинального письма"
}
```

**Response:**
```json
{
  "response": "Сгенерированный текст ответа"
}
```

## Режимы работы

- **С OpenAI API**: Если указан валидный API ключ, используется ИИ для генерации ответов
- **Демо режим**: Если API ключ не указан, используются заранее подготовленные шаблоны

## Типы писем

- `complaint` - Жалоба/Претензия
- `information_request` - Запрос информации
- `regulatory` - Регуляторный запрос
- `partnership` - Партнерское предложение
- `approval_request` - Запрос на согласование
- `notification` - Уведомление

## Стили ответов

- `official` - Строгий официальный стиль
- `business` - Деловой корпоративный стиль
- `client` - Клиентоориентированный стиль
