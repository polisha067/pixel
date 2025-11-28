"""
Сервис для работы с Yandex Cloud AI (YandexGPT).

Этот модуль отвечает за все взаимодействие с YandexGPT API:
- Отправка запросов к нейросети
- Получение ответов
- Обработка ошибок

YandexGPT - это русскоязычная языковая модель от Яндекса,
которая понимает контекст и может генерировать тексты.

В режиме тестирования (USE_MOCK_AI=True) используются мок-функции
вместо реальных запросов к API.
"""

import requests
import json
from typing import Optional

from backend.config import settings

# Импортируем мок-функции для тестирования
try:
    from backend.services.yandex_ai_mock import (
        send_request_to_yandex_mock,
        send_request_with_context_mock,
        test_yandex_connection_mock
    )
except ImportError:
    # Если мок-файл не найден, создаем заглушки
    def send_request_to_yandex_mock(*args, **kwargs):
        return "Мок-ответ: функция не реализована"
    
    def send_request_with_context_mock(*args, **kwargs):
        return "Мок-ответ: функция не реализована"
    
    def test_yandex_connection_mock():
        return True


def send_request_to_yandex(prompt: str, temperature: float = 0.6) -> str:
    """
    Отправляет запрос к YandexGPT API и получает ответ.
    
    Это основная функция для работы с нейросетью.
    Все остальные функции (классификация, генерация ответов) используют её.
    
    В режиме тестирования (USE_MOCK_AI=True) использует мок-функцию.
    
    Args:
        prompt: Текст запроса (промпт) для нейросети
        temperature: Температура генерации (0.0-1.0)
                    - 0.0 = более детерминированный, точный ответ
                    - 1.0 = более креативный, разнообразный ответ
                    - 0.6 = баланс между точностью и креативностью
    
    Returns:
        str: Ответ от нейросети
    
    Raises:
        Exception: Если произошла ошибка при запросе к API
    
    Пример использования:
        response = send_request_to_yandex("Привет! Как дела?")
        print(response)  # "Привет! У меня всё отлично, спасибо!"
    """
    # Если включен мок-режим, используем мок-функцию
    if settings.USE_MOCK_AI:
        print("🔧 Используется мок-режим Yandex AI")
        return send_request_to_yandex_mock(prompt, temperature)
    
    # ========== Реальный запрос к YandexGPT API ==========
    # URL эндпоинта YandexGPT API
    url = settings.YANDEX_API_URL
    
    # Заголовки запроса
    # Authorization - API ключ для аутентификации
    # x-folder-id - ID каталога в Yandex Cloud
    headers = {
        "Authorization": f"Api-Key {settings.YANDEX_API_KEY}",
        "x-folder-id": settings.YANDEX_FOLDER_ID,
        "Content-Type": "application/json"
    }
    
    # Тело запроса в формате JSON
    # modelUri - указывает, какую модель использовать (yandexgpt/latest)
    # completionOptions - настройки генерации
    # messages - история диалога (в нашем случае один запрос)
    payload = {
        "modelUri": f"gpt://{settings.YANDEX_FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,  # Не используем потоковую передачу
            "temperature": temperature,  # Температура генерации
            "maxTokens": 2000  # Максимальная длина ответа (в токенах)
        },
        "messages": [
            {
                "role": "user",  # Роль отправителя
                "text": prompt    # Текст запроса
            }
        ]
    }
    
    try:
        # Отправляем POST запрос к API
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # Проверяем статус ответа
        # 200 = успешно
        # Другие коды = ошибка
        response.raise_for_status()
        
        # Парсим JSON ответ
        data = response.json()
        
        # Извлекаем текст ответа из структуры ответа API
        # Структура: result.alternatives[0].message.text
        if "result" in data and "alternatives" in data["result"]:
            if len(data["result"]["alternatives"]) > 0:
                answer = data["result"]["alternatives"][0]["message"]["text"]
                return answer.strip()  # Убираем лишние пробелы
            else:
                raise Exception("Нейросеть не вернула ответ!")
        else:
            raise Exception(f"Неожиданный формат ответа от API: {data}")
    
    except requests.exceptions.RequestException as e:
        # Обработка ошибок сети (нет интернета, таймаут и т.д.)
        raise Exception(f"Ошибка при запросе к YandexGPT API: {str(e)}")
    
    except json.JSONDecodeError as e:
        # Ошибка парсинга JSON ответа
        raise Exception(f"Ошибка при парсинге ответа от API: {str(e)}")
    
    except Exception as e:
        # Любая другая ошибка
        raise Exception(f"Неожиданная ошибка: {str(e)}")
    # URL эндпоинта YandexGPT API
    url = settings.YANDEX_API_URL
    
    # Заголовки запроса
    # Authorization - API ключ для аутентификации
    # x-folder-id - ID каталога в Yandex Cloud
    headers = {
        "Authorization": f"Api-Key {settings.YANDEX_API_KEY}",
        "x-folder-id": settings.YANDEX_FOLDER_ID,
        "Content-Type": "application/json"
    }
    
    # Тело запроса в формате JSON
    # modelUri - указывает, какую модель использовать (yandexgpt/latest)
    # completionOptions - настройки генерации
    # messages - история диалога (в нашем случае один запрос)
    payload = {
        "modelUri": f"gpt://{settings.YANDEX_FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,  # Не используем потоковую передачу
            "temperature": temperature,  # Температура генерации
            "maxTokens": 2000  # Максимальная длина ответа (в токенах)
        },
        "messages": [
            {
                "role": "user",  # Роль отправителя
                "text": prompt    # Текст запроса
            }
        ]
    }
    
    try:
        # Отправляем POST запрос к API
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # Проверяем статус ответа
        # 200 = успешно
        # Другие коды = ошибка
        response.raise_for_status()
        
        # Парсим JSON ответ
        data = response.json()
        
        # Извлекаем текст ответа из структуры ответа API
        # Структура: result.alternatives[0].message.text
        if "result" in data and "alternatives" in data["result"]:
            if len(data["result"]["alternatives"]) > 0:
                answer = data["result"]["alternatives"][0]["message"]["text"]
                return answer.strip()  # Убираем лишние пробелы
            else:
                raise Exception("Нейросеть не вернула ответ!")
        else:
            raise Exception(f"Неожиданный формат ответа от API: {data}")
    
    except requests.exceptions.RequestException as e:
        # Обработка ошибок сети (нет интернета, таймаут и т.д.)
        raise Exception(f"Ошибка при запросе к YandexGPT API: {str(e)}")
    
    except json.JSONDecodeError as e:
        # Ошибка парсинга JSON ответа
        raise Exception(f"Ошибка при парсинге ответа от API: {str(e)}")
    
    except Exception as e:
        # Любая другая ошибка
        raise Exception(f"Неожиданная ошибка: {str(e)}")


