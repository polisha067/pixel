from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models import MailRequest, EmailResponse
from ai_funcs import generate_answer
import uvicorn
import os


app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(tags=["MailRequest"])

app.include_router(router)

# Получаем путь к frontend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

# Выводим информацию для отладки
print(f"BASE_DIR: {BASE_DIR}")
print(f"FRONTEND_DIR: {FRONTEND_DIR}")
print(f"Frontend exists: {os.path.exists(FRONTEND_DIR)}")

# Монтируем статические файлы (CSS, JS)
if os.path.exists(FRONTEND_DIR):
    try:
        app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
        print(f"Static files mounted from: {FRONTEND_DIR}")
    except Exception as e:
        print(f"Error mounting static files: {e}")
else:
    print(f"WARNING: Frontend directory not found at {FRONTEND_DIR}")

@app.get('/')
async def root():
    # Возвращаем HTML страницу вместо JSON
    index_path = os.path.join(FRONTEND_DIR, 'index.html')
    print(f"Looking for index.html at: {index_path}")
    print(f"Index exists: {os.path.exists(index_path)}")
    
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type='text/html')
    else:
        # Если файл не найден, возвращаем простую HTML страницу с информацией
        return {
            'error': 'Frontend files not found',
            'frontend_dir': FRONTEND_DIR,
            'index_path': index_path,
            'base_dir': BASE_DIR
        }

@app.post('/mail_generator', response_model=EmailResponse)
async def mail_generator(request: MailRequest):
    try:
        print(f"Received request to generate email. Email length: {len(request.email)}")
        generated_letter = await generate_answer(request.email)
        print(f"Email generated successfully. Length: {len(generated_letter)}")
        return EmailResponse(content=generated_letter)
    except ValueError as e:
        # Ошибка с переменными окружения
        print(f"Configuration error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Configuration error: {str(e)}. Please check your .env file."
        )
    except Exception as e:
        # Другие ошибки
        error_msg = str(e)
        print(f"Error generating email: {error_msg}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating email: {error_msg}"
        )

if __name__ == '__main__':
    print("Starting FastAPI server on http://127.0.0.1:8001")
    print("Frontend should be available at http://localhost:8001")
    try:
        uvicorn.run(app, host='127.0.0.1', port=8001, log_level='info')
    except Exception as e:
        print(f"Error starting server: {e}")
        raise