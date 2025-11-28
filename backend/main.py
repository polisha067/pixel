"""
Banking Assistant - FastAPI Backend
ИИ-ассистент для генерации деловой переписки
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Инициализация FastAPI
app = FastAPI(
    title="Banking Assistant API",
    description="ИИ-ассистент для генерации деловой переписки",
    version="1.0.0"
)

# Настройка CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Модели данных
class LetterAnalysisRequest(BaseModel):
    text: str

class LetterAnalysisResponse(BaseModel):
    type: str
    type_display: str
    urgency: str
    urgency_display: str
    key_params: List[str]

class ResponseGenerationRequest(BaseModel):
    letter_type: str
    style: str
    original_text: str

class ResponseGenerationResponse(BaseModel):
    response: str

# Типы писем и их характеристики
LETTER_TYPES = {
    "complaint": {
        "display": "Жалоба/Претензия",
        "urgency": "high",
        "urgency_display": "Высокая срочность (ответ в течение 3 дней)",
        "keywords": ["жалоба", "претензия", "недоволен", "проблема", "возврат"]
    },
    "information_request": {
        "display": "Запрос информации",
        "urgency": "medium",
        "urgency_display": "Средняя срочность (ответ в течение 5 дней)",
        "keywords": ["прошу предоставить", "нужна информация", "запрос"]
    },
    "regulatory": {
        "display": "Регуляторный запрос",
        "urgency": "high",
        "urgency_display": "Высокая срочность (ответ в течение 2 дней)",
        "keywords": ["регулятор", "надзор", "проверка", "инспекция"]
    },
    "partnership": {
        "display": "Партнерское предложение",
        "urgency": "medium",
        "urgency_display": "Средняя срочность (ответ в течение 7 дней)",
        "keywords": ["сотрудничество", "партнерство", "предложение"]
    },
    "approval_request": {
        "display": "Запрос на согласование",
        "urgency": "high",
        "urgency_display": "Высокая срочность (ответ в течение 3 дней)",
        "keywords": ["согласование", "утверждение", "одобрение"]
    },
    "notification": {
        "display": "Уведомление",
        "urgency": "low",
        "urgency_display": "Низкая срочность (архивное хранение)",
        "keywords": ["уведомляем", "информируем", "сообщаем"]
    }
}

# Функции для анализа текста
def analyze_letter_type(text: str) -> str:
    """Определяет тип письма на основе ключевых слов"""
    text_lower = text.lower()

    for letter_type, config in LETTER_TYPES.items():
        if any(keyword in text_lower for keyword in config["keywords"]):
            return letter_type

    return "information_request"  # по умолчанию

def extract_key_params(text: str, letter_type: str) -> List[str]:
    """Извлекает ключевые параметры из текста"""
    params = []

    # Базовые параметры для всех типов
    if "сумма" in text.lower():
        params.append("Указана денежная сумма")
    if "дата" in text.lower():
        params.append("Указаны сроки")
    if "договор" in text.lower():
        params.append("Упоминание договора")

    # Специфические параметры по типам
    if letter_type == "complaint":
        params.extend([
            "Недовольство качеством обслуживания",
            "Требование компенсации"
        ])
    elif letter_type == "regulatory":
        params.extend([
            "Требование регулятора",
            "Необходимость отчетности"
        ])

    return params[:5]  # ограничиваем до 5 параметров

# API эндпоинты
@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {"message": "Banking Assistant API", "status": "running"}

@app.post("/api/analyze", response_model=LetterAnalysisResponse)
async def analyze_letter(request: LetterAnalysisRequest):
    """Анализ входящего письма"""
    try:
        # Определяем тип письма
        letter_type = analyze_letter_type(request.text)

        # Получаем конфигурацию типа
        type_config = LETTER_TYPES[letter_type]

        # Извлекаем ключевые параметры
        key_params = extract_key_params(request.text, letter_type)

        return LetterAnalysisResponse(
            type=letter_type,
            type_display=type_config["display"],
            urgency=type_config["urgency"],
            urgency_display=type_config["urgency_display"],
            key_params=key_params
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")

@app.post("/api/generate", response_model=ResponseGenerationResponse)
async def generate_response(request: ResponseGenerationRequest):
    """Генерация ответа на письмо"""
    try:
        # Если нет API ключа OpenAI, используем демо-ответы
        if not openai.api_key:
            response = generate_demo_response(request.style, request.letter_type)
        else:
            # Генерация через OpenAI
            response = await generate_ai_response(request)

        return ResponseGenerationResponse(response=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")

# Вспомогательные функции
def generate_demo_response(style: str, letter_type: str) -> str:
    """Генерация демо-ответов для тестирования без OpenAI"""
    responses = {
        "official": """Уважаемые господа!

В ответ на Ваше обращение сообщаем следующее:

Банк рассмотрел все обстоятельства, изложенные в Вашем письме. Мы относимся с пониманием к Вашей ситуации и готовы предложить следующие решения:

1. Проведение дополнительной проверки по указанным обстоятельствам
2. Предоставление подробной информации по интересующим вопросам
3. Организация встречи для детального обсуждения ситуации

Просим Вас уточнить предпочтительные сроки для проведения консультации.

С уважением,
Руководитель управления по работе с клиентами
Иванов И.И.""",

        "business": """Добрый день!

Благодарим Вас за обращение в наш банк.

Мы внимательно изучили Ваш запрос и подготовили следующие предложения:

• Предоставление запрашиваемой информации в течение 2 рабочих дней
• Организация консультации с профильным специалистом
• Подготовка индивидуального предложения по интересующим продуктам

Будем благодарны за дополнительную информацию, которая поможет нам лучше понять Ваши потребности.

С наилучшими пожеланиями,
Менеджер по работе с клиентами
Петрова А.С.""",

        "client": """Здравствуйте!

Спасибо, что обратились в наш банк. Мы ценим Ваше доверие и всегда стремимся предоставлять лучший сервис.

Понимая важность Вашего вопроса, мы:

• Подготовим всю необходимую информацию в кратчайшие сроки
• Организуем удобное время для подробной консультации
• Предложим наиболее подходящие решения для Вашей ситуации

Пожалуйста, сообщите, если у Вас есть дополнительные вопросы или пожелания.

Мы будем рады помочь!

С уважением,
Ваша команда поддержки банка"""
    }

    return responses.get(style, responses["business"])

async def generate_ai_response(request: ResponseGenerationRequest) -> str:
    """Генерация ответа через OpenAI"""
    style_prompts = {
        "official": "строгий официальный стиль для регуляторов и государственных органов",
        "business": "деловой корпоративный стиль для партнеров и контрагентов",
        "client": "клиентоориентированный стиль для физических лиц"
    }

    prompt = f"""
Ты - специалист по деловой переписке крупного банка. Сгенерируй ответ на следующее письмо.

СТИЛЬ ОТВЕТА: {style_prompts[request.style]}

ТИП ПИСЬМА: {request.letter_type}

ОРИГИНАЛЬНОЕ ПИСЬМО:
{request.original_text}

ТРЕБОВАНИЯ К ОТВЕТУ:
- Соблюдай корпоративный стиль банка
- Будь вежливым и профессиональным
- Включи конкретные действия и сроки
- Используй формальный язык
- Максимум 300 слов

Сгенерируй полный текст ответа:
"""

    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"OpenAI API error: {e}")
        # Fallback to demo response
        return generate_demo_response(request.style, request.letter_type)

# Запуск сервера (для разработки)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
