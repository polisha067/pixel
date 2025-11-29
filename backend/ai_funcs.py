from openai import OpenAI
from dotenv import load_dotenv
import os, json
from ai_promts import ANALISYS_PROMT, get_generation_promt, BUSINESS_INFO_EXTRACTION_PROMPT
from rag_system import get_rag_context

load_dotenv()

api_key = os.getenv('api_key')
folder_id = os.getenv('folder_id')

if not api_key or not folder_id:
    raise ValueError("API key or folder ID not found in environment variables")

model = f"gpt://{folder_id}/qwen3-235b-a22b-fp8/latest"

client = OpenAI(
    base_url="https://rest-assistant.api.cloud.yandex.net/v1",
    api_key=api_key,
    project=folder_id
)


async def analyze_mail(email):
    try:
        response = client.responses.create(
            model=model,
            instructions=ANALISYS_PROMT,
            input=email,
            temperature=0.1
        )

        result_text = response.output_text.strip()

        result = json.loads(result_text)

        if "email_type" not in result or "deadline" not in result:
            raise ValueError("Invalid response structure from API")
        
        # Если specialization не указана, устанавливаем "Прочее"
        if "specialization" not in result:
            result["specialization"] = "Прочее"

        return result

    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse API response as JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"Yandex API error: {str(e)}")

async def generate_mail(email, instructions):
    try:
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=email
        )
        return response.output_text

    except Exception as e:
        raise Exception(f"Yandex API error: {str(e)}")


async def extract_business_info(email_content):
    """
    Извлекает важную бизнес-информацию о клиенте из письма.
    
    Args:
        email_content: Текст письма от клиента
    
    Returns:
        Словарь с извлеченной информацией (например, {"has_credit_card": true})
    """
    try:
        response = client.responses.create(
            model=model,
            instructions=BUSINESS_INFO_EXTRACTION_PROMPT,
            input=email_content,
            temperature=0.1
        )

        result_text = response.output_text.strip()
        
        # Убираем markdown код блоки, если есть
        if result_text.startswith("```"):
            # Удаляем ```json и ``` в начале и конце
            result_text = result_text.replace("```json", "").replace("```", "").strip()

        result = json.loads(result_text)
        
        # Фильтруем только важные поля
        important_keys = [
            "has_credit_card", "has_debit_card", "has_mortgage", 
            "has_car_loan", "has_consumer_loan", "has_account", "has_insurance"
        ]
        
        filtered_result = {k: v for k, v in result.items() if k in important_keys}
        
        if filtered_result:
            print(f"[BIZ_INFO] Извлечена бизнес-информация: {filtered_result}")
        else:
            print("[BIZ_INFO] Важная бизнес-информация не найдена в письме")
        
        return filtered_result

    except json.JSONDecodeError as e:
        print(f"[BIZ_INFO] Ошибка парсинга JSON: {str(e)}")
        print(f"[BIZ_INFO] Ответ API: {result_text[:200]}")
        return {}
    except Exception as e:
        print(f"[BIZ_INFO] Ошибка извлечения информации: {str(e)}")
        return {}


def format_business_info_context(business_info: dict) -> str:
    """
    Форматирует бизнес-информацию для включения в контекст генерации ответа.
    
    Args:
        business_info: Словарь с бизнес-информацией
    
    Returns:
        Отформатированная строка с информацией
    """
    if not business_info:
        return ""
    
    formatted = []
    formatted.append("═══════════════════════════════════════════════════════════════")
    formatted.append("ВАЖНАЯ БИЗНЕС-ИНФОРМАЦИЯ О КЛИЕНТЕ")
    formatted.append("═══════════════════════════════════════════════════════════════")
    formatted.append("")
    
    info_labels = {
        "has_credit_card": "Наличие кредитной карты",
        "has_debit_card": "Наличие дебетовой карты",
        "has_mortgage": "Наличие ипотеки",
        "has_car_loan": "Наличие автокредита",
        "has_consumer_loan": "Наличие потребительского кредита",
        "has_account": "Наличие счета в банке",
        "has_insurance": "Наличие страховки"
    }
    
    for key, value in business_info.items():
        label = info_labels.get(key, key)
        status = "Да" if value else "Нет"
        formatted.append(f"- {label}: {status}")
    
    formatted.append("")
    formatted.append("ВАЖНО: Используй эту информацию при генерации ответа. Если клиент является держателем карты или имеет кредит - учитывай это в ответе.")
    formatted.append("═══════════════════════════════════════════════════════════════")
    formatted.append("")
    
    return "\n".join(formatted)


