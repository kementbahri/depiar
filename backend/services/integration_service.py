import requests
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models import Integration
import logging
from ..utils.retry import retry_with_backoff
import ssl
import certifi

logger = logging.getLogger(__name__)

class IntegrationService:
    def __init__(self, db: Session):
        self.db = db
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    def create_integration(self, user_id: int, type: str, name: str, config: Dict[str, Any]) -> Integration:
        """Yeni entegrasyon oluştur"""
        # Config'i doğrula
        self._validate_config(type, config)

        integration = Integration(
            user_id=user_id,
            type=type,
            name=name,
            config=config
        )
        self.db.add(integration)
        self.db.commit()
        self.db.refresh(integration)
        return integration

    def _validate_config(self, type: str, config: Dict[str, Any]) -> None:
        """Entegrasyon konfigürasyonunu doğrula"""
        required_fields = {
            "cpanel": ["host", "username", "password", "token"],
            "directadmin": ["host", "username", "password"],
            "cloudflare": ["api_token"]
        }

        if type not in required_fields:
            raise ValueError(f"Unsupported integration type: {type}")

        missing_fields = [field for field in required_fields[type] if field not in config]
        if missing_fields:
            raise ValueError(f"Missing required fields for {type}: {', '.join(missing_fields)}")

    def update_integration(self, integration_id: int, config: Dict[str, Any] = None, is_active: bool = None) -> Integration:
        """Entegrasyonu güncelle"""
        integration = self.db.query(Integration).filter(Integration.id == integration_id).first()
        if integration:
            if config:
                self._validate_config(integration.type, config)
                integration.config = config
            if is_active is not None:
                integration.is_active = is_active
            integration.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(integration)
        return integration

    def delete_integration(self, integration_id: int) -> None:
        """Entegrasyonu sil"""
        integration = self.db.query(Integration).filter(Integration.id == integration_id).first()
        if integration:
            self.db.delete(integration)
            self.db.commit()

    def get_integrations(self, user_id: int) -> list[Integration]:
        """Kullanıcının entegrasyonlarını getir"""
        return self.db.query(Integration).filter(Integration.user_id == user_id).all()

    async def sync_integration(self, integration_id: int) -> bool:
        """Entegrasyonu senkronize et (asenkron)"""
        integration = self.db.query(Integration).filter(Integration.id == integration_id).first()
        if not integration or not integration.is_active:
            return False

        try:
            if integration.type == "cpanel":
                return await self._sync_cpanel(integration)
            elif integration.type == "directadmin":
                return await self._sync_directadmin(integration)
            elif integration.type == "cloudflare":
                return await self._sync_cloudflare(integration)
            else:
                logger.error(f"Unknown integration type: {integration.type}")
                return False

        except Exception as e:
            logger.error(f"Integration sync failed: {str(e)}")
            return False

    @retry_with_backoff(max_retries=3, delay=1)
    async def _sync_cpanel(self, integration: Integration) -> bool:
        """cPanel entegrasyonunu senkronize et"""
        try:
            config = integration.config
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{config['host']}:2087/json-api/cpanel",
                    auth=aiohttp.BasicAuth(config['username'], config['password']),
                    ssl=self.ssl_context,
                    headers={
                        "Authorization": f"Basic {config['token']}"
                    }
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Senkronizasyon başarılı
                    integration.last_sync = datetime.utcnow()
                    self.db.commit()
                    return True

        except Exception as e:
            logger.error(f"cPanel sync failed: {str(e)}")
            raise

    @retry_with_backoff(max_retries=3, delay=1)
    async def _sync_directadmin(self, integration: Integration) -> bool:
        """DirectAdmin entegrasyonunu senkronize et"""
        try:
            config = integration.config
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{config['host']}:2222/CMD_API_SHOW_ALL_USERS",
                    auth=aiohttp.BasicAuth(config['username'], config['password']),
                    ssl=self.ssl_context
                ) as response:
                    response.raise_for_status()
                    data = await response.text()
                    
                    # Senkronizasyon başarılı
                    integration.last_sync = datetime.utcnow()
                    self.db.commit()
                    return True

        except Exception as e:
            logger.error(f"DirectAdmin sync failed: {str(e)}")
            raise

    @retry_with_backoff(max_retries=3, delay=1)
    async def _sync_cloudflare(self, integration: Integration) -> bool:
        """Cloudflare entegrasyonunu senkronize et"""
        try:
            config = integration.config
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.cloudflare.com/client/v4/zones",
                    headers={
                        "Authorization": f"Bearer {config['api_token']}",
                        "Content-Type": "application/json"
                    },
                    ssl=self.ssl_context
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Senkronizasyon başarılı
                    integration.last_sync = datetime.utcnow()
                    self.db.commit()
                    return True

        except Exception as e:
            logger.error(f"Cloudflare sync failed: {str(e)}")
            raise 