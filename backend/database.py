from sqlalchemy.orm import Session
from models import Base, engine, SessionLocal

# Импорт библиотек для хеширования паролей
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    HAS_PASSLIB = True
except ImportError:
    print("[WARNING] passlib not installed, trying bcrypt directly")
    HAS_PASSLIB = False

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    print("[WARNING] bcrypt not installed, using simple hash (NOT SECURE)")
    HAS_BCRYPT = False

# Простая заглушка если ничего не установлено
if not HAS_PASSLIB and not HAS_BCRYPT:
    class SimpleHash:
        def hash(self, password):
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest()
        def verify(self, plain, hashed):
            import hashlib
            return hashlib.sha256(plain.encode()).hexdigest() == hashed
    pwd_context = SimpleHash()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    try:
        # Удаляем старые таблицы и создаем заново (для разработки)
        # В продакшене использовать миграции!
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("[DB] Database tables created successfully")
    except Exception as e:
        print(f"[DB] Error creating database: {str(e)}")
        # Если не удалось удалить, просто создаем
        Base.metadata.create_all(bind=engine)
        print("[DB] Database tables created (some may already exist)")

def verify_password(plain_password, hashed_password):
    """
    Проверяет соответствие пароля хешу.
    """
    try:
        if not plain_password or not hashed_password:
            return False
        
        if HAS_PASSLIB:
            return pwd_context.verify(plain_password, hashed_password)
        elif HAS_BCRYPT:
            # Используем bcrypt напрямую
            if isinstance(plain_password, str):
                plain_password = plain_password.encode('utf-8')
            if isinstance(hashed_password, str):
                hashed_password = hashed_password.encode('utf-8')
            return bcrypt.checkpw(plain_password, hashed_password)
        else:
            # Простая проверка для заглушки
            return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"[ERROR] Password verification error: {str(e)}")
        return False

def get_password_hash(password):
    """
    Хеширует пароль с использованием bcrypt.
    Bcrypt ограничивает длину пароля до 72 байт (не символов!).
    Функция автоматически обрезает пароль до 72 байт, если он длиннее.
    """
    try:
        # Убеждаемся, что пароль - строка
        if password is None:
            raise ValueError("Password cannot be None")
        
        if not isinstance(password, str):
            password = str(password)
        
        # Кодируем в UTF-8 для подсчета байт
        password_bytes = password.encode('utf-8')
        
        # Bcrypt ограничивает до 72 байт - обрезаем если нужно
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Хешируем пароль
        if HAS_PASSLIB:
            # Passlib работает со строками, но мы передаем байты для безопасности
            # Декодируем обратно в строку для passlib
            password_str = password_bytes.decode('utf-8', errors='ignore')
            hashed = pwd_context.hash(password_str)
        elif HAS_BCRYPT:
            # Используем bcrypt напрямую (работает с байтами)
            salt = bcrypt.gensalt()
            hashed_bytes = bcrypt.hashpw(password_bytes, salt)
            hashed = hashed_bytes.decode('utf-8')
        else:
            # Простая заглушка
            password_str = password_bytes.decode('utf-8', errors='ignore')
            hashed = pwd_context.hash(password_str)
        
        return hashed
        
    except Exception as e:
        print(f"[ERROR] Password hashing error: {str(e)}")
        print(f"[ERROR] Password type: {type(password)}, value: {repr(password)}")
        import traceback
        traceback.print_exc()
        raise ValueError(f"Error hashing password: {str(e)}")
