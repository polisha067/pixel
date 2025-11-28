"""
Pydantic схемы для валидации данных писем.

Схемы для работы с письмами/обращениями:
- Создание письма
- Обновление письма
- Ответы API с информацией о письме
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from backend.database.models import LetterStatus


class LetterCreate(BaseModel):
    """
    Схема для создания нового письма.
    
    Используется когда пользователь отправляет обращение.
    Требует только текст письма - категория определяется автоматически.
    """
    text: str  # Текст обращения от пользователя


class LetterUpdate(BaseModel):
    """
    Схема для обновления письма.
    
    Используется для обновления статуса или ответа.
    Все поля опциональны - можно обновить только нужные.
    """
    status: Optional[LetterStatus] = None
    draft_response: Optional[str] = None
    final_response: Optional[str] = None


class LetterResponse(BaseModel):
    """
    Схема для ответа API с информацией о письме.
    
    Используется когда API возвращает данные письма.
    Включает всю информацию: текст, категорию, статус, ответы.
    """
    id: int
    text: str
    category: str
    status: LetterStatus
    user_id: int
    employee_id: Optional[int]
    draft_response: Optional[str]
    final_response: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LetterWithUserResponse(LetterResponse):
    """
    Расширенная схема письма с информацией о пользователе.
    
    Включает информацию об отправителе письма.
    """
    user_name: Optional[str] = None  # Имя пользователя-отправителя
    
    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    """
    Схема для создания сообщения в чате редактирования.
    
    Используется когда сотрудник отправляет сообщение в чат
    для редактирования ответа.
    """
    message: str  # Текст сообщения от сотрудника


class ChatMessageResponse(BaseModel):
    """
    Схема для ответа API с информацией о сообщении в чате.
    """
    id: int
    letter_id: int
    role: str  # "employee" или "assistant"
    message: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """
    Схема для ответа API при отправке сообщения в чат.
    
    Включает:
    - Улучшенный ответ от нейросети
    - Обновленный черновик ответа
    """
    improved_response: str  # Улучшенный ответ от нейросети
    updated_draft: str  # Обновленный черновик в письме


class FinalResponseCreate(BaseModel):
    """
    Схема для отправки финального ответа.
    
    Используется когда сотрудник отправляет финальный ответ пользователю.
    """
    final_response: str  # Финальный текст ответа

