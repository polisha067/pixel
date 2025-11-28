"""
Pydantic схемы для валидации данных пользователей.

Pydantic - это библиотека для валидации данных.
Схемы определяют структуру данных, которые принимает и возвращает API.
Они автоматически проверяют типы данных и валидируют их.

Используются в FastAPI для:
- Валидации входящих данных (request body)
- Сериализации исходящих данных (response)
- Автоматической генерации документации API
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from backend.database.models import UserRole


# ========== Схемы для создания ==========

class UserCreate(BaseModel):
    """
    Схема для создания нового пользователя.
    
    Используется при регистрации пользователя.
    Все поля обязательны.
    """
    name: str  # Имя пользователя
    email: EmailStr  # Email (автоматически валидируется)
    role: UserRole = UserRole.USER  # Роль (по умолчанию "user")


class EmployeeCreate(BaseModel):
    """
    Схема для регистрации сотрудника.
    
    Используется когда пользователь регистрируется как сотрудник.
    Требует указания категории услуг, с которой будет работать сотрудник.
    """
    name: str  # Имя сотрудника
    email: EmailStr  # Email
    department: Optional[str] = None  # Название отдела (опционально)
    category: str  # Категория услуг (credit, insurance, mortgage и т.д.)


# ========== Схемы для ответов ==========

class UserResponse(BaseModel):
    """
    Схема для ответа API с информацией о пользователе.
    
    Используется когда API возвращает данные пользователя.
    Не включает секретные данные (пароли и т.д.).
    """
    id: int
    name: str
    email: str
    role: UserRole
    created_at: datetime
    
    # Настройка для работы с SQLAlchemy моделями
    class Config:
        from_attributes = True  # Позволяет создавать из SQLAlchemy моделей


class EmployeeResponse(BaseModel):
    """
    Схема для ответа API с информацией о сотруднике.
    
    Включает информацию о пользователе и его специализации.
    """
    id: int
    user_id: int
    department: Optional[str]
    category: str
    created_at: datetime
    user: UserResponse  # Вложенная информация о пользователе
    
    class Config:
        from_attributes = True

