from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import OAuth2PasswordBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
from database import SessionLocal, engine
from auth import get_current_user
from .routers import auth, domains, emails, databases, customers, email_accounts, ssl, import_router, dns, ftp, tasks, logs, service_plans, reseller_plans, users, resellers, settings, reports, ssh, subdomains, database_management, backup, vendors, monitoring, software, files, webhooks, integrations
from .middleware import ErrorHandlerMiddleware, RequestLoggingMiddleware, ValidationErrorHandlerMiddleware, LanguageMiddleware, AuthMiddleware
import os
from dotenv import load_dotenv
from .utils.i18n import get_translation, get_language_from_request
from .services.backup_service import start_backup_scheduler
from .services.ssl_service import start_ssl_renewal_scheduler
from .services.monitoring_service import start_monitoring_scheduler
import logging

load_dotenv()

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Web Hosting Control Panel API",
    description="Web hosting control panel API documentation",
    version="1.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware'leri ekle
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ValidationErrorHandlerMiddleware)
app.add_middleware(LanguageMiddleware)
app.add_middleware(AuthMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# Trusted hosts middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(",")
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rate limit decorator
def rate_limit(limit: str):
    def decorator(func):
        return limiter.limit(limit)(func)
    return decorator

# User routes
@app.post("/api/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=user.password  # In production, hash the password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/api/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# Domain routes
@app.post("/api/domains/", response_model=schemas.Domain)
def create_domain(
    domain: schemas.DomainCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_domain = models.Domain(**domain.dict(), user_id=current_user.id)
    db.add(db_domain)
    db.commit()
    db.refresh(db_domain)
    return db_domain

@app.get("/api/domains/", response_model=List[schemas.Domain])
def read_domains(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    domains = db.query(models.Domain).filter(models.Domain.user_id == current_user.id).all()
    return domains

# Email routes
@app.post("/api/emails/", response_model=schemas.EmailAccount)
def create_email_account(
    email: schemas.EmailAccountCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_email = models.EmailAccount(**email.dict(), user_id=current_user.id)
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    return db_email

@app.get("/api/emails/", response_model=List[schemas.EmailAccount])
def read_email_accounts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    emails = db.query(models.EmailAccount).filter(models.EmailAccount.user_id == current_user.id).all()
    return emails

# File management routes
@app.get("/api/files/")
def list_files(
    path: str = "/",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Implement file listing logic
    return {"message": "File listing endpoint"}

@app.post("/api/files/upload")
def upload_file(
    file: UploadFile,
    path: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Implement file upload logic
    return {"message": "File upload endpoint"}

# Include routers with rate limits
app.include_router(
    auth.router,
    prefix="/api",
    tags=["auth"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    domains.router,
    prefix="/api",
    tags=["domains"],
    dependencies=[Depends(rate_limit("10/minute"))]
)

app.include_router(
    emails.router,
    prefix="/api",
    tags=["emails"],
    dependencies=[Depends(rate_limit("10/minute"))]
)

app.include_router(
    databases.router,
    prefix="/api",
    tags=["databases"],
    dependencies=[Depends(rate_limit("10/minute"))]
)

app.include_router(
    customers.router,
    prefix="/api",
    tags=["customers"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    email_accounts.router,
    prefix="/api",
    tags=["email_accounts"],
    dependencies=[Depends(rate_limit("10/minute"))]
)

app.include_router(
    ssl.router,
    prefix="/api",
    tags=["ssl"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    import_router,
    prefix="/api",
    tags=["import"],
    dependencies=[Depends(rate_limit("2/minute"))]
)

app.include_router(
    dns.router,
    prefix="/api",
    tags=["dns"],
    dependencies=[Depends(rate_limit("10/minute"))]
)

app.include_router(
    ftp.router,
    prefix="/api",
    tags=["ftp"],
    dependencies=[Depends(rate_limit("10/minute"))]
)

app.include_router(
    tasks.router,
    prefix="/api",
    tags=["tasks"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    logs.router,
    prefix="/api",
    tags=["logs"],
    dependencies=[Depends(rate_limit("10/minute"))]
)

app.include_router(
    service_plans.router,
    prefix="/api/service-plans",
    tags=["service-plans"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    reseller_plans.router,
    prefix="/api/reseller-plans",
    tags=["reseller-plans"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    users.router,
    prefix="/api/users",
    tags=["users"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    resellers.router,
    prefix="/api/resellers",
    tags=["resellers"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    settings.router,
    prefix="/api/settings",
    tags=["settings"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    reports.router,
    prefix="/api/reports",
    tags=["reports"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(ssh.router)

app.include_router(
    subdomains.router,
    prefix="/api",
    tags=["subdomains"],
    dependencies=[Depends(rate_limit("10/minute"))]
)

app.include_router(
    database_management.router,
    prefix="/api",
    tags=["database-management"],
    dependencies=[Depends(rate_limit("10/minute"))]
)

app.include_router(
    backup.router,
    prefix="/api/backup",
    tags=["backup"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    vendors.router,
    prefix="/api/vendors",
    tags=["vendors"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    monitoring.router,
    prefix="/api",
    tags=["monitoring"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    software.router,
    prefix="/api",
    tags=["software"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    files.router,
    prefix="/api",
    tags=["files"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    webhooks.router,
    prefix="/api",
    tags=["webhooks"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

app.include_router(
    integrations.router,
    prefix="/api",
    tags=["integrations"],
    dependencies=[Depends(rate_limit("5/minute"))]
)

@app.get("/")
@rate_limit("5/minute")
async def root(request: Request):
    """API ana sayfası"""
    language = get_language_from_request(request)
    return {
        "message": get_translation("common.welcome", language),
        "version": "1.0.0"
    }

# Zamanlayıcıları başlat
start_backup_scheduler()
start_ssl_renewal_scheduler()
start_monitoring_scheduler()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 