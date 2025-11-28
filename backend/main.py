from fastapi import FastAPI, APIRouter, HTTPException
from models import MailRequest, EmailResponse
from message_generation import generate_mail
import uvicorn


app = FastAPI()

router = APIRouter(tags=["MailRequest"])

app.include_router(router)

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

def generate_answer(incoming_letter):
    return generate_mail(incoming_letter, instructions="Write a letter answering to this, you are employee in the bank PSB.")

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)