def send_request_with_context(
    prompt: str,
    context: Optional[str] = None,
    system_instruction: Optional[str] = None,
    temperature: float = 0.6
) -> str:
    """
    Отправляет запрос к YandexGPT с дополнительным контекстом.
    
    Эта функция позволяет передать нейросети:
    - Системную инструкцию (роль, стиль ответа)
    - Контекст (предыдущие сообщения, история)
    
    В режиме тестирования (USE_MOCK_AI=True) использует мок-функцию.
    
    Args:
        prompt: Основной запрос
        context: Дополнительный контекст (история, предыдущие сообщения)
        system_instruction: Системная инструкция (роль ассистента, стиль)
        temperature: Температура генерации
    
    Returns:
        str: Ответ от нейросети
    
    Пример использования:
        response = send_request_with_context(
            prompt="Сгенерируй ответ на жалобу",
            context="Предыдущее письмо: ...",
            system_instruction="Ты помощник банка. Отвечай вежливо."
        )
    """
    # Если включен мок-режим, используем мок-функцию напрямую
    if settings.USE_MOCK_AI:
        print("🔧 Используется мок-режим Yandex AI (с контекстом)")
        return send_request_with_context_mock(prompt, context, system_instruction, temperature)
    
    # Формируем полный промпт с контекстом
    full_prompt = ""
    
    # Если есть системная инструкция, добавляем её в начало
    if system_instruction:
        full_prompt += f"Системная инструкция: {system_instruction}\n\n"
    
    # Если есть контекст, добавляем его
    if context:
        full_prompt += f"Контекст:\n{context}\n\n"
    
    # Добавляем основной запрос
    full_prompt += prompt
    
    # Отправляем запрос
    return send_request_to_yandex(full_prompt, temperature)


def test_yandex_connection() -> bool:
    """
    Тестирует подключение к YandexGPT API.
    
    Отправляет простой тестовый запрос, чтобы проверить,
    что API ключи правильные и API доступен.
    
    В режиме тестирования (USE_MOCK_AI=True) всегда возвращает True.
    
    Returns:
        bool: True если подключение работает, False если нет
    
    Использование:
        if test_yandex_connection():
            print("✅ YandexGPT API работает!")
        else:
            print("❌ Ошибка подключения к YandexGPT API")
    """
    # Если включен мок-режим, используем мок-тест
    if settings.USE_MOCK_AI:
        return test_yandex_connection_mock()
    
    try:
        # Отправляем простой тестовый запрос
        response = send_request_to_yandex("Скажи 'Привет' одним словом.")
        
        # Если получили ответ, значит всё работает
        if response:
            print(f"✅ Тест подключения успешен! Ответ: {response}")
            return True
        else:
            print("❌ Получен пустой ответ от API")
            return False
    
    except Exception as e:
        print(f"❌ Ошибка при тестировании подключения: {str(e)}")
        return False

