"""
CRUD операции для работы с базой данных.

CRUD = Create, Read, Update, Delete
Этот файл содержит функции для всех основных операций с данными:
- Создание записей
- Чтение записей
- Обновление записей
- Удаление записей

Все функции принимают сессию БД (db) и возвращают объекты моделей.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.database.models import User, Employee, Letter, ChatMessage, UserRole, LetterStatus


# ========== Операции с пользователями ==========

def create_user(db: Session, name: str, email: str, role: UserRole = UserRole.USER) -> User:
    """
    Создает нового пользователя в базе данных.
    
    Args:
        db: Сессия базы данных
        name: Имя пользователя
        email: Email пользователя (должен быть уникальным)
        role: Роль пользователя (user или employee)
    
    Returns:
        User: Созданный объект пользователя
    
    Raises:
        Exception: Если пользователь с таким email уже существует
    """
    # Проверяем, не существует ли уже пользователь с таким email
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise ValueError(f"Пользователь с email {email} уже существует!")
    
    # Создаем новый объект пользователя
    db_user = User(
        name=name,
        email=email,
        role=role
    )
    
    # Добавляем в сессию
    db.add(db_user)
    # Сохраняем изменения в БД
    db.commit()
    # Обновляем объект, чтобы получить ID из БД
    db.refresh(db_user)
    
    return db_user


def get_user_by_id(db: Session, user_id: int) -> User:
    """
    Получает пользователя по ID.
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
    
    Returns:
        User или None, если пользователь не найден
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User:
    """
    Получает пользователя по email.
    
    Args:
        db: Сессия базы данных
        email: Email пользователя
    
    Returns:
        User или None, если пользователь не найден
    """
    return db.query(User).filter(User.email == email).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """
    Получает список всех пользователей с пагинацией.
    
    Args:
        db: Сессия базы данных
        skip: Количество записей для пропуска (для пагинации)
        limit: Максимальное количество записей
    
    Returns:
        Список пользователей
    """
    return db.query(User).offset(skip).limit(limit).all()


# ========== Операции с сотрудниками ==========

def create_employee(db: Session, user_id: int, department: str, category: str) -> Employee:
    """
    Создает запись сотрудника.
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя, который является сотрудником
        department: Название отдела
        category: Категория услуг (credit, insurance, mortgage и т.д.)
    
    Returns:
        Employee: Созданный объект сотрудника
    
    Raises:
        ValueError: Если пользователь не найден или уже является сотрудником
    """
    # Проверяем, существует ли пользователь
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError(f"Пользователь с ID {user_id} не найден!")
    
    # Проверяем, не является ли уже сотрудником
    existing_employee = db.query(Employee).filter(Employee.user_id == user_id).first()
    if existing_employee:
        raise ValueError(f"Пользователь с ID {user_id} уже является сотрудником!")
    
    # Создаем запись сотрудника
    db_employee = Employee(
        user_id=user_id,
        department=department,
        category=category
    )
    
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    
    return db_employee


def get_employee_by_id(db: Session, employee_id: int) -> Employee:
    """
    Получает сотрудника по ID.
    
    Args:
        db: Сессия базы данных
        employee_id: ID сотрудника
    
    Returns:
        Employee или None
    """
    return db.query(Employee).filter(Employee.id == employee_id).first()


def get_employee_by_user_id(db: Session, user_id: int) -> Employee:
    """
    Получает сотрудника по ID пользователя.
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
    
    Returns:
        Employee или None
    """
    return db.query(Employee).filter(Employee.user_id == user_id).first()


def get_employees_by_category(db: Session, category: str) -> list[Employee]:
    """
    Получает всех сотрудников, работающих с определенной категорией услуг.
    
    Это ключевая функция для маршрутизации писем!
    Когда письмо классифицировано по категории, мы находим сотрудника,
    который работает с этой категорией.
    
    Args:
        db: Сессия базы данных
        category: Категория услуг (credit, insurance, mortgage и т.д.)
    
    Returns:
        Список сотрудников, работающих с этой категорией
    """
    return db.query(Employee).filter(Employee.category == category).all()


def get_all_employees(db: Session, skip: int = 0, limit: int = 100) -> list[Employee]:
    """
    Получает список всех сотрудников.
    
    Args:
        db: Сессия базы данных
        skip: Количество записей для пропуска
        limit: Максимальное количество записей
    
    Returns:
        Список сотрудников
    """
    return db.query(Employee).offset(skip).limit(limit).all()


# ========== Операции с письмами ==========

def create_letter(
    db: Session,
    text: str,
    user_id: int,
    category: str,
    draft_response: str = None,
    employee_id: int = None
) -> Letter:
    """
    Создает новое письмо.
    
    Args:
        db: Сессия базы данных
        text: Текст обращения от пользователя
        user_id: ID пользователя-отправителя
        category: Категория услуги (определена нейросетью)
        draft_response: Черновик ответа от нейросети (опционально)
        employee_id: ID сотрудника, которому назначено письмо (опционально)
    
    Returns:
        Letter: Созданный объект письма
    """
    db_letter = Letter(
        text=text,
        user_id=user_id,
        category=category,
        draft_response=draft_response,
        employee_id=employee_id,
        status=LetterStatus.WAITING  # По умолчанию статус "ожидание"
    )
    
    db.add(db_letter)
    db.commit()
    db.refresh(db_letter)
    
    return db_letter


