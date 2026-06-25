import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Resolve absolute path for SQLite fallback
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = (BASE_DIR / "database.db").as_posix()

# Check if PostgreSQL URL is provided in environment
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
    DATABASE_PATH = "Supabase Cloud Database"
    # Create PostgreSQL engine (check_same_thread is not valid for PostgreSQL dialects)
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    print(f"[DB] Connected to database from environment: {SQLALCHEMY_DATABASE_URL.split('@')[-1] if '@' in SQLALCHEMY_DATABASE_URL else 'PostgreSQL'}")
else:
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    print(f"[DB] Connected to persistent SQLite database: {DATABASE_PATH}")
    
    # Create SQLite engine with multi-threading compatibility argument
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

# Run raw migrations to dynamically add missing columns in campaigns table if needed (only for SQLite fallback)
if engine.dialect.name == "sqlite":
    try:
        from sqlalchemy import text
        with engine.begin() as conn:
            cursor = conn.execute(text("PRAGMA table_info(campaigns)"))
            columns = [row[1] for row in cursor.fetchall()]
            if columns:
                if "generate_adsets" not in columns:
                    conn.execute(text("ALTER TABLE campaigns ADD COLUMN generate_adsets BOOLEAN DEFAULT 0"))
                if "adset_count" not in columns:
                    conn.execute(text("ALTER TABLE campaigns ADD COLUMN adset_count INTEGER DEFAULT 0"))
                if "auto_generate_adsets" not in columns:
                    conn.execute(text("ALTER TABLE campaigns ADD COLUMN auto_generate_adsets BOOLEAN DEFAULT 1"))
    except Exception as e:
        print(f"[ERROR] Database migration failed: {e}")

# Setup local sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base for models
Base = declarative_base()

def get_db():
    """
    Reusable FastAPI database session dependency.
    Yields a database session and closes it when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

