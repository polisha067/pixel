from fastapi import APIRouter, HTTPException, Depends, Header, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from models import (
    MailRequest, EmailResponse, UserRegister, UserLogin, 
    LetterCreate, LetterResponse, LetterListResponse, StatsResponse,
    LetterUpdateResponse, User, Letter, UserType, LetterStatus, EmailType, get_msk_now, MSK_TZ
)
from ai_funcs import generate_answer, analyze_mail, extract_business_info
from database import get_db
from funcs import (
    get_current_user, save_business_info, get_user_business_info,
    get_client_letter_history, user_sessions, check_employee_role
)
from datetime import datetime, timedelta
from sqlalchemy import or_
import os

# Создаем роутеры
router = APIRouter()

# Получаем путь к frontend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')


# ==================== HTML СТРАНИЦЫ ====================

@router.get('/')
async def root():
    """Главная страница"""
    index_path = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type='text/html')
    return {"message": "Frontend not found"}


@router.get('/register-client.html')
async def register_client():
    """Страница регистрации клиента"""
    path = os.path.join(FRONTEND_DIR, 'register-client.html')
    print(f"[DEBUG] register-client.html requested")
    print(f"[DEBUG] Looking for register-client.html at: {path}")
    print(f"[DEBUG] File exists: {os.path.exists(path)}")
    if os.path.exists(path):
        print(f"[DEBUG] Returning file: {path}")
        return FileResponse(path, media_type='text/html')
    print(f"[DEBUG] File NOT found at: {path}")
    raise HTTPException(status_code=404, detail=f"Page not found at {path}")


@router.get('/register-employee.html')
async def register_employee():
    """Страница регистрации сотрудника"""
    path = os.path.join(FRONTEND_DIR, 'register-employee.html')
    if os.path.exists(path):
        return FileResponse(path, media_type='text/html')
    raise HTTPException(status_code=404, detail="Page not found")


@router.get('/login.html')
async def login_page():
    """Страница входа"""
    path = os.path.join(FRONTEND_DIR, 'login.html')
    if os.path.exists(path):
        return FileResponse(path, media_type='text/html')
    raise HTTPException(status_code=404, detail="Page not found")


@router.get('/client-dashboard.html')
async def client_dashboard():
    """Дашборд клиента"""
    path = os.path.join(FRONTEND_DIR, 'client-dashboard.html')
    if os.path.exists(path):
        return FileResponse(path, media_type='text/html')
    raise HTTPException(status_code=404, detail="Page not found")


@router.get('/employee-dashboard.html')
async def employee_dashboard():
    """Дашборд сотрудника"""
    path = os.path.join(FRONTEND_DIR, 'employee-dashboard.html')
    if os.path.exists(path):
        return FileResponse(path, media_type='text/html')
    raise HTTPException(status_code=404, detail="Page not found")


# ==================== API РОУТЕРЫ ====================

@router.get('/api/health')
async def health_check():
    """Health check endpoint для Docker"""
    return {"status": "ok", "message": "Server is running"}


