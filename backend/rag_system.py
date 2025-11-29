import os
from typing import List, Tuple, Dict

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), 'knowledge_base')


def load_knowledge_file(filename: str) -> str:
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
    knowledge_files = {}
    
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        print(f"[RAG] Warning: Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}")
        return knowledge_files
    
    for filename in os.listdir(KNOWLEDGE_BASE_DIR):
        if filename.endswith('.txt'):
            file_key = filename.replace('.txt', '')
            content = load_knowledge_file(filename)
            if content:
                knowledge_files[file_key] = content
    
    return knowledge_files


def determine_relevant_files(query: str) -> List[str]:
    query_lower = query.lower()
    relevant_files = set()
    
    keyword_to_file = {
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
        "кредитная карта": "cards.txt",
        "кредитка": "cards.txt",
        "дебетовая карта": "cards.txt",
        "дебетка": "cards.txt",
        "карта": "cards.txt",
        "лимит": "cards.txt",
        "льготный период": "cards.txt",
        "страхование": "insurance.txt",
        "страховка": "insurance.txt",
        "осаго": "insurance.txt",
        "каско": "insurance.txt",
        "полис": "insurance.txt",
        "инвестиции": "investments.txt",
        "инвест": "investments.txt",
        "пиф": "investments.txt",
        "офз": "investments.txt",
        "облигации": "investments.txt",
        "акции": "investments.txt",
        "накопления": "investments.txt",
        "накопительный счет": "investments.txt",
        "онлайн": "online_banking.txt",
        "интернет-банк": "online_banking.txt",
        "псб онлайн": "online_banking.txt",
        "мобильное приложение": "online_banking.txt",
        "платежи": "online_banking.txt",
        "переводы": "online_banking.txt",
        "кэшбэк": "cashback.txt",
        "бонусы": "cashback.txt",
        "cashback": "cashback.txt",
        "счет": "accounts.txt",
        "открытие счета": "accounts.txt",
        "закрытие счета": "accounts.txt",
        "контакты": "contacts.txt",
        "отделение": "contacts.txt",
        "горячая линия": "contacts.txt",
        "телефон": "contacts.txt",
        "адрес": "contacts.txt"
    }
    
    for keyword, filename in keyword_to_file.items():
        if keyword in query_lower:
            relevant_files.add(filename)
    
    if not relevant_files:
        relevant_files = {"credit.txt", "contacts.txt"}
    
    return list(relevant_files)


def extract_relevant_context(query: str, knowledge_files: Dict[str, str]) -> str:
    if not knowledge_files:
        return ""
    
    relevant_filenames = determine_relevant_files(query)
    context_parts = []
    
    for filename in relevant_filenames:
        file_key = filename.replace('.txt', '')
        if file_key in knowledge_files:
            content = knowledge_files[file_key]
            context_parts.append(f"=== {file_key.upper().replace('_', ' ')} ===\n{content}")
            print(f"[RAG] Добавлен файл: {filename}")
    
    if not context_parts:
        for file_key, content in list(knowledge_files.items())[:2]:
            context_parts.append(f"=== {file_key.upper().replace('_', ' ')} ===\n{content}")
    
    return "\n\n".join(context_parts)


async def get_rag_context(query: str) -> str:
    knowledge_files = load_all_knowledge_base()
    
    if not knowledge_files:
        print("[RAG] ОШИБКА: База знаний пуста или не найдена!")
        return ""
    
    print(f"[RAG] Загружено файлов базы знаний: {len(knowledge_files)}")
    
    context = extract_relevant_context(query, knowledge_files)
    
    print(f"[RAG] Запрос: {query[:100]}...")
    print(f"[RAG] Извлечен контекст: {len(context)} символов")
    if context:
        print(f"[RAG] Начало контекста: {context[:200]}...")
    else:
        print("[RAG] ВНИМАНИЕ: Контекст не извлечен!")
    
    return context
