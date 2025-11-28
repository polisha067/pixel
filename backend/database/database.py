"""
Модуль для работы с базой данных.

Этот файл отвечает за:
- Подключение к базе данных SQLite
- Создание сессий для работы с БД
- Инициализацию таблиц при первом запуске
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.config import settings

# ========== Создание движка базы данных ==========
# Engine - это объект, который управляет подключением к БД
# SQLite - файловая база данных, не требует отдельного сервера
# connect_args={"check_same_thread": False} - позволяет использовать БД из разных потоков
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # Нужно для SQLite в многопоточном режиме
)

# ========== Создание фабрики сессий ==========
# SessionLocal - это фабрика для создания сессий
# Сессия - это объект, через который мы выполняем все операции с БД
# autocommit=False - изменения не применяются автоматически, нужно вызывать commit()
# autoflush=False - изменения не отправляются в БД автоматически
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ========== Базовый класс для моделей ==========
# Base - это базовый класс, от которого наследуются все модели (таблицы)
# SQLAlchemy использует его для создания таблиц и работы с ними
Base = declarative_base()


def get_db():
    """
    Функция-генератор для получения сессии базы данных.
    
    Используется в FastAPI через Depends() для автоматического
    управления жизненным циклом сессии.
    
    Yields:
        Session: Сессия базы данных
        
    Пример использования:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    # Создаем новую сессию
    db = SessionLocal()
    try:
        # Возвращаем сессию для использования
        yield db
    finally:
        # Закрываем сессию после использования
        # Это важно для освобождения ресурсов
        db.close()


def init_db():
    """
    Инициализирует базу данных - создает все таблицы.
    
    Эта функция должна быть вызвана при первом запуске приложения.
    Она создает все таблицы на основе моделей, определенных в models.py.
    
    Если таблицы уже существуют, ничего не происходит.
    """
    # Создаем все таблицы, определенные в моделях
    # Base.metadata содержит информацию о всех моделях
    Base.metadata.create_all(bind=engine)
    print("✅ База данных инициализирована!")

