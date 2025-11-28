"""
API эндпоинты для сотрудников банка.

Этот модуль содержит эндпоинты для:
- Просмотра назначенных писем
- Работы с письмом (открытие, редактирование)
- Чата с нейросетью для редактирования ответа
- Отправки финального ответа пользователю
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database.database import get_db
from backend.database import crud
from backend.database.models import LetterStatus
from backend.schemas.letter import (
    LetterResponse, 
    ChatMessageCreate, 
    ChatMessageResponse,
    ChatResponse,
    FinalResponseCreate
)
from backend.services.yandex_ai import send_request_with_context

# Создаем роутер для эндпоинтов сотрудников
router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.get("/letters", response_model=List[LetterResponse])
def get_employee_letters(
    employee_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Получить все письма, назначенные сотруднику.
    
    Сотрудник видит только письма, которые назначены ему
    (по его категории услуг).
    
    Можно фильтровать по статусу:
    - waiting - ожидающие обработки
    - in_progress - в работе
    - sent - отправленные
    
    Args:
        employee_id: ID сотрудника
        status: Фильтр по статусу (опционально)
        db: Сессия базы данных
    
    Returns:
        List[LetterResponse]: Список писем сотрудника
    """
    # Проверяем, что сотрудник существует
    employee = crud.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    
    # Преобразуем строковый статус в enum (если указан)
    status_enum = None
    if status:
        try:
            status_enum = LetterStatus[status.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Неверный статус: {status}")
    
    # Получаем письма сотрудника
    letters = crud.get_letters_by_employee(db, employee_id, status_enum)
    
    # Сортируем по дате создания (новые первыми)
    letters.sort(key=lambda x: x.created_at, reverse=True)
    
    return letters


@router.get("/letters/{letter_id}", response_model=LetterResponse)
def get_employee_letter(letter_id: int, employee_id: int, db: Session = Depends(get_db)):
    """
    Получить конкретное письмо для работы.
    
    Когда сотрудник открывает письмо:
    1. Статус меняется на "in_progress" (если был "waiting")
    2. Возвращается письмо с черновиком ответа
    
    Args:
        letter_id: ID письма
        employee_id: ID сотрудника (для проверки прав доступа)
        db: Сессия базы данных
    
    Returns:
        LetterResponse: Письмо с черновиком ответа
    
    Raises:
        HTTPException: Если письмо не найдено или не назначено сотруднику
    """
    # Получаем письмо
    letter = crud.get_letter_by_id(db, letter_id)
    
    if not letter:
        raise HTTPException(status_code=404, detail="Письмо не найдено")
    
    # Проверяем, что письмо назначено этому сотруднику
    if letter.employee_id != employee_id:
        raise HTTPException(status_code=403, detail="Письмо не назначено вам")
    
    # Если письмо в статусе "waiting", меняем на "in_progress"
    if letter.status == LetterStatus.WAITING:
        crud.update_letter_status(db, letter_id, LetterStatus.IN_PROGRESS)
        db.refresh(letter)
    
    return letter


@router.post("/letters/{letter_id}/chat", response_model=ChatResponse)
def send_chat_message(
    letter_id: int,
    employee_id: int,
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db)
):
    """
    Отправить сообщение в чат для редактирования ответа.
    
    Это ключевой эндпоинт для редактирования ответов!
    
    Когда сотрудник хочет изменить ответ, он пишет в чат:
    "Сделай ответ более вежливым" или "Добавь информацию о документах"
    
    Нейросеть:
    1. Анализирует просьбу сотрудника
    2. Учитывает исходное письмо и текущий черновик
    3. Учитывает историю чата
    4. Генерирует улучшенный ответ
    5. Обновляет черновик в письме
    
    Args:
        letter_id: ID письма
        employee_id: ID сотрудника
        message_data: Сообщение от сотрудника
        db: Сессия базы данных
    
    Returns:
        ChatResponse: Улучшенный ответ от нейросети
    
    Raises:
        HTTPException: Если письмо не найдено или не назначено сотруднику
    """
    # Получаем письмо
    letter = crud.get_letter_by_id(db, letter_id)
    
    if not letter:
        raise HTTPException(status_code=404, detail="Письмо не найдено")
    
    # Проверяем права доступа
    if letter.employee_id != employee_id:
        raise HTTPException(status_code=403, detail="Письмо не назначено вам")
    
    try:
        # ========== ШАГ 1: Сохраняем сообщение сотрудника ==========
        crud.create_chat_message(
            db=db,
            letter_id=letter_id,
            role="employee",
            message=message_data.message
        )
        
        # ========== ШАГ 2: Получаем историю чата ==========
        # История нужна для контекста - нейросеть видит предыдущие сообщения
        chat_history = crud.get_chat_messages_by_letter(db, letter_id)
        
        # Формируем текст истории для промпта
        history_text = ""
        for msg in chat_history:
            role_name = "Сотрудник" if msg.role == "employee" else "Ассистент"
            history_text += f"{role_name}: {msg.message}\n"
        
        # ========== ШАГ 3: Формируем промпт для нейросети ==========
        system_instruction = """Ты - помощник для редактирования ответов банка.
Твоя задача - улучшать ответы на основе просьб сотрудника, сохраняя корпоративный стиль и юридическую корректность."""
        
        context = f"""Исходное письмо от клиента:
{letter.text}

Текущий черновик ответа:
{letter.draft_response or "Черновик еще не создан"}

История редактирования:
{history_text if history_text else "Истории пока нет"}"""
        
        prompt = f"""Сотрудник просит: {message_data.message}

Предложи улучшенную версию ответа, учитывая просьбу сотрудника.
Сохрани корпоративный стиль банка, юридическую корректность и вежливый тон."""
        
        # ========== ШАГ 4: Отправляем запрос к нейросети ==========
        print(f"💬 Обрабатываю запрос сотрудника для письма {letter_id}...")
        improved_response = send_request_with_context(
            prompt=prompt,
            context=context,
            system_instruction=system_instruction,
            temperature=0.7
        )
        print(f"✅ Получен улучшенный ответ")
        
        # ========== ШАГ 5: Сохраняем ответ ассистента в чат ==========
        crud.create_chat_message(
            db=db,
            letter_id=letter_id,
            role="assistant",
            message=improved_response
        )
        
        # ========== ШАГ 6: Обновляем черновик в письме ==========
        crud.update_letter_draft_response(db, letter_id, improved_response)
        
        return ChatResponse(
            improved_response=improved_response,
            updated_draft=improved_response
        )
    
    except Exception as e:
        print(f"❌ Ошибка при обработке сообщения в чате: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке запроса: {str(e)}")


