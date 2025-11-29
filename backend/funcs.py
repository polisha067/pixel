from fastapi import HTTPException, Depends, status, Header, APIRouter
from sqlalchemy.orm import Session
from models import User, Letter, LetterStatus, UserBusinessInfo, get_msk_now
from database import get_db

# Простая система сессий (в продакшене использовать JWT)
user_sessions = {}


def get_current_user(
        x_session_id: str = Header(..., alias="X-Session-ID"),
        db: Session = Depends(get_db)
) -> User:
    """Получить текущего пользователя по session_id из заголовка"""
    if x_session_id not in user_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = user_sessions[x_session_id]
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def save_business_info(user_id: int, business_info: dict, letter_id: int, db: Session):
    """
    Сохраняет или обновляет бизнес-информацию о пользователе.
    
    Args:
        user_id: ID пользователя
        business_info: Словарь с информацией (например, {"has_credit_card": true})
        letter_id: ID письма, из которого извлечена информация
        db: Сессия базы данных
    """
    if not business_info:
        return
    
    for info_key, info_value in business_info.items():
        # Проверяем, существует ли уже запись
        existing_info = db.query(UserBusinessInfo).filter(
            UserBusinessInfo.user_id == user_id,
            UserBusinessInfo.info_key == info_key
        ).first()
        
        if existing_info:
            # Обновляем существующую запись
            existing_info.info_value = str(info_value).lower() if isinstance(info_value, bool) else str(info_value)
            existing_info.source_letter_id = letter_id
            existing_info.updated_at = get_msk_now()
            print(f"[BIZ_INFO] Обновлена информация: {info_key} = {info_value} для пользователя {user_id}")
        else:
            # Создаем новую запись
            new_info = UserBusinessInfo(
                user_id=user_id,
                info_key=info_key,
                info_value=str(info_value).lower() if isinstance(info_value, bool) else str(info_value),
                source_letter_id=letter_id
            )
            db.add(new_info)
            print(f"[BIZ_INFO] Сохранена новая информация: {info_key} = {info_value} для пользователя {user_id}")
    
    db.commit()


def get_user_business_info(user_id: int, db: Session) -> dict:
    """
    Получает сохраненную бизнес-информацию о пользователе.
    
    Args:
        user_id: ID пользователя
        db: Сессия базы данных
    
    Returns:
        Словарь с бизнес-информацией
    """
    info_records = db.query(UserBusinessInfo).filter(
        UserBusinessInfo.user_id == user_id
    ).all()
    
    business_info = {}
    for record in info_records:
        # Преобразуем строковые значения обратно в boolean, если нужно
        value = record.info_value
        if value.lower() == "true":
            business_info[record.info_key] = True
        elif value.lower() == "false":
            business_info[record.info_key] = False
        else:
            business_info[record.info_key] = value
    
    return business_info


def get_client_letter_history(author_id: int, exclude_letter_id: int, db: Session, limit: int = 10):
    """
    Получает историю предыдущих писем клиента для использования в контексте генерации ответа.
    
    Args:
        author_id: ID автора (клиента)
        exclude_letter_id: ID письма, которое нужно исключить из истории (текущее письмо)
        db: Сессия базы данных
        limit: Максимальное количество писем для включения в историю
    
    Returns:
        Список словарей с информацией о письмах для передачи в generate_answer
    """
    # Получаем предыдущие письма клиента, отсортированные по дате (новые сначала)
    # Исключаем текущее письмо и берем только завершенные (с ответами)
    previous_letters = db.query(Letter).filter(
        Letter.author_id == author_id,
        Letter.id != exclude_letter_id,
        Letter.status == LetterStatus.COMPLETED,
        Letter.response.isnot(None)
    ).order_by(Letter.created_at.desc()).limit(limit).all()
    
    # Форматируем для передачи в generate_answer
    history = []
    for prev_letter in previous_letters:
        history.append({
            'content': prev_letter.content,
            'response': prev_letter.response,
            'created_at': prev_letter.created_at.isoformat() if prev_letter.created_at else None
        })
    
    return history

def check_employee_role(user: User):
    if user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав. Требуется роль employee"
        )
