"""
RAG система для поиска релевантной информации из базы знаний ПСБ
Работает с файлами в папке knowledge_base/
"""
import os
from typing import List, Tuple, Dict

# Путь к папке с базой знаний
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), 'knowledge_base')

# Маппинг ключевых слов к файлам базы знаний


def load_knowledge_file(filename: str) -> str:
    """Загружает содержимое файла из базы знаний"""
    filepath = os.path.join(KNOWLEDGE_BASE_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"[RAG] Warning: Knowledge file not found: {filepath}")
        return ""
    except Exception as e:
        print(f"[RAG] Error loading {filename}: {e}")
        return ""


def load_all_knowledge_base() -> Dict[str, str]:
    """Загружает все файлы базы знаний"""
    knowledge_files = {}
    
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        print(f"[RAG] Warning: Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}")
        return knowledge_files
    
    # Загружаем все файлы из папки
    for filename in os.listdir(KNOWLEDGE_BASE_DIR):
        if filename.endswith('.txt'):
            file_key = filename.replace('.txt', '')
            content = load_knowledge_file(filename)
            if content:
                knowledge_files[file_key] = content
    
    return knowledge_files


def determine_relevant_files(query: str) -> List[str]:
    """
    Определяет, какие файлы базы знаний релевантны запросу
    """
    query_lower = query.lower()
    relevant_files = set()
    
    # Прямое сопоставление ключевых слов с файлами
    keyword_to_file = {
        # Кредитование
        "ипотека": "credit.txt",
        "ипотечный": "credit.txt",
        "ипотеку": "credit.txt",
        "ипотеке": "credit.txt",
        "автокредит": "credit.txt",
        "автомобиль": "credit.txt",
        "машина": "credit.txt",
        "потребительский кредит": "credit.txt",
        "ставка": "credit.txt",
        "ставку": "credit.txt",
        "взнос": "credit.txt",
        "возраст": "credit.txt",
        # Карты
        "кредитная карта": "cards.txt",
        "кредитка": "cards.txt",
        "дебетовая карта": "cards.txt",
        "дебетка": "cards.txt",
        "карта": "cards.txt",
        "лимит": "cards.txt",
        "льготный период": "cards.txt",
        # Страхование
        "страхование": "insurance.txt",
        "страховка": "insurance.txt",
        "осаго": "insurance.txt",
        "каско": "insurance.txt",
        "полис": "insurance.txt",
        # Инвестиции
        "инвестиции": "investments.txt",
        "инвест": "investments.txt",
        "пиф": "investments.txt",
        "офз": "investments.txt",
        "облигации": "investments.txt",
        "акции": "investments.txt",
        "накопления": "investments.txt",
        "накопительный счет": "investments.txt",
        # Онлайн-банкинг
        "онлайн": "online_banking.txt",
        "интернет-банк": "online_banking.txt",
        "псб онлайн": "online_banking.txt",
        "мобильное приложение": "online_banking.txt",
        "платежи": "online_banking.txt",
        "переводы": "online_banking.txt",
        # Кэшбэк
        "кэшбэк": "cashback.txt",
        "бонусы": "cashback.txt",
        "cashback": "cashback.txt",
        # Счета
        "счет": "accounts.txt",
        "открытие счета": "accounts.txt",
        "закрытие счета": "accounts.txt",
        # Контакты
        "контакты": "contacts.txt",
        "отделение": "contacts.txt",
        "горячая линия": "contacts.txt",
        "телефон": "contacts.txt",
        "адрес": "contacts.txt"
    }
    
    # Проверяем ключевые слова
    for keyword, filename in keyword_to_file.items():
        if keyword in query_lower:
            relevant_files.add(filename)
    
    # Если ничего не найдено, возвращаем основные файлы
    if not relevant_files:
        relevant_files = {"credit.txt", "contacts.txt"}  # Базовые файлы
    
    return list(relevant_files)


def extract_relevant_context(query: str, knowledge_files: Dict[str, str]) -> str:
    """
    Извлекает релевантный контекст из базы знаний на основе запроса.
    
    Args:
        query: Запрос клиента
        knowledge_files: Словарь с содержимым файлов базы знаний
    
    Returns:
        Релевантный контекст из базы знаний
    """
    if not knowledge_files:
        return ""
    
    # Определяем релевантные файлы
    relevant_filenames = determine_relevant_files(query)
    
    # Собираем контекст из релевантных файлов
    context_parts = []
    
    for filename in relevant_filenames:
        file_key = filename.replace('.txt', '')
        if file_key in knowledge_files:
            content = knowledge_files[file_key]
            context_parts.append(f"=== {file_key.upper().replace('_', ' ')} ===\n{content}")
            print(f"[RAG] Добавлен файл: {filename}")
    
    # Если ничего не найдено, возвращаем первые файлы
    if not context_parts:
        for file_key, content in list(knowledge_files.items())[:2]:
            context_parts.append(f"=== {file_key.upper().replace('_', ' ')} ===\n{content}")
    
    return "\n\n".join(context_parts)


async def get_rag_context(query: str) -> str:
    """
    Получает релевантный контекст из базы знаний для запроса.
    Это основная функция для использования в RAG системе.
    
    Args:
        query: Запрос клиента
    
    Returns:
        Релевантный контекст из базы знаний ПСБ
    """
    # Загружаем все файлы базы знаний
    knowledge_files = load_all_knowledge_base()
    
    if not knowledge_files:
        print("[RAG] ОШИБКА: База знаний пуста или не найдена!")
        return ""
    
    print(f"[RAG] Загружено файлов базы знаний: {len(knowledge_files)}")
    
    # Извлекаем релевантный контекст
    context = extract_relevant_context(query, knowledge_files)
    
    # Логируем для отладки
    print(f"[RAG] Запрос: {query[:100]}...")
    print(f"[RAG] Извлечен контекст: {len(context)} символов")
    if context:
        print(f"[RAG] Начало контекста: {context[:200]}...")
    else:
        print("[RAG] ВНИМАНИЕ: Контекст не извлечен!")
    
    return context
