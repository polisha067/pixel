from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from models import (
    MailRequest, EmailResponse, UserRegister, UserLogin, 
    LetterCreate, LetterResponse, LetterListResponse, StatsResponse,
    User, Letter, UserType, LetterStatus
)
from ai_funcs import generate_mail, analyze_mail
from database import get_db, init_db, verify_password, get_password_hash
import uvicorn
import os
from datetime import datetime

app = FastAPI()

# Глобальный обработчик исключений для возврата JSON вместо HTML
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    error_msg = str(exc)
    print(f"[ERROR] Unhandled exception: {error_msg}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {error_msg}"}
    )

# Инициализация базы данных
try:
    print("[INIT] Initializing database...")
    init_db()
    print("[INIT] Database initialized successfully")
except Exception as e:
    print(f"[INIT] Error initializing database: {str(e)}")
    import traceback
    traceback.print_exc()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Получаем путь к frontend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
print(f"[INIT] Frontend directory: {FRONTEND_DIR}")
print(f"[INIT] Frontend exists: {os.path.exists(FRONTEND_DIR)}")
if os.path.exists(FRONTEND_DIR):
    files = os.listdir(FRONTEND_DIR)
    print(f"[INIT] Frontend files: {files}")
    # Проверяем наличие HTML файлов
    html_files = [f for f in files if f.endswith('.html')]
    print(f"[INIT] HTML files found: {html_files}")

# Простая система сессий (в продакшене использовать JWT)
user_sessions = {}

# Главная страница
@app.get('/')
async def root():
    index_path = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type='text/html')
    return {"message": "Frontend not found"}

# Маршруты для HTML страниц (должны быть ДО монтирования StaticFiles)
@app.get('/register-client.html')
async def register_client():
    path = os.path.join(FRONTEND_DIR, 'register-client.html')
    print(f"[DEBUG] register-client.html requested")
    print(f"[DEBUG] Looking for register-client.html at: {path}")
    print(f"[DEBUG] File exists: {os.path.exists(path)}")
    if os.path.exists(path):
        print(f"[DEBUG] Returning file: {path}")
        return FileResponse(path, media_type='text/html')
    print(f"[DEBUG] File NOT found at: {path}")
    raise HTTPException(status_code=404, detail=f"Page not found at {path}")

@app.get('/register-employee.html')
async def register_employee():
    path = os.path.join(FRONTEND_DIR, 'register-employee.html')
    if os.path.exists(path):
        return FileResponse(path, media_type='text/html')
    raise HTTPException(status_code=404, detail="Page not found")

@app.get('/login.html')
async def login_page():
    path = os.path.join(FRONTEND_DIR, 'login.html')
    if os.path.exists(path):
        return FileResponse(path, media_type='text/html')
    raise HTTPException(status_code=404, detail="Page not found")

@app.get('/client-dashboard.html')
async def client_dashboard():
    path = os.path.join(FRONTEND_DIR, 'client-dashboard.html')
    if os.path.exists(path):
        return FileResponse(path, media_type='text/html')
    raise HTTPException(status_code=404, detail="Page not found")

@app.get('/employee-dashboard.html')
async def employee_dashboard():
    path = os.path.join(FRONTEND_DIR, 'employee-dashboard.html')
    if os.path.exists(path):
        return FileResponse(path, media_type='text/html')
    raise HTTPException(status_code=404, detail="Page not found")

# Монтируем статические файлы (CSS, JS) ПОСЛЕ маршрутов для HTML
# Важно: это должно быть ПОСЛЕ всех @app.get маршрутов для HTML страниц
if os.path.exists(FRONTEND_DIR):
    print(f"[INIT] Mounting static files from: {FRONTEND_DIR}")
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    print(f"[INIT] Static files mounted successfully")
else:
    print(f"[INIT] WARNING: Frontend directory not found, static files not mounted")

