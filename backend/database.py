from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Veritabanı bağlantı bilgileri
MYSQL_USER = "depiar"
MYSQL_PASSWORD = os.getenv("MYSQL_DEPIAR_PASSWORD", "depiar")
MYSQL_HOST = "localhost"
MYSQL_PORT = "3306"
MYSQL_DATABASE = "depiar"

# SQLAlchemy bağlantı URL'si
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

# Engine oluştur
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10
)

# SessionLocal sınıfı
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base sınıfı
Base = declarative_base()

# Veritabanı bağlantısı için yardımcı fonksiyon
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