def get_letter_by_id(db: Session, letter_id: int) -> Letter:
    """
    Получает письмо по ID.
    
    Args:
        db: Сессия базы данных
        letter_id: ID письма
    
    Returns:
        Letter или None
    """
    return db.query(Letter).filter(Letter.id == letter_id).first()


def get_letters_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[Letter]:
    """
    Получает все письма, отправленные определенным пользователем.
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        skip: Количество записей для пропуска
        limit: Максимальное количество записей
    
    Returns:
        Список писем пользователя
    """
    return db.query(Letter).filter(Letter.user_id == user_id).offset(skip).limit(limit).all()


def get_letters_by_employee(
    db: Session,
    employee_id: int,
    status: LetterStatus = None,
    skip: int = 0,
    limit: int = 100
) -> list[Letter]:
    """
    Получает все письма, назначенные определенному сотруднику.
    
    Можно фильтровать по статусу (waiting, in_progress, sent).
    
    Args:
        db: Сессия базы данных
        employee_id: ID сотрудника
        status: Фильтр по статусу (опционально)
        skip: Количество записей для пропуска
        limit: Максимальное количество записей
    
    Returns:
        Список писем сотрудника
    """
    query = db.query(Letter).filter(Letter.employee_id == employee_id)
    
    # Если указан статус, добавляем фильтр
    if status:
        query = query.filter(Letter.status == status)
    
    return query.offset(skip).limit(limit).all()


def update_letter_status(db: Session, letter_id: int, status: LetterStatus) -> Letter:
    """
    Обновляет статус письма.
    
    Используется когда:
    - Сотрудник открывает письмо → status = IN_PROGRESS
    - Сотрудник отправляет ответ → status = SENT
    
    Args:
        db: Сессия базы данных
        letter_id: ID письма
        status: Новый статус
    
    Returns:
        Letter: Обновленный объект письма
    
    Raises:
        ValueError: Если письмо не найдено
    """
    letter = get_letter_by_id(db, letter_id)
    if not letter:
        raise ValueError(f"Письмо с ID {letter_id} не найдено!")
    
    letter.status = status
    db.commit()
    db.refresh(letter)
    
    return letter


def update_letter_draft_response(db: Session, letter_id: int, draft_response: str) -> Letter:
    """
    Обновляет черновик ответа в письме.
    
    Используется при редактировании ответа через чат с нейросетью.
    
    Args:
        db: Сессия базы данных
        letter_id: ID письма
        draft_response: Новый черновик ответа
    
    Returns:
        Letter: Обновленный объект письма
    """
    letter = get_letter_by_id(db, letter_id)
    if not letter:
        raise ValueError(f"Письмо с ID {letter_id} не найдено!")
    
    letter.draft_response = draft_response
    db.commit()
    db.refresh(letter)
    
    return letter


def update_letter_final_response(db: Session, letter_id: int, final_response: str) -> Letter:
    """
    Устанавливает финальный ответ и меняет статус на "отправлено".
    
    Используется когда сотрудник отправляет финальный ответ пользователю.
    
    Args:
        db: Сессия базы данных
        letter_id: ID письма
        final_response: Финальный текст ответа
    
    Returns:
        Letter: Обновленный объект письма
    """
    letter = get_letter_by_id(db, letter_id)
    if not letter:
        raise ValueError(f"Письмо с ID {letter_id} не найдено!")
    
    letter.final_response = final_response
    letter.status = LetterStatus.SENT
    db.commit()
    db.refresh(letter)
    
    return letter


def assign_letter_to_employee(db: Session, letter_id: int, employee_id: int) -> Letter:
    """
    Назначает письмо сотруднику.
    
    Используется при маршрутизации писем после классификации.
    
    Args:
        db: Сессия базы данных
        letter_id: ID письма
        employee_id: ID сотрудника
    
    Returns:
        Letter: Обновленный объект письма
    """
    letter = get_letter_by_id(db, letter_id)
    if not letter:
        raise ValueError(f"Письмо с ID {letter_id} не найдено!")
    
    letter.employee_id = employee_id
    db.commit()
    db.refresh(letter)
    
    return letter


# ========== Операции с сообщениями чата ==========

def create_chat_message(
    db: Session,
    letter_id: int,
    role: str,
    message: str
) -> ChatMessage:
    """
    Создает новое сообщение в чате редактирования.
    
    Args:
        db: Сессия базы данных
        letter_id: ID письма
        role: Роль отправителя ("employee" или "assistant")
        message: Текст сообщения
    
    Returns:
        ChatMessage: Созданный объект сообщения
    """
    db_message = ChatMessage(
        letter_id=letter_id,
        role=role,
        message=message
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message


def get_chat_messages_by_letter(db: Session, letter_id: int) -> list[ChatMessage]:
    """
    Получает всю историю чата для определенного письма.
    
    Сообщения возвращаются в хронологическом порядке (от старых к новым).
    
    Args:
        db: Сессия базы данных
        letter_id: ID письма
    
    Returns:
        Список сообщений в чате
    """
    return db.query(ChatMessage).filter(
        ChatMessage.letter_id == letter_id
    ).order_by(ChatMessage.timestamp.asc()).all()

