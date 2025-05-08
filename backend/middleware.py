from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .utils.i18n import get_language_from_request, get_translation
import logging
import time
import json
from typing import Callable
from pydantic import ValidationError
from redis import Redis
import os
from dotenv import load_dotenv
from .utils.logger import log_warning

# .env dosyasını yükle
load_dotenv()

# Redis bağlantısı
redis_client = Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    decode_responses=True
)

# Rate limit ayarları
RATE_LIMIT = {
    'default': {'requests': 100, 'period': 60},  # 100 istek/dakika
    'auth': {'requests': 5, 'period': 60},       # 5 istek/dakika
    'api': {'requests': 1000, 'period': 3600},   # 1000 istek/saat
}

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            language = get_language_from_request(request)
            return JSONResponse(
                status_code=500,
                content={
                    "error": get_translation("errors.internal_server_error", language),
                    "detail": str(e)
                }
            )

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # İsteği logla
        logger.info(f"Request started: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Yanıtı logla
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"Status: {response.status_code} Duration: {process_time:.2f}s"
            )
            
            return response
        except Exception as e:
            logger.error(f"Request failed: {request.method} {request.url.path}", exc_info=True)
            raise

class ValidationErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            language = get_language_from_request(request)
            return JSONResponse(
                status_code=422,
                content={
                    "error": get_translation("errors.validation_error", language),
                    "detail": e.errors()
                }
            )
        except ValueError as e:
            logger.warning(f"Value error: {str(e)}")
            language = get_language_from_request(request)
            return JSONResponse(
                status_code=422,
                content={
                    "error": get_translation("errors.validation_error", language),
                    "detail": str(e)
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            language = get_language_from_request(request)
            return JSONResponse(
                status_code=500,
                content={
                    "error": get_translation("errors.internal_server_error", language),
                    "detail": "An unexpected error occurred. Please try again later."
                }
            )

class LanguageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        # Dil bilgisini request'e ekle
        request.state.language = get_language_from_request(request)
        
        response = await call_next(request)
        return response 

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    
    # IP adresini al
    client_ip = request.client.host
    
    # Endpoint tipini belirle
    if request.url.path.startswith('/api/auth'):
        endpoint_type = 'auth'
    elif request.url.path.startswith('/api'):
        endpoint_type = 'api'
    else:
        endpoint_type = 'default'
    
    # Rate limit ayarlarını al
    limit = RATE_LIMIT[endpoint_type]
    
    # Redis key oluştur
    key = f"rate_limit:{endpoint_type}:{client_ip}"
    
    # Mevcut istek sayısını al
    current = redis_client.get(key)
    
    if current and int(current) > limit['requests']:
        log_warning(
            "Rate limit exceeded",
            {
                "ip": client_ip,
                "endpoint": request.url.path,
                "limit": limit['requests'],
                "period": limit['period']
            }
        )
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests",
                "retry_after": limit['period']
            }
        )
    
    # İstek sayısını artır
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, limit['period'])
    pipe.execute()
    
    # Response'u al
    response = await call_next(request)
    
    # Rate limit başlıklarını ekle
    response.headers["X-RateLimit-Limit"] = str(limit['requests'])
    response.headers["X-RateLimit-Remaining"] = str(
        limit['requests'] - int(current or 0)
    )
    response.headers["X-RateLimit-Reset"] = str(
        int(time.time()) + limit['period']
    )
    
    return response

async def security_middleware(request: Request, call_next):
    """Güvenlik middleware'i"""
    
    # Response'u al
    response = await call_next(request)
    
    # Güvenlik başlıklarını ekle
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
    
    return response

async def logging_middleware(request: Request, call_next):
    """Loglama middleware'i"""
    
    # İstek başlangıç zamanı
    start_time = time.time()
    
    # Response'u al
    response = await call_next(request)
    
    # İşlem süresi
    process_time = time.time() - start_time
    
    # Log mesajı
    log_info(
        "Request processed",
        {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": f"{process_time:.2f}s",
            "client_ip": request.client.host
        }
    )
    
    return response 