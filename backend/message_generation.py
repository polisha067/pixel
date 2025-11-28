from openai import OpenAI
from dotenv import load_dotenv
import os

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