def format_letter_history(letters_history):
    """
    Форматирует историю писем для включения в контекст генерации.
    
    Args:
        letters_history: Список словарей с ключами 'content', 'response', 'created_at'
    
    Returns:
        Отформатированная строка с историей переписки
    """
    if not letters_history:
        return ""
    
    formatted_history = []
    formatted_history.append("═══════════════════════════════════════════════════════════════")
    formatted_history.append("ИСТОРИЯ ПРЕДЫДУЩЕЙ ПЕРЕПИСКИ С КЛИЕНТОМ")
    formatted_history.append("═══════════════════════════════════════════════════════════════")
    formatted_history.append("")
    
    for idx, letter in enumerate(letters_history, 1):
        formatted_history.append(f"--- Письмо #{idx} (дата: {letter.get('created_at', 'не указана')}) ---")
        formatted_history.append("")
        formatted_history.append("КЛИЕНТ:")
        formatted_history.append(letter.get('content', ''))
        formatted_history.append("")
        
        # Если есть ответ, добавляем его
        if letter.get('response'):
            formatted_history.append("ОТВЕТ БАНКА:")
            formatted_history.append(letter.get('response', ''))
            formatted_history.append("")
        
        formatted_history.append("-" * 60)
        formatted_history.append("")
    
    formatted_history.append("═══════════════════════════════════════════════════════════════")
    formatted_history.append("")
    formatted_history.append("ВАЖНО: Учитывай эту историю при генерации ответа. Если клиент продолжает предыдущую тему или задает уточняющие вопросы - обязательно используй контекст из истории переписки.")
    formatted_history.append("")
    
    return "\n".join(formatted_history)


async def generate_answer(incoming_letter, letters_history=None, business_info=None):
    """
    Генерирует ответ на входящее письмо с учетом истории переписки и бизнес-информации о клиенте.
    
    Args:
        incoming_letter: Текст текущего письма от клиента
        letters_history: Список предыдущих писем клиента (опционально).
                        Каждый элемент должен быть словарем с ключами:
                        'content' (текст письма), 'response' (ответ банка, если есть),
                        'created_at' (дата создания)
        business_info: Словарь с бизнес-информацией о клиенте (опционально).
                      Например, {"has_credit_card": True, "has_mortgage": False}
    
    Returns:
        Сгенерированный ответ
    """
    email_analisys = await analyze_mail(incoming_letter)
    email_type = email_analisys.get("email_type", "OTHER")
    specialization = email_analisys.get("specialization", None)
    
    # Получаем релевантный контекст из базы знаний ПСБ
    rag_context = await get_rag_context(incoming_letter)
    
    # Форматируем историю переписки, если она есть
    history_context = ""
    if letters_history:
        history_context = format_letter_history(letters_history)
        print(f"[HISTORY] Используется история из {len(letters_history)} предыдущих писем")
        if history_context:
            print(f"[HISTORY] История сформирована ({len(history_context)} символов)")
    
    # Форматируем бизнес-информацию, если она есть
    business_info_context = ""
    if business_info:
        business_info_context = format_business_info_context(business_info)
        if business_info_context:
            print(f"[BIZ_INFO] Используется бизнес-информация о клиенте")
            print(f"[BIZ_INFO] Информация: {business_info}")
    
    # Логируем для отладки
    if rag_context:
        print(f"[RAG] Извлечен контекст ({len(rag_context)} символов):")
        print(f"[RAG] Первые 200 символов: {rag_context[:200]}...")
    else:
        print("[RAG] ВНИМАНИЕ: Контекст из базы знаний не извлечен!")
    
    # Объединяем контексты
    full_context = history_context
    if business_info_context:
        full_context = (full_context + "\n" + business_info_context) if full_context else business_info_context
    
    instruction = get_generation_promt(email_type, rag_context, specialization, full_context)
    r = await generate_mail(incoming_letter, instructions=instruction)
    return r