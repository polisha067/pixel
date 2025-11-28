from pydantic import BaseModel

class MailRequest(BaseModel):
    email: str

class EmailResponse(BaseModel):
    content: str