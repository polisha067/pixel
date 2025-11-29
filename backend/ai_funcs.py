from openai import OpenAI
from dotenv import load_dotenv
import os, json
from ai_promts import ANALISYS_PROMT, get_generation_promt
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

async def generate_answer(incoming_letter):
    email_analisys = await analyze_mail(incoming_letter)
    email_type = email_analisys.get("email_type", "OTHER")
    specialization = email_analisys.get("specialization", None)
    
    # Получаем релевантный контекст из базы знаний ПСБ
    rag_context = await get_rag_context(incoming_letter)
    
    # Логируем для отладки
    if rag_context:
        print(f"[RAG] Извлечен контекст ({len(rag_context)} символов):")
        print(f"[RAG] Первые 200 символов: {rag_context[:200]}...")
    else:
        print("[RAG] ВНИМАНИЕ: Контекст из базы знаний не извлечен!")
    
    instruction = get_generation_promt(email_type, rag_context, specialization)
    r = await generate_mail(incoming_letter, instructions=instruction)
    return r