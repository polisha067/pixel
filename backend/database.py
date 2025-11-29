from sqlalchemy.orm import Session
from models import Base, engine, SessionLocal

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

def init_db(reset_db=False):
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if reset_db and existing_tables:
            print("[DB] WARNING: Resetting database (all data will be lost!)")
            Base.metadata.drop_all(bind=engine)
            print("[DB] All tables dropped")
            existing_tables = []
        
        Base.metadata.create_all(bind=engine)
        
        existing_tables_after = inspector.get_table_names()
        
        if 'users' in existing_tables_after:
            _add_missing_columns('users', [
                ('classification', 'VARCHAR', 'NULL'),
                ('specialization', 'VARCHAR', 'NULL'),
                ('first_name', 'VARCHAR', 'NULL'),
                ('last_name', 'VARCHAR', 'NULL')
            ])
        
        if 'letters' in existing_tables_after:
            _add_missing_columns('letters', [
                ('email_type', 'VARCHAR', 'NULL'),
                ('deadline', 'DATETIME', 'NULL'),
                ('specialization', 'VARCHAR', 'NULL')
            ])
        
        if 'user_business_info' not in existing_tables_after:
            print("[DB] Creating user_business_info table")
            Base.metadata.create_all(bind=engine)
        
        if existing_tables:
            print(f"[DB] Database tables already exist: {existing_tables}")
            print("[DB] Existing data will be preserved")
        else:
            print("[DB] Database tables created successfully")
    except Exception as e:
        print(f"[DB] Error initializing database: {str(e)}")
        import traceback
        traceback.print_exc()
        try:
            Base.metadata.create_all(bind=engine)
            print("[DB] Database tables created (fallback)")
        except Exception as e2:
            print(f"[DB] Failed to create tables: {str(e2)}")

def _add_missing_columns(table_name, columns):
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        for col_name, col_type, col_default in columns:
            if col_name not in existing_columns:
                print(f"[DB] Adding missing column: {table_name}.{col_name}")
                if col_default == 'NULL':
                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                else:
                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} DEFAULT {col_default}"
                
                with engine.begin() as conn:
                    conn.execute(text(alter_sql))
                print(f"[DB] Column {col_name} added successfully")
    except Exception as e:
        print(f"[DB] Error adding columns to {table_name}: {str(e)}")
        import traceback
        traceback.print_exc()

def verify_password(plain_password, hashed_password):
    try:
        if not plain_password or not hashed_password:
            return False
        
        if HAS_PASSLIB:
            return pwd_context.verify(plain_password, hashed_password)
        elif HAS_BCRYPT:
            if isinstance(plain_password, str):
                plain_password = plain_password.encode('utf-8')
            if isinstance(hashed_password, str):
                hashed_password = hashed_password.encode('utf-8')
            return bcrypt.checkpw(plain_password, hashed_password)
        else:
            return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"[ERROR] Password verification error: {str(e)}")
        return False

def get_password_hash(password):
    try:
        if password is None:
            raise ValueError("Password cannot be None")
        
        if not isinstance(password, str):
            password = str(password)
        
        password_bytes = password.encode('utf-8')
        
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        if HAS_PASSLIB:
            password_str = password_bytes.decode('utf-8', errors='ignore')
            hashed = pwd_context.hash(password_str)
        elif HAS_BCRYPT:
            salt = bcrypt.gensalt()
            hashed_bytes = bcrypt.hashpw(password_bytes, salt)
            hashed = hashed_bytes.decode('utf-8')
        else:
            password_str = password_bytes.decode('utf-8', errors='ignore')
            hashed = pwd_context.hash(password_str)
        
        return hashed
        
    except Exception as e:
        print(f"[ERROR] Password hashing error: {str(e)}")
        print(f"[ERROR] Password type: {type(password)}, value: {repr(password)}")
        import traceback
        traceback.print_exc()
        raise ValueError(f"Error hashing password: {str(e)}")
