"""
API эндпоинты для авторизации и регистрации.

Этот модуль содержит эндпоинты для:
- Регистрации пользователей
- Регистрации сотрудников
- Простой авторизации (по email)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database import crud
from backend.database.models import UserRole
from backend.schemas.user import UserCreate, UserResponse, EmployeeCreate, EmployeeResponse
from backend.config import settings

# Создаем роутер для эндпоинтов авторизации
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register/user", response_model=UserResponse)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация обычного пользователя (клиента банка).
    
    Создает нового пользователя с ролью "user".
    Пользователь может отправлять обращения в банк.
    
    Args:
        user_data: Данные пользователя (имя, email)
        db: Сессия базы данных
    
    Returns:
        UserResponse: Созданный пользователь
    
    Raises:
        HTTPException: Если пользователь с таким email уже существует
    """
    try:
        # Создаем пользователя через CRUD функцию
        user = crud.create_user(
            db=db,
            name=user_data.name,
            email=user_data.email,
            role=UserRole.USER
        )
        return user
    except ValueError as e:
        # Если пользователь уже существует, возвращаем ошибку
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/register/employee", response_model=EmployeeResponse)
def register_employee(employee_data: EmployeeCreate, db: Session = Depends(get_db)):
    """
    Регистрация сотрудника банка.
    
    Создает пользователя с ролью "employee" и запись сотрудника
    с указанной категорией услуг.
    
    Сотрудник будет получать письма только по своей категории.
    
    Args:
        employee_data: Данные сотрудника (имя, email, отдел, категория)
        db: Сессия базы данных
    
    Returns:
        EmployeeResponse: Созданный сотрудник
    
    Raises:
        HTTPException: Если пользователь уже существует или категория неверна
    """
    # Проверяем, что категория валидна
    if employee_data.category not in settings.BANK_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Неверная категория. Доступные категории: {', '.join(settings.BANK_CATEGORIES)}"
        )
    
    try:
        # Создаем пользователя с ролью employee
        user = crud.create_user(
            db=db,
            name=employee_data.name,
            email=employee_data.email,
            role=UserRole.EMPLOYEE
        )
        
        # Создаем запись сотрудника
        employee = crud.create_employee(
            db=db,
            user_id=user.id,
            department=employee_data.department,
            category=employee_data.category
        )
        
        # Обновляем объект, чтобы включить информацию о пользователе
        db.refresh(employee)
        
        return employee
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=UserResponse)
def login(email: str, db: Session = Depends(get_db)):
    """
    Простая авторизация по email.
    
    В реальном приложении здесь была бы проверка пароля,
    но для хакатона используем упрощенную версию.
    
    Args:
        email: Email пользователя
        db: Сессия базы данных
    
    Returns:
        UserResponse: Пользователь
    
    Raises:
        HTTPException: Если пользователь не найден
    """
    user = crud.get_user_by_email(db, email)
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return user

