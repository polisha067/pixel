from openai import OpenAI
from dotenv import load_dotenv
import os, json
from ai_promts import ANALISYS_PROMT, get_generation_promt

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
    email_type = email_analisys["email_type"]
    instruction = get_generation_promt(email_type)
    r = await generate_mail(incoming_letter, instructions=instruction)
    return r