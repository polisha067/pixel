"""
Мок-версия сервиса Yandex AI для тестирования без реального API.

Этот файл содержит заглушки, которые возвращают тестовые ответы
вместо реальных запросов к YandexGPT.

Использование:
1. В config.py установите USE_MOCK_AI = True
2. Или временно замените импорты в других файлах
"""

import random
from typing import Optional


# Тестовые ответы для классификации
CLASSIFICATION_RESPONSES = {
    "credit": [
        "credit", "credit", "credit", "credit"
    ],
    "insurance": [
        "insurance", "insurance", "insurance"
    ],
    "mortgage": [
        "mortgage", "mortgage"
    ],
    "deposit": [
        "deposit", "deposit"
    ],
    "cards": [
        "cards", "cards"
    ],
    "other": [
        "other", "other", "other"
    ]
}

# Тестовые ответы для генерации
GENERATION_TEMPLATES = {
    "credit": """Уважаемый клиент!

Благодарим Вас за обращение в наш банк по вопросу кредитования.

Мы получили Ваш запрос и готовы помочь Вам с оформлением кредита. 
Для рассмотрения Вашей заявки нам потребуются следующие документы:
- Паспорт
- Справка о доходах
- Документы, подтверждающие трудоустройство

Наш специалист свяжется с Вами в ближайшее время для уточнения деталей 
и консультации по условиям кредитования.

С уважением,
Отдел кредитования""",

    "insurance": """Уважаемый клиент!

Благодарим Вас за обращение в наш банк по вопросу страхования.

Мы получили Ваш запрос и готовы помочь Вам с оформлением страхового полиса.
Наш банк предлагает широкий спектр страховых услуг, включая ОСАГО, КАСКО 
и другие виды страхования.

Для оформления страховки Вам необходимо:
- Предоставить документы на транспортное средство (для автострахования)
- Заполнить заявление
- Оплатить страховую премию

Наш специалист свяжется с Вами для уточнения деталей и расчета стоимости.

С уважением,
Отдел страхования""",

    "default": """Уважаемый клиент!

Благодарим Вас за обращение в наш банк.

Мы получили Ваше письмо и обязательно рассмотрим его в ближайшее время.
Наш специалист свяжется с Вами для уточнения деталей и решения Вашего вопроса.

Если у Вас есть срочные вопросы, Вы можете связаться с нами по телефону 
горячей линии или посетить ближайшее отделение банка.

С уважением,
Команда банка"""
}


def send_request_to_yandex_mock(prompt: str, temperature: float = 0.6) -> str:
    """
    Мок-версия функции отправки запроса к YandexGPT.
    
    Анализирует промпт и возвращает подходящий тестовый ответ.
    
    Args:
        prompt: Текст запроса
        temperature: Игнорируется в мок-версии
    
    Returns:
        str: Тестовый ответ
    """
    prompt_lower = prompt.lower()
    
    # Определяем тип запроса по ключевым словам
    if "определи тип" in prompt_lower or "категория" in prompt_lower:
        # Это запрос на классификацию
        return classify_mock(prompt)
    elif "сгенерируй ответ" in prompt_lower or "ответ банка" in prompt_lower:
        # Это запрос на генерацию ответа
        return generate_response_mock(prompt)
    elif "улучшенную версию" in prompt_lower or "редактирование" in prompt_lower:
        # Это запрос на редактирование через чат
        return improve_response_mock(prompt)
    else:
        # Общий ответ
        return "Спасибо за обращение! Мы рассмотрим ваш запрос в ближайшее время."


def classify_mock(prompt: str) -> str:
    """
    Мок-классификация письма.
    
    Определяет категорию по ключевым словам в промпте.
    """
    prompt_lower = prompt.lower()
    
    # Ключевые слова для определения категории
    if any(word in prompt_lower for word in ["кредит", "credit", "займ", "ссуда"]):
        return "credit"
    elif any(word in prompt_lower for word in ["страхование", "insurance", "осаго", "каско", "полис"]):
        return "insurance"
    elif any(word in prompt_lower for word in ["ипотека", "mortgage", "ипотечный"]):
        return "mortgage"
    elif any(word in prompt_lower for word in ["вклад", "deposit", "депозит"]):
        return "deposit"
    elif any(word in prompt_lower for word in ["карта", "card", "карточка"]):
        return "cards"
    elif any(word in prompt_lower for word in ["бизнес", "business", "расчетный счет"]):
        return "business"
    elif any(word in prompt_lower for word in ["инвестиции", "investment", "брокер"]):
        return "investment"
    elif any(word in prompt_lower for word in ["интернет-банк", "online", "банкинг"]):
        return "online_banking"
    elif any(word in prompt_lower for word in ["валюта", "currency", "обмен"]):
        return "currency"
    else:
        return "other"


def generate_response_mock(prompt: str) -> str:
    """
    Мок-генерация ответа.
    
    Определяет категорию и возвращает соответствующий шаблон.
    """
    prompt_lower = prompt.lower()
    
    # Определяем категорию из промпта
    category = classify_mock(prompt)
    
    # Возвращаем соответствующий шаблон
    if category in GENERATION_TEMPLATES:
        return GENERATION_TEMPLATES[category]
    else:
        return GENERATION_TEMPLATES["default"]


def improve_response_mock(prompt: str) -> str:
    """
    Мок-улучшение ответа через чат.
    
    Возвращает улучшенную версию ответа.
    """
    # Извлекаем текущий черновик из промпта
    if "Текущий черновик ответа:" in prompt:
        parts = prompt.split("Текущий черновик ответа:")
        if len(parts) > 1:
            draft = parts[1].split("\n")[0].strip()
            
            # Добавляем улучшения в зависимости от просьбы сотрудника
            if "вежлив" in prompt.lower() or "вежливым" in prompt.lower():
                return draft.replace("Уважаемый", "Уважаемый").replace("!", "!") + "\n\nМы всегда рады помочь нашим клиентам!"
            elif "документ" in prompt.lower():
                return draft + "\n\nДля уточнения деталей просим предоставить необходимые документы."
            elif "контакт" in prompt.lower() or "связаться" in prompt.lower():
                return draft + "\n\nВы можете связаться с нами по телефону горячей линии или посетить ближайшее отделение."
            else:
                return draft + "\n\nМы готовы ответить на все ваши вопросы."
    
    # Если не удалось извлечь черновик, возвращаем общий ответ
    return """Уважаемый клиент!

Благодарим Вас за обращение. Мы рассмотрели Ваш запрос и готовы предоставить 
необходимую информацию.

Наш специалист свяжется с Вами в ближайшее время для уточнения деталей.

С уважением,
Команда банка"""


def send_request_with_context_mock(
    prompt: str,
    context: Optional[str] = None,
    system_instruction: Optional[str] = None,
    temperature: float = 0.6
) -> str:
    """
    Мок-версия функции с контекстом.
    
    Использует контекст для более точного ответа.
    """
    # Если это запрос на улучшение ответа
    if "улучшенную версию" in prompt.lower() or "редактирование" in prompt.lower():
        return improve_response_mock(prompt)
    
    # Иначе используем обычную генерацию
    return generate_response_mock(prompt)


def test_yandex_connection_mock() -> bool:
    """
    Мок-тест подключения (всегда возвращает True).
    """
    print("✅ Мок-режим: подключение работает!")
    return True