@router.get("/letters/{letter_id}/chat", response_model=List[ChatMessageResponse])
def get_chat_messages(letter_id: int, employee_id: int, db: Session = Depends(get_db)):
    """
    Получить историю чата для письма.
    
    Возвращает все сообщения в чате редактирования:
    - Сообщения сотрудника
    - Ответы нейросети
    
    Args:
        letter_id: ID письма
        employee_id: ID сотрудника
        db: Сессия базы данных
    
    Returns:
        List[ChatMessageResponse]: История чата
    """
    # Проверяем права доступа
    letter = crud.get_letter_by_id(db, letter_id)
    if not letter:
        raise HTTPException(status_code=404, detail="Письмо не найдено")
    
    if letter.employee_id != employee_id:
        raise HTTPException(status_code=403, detail="Письмо не назначено вам")
    
    # Получаем историю чата
    messages = crud.get_chat_messages_by_letter(db, letter_id)
    
    return messages


@router.post("/letters/{letter_id}/send")
def send_final_response(
    letter_id: int,
    employee_id: int,
    response_data: FinalResponseCreate,
    db: Session = Depends(get_db)
):
    """
    Отправить финальный ответ пользователю.
    
    Когда сотрудник закончил редактирование и готов отправить ответ:
    1. Сохраняется финальный ответ
    2. Статус меняется на "sent"
    3. Пользователь может увидеть ответ
    
    Args:
        letter_id: ID письма
        employee_id: ID сотрудника
        response_data: Данные с финальным ответом
        db: Сессия базы данных
    
    Returns:
        dict: Сообщение об успехе
    
    Raises:
        HTTPException: Если письмо не найдено или не назначено сотруднику
    """
    # Проверяем права доступа
    letter = crud.get_letter_by_id(db, letter_id)
    if not letter:
        raise HTTPException(status_code=404, detail="Письмо не найдено")
    
    if letter.employee_id != employee_id:
        raise HTTPException(status_code=403, detail="Письмо не назначено вам")
    
    # Обновляем письмо: устанавливаем финальный ответ и статус "sent"
    crud.update_letter_final_response(db, letter_id, response_data.final_response)
    
    print(f"✅ Письмо {letter_id}: финальный ответ отправлен пользователю")
    
    return {"message": "Ответ успешно отправлен пользователю", "letter_id": letter_id}

