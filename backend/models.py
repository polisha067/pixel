from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os

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

# Модели базы данных
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    user_type = Column(SQLEnum(UserType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
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
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    author = relationship("User", foreign_keys=[author_id], back_populates="letters")
    employee = relationship("User", foreign_keys=[employee_id], back_populates="assigned_letters")

# Pydantic модели для API
class MailRequest(BaseModel):
    email: str

class EmailResponse(BaseModel):
    content: str

class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    user_type: str

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
    created_at: str
    updated_at: str

class LetterListResponse(BaseModel):
    letters: list[LetterResponse]

class StatsResponse(BaseModel):
    total_completed: int