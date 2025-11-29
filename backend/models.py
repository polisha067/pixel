from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os

try:
    from zoneinfo import ZoneInfo
    MSK_TZ = ZoneInfo("Europe/Moscow")
except (ImportError, ModuleNotFoundError):
    try:
        import pytz
        MSK_TZ = pytz.timezone("Europe/Moscow")
    except ImportError:
        print("[WARNING] Neither zoneinfo nor pytz available, using UTC for timezone")
        MSK_TZ = None

def get_msk_now():
    if MSK_TZ is None:
        return datetime.utcnow()
    return datetime.now(MSK_TZ)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'bank_system.db')}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserType(str, enum.Enum):
    CLIENT = "client"
    EMPLOYEE = "employee"

class LetterStatus(str, enum.Enum):
    PENDING = "pending"
    IN_WORK = "in_work"
    RESPONSE_READY = "response_ready"
    COMPLETED = "completed"

class Specialization(str, enum.Enum):
    CREDIT = "Кредитование"
    INSURANCE = "Страхование"
    CARDS = "Дебетовые/кредитные карты"
    INVESTMENTS = "Инвестиции и накопления"
    ONLINE_BANKING = "Онлайн-банкинг (ПСБ Онлайн)"
    CASHBACK = "Кэшбэк и бонусы"
    ACCOUNTS = "Открытие/закрытие счетов"
    OTHER = "Прочее"

class EmailType(str, enum.Enum):
    COMPLAINT = "COMPLAINT"
    INQUIRY = "INQUIRY"
    APPLICATION = "APPLICATION"
    SUPPORT = "SUPPORT"
    CLARIFICATION = "CLARIFICATION"
    OTHER = "OTHER"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    user_type = Column(SQLEnum(UserType), nullable=False)
    specialization = Column(String, nullable=True)
    classification = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: get_msk_now())
    
    letters = relationship(
        "Letter", 
        foreign_keys="[Letter.author_id]",
        back_populates="author",
        primaryjoin="User.id == Letter.author_id"
    )
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
    email_type = Column(SQLEnum(EmailType), nullable=True)
    specialization = Column(String, nullable=True)
    deadline = Column(DateTime, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: get_msk_now())
    updated_at = Column(DateTime, default=lambda: get_msk_now(), onupdate=lambda: get_msk_now())
    
    author = relationship("User", foreign_keys=[author_id], back_populates="letters")
    employee = relationship("User", foreign_keys=[employee_id], back_populates="assigned_letters")

class UserBusinessInfo(Base):
    __tablename__ = "user_business_info"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    info_key = Column(String, nullable=False, index=True)
    info_value = Column(String, nullable=True)
    source_letter_id = Column(Integer, ForeignKey("letters.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: get_msk_now())
    updated_at = Column(DateTime, default=lambda: get_msk_now(), onupdate=lambda: get_msk_now())
    
    user = relationship("User", foreign_keys=[user_id])
    source_letter = relationship("Letter", foreign_keys=[source_letter_id])

class MailRequest(BaseModel):
    email: str

class EmailResponse(BaseModel):
    content: str

class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    user_type: str
    specialization: str | None = None
    classification: str | None = None
    username: str | None = None

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
    email_type: str | None
    specialization: str | None
    deadline: str | None
    created_at: str
    updated_at: str

class LetterListResponse(BaseModel):
    letters: list[LetterResponse]

class StatsResponse(BaseModel):
    total_completed: int

class LetterUpdateResponse(BaseModel):
    response: str