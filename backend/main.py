from fastapi import FastAPI, APIRouter, HTTPException
from models import MailRequest, EmailResponse
from fastapi.middleware.cors import CORSMiddleware
from ai_funcs import generate_mail, analyze_mail, generate_answer
import uvicorn


app = FastAPI()

router = APIRouter(tags=["MailRequest"])

app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:8000", "http://127.0.0.1:8000", "http://127.0.0.1:8001", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
async def root():
    return {'message': 'This is our project'}

@app.post('/mail_generator', response_model=EmailResponse)
async def mail_generator(request: MailRequest):
    try:
        generated_letter = await generate_answer(request.email)
        return EmailResponse(content=generated_letter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating email: {str(e)}")

if __name__ == '__main__':
    uvicorn.run("main:app", host='127.0.0.1', port=8001)