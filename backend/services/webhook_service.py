import hmac
import hashlib
import json
import requests
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models import Webhook
import logging
import os
from ..utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

class WebhookService:
    def __init__(self, db: Session):
        self.db = db
        self.webhook_secret = os.getenv("WEBHOOK_SECRET", os.urandom(32).hex())
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    def create_webhook(self, user_id: int, url: str, events: List[str]) -> Webhook:
        """Yeni webhook oluştur"""
        # Benzersiz bir secret oluştur
        secret = hmac.new(
            self.webhook_secret.encode(),
            str(datetime.utcnow()).encode(),
            hashlib.sha256
        ).hexdigest()

        webhook = Webhook(
            user_id=user_id,
            url=url,
            events=events,
            secret=secret
        )
        self.db.add(webhook)
        self.db.commit()
        self.db.refresh(webhook)
        return webhook

    async def trigger_webhook(self, event: str, payload: Dict[str, Any]) -> None:
        """Webhook'u tetikle (asenkron)"""
        webhooks = self.db.query(Webhook).filter(
            Webhook.is_active == True,
            Webhook.events.contains([event])
        ).all()

        tasks = []
        for webhook in webhooks:
            tasks.append(self._trigger_single_webhook(webhook, event, payload))

        if tasks:
            await asyncio.gather(*tasks)

    @retry_with_backoff(max_retries=3, delay=1)
    async def _trigger_single_webhook(self, webhook: Webhook, event: str, payload: Dict[str, Any]) -> None:
        """Tek bir webhook'u tetikle (yeniden deneme mekanizmalı)"""
        try:
            # Payload'ı imzala
            signature = hmac.new(
                webhook.secret.encode(),
                json.dumps(payload).encode(),
                hashlib.sha256
            ).hexdigest()

            # Webhook'u çağır
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook.url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": signature,
                        "X-Webhook-Event": event
                    },
                    timeout=5
                ) as response:
                    response.raise_for_status()

            # Son tetiklenme zamanını güncelle
            webhook.last_triggered = datetime.utcnow()
            self.db.commit()

        except Exception as e:
            logger.error(f"Webhook trigger failed for {webhook.url}: {str(e)}")
            raise

    def delete_webhook(self, webhook_id: int) -> None:
        """Webhook'u sil"""
        webhook = self.db.query(Webhook).filter(Webhook.id == webhook_id).first()
        if webhook:
            self.db.delete(webhook)
            self.db.commit()

    def update_webhook(self, webhook_id: int, url: str = None, events: List[str] = None, is_active: bool = None) -> Webhook:
        """Webhook'u güncelle"""
        webhook = self.db.query(Webhook).filter(Webhook.id == webhook_id).first()
        if webhook:
            if url:
                webhook.url = url
            if events:
                webhook.events = events
            if is_active is not None:
                webhook.is_active = is_active
            webhook.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(webhook)
        return webhook

    def get_webhooks(self, user_id: int) -> List[Webhook]:
        """Kullanıcının webhook'larını getir"""
        return self.db.query(Webhook).filter(Webhook.user_id == user_id).all()

    def verify_webhook_signature(self, signature: str, payload: str, secret: str) -> bool:
        """Webhook imzasını doğrula"""
        expected_signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature) 