# Регистрация
@app.post('/api/register')
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    try:
        print(f"[REGISTER] Attempting to register user: {user_data.username}")
        
        # Проверка существующего пользователя
        existing_user = db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()
        if existing_user:
            print(f"[REGISTER] User already exists: {user_data.username}")
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Проверка типа пользователя
        if user_data.user_type not in ["client", "employee"]:
            print(f"[REGISTER] Invalid user type: {user_data.user_type}")
            raise HTTPException(status_code=400, detail="Invalid user type")
        
        # Хеширование пароля
        try:
            password_hash = get_password_hash(user_data.password)
            print(f"[REGISTER] Password hashed successfully")
        except Exception as e:
            print(f"[REGISTER] Error hashing password: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing password: {str(e)}")
        
        # Создание пользователя
        try:
            new_user = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=password_hash,
                user_type=UserType(user_data.user_type)
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            print(f"[REGISTER] User created successfully: {new_user.id}")
        except Exception as e:
            db.rollback()
            print(f"[REGISTER] Database error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        return {"message": "User registered successfully", "user_id": new_user.id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[REGISTER] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Авторизация
@app.post('/api/login')
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    try:
        print(f"[LOGIN] Attempting login for: {credentials.username}")
        user = db.query(User).filter(User.username == credentials.username).first()
        if not user:
            print(f"[LOGIN] User not found: {credentials.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not verify_password(credentials.password, user.password_hash):
            print(f"[LOGIN] Invalid password for: {credentials.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Простая сессия (в продакшене использовать JWT)
        session_id = f"{user.id}_{datetime.now().timestamp()}"
        user_sessions[session_id] = user.id
        print(f"[LOGIN] Login successful: {credentials.username}, session: {session_id}")
        
        return {
            "message": "Login successful",
            "session_id": session_id,
            "user_type": user.user_type.value,
            "user_id": user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[LOGIN] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Получить текущего пользователя
def get_current_user(session_id: str, db: Session = Depends(get_db)):
    if session_id not in user_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = user_sessions[session_id]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Клиент: отправить письмо
@app.post('/api/letters')
async def create_letter(
    letter_data: LetterCreate,
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    user = get_current_user(session_id, db)
    if user.user_type != UserType.CLIENT:
        raise HTTPException(status_code=403, detail="Only clients can create letters")
    
    new_letter = Letter(
        content=letter_data.content,
        status=LetterStatus.PENDING,
        author_id=user.id
    )
    db.add(new_letter)
    db.commit()
    db.refresh(new_letter)
    
    return {
        "message": "Letter created successfully",
        "letter_id": new_letter.id
    }

# Клиент: получить свои письма
@app.get('/api/letters/my', response_model=LetterListResponse)
async def get_my_letters(
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    user = get_current_user(session_id, db)
    if user.user_type != UserType.CLIENT:
        raise HTTPException(status_code=403, detail="Only clients can view their letters")
    
    letters = db.query(Letter).filter(Letter.author_id == user.id).order_by(Letter.created_at.desc()).all()
    
    letter_responses = [
        LetterResponse(
            id=letter.id,
            content=letter.content,
            status=letter.status.value,
            response=letter.response,
            created_at=letter.created_at.isoformat(),
            updated_at=letter.updated_at.isoformat()
        )
        for letter in letters
    ]
    
    return LetterListResponse(letters=letter_responses)

# Клиент: одобрить ответ
@app.post('/api/letters/{letter_id}/approve')
async def approve_letter(
    letter_id: int,
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    user = get_current_user(session_id, db)
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")
    
    if letter.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not your letter")
    
    if letter.status != LetterStatus.RESPONSE_READY:
        raise HTTPException(status_code=400, detail="Letter is not ready for approval")
    
    letter.status = LetterStatus.COMPLETED
    db.commit()
    
    return {"message": "Letter approved and completed"}

# Сотрудник: получить все письма
@app.get('/api/letters/all', response_model=LetterListResponse)
async def get_all_letters(
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    user = get_current_user(session_id, db)
    if user.user_type != UserType.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Only employees can view all letters")
    
    letters = db.query(Letter).order_by(Letter.created_at.desc()).all()
    
    letter_responses = [
        LetterResponse(
            id=letter.id,
            content=letter.content,
            status=letter.status.value,
            response=letter.response,
            created_at=letter.created_at.isoformat(),
            updated_at=letter.updated_at.isoformat()
        )
        for letter in letters
    ]
    
    return LetterListResponse(letters=letter_responses)

# Сотрудник: взять письмо в работу
@app.post('/api/letters/{letter_id}/take')
async def take_letter(
    letter_id: int,
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    user = get_current_user(session_id, db)
    if user.user_type != UserType.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Only employees can take letters")
    
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")
    
    if letter.status != LetterStatus.PENDING:
        raise HTTPException(status_code=400, detail="Letter is not available")
    
    letter.status = LetterStatus.IN_WORK
    letter.employee_id = user.id
    db.commit()
    
    return {"message": "Letter taken in work"}

# Сотрудник: обработать письмо (генерировать ответ)
@app.post('/api/letters/{letter_id}/process')
async def process_letter(
    letter_id: int,
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    user = get_current_user(session_id, db)
    if user.user_type != UserType.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Only employees can process letters")
    
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")
    
    if letter.status != LetterStatus.IN_WORK or letter.employee_id != user.id:
        raise HTTPException(status_code=400, detail="Letter is not in your work")
    
    try:
        # Генерация ответа через нейронку
        generated_response = await generate_answer(letter.content)
        letter.response = generated_response
        letter.status = LetterStatus.RESPONSE_READY
        db.commit()
        
        return {
            "message": "Letter processed successfully",
            "response": generated_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing letter: {str(e)}")

# Статистика завершенных писем
@app.get('/api/stats', response_model=StatsResponse)
async def get_stats(
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    user = get_current_user(session_id, db)
    if user.user_type != UserType.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Only employees can view stats")
    
    total_completed = db.query(Letter).filter(Letter.status == LetterStatus.COMPLETED).count()
    
    return StatsResponse(total_completed=total_completed)

# Старый endpoint для совместимости
async def generate_answer(incoming_letter):
    email_type = await analyze_mail(incoming_letter)
    r = await generate_mail(incoming_letter, instructions=f"Write a {email_type} letter answering to this, you are employee in the bank PSB.")
    return r

@app.post('/mail_generator', response_model=EmailResponse)
async def mail_generator(request: MailRequest):
    try:
        generated_letter = await generate_answer(request.email)
        return EmailResponse(content=generated_letter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating email: {str(e)}")

if __name__ == '__main__':
    print("=" * 50)
    print("Starting FastAPI server on http://0.0.0.0:8001")
    print(f"[INIT] Current working directory: {os.getcwd()}")
    print(f"[INIT] Script location: {__file__}")
    print(f"[INIT] BASE_DIR: {BASE_DIR}")
    print(f"[INIT] FRONTEND_DIR: {FRONTEND_DIR}")
    print("=" * 50)
    # Выводим все зарегистрированные маршруты
    print("\n[INIT] Registered routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"  {list(route.methods)} {route.path}")
    print("=" * 50)
    uvicorn.run(app, host='127.0.0.1', port=8001, log_level='info')