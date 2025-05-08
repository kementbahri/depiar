import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.notification_service import NotificationService
from models.notification_page import NotificationPage
from database import Base

# Test veritabanı
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_create_notification_page(db_session):
    service = NotificationService(db_session)
    notification = service.update_notification_page(
        type="test",
        title="Test Notification",
        content="<html>Test content</html>"
    )
    
    assert notification.type == "test"
    assert notification.title == "Test Notification"
    assert notification.content == "<html>Test content</html>"
    assert notification.is_active == True

def test_get_notification_page(db_session):
    service = NotificationService(db_session)
    # Önce bir sayfa oluştur
    service.update_notification_page(
        type="test",
        title="Test Notification",
        content="<html>Test content</html>"
    )
    
    # Sonra getir
    notification = service.get_notification_page("test")
    assert notification is not None
    assert notification.type == "test"

def test_toggle_notification_page(db_session):
    service = NotificationService(db_session)
    # Önce bir sayfa oluştur
    service.update_notification_page(
        type="test",
        title="Test Notification",
        content="<html>Test content</html>"
    )
    
    # Pasif yap
    notification = service.toggle_notification_page("test", False)
    assert notification.is_active == False
    
    # Aktif yap
    notification = service.toggle_notification_page("test", True)
    assert notification.is_active == True

def test_list_notification_pages(db_session):
    service = NotificationService(db_session)
    # Birkaç sayfa oluştur
    service.update_notification_page(
        type="test1",
        title="Test 1",
        content="<html>Test 1</html>"
    )
    service.update_notification_page(
        type="test2",
        title="Test 2",
        content="<html>Test 2</html>"
    )
    
    # Listele
    notifications = service.list_notification_pages()
    assert len(notifications) == 2
    assert notifications[0].type == "test1"
    assert notifications[1].type == "test2" 