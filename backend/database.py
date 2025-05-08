from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Veritabanı URL'sini al
DATABASE_URL = os.getenv("DATABASE_URL")

# Engine oluştur
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True  # Bağlantı kopması durumunda otomatik yeniden bağlanma
)

# Session factory
SessionLocal = scoped_session(sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
))

# Base class
Base = declarative_base()

# Veritabanı bağlantısı için context manager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Veritabanı bağlantısını test et
def test_db_connection():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"Veritabanı bağlantı hatası: {e}")
        return False

def init_db():
    from .models import Base
    Base.metadata.create_all(bind=engine) 