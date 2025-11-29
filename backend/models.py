from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os

# Московское время - используем zoneinfo (Python 3.9+) или pytz как fallback
try:
    from zoneinfo import ZoneInfo
    MSK_TZ = ZoneInfo("Europe/Moscow")
except (ImportError, ModuleNotFoundError):
    try:
        import pytz
        MSK_TZ = pytz.timezone("Europe/Moscow")
    except ImportError:
        # Если ничего не установлено, используем UTC (не идеально, но работает)
        print("[WARNING] Neither zoneinfo nor pytz available, using UTC for timezone")
        MSK_TZ = None

def get_msk_now():
    """Возвращает текущее время в московском часовом поясе"""
    if MSK_TZ is None:
        # Fallback на UTC если нет timezone библиотек
        return datetime.utcnow()
    return datetime.now(MSK_TZ)

# База данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'bank_system.db')}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enum для типа пользователя
class UserType(str, enum.Enum):
    CLIENT = "client"
    EMPLOYEE = "employee"

# Enum для статуса письма
class LetterStatus(str, enum.Enum):
    PENDING = "pending"  # Ожидает обработки
    IN_WORK = "in_work"  # В работе у сотрудника
    RESPONSE_READY = "response_ready"  # Ответ готов, ожидает одобрения
    COMPLETED = "completed"  # Завершено

# Enum для специализации сотрудников банка
class Specialization(str, enum.Enum):
    CREDIT = "Кредитование"  # Кредитование (ипотека, автокредит, потребительский кредит)
    INSURANCE = "Страхование"  # Страхование (страхование жизни, имущества, ОСАГО)
    CARDS = "Дебетовые/кредитные карты"  # Дебетовые/кредитные карты
    INVESTMENTS = "Инвестиции и накопления"  # Инвестиции и накопления
    ONLINE_BANKING = "Онлайн-банкинг (ПСБ Онлайн)"  # Онлайн-банкинг (ПСБ Онлайн)
    CASHBACK = "Кэшбэк и бонусы"  # Кэшбэк и бонусы
    ACCOUNTS = "Открытие/закрытие счетов"  # Открытие/закрытие счетов
    OTHER = "Прочее"  # Прочее

# Enum для типа письма (классификация) - оставляем для обратной совместимости
class EmailType(str, enum.Enum):
    COMPLAINT = "COMPLAINT"  # Жалоба
    INQUIRY = "INQUIRY"  # Запрос информации
    APPLICATION = "APPLICATION"  # Заявка на услугу
    SUPPORT = "SUPPORT"  # Техподдержка
    CLARIFICATION = "CLARIFICATION"  # Уточнение
    OTHER = "OTHER"  # Другое

# Модели базы данных
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)  # Формируется автоматически из имени и фамилии
    first_name = Column(String, nullable=True)  # Имя
    last_name = Column(String, nullable=True)  # Фамилия
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    user_type = Column(SQLEnum(UserType), nullable=False)
    # Специализация для сотрудников (какие услуги они обрабатывают)
    specialization = Column(String, nullable=True)  # Может быть несколько через запятую или null для всех
    # Старое поле classification оставляем для обратной совместимости
    classification = Column(String, nullable=True)  # Может быть несколько через запятую или null для всех
    created_at = Column(DateTime, default=lambda: get_msk_now())
    
    # Письма, которые пользователь отправил (как автор)
    letters = relationship(
        "Letter", 
        foreign_keys="[Letter.author_id]",
        back_populates="author",
        primaryjoin="User.id == Letter.author_id"
    )
    # Письма, которые пользователь обрабатывает (как сотрудник)  
    assigned_letters = relationship(
        "Letter", 
        foreign_keys="[Letter.employee_id]",
        back_populates="employee",
        primaryjoin="User.id == Letter.employee_id"
    )

class Letter(Base):
    __tablename__ = "letters"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    status = Column(SQLEnum(LetterStatus), default=LetterStatus.PENDING)
    response = Column(String, nullable=True)
    # Классификация письма
    email_type = Column(SQLEnum(EmailType), nullable=True)  # Тип письма (классификация) - для обратной совместимости
    specialization = Column(String, nullable=True)  # Специализация, к которой относится письмо
    deadline = Column(DateTime, nullable=True)  # Дедлайн для ответа
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: get_msk_now())
    updated_at = Column(DateTime, default=lambda: get_msk_now(), onupdate=lambda: get_msk_now())
    
    author = relationship("User", foreign_keys=[author_id], back_populates="letters")
    employee = relationship("User", foreign_keys=[employee_id], back_populates="assigned_letters")

# Pydantic модели для API
class MailRequest(BaseModel):
    email: str

class EmailResponse(BaseModel):
    content: str

class UserRegister(BaseModel):
    first_name: str  # Имя
    last_name: str  # Фамилия
    email: str
    password: str
    user_type: str
    specialization: str | None = None  # Специализация для сотрудников (через запятую или null)
    classification: str | None = None  # Старое поле для обратной совместимости
    username: str | None = None  # Для обратной совместимости, если не указан - формируется автоматически

class UserLogin(BaseModel):
    username: str
    password: str

class LetterCreate(BaseModel):
    content: str

class LetterResponse(BaseModel):
    id: int
    content: str
    status: str
    response: str | None
    employee_id: int | None
    email_type: str | None  # Классификация письма (для обратной совместимости)
    specialization: str | None  # Специализация письма
    deadline: str | None  # Дедлайн в формате ISO
    created_at: str
    updated_at: str

class LetterListResponse(BaseModel):
    letters: list[LetterResponse]

class StatsResponse(BaseModel):
    total_completed: int

class LetterUpdateResponse(BaseModel):
    response: str