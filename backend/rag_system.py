"""
RAG система для поиска релевантной информации из базы знаний ПСБ
"""
import os
from typing import List, Tuple

# Путь к базе знаний
KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(__file__), 'psb_knowledge_base.txt')


def load_knowledge_base() -> str:
    """Загружает базу знаний из файла"""
    try:
        with open(KNOWLEDGE_BASE_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"[RAG] Warning: Knowledge base file not found at {KNOWLEDGE_BASE_PATH}")
        return ""


def extract_relevant_context(query: str, knowledge_base: str, max_chunks: int = 3) -> str:
    """
    Извлекает релевантный контекст из базы знаний на основе запроса.
    Использует простой поиск по ключевым словам и разбиение на секции.
    
    Args:
        query: Запрос клиента
        max_chunks: Максимальное количество релевантных секций для возврата
    
    Returns:
        Релевантный контекст из базы знаний
    """
    if not knowledge_base:
        return ""
    
    # Ключевые слова для каждой категории
    category_keywords = {
        "ипотека": ["ипотека", "ипотечный", "ипотеку", "ипотеке", "недвижимость", "квартира", "дом", "жилье", "материнский капитал", "молодая семья", "военная ипотека", "ставка", "ставку", "возраст", "взнос"],
        "автокредит": ["автокредит", "автомобиль", "машина", "авто", "транспорт", "лизинг", "trade-in"],
        "потребительский кредит": ["потребительский кредит", "кредит", "займ", "ссуда", "деньги в долг"],
        "кредитные карты": ["кредитная карта", "кредитка", "лимит", "льготный период"],
        "дебетовые карты": ["дебетовая карта", "дебетка", "карта", "снятие наличных", "обслуживание"],
        "страхование": ["страхование", "страховка", "осаго", "каско", "полис", "страховой"],
        "инвестиции": ["инвестиции", "инвест", "пиф", "офз", "облигации", "акции", "накопления", "накопительный счет"],
        "онлайн-банкинг": ["онлайн", "интернет-банк", "псб онлайн", "мобильное приложение", "платежи", "переводы", "калькулятор"],
        "кэшбэк": ["кэшбэк", "бонусы", "cashback", "начисления", "проценты"],
        "счета": ["счет", "открытие счета", "закрытие счета", "расчетный счет", "текущий счет"]
    }
    
    query_lower = query.lower()
    
    # Определяем релевантные категории
    relevant_categories = []
    for category, keywords in category_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            relevant_categories.append(category)
    
    # Если не найдено совпадений, возвращаем общую информацию
    if not relevant_categories:
        # Возвращаем первые несколько разделов базы знаний
        sections = knowledge_base.split('\n\n')
        return '\n\n'.join(sections[:max_chunks])
    
    # Извлекаем релевантные секции из базы знаний
    # Для запросов об ипотеке, ставках, возрасте - ищем весь раздел с ипотекой
    if "ипотека" in relevant_categories or any(kw in query_lower for kw in ["ставка", "ставку", "минимальная ставка", "возраст", "взнос", "ипотеку", "ипотеке", "ипотечный"]):
        # Ищем раздел "1.1. Ипотека" целиком
        lines = knowledge_base.split('\n')
        mortgage_start = None
        mortgage_end = None
        
        for i, line in enumerate(lines):
            # Ищем начало раздела об ипотеке
            if "1.1. Ипотека" in line or ("Ипотека" in line and i > 0 and "1.1" in lines[i-1]):
                mortgage_start = i
            # Ищем конец раздела (начало следующего раздела)
            elif mortgage_start is not None:
                line_stripped = line.strip()
                if line_stripped.startswith("1.2") or line_stripped.startswith("2.") or (line_stripped and line_stripped[0].isdigit() and "1.1" not in line):
                    mortgage_end = i
                    break
        
        if mortgage_start is not None:
            mortgage_end = mortgage_end if mortgage_end else len(lines)
            mortgage_section = '\n'.join(lines[mortgage_start:mortgage_end])
            print(f"[RAG] Найден раздел об ипотеке: строки {mortgage_start}-{mortgage_end}")
            return mortgage_section
        else:
            print("[RAG] Раздел об ипотеке не найден, используем обычный поиск")
    
    # Для других категорий используем обычный поиск
    sections = knowledge_base.split('\n\n')
    relevant_sections = []
    
    for section in sections:
        section_lower = section.lower()
        # Проверяем, содержит ли секция ключевые слова из релевантных категорий
        for category in relevant_categories:
            keywords = category_keywords[category]
            if any(keyword in section_lower for keyword in keywords):
                if section not in relevant_sections:
                    relevant_sections.append(section)
                break
    
    # Если нашли релевантные секции, возвращаем их
    if relevant_sections:
        return '\n\n'.join(relevant_sections[:max_chunks])
    
    # Если ничего не найдено, возвращаем начало базы знаний
    return '\n\n'.join(sections[:2])


async def get_rag_context(query: str) -> str:
    """
    Получает релевантный контекст из базы знаний для запроса.
    Это основная функция для использования в RAG системе.
    
    Args:
        query: Запрос клиента
    
    Returns:
        Релевантный контекст из базы знаний ПСБ
    """
    knowledge_base = load_knowledge_base()
    if not knowledge_base:
        print("[RAG] ОШИБКА: База знаний пуста!")
        return ""
    
    context = extract_relevant_context(query, knowledge_base)
    
    # Логируем для отладки
    print(f"[RAG] Запрос: {query[:100]}...")
    print(f"[RAG] Извлечен контекст: {len(context)} символов")
    if context:
        print(f"[RAG] Начало контекста: {context[:150]}...")
    else:
        print("[RAG] ВНИМАНИЕ: Контекст не извлечен!")
    
    return context