@router.post('/api/register')
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    try:
        # Получаем имя и фамилию
        first_name = user_data.first_name.strip() if hasattr(user_data, 'first_name') and user_data.first_name else None
        last_name = user_data.last_name.strip() if hasattr(user_data, 'last_name') and user_data.last_name else None
        
        # Формируем username из имени и фамилии
        if first_name and last_name:
            base_username = f"{first_name} {last_name}"
            username = base_username
            # Проверяем, не существует ли уже пользователь с таким username
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username} {counter}"
                counter += 1
        elif hasattr(user_data, 'username') and user_data.username:
            # Для обратной совместимости
            username = user_data.username
        else:
            raise HTTPException(status_code=400, detail="Имя и фамилия обязательны для заполнения")
        
        print(f"[REGISTER] Attempting to register user: {username} ({first_name} {last_name})")
        
        # Проверка существующего пользователя по email
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            print(f"[REGISTER] User with email already exists: {user_data.email}")
            raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
        
        # Проверка типа пользователя
        if user_data.user_type not in ["client", "employee"]:
            print(f"[REGISTER] Invalid user type: {user_data.user_type}")
            raise HTTPException(status_code=400, detail="Invalid user type")
        
        # Хеширование пароля
        try:
            from database import get_password_hash
            password_hash = get_password_hash(user_data.password)
            print(f"[REGISTER] Password hashed successfully")
        except Exception as e:
            print(f"[REGISTER] Error hashing password: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing password: {str(e)}")
        
        # Создание пользователя
        try:
            # Используем specialization, если указано, иначе classification (для обратной совместимости)
            specialization = user_data.specialization if hasattr(user_data, 'specialization') and user_data.specialization else user_data.classification
            
            new_user = User(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=user_data.email,
                password_hash=password_hash,
                user_type=UserType(user_data.user_type),
                specialization=specialization if user_data.user_type == "employee" else None,
                classification=user_data.classification if user_data.user_type == "employee" else None  # Для обратной совместимости
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


@router.post('/api/login')
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Авторизация пользователя"""
    try:
        login_input = credentials.username.strip()
        print(f"[LOGIN] Attempting login for: {login_input}")
        
        # Пытаемся найти пользователя по username или email
        user = db.query(User).filter(
            (User.username == login_input) | (User.email == login_input)
        ).first()
        
        if not user:
            print(f"[LOGIN] User not found: {login_input}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        from database import verify_password
        if not verify_password(credentials.password, user.password_hash):
            print(f"[LOGIN] Invalid password for: {login_input}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Простая сессия (в продакшене использовать JWT)
        session_id = f"{user.id}_{get_msk_now().timestamp()}"
        user_sessions[session_id] = user.id
        print(f"[LOGIN] Login successful: {login_input} (user: {user.username}), session: {session_id}")
        
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


@router.post('/api/letters')
async def create_letter(
    letter_data: LetterCreate,
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    """Клиент: отправить письмо"""
    user = get_current_user(session_id, db)
    if user.user_type != UserType.CLIENT:
        raise HTTPException(status_code=403, detail="Only clients can create letters")
    
    # Получаем текущую дату создания письма
    created_at = get_msk_now()
    
    # Анализируем письмо для определения классификации, специализации и дедлайна
    email_type = None
    specialization = None
    deadline = None
    assigned_employee_id = None
    
    try:
        analysis = await analyze_mail(letter_data.content)
        email_type_str = analysis.get("email_type")
        specialization_str = analysis.get("specialization")
        deadline_str = analysis.get("deadline")
        
        if email_type_str:
            try:
                email_type = EmailType(email_type_str)
            except ValueError:
                email_type = EmailType.OTHER
        
        if specialization_str:
            specialization = specialization_str
        
        # Если дедлайн указан в письме, используем его
        if deadline_str:
            try:
                # Парсим дату в формате ГГГГ-ММ-ДД
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
                # Устанавливаем время на конец дня в MSK
                deadline = deadline.replace(hour=23, minute=59, second=59)
                if MSK_TZ:
                    # Для pytz используем localize, для zoneinfo просто replace
                    if hasattr(MSK_TZ, 'localize'):
                        deadline = MSK_TZ.localize(deadline)
                    else:
                        deadline = deadline.replace(tzinfo=MSK_TZ)
            except (ValueError, TypeError) as e:
                print(f"[LETTER] Error parsing deadline: {e}")
                deadline = None
        
        # Если дедлайн не указан в письме или не удалось распарсить, устанавливаем 10 дней от даты создания
        if deadline is None:
            deadline = created_at + timedelta(days=10)
            # Устанавливаем время на конец дня
            deadline = deadline.replace(hour=23, minute=59, second=59)
            print(f"[LETTER] Deadline not specified, setting to 10 days from creation: {deadline}")
        
        # Автоматически назначаем письмо соответствующему специалисту
        if specialization:
            # Ищем сотрудника с соответствующей специализацией
            employees = db.query(User).filter(
                User.user_type == UserType.EMPLOYEE,
                User.specialization.isnot(None)
            ).all()
            
            for employee in employees:
                if employee.specialization:
                    # Специализация может быть через запятую (несколько)
                    specializations = [s.strip() for s in employee.specialization.split(',')]
                    if specialization in specializations:
                        assigned_employee_id = employee.id
                        print(f"[LETTER] Auto-assigned to employee {employee.id} with specialization {specialization}")
                        break
            
            # Если не нашли по specialization, пробуем по старому полю classification
            if not assigned_employee_id:
                employees = db.query(User).filter(
                    User.user_type == UserType.EMPLOYEE,
                    User.classification.isnot(None)
                ).all()
                
                for employee in employees:
                    if employee.classification:
                        classifications = [c.strip() for c in employee.classification.split(',')]
                        if email_type and email_type.value in classifications:
                            assigned_employee_id = employee.id
                            print(f"[LETTER] Auto-assigned to employee {employee.id} by classification")
                            break
            
    except Exception as e:
        print(f"[LETTER] Error analyzing letter: {e}")
        import traceback
        traceback.print_exc()
        # Продолжаем создание письма даже если анализ не удался
        email_type = EmailType.OTHER
        specialization = "Прочее"
        # Устанавливаем дедлайн 10 дней от даты создания
        deadline = created_at + timedelta(days=10)
        deadline = deadline.replace(hour=23, minute=59, second=59)
        print(f"[LETTER] Analysis failed, setting default deadline: {deadline}")
    
    # Если специализация не определена, устанавливаем "Прочее"
    if not specialization:
        specialization = "Прочее"
    
    # Если письмо назначено сотруднику, сразу ставим статус IN_WORK
    status = LetterStatus.IN_WORK if assigned_employee_id else LetterStatus.PENDING
    
    new_letter = Letter(
        content=letter_data.content,
        status=status,
        author_id=user.id,
        email_type=email_type,
        specialization=specialization,
        employee_id=assigned_employee_id,
        deadline=deadline,
        created_at=created_at  # Явно устанавливаем дату создания
    )
    db.add(new_letter)
    db.commit()
    db.refresh(new_letter)
    
    # Извлекаем и сохраняем важную бизнес-информацию из письма
    try:
        business_info = await extract_business_info(letter_data.content)
        if business_info:
            save_business_info(user.id, business_info, new_letter.id, db)
            print(f"[LETTER] Сохранена бизнес-информация для пользователя {user.id}")
    except Exception as e:
        print(f"[LETTER] Ошибка при извлечении бизнес-информации: {e}")
        import traceback
        traceback.print_exc()
        # Продолжаем работу даже если извлечение информации не удалось
    
    return {
        "message": "Letter created successfully",
        "letter_id": new_letter.id,
        "email_type": email_type.value if email_type else None,
        "specialization": specialization,
        "deadline": deadline.isoformat() if deadline else None,
        "assigned_employee_id": assigned_employee_id
    }


@router.get('/api/letters/my', response_model=LetterListResponse)
async def get_my_letters(
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    """Клиент: получить свои письма"""
    user = get_current_user(session_id, db)
    if user.user_type != UserType.CLIENT:
        raise HTTPException(status_code=403, detail="Only clients can view their letters")
    
    letters = db.query(Letter).filter(Letter.author_id == user.id).order_by(Letter.created_at.desc()).all()
    
    letter_responses = [
        LetterResponse(
            id=letter.id,
            content=letter.content,
            status=letter.status.value,
            # Показываем ответ клиенту ТОЛЬКО если письмо одобрено (статус completed)
            response=letter.response if letter.status == LetterStatus.COMPLETED else None,
            employee_id=letter.employee_id,
            email_type=letter.email_type.value if letter.email_type else None,
            specialization=letter.specialization,
            deadline=letter.deadline.isoformat() if letter.deadline else None,
            created_at=letter.created_at.isoformat() if letter.created_at else "",
            updated_at=letter.updated_at.isoformat() if letter.updated_at else ""
        )
        for letter in letters
    ]
    
    return LetterListResponse(letters=letter_responses)


@router.get('/api/letters/all', response_model=LetterListResponse)
async def get_all_letters(
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    """Сотрудник: получить все письма"""
    user = get_current_user(session_id, db)
    if user.user_type != UserType.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Only employees can view all letters")
    
    # Фильтруем письма по специализации сотрудника
    query = db.query(Letter)
    
    # Если у сотрудника указана специализация, фильтруем по ней
    if user.specialization:
        # Специализация может быть через запятую (несколько)
        specializations = [s.strip() for s in user.specialization.split(',')]
        # Фильтруем письма, которые соответствуют специализации сотрудника
        conditions = []
        for spec in specializations:
            conditions.append(Letter.specialization == spec)
        
        if conditions:
            query = query.filter(or_(*conditions))
    # Если специализация не указана, проверяем старое поле classification
    elif user.classification:
        # Классификация может быть через запятую (несколько типов)
        classifications = [c.strip() for c in user.classification.split(',')]
        # Фильтруем письма, которые соответствуют классификации сотрудника или не имеют классификации
        conditions = []
        for cls in classifications:
            try:
                email_type_enum = EmailType(cls)
                conditions.append(Letter.email_type == email_type_enum)
            except ValueError:
                pass  # Пропускаем неверные значения
        
        if conditions:
            query = query.filter(or_(*conditions, Letter.email_type.is_(None)))
    # Если ни специализация, ни классификация не указаны, сотрудник видит все письма
    
    letters = query.order_by(Letter.created_at.desc()).all()
    
    letter_responses = [
        LetterResponse(
            id=letter.id,
            content=letter.content,
            status=letter.status.value,
            response=letter.response,
            employee_id=letter.employee_id,
            email_type=letter.email_type.value if letter.email_type else None,
            specialization=letter.specialization,
            deadline=letter.deadline.isoformat() if letter.deadline else None,
            created_at=letter.created_at.isoformat() if letter.created_at else "",
            updated_at=letter.updated_at.isoformat() if letter.updated_at else ""
        )
        for letter in letters
    ]
    
    return LetterListResponse(letters=letter_responses)


@router.post('/api/letters/{letter_id}/take')
async def take_letter(
    letter_id: int,
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    """Сотрудник: взять письмо в работу"""
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


@router.post('/api/letters/{letter_id}/process')
async def process_letter(
    letter_id: int,
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    """Сотрудник: обработать письмо (генерировать ответ)"""
    user = get_current_user(session_id, db)
    if user.user_type != UserType.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Only employees can process letters")
    
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")
    
    if letter.status != LetterStatus.IN_WORK or letter.employee_id != user.id:
        raise HTTPException(status_code=400, detail="Letter is not in your work")
    
    try:
        # Получаем историю предыдущих писем клиента
        letters_history = get_client_letter_history(letter.author_id, letter.id, db)
        
        # Получаем сохраненную бизнес-информацию о клиенте
        business_info = get_user_business_info(letter.author_id, db)
        
        # Генерация ответа через нейронку с учетом истории переписки и бизнес-информации
        generated_response = await generate_answer(
            letter.content, 
            letters_history=letters_history,
            business_info=business_info if business_info else None
        )
        letter.response = generated_response
        letter.status = LetterStatus.RESPONSE_READY
        letter.updated_at = get_msk_now()
        db.commit()
        
        return {
            "message": "Letter processed successfully",
            "response": generated_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing letter: {str(e)}")


@router.put('/api/letters/{letter_id}/response')
async def update_letter_response(
    letter_id: int,
    response_data: LetterUpdateResponse,
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    """Сотрудник: обновить ответ (редактировать)"""
    user = get_current_user(session_id, db)
    if user.user_type != UserType.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Only employees can update responses")
    
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")
    
    if letter.employee_id != user.id:
        raise HTTPException(status_code=403, detail="Not your letter to update")
    
    if letter.status not in [LetterStatus.IN_WORK, LetterStatus.RESPONSE_READY]:
        raise HTTPException(status_code=400, detail="Letter is not in editable state")
    
    letter.response = response_data.response
    letter.status = LetterStatus.RESPONSE_READY
    letter.updated_at = get_msk_now()
    db.commit()
    
    return {"message": "Response updated successfully"}


@router.post('/api/letters/{letter_id}/regenerate')
async def regenerate_letter_response(
    letter_id: int,
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    """Сотрудник: перегенерировать ответ"""
    user = get_current_user(session_id, db)
    if user.user_type != UserType.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Only employees can regenerate responses")
    
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")
    
    if letter.employee_id != user.id:
        raise HTTPException(status_code=403, detail="Not your letter to regenerate")
    
    if letter.status not in [LetterStatus.IN_WORK, LetterStatus.RESPONSE_READY]:
        raise HTTPException(status_code=400, detail="Letter is not in regeneratable state")
    
    try:
        # Получаем историю предыдущих писем клиента
        letters_history = get_client_letter_history(letter.author_id, letter.id, db)
        
        # Получаем сохраненную бизнес-информацию о клиенте
        business_info = get_user_business_info(letter.author_id, db)
        
        # Генерация нового ответа через нейронку с учетом истории переписки и бизнес-информации
        generated_response = await generate_answer(
            letter.content, 
            letters_history=letters_history,
            business_info=business_info if business_info else None
        )
        letter.response = generated_response
        letter.status = LetterStatus.RESPONSE_READY
        letter.updated_at = get_msk_now()
        db.commit()
        
        return {
            "message": "Response regenerated successfully",
            "response": generated_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating response: {str(e)}")


@router.post('/api/letters/{letter_id}/approve')
async def approve_letter(
    letter_id: int,
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    """Сотрудник: одобрить ответ"""
    user = get_current_user(session_id, db)
    if user.user_type != UserType.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Only employees can approve letters")
    
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    
    if not letter:
        raise HTTPException(status_code=404, detail="Letter not found")
    
    if letter.employee_id != user.id:
        raise HTTPException(status_code=403, detail="Not your letter to approve")
    
    if letter.status != LetterStatus.RESPONSE_READY:
        raise HTTPException(status_code=400, detail="Letter is not ready for approval")
    
    letter.status = LetterStatus.COMPLETED
    db.commit()
    
    return {"message": "Letter approved and completed"}


@router.get('/api/stats', response_model=StatsResponse)
async def get_stats(
    session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    """Статистика завершенных писем"""
    user = get_current_user(session_id, db)
    if user.user_type != UserType.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Only employees can view stats")
    
    total_completed = db.query(Letter).filter(Letter.status == LetterStatus.COMPLETED).count()
    
    return StatsResponse(total_completed=total_completed)


@router.post('/mail_generator', response_model=EmailResponse)
async def mail_generator(request: MailRequest):
    """Генерация письма (legacy endpoint)"""
    try:
        generated_letter = await generate_answer(request.email)
        return EmailResponse(content=generated_letter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating email: {str(e)}")

@router.get("/user/{user_id}", summary="Получить статистику пользователя")
async def get_user_stats(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # Проверяем права доступа текущего пользователя
    check_employee_role(current_user)
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    business_info = get_user_business_info(user_id, db)

    return {
        "user_id": target_user.id,
        "email": target_user.email,
        "first_name": target_user.first_name,
        "last_name": target_user.last_name,
        "role": target_user.role,
        "business_info": business_info,
        "requested_by": {
            "user_id": current_user.id,
            "email": current_user.email
        }
    }