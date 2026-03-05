"""Webhook endpoints for real-time ERP/POS event processing."""

import hashlib
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.database import get_db
from backend.services.erp_integration.webhook_handler import (
    ERPWebhookHandler,
    POSWebhookHandler,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook HMAC signature."""
    if not secret:
        return True  # Skip verification if no secret configured
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/erp")
async def handle_erp_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_webhook_signature: str = Header(default=""),
):
    """Receive and process ERP system webhook events."""
    body = await request.body()

    if settings.erp_webhook_secret and not _verify_signature(
        body, x_webhook_signature, settings.erp_webhook_secret
    ):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    event_type = payload.get("event_type", "")

    handler = ERPWebhookHandler(db)
    result = await handler.handle_event(event_type, payload.get("data", {}))
    return result


@router.post("/pos")
async def handle_pos_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_webhook_signature: str = Header(default=""),
):
    """Receive and process POS system webhook events."""
    body = await request.body()

    if settings.pos_webhook_secret and not _verify_signature(
        body, x_webhook_signature, settings.pos_webhook_secret
    ):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    event_type = payload.get("event_type", "")

    handler = POSWebhookHandler(db)
    result = await handler.handle_event(event_type, payload.get("data", {}))
    return result
