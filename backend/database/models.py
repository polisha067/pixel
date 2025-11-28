"""
Модели базы данных (таблицы).

Этот файл определяет структуру всех таблиц в базе данных.
Каждый класс здесь - это одна таблица, атрибуты класса - это колонки.

SQLAlchemy автоматически создаст таблицы на основе этих моделей.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from backend.database.database import Base
from backend.config import settings


# ========== Перечисления (Enums) ==========

class UserRole(str, enum.Enum):
    """
    Роли пользователей в системе.
    
    user - обычный пользователь (клиент банка), может отправлять обращения
    employee - сотрудник банка, может обрабатывать обращения
    """
    USER = "user"
    EMPLOYEE = "employee"


class LetterStatus(str, enum.Enum):
    """
    Статусы писем в системе.
    
    waiting - письмо создано, но сотрудник еще не открыл
    in_progress - сотрудник открыл письмо и работает над ответом
    sent - ответ отправлен пользователю
    closed - письмо закрыто (опционально)
    """
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    SENT = "sent"
    CLOSED = "closed"


# ========== Модели (таблицы) ==========

class User(Base):
    """
    Таблица пользователей системы.
    
    Хранит информацию обо всех пользователях:
    - Обычных клиентах банка (role = "user")
    - Сотрудниках банка (role = "employee")
    
    Связи:
    - Один пользователь может отправить много писем (relationship letters)
    - Один пользователь может быть сотрудником (relationship employee)
    """
    __tablename__ = "users"  # Имя таблицы в БД
    
    # ========== Колонки таблицы ==========
    
    # ID пользователя (первичный ключ, автоинкремент)
    id = Column(Integer, primary_key=True, index=True, comment="Уникальный идентификатор пользователя")
    
    # Имя пользователя
    name = Column(String(100), nullable=False, comment="Имя пользователя")
    
    # Email пользователя (уникальный)
    email = Column(String(100), unique=True, nullable=False, index=True, comment="Email адрес")
    
    # Роль пользователя (user или employee)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER, comment="Роль: пользователь или сотрудник")
    
    # Дата создания записи (автоматически устанавливается при создании)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Дата регистрации")
    
    # ========== Связи с другими таблицами ==========
    
    # Связь один-ко-многим: один пользователь может отправить много писем
    letters = relationship("Letter", back_populates="user", foreign_keys="Letter.user_id")
    
    # Связь один-к-одному: пользователь может быть сотрудником
    employee = relationship("Employee", back_populates="user", uselist=False)


class Employee(Base):
    """
    Таблица сотрудников банка.
    
    Расширяет информацию о пользователе с ролью "employee".
    Хранит специализацию сотрудника - категорию банковских услуг,
    по которой он обрабатывает обращения.
    
    Связи:
    - Связан с User через user_id
    - Один сотрудник может обработать много писем (relationship letters)
    """
    __tablename__ = "employees"
    
    # ========== Колонки таблицы ==========
    
    # ID сотрудника (первичный ключ)
    id = Column(Integer, primary_key=True, index=True, comment="Уникальный идентификатор сотрудника")
    
    # Ссылка на пользователя (внешний ключ)
    # ondelete="CASCADE" - если пользователь удален, удаляется и запись сотрудника
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, comment="ID пользователя")
    
    # Отдел сотрудника (например, "Отдел кредитования", "Отдел страхования")
    department = Column(String(200), nullable=True, comment="Название отдела")
    
    # Специализация (категория банковских услуг)
    # Это ключевое поле - по нему определяется, какие письма получает сотрудник
    # Должно совпадать с одной из категорий из settings.BANK_CATEGORIES
    # Например: "credit", "insurance", "mortgage" и т.д.
    category = Column(String(50), nullable=False, index=True, comment="Категория услуг (credit, insurance, mortgage и т.д.)")
    
    # Дата создания записи
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Дата регистрации как сотрудника")
    
    # ========== Связи с другими таблицами ==========
    
    # Связь с пользователем
    user = relationship("User", back_populates="employee")
    
    # Связь один-ко-многим: один сотрудник может обработать много писем
    letters = relationship("Letter", back_populates="employee", foreign_keys="Letter.employee_id")


class Letter(Base):
    """
    Таблица писем/обращений.
    
    Хранит все обращения от пользователей:
    - Текст обращения
    - Категорию услуги (определяется нейросетью)
    - Статус обработки
    - Черновик ответа от нейросети
    - Финальный ответ от сотрудника
    
    Связи:
    - Принадлежит пользователю (user_id)
    - Назначена сотруднику (employee_id)
    - Имеет историю чата для редактирования (relationship chat_messages)
    """
    __tablename__ = "letters"
    
    # ========== Колонки таблицы ==========
    
    # ID письма (первичный ключ)
    id = Column(Integer, primary_key=True, index=True, comment="Уникальный идентификатор письма")
    
    # Текст обращения от пользователя
    text = Column(Text, nullable=False, comment="Текст обращения от пользователя")
    
    # Категория банковской услуги (определяется нейросетью)
    # Должна совпадать с одной из категорий из settings.BANK_CATEGORIES
    # Например: "credit", "insurance", "mortgage" и т.д.
    category = Column(String(50), nullable=False, index=True, comment="Категория услуги (определена нейросетью)")
    
    # Статус обработки письма
    status = Column(Enum(LetterStatus), nullable=False, default=LetterStatus.WAITING, index=True, comment="Статус: ожидание, в работе, отправлено")
    
    # ========== Связи с пользователями ==========
    
    # ID пользователя, который отправил письмо (внешний ключ)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="ID пользователя-отправителя")
    
    # ID сотрудника, которому назначено письмо (внешний ключ)
    # Может быть NULL, если письмо еще не назначено
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True, comment="ID сотрудника-обработчика")
    
    # ========== Ответы ==========
    
    # Черновик ответа, сгенерированный нейросетью
    # Сотрудник видит этот черновик и может редактировать его через чат
    draft_response = Column(Text, nullable=True, comment="Черновик ответа от нейросети")
    
    # Финальный ответ, отправленный пользователю
    # Заполняется сотрудником после редактирования
    final_response = Column(Text, nullable=True, comment="Финальный ответ, отправленный пользователю")
    
    # ========== Даты ==========
    
    # Дата создания письма
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="Дата создания письма")
    
    # Дата последнего обновления (автоматически обновляется при изменении)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Дата последнего обновления")
    
    # ========== Связи с другими таблицами ==========
    
    # Связь с пользователем-отправителем
    user = relationship("User", back_populates="letters", foreign_keys=[user_id])
    
    # Связь с сотрудником-обработчиком
    employee = relationship("Employee", back_populates="letters", foreign_keys=[employee_id])
    
    # Связь один-ко-многим: одно письмо может иметь много сообщений в чате
    chat_messages = relationship("ChatMessage", back_populates="letter", cascade="all, delete-orphan")


class ChatMessage(Base):
    """
    Таблица сообщений в чате редактирования.
    
    Хранит историю общения сотрудника с нейросетью при редактировании ответа.
    Каждое сообщение - это либо запрос сотрудника, либо ответ нейросети.
    
    Связи:
    - Принадлежит письму (letter_id)
    """
    __tablename__ = "chat_messages"
    
    # ========== Колонки таблицы ==========
    
    # ID сообщения (первичный ключ)
    id = Column(Integer, primary_key=True, index=True, comment="Уникальный идентификатор сообщения")
    
    # Ссылка на письмо (внешний ключ)
    # ondelete="CASCADE" - если письмо удалено, удаляются все сообщения
    letter_id = Column(Integer, ForeignKey("letters.id", ondelete="CASCADE"), nullable=False, index=True, comment="ID письма")
    
    # Роль отправителя сообщения
    # "employee" - сообщение от сотрудника
    # "assistant" - ответ от нейросети
    role = Column(String(20), nullable=False, comment="Роль: employee (сотрудник) или assistant (нейросеть)")
    
    # Текст сообщения
    message = Column(Text, nullable=False, comment="Текст сообщения")
    
    # Дата и время отправки сообщения
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="Дата и время отправки")
    
    # ========== Связи с другими таблицами ==========
    
    # Связь с письмом
    letter = relationship("Letter", back_populates="chat_